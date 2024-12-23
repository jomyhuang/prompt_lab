from typing import Dict, List, Any, Union
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, validator, field_validator, ValidationError
from typing import List, Optional
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import OutputParserException
import os
from dotenv import load_dotenv
from model_config import get_available_models, create_model_instance, CARD_TEST_MODELS, get_default_model

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
    # card_id: str = Field(..., description="卡牌ID")
    card_id: int = Field(..., description="卡牌ID")
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
   示例模板：
   {{
        "action": "MOVE_CARD",
        "parameters": {{
            "card_id": "",
            "target_position": "",
            "source": ""
        }},
        "duration": 0.5,
        "sequence": 0
   }}

2. PLAY_ANIMATION: 播放动画效果
   - 参数: animation_name, target_id
   - 示例: 播放治疗特效
   示例模板：
   {{
        "action": "PLAY_ANIMATION",
        "parameters": {{
            "animation_name": "",
            "target_id": ""
        }},
        "duration": 1.0,
        "sequence": 0
   }}

3. UPDATE_HEALTH: 更新生命值
   - 参数: target_id, value, type(heal/damage)
   - 示例: 治疗玩家3点生命
   示例模板：
   {{
        "action": "UPDATE_HEALTH",
        "parameters": {{
            "target_id": "",
            "value": 0,
            "type": ""
        }},
        "duration": 0.3,
        "sequence": 0
   }}

4. SHOW_MESSAGE: 显示消息
   - 参数: message
   - 示例: 显示"治疗术恢复了3点生命值"
   示例模板：
   {{
        "action": "SHOW_MESSAGE",
        "parameters": {{
            "message": ""
        }},
        "duration": 1.0,
        "sequence": 0
   }}

5. CREATE_CARD: 创建卡牌
   - 参数: card_id, owner, position
   - 示例: 在玩家场上创建随从
   示例模板：
   {{
        "action": "CREATE_CARD",
        "parameters": {{
            "card_id": "",
            "owner": "",
            "position": ""
        }},
        "duration": 0.5,
        "sequence": 0
   }}

6. APPLY_EFFECT: 应用效果
   - 参数: effect_type, target_id, value
   - 示例: 给目标施加buff。effect_type 必须是以下之一: battlecry, deathrattle, taunt, charge, spell_damage, adjacent_effect, conditional_effect, armor_gain, card_draw, destroy_minion
   示例模板：
   {{
        "action": "APPLY_EFFECT",
        "parameters": {{
            "effect_type": "",
            "target_id": "",
            "value": 0
        }},
        "duration": 0.5,
        "sequence": 0
   }}

7. UPDATE_STATS: 更新统计数据
   - 参数: target_id, stats
   - 示例: 更新玩家攻击力
   示例模板：
   {{
        "action": "UPDATE_STATS",
        "parameters": {{
            "target_id": "",
            "stats": {{}}
        }},
        "duration": 0.3,
        "sequence": 0
   }}

8. DRAW_CARD: 抽牌
   - 参数: target_id, draw_count
   - 示例: 玩家抽牌
   示例模板：
   {{
        "action": "DRAW_CARD",
        "parameters": {{
            "target_id": "",
            "draw_count": 0
        }},
        "duration": 0.5,
        "sequence": 0
   }}

9. DESTROY_CARD: 摧毁卡牌
   - 参数: card_id
   - 示例: 摧毁场上的卡牌
   示例模板：
   {{
        "action": "DESTROY_CARD",
        "parameters": {{
            "card_id": ""
        }},
        "duration": 0.5,
        "sequence": 0
   }}

10. APPLY_ARMOR: 应用护甲
    - 参数: target_id, armor_value
    - 示例: 给玩家添加护甲
    示例模板：
    {{
        "action": "APPLY_ARMOR",
        "parameters": {{
            "target_id": "",
            "armor_value": 0
        }},
        "duration": 0.3,
        "sequence": 0
    }}

