# LLM游戏框架

基于LangGraph和Streamlit构建的LLM驱动的游戏框架。

## 特性

- 基于LangGraph的状态管理
- Human-in-loop交互模式
- 标准化的Streamlit UI组件
- 清晰的提示词工程

## 安装

```bash
pip install -r requirements.txt
```

## 目录结构

```
llm_game_cli/
├── requirements.txt    # 依赖管理
├── README.md          # 项目说明
├── game_state.py      # 游戏状态管理
├── game_graph.py      # LangGraph状态图
├── game_ui.py         # Streamlit UI组件
├── llm_interface.py   # LLM交互接口
└── main.py           # 主程序入口
```

## 使用方法

1. 安装依赖
2. 配置环境变量
3. 运行程序:
```bash
streamlit run main.py
```
