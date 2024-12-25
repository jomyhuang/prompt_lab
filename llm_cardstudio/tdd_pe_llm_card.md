

1.在 gui_main.py 中增加攻击UI, 进入呼叫perform_attack前, 如果没有指定的攻击者,或是没有指定的目标,则激活UI进入选择攻击者或是选择目标
在render_chat_view 对话框下方的攻击按钮,按下后,
在下方,使用selectbox选择我方场上的卡牌,选择敌方场上的卡牌
按下确认攻击键, 通过user_input 激活 perform_attack
2. 修改perform_attack 参考 play_card 使用命令序列模式
3. 增加 perform_attack 的命令序列在 llm_commands_interaction.py 中
3-1. perform_attack开始进入attack,并执行命令序列
4. 命令序列如下
4-1.检查我方场上的卡牌(如果没有,则无法攻击),选择敌方场上的卡牌(如果没有,跳过该指令则直接攻击对手伤害)
4-2. 将伤害的卡牌移动到墓地,计算对手伤害
5. 结束攻击, 回到action阶段玩家后续行动






        self.command_handlers = {
            'MOVE_CARD': self._handle_move_card,
            'PLAY_ANIMATION': self._handle_animation,
            'UPDATE_HEALTH': self._handle_update_health,
            'SHOW_MESSAGE': self._handle_show_message,
            'CREATE_CARD': self._handle_create_card,
            'APPLY_EFFECT': self._handle_apply_effect,
            'UPDATE_STATS': self._handle_update_stats,
            'DRAW_CARD': self._handle_draw_card,
            'DESTROY_CARD': self._handle_destroy_card,
            'APPLY_ARMOR': self._handle_apply_armor,
            'TRIGGER_EFFECT': self._handle_trigger_effect,
            'CHECK_CONDITION': self._handle_check_condition
        }
        
        self.effect_handlers = {
            'battlecry': self._handle_battlecry,
            'deathrattle': self._handle_deathrattle,
            'taunt': self._handle_taunt,
            'charge': self._handle_charge,
            'spell_damage': self._handle_spell_damage,
            'adjacent_effect': self._handle_adjacent_effect,
            'conditional_effect': self._handle_conditional_effect,
            'armor_gain': self._handle_armor_gain,
            'card_draw': self._handle_card_draw
        }

卡牌操作：
CREATE_CARD {card_id, owner, position}: 创建一张卡牌。
MOVE_CARD {card_id, target_position, duration}: 移动卡牌。
DISCARD_CARD {card_id, duration}: 弃掉一张卡牌。
TAP_CARD {card_id, duration}: 横置一张卡牌
角色操作：
UPDATE_HEALTH {player_id, health_value, animation}: 更新生命值。
APPLY_EFFECT {target_id, effect_type, effect_value, duration}: 应用效果。
UI 元素操作：
SHOW_MESSAGE {message}: 显示消息
SET_BACKGROUND {background_image}：设置背景
ACTIVATE_BUTTON {button_id, is_active}：激活按钮
SHOW_HIGHLIGHT {card_id/target_id/area}：高亮显示元素
状态变化
UPDATE_TEXT {element_id, text_value}: 更新文本元素(比如资源数量)
UPDATE_SPRITE {element_id, sprite_name}：修改卡牌图片或卡背
动画效果：
PLAY_ANIMATION {target_id, animation_name, duration}: 播放动画效果。
FADE_ELEMENT {target_id, duration, direction}: 让元素淡入或者淡出
多指令支持： 例如，卡牌移动的同时播放动画 [MOVE_CARD, PLAY_ANIMATION]


玩家输入: “我打出这张火球术，攻击敌方英雄”
对话模块 (LLM):
理解意图：play，attack
提取信息：card_name = 火球术, target = 敌方英雄
输出指令：{command_type : "play", card: "火球术", target:"敌方英雄"}
指令生成模块:
根据指令和游戏逻辑生成 UI 渲染指令
例如：
[
{"action": "MOVE_CARD", "card_id": "火球术", "target_position": "目标英雄位置", "duration": 0.5},
{"action": "PLAY_ANIMATION", "target_id":"目标英雄","animation_name":"火球爆炸", "duration":0.3},
{"action": "UPDATE_HEALTH", "player_id": "敌方玩家", "health_value": -5},
{"action":"SHOW_MESSAGE", "message": "你对敌方英雄施放了火球术"}
]














