# LLM游戏框架

基于LangGraph和Streamlit构建的LLM驱动的游戏框架。

## 特性

- 基于LangGraph的状态管理
- Human-in-loop交互模式
- 标准化的Streamlit UI组件
- 清晰的提示词工程

## 安装

1. 克隆仓库:
```bash
git clone <repository_url>
cd llm_game_cli_cursor
```

2. 安装依赖:
```bash
pip install -r requirements.txt
```

3. 配置环境变量:
创建.env文件并设置以下变量:
```
OPENAI_API_KEY=your_openai_api_key
OPENAI_API_BASE=your_openai_api_base
GOOGLE_API_KEY=your_google_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_BASE=your_deepseek_api_base
```

## 使用方法

1. 运行游戏:
```bash
streamlit run gui_main.py
```

2. 自定义游戏:
- 继承GameState类定义游戏状态
- 扩展GameWorkflow类实现游戏逻辑
- 调整LLMInteraction的提示词
- 自定义GUI界面

## 项目结构

```
llm_game_cli_cursor/
├── game_state.py      # 游戏状态管理
├── game_workflow.py   # LangGraph游戏流程
├── llm_interaction.py # LLM交互管理
├── gui_main.py        # Streamlit GUI界面
├── requirements.txt   # 项目依赖
└── README.md         # 项目文档
```

## 主要功能

1. 基本通用游戏框架的langgraph图
2. 基本通用游戏框架的streamlit UI
3. 连接LLM大模型实现对话
4. 通过对话messages输出游戏节点名称
5. 在玩家回合使用对话命令与LLM对话交互
6. 按钮"结束玩家"回合, 触发玩家回合结束
7. AI玩家回合, 输出范本对话后, 进入图流程

## 开发指南

1. 状态管理:
- 使用TypedDict定义状态类型
- 实现状态验证和更新
- 管理消息历史

2. 游戏流程:
- 定义清晰的节点和转换
- 实现Human-in-loop交互
- 处理异常情况

3. LLM交互:
- 配置模型和提示词
- 实现命令解析
- 管理对话上下文

4. GUI开发:
- 使用标准组件
- 实现响应式更新
- 优化用户体验

## 注意事项

1. 状态管理:
- 保持状态一致性
- 及时更新UI
- 处理并发问题

2. LLM交互:
- 处理API限制
- 优化响应时间
- 保护API密钥

3. 界面开发:
- 遵循Streamlit最佳实践
- 优化性能
- 提供良好的用户体验 