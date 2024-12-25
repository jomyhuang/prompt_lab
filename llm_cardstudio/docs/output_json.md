
原本格式:
```json
{
    "card_id": "card_3",
    "instructions": [
      {
        "action": "MOVE_CARD",
        "parameters": {
          "card_id": "card_3",
          "target_position": "field",
          "source": "hand"
        },
        "duration": 0.5,
        "sequence": 1
      },
      {
        "action": "APPLY_EFFECT",
        "parameters": {
          "effect_type": "armor_gain",
          "target_id": "player",
          "value": 5
        },
        "duration": 0.2,
        "sequence": 2
      },
      {
        "action": "SHOW_MESSAGE",
        "parameters": {
          "message": "魔法学徒提升了玩家5点护甲值"
        },
        "duration": 1,
        "sequence": 3
      },
      {
        "action": "PLAY_ANIMATION",
        "parameters": {
          "animation_name": "armor_up",
          "target_id": "player"
        },
        "duration": 0.8,
        "sequence": 4
      }
    ],
    "state_updates": {
      "player_stats.armor": 5
    }
}
```

phase = <phase:drawcard,phase:playcard,phase:attack,phase:defense,phase:endturn> 
1. 将 instructions 序列，改成对应不同阶段的指令序列
2. 指令序列必要一定要有phase:playcard，代表卡牌进场生效，不然其他指令阶段无效
3. phase:drawcard 抽牌时，...
4. phase:attack,phase:defense 进入战斗时，攻击时，防御时，...
5. phase:endturn 回合结束时，...

修改后格式:
```json
{
    "card_id": "card_3",
    "phase:playcard_instructions": [
      {
        "action": "MOVE_CARD",
        "parameters": {
          "card_id": "card_3",
          "target_position": "field",
          "source": "hand"
        },
        "duration": 0.5,
        "sequence": 1
      },
      {
        "action": "APPLY_EFFECT",
        "parameters": {
          "effect_type": "armor_gain",
          "target_id": "player",
          "value": 5
        },
        "duration": 0.2,
        "sequence": 2
      },
      {
        "action": "SHOW_MESSAGE",
        "parameters": {
          "message": "魔法学徒提升了玩家5点护甲值"
        },
        "duration": 1,
        "sequence": 3
      },
      {
        "action": "PLAY_ANIMATION",
        "parameters": {
          "animation_name": "armor_up",
          "target_id": "player"
        },
        "duration": 0.8,
        "sequence": 4
      }
    ],
    "phase:playcard_state_updates": {
      "player_stats.armor": 5
    }
    "<phase:...>_instructions": [
      <list of instructions for the phase>
    ],
    "<phase:...>_state_updates": {
      "player_stats.armor": 5
    }
}
```

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
   示例模板:
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
   示例模板:
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
   示例模板:
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
   示例模板:
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
   示例模板:
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
   示例模板:
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
   示例模板:
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
   示例模板:
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
   示例模板:
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
    示例模板:
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
    示例模板:
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
    示例模板:
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

