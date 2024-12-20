from typing import Dict, List, Any, Union
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, validator, field_validator, ValidationError
from typing import List, Optional
import json
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

# 定义卡牌效果类型
class CardEffect(BaseModel):
    effect_type: str = Field(..., description="效果类型")
    target_type: str = Field(..., description="目标类型")
    value: Union[int, str] = Field(..., description="效果值")
    condition: Optional[str] = Field(None, description="触发条件")
    duration: Optional[int] = Field(None, description="持续回合数")

# 定义指令参数模型
class InstructionParameters(BaseModel):
    card_id: Optional[str] = Field(None, description="卡牌ID")
    # card_id: Optional[int] = Field(None, description="卡牌ID")
    target_position: Optional[str] = Field(None, description="目标位置")
    source: Optional[str] = Field(None, description="来源位置")
    animation_name: Optional[str] = Field(None, description="动画名称")
    target_id: Optional[str] = Field(None, description="目标ID")
    value: Optional[int] = Field(None, description="数值")
    type: Optional[str] = Field(None, description="类型")
    message: Optional[str] = Field(None, description="消息内容")
    effect_type: Optional[str] = Field(None, description="效果类型")
    owner: Optional[str] = Field(None, description="拥有者")
    position: Optional[str] = Field(None, description="位置")
    effect: Optional[CardEffect] = Field(None, description="卡牌效果")
    attack: Optional[int] = Field(None, description="攻击力")
    health: Optional[int] = Field(None, description="生命值")
    armor: Optional[int] = Field(None, description="护甲值")
    adjacent_targets: Optional[List[str]] = Field(None, description="相邻目标")
    draw_count: Optional[int] = Field(None, description="抽牌数量")

    @field_validator('type')
    def validate_type(cls, v):
        valid_types = ['heal', 'damage', 'buff', 'debuff', 'destroy', 'draw', 'armor']
        if v and v not in valid_types:
            raise ValueError(f'类型必须是以下之一: {valid_types}')
        return v

    @field_validator('target_position')
    def validate_position(cls, v):
        valid_positions = ['hand', 'field', 'deck', 'discard', 'adjacent']
        if v and v not in valid_positions:
            raise ValueError(f'位置必须是以下之一: {valid_positions}')
        return v

    @field_validator('effect_type')
    def validate_effect_type(cls, v):
        valid_effects = [
            'battlecry', 'deathrattle', 'taunt', 'charge', 
            'spell_damage', 'adjacent_effect', 'conditional_effect',
            'armor_gain', 'card_draw', 'destroy_minion'
        ]
        if v and v not in valid_effects:
            raise ValueError(f'效果类型必须是以下之一: {valid_effects}')
        return v

# 定义单个指令模型
class Instruction(BaseModel):
    action: str = Field(..., description="指令类型")
    parameters: InstructionParameters = Field(..., description="指令参数")
    duration: float = Field(..., description="执行时长")
    sequence: int = Field(..., description="执行序号")

    @field_validator('action')
    def validate_action(cls, v):
        valid_actions = [
            'MOVE_CARD', 'PLAY_ANIMATION', 'UPDATE_HEALTH',
            'SHOW_MESSAGE', 'CREATE_CARD', 'APPLY_EFFECT',
            'UPDATE_STATS', 'DRAW_CARD', 'DESTROY_CARD',
            'APPLY_ARMOR', 'TRIGGER_EFFECT', 'CHECK_CONDITION'
        ]
        if v not in valid_actions:
            raise ValueError(f'动作必须是以下之一: {valid_actions}')
        return v

    @field_validator('duration')
    def validate_duration(cls, v):
        if v < 0 or v > 5.0:
            raise ValueError('持续时间必须在0-5秒之间')
        return v

