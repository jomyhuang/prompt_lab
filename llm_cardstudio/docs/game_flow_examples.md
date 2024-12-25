# 游戏流程详细示例

## 1. 复杂回合示例

### 1.1 多效果触发顺序

输入：
```
回合开始时，场上有以下效果：
1. 见习法师（回合开始时抽一张牌）
2. 魔法水晶（回合开始时获得一点法力值）
3. 诅咒物品（回合开始时受到1点伤害）
4. 生命之树（回合开始时恢复1点生命）

玩家状态：
- 生命值：20
- 法力值：3/3
- 手牌：3张
```

输出：
```json
{
    "turn_start_resolution": {
        "effect_queue": [
            {
                "source": "见习法师",
                "effect_type": "draw",
                "priority": 1,
                "resolution": {
                    "action": "draw_card",
                    "result": "success",
                    "new_hand_size": 4
                }
            },
            {
                "source": "魔法水晶",
                "effect_type": "resource_gain",
                "priority": 2,
                "resolution": {
                    "action": "gain_mana",
                    "amount": 1,
                    "new_mana": "4/4"
                }
            },
            {
                "source": "诅咒物品",
                "effect_type": "damage",
                "priority": 3,
                "resolution": {
                    "action": "deal_damage",
                    "amount": 1,
                    "new_health": 19
                }
            },
            {
                "source": "生命之树",
                "effect_type": "heal",
                "priority": 4,
                "resolution": {
                    "action": "heal",
                    "amount": 1,
                    "new_health": 20
                }
            }
        ],
        "final_state": {
            "health": 20,
            "mana": "4/4",
            "hand_size": 4,
            "effects_resolved": 4
        }
    }
}
```

### 1.2 复杂行动阶段

输入：
```
玩家行动序列：
1. 使用"召唤术"（费用：3，效果：召唤两个1/1的小精灵）
2. 使用"增益光环"（费用：2，效果：所有友方随从+1/+1）
3. 使用小精灵攻击对手的2/2防御者
4. 使用另一个小精灵直接攻击对手

玩家状态：
- 法力值：6/6
- 场上单位：两个2/2小精灵（受增益光环影响）
对手状态：
- 生命值：20
- 场上单位：一个2/2防御者
```

输出：
```json
{
    "action_phase_resolution": {
        "actions": [
            {
                "action": "play_card",
                "card": "召唤术",
                "cost": 3,
                "resolution": {
                    "effect": "summon",
                    "tokens": [
                        {
                            "name": "小精灵",
                            "stats": "1/1",
                            "position": "board_1"
                        },
                        {
                            "name": "小精灵",
                            "stats": "1/1",
                            "position": "board_2"
                        }
                    ],
                    "mana_remaining": 3
                }
            },
            {
                "action": "play_card",
                "card": "增益光环",
                "cost": 2,
                "resolution": {
                    "effect": "buff_all",
                    "targets": [
                        {
                            "name": "小精灵_1",
                            "old_stats": "1/1",
                            "new_stats": "2/2"
                        },
                        {
                            "name": "小精灵_2",
                            "old_stats": "1/1",
                            "new_stats": "2/2"
                        }
                    ],
                    "mana_remaining": 1
                }
            },
            {
                "action": "attack",
                "attacker": "小精灵_1",
                "defender": "防御者",
                "resolution": {
                    "combat": {
                        "damage_dealt": {
                            "to_defender": 2,
                            "to_attacker": 2
                        },
                        "result": {
                            "attacker_destroyed": true,
                            "defender_destroyed": true
                        }
                    }
                }
            },
            {
                "action": "attack",
                "attacker": "小精灵_2",
                "defender": "opponent",
                "resolution": {
                    "combat": {
                        "damage_dealt": 2,
                        "new_opponent_health": 18
                    }
                }
            }
        ],
        "final_state": {
            "player": {
                "mana": "1/6",
                "board": [
                    {
                        "name": "小精灵_2",
                        "stats": "2/2",
                        "can_attack": false
                    }
                ]
            },
            "opponent": {
                "health": 18,
                "board": []
            }
        }
    }
}
```

## 2. 复杂效果链示例

### 2.1 连锁效果触发

输入：
```
效果触发序列：
1. 玩家使用"连环闪电"（对一个目标造成3点伤害）
2. 目标是装备了"反伤护甲"的敌方随从（受到伤害时反弹1点伤害）
3. 场上有"法力增幅"（所有法术伤害+1）
4. 玩家有"法术护盾"（受到伤害时抵消1点）

目标状态：
- 生命值：4
- 装备：反伤护甲
```

