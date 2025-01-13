# LLM Card Studio (智能卡牌游戏开发工作室)

基于大语言模型的智能卡牌游戏开发平台，集成了游戏设计、开发和测试的完整工具链。

## 核心特性

### 1. LLM 命令交互系统
- 智能命令解析与执行
  - 自然语言指令处理
  - 多轮对话管理
  - 上下文感知
- 多模型支持与切换
  - OpenAI (GPT-3.5/4)
  - Claude-3
  - 国内模型支持
- 自然语言游戏规则解释
  - 动态规则查询
  - 情境相关提示
  - 多语言支持
- 动态规则调整
  - 实时规则修改
  - 平衡性调整
  - 自定义规则验证

### 2. 游戏管理系统
- 完整的游戏状态管理
  - 回合制系统
  - 资源管理
  - 事件系统
- 回合制对战系统
  - 多玩家支持
  - AI对手
  - 联机对战
- 卡牌效果处理器
  - 效果链处理
  - 触发器系统
  - 状态追踪
- 存档管理功能
  - 自动存档
  - 进度恢复
  - 对战记录

### 3. GUI 界面
- 基于 Streamlit 的现代界面
  - 响应式设计
  - 主题定制
  - 多设备支持
- 实时游戏状态展示
  - 资源面板
  - 卡牌展示
  - 效果动画
- 卡牌操作可视化
  - 拖放操作
  - 卡牌预览
  - 效果提示
- 对战记录回放
  - 回合重放
  - 关键时刻标记
  - 数据分析

## 核心模块说明

### 游戏引擎 (game_manager.py)
```python
class GameManager:
    def __init__(self):
        # 游戏核心初始化
        self.state = GameState()
        self.players = PlayerManager()
        self.effects = EffectProcessor()

    def process_turn(self):
        # 回合处理逻辑
        pass
```

### LLM交互系统 (llm_interaction.py)
```python
class LLMInteraction:
    def __init__(self):
        # LLM服务初始化
        self.model = ModelConfig()
        self.history = MessageHistory()

    async def process_command(self, command):
        # 命令处理逻辑
        pass
```

### 提示词处理 (pe_commands.py)
```python
class CommandProcessor:
    def __init__(self):
        # 命令处理器初始化
        self.templates = PromptTemplates()
        self.validator = CommandValidator()

    def execute(self, command):
        # 命令执行逻辑
        pass
```

## 配置说明

### 1. 环境配置
创建 `.env` 文件:
```env
OPENAI_API_KEY=你的API密钥
MODEL_NAME=选用的模型
GAME_MODE=standard/custom
DEBUG_LEVEL=info/debug
```

### 2. 卡牌配置 (cards.json)
```json
{
  "card_id": {
    "name": "卡牌名称",
    "type": "卡牌类型",
    "cost": "能量消耗",
    "effect": {
      "type": "效果类型",
      "value": "效果数值",
      "conditions": ["触发条件"],
      "targets": ["目标选择"]
    }
  }
}
```

### 3. 卡组配置 (decks.json)
```json
{
  "deck_id": {
    "name": "卡组名称",
    "cards": ["card_id_1", "card_id_2"],
    "restrictions": {
      "min_cards": 40,
      "max_cards": 60
    }
  }
}
```

## 开发指南

### 1. 添加新卡牌
1. 在 `cards.json` 中定义卡牌属性
2. 实现卡牌效果处理器
   ```python
   @effect_processor.register
   def process_effect(card, target):
       # 效果处理逻辑
       pass
   ```
3. 添加对应的测试用例
4. 更新游戏平衡性文档

### 2. 自定义游戏规则
1. 修改 `game_manager.py` 中的规则定义
2. 更新 LLM 提示词模板
3. 测试新规则的交互效果

### 3. 界面开发
1. 组件开发
   ```python
   def render_card(card):
       st.container():
           # 卡牌渲染逻辑
           pass
   ```
2. 事件处理
3. 状态更新

## 测试驱动开发

### 1. 单元测试
```bash
python -m pytest tests/unit/
```

### 2. 集成测试
```bash
python -m pytest tests/integration/
```

### 3. 性能测试
```bash
python benchmarks/run.py
```

## 注意事项

1. API 使用
   - 确保 API 密钥配置正确
   - 监控 API 使用量
   - 实现请求重试机制

2. 游戏开发
   - 定期备份游戏存档
   - 遵循测试驱动开发流程
   - 保持代码文档的同步更新

3. 性能优化
   - 缓存常用数据
   - 优化 LLM 调用
   - 减少不必要的状态更新

## 更新日志

### v1.0.0 (2024-03)
- 完整的游戏核心功能
- 多模型支持
- GUI 界面实现

### v0.9.0 (2024-02)
- Beta 测试版本
- 基础功能完善
- 文档更新

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交变更
4. 发起 Pull Request

## 许可证

MIT License