# ------------------------------------------------------------------
#                         卡牌设计与规则提示词工程
# ------------------------------------------------------------------

# ------------------------------------------------------------------
#                             I.  全局说明
# ------------------------------------------------------------------
# 1. 任务目标:
#    指导 LLM 为卡牌对战游戏生成卡牌设计方案和游戏规则。
# 2. 适用范围
#    本提示词工程适用于大多数卡牌对战游戏, 尤其适用于类似《游戏王》的卡牌游戏.
# 3. 主要模块:
#    - 基础游戏元素定义
#    - 卡牌类型及属性定义
#    - 游戏规则生成
#    - LLM 对话行为设定
#    - 游戏 AI 行为设定
# 4. 使用方法
#    - 根据实际需要选择对应的提示词模板。
#    - 使用占位符动态填充具体数据（如卡牌类型、属性等）
#    - 在实际使用中，基于 LangChain 等框架进行链式调用。
#    - 基于 LLM 的输出，使用结构化的数据格式存储。
# 5. 输出格式:
#    通常采用 JSON 或者 YAML 格式，方便程序直接解析和使用。

# ------------------------------------------------------------------
#                     II.  基本游戏元素定义
# ------------------------------------------------------------------

# 1. 游戏核心规则提示词模板：
RULE_GAME_CORE = """
Task: You are a card-based game expert, please analyze following rules, and generate a summary for those rules.
Here are the basic rules for a card game:
Game Title: {game_title}
Game Goal: {game_goal} (e.g., Reduce opponent life to zero)
Basic Game Flow/Round Structure: {round_structure_description} (e.g., Draw Phase> Standby Phase > Main Phase > Battle Phase > End Phase)
Resource Mechanism for a Game: {resource_mechanism_description} (e.g., magic points, mana, energy)
Win Condition:{win_condition_description} (e.g., Reduce opponent health point to zero or opponent has no cards in the deck)
Loss Condition:{loss_condition_description} (e.g., Own health point becomes zero or player has no cards in the deck)
Output:  (Please give brief description for those rules)
- Summary of Basic rules:
"""

# 2. 游戏属性定义提示词模板:
RULE_GAME_ATTRIBUTE = """
Task: You are a card game expert, please define how each game attribute works in a card-based game.
Attribute Definitions: {attribute_list_description}(e.g.,
    Life Point Represents the health value of a player.
    Attack Value Represents the attack power of a monster card.
    Defence Value Represents the defense power of a monster card.
    Level Represents the power level of the card.
    Cost Represents energy needed to play the card.
    Attribute Represents the type of the game card like fire, water, grass)
Output:  (Please give brief description for those attribute definitions, and follow the same format as input description)
- Description of Game Attributes:
"""

# ------------------------------------------------------------------
#                   III. 卡牌类型及属性定义
# ------------------------------------------------------------------

# 1. 卡牌类型定义提示词模板：
RULE_CARD_TYPE = """
Task: You are a card-based game expert, please define detailed descriptions for each card type.
Card Type: {card_type} (e.g., monster, spell, trap)
Card Attributes: {attribute_specification},
(e.g.,
        - If card_type is monster: level  (1-12) , attack, defense,attribute, effect
        - If card_type is spell: type (e.g., normal, quick-play, continuous), effect
        - if card_type is trap: type (e.g., normal, continuous, counter), trigger condition , effect.)

If there are any special card effect rules please give description, otherwise ignore it.
Output:
Description for that Card Type:(please provide a brief and comprehensive of the rule)
- Description of {card_type}:
"""

# 2. 卡牌特殊规则定义提示词模版
RULE_CARD_SPECIAL = """
Task: You are a card-based game expert, please define special rules for various types of card, if there are no special rules, please ignore it.
Special Rules: {card_special_rules_description} (e.g., if a card has continuous effect, the effect will be active as long as the card exists)
Output:  (Please give brief explanation for special rules)
- Description of Special Card Rules:
 """


# ------------------------------------------------------------------
#                 IV.  战斗/回合规则定义
# ------------------------------------------------------------------