输出：
```json
{
    "effect_chain_resolution": {
        "initial_effect": {
            "card": "连环闪电",
            "base_damage": 3,
            "modified_damage": 4,
            "modifier": {
                "source": "法力增幅",
                "amount": 1
            }
        },
        "chain_sequence": [
            {
                "step": 1,
                "effect": "deal_damage",
                "source": "连环闪电",
                "target": "敌方随从",
                "amount": 4,
                "result": {
                    "damage_dealt": 4,
                    "target_health": 0,
                    "target_destroyed": true
                }
            },
            {
                "step": 2,
                "effect": "damage_reflection",
                "source": "反伤护甲",
                "target": "玩家",
                "amount": 1,
                "result": {
                    "damage_reduced": 1,
                    "actual_damage": 0,
                    "modifier": {
                        "source": "法术护盾",
                        "effect": "prevent_damage"
                    }
                }
            }
        ],
        "final_state": {
            "target": {
                "status": "destroyed",
                "equipment": {
                    "name": "反伤护甲",
                    "status": "destroyed"
                }
            },
            "player": {
                "health": "unchanged",
                "effects": {
                    "法术护盾": "triggered"
                }
            }
        }
    }
}
```

### 2.2 复杂状态效果

输入：
```
场上状态：
1. 玩家控制"元素使者"（攻击时，目标获得相应元素标记）
2. 目标已有"火焰标记"和"冰霜标记"
3. 场上有"元素共鸣"（当一个单位获得第三个元素标记时，造成3点伤害）
4. 玩家使用元素使者攻击，施加"闪电标记"

目标状态：
- 生命值：5
- 现有标记：火焰、冰霜
```

输出：
```json
{
    "status_effect_resolution": {
        "initial_action": {
            "type": "attack",
            "source": "元素使者",
            "target": "敌方随从",
            "effect": "apply_mark"
        },
        "mark_sequence": [
            {
                "step": 1,
                "action": "add_mark",
                "mark": "闪电标记",
                "target_marks": [
                    "火焰标记",
                    "冰霜标记",
                    "闪电标记"
                ]
            },
            {
                "step": 2,
                "trigger": "元素共鸣",
                "condition": "three_marks",
                "effect": {
                    "type": "damage",
                    "amount": 3,
                    "target": "marked_unit"
                }
            }
        ],
        "final_state": {
            "target": {
                "health": 2,
                "marks": [
                    "火焰标记",
                    "冰霜标记",
                    "闪电标记"
                ],
                "effects_received": [
                    "元素共鸣伤害"
                ]
            }
        }
    }
}
```

## 3. 特殊情况处理示例

### 3.1 死亡触发顺序

输入：
```
场上情况：
1. 玩家使用"毒云术"（对所有随从造成2点伤害）
2. 场上有以下随从：
   - "亡灵巫师"（死亡时抽一张牌）
   - "复仇战士"（死亡时对敌方英雄造成2点伤害）
   - "生命使者"（死亡时为所有者恢复2点生命）

所有随从生命值均为2
```

输出：
```json
{
    "death_trigger_resolution": {
        "initial_effect": {
            "spell": "毒云术",
            "damage": 2,
            "affected_units": [
                "亡灵巫师",
                "复仇战士",
                "生命使者"
            ]
        },
        "death_sequence": [
            {
                "step": 1,
                "unit": "亡灵巫师",
                "trigger": "death",
                "effect": {
                    "type": "draw",
                    "cards": 1,
                    "result": "success"
                }
            },
            {
                "step": 2,
                "unit": "复仇战士",
                "trigger": "death",
                "effect": {
                    "type": "damage",
                    "target": "enemy_hero",
                    "amount": 2,
                    "result": "damage_dealt"
                }
            },
            {
                "step": 3,
                "unit": "生命使者",
                "trigger": "death",
                "effect": {
                    "type": "heal",
                    "target": "owner",
                    "amount": 2,
                    "result": "health_restored"
                }
            }
        ],
        "final_state": {
            "player": {
                "hand_size": "+1",
                "health": "+2"
            },
            "opponent": {
                "health": "-2"
            },
            "board": {
                "cleared": true,
                "death_triggers": "all_resolved"
            }
        }
    }
}
```

### 3.2 资源上限处理

输入：
```
状态：
1. 玩家手牌数：9
2. 玩家触发"疯狂研究"（抽三张牌，每超出手牌上限一张，受到1点伤害）
3. 手牌上限：10

玩家状态：
- 生命值：15
- 牌库剩余：5张
```

