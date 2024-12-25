# 游戏流程规则设计

## 1. 游戏基础规则

### 1.1 游戏设置
```json
{
    "game_settings": {
        "initial_health": 30,
        "initial_mana": 0,
        "max_mana": 10,
        "hand_size_limit": 10,
        "deck_size": {
            "min": 30,
            "max": 40
        },
        "board_size_limit": 7,
        "turn_time_limit": 90
    }
}
```

### 1.2 资源系统
```json
{
    "resource_rules": {
        "mana": {
            "gain_per_turn": 1,
            "refresh_timing": "start_of_turn",
            "carry_over": false
        },
        "card_draw": {
            "per_turn": 1,
            "timing": "start_of_turn",
            "fatigue_damage": {
                "enabled": true,
                "initial": 1,
                "increment": 1
            }
        }
    }
}
```

## 2. 回合流程

### 2.1 回合阶段定义
```json
{
    "turn_phases": [
        {
            "name": "开始阶段",
            "steps": [
                {
                    "name": "触发开始效果",
                    "timing": "start_of_turn",
                    "priority": 1
                },
                {
                    "name": "恢复法力值",
                    "action": "refresh_mana",
                    "priority": 2
                },
                {
                    "name": "抽牌",
                    "action": "draw_card",
                    "priority": 3
                }
            ]
        },
        {
            "name": "主要阶段",
            "steps": [
                {
                    "name": "行动阶段",
                    "allowed_actions": [
                        "play_card",
                        "attack",
                        "use_ability"
                    ],
                    "restrictions": {
                        "cards_per_turn": "unlimited",
                        "attacks_per_unit": 1
                    }
                }
            ]
        },
        {
            "name": "结束阶段",
            "steps": [
                {
                    "name": "触发结束效果",
                    "timing": "end_of_turn",
                    "priority": 1
                },
                {
                    "name": "检查手牌上限",
                    "action": "check_hand_size",
                    "priority": 2
                }
            ]
        }
    ]
}
```

### 2.2 回合执行示例

输入：
```
当前回合：玩家回合
阶段：开始阶段
游戏状态：
- 玩家生命值：30
- 玩家法力值：3/3
- 玩家手牌：4张
- 场上有"见习法师"（效果：回合开始时抽一张牌）
```

输出：
```json
{
    "phase_execution": {
        "phase": "start_of_turn",
        "steps": [
            {
                "action": "trigger_effects",
                "effects": [
                    {
                        "source": "见习法师",
                        "effect": "draw_card",
                        "count": 1
                    }
                ]
            },
            {
                "action": "refresh_mana",
                "details": {
                    "old_value": 3,
                    "new_value": 4,
                    "max_value": 4
                }
            },
            {
                "action": "draw_card",
                "count": 1,
                "source": "turn_draw"
            }
        ],
        "resulting_state": {
            "player_health": 30,
            "player_mana": "4/4",
            "hand_size": 6
        }
    }
}
```

## 3. 战斗系统

### 3.1 战斗规则
```json
{
    "combat_rules": {
        "attack_timing": "main_phase",
        "attack_restrictions": {
            "summoning_sickness": true,
            "once_per_turn": true,
            "valid_targets": [
                "enemy_creatures",
                "enemy_player"
            ]
        },
        "damage_resolution": {
            "simultaneous": true,
            "excess_to_player": false
        },
        "keywords": {
            "charge": {
                "effect": "ignore_summoning_sickness",
                "duration": "permanent"
            },
            "taunt": {
                "effect": "must_be_attacked",
                "duration": "permanent"
            }
        }
    }
}
```

### 3.2 战斗示例

输入：
```
行动：攻击
攻击者：烈焰战士（3/2）
防御者：石墙守卫（2/4，嘲讽）
```

输出：
```json
{
    "combat_resolution": {
        "steps": [
            {
                "step": "validate_attack",
                "checks": [
                    {
                        "type": "can_attack",
                        "result": true
                    },
                    {
                        "type": "valid_target",
                        "result": true
                    }
                ]
            },
            {
                "step": "deal_damage",
                "actions": [
                    {
                        "source": "烈焰战士",
                        "target": "石墙守卫",
                        "amount": 3
                    },
                    {
                        "source": "石墙守卫",
                        "target": "烈焰战士",
                        "amount": 2
                    }
                ]
            },
            {
                "step": "check_survival",
                "results": [
                    {
                        "unit": "烈焰战士",
                        "health": 0,
                        "status": "destroyed"
                    },
                    {
                        "unit": "石墙守卫",
                        "health": 1,
                        "status": "survived"
                    }
                ]
            }
        ]
    }
}
```

## 4. 效果处理系统

