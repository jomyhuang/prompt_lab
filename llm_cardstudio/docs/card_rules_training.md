# 卡牌规则训练数据集

## 1. 基础卡牌规则示例

### 1.1 生物卡牌

输入：
```
卡牌类型：生物
费用：3
名称：烈焰战士
属性：3攻击力/2生命值
效果：战吼：对一个敌方随从造成2点伤害
```

输出：
```json
{
    "card_type": "creature",
    "cost": 3,
    "name": "烈焰战士",
    "stats": {
        "attack": 3,
        "health": 2
    },
    "effects": [
        {
            "type": "battlecry",
            "effect": "damage",
            "target": "enemy_creature",
            "value": 2
        }
    ],
    "rule_text": "当你使用此卡牌时，选择一个敌方随从，对其造成2点伤害。",
    "resolution_steps": [
        "1. 支付3点法力值",
        "2. 将烈焰战士放置到战场",
        "3. 触发战吼效果",
        "4. 选择一个敌方随从作为目标",
        "5. 造成2点伤害"
    ]
}
```

### 1.2 法术卡牌

输入：
```
卡牌类型：法术
费用：4
名称：火球术
效果：造成6点伤害，如果目标是随从，则改为造成8点伤害
```

输出：
```json
{
    "card_type": "spell",
    "cost": 4,
    "name": "火球术",
    "effects": [
        {
            "type": "damage",
            "target": "any",
            "value": 6,
            "condition": null
        },
        {
            "type": "damage",
            "target": "creature",
            "value": 2,
            "condition": {
                "target_type": "creature"
            }
        }
    ],
    "rule_text": "对任意目标造成6点伤害。如果目标是随从，则改为造成8点伤害。",
    "resolution_steps": [
        "1. 支付4点法力值",
        "2. 选择目标",
        "3. 检查目标类型",
        "4. 计算并造成伤害"
    ]
}
```

## 2. 进阶卡牌规则示例

### 2.1 连锁效果卡牌

输入：
```
卡牌类型：生物
费用：5
名称：连环法师
属性：4攻击力/3生命值
效果：战吼：造成2点伤害。如果该伤害消灭了目标，则重复此效果。
```

输出：
```json
{
    "card_type": "creature",
    "cost": 5,
    "name": "连环法师",
    "stats": {
        "attack": 4,
        "health": 3
    },
    "effects": [
        {
            "type": "battlecry",
            "effect": "damage",
            "target": "any",
            "value": 2,
            "chain_condition": {
                "type": "target_destroyed",
                "action": "repeat_effect"
            }
        }
    ],
    "rule_text": "战吼：造成2点伤害。如果该伤害消灭了目标，则重复此效果。",
    "resolution_steps": [
        "1. 支付5点法力值",
        "2. 将连环法师放置到战场",
        "3. 触发战吼效果",
        "4. 选择目标",
        "5. 造成2点伤害",
        "6. 检查目标是否被消灭",
        "7. 如果目标被消灭，重复步骤4-6"
    ]
}
```

### 2.2 状态效果卡牌

输入：
```
卡牌类型：法术
费用：3
名称：寒冰诅咒
效果：冻结一个随从。在其解冻时，对其造成3点伤害。
```

输出：
```json
{
    "card_type": "spell",
    "cost": 3,
    "name": "寒冰诅咒",
    "effects": [
        {
            "type": "freeze",
            "target": "creature",
            "duration": 1
        },
        {
            "type": "damage",
            "target": "affected_creature",
            "value": 3,
            "trigger": {
                "type": "on_unfreeze",
                "target": "self"
            }
        }
    ],
    "rule_text": "冻结一个随从。在其解冻时，对其造成3点伤害。",
    "resolution_steps": [
        "1. 支付3点法力值",
        "2. 选择目标随从",
        "3. 施加冻结效果",
        "4. 添加解冻触发器",
        "5. 在解冻时造成伤害"
    ]
}
```

## 3. 复杂卡牌规则示例

### 3.1 多重触发卡牌

输入：
```
卡牌类型：生物
费用：6
名称：元素编织者
属性：5攻击力/5生命值
效果：在你施放一个法术后，获得+1/+1。在回合结束时，如果本回合获得过3次或以上增益，对所有敌方随从造成2点伤害。
```

输出：
```json
{
    "card_type": "creature",
    "cost": 6,
    "name": "元素编织者",
    "stats": {
        "attack": 5,
        "health": 5
    },
    "effects": [
        {
            "type": "buff",
            "trigger": {
                "type": "on_spell_cast",
                "source": "friendly"
            },
            "effect": {
                "type": "stat_change",
                "attack": 1,
                "health": 1
            }
        },
        {
            "type": "damage",
            "trigger": {
                "type": "end_of_turn",
                "condition": {
                    "type": "buff_count",
                    "value": 3,
                    "operator": "greater_or_equal"
                }
            },
            "target": "all_enemy_creatures",
            "value": 2
        }
    ],
    "rule_text": "在你施放一个法术后，获得+1/+1。在回合结束时，如果本回合获得过3次或以上增益，对所有敌方随从造成2点伤害。",
    "resolution_steps": [
        "1. 支付6点法力值",
        "2. 将元素编织者放置到战场",
        "3. 设置法术施放监听器",
        "4. 设置回合结束监听器",
        "5. 记录增益次数",
        "6. 在回合结束时检查条件并处理效果"
    ]
}
```