# 定义完整输出模型
class CommandOutput(BaseModel):
    card_id: str = Field(..., description="卡牌ID")
    phase_playcard_instructions: List[Instruction] = Field(..., description="出牌阶段指令列表")
    phase_playcard_state_updates: Dict[str, Any] = Field(..., description="出牌阶段状态更新")
    phase_drawcard_instructions: Optional[List[Instruction]] = Field(None, description="抽牌阶段指令列表")
    phase_drawcard_state_updates: Optional[Dict[str, Any]] = Field(None, description="抽牌阶段状态更新")
    phase_attack_instructions: Optional[List[Instruction]] = Field(None, description="攻击阶段指令列表")
    phase_attack_state_updates: Optional[Dict[str, Any]] = Field(None, description="攻击阶段状态更新")
    phase_defense_instructions: Optional[List[Instruction]] = Field(None, description="防御阶段指令列表")
    phase_defense_state_updates: Optional[Dict[str, Any]] = Field(None, description="防御阶段状态更新")
    phase_endturn_instructions: Optional[List[Instruction]] = Field(None, description="回合结束阶段指令列表")
    phase_endturn_state_updates: Optional[Dict[str, Any]] = Field(None, description="回合结束阶段状态更新")

    @field_validator('phase_playcard_instructions')
    def validate_playcard_instructions(cls, v):
        if not v:
            raise ValueError('出牌阶段指令列表不能为空')
        sequences = [inst.sequence for inst in v]
        if len(sequences) != len(set(sequences)):
            raise ValueError('指令序列号必须唯一')
        if sorted(sequences) != list(range(1, len(sequences) + 1)):
            raise ValueError('指令序列号必须连续')
        return v

    @field_validator('phase_playcard_state_updates')
    def validate_playcard_state_updates(cls, v):
        if not isinstance(v, dict):
            raise ValueError('状态更新必须是字典类型')
        return v

# 定义输出解析器
output_parser = PydanticOutputParser(pydantic_object=CommandOutput)

# 定义基础提示模板
BASE_TEMPLATE = """
你是一个卡牌游戏指令生成器。你的任务是将卡牌操作转换为游戏系统可执行的指令序列。

游戏阶段说明：
1. phase:playcard - 出牌阶段（必需）：卡牌从手牌进入场上并触发效果
2. phase:drawcard - 抽牌阶段（可选）：抽牌时触发的效果
3. phase:attack - 攻击阶段（可选）：进入战斗/攻击时触发的效果
4. phase:defense - 防御阶段（可选）：被攻击/防御时触发的效果
5. phase:endturn - 回合结束阶段（可选）：回合结束时触发的效果

可用的指令类型：
1. MOVE_CARD: 移动卡牌
   - 参数: card_id, target_position, source
   - 示例: 从手牌移动到场上。target_position 必须是以下之一: hand, field, deck, discard, adjacent

2. PLAY_ANIMATION: 播放动画效果
   - 参数: animation_name, target_id
   - 示例: 播放治疗特效

3. UPDATE_HEALTH: 更新生命值
   - 参数: target_id, value, type(heal/damage)
   - 示例: 治疗玩家3点生命

4. SHOW_MESSAGE: 显示消息
   - 参数: message
   - 示例: 显示"治疗术恢复了3点生命值"

5. CREATE_CARD: 创建卡牌
   - 参数: card_id, owner, position
   - 示例: 在玩家场上创建随从

6. APPLY_EFFECT: 应用效果
   - 参数: effect_type, target_id, value
   - 示例: 给目标施加buff。effect_type 必须是以下之一: battlecry, deathrattle, taunt, charge, spell_damage, adjacent_effect, conditional_effect, armor_gain, card_draw, destroy_minion

7. UPDATE_STATS: 更新统计数据
   - 参数: target_id, stats
   - 示例: 更新玩家攻击力

8. DRAW_CARD: 抽牌
   - 参数: target_id, draw_count
   - 示例: 玩家抽牌

9. DESTROY_CARD: 摧毁卡牌
   - 参数: card_id
   - 示例: 摧毁场上的卡牌

10. APPLY_ARMOR: 应用护甲
    - 参数: target_id, armor_value
    - 示例: 给玩家添加护甲

11. TRIGGER_EFFECT: 触发效果
    - 参数: effect_type, target_id
    - 示例: 触发随从的死亡效果

12. CHECK_CONDITION: 检查条件
    - 参数: condition, target_id
    - 示例: 检查玩家是否有足够的能量

规则说明：
1. 每个指令必须包含 action、parameters、duration 和 sequence
2. sequence 决定指令执行顺序，在每个阶段内必须连续且从1开始
3. duration 表示执行时长(秒)
4. state_updates 用于更新游戏状态(如生命值、能量等)
5. phase:playcard 阶段是必需的，其他阶段根据卡牌效果选择性添加

当前游戏状态：
{game_state}

当前卡牌信息：
{card_data}

玩家操作描述：
{player_action}

请生成符合以下格式的指令序列：
{format_instructions}

注意事项：
1. 指令序列要完整表达操作流程
2. 动画时长要合理
3. 所有数值变化都要反映在对应阶段的state_updates中
4. 消息要清晰易懂
5. 严格遵守可用指令类型和游戏阶段
"""

