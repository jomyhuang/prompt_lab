# LangGraph 状态管理与Human-in-loop开发指南

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

## 1. 基础概念

### 1.1 状态定义
```python
from typing import Annotated, TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.types import interrupt, Command

# 定义状态类型
class State(TypedDict):
    messages: Annotated[list, add_messages]
    current_turn: Literal["player", "dealer"]
    game_over: bool
```

### 1.2 关键概念
1. State对象:
- 使用TypedDict定义类型
- 使用Annotated标注更新行为
- 保持状态字段清晰

2. interrupt()机制:
- 暂停图执行
- 传递状态信息到前端
- 等待用户输入
- 通过graph.invoke(Command(resume=“action str” 或是 {“action”: “attack”, “row”: 1, “col”: 2})) 恢复, 传入的是interrupt的return值.

3. 状态更新:
- 追加而不是覆盖消息
- 保持状态一致性
- 正确处理状态转换

## 2. 图的构建与执行

### 2.1 节点定义
```python
def state_node(state: State) -> State:

    # 处理用户操作
    state["messages"] = ....

    # 必须返回state
    return state
```

### 2.2 图的构建
```python
# 创建图
graph = StateGraph(State)

# 添加节点
graph.add_node("player_turn", player_turn)
graph.add_node("dealer_turn", dealer_turn)

# 添加边
graph.add_edge(START, "player_turn")
graph.add_edge("player_turn", "dealer_turn")
graph.add_edge("dealer_turn", END)

# 编译图
# 当使用interrupt()时, 需要启用checkpointer
graph = graph.compile(checkpointer=checkpointer)
```

### 2.3 条件流转
```python
def route(state: State) -> Literal["player_turn", "dealer_turn", END]:
    if state["game_over"]:
        return END
    elif state["current_turn"] == "player":
        return "player_turn"
    else:
        return "dealer_turn"

# 添加路由
graph.add_node("route", route)
graph.add_edge(START, "route")
graph.add_edge("route", "player_turn")
graph.add_edge("route", "dealer_turn")
graph.add_edge("route", END)

# 添加条件流转
graph.add_conditional_edges(
    "route",
    lambda x: (
        "handle_end" if x["game_over"] else
        "player_action" if x["current_turn"] == "player" else
        "computer_action"
    )
)
```

## 3. Human-in-loop实现

### 3.1 基本流程
1. 启用checkpointer
2. 准备状态信息
3. 调用interrupt()暂停
4. 等待用户输入
5. 通过Command恢复
6. 处理用户操作
7. 更新状态

### 3.2 Checkpointer配置
```python
from langgraph.checkpoint.memory import MemorySaver
import random

# 1. 创建checkpointer
checkpointer = MemorySaver()

# 2. 创建带thread_id的配置
thread_id = str(random.randint(1, 1000000))
config = {"configurable": {"thread_id": thread_id}}

# 3. 创建图时启用checkpointer (必须!!)
graph = build_graph(checkpointer=checkpointer)

# 4. 使用config调用图
initial_state = init_game()
result = graph.invoke(initial_state, config=config)
```

注意事项:
1. interrupt()必须启用checkpointer才能使用
2. 使用thread_id标识不同的执行流
3. 可以选择不同的存储后端(如MemorySaver或LocalStateCheckpointer)
4. 不能在interrupt()外围通过try catch捕获异常

### 3.3 Human-in-loop节点实现
```python
def player_turn(state: GameState) -> GameState:
    """Human-in-loop节点实现
    
    关键点:
    1. 检查游戏状态
    2. 准备展示信息
    3. 使用interrupt暂停
    4. 处理用户操作
    5. 更新游戏状态
    """
    gameinfo = {
        ...
    }

    # 在interrup前, 代码在resume时候, 会重复执行, 不能有更新state的操作
    # 使用interrupt等待玩家操作
    print("[player_turn] before interrupt")
    action = interrupt(game_info)
    print("[player_turn] after interrupt", action)
   
    # 通过返回的action 处理玩家操作, 文本或是Command()
    if action == "hit":
        ...
                
    elif action == "stand":
        ...

    return state
```

### 3.4 状态恢复
```python
def handle_player_action(action: str):
    """处理玩家操作并同步状态"""

    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    # 创建Command并调用图, 并且可以更新状态
    command = Command(resume="hit", update={"messages": [feedback_msg]}) 

    # 恢复到中断点继续图状态流动, 会从整体中断函数开始执行, 返回resume值
    result = st.session_state.graph.invoke(command, config=config)
    
    # 或是跳转到特定节点
    result = st.session_state.graph.invoke(Command(goto="run_tool", update={"messages": [feedback_msg]}), config=config)

    # 同步状态
    st.session_state.game_state = result
    st.session_state.require_update = True
```

### 3.5 最佳实践
1. interrupt()使用:
- 只传必要的游戏信息
- 明确定义有效操作
- 使用thread_id标识执行流
- 不能在interrupt()外围通过try catch捕获异常, 不一定需要传入给interrupt("please input something...") 特别的参数
- 通过中断函数重新呼叫, 通过 graph.invoke(Command(resume=str或dict), config=config) 来恢复继续图流动

2. 状态同步:
- interrupt()返回后立即更新状态
- Command恢复前验证状态
- 保持session_state同步

3. 代码规范:
- 以LangGarph 规范使用 messages: Annotated[list[dict], "游戏消息"] 保存对话信息
    - 以 AIMessage, HumanMessage, SystemMessage 规范使用, 构建并保存对话信息
