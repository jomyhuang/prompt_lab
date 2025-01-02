#基于大语言模型驱动的chat-based游戏UI设计

## 0. 参考文档

### LangGraph 基本设计模式:
https://langchain-ai.github.io/langgraph/tutorials/introduction/#setup
https://langchain-ai.github.io/langgraph/tutorials/introduction/#part-4-human-in-the-loop

### LangGraph API
- LangGraph官方文档: https://python.langchain.com/docs/langgraph
- StateGraph API: https://python.langchain.com/api/langgraph/graph
- Human-in-loop 设计模式: 
https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/
https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/#design-patterns

### Streamlit API
- Streamlit官方文档: https://docs.streamlit.io
- Session State: https://docs.streamlit.io/library/api-reference/session-state
- Components: https://docs.streamlit.io/library/api-reference/widgets

### 1.参考代码:
@llm_cardstudio/gui_main.py
@langgraph_study/blackjack_game.py
@langgraph_study/battleship_game_v2.py

### 2.技术栈:
- Streamlit GUI
- LangGraph
- LangChain

### 3. 设计目标
以大语言LLM模型驱动, 基于chat-based的界面, 能够实现游戏状态的展示, 玩家操作的输入, 以及游戏流程的控制.
核心技术以LangGraph为主, 使用LangChain来实现LLM的调用.
以Human-in-loop为核心, 使用LangGraph的Human-in-loop设计模式来实现人机交互.
以状态管理为核心, 使用LangGraph的StateGraph来实现状态管理, 通过streamlit的session_state实现状态同步进行交互界面的渲染.

### 4. Game GUI layout
- sidebar: 游戏规则, 游戏设置, 游戏状态, 游戏日志, 通常默认为折叠
- main: 分割界面为游戏区和聊天区
- game_col: game_view 游戏区, 渲染游戏状态 game_view
- chat_col: chat_view 聊天区, 渲染聊天记录, 玩家对话操作输入(使用标准streamlit chat组件)
    - action_view: 渲染游戏操作按钮, 通常为不同状态下, 不同的操作按钮, 用于合成对话文本命令发给LLM
    - 可以进一步扩张由LLM生成 action_view 不同的合成对话指令界面(减少对话文本重复输入与LLM Tool calling的正确性) 

```python
    # 设置页面配置
    st.set_page_config(
        page_title="🎮 LLM Card Studio",
        page_icon="🎮",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # 分割界面为游戏区和聊天区
    # 通常为 50% 50%, 或是 60% 40% 固定比例
    game_col, chat_col = st.columns([1, 1])
    
    # 渲染游戏区
    with game_col:
        render_game_view()    

    # 渲染聊天区
    with chat_col:
        render_chat_view()
        render_action_view()

        update_require = await _process_game_loop():
        if update_require or st.session_state.update_required:
            st.session_state.update_required = False
            # 如果需要更新,重置标志并重新渲染
            print(f"[main] mainloop rerun {time.time()}")
            st.rerun()
```

### 5.规范与最佳实践
- 在没有特别指示下 均采用streamlit的标准组件, 如chat组件, 按钮组件, 表格组件等
- 在需要特殊定制时, 采用streamlit的custom组件, 如自定义的chat组件, 自定义的按钮组件, 自定义的表格组件等
- 尽量减少使用st.html, 以css方式调整布局跟输出
- 尽量减少使用st.write, 以st.markdown方式输出

- 以langGarph 规范使用 messages: Annotated[list[dict], "游戏消息"] 保存对话信息
    - 以 AIMessage, HumanMessage, SystemMessage 规范使用, 构建并保存对话信息
- 以 TypedDict 规范使用, 保存主要的LangGraph状态流动

### 9. 注意事项
- 确保stremlit st.rerun的减少与分散在代码不同位置
- 确保渲染主画面布局不要跳动, 大多情况都是高度变化所导致