# 创建提示模板
CARD_COMMAND_PROMPT = PromptTemplate(
    template=BASE_TEMPLATE,
    input_variables=["game_state", "card_data", "player_action"],
    partial_variables={"format_instructions": output_parser.get_format_instructions()}
)

class CardCommandGenerator:
    def __init__(self):
        self.output_parser = PydanticOutputParser(pydantic_object=CommandOutput)
        self.prompt_template = CARD_COMMAND_PROMPT
        load_dotenv()
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", google_api_key=os.environ.get("GOOGLE_API_KEY"))

    def generate_command_template(self, action: str) -> Dict:
        """生成指令模板"""
        if action not in COMMAND_TEMPLATES:
            raise ValueError(f'未知的指令类型: {action}')
        return COMMAND_TEMPLATES[action].copy()

    def format_prompt(self, game_state: Dict, card_data: Dict, player_action: str) -> str:
        """格式化提示词"""
        return self.prompt_template.format(
            game_state=json.dumps(game_state, ensure_ascii=False, indent=2),
            card_data=json.dumps(card_data, ensure_ascii=False, indent=2),
            player_action=player_action
        )

    def parse_llm_response(self, llm_response: str) -> CommandOutput:
        """解析LLM响应，提供详细的错误信息用于调试"""
        try:
            return self.output_parser.parse(llm_response)
        except ValidationError as ve:
            # 格式化验证错误信息
            error_messages = []
            for error in ve.errors():
                location = " -> ".join(str(loc) for loc in error["loc"])
                error_messages.append(f"位置 {location}: {error['msg']}")
            raise ValidationError(error_messages, ve.model)
        except Exception as e:
            error_msg = str(e)
            if "Got:" in error_msg:
                error_msg = "Got: " + error_msg.split("Got:")[1].strip()
            raise ValueError(error_msg)

    def validate_game_state(self, game_state: Dict) -> bool:
        """验证游戏状态格式"""
        required_keys = ['player_stats', 'opponent_stats']
        required_stats = ['hp', 'energy', 'armor']
        
        if not all(key in game_state for key in required_keys):
            raise ValueError("游戏状态缺少必需的键：player_stats 或 opponent_stats")
            
        for key in required_keys:
            if not all(stat in game_state[key] for stat in required_stats):
                raise ValueError(f"游戏状态 {key} 缺少必需的属性：{', '.join(required_stats)}")
                
        return True

    def validate_card_data(self, card_data: Dict) -> bool:
        """验证卡牌数据格式"""
        required_keys = ['id', 'name', 'type', 'cost']
        if not all(key in card_data for key in required_keys):
            raise ValueError(f"卡牌数据缺少必需的键：{', '.join(required_keys)}")
        return True

    def validate_phase_instructions(self, instructions: List[Instruction], phase_name: str) -> bool:
        """验证特定阶段的指令列表"""
        if not instructions:
            if phase_name == "phase_playcard":
                raise ValueError("出牌阶段指令列表不能为空")
            return True
            
        sequences = [inst.sequence for inst in instructions]
        if len(sequences) != len(set(sequences)):
            raise ValueError(f"{phase_name} 阶段的指令序列号必须唯一")
            
        if sorted(sequences) != list(range(1, len(sequences) + 1)):
            raise ValueError(f"{phase_name} 阶段的指令序列号必须连续且从1开始")
            
        return True

    def validate_phase_state_updates(self, state_updates: Dict[str, Any], phase_name: str) -> bool:
        """验证特定阶段的状态更新"""
        if not isinstance(state_updates, dict):
            raise ValueError(f"{phase_name} 阶段的状态更新必须是字典类型")
            
        valid_paths = [
            'player_stats.hp', 'player_stats.energy', 'player_stats.armor',
            'opponent_stats.hp', 'opponent_stats.energy', 'opponent_stats.armor',
            'player_stats.spell_damage', 'opponent_stats.spell_damage',
            'player_stats.card_draw', 'opponent_stats.card_draw'
        ]
        
        for path in state_updates.keys():
            if path not in valid_paths:
                raise ValueError(f"{phase_name} 阶段包含无效的状态更新路径: {path}")
                
        return True

