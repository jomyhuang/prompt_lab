# LangGraph 状态管理与Human-in-loop开发指南

## 0. 参考文档

### LangGraph API
- LangGraph官方文档: https://python.langchain.com/docs/langgraph
- StateGraph API: https://python.langchain.com/api/langgraph/graph
- Human-in-loop API: https://python.langchain.com/api/langgraph/types

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
- 通过Command恢复

3. 状态更新:
- 追加而不是覆盖消息
- 保持状态一致性
- 正确处理状态转换

## 2. 图的构建与执行

### 2.1 节点定义
```python
def player_turn(state: State) -> State:
    """Human-in-loop节点实现"""
    if state["game_over"]:
        return state
        
    game_info = {
        "messages": state["messages"],
        "valid_actions": ["hit", "stand"]
    }
    
    action = interrupt(game_info)
    
    if isinstance(action, Command):
        resume_action = action.resume
        if resume_action == "hit":
            state["messages"].append({"role": "user", "content": "hit"})
        elif resume_action == "stand":
            state["messages"].append({"role": "user", "content": "stand"})
            state["current_turn"] = "dealer"
    
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
graph = graph.compile()
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
```

## 3. Human-in-loop实现

### 3.1 基本流程
1. 准备状态信息
2. 调用interrupt()暂停
3. 等待用户输入
4. 通过Command恢复
5. 处理用户操作
6. 更新状态

### 3.2 Command处理
```python
def process_user_action(action: str) -> Command:
    """处理用户操作并创建Command对象"""
    valid_actions = ["hit", "stand"]
    if action not in valid_actions:
        raise ValueError(f"Invalid action: {action}")
        
    return Command(resume=action)
```

### 3.3 最佳实践
1. interrupt()使用:
- 只传必要信息
- 明确定义有效操作
- 正确使用Command

2. 状态同步:
- interrupt()返回后立即同步
- Command恢复前验证状态
- 保持更新一致性

## 4. Streamlit集成

### 4.1 状态管理
```python
# 1. 图的初始化
def init_game_graph():
    """初始化游戏图实例"""
    graph = StateGraph(State)
    graph.add_node("player_turn", player_turn)
    graph.add_edge(START, "player_turn")
    graph.add_edge("player_turn", END)
    return graph.compile()

# 2. 状态初始化
def init_game_state() -> State:
    """初始化游戏状态"""
    return {
        "messages": [],
        "current_turn": "player",
        "game_over": False
    }

# 3. 主游戏循环
def run_game():
    """主游戏循环"""
    if "graph" not in st.session_state:
        st.session_state.graph = init_game_graph()
    if "game_state" not in st.session_state:
        st.session_state.game_state = init_game_state()
    
    try:
        result = st.session_state.graph.invoke(st.session_state.game_state)
        st.session_state.game_state = result
        st.session_state.require_update = True
    except Exception as e:
        st.error(f"Graph execution error: {str(e)}")
```

### 4.2 渲染树设计
```python
# 1. 主渲染函数
def render_main():
    """主渲染函数"""
    if "require_update" not in st.session_state:
        st.session_state.require_update = False
        
    render_header()
    render_game_board()
    render_controls()
    
    if st.session_state.require_update:
        st.session_state.require_update = False
        st.rerun()

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

### 4.3 状态同步
```python
def handle_player_action(action: str):
    """处理玩家操作并同步状态"""
    try:
        command = Command(resume=action)
        result = st.session_state.graph.invoke(command)
        st.session_state.game_state = result
        st.session_state.require_update = True
    except Exception as e:
        st.error(f"Action processing error: {str(e)}")

def render_game_state():
    """渲染游戏状态"""
    state = st.session_state.game_state
    st.write("Current Turn:", state["current_turn"])
    if "messages" in state:
        for msg in state["messages"]:
            st.write(msg["content"])
```

## 5. 最佳实践

### 5.1 状态管理
1. 图的调用规范:
- 使用invoke()执行主要逻辑
- stream()仅用于调试
- 正确处理Command

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

### 5.3 性能优化
1. 状态更新:
- 减少不必要调用
- 合理使用缓存
- 避免频繁重渲染

2. 错误处理:
- 完善异常捕获
- 友好错误提示
- 保持状态一致

## 6. 调试与监控

### 6.1 状态监控
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

### 6.2 调试建议
1. 状态检查:
- 使用 `debug_state_change()` 监控状态
- 使用 `log_state_action()` 记录操作
- 在开发环境中启用调试功能

2. 错误处理:
- 捕获并显示详细错误信息
- 保持状态一致性
- 提供回滚机制

3. 调试工具:
- 使用Streamlit内置组件显示信息
- 保持日志可追踪性
- 避免影响生产环境 