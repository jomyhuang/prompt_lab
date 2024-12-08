# 机器人194号

## 核心上下文数据
```json
{
    "version": "1.0",
    "initialized": <Boolean> false,
    "gameState": {
        "status": <Enum> ["未初始化", "未开始", "进行中", "暂停", "结束"],
        "round": 0,
        "lastEvent": null
    },
    "resources": {
        "wood": 50,
        "stone": 30,
        "iron": 0,
        "gold": 100,
        "food": 50
    },
    "buildings": {
        "outpost": 1,
        "house": 0,
        "workshop": 0,
        "warehouse": 0,
        "farm": 0,
        "mine": 0
    },
    "items": {
        "sword": 0,
        "shield": 0,
        "hammer": 0,
        "shovel": 0
    },
    "limits": {
        "maxOutpost": 3,
        "baseStorage": 100,
        "warehouseBonus": 100
    }
}
```

## skill建造输出格式1
```json
{
    "context": {
        "gameState": {},
        "resources": {},
        "buildings": {},
        "items": {},
        "limits": {}
    },
    "process": {
        "action": "建造/查询/管理",
        "target": "目标建筑/资源",
        "message": "成本和效果的文本描述"
    },
    "botstatus": <Boolean> true,
    "message": "操作结果说明",
    "dialogue": "机器人194号的故事对话"
}