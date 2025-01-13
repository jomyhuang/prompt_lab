# LLM Game Agent Template (LLM游戏智能体模板)

基于 LangGraph 和 Streamlit 构建的 LLM 游戏智能体开发框架，提供完整的游戏AI开发工具链。

## 核心特性

### 1. 智能体框架
- 基于 LangGraph 的状态管理
  - 完整的状态图定义
  - 状态转换控制
  - 事件驱动机制
- 多智能体协作系统
  - 智能体角色定义
  - 消息传递机制
  - 协作策略管理
- 决策引擎
  - 基于规则的决策
  - 强化学习支持
  - 策略优化

### 2. 游戏引擎集成
- 标准化游戏接口
  - 状态表示
  - 动作空间
  - 奖励机制
- 多种游戏类型支持
  - 棋类游戏
  - 卡牌游戏
  - 文字冒险
- 自定义游戏开发
  - 游戏规则定义
  - 状态转换实现
  - 界面组件开发

### 3. 开发工具链
- 调试与分析工具
  - 状态可视化
  - 决策树展示
  - 性能分析
- 测试框架
  - 单元测试
  - 集成测试
  - 性能基准
- 部署工具
  - 容器化支持
  - 云端部署
  - 监控系统

## 核心模块说明

### 1. 框架核心 (main.py)

```python
class GameFramework:
    def __init__(self):
        self.session = SessionManager()
        self.agent = GameAgent()
        self.ui = UIManager()

    async def run_game_loop(self):
        while not self.session.is_ended:
            state = await self.agent.process_turn()
            self.ui.update(state)
```

### 2. 状态管理 (game_agent.py)

```python
class GameAgent:
    def __init__(self):
        self.graph = StateGraph()
        self.state = GameState()
        self.tools = AgentTools()

    def define_workflow(self):
        self.graph.add_node("init", self.initialize)
        self.graph.add_node("player_turn", self.process_player)
        self.graph.add_node("ai_turn", self.process_ai)
```

### 3. LLM交互 (llm_interaction.py)

```python
class LLMInteraction:
    def __init__(self, model_config):
        self.model = self.load_model(model_config)
        self.history = MessageHistory()
        self.templates = PromptTemplates()

    async def get_response(self, prompt, context):
        messages = self.templates.format(prompt, context)
        return await self.model.generate(messages)
```

## 项目结构

```
llm_game_agent_template/
├── main.py                 # 框架入口
├── game_agent.py          # 智能体核心
├── llm_interaction.py     # LLM交互管理
├── agent_tool.py          # 工具函数
├── games/                 # 游戏实现
│   └── base_game/        # 基础游戏模板
│       ├── game_view.py  # 游戏视图
│       └── action_view.py # 动作视图
└── docs/                 # 文档目录
```

## 配置说明

### 1. 环境配置
创建 `.env` 文件:
```env
# LLM API配置
OPENAI_API_KEY=你的OpenAI密钥
ANTHROPIC_API_KEY=你的Anthropic密钥

# 框架配置
GAME_TYPE=chess/card/adventure
DEBUG_MODE=true/false
LOG_LEVEL=info/debug
```

### 2. 游戏配置
创建 `game_config.json`:
```json
{
  "game_type": "chess",
  "parameters": {
    "board_size": 8,
    "time_control": "standard",
    "ai_difficulty": "medium"
  },
  "rules": {
    "custom_rules": [],
    "variations": []
  }
}
```

## 开发指南

### 1. 创建新游戏

1. 定义游戏状态
```python
class ChessGameState(GameState):
    def __init__(self):
        self.board = Board()
        self.current_player = "white"
        self.move_history = []
```

2. 实现动作处理
```python
class ChessActions(GameActions):
    def validate_move(self, move):
        # 移动验证逻辑
        pass

    def apply_move(self, move):
        # 移动执行逻辑
        pass
```

3. 创建游戏视图
```python
class ChessView(GameView):
    def render_board(self):
        # 棋盘渲染逻辑
        pass

    def handle_input(self):
        # 输入处理逻辑
        pass
```

### 2. 自定义智能体

1. 定义决策逻辑
```python
class ChessAgent(GameAgent):
    def evaluate_position(self):
        # 局面评估
        pass

    def select_move(self):
        # 移动选择
        pass
```

2. 配置提示词模板
```python
CHESS_PROMPTS = {
    "analyze_position": "分析当前局面...",
    "suggest_move": "建议下一步移动...",
    "evaluate_outcome": "评估可能的结果..."
}
```

## 测试指南

### 1. 单元测试
```bash
# 运行所有测试
python -m pytest tests/

# 运行特定模块测试
python -m pytest tests/test_game_agent.py
```

### 2. 性能测试
```bash
# 运行基准测试
python benchmarks/run_benchmarks.py

# 生成性能报告
python benchmarks/generate_report.py
```

## 部署指南

### 1. Docker部署
```bash
# 构建镜像
docker build -t llm-game-agent .

# 运行容器
docker run -p 8501:8501 llm-game-agent
```

### 2. 云端部署
```bash
# AWS部署
aws ecs deploy --cluster game-cluster --service game-service

# GCP部署
gcloud run deploy game-service --image gcr.io/project/game-agent
```

## 性能优化

1. LLM调用优化
   - 使用缓存
   - 批量处理
   - 异步调用

2. 状态管理优化
   - 状态压缩
   - 增量更新
   - 懒加载

3. UI性能优化
   - 组件缓存
   - 按需渲染
   - 数据分页

## 更新日志

### v0.5.0 (2024-03)
- 完整的框架核心功能
- 多种游戏类型支持
- 性能优化

### v0.4.0 (2024-02)
- 增加新的游戏模板
- 改进智能体决策系统
- 文档更新

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交变更
4. 发起 Pull Request

## 许可证

MIT License