11. TRIGGER_EFFECT: 触发效果
    - 参数: effect_type, target_id
    - 示例: 触发随从的死亡效果
    示例模板：
    {{
        "action": "TRIGGER_EFFECT",
        "parameters": {{
            "effect_type": "",
            "target_id": ""
        }},
        "duration": 0.5,
        "sequence": 0
    }}

12. CHECK_CONDITION: 检查条件
    - 参数: condition, target_id
    - 示例: 检查玩家是否有足够的能量
    示例模板：
    {{
        "action": "CHECK_CONDITION",
        "parameters": {{
            "condition": "",
            "target_id": ""
        }},
        "duration": 0.3,
        "sequence": 0
    }}

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
    def __init__(self, vendor_name: str = None, model_name: str = None):
        """初始化命令生成器
        
        Args:
            vendor_name: 模型供应商名称，如果为None则使用默认值
            model_name: 模型名称，如果为None则使用供应商的baseline模型
        """
        # 加载环境变量
        load_dotenv()
        
        self.output_parser = PydanticOutputParser(pydantic_object=CommandOutput)
        self.prompt_template = CARD_COMMAND_PROMPT
        
        from model_config import get_available_models, create_model_instance, get_default_model
        
        # 获取可用模型
        available_vendors = get_available_models(use_default=True)
        if not available_vendors:
            raise ValueError("没有可用的模型配置，且默认配置也不可用")
            
        # 如果没有指定供应商和模型，使用默认配置
        if vendor_name is None and model_name is None:
            vendor_name, model_name = get_default_model()
        # 如果只指定了供应商，使用其baseline模型
        elif model_name is None:
            if vendor_name not in available_vendors:
                raise ValueError(f"供应商 {vendor_name} 不可用")
            vendor_config = available_vendors[vendor_name]
            model_name = vendor_config.baseline_models[0]
        # 验证指定的供应商和模型
        else:
            if vendor_name not in available_vendors:
                raise ValueError(f"供应商 {vendor_name} 不可用")
            vendor_config = available_vendors[vendor_name]
            if model_name not in vendor_config.models:
                raise ValueError(f"模型 {model_name} 不在供应商 {vendor_name} 的模型列表中")
            
        # 创建模型实例
        self.llm = create_model_instance(vendor_name, model_name)
        self.vendor_name = vendor_name
        self.model_name = model_name

    # def generate_command_template(self, action: str) -> Dict:
    #     """生成指令模板"""
    #     if action not in COMMAND_TEMPLATES:
    #         raise ValueError(f'未知的指令类型: {action}')
    #     return COMMAND_TEMPLATES[action].copy()

    def format_prompt(self, game_state: Dict, card_data: Dict, player_action: str) -> str:
        """格式化提示词"""
        return self.prompt_template.format(
            game_state=json.dumps(game_state, ensure_ascii=False, indent=2),
            card_data=json.dumps(card_data, ensure_ascii=False, indent=2),
            player_action=player_action
        )

    def save_validation_result(self, result: Dict[str, Any], success: bool, case_info: Dict[str, str] = None):
        """保存验证结果到JSON文件
        
        Args:
            result: 验证结果数据
            success: 验证是否成功
            case_info: 测试用例信息，包含case_id和description
        """
        import datetime
        import os
        from collections import OrderedDict
        
        # 创建save_com目录（如果不存在）
        save_dir = "save_com"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        # 生成时间戳作为文件名
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{save_dir}/validation_{timestamp}.json"
        
        # 使用OrderedDict确保字段顺序
        save_data = OrderedDict([
            ("timestamp", timestamp),
            ("success", success),
            ("model_info", {
                "vendor": self.vendor_name,
                "model": self.model_name
            })
        ])
        
        # 如果有测试用例信息，添加到保存数据中
        if case_info:
            save_data.update([
                ("case_id", case_info.get("case_id")),
                ("description", case_info.get("description")),
                ("card_effects", case_info.get("effects", "")),
                ("player_action", case_info.get("player_action", ""))
            ])
            
        save_data["result"] = result
        
        # 保存到JSON文件，使用indent=4确保更好的格式化，并对中文使用原始编码
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(
                save_data,
                f,
                ensure_ascii=False,  # 保持中文原始编码
                indent=4,           # 使用4空格缩进
                separators=(',', ': ')  # 在冒号后添加空格，使格式更整洁
            )

    def parse_llm_response(self, llm_response: str, case_info: Dict[str, str] = None):
        """解析LLM响应，提供详细的错误信息用于调试"""
        try:
            # 尝试解析响应
            parsed_output = self.output_parser.parse(llm_response)
            # 保存成功的验证结果
            self.save_validation_result(
                result=json.loads(parsed_output.json()),
                success=True,
                case_info=case_info
            )
            return parsed_output
        except (ValidationError, OutputParserException) as e:
            # 清理原始响应中的markdown代码块标记
            cleaned_response = llm_response
            if "```json" in cleaned_response:
                cleaned_response = cleaned_response.split("```json")[-1]
                if "```" in cleaned_response:
                    cleaned_response = cleaned_response.split("```")[0]
            
            # 尝试解析清理后的响应为JSON
            try:
                response_json = json.loads(cleaned_response.strip())
            except json.JSONDecodeError:
                response_json = {"raw_text": cleaned_response}
            
            # 格式化错误消息
            error_msg = str(e)
            error_lines = error_msg.split(". ")
            formatted_error = {
                "main_error": error_lines[0],
                "validation_details": error_lines[1] if len(error_lines) > 1 else None,
                "troubleshooting_url": next((line for line in error_lines if "visit:" in line), None)
            }
            
            # 保存失败的验证结果
            error_data = {
                "error_type": type(e).__name__,
                "error_message": formatted_error,
                "original_response": response_json
            }
            self.save_validation_result(
                result=error_data,
                success=False,
                case_info=case_info
            )
            raise e

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
        # print(response.content)
        
        # 解析响应
        parsed_output = generator.parse_llm_response(response.content)
        print("\n解析后的输出:")
        print(parsed_output.model_dump_json(indent=2, exclude_unset=True))
        print("\n完成解析")
            
    except ValidationError as ve:
        # 格式化验证错误信息
        error_messages = []
        for error in ve.errors():
            location = " -> ".join(str(loc) for loc in error["loc"])
            error_messages.append(f"位置 {location}: {error['msg']}")
        print(f"验证错误: {', '.join(error_messages)}")
    except OutputParserException as e:
        error_msg = str(e)
        if "Got:" in error_msg:
            error_msg = "Got: " + error_msg.split("Got:")[1].strip()
        print(f"输出解析错误: {error_msg}")
    except Exception as e:
        print(f"错误: {str(e)}")