# 1. 战斗规则提示词模板：
RULE_BATTLE = """
 Task: You are a card battle expert, please define the detailed battle rule.
Battle Calculation: Please define the calculation of attack and defense.
Damage Calculation: Please define the calculation of life point reduction when card attacking other card directly or player directly for battle.
Any other special rules for battle: Please give a brief description for any special rules.
Output: (Please provide a brief and comprehensive summary for the rule)
- Description for Battle Rules:
"""


# 2. 回合流程提示词模版
RULE_TURN_PHASE = """
Task: You are a card based game expert, please define all the round phase in order, and please also describe what can a player do in this phase.
Round Phase:  {round_phase_description}, (e.g., Draw Phase> Standby Phase > Main Phase > Battle Phase > End Phase)
Output: (Please describe all the phases based on the input description.
- Description of Round Structure:
"""


# ------------------------------------------------------------------
#                   V.  游戏流程规则定义
# ------------------------------------------------------------------

# 1.  游戏流程规则定义提示词模板
RULE_GAME_FLOW = """
Task: You are a card game expert, please describe how should the game progress step by step.
Game Flow Description {game_flow_description}.
(e.g.,
1.  At the start of the game, both players should shuffle their decks, draw initial hand cards (5 cards) , and then place the card on the filed.
2. Players take their turns one by one. Each player has the right to choose one action to perform during his turn
3. After a given set of turns the game should automatically decide a winner.)
Output: (Please provide a detailed game flow description step by step based on the input)
- Description for overall game flow:
"""


# ------------------------------------------------------------------
#                     VI. 特殊规则定义
# ------------------------------------------------------------------
# 1. 特殊规则提示词模版
RULE_SPECIAL = """
Task: You are a card-based game expert, please define the following special rules for a given card game.
Special Rules: {special_rules_description}
(e.g.,
- Chain Mechanism: If one player plays a card with counter effect, then the other player can play another effect to counter that, until no additional counter card can be played.
- Card Prioritie: For a given round, spell card > trap card > monster card. Only high priority card can be played at a given time without counter card.
- Duplicate Card Limit for Deck Construction: Only 3 card with the same name is allowed in the deck)

Output: (Please provide a brief explanation for those rules)
- Description of Special rules:
"""


# ------------------------------------------------------------------
#                   VII. LLM 对话规则定义
# ------------------------------------------------------------------

# 1.  对话处理提示词模板：
PROMPT_CHAT_PROCESS = """
Task: You are a card-based game player, and you receive a message from other players, and must choose the next action based on your current situation.
Here is the history of the conversation {chat_history}.
Current situation: {game_state}.
Message from player: {user_message}
Output:
 Action : [card_action, game_action], the card_action includes following options [play, attack]
Game action Options: [end_phase]
Your response: ( respond based on your action and current game state in a story-telling format)
"""

# ------------------------------------------------------------------
#                     VIII. 游戏 AI 行为规则
# ------------------------------------------------------------------

# 游戏 AI 提示词模板：
PROMPT_AI_ACTION = """
 Task: You are an AI player in a card-based game.
 You should choose the next action based on your current situation.
 Current situation: {game_state}.
The phase of the round:{current_phase_description}
 Here are all the card in your hand: {hand_card}.
 Here are all the card on the field: {card_field}.
Here is the action from the other player:{current_player_action_description}
 Output:
  Action : [card_action, game_action], the card_action include following options [play, attack]
  Game action options: [end_phase]
  Your response: (Give a brief explanation based on you action and current game state)
"""


# ------------------------------------------------------------------
#                      IX.  提示词示例
# ------------------------------------------------------------------
# 以下是一些提示词使用方式示例

# 游戏基础信息规则
# 示例1：
# 使用结构化数据定义游戏核心规则：
game_core_data = {
    "game_title": "卡牌决斗",
    "game_goal": "将对方玩家的生命值降为 0",
    "round_structure_description": "抽牌阶段 > 主要阶段 > 战斗阶段 > 结束阶段",
    "resource_mechanism_description": "每回合开始回复 1 点魔法值，初始 3 点。",
     "win_condition_description": "当对方的生命值降为 0，或者对方卡组没有卡时，该玩家获胜",
     "loss_condition_description":"当己方的生命值降为 0，或者己方卡组没有卡时，该玩家输掉游戏。"
}

