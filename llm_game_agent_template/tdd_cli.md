# LLM游戏框架

基于LangGraph和Streamlit构建的LLM驱动的游戏框架。

## 特性

- 基于LangGraph的状态管理
- Human-in-loop交互模式
- 标准化的Streamlit UI组件
- 清晰的提示词工程

## 实现功能
- 基本通用游戏框架的langgraph图
- 基本通用游戏框架的streamlit UI
- 连接LLM大模型实现对话
- 通过对话messages输出游戏节点名称
- 在玩家回合使用对话命令与LLM对话交互
- 按钮"结束玩家"回合, 触发玩家回合结束, 进入图流程
- AI玩家回合, 输出范本对话后, 进入图流程

## 规范

tdd_UI_design_chatbased_game.md
tdd_langgraph_state_humanloop.md

实践参考 @LLMInteraction 里关于langchain的最新实践方式, 可以同时支持配置多种模型


## 参考代码
@blackjack_game.py
@battleship_game_v2.py
@gui_main.py 

生成一个基于 @tdd_UI_design_chatbased_game.md 的通用框架代码架构. 并按照@tdd_langgraph_state_humanloop.md这个规范编写 参考文件中提供的URL可以网上读取. 代码实践分析 @blackjack_game.py @battleship_game_v2.py @gui_main.py 提出你的最佳实践方案




