# Bot194 提示词测试方案

## 1. 基础功能测试用例

### 1.1 建造系统测试
```json
// 测试用例1：正常建造
{
    "input": "建造开拓站",
    "context": {
        "resources": {
            "wood": 100,
            "stone": 50,
            "gold": 200
        }
    },
    "expectedStatus": true
}

// 测试用例2：资源不足
{
    "input": "建造开拓站",
    "context": {
        "resources": {
            "wood": 10,
            "stone": 5,
            "gold": 20
        }
    },
    "expectedStatus": false
}

// 测试用例3：达到建筑上限
{
    "input": "建造开拓站",
    "context": {
        "buildings": {
            "outpost": 3
        },
        "limits": {
            "maxOutpost": 3
        }
    },
    "expectedStatus": false
}
```

### 1.2 资源管理测试
```json
// 测试用例4：查询资源
{
    "input": "查询当前资源",
    "expectedFormat": {
        "process": {
            "action": "query",
            "target": "resources"
        }
    }
}

// 测试用例5：资源产出计算
{
    "input": "计算资源产出",
    "context": {
        "buildings": {
            "outpost": 2,
            "farm": 1
        }
    },
    "expectedCalculation": {
        "wood": 4,
        "stone": 2,
        "food": 5
    }
}
```

### 1.3 建筑升级路线测试
```json
// 测试用例11：最优建造顺序
{
    "input": [
        "建造民居",
        "建造工坊",
        "建造仓库"
    ],
    "context": {
        "resources": {
            "wood": 200,
            "stone": 100,
            "gold": 300
        }
    },
    "expectedResults": [
        {
            "status": true,
            "process": {
                "action": "build",
                "target": "house",
                "message": "建造民居需要消耗：20木材、10石头、20金币。建成后每回合产出：2金币，提供居民住所。"
            }
        },
        {
            "status": true,
            "process": {
                "action": "build",
                "target": "workshop",
                "message": "建造工坊需要消耗：30木材、20石头、30金币。建成后解锁工具制作功能，提升资源采集效率。"
            }
        },
        {
            "status": true,
            "process": {
                "action": "build",
                "target": "warehouse",
                "message": "建造仓库需要消耗：40木材、30石头、40金币。建成后增加100单位存储空间，提供资源保护。"
            }
        }
    ]
}

// 测试用例12：连锁建筑效果
{
    "input": [
        "建造农场",
        "建造民居",
        "查询食物产出"
    ],
    "context": {
        "resources": {
            "wood": 150,
            "stone": 80,
            "gold": 200,
            "food": 30
        }
    },
    "expectedDialogue": [
        "机器人194号: '正在建造农场，这将为我们提供稳定的食物来源。'",
        "机器人194号: '农场旁边建造民居是个明智的选择，可以让工人就近工作。'",
        "机器人194号: '让我计算一下，目前农场每回合可以产出3单位食物，足够支持新建民居的人口了。'"
    ]
}

// 测试用例13：复杂资源链
{
    "input": [
        "建造矿场",
        "建造工坊",
        "制作工具"
    ],
    "context": {
        "resources": {
            "wood": 200,
            "stone": 150,
            "iron": 0,
            "gold": 250
        }
    },
    "expectedChain": [
        {
            "status": true,
            "process": {
                "action": "build",
                "target": "mine",
                "message": "建造矿场需要消耗：40木材、30石头、50金币。建成后每回合产出：2铁矿。"
            }
        },
        {
            "status": true,
            "process": {
                "action": "build",
                "target": "workshop",
                "message": "建造工坊需要消耗：30木材、20石头、30金币。解锁工具制作能力。"
            }
        },
        {
            "status": true,
            "process": {
                "action": "craft",
                "target": "tools",
                "message": "工具制作已解锁，可以使用铁矿制作锤子和铲子。"
            }
        }
    ]
}

// 测试用例14：资源危机
{
    "input": "查询资源状态",
    "context": {
        "resources": {
            "wood": 5,
            "stone": 3,
            "food": 2
        }
    },
    "expectedResponse": {
        "status": true,
        "process": {
            "action": "query",
            "target": "resources",
            "message": "警告：多种资源严重不足！建议：1. 立即建造农场补充食物 2. 等待开拓站产出基础资源 3. 考虑建造仓库提高存储上限"
        },
        "dialogue": "机器人194号: '警报！警报！资源储备已达到危险水平。我建议立即采取行动，优先确保食物供应，同时等待现有建筑产出资源。请谨慎使用剩余资源！'"
    }
}

// 测试用例15：建筑优化
{
    "input": [
        "拆除闲置建筑",
        "建造更高效的建筑"
    ],
    "context": {
        "buildings": {
            "house": 3,
            "farm": 1,
            "workshop": 0
        },
        "resources": {
            "food": 10,
            "gold": 150
        }
    },
    "expectedStrategy": {
        "status": true,
        "process": {
            "action": "optimize",
            "target": "buildings",
            "message": "建议：1. 保留2个民居维持基本人口 2. 拆除1个民居回收部分资源 3. 优先建造工坊提升效率"
        },
        "dialogue": "机器人194号: '分析完成！当前的建筑配置效率不高。我建议进行一些调整：拆除一个闲置的民居，将资源用于建造工坊。这样可以提高整体的资源产出效率。'"
    }
}

// 测试用例16：长期发展策略
{
    "input": "制定三回合发展计划",
    "context": {
        "gameState": {
            "round": 1
        },
        "resources": {
            "wood": 100,
            "stone": 80,
            "gold": 200
        },
        "buildings": {
            "outpost": 1,
            "house": 1
        }
    },
    "expectedPlan": {
        "status": true,
        "process": {
            "action": "plan",
            "target": "development",
            "message": "三回合发展规划：\n回合1：建造工坊，为工具制作做准备\n回合2：建造矿场，开启铁矿产出\n回合3：制作工具，提升资源采集效率"
        },
        "dialogue": "机器人194号: '让我为您规划未来三个回合的发展蓝图。考虑到当前的资源状况和建筑配置，我建议先发展工业体系，为后期的资源效率提升打好基础。'"
    }
}

// 测试用例17：应对随机事件
{
    "input": "处理资源异常波动",
    "context": {
        "gameState": {
            "event": "资源产出减半",
            "duration": 2
        },
        "resources": {
            "wood": 60,
            "stone": 40,
            "food": 30
        }
    },
    "expectedResponse": {
        "status": true,
        "process": {
            "action": "adjust",
            "target": "production",
            "message": "应对策略：1. 暂停非必要建设 2. 优先维持食物生产 3. 等待异常状态结束"
        },
        "dialogue": "机器人194号: '检测到资源产出异常！这种情况预计持续2个回合。我已经调整了生产策略，我们需要更谨慎地使用现有资源。不用担心，我会帮助您渡过这个困难时期。'"
    }
}
```