def run_command_tests(case_id: str = None, vendor_name: str = None, model_name: str = None):
    """运行命令生成测试用例
    
    Args:
        case_id: 指定要运行的测试用例ID。如果为None，则显示选择菜单
        vendor_name: 模型供应商名称
        model_name: 模型名称
    """
    import json
    from pathlib import Path
    from model_config import get_available_models, CARD_TEST_MODELS, get_default_model

    # 显示模型选择菜单
    if vendor_name is None or model_name is None:
        available_vendors = get_available_models()
        if not available_vendors:
            print("错误: 没有可用的模型配置")
            return
            
        print("\n可用的模型配置:")
        vendor_list = list(available_vendors.keys())
        for i, vendor_name in enumerate(vendor_list, 1):
            config = available_vendors[vendor_name]
            print(f"\n{i}. {config.name}:")
            for j, model in enumerate(config.models, 1):
                is_baseline = "(*)" if model in config.baseline_models else ""
                print(f"  {i}.{j} {model} {is_baseline}")
                
        try:
            vendor_choice = int(input("\n请选择供应商 (1-{0}): ".format(len(vendor_list))))
            if vendor_choice < 1 or vendor_choice > len(vendor_list):
                print("错误: 无效的供应商选择")
                return
                
            vendor_name = vendor_list[vendor_choice - 1]
            config = available_vendors[vendor_name]
            
            model_choice = int(input(f"请选择模型 (1-{len(config.models)}): "))
            if model_choice < 1 or model_choice > len(config.models):
                print("错误: 无效的模型选择")
                return
                
            model_name = config.models[model_choice - 1]
        except ValueError:
            print("错误: 请输入有效的数字")
            return

    # 创建命令生成器实例
    try:
        generator = CardCommandGenerator(vendor_name, model_name)
        print(f"\n使用模型: {generator.vendor_name} / {generator.model_name}")
    except Exception as e:
        print(f"错误: 创建模型实例失败: {str(e)}")
        return

    # 读取测试数据
    test_file = Path("pe_com_test.json")
    if not test_file.exists():
        print(f"错误: 测试文件 {test_file} 不存在")
        return

    try:
        with open(test_file, "r", encoding="utf-8") as f:
            test_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"错误: 测试文件JSON格式无效: {e}")
        return
    except Exception as e:
        print(f"错误: 读取测试文件时出错: {e}")
        return
    
    # 如果没有指定case_id，显示选择菜单
    if case_id is None:
        print("\n可用的测试用例:")
        print("0. 运行所有测试用例")
        for i, test_case in enumerate(test_data["test_cases"], 1):
            print(f"{i}. {test_case['description']}")
        
        try:
            choice = int(input("\n请选择要运行的测试用例 (0-{0}): ".format(len(test_data["test_cases"]))))
            if choice < 0 or choice > len(test_data["test_cases"]):
                print("错误: 无效的选择")
                return
                
            if choice == 0:
                case_id = None
            else:
                case_id = test_data["test_cases"][choice - 1]["case_id"]
        except ValueError:
            print("错误: 请输入有效的数字")
            return

    # 根据选择运行测试
    test_cases = test_data["test_cases"]
    if case_id:
        # 运行单个测试用例
        test_case = next((tc for tc in test_cases if tc["case_id"] == case_id), None)
        if test_case:
            run_single_test(generator, test_case)
        else:
            print(f"错误: 未找到测试用例 {case_id}")
    else:
        # 运行所有测试用例
        print("\n运行所有测试用例...")
        for test_case in test_cases:
            run_single_test(generator, test_case)

