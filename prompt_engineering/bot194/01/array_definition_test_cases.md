# 数组定义测试用例

#### 测试用例 1：创建数组
##### input.json
```json
{
    "input": "创建一个名为'resources'的数组，包含木材、石头、金币三种资源",
    "context": {
        "arrays": {}
    }
}
```

##### output.json
```json
{
    "updated_context": {
        "arrays": {
            "resources": ["wood", "stone", "gold"]
        }
    },
    "process": {
        "action": "create",
        "target": "resources",
        "details": "创建包含3个元素的数组"
    },
    "botstatus": true,
    "message": "资源数组创建成功",
    "dialogue": "我已经创建了包含木材、石头和金币的资源数组。"
}
```

#### 测试用例 2：添加元素
##### input.json
```json
{
    "input": "在resources数组中添加'iron'资源",
    "context": {
        "arrays": {
            "resources": ["wood", "stone", "gold"]
        }
    }
}
```

##### output.json
```json
{
    "updated_context": {
        "arrays": {
            "resources": ["wood", "stone", "gold", "iron"]
        }
    },
    "process": {
        "action": "add",
        "target": "resources",
        "details": "添加元素'iron'"
    },
    "botstatus": true,
    "message": "成功添加iron资源",
    "dialogue": "已将铁矿资源添加到资源列表中。"
}
```

#### 测试用例 3：删除元素
##### input.json
```json
{
    "input": "从resources数组中删除'stone'资源",
    "context": {
        "arrays": {
            "resources": ["wood", "stone", "gold", "iron"]
        }
    }
}
```

##### output.json
```json
{
    "updated_context": {
        "arrays": {
            "resources": ["wood", "gold", "iron"]
        }
    },
    "process": {
        "action": "remove",
        "target": "resources",
        "details": "删除元素'stone'"
    },
    "botstatus": true,
    "message": "成功删除stone资源",
    "dialogue": "已将石头资源从资源列表中移除。"
}
```

#### 测试用例 4：查询数组
##### input.json
```json
{
    "input": "查看resources数组的内容",
    "context": {
        "arrays": {
            "resources": ["wood", "gold", "iron"]
        }
    }
}
```

##### output.json
```json
{
    "updated_context": {
        "arrays": {
            "resources": ["wood", "gold", "iron"]
        }
    },
    "process": {
        "action": "query",
        "target": "resources",
        "details": "查询数组内容"
    },
    "botstatus": true,
    "message": "当前资源列表：wood, gold, iron",
    "dialogue": "目前的资源包括：木材、金币和铁矿。"
}
```

#### 测试用例 5：创建超长数组
##### input.json
```json
{
    "input": "创建一个包含150个数字的数组",
    "context": {
        "arrays": {}
    }
}
```

##### output.json
```json
{
    "updated_context": {
        "arrays": {}
    },
    "process": {
        "action": "create",
        "target": "numbers",
        "details": "尝试创建150个元素的数组"
    },
    "botstatus": false,
    "message": "数组长度超过最大限制(100)",
    "dialogue": "抱歉，出于性能考虑，数组长度不能超过100个元素。"
}
``` 