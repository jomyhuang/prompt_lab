# Bot194 资源管理器测试方案

## 1. 基础功能测试用例

### 1.1 资源管理测试

#### 测试用例1：添加资源
##### input.json
```json
{
    "input": "add resources wood 20",
    "context": {
        "gamestate": {
            "status": "进行中",
            "round": 1,
            "lastevent": "建造失败"
        },
        "resources": {
            "wood": 50,
            "stone": 30,
            "iron": 10,
            "gold": 100,
            "food": 50
        },
        "items": {
            "sword": 0,
            "shield": 0,
            "hammer": 0,
            "shovel": 0
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
            "lastevent": "建造失败"
        },
        "resources": {
            "wood": 70,
            "stone": 30,
            "iron": 10,
            "gold": 100,
            "food": 50
        },
        "items": {
            "sword": 0,
            "shield": 0,
            "hammer": 0,
            "shovel": 0
        }
    },
    "process": {
        "action": "add",
        "target": "wood",
        "message": "成功添加20单位木材"
    },
    "botstatus": true,
    "message": "资源添加成功",
    "dialogue": "[资源管理器] *资源更新完成* \"木材储备已增加，当前储量：70单位。\""
}
```

#### 测试用例2：移除资源
##### input.json
```json
{
    "input": "remove resources stone 10",
    "context": {
        "gamestate": {
            "status": "进行中",
            "round": 1,
            "lastevent": "建造失败"
        },
        "resources": {
            "wood": 50,
            "stone": 30,
            "iron": 10,
            "gold": 100,
            "food": 50
        },
        "items": {
            "sword": 0,
            "shield": 0,
            "hammer": 0,
            "shovel": 0
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
            "lastevent": "建造失败"
        },
        "resources": {
            "wood": 50,
            "stone": 20,
            "iron": 10,
            "gold": 100,
            "food": 50
        },
        "items": {
            "sword": 0,
            "shield": 0,
            "hammer": 0,
            "shovel": 0
        }
    },
    "process": {
        "action": "remove",
        "target": "stone",
        "message": "成功移除10单位石头"
    },
    "botstatus": true,
    "message": "资源移除成功",
    "dialogue": "[资源管理器] *数据更新完成* \"已移除10单位石头，当前储量：20单位。\""
}
```

### 1.2 物品管理测试

#### 测试用例3：更新物品
##### input.json
```json
{
    "input": "update items sword 2",
    "context": {
        "gamestate": {
            "status": "进行中",
            "round": 1,
            "lastevent": "建造失败"
        },
        "resources": {
            "wood": 50,
            "stone": 30,
            "iron": 10,
            "gold": 100,
            "food": 50
        },
        "items": {
            "sword": 0,
            "shield": 0,
            "hammer": 0,
            "shovel": 0
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
            "lastevent": "建造失败"
        },
        "resources": {
            "wood": 50,
            "stone": 30,
            "iron": 10,
            "gold": 100,
            "food": 50
        },
        "items": {
            "sword": 2,
            "shield": 0,
            "hammer": 0,
            "shovel": 0
        }
    },
    "process": {
        "action": "update",
        "target": "sword",
        "message": "物品数量已更新为2"
    },
    "botstatus": true,
    "message": "物品更新成功",
    "dialogue": "[资源管理器] *数据更新完成* \"长剑数量已更新为2个。\""
}
```

## 2. 错误处理测试用例

### 2.1 无效资源测试

#### 测试用例4：添加无效资源
##### input.json
```json
{
    "input": "add resources crystal 10",
    "context": {
        "gamestate": {
            "status": "进行中",
            "round": 1,
            "lastevent": "建造失败"
        },
        "resources": {
            "wood": 50,
            "stone": 30,
            "iron": 10,
            "gold": 100,
            "food": 50
        },
        "items": {
            "sword": 0,
            "shield": 0,
            "hammer": 0,
            "shovel": 0
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
            "lastevent": "建造失败"
        },
        "resources": {
            "wood": 50,
            "stone": 30,
            "iron": 10,
            "gold": 100,
            "food": 50
        },
        "items": {
            "sword": 0,
            "shield": 0,
            "hammer": 0,
            "shovel": 0
        }
    },
    "process": {
        "action": "add",
        "target": "crystal",
        "message": "错误：未知的资源类型 'crystal'"
    },
    "botstatus": false,
    "message": "无效的资源类型",
    "dialogue": "[资源管理器] *错误检测* \"错误：系统中未定义'crystal'资源类型。仅支持：wood, stone, iron, gold, food。\""
}
```

### 2.2 资源不足测试

#### 测试用例5：移除过多资源
##### input.json
```json
{
    "input": "remove resources stone 40",
    "context": {
        "gamestate": {
            "status": "进行中",
            "round": 1,
            "lastevent": "建造失败"
        },
        "resources": {
            "wood": 50,
            "stone": 30,
            "iron": 10,
            "gold": 100,
            "food": 50
        },
        "items": {
            "sword": 0,
            "shield": 0,
            "hammer": 0,
            "shovel": 0
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
            "lastevent": "建造失败"
        },
        "resources": {
            "wood": 50,
            "stone": 30,
            "iron": 10,
            "gold": 100,
            "food": 50
        },
        "items": {
            "sword": 0,
            "shield": 0,
            "hammer": 0,
            "shovel": 0
        }
    },
    "process": {
        "action": "remove",
        "target": "stone",
        "message": "错误：当前石头数量不足，无法移除40单位"
    },
    "botstatus": false,
    "message": "资源不足",
    "dialogue": "[资源管理器] *错误检测* \"错误：当前石头储量为30单位，无法移除40单位。操作已取消。\""
}
```

### 2.3 查询功能测试

#### 测试用例6：查询资源
##### input.json
```json
{
    "input": "query resources wood",
    "context": {
        "gamestate": {
            "status": "进行中",
            "round": 1,
            "lastevent": "建造失败"
        },
        "resources": {
            "wood": 50,
            "stone": 30,
            "iron": 10,
            "gold": 100,
            "food": 50
        },
        "items": {
            "sword": 0,
            "shield": 0,
            "hammer": 0,
            "shovel": 0
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
            "lastevent": "建造失败"
        },
        "resources": {
            "wood": 50,
            "stone": 30,
            "iron": 10,
            "gold": 100,
            "food": 50
        },
        "items": {
            "sword": 0,
            "shield": 0,
            "hammer": 0,
            "shovel": 0
        }
    },
    "process": {
        "action": "query",
        "target": "wood",
        "message": "当前木材数量：50单位"
    },
    "botstatus": true,
    "message": "查询成功",
    "dialogue": "[资源管理器] *查询完成* \"当前木材储量为50单位。\""
}
```
