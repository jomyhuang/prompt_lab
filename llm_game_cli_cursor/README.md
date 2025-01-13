# LLM Game Framework

基于 LangGraph 和 Streamlit 构建的 LLM 游戏框架。

# 2025-01-12 V0.5 Tag

## 项目结构

```
llm_game_cli_cursor/
├── main.py              # 主程序入口和框架核心
├── game_agent.py        # LangGraph游戏状态管理
├── llm_interaction.py   # LLM模型交互管理
├── agent_tool.py        # 消息处理工具函数
└── games/              # 游戏界面组件目录
    └── base_game/      # 基础游戏界面
        ├── __init__.py
        ├── game_view.py    # 游戏状态显示
        └── action_view.py  # 玩家操作界面
```

## 核心模块说明

### 1. 框架核心 (main.py)

主要职责:
- 会话状态管理 (`_init_session_state`)
- 游戏Agent初始化 (`_init_game_agent`)
- 聊天界面渲染 (`render_chat_view`)
- 游戏循环处理 (`_process_game_loop`)
- Human-in-Loop 交互流程

关键组件:
- 状态更新机制 (require_update/require_update_chat)
- 消息流处理 (streaming/invoke 模式)
- 界面布局管理

### 2. 状态管理 (game_agent.py)

基于 LangGraph 的状态图实现:
- 游戏状态定义 (`GameState`)
- 状态转换节点
  - init -> welcome -> route
  - player_turn/ai_turn -> route
  - route -> end
- Human-in-Loop 中断机制
- 状态验证和更新

### 3. LLM交互 (llm_interaction.py)

LLM模型管理:
- 支持多种模型 (Google/OpenAI/DeepSeek)
- 对话历史管理
- 流式输出支持
- 上下文提示词模板

### 4. 界面组件 (games/base_game)

可扩展的游戏界面:
- 游戏状态显示 (game_view.py)
- 玩家操作界面 (action_view.py)
- 支持自定义游戏类型

## 工作流程

1. 初始化流程:
```
main.py
  ├── _init_session_state  # 初始化会话状态
  └── _init_game_agent     # 创建游戏Agent
```

2. 游戏循环:
```
_process_game_loop
  ├── streaming模式: _process_streaming_agent
  └── invoke模式: _process_invoke_agent
```

3. 状态更新机制:
```
require_update_chat (新对话优先)
  └── require_update (状态更新)
      └── rerun (界面刷新)
```

4. Human-in-Loop 交互:
```
player_turn
  ├── interrupt -> GUI操作
  └── resume -> 状态更新
```

## 特点和优势

1. 模块化设计
- 核心框架与游戏逻辑分离
- 界面组件可扩展
- 消息处理统一管理

2. 双模式支持
- Streaming: 实时流式输出
- Invoke: 标准调用模式

3. 状态管理
- 基于 LangGraph 的状态图
- 完整的状态验证
- 灵活的中断机制

4. 界面交互
- 标准化的 Streamlit 组件
- 响应式更新机制
- 清晰的状态反馈

## 开发指南

1. 添加新游戏类型:
```python
games/
  ├── base_game/     # 基础游戏
  ├── card_game/     # 卡牌游戏
  └── chess_game/    # 棋类游戏
```

2. 自定义界面组件:
- 继承基础游戏视图
- 实现特定游戏逻辑
- 保持状态管理接口

3. 注意事项:
- 保持核心框架代码稳定
- 遵循状态更新机制
- 正确处理中断流程

## 依赖要求

- Python 3.10+
- streamlit
- langchain
- langgraph
- 其他依赖见 requirements.txt

## 使用说明

1. 安装依赖:
```bash
pip install -r requirements.txt
```

2. 配置环境变量:
```bash
# LLM API配置
OPENAI_API_KEY=xxx
GOOGLE_API_KEY=xxx
DEEPSEEK_API_KEY=xxx
```

3. 运行程序:
```bash
streamlit run main.py
```