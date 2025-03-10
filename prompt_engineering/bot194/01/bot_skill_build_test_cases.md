# Bot194 提示词测试方案

## 1. 基础功能测试用例

### 1.1 建造系统测试

#### 测试用例1：正常建造
##### input.json
```json
{
    "input": "建造开拓站",
    "context": {
        "resources": {
            "wood": 100,
            "stone": 50,
            "gold": 200
        },
        "buildings": {
            "outpost": 0
        }
    }
}
```

##### output.json
```json
{
    "updated_context": {
        "gamestate": {
            "status": "进行中",
            "round": 1,
            "lastevent": "建造开拓站"
        },
        "resources": {
            "wood": 70,
            "stone": 30,
            "gold": 150
        },
        "buildings": {
            "outpost": 1
        }
    },
    "process": {
        "action": "建造",
        "target": "开拓站",
        "message": "消耗木材30,石头20,金币50"
    },
    "botstatus": true,
    "message": "开拓站建造成功",
    "dialogue": "新的开拓站已经建好了,这将扩大我们的影响力!"
}
```

#### 测试用例2：资源不足
##### input.json
```json
{
    "input": "建造开拓站",
    "context": {
        "resources": {
            "wood": 10,
            "stone": 5,
            "gold": 20
        }
    }
}
```

##### output.json
```json
{
    "updated_context": {
        "gamestate": {
            "status": "进行中",
            "round": 1,
            "lastevent": "建造开拓站"
        },
        "resources": {
            "wood": 10,
            "stone": 5,
            "gold": 20
        }
    },
    "process": {
        "action": "建造",
        "target": "开拓站",
        "message": "资源不足,需要:消耗木材30,石头20,金币50"
    },
    "botstatus": false,
    "message": "资源不足,无法建造",
    "dialogue": "抱歉,当前资源储备不足以建造开拓站。请先收集更多资源。"
}
```

#### 测试用例3：达到建筑上限
##### input.json
```json
{
    "input": "建造开拓站",
    "context": {
        "resources": {
            "wood": 100,
            "stone": 50,
            "gold": 200
        },
        "buildings": {
            "outpost": 3
        },
        "limits": {
            "maxOutpost": 3
        }
    }
}
```

##### output.json
```json
{
    "updated_context": {
        "gamestate": {
            "status": "进行中",
            "round": 1,
            "lastevent": "建造开拓站"
        },
        "resources": {
            "wood": 100,
            "stone": 50,
            "gold": 200
        },
        "buildings": {
            "outpost": 3
        },
        "limits": {
            "maxOutpost": 3
        }
    },
    "process": {
        "action": "建造",
        "target": "开拓站",
        "message": "已达到开拓站数量上限(3/3)"
    },
    "botstatus": false,
    "message": "无法建造：已达到开拓站数量上限",
    "dialogue": "[机器人194号] *系统发出警告声* \"指挥官，我们已经达到了开拓站的最大数量限制。建议考虑其他类型的建筑。\""
}
```

### 1.2 资源管理测试

#### 测试用例4：查询资源
##### input.json
```json
{
    "input": "查询资源状态",
    "context": {
        "resources": {
            "wood": 100,
            "stone": 50,
            "iron": 20,
            "gold": 200,
            "food": 150
        }
    }
}
```

##### output.json
```json
{
    "updated_context": {
        "resources": {
            "wood": 100,
            "stone": 50,
            "iron": 20,
            "gold": 200,
            "food": 150
        }
    },
    "process": {
        "action": "查询",
        "target": "资源",
        "message": "当前资源储备情况"
    },
    "botstatus": true,
    "message": "资源查询成功",
    "dialogue": "当前资源储备:\n- 木材: 100\n- 石头: 50\n- 铁矿: 20\n- 金币: 200\n- 食物: 150"
}
```

## 2. 测试验证重点

### 2.1 输入验证
1. 指令格式正确性
2. 上下文数据完整性
3. 参数类型合法性

### 2.2 输出验证
1. 返回格式符合规范
2. 状态变更正确性
3. 资源计算准确性
4. 对话内容合理性

### 2.3 边界条件测试
1. 资源为零或不足
2. 达到建筑上限
3. 非法操作处理
4. 异常状态恢复