# 使用示例
def main():
    # 创建生成器实例
    generator = CardCommandGenerator()
    
    # 准备测试数据
    game_state = {
        "player_stats": {"hp": 20, "energy": 3, "armor": 0},
        "opponent_stats": {"hp": 30, "energy": 3, "armor": 0}
    }

    # card_data = {
    #     "id": "card_3",
    #     "name": "魔法学徒",
    #     "type": "随从",
    #     "cost": 5,
    #     "effect": "提升护甲值+5"
    # }
    # player_action = "魔法学徒"
    card_data = {
        "id": "card_4",
        "name": "魔法忍者",
        "type": "随从",
        "cost": 5,
        "effect": "提升护甲值+5。攻击时，抽一张手牌。防守时，受到伤害时获得1点护甲"
    }
    player_action = "魔法忍者"
    
    try:
        # 验证输入数据
        if not generator.validate_game_state(game_state):
            raise ValueError("游戏状态格式无效")
        if not generator.validate_card_data(card_data):
            raise ValueError("卡牌数据格式无效")
            
        # 生成提示词
        prompt = generator.format_prompt(game_state, card_data, player_action)
        
        # 调用LLM获取响应
        print("\n generator.llm.invoke")
        response = generator.llm.invoke(prompt)

        print("\nLLM响应:")
        print(response.content)
        
        # 解析响应
        parsed_output = generator.parse_llm_response(response.content)
        print("\n解析后的输出:")
        print(parsed_output.model_dump_json(indent=2))
        print("\n完成解析")
            
    except ValidationError as ve:
        print("数据验证错误:")
        for error in ve.errors():
            location = " -> ".join(str(loc) for loc in error["loc"])
            print(f"- 位置 {location}: {error['msg']}")
    except Exception as e:
        print(f"错误: {str(e)}")

# 指令模板示例
COMMAND_TEMPLATES = {
    "MOVE_CARD": {
        "action": "MOVE_CARD",
        "parameters": {
            "card_id": "",
            "target_position": "",
            "source": ""
        },
        "duration": 0.5,
        "sequence": 0
    },
    "PLAY_ANIMATION": {
        "action": "PLAY_ANIMATION",
        "parameters": {
            "animation_name": "",
            "target_id": ""
        },
        "duration": 1.0,
        "sequence": 0
    },
    "UPDATE_HEALTH": {
        "action": "UPDATE_HEALTH",
        "parameters": {
            "target_id": "",
            "value": 0,
            "type": ""
        },
        "duration": 0.3,
        "sequence": 0
    },
    "SHOW_MESSAGE": {
        "action": "SHOW_MESSAGE",
        "parameters": {
            "message": ""
        },
        "duration": 1.0,
        "sequence": 0
    },
    "CREATE_CARD": {
        "action": "CREATE_CARD",
        "parameters": {
            "card_id": "",
            "owner": "",
            "position": ""
        },
        "duration": 0.5,
        "sequence": 0
    },
    "APPLY_EFFECT": {
        "action": "APPLY_EFFECT",
        "parameters": {
            "effect_type": "",
            "target_id": "",
            "value": 0
        },
        "duration": 0.5,
        "sequence": 0
    },
    "UPDATE_STATS": {
        "action": "UPDATE_STATS",
        "parameters": {
            "target_id": "",
            "stats": {}
        },
        "duration": 0.3,
        "sequence": 0
    },
    "DRAW_CARD": {
        "action": "DRAW_CARD",
        "parameters": {
            "target_id": "",
            "draw_count": 0
        },
        "duration": 0.5,
        "sequence": 0
    },
    "DESTROY_CARD": {
        "action": "DESTROY_CARD",
        "parameters": {
            "card_id": ""
        },
        "duration": 0.5,
        "sequence": 0
    },
    "APPLY_ARMOR": {
        "action": "APPLY_ARMOR",
        "parameters": {
            "target_id": "",
            "armor_value": 0
        },
        "duration": 0.3,
        "sequence": 0
    },
    "TRIGGER_EFFECT": {
        "action": "TRIGGER_EFFECT",
        "parameters": {
            "effect_type": "",
            "target_id": ""
        },
        "duration": 0.5,
        "sequence": 0
    },
    "CHECK_CONDITION": {
        "action": "CHECK_CONDITION",
        "parameters": {
            "condition": "",
            "target_id": ""
        },
        "duration": 0.3,
        "sequence": 0
    }
}

if __name__ == "__main__":
    main()