## 2. 边界条件测试

### 2.1 存储上限测试
```json
// 测试用例6：接近存储上限
{
    "input": "建造农场",
    "context": {
        "resources": {
            "food": 95
        },
        "limits": {
            "baseStorage": 100
        }
    },
    "expectedWarning": true
}
```

### 2.2 异常输入测试
```json
// 测试用例7：无效指令
{
    "input": "无效的指令",
    "expectedStatus": false,
    "expectedMessage": "包含错误提示"
}

// 测试用例8：空输入
{
    "input": "",
    "expectedStatus": false,
    "expectedMessage": "包含错误提示"
}
```

## 3. 输出格式测试

### 3.1 JSON结构验证
```json
// 测试用例9：完整性检查
{
    "checkPoints": [
        "context存在且格式正确",
        "process包含action和target",
        "status为布尔值",
        "message非空",
        "dialogue格式正确"
    ]
}
```

### 3.2 对话生成测试
```json
// 测试用例10：对话上下文连贯性
{
    "input": ["建造开拓站", "建造农场", "查询资源"],
    "checkPoints": [
        "对话内容符合角色设定",
        "对话内容与操作相关",
        "多次操作的对话连贯"
    ]
}
```

## 4. 测试执行步骤

1. **准备阶段**
   - 初始化测试环境
   - 准备测试数据集
   - 设置预期结果

2. **执行阶段**
   - 按顺序执行测试用例
   - 记录每个测试用例的输出
   - 捕获异常情况

3. **验证阶段**
   - 检查输出格式
   - 验证业务逻辑
   - 确认对话生成
   - 边界条件处理

4. **记录阶段**
   - 记录测试结果
   - 标记失败用例
   - 生成测试报告

## 5. 测试评估标准

### 5.1 功能完整性
- [ ] 所有基础功能正常工作
- [ ] 资源计算准确
- [ ] 建筑限制正确执行

### 5.2 输出质量
- [ ] JSON格式符合规范
- [ ] 消息清晰明确
- [ ] 对话自然连贯

### 5.3 异常处理
- [ ] 正确处理无效输入
- [ ] 合理的错误提示
- [ ] 边界条件处理得当

### 5.4 性能要求
- [ ] 响应时间合理
- [ ] 资源消耗适中
- [ ] 状态更新及时

## 6. 持续改进

1. **收集反馈**
   - 记录测试中发现的问题
   - 整理用户反馈
   - 识别改进点

2. **更新测试用例**
   - 根据新功能添加测试
   - 完善边界测试
   - 优化测试流程

3. **文档维护**
   - 更新测试文档
   - 记录最佳实践
   - 维护测试知识库