# 示例2
# 使用结构化数据定义游戏属性：
game_attribute_data = {
    "attribute_list_description": """
    Life Point: Represents the health value of a player.
    Attack Value: Represents the attack power of a monster card.
    Defence Value: Represents the defense power of a monster card.
    Level: Represents the power level of a card.
    Cost: Represents energy needed to play the card
    Attribute: Represents the type of the game card like fire, water, grass
    """
}

# 卡牌规则示例
# 示例3
# 使用结构化数据定义卡牌类型
card_type_data = {
    "card_type": "monster",
    "attribute_specification":  "level  (1-12) , attack, defense,attribute, effect"
}

# 示例 4:
# 定义卡牌特殊规则
card_special_rules = {
  "card_special_rules_description":"If a monster with 'piercing attack' effect attacks a monster card, and the attack is higher than the defense of that monster, the extra damage will be given to the player directly"
}

# 回合流程示例
# 示例5
# 定义回合流程
round_phase_data = {
  "round_phase_description":"Draw Phase > Standby Phase > Main Phase > Battle Phase > End Phase"
}

# 游戏流程
game_flow = {"game_flow_description": """
1. At the start of the game, both players should shuffle their decks, draw initial hand cards (5 cards) , and then place the card on the filed.
2. Players take their turns one by one. Each player has the right to choose one action to perform during his turn
3. After a given set of turns the game should automatically decide a winner.
"""
}
#战斗规则示例
# 示例6
battle_rules_data = {
    "battle_calculation":"monster with higher attack point can attack monster with lower attack point",
    "damage_calculation":"difference between attack point and defence point will be reduced from the other player or monster health. if the attack point lower then defence point, then the monster will not be destroyed, and 0 damage would be inflicted., the minimum attack damage would be 1",
    "special_rules" : "If a spell or trap card is used in battle, then the effect of that specific card would be applied."
}

# 特殊规则示例
special_rules_data ={
   "special_rules_description":"Chain Mechanism: If one player plays a card with counter effect, then the other player can play another effect to counter that, until no additional counter card can be played.\
   Card Prioritie: For a given round, spell card > trap card > monster card. Only high priority card can be played at a given time without counter card.\
     Duplicate Card Limit for Deck Construction: Only 3 card with the same name is allowed in the deck"
}

# 对话信息示例
chat_message_data ={
    "chat_history": "user1:(I am going to use a magic card) AI:( Please be my guest)",
    "game_state":  "player1 life point 3000; AI life point : 4000; player1 hand cards: ['monster','spell'], AI hand card:['trap','monster'],
    card_field_player1:['monster23','monster12']; card_field_AI:[]",
   "user_message":" I am going to use attack card"
}
#AI 行为信息示例
ai_action_data = {
    "game_state": "player1 life point 3000; AI life point : 4000; player1 hand cards: ['monster','spell'], AI hand card:['trap','monster'],card_field_player1:['monster23','monster12']; card_field_AI:[]",
    "current_phase_description": "Main Phase",
    "hand_card": "['trap','monster']",
    "card_field": "[]",
    "current_player_action_description":"user1 used attack card"
}

# 游戏规则示例
{
 "game_title": "卡牌对战",
 "game_goal": "将对方生命值降为 0",
 "round_structure": ["抽牌", "主要阶段", "战斗阶段", "结束阶段"],
 "resource_mechanism": "玩家每回合回复 1 点魔法值，初始 3 点。",
 "win_condition": "生命值降为 0 或者卡组耗尽。"
,
 "card_type_rules": [
    {
      "card_type": "monster",
      "attributes": ["level", "attack", "defense", "attribute", "effect"],

    },
     {
      "card_type": "spell",
      "attributes": ["type", "effect"],
    },
    {
    "card_type": "trap",
      "attributes": ["type", "trigger condition" ,"effect"]
    }
  ],

"battle_rules": {
      "battle_calculation": "攻击力高于对方防御力视为攻击成功",
      "damage_calculation": "生命值的扣减等于对方攻击力减去我方防御力，最小为1点。",
            "special_rules": "如果怪兽的等级高于对方，可以进行额外攻击"
},
   "special_rules" : {
    "card_priorities":"卡牌效果优先级：连锁效果>陷阱效果>魔法效果>怪兽效果"
     "duplicate_card_limit": "每张卡组最多有3张同名卡"
}
}