### 3.2 条件选择卡牌

输入：
```
卡牌类型：法术
费用：4
名称：元素召唤
效果：选择一项：召唤两个2/2的火元素；或者召唤一个4/4的水元素并抽一张牌；或者召唤一个3/3的风元素，使其获得冲锋。
```

输出：
```json
{
    "card_type": "spell",
    "cost": 4,
    "name": "元素召唤",
    "effects": [
        {
            "type": "choice",
            "options": [
                {
                    "type": "summon",
                    "token": {
                        "name": "火元素",
                        "attack": 2,
                        "health": 2
                    },
                    "count": 2
                },
                {
                    "type": "multi_effect",
                    "effects": [
                        {
                            "type": "summon",
                            "token": {
                                "name": "水元素",
                                "attack": 4,
                                "health": 4
                            },
                            "count": 1
                        },
                        {
                            "type": "draw",
                            "count": 1
                        }
                    ]
                },
                {
                    "type": "summon",
                    "token": {
                        "name": "风元素",
                        "attack": 3,
                        "health": 3,
                        "keywords": ["charge"]
                    },
                    "count": 1
                }
            ]
        }
    ],
    "rule_text": "选择一项：召唤两个2/2的火元素；或者召唤一个4/4的水元素并抽一张牌；或者召唤一个3/3的风元素，使其获得冲锋。",
    "resolution_steps": [
        "1. 支付4点法力值",
        "2. 显示选项列表",
        "3. 等待玩家选择",
        "4. 根据选择执行相应效果"
    ]
}
```

## 4. 特殊机制卡牌示例

### 4.1 转化卡牌

输入：
```
卡牌类型：生物
费用：2
名称：见习变形师
属性：2攻击力/2生命值
效果：在你的回合开始时，此随从随机变形成为一个法力值消耗增加1的随从。
```

输出：
```json
{
    "card_type": "creature",
    "cost": 2,
    "name": "见习变形师",
    "stats": {
        "attack": 2,
        "health": 2
    },
    "effects": [
        {
            "type": "transform",
            "trigger": {
                "type": "start_of_turn",
                "condition": {
                    "owner": "self"
                }
            },
            "target": "self",
            "transform_rule": {
                "type": "random_creature",
                "cost_modifier": 1,
                "cost_operation": "add"
            }
        }
    ],
    "rule_text": "在你的回合开始时，此随从随机变形成为一个法力值消耗增加1的随从。",
    "resolution_steps": [
        "1. 在回合开始时触发",
        "2. 获取可变形目标池",
        "3. 随机选择目标",
        "4. 执行变形效果"
    ]
}
```

### 4.2 连环任务卡牌

输入：
```
卡牌类型：法术
费用：1
名称：元素掌控
效果：任务：在一回合内施放3个法术。奖励：将一张"元素风暴"置入你的手牌。
元素风暴：对所有敌人造成等同于你本局游戏已施放法术数量的伤害。
```

输出：
```json
{
    "card_type": "spell",
    "subtype": "quest",
    "cost": 1,
    "name": "元素掌控",
    "effects": [
        {
            "type": "quest",
            "condition": {
                "type": "cast_spell",
                "count": 3,
                "timeframe": "single_turn"
            },
            "reward": {
                "type": "add_to_hand",
                "card": {
                    "name": "元素风暴",
                    "type": "spell",
                    "effect": {
                        "type": "damage",
                        "target": "all_enemies",
                        "value": {
                            "type": "dynamic",
                            "source": "spells_cast_count",
                            "timeframe": "game"
                        }
                    }
                }
            }
        }
    ],
    "rule_text": "任务：在一回合内施放3个法术。\n奖励：将一张"元素风暴"置入你的手牌。\n元素风暴：对所有敌人造成等同于你本局游戏已施放法术数量的伤害。",
    "resolution_steps": [
        "1. 支付1点法力值",
        "2. 创建任务追踪器",
        "3. 监听法术施放事件",
        "4. 检查完成条件",
        "5. 完成时发放奖励"
    ]
}
```

## 5. 训练数据使用指南

### 5.1 数据格式说明
1. 输入格式：使用自然语言描述卡牌
2. 输出格式：结构化JSON数据
3. 包含规则文本和执行步骤

### 5.2 训练建议
1. 确保覆盖各种卡牌类型
2. 包含简单到复杂的效果
3. 注意边界情况
4. 保持描述的一致性

### 5.3 验证方法
1. 检查JSON格式正确性
2. 验证规则解析准确性
3. 测试效果执行流程
4. 确认文本生成质量

这些训练数据：
1. 涵盖了多种卡牌类型
2. 包含了各种复杂度的效果
3. 提供了详细的解析示例
4. 保持了格式的一致性

您觉得这些训练数据如何？需要我补充其他类型的示例吗？