- 以 TypedDict 规范使用, 保存主要的LangGraph状态流动



## 4. Streamlit集成

### 4.1 状态管理
```python
# 1. 图的初始化
def build_graph(checkpointer: Checkpointer):
    """初始化游戏图实例"""
    graph = StateGraph(State)
    graph.add_node("player_turn", player_turn)
    graph.add_edge(START, "player_turn")
    graph.add_edge("player_turn", END)

    if not checkpointer:
        raise ValueError("build graph error, checkpointer is required")

    return graph.compile(checkpointer=checkpointer)

# 2. 状态初始化
def init_game_state() -> State:
    """初始化游戏状态"""
    return {
        "messages": [],
        "current_turn": "player",
        "game_over": False
    }

# 3. 初始化游戏状态
def init_game_app():
    st.session_state.game_started = True
    st.session_state.checkpointer = MemorySaver()
    st.session_state.thread_id = str(random.randint(1, 1000000))
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    st.session_state.config = config
    st.session_state.graph = build_graph(checkpointer=st.session_state.checkpointer)


# 3. 主游戏循环
def run_game():
    """主游戏循环"""

    if "graph" not in st.session_state or "game_state" not in st.session_state:
        init_game_app()
        init_game_state = init_game_state()
        config = st.session_state.config
        print(f"[main] initial invoke ----")
        # 启动图, 必须在interrupt, resume前, 初始化图一次invoke, 写入init_game_state
        st.session_state.game_state = st.session_state.graph.invoke(init_game_state, config=config)
        print(f"[main] after initial invoke ----")
        st.session_state.require_update = True

    # ....(streamlit main UI render code)
    render_main()

    # 调用图的 invoke 方法执行游戏流程
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    print(f"[main] Before main invoke ----")
    st.session_state.game_state = st.session_state.graph.invoke(
        Command(resume=None), 
        config=config)
    print(f"[main] After main invoke ----")
            
    # 检查是否需要重新渲染(必须摆在整个main最后)
    if st.session_state.need_rerun:
        st.session_state.need_rerun = False
        print(f"[main] need_rerun ----", time.time())
        st.rerun()


```

### 4.2 streamlit 渲染树设计
```python
# 1. 主渲染函数
def render_main():
    """主渲染函数"""
    if "require_update" not in st.session_state:
        st.session_state.require_update = False
        
    render_header()
    render_game_board()
    render_controls()
    
# 2. 子渲染函数
def render_game_board():
    """游戏板渲染"""
    st.write(f"Current Turn: {st.session_state.game_state['current_turn']}")

# 3. 交互处理
def handle_player_action():
    """处理玩家操作"""
    if st.button("Hit"):
        process_player_action("hit")
        st.session_state.require_update = True
```

## 5. 最佳实践

### 5.1 状态管理
1. 图的调用规范:
- 使用invoke()执行主要逻辑

2. 状态一致性:
- 及时同步状态
- 统一状态来源
- 避免状态分散

### 5.2 渲染规范
1. 组件职责:
- 主渲染函数控制更新
- 子组件纯UI渲染
- 交互函数设置标志

2. 更新流程:
- 单一更新入口
- 批量处理更新
- 避免重复渲染
- 禁止在main()中使用st.rerun() 会造成中断代码
- 使用session_state.require_update = True 来触发更新


## 6. 调试与监控

### 6.1 调试编码
- 尽量减少 try..except 代码, 直接输出错误信息到终端
- 在节点函数进入时, print输出节点名称
- 在特定命令前后, print输出调用前后信息, 以下为特定命令:
    - 在invoke()前后
    - 在interrupt()前后
    - 在resume()前后
    - 在goto()前后
    - 在goto_node()前后
- 在调用st.rerun()时, 输出函数名称, rerun时间戳记


### 6.2 状态监控
```python
def debug_state_change(state: State):
    """调试状态变化(仅用于开发)"""
    try:
        # 使用expander来折叠调试信息
        with st.expander("Debug Info", expanded=False):
            # 显示完整状态
            st.json(state)
            
            # 显示最新消息
            if state.get("messages"):
                st.write("Latest Message:", state["messages"][-1])
                
            # 显示当前回合
            st.write("Current Turn:", state["current_turn"])
            
            # 显示游戏状态
            st.write("Game Status:", "Ended" if state["game_over"] else "In Progress")
    except Exception as e:
        st.error(f"Debug error: {str(e)}")
        
def log_state_action(action: str, state: State):
    """记录状态变化和操作(仅用于开发)"""
    try:
        # 在侧边栏显示日志
        with st.sidebar:
            if "debug_log" not in st.session_state:
                st.session_state.debug_log = []
            
            # 记录操作和状态变化
            log_entry = {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "action": action,
                "turn": state["current_turn"],
                "game_over": state["game_over"]
            }
            
            st.session_state.debug_log.append(log_entry)
            
            # 显示最近的日志
            st.write("### Debug Log")
            for entry in st.session_state.debug_log[-5:]:
                st.write(f"{entry['timestamp']} - {entry['action']}")
    except Exception as e:
        st.error(f"Logging error: {str(e)}")
```

### 6.3 调试建议
1. 状态检查:
- 使用 `debug_state_change()` 监控状态
- 使用 `log_state_action()` 记录操作
- 在开发环境中启用调试功能

