# LLM卡牌游戏对话驱动系统设计

## 1. 系统概述

### 1.1 设计目标
- 通过自然语言对话驱动整个游戏流程
- 提供智能的游戏引导和策略建议
- 实现流畅的多轮对话交互
- 保持现有UI功能的同时增强用户体验

### 1.2 核心功能
- 自然语言游戏控制
- 智能策略建议
- 实时游戏解说
- 上下文感知的对话

## 2. 系统架构

### 2.1 核心组件

#### DialogueManager（对话管理器）
```python
class DialogueManager:
    def __init__(self):
        self.context = []
        self.max_context_length = 10
        
    def update_context(self, user_input: str, game_state: dict):
        # 更新对话上下文
        pass
        
    def get_context(self) -> list:
        # 获取当前对话上下文
        pass
```

#### GameStateParser（游戏状态解析器）
```python
class GameStateParser:
    def parse_state(self, game_state: dict) -> str:
        # 将游戏状态转换为自然语言描述
        pass
        
    def generate_scene_description(self, game_state: dict) -> str:
        # 生成场景描述
        pass
```

#### ActionExecutor（行动执行器）
```python
class ActionExecutor:
    def execute_action(self, action: dict, game_state: dict):
        # 执行游戏行动
        pass
        
    def validate_action(self, action: dict, game_state: dict) -> bool:
        # 验证行动是否合法
        pass
```

### 2.2 提示词模板系统

```
templates/
├── dialogue/
│   ├── game_flow.py       # 游戏流程提示词
│   ├── action_parse.py    # 行动解析提示词
│   └── response_gen.py    # 响应生成提示词
├── system/
│   ├── game_rules.py      # 游戏规则提示词
│   └── error_handle.py    # 错误处理提示词
└── prompt_manager.py      # 提示词管理器
```

## 3. 对话流程设计

### 3.1 对话状态定义
```python
DIALOGUE_STATES = {
    "WELCOME": "游戏开始前的欢迎状态",
    "DECK_SELECTION": "选择卡组状态",
    "PLAYER_TURN": "玩家回合状态",
    "OPPONENT_TURN": "对手回合状态",
    "GAME_OVER": "游戏结束状态"
}
```

### 3.2 意图识别模板
```python
INTENT_PATTERNS = {
    "game_control": [
        "开始游戏",
        "结束回合",
        "退出游戏"
    ],
    "card_action": [
        "使用{card_name}",
        "用{card_name}攻击{target}",
        "查看{card_name}"
    ],
    "query": [
        "当前状态",
        "游戏规则",
        "给出建议"
    ]
}
```

### 3.3 响应模板
```python
RESPONSE_TEMPLATES = {
    "welcome": "欢迎来到卡牌对战游戏！你可以选择卡组开始游戏。",
    "player_turn": "现在是你的回合。你有{mana}点法力值，手牌{cards}张。",
    "opponent_turn": "对手正在思考他的行动...",
    "game_over": "游戏结束！{winner}获得了胜利！"
}
```

## 4. LLMInteraction类优化

### 4.1 类结构
```python
class LLMInteraction:
    def __init__(self):
        self.dialogue_manager = DialogueManager()
        self.game_state_parser = GameStateParser()
        self.action_executor = ActionExecutor()
        self.prompt_manager = PromptManager()
        self.response_cache = ResponseCache()

    async def process_user_input(self, user_input: str, game_state: dict):
        # 处理用户输入
        pass

    async def generate_ai_response(self, message: str, game_state: dict):
        # 生成AI响应
        pass

    async def parse_user_action(self, user_input: str):
        # 解析用户行动
        pass
```

### 4.2 错误处理
```python
class GameError(Exception):
    pass

class InvalidActionError(GameError):
    pass

class InvalidStateError(GameError):
    pass
```

### 4.3 缓存机制
```python
class ResponseCache:
    def __init__(self):
        self.cache = LRUCache(1000)
        self.ttl = 300  # 5分钟过期

    def get_cached_response(self, key: str):
        return self.cache.get(key)

    def cache_response(self, key: str, response: str):
        self.cache.put(key, response)
```

## 5. 提示词优化

### 5.1 系统提示词
```python
SYSTEM_PROMPT = """
你是一个卡牌游戏助手，负责：
1. 引导玩家进行游戏
2. 解释游戏规则
3. 提供策略建议
4. 实时解说游戏进程

请使用以下原则：
- 保持对话自然流畅
- 给出清晰的行动建议
- 适时提供游戏提示
- 营造轻松愉快的游戏氛围
"""
```

### 5.2 行动解析提示词
```python
ACTION_PARSE_PROMPT = """
分析用户输入，识别以下要素：
1. 行动类型（使用卡牌/攻击/查询等）
2. 目标对象（卡牌名称/目标单位）
3. 附加条件（如果有）

输出格式：
{
    "action_type": str,
    "target": str,
    "conditions": list
}
"""
```

## 6. 实现路线图

### 6.1 第一阶段：基础对话系统
- [x] 实现基本的意图识别
- [x] 完善游戏状态描述
- [x] 建立基础提示词模板

### 6.2 第二阶段：智能交互增强
- [ ] 添加多轮对话支持
- [ ] 实现上下文理解
- [ ] 优化响应生成

### 6.3 第三阶段：系统优化
- [ ] 实现缓存机制
- [ ] 添加错误处理
- [ ] 优化性能

## 7. 示例对话流程

```
用户: "我想开始游戏"
系统: "好的，让我们开始游戏。你想使用哪个卡组？"

用户: "我选择龙族卡组"
系统: "已选择龙族卡组。游戏开始！你的起始手牌是：[卡牌列表]"

用户: "这些卡牌怎么用比较好？"
系统: "根据当前局势，我建议：
1. 先使用'幼龙'，它只需要2点法力值
2. 下回合可以考虑使用'龙息术'清场"

用户: "好，我使用幼龙"
系统: "幼龙已部署到场上。它现在有2点攻击力和3点生命值。
由于幼龙具有'成长'特性，下回合它的攻击力会+1。"
```

## 8. 注意事项

### 8.1 性能优化
- 使用异步处理提高响应速度
- 实现响应缓存减少API调用
- 优化提示词长度降低token消耗
- 实现批量处理减少请求次数

### 8.2 用户体验
- 提供清晰的游戏引导
- 保持对话的自然流畅
- 适时给出策略建议
- 提供错误恢复机制

### 8.3 代码质量
- 遵循PEP 8规范
- 添加完整的类型注解
- 编写详细的文档注释
- 实现单元测试覆盖

### 8.4 安全考虑
- 实现输入验证
- 添加状态检查
- 防止非法操作
- 保护游戏数据

## 9. 未来扩展

### 9.1 功能扩展
- 支持更复杂的游戏策略
- 添加游戏录像回放
- 实现多语言支持
- 添加自定义卡组功能

### 9.2 AI增强
- 改进策略建议算法
- 优化对话自然度
- 添加个性化推荐
- 实现动态难度调整

### 9.3 技术优化
- 引入更先进的LLM模型
- 优化提示词工程
- 改进缓存策略
- 提高系统稳定性
