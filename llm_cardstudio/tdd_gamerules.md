
# 游戏状态核心数据

    # 游戏状态
        self.game_state = {
            "gameloop_state": "welcome",    # 游戏主循环状态
            "player_stats": {
                "hp": 100,                  #玩家生命
                "energy": 3,                #玩家能量
                "armor": 0                  #玩家护甲
            },
            "opponent_stats": {
                "hp": 100,                  #对手生命
                "energy": 3,                #对手能量
                "armor": 0                  #对手护甲
            },
            "turn_info": {
                "current_turn": 0,          #回合计数
                "active_player": None       #当前回合的玩家 player or opponent
            },
            "field_cards": {                #场上的卡牌
                "player": [],   
                "opponent": []
            },
             "hand_cards": {                #手牌
                "player": [],
                "opponent": []
            },
            "log": []
        }
        
    # 卡组状态
        self.deck_state = {
            "player": {
                "deck": [],
                "draw_history": [],
                "discard_pile": []
            },
            "opponent": {
                "deck": [],
                "draw_history": [],
                "discard_pile": []
            }
        }


# 单张卡牌的数据定义
    {
        "id": "card_30",
        "name": "生命收割者",
        "type": "随从",
        "cost": 6,
        "attack": 5,
        "health": 5,
        "effect": "战吼:摧毁一个生命值小于2的随从",
        "status": "可用"
    }


# 游戏规则与定义
“main_rules”: {
 "game_title": "LLM卡牌对战",
 "game_goal": "将对方生命值降为 0",
 "round_structure": ["抽牌", "行动阶段", "战斗阶段", "结束阶段"],
 "resource_mechanism": "玩家每回合回复 1 点能量（energy）值，初始 3 点。",
    å"win_condition_description": "当对方的生命值降为 0，或者对方卡组没有卡时，该玩家获胜",
    "loss_condition_description":"当己方的生命值降为 0，或者己方卡组没有卡时，该玩家输掉游戏。"
}

 "card_type_rules": [
    {
      "card_type": "随从",
      "attributes": ["cost", "attack", "health", "effect"],
      "rules": "随从卡使用卡牌后，自动加入我方战场（field_cards）。"
    },
    {
      "card_type": "法术",
      "attributes": ["cost", "effect"],
      "rules": "法术卡使用卡牌后，无论是否成功发生效果（effect），自动进入弃牌堆。"
    }
  ]


# 玩家行动阶段-攻击流程规则：
1、选择要攻击的卡牌（默认选择我方field_cards）第一张
2、选择被攻击的目标（默认选择对方field_cards）第一张
2-1、如果对方field_cards没有卡，则选直接攻击对方生命值
3、如果是法术，则触发法术效果，直接进入弃牌堆
4、如果是随从，判断攻击是否成功
"battle_rules": {
      "battle_calculation": "我方卡牌attack值高于对方卡牌health值加上对手armor值视为攻击成功",
      "damage_calculation": "我方卡牌health扣减等于对方attack值，最小为1点。"
}
4-1、如果攻击成功，先扣除对方armor值，armor值最小为0，扣除卡牌attack值的对方玩家hp生命值
4-2、如果攻击失败，不扣除对方armor值，直接扣除对手卡牌attack值的我方卡牌health生命值
5、攻击与防守的卡牌，攻击结束后都移出战场到各自的discard_pile中