def run_single_test(generator: CardCommandGenerator, test_case: dict):
    """运行单个测试用例
    
    Args:
        generator: 命令生成器实例
        test_case: 测试用例数据
    """
    import time
    
    start_time = time.time()
    
    print(f"\n执行测试用例: {test_case['case_id']}")
    print(f"描述: {test_case['description']}")
    print(f"动作: {test_case['player_action']}")
    
    try:
        # 格式化提示词
        prompt = generator.format_prompt(
            game_state=test_case["game_state"],
            card_data=test_case["card_data"],
            player_action=test_case["player_action"]
        )
        
        # 调用LLM获取响应
        print("generator.llm.invoke")
        print(f"正在使用模型: {generator.vendor_name}/{generator.model_name}")
        llm_response = generator.llm.invoke(prompt).content
        
        # 解析响应
        try:
            # 从card_data中获取effects
            card_effects = test_case.get("card_data", {}).get("effects", "")
            parsed_output = generator.parse_llm_response(
                llm_response,
                case_info={
                    "case_id": test_case["case_id"],
                    "description": test_case["description"],
                    "effects": card_effects,
                    "player_action": test_case["player_action"]
                }
            )
            end_time = time.time()
            execution_time = end_time - start_time
            print(f"✓ 测试成功: {test_case['case_id']}")
            print(f"执行时间: {execution_time:.2f} 秒")
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            print(f"✗ 测试失败: {test_case['case_id']}")
            print(f"错误信息: {str(e)}")
            print(f"执行时间: {execution_time:.2f} 秒")
            
    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"✗ 测试执行错误: {str(e)}")
        print(f"执行时间: {execution_time:.2f} 秒")

if __name__ == "__main__":
    run_command_tests()