### 4.1 效果优先级规则
```json
{
    "effect_priority": {
        "timing_order": [
            "prevent",
            "replace",
            "trigger",
            "continuous"
        ],
        "layer_order": [
            "copy_effects",
            "control_change",
            "text_change",
            "type_change",
            "ability_add_remove",
            "power_toughness_set",
            "power_toughness_modify",
            "counter_modify"
        ]
    }
}
```

### 4.2 效果处理示例

输入：
```
触发效果：
1. 元素使者的"回合结束时获得+1/+1"
2. 寒冰诅咒的"解冻时造成3点伤害"
3. 火焰护盾的"受到伤害时反弹1点伤害"
```

输出：
```json
{
    "effect_resolution": {
        "effect_stack": [
            {
                "source": "元素使者",
                "type": "trigger",
                "timing": "end_of_turn",
                "priority": 1
            },
            {
                "source": "寒冰诅咒",
                "type": "trigger",
                "timing": "on_unfreeze",
                "priority": 2
            },
            {
                "source": "火焰护盾",
                "type": "trigger",
                "timing": "on_damage",
                "priority": 3
            }
        ],
        "resolution_order": [
            {
                "effect": "火焰护盾",
                "resolution": "damage_reflection"
            },
            {
                "effect": "寒冰诅咒",
                "resolution": "damage_effect"
            },
            {
                "effect": "元素使者",
                "resolution": "stat_modification"
            }
        ]
    }
}
```

## 5. 游戏状态转换

### 5.1 状态检查规则
```json
{
    "state_based_actions": {
        "check_timing": [
            "after_each_action",
            "before_priority_passes"
        ],
        "checks": [
            {
                "condition": "creature_zero_health",
                "action": "destroy_creature"
            },
            {
                "condition": "player_zero_health",
                "action": "end_game"
            },
            {
                "condition": "hand_over_limit",
                "action": "discard_excess"
            }
        ]
    }
}
```

### 5.2 状态转换示例

输入：
```
当前状态：
- 玩家A生命值：5
- 玩家B生命值：3
- 场上效果："持续伤害"（回合结束时对双方造成1点伤害）
```

输出：
```json
{
    "state_transition": {
        "trigger": "end_of_turn_damage",
        "effects": [
            {
                "type": "damage",
                "target": "both_players",
                "amount": 1
            }
        ],
        "state_checks": [
            {
                "check": "player_health",
                "player_a": {
                    "old_health": 5,
                    "new_health": 4,
                    "status": "alive"
                },
                "player_b": {
                    "old_health": 3,
                    "new_health": 2,
                    "status": "alive"
                }
            }
        ],
        "game_continues": true
    }
}
```

## 6. 特殊规则处理

### 6.1 连锁规则
```json
{
    "chain_rules": {
        "max_chain_length": 20,
        "resolution_order": "last_in_first_out",
        "interrupt_window": {
            "enabled": true,
            "duration": 5,
            "allowed_card_types": ["instant", "reaction"]
        }
    }
}
```

### 6.2 特殊规则示例

输入：
```
连锁情况：
1. 玩家A使用"火球术"
2. 玩家B使用"反制法术"
3. 玩家A使用"法术护盾"
```

输出：
```json
{
    "chain_resolution": {
        "chain_links": [
            {
                "index": 1,
                "card": "火球术",
                "player": "A",
                "target": "player_B"
            },
            {
                "index": 2,
                "card": "反制法术",
                "player": "B",
                "target": "fire_ball"
            },
            {
                "index": 3,
                "card": "法术护盾",
                "player": "A",
                "target": "fire_ball"
            }
        ],
        "resolution_sequence": [
            {
                "resolve": "法术护盾",
                "effect": "protect_spell",
                "result": "fire_ball_protected"
            },
            {
                "resolve": "反制法术",
                "effect": "counter_spell",
                "result": "countered_but_protected"
            },
            {
                "resolve": "火球术",
                "effect": "deal_damage",
                "result": "success"
            }
        ]
    }
}
```

## 7. 游戏流程训练建议

### 7.1 训练数据准备
1. 覆盖所有基本回合阶段
2. 包含各种战斗场景
3. 测试复杂效果链
4. 验证特殊规则处理

### 7.2 验证方法
1. 检查规则一致性
2. 测试边界情况
3. 验证优先级处理
4. 确保状态转换正确

### 7.3 优化建议
1. 定期更新规则库
2. 收集实战数据
3. 调整处理逻辑
4. 优化性能表现

这个游戏流程规则设计提供了：
1. 完整的回合结构
2. 详细的战斗系统
3. 清晰的效果处理
4. 准确的状态转换

您觉得这个游戏流程设计如何？需要我详细解释某些部分吗？