输出：
```json
{
    "resource_limit_handling": {
        "trigger_effect": {
            "card": "疯狂研究",
            "effect": "draw_cards",
            "amount": 3
        },
        "resolution_steps": [
            {
                "step": 1,
                "action": "draw_cards",
                "cards_drawn": 3,
                "new_hand_size": 12,
                "excess": 2
            },
            {
                "step": 2,
                "action": "check_hand_limit",
                "limit": 10,
                "excess": 2,
                "consequence": {
                    "type": "damage",
                    "amount": 2,
                    "source": "card_excess"
                }
            },
            {
                "step": 3,
                "action": "discard_cards",
                "amount": 2,
                "selection": "random"
            }
        ],
        "final_state": {
            "player": {
                "health": 13,
                "hand_size": 10,
                "cards_discarded": 2
            },
            "deck": {
                "remaining": 2
            }
        }
    }
}
```

## 4. 高级游戏机制示例

### 4.1 条件触发连锁

输入：
```
场上状态：
1. 玩家控制"奥术增幅器"（当你施放法术时，复制该法术）
2. 玩家使用"魔力爆发"（对敌方英雄造成3点伤害，如果你本回合施放过法术，再造成2点伤害）
3. 本回合已施放一个法术

对手状态：
- 生命值：20
- 无防御效果
```

输出：
```json
{
    "conditional_chain_resolution": {
        "initial_spell": {
            "name": "魔力爆发",
            "base_effect": {
                "damage": 3,
                "conditional_damage": 2,
                "condition": "spell_cast_this_turn"
            }
        },
        "resolution_sequence": [
            {
                "step": 1,
                "effect": "check_condition",
                "condition": "spell_cast_this_turn",
                "result": true,
                "damage_modifier": "+2"
            },
            {
                "step": 2,
                "effect": "trigger_amplifier",
                "source": "奥术增幅器",
                "action": "copy_spell",
                "copy_details": {
                    "spell": "魔力爆发",
                    "inherits_conditions": true
                }
            },
            {
                "step": 3,
                "resolution": [
                    {
                        "spell": "原始魔力爆发",
                        "damage": 5,
                        "target": "enemy_hero"
                    },
                    {
                        "spell": "复制魔力爆发",
                        "damage": 5,
                        "target": "enemy_hero"
                    }
                ]
            }
        ],
        "final_state": {
            "opponent": {
                "initial_health": 20,
                "damage_taken": 10,
                "final_health": 10
            },
            "spells_resolved": 2,
            "conditions_checked": 1,
            "triggers_activated": 1
        }
    }
}
```

### 4.2 优先级冲突处理

输入：
```
同时触发的效果：
1. "时间扭曲"（回合结束时，获得一个额外回合）
2. "命运转轮"（回合结束时，交换双方生命值）
3. "终局预言"（回合结束时，如果任一玩家生命值低于10，游戏结束）

当前状态：
- 玩家生命值：8
- 对手生命值：25
```

输出：
```json
{
    "priority_conflict_resolution": {
        "trigger_timing": "end_of_turn",
        "effect_priority": {
            "rules": [
                {
                    "type": "game_ending_effects",
                    "priority": 1
                },
                {
                    "type": "state_changing_effects",
                    "priority": 2
                },
                {
                    "type": "turn_structure_effects",
                    "priority": 3
                }
            ]
        },
        "resolution_sequence": [
            {
                "step": 1,
                "effect": "终局预言",
                "check": {
                    "condition": "life_below_10",
                    "result": true,
                    "affected_player": "player"
                },
                "resolution": "game_end"
            },
            {
                "step": 2,
                "effect": "命运转轮",
                "action": "swap_life",
                "result": {
                    "player_new_health": 25,
                    "opponent_new_health": 8
                }
            },
            {
                "step": 3,
                "effect": "时间扭曲",
                "action": "grant_extra_turn",
                "result": "effect_queued"
            }
        ],
        "final_state": {
            "game_status": "ended",
            "winner": "opponent",
            "reason": "终局预言",
            "unresolved_effects": [
                "命运转轮",
                "时间扭曲"
            ]
        }
    }
}
```

## 5. 训练建议

### 5.1 数据准备
1. 覆盖各种复杂场景
2. 包含边界条件测试
3. 提供详细的状态变化
4. 记录完整的解决步骤

### 5.2 重点关注
1. 效果优先级处理
2. 条件判断逻辑
3. 状态更新准确性
4. 规则一致性维护

### 5.3 验证方法
1. 模拟实际对局
2. 测试极端情况
3. 检查规则冲突
4. 验证结果合理性

这些示例提供了：
1. 详细的场景描述
2. 完整的处理流程
3. 清晰的状态变化
4. 规则应用示范

您觉得这些示例如何？需要我补充其他类型的场景吗？
