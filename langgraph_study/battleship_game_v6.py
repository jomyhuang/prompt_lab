from typing import TypedDict, Literal, List, Optional
from langgraph.graph import StateGraph, END, START
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
import streamlit as st
import random

# 定义游戏状态
class GameState(TypedDict):
    player_board: List[List[str]]  # 玩家棋盘
    ai_board: List[List[str]]  # AI棋盘
    player_shots: List[tuple]  # 玩家射击记录
    ai_shots: List[tuple]  # AI射击记录
    current_turn: Literal["player", "ai"]  # 当前回合
    game_over: bool  # 游戏是否结束
    message: str  # 游戏消息
    player_ships: int  # 玩家剩余船只
    ai_ships: int  # AI剩余船只
    last_shot: Optional[tuple]  # 最后射击位置

# 初始化棋盘
def init_board(size: int = 10) -> List[List[str]]:
    return [["~" for _ in range(size)] for _ in range(size)]

# 初始化游戏状态
def init_game() -> GameState:
    return {
        "player_board": init_board(),
        "ai_board": init_board(),
        "player_shots": [],
        "ai_shots": [],
        "current_turn": "player",
        "game_over": False,
        "message": "Welcome to Battleship!",
        "player_ships": 5,
        "ai_ships": 5,
        "last_shot": None
    }

# 玩家回合节点
def player_turn(state: GameState) -> GameState:
    if state["current_turn"] == "player" and not state["game_over"]:
        # 准备展示给玩家的游戏信息
        game_info = {
            "message": "Your turn! Select a target.",
            "player_board": state["player_board"],
            "ai_board": state["ai_board"],
            "player_shots": state["player_shots"],
            "ai_shots": state["ai_shots"],
            "player_ships": state["player_ships"],
            "ai_ships": state["ai_ships"]
        }
        
        # 使用interrupt等待玩家操作
        target = interrupt(game_info)
        
        # 处理玩家射击
        if target not in state["player_shots"]:
            state["player_shots"].append(target)
            x, y = target
            if state["ai_board"][x][y] == "S":  # 击中船只
                state["ai_board"][x][y] = "X"
                state["ai_ships"] -= 1
                state["message"] = f"Hit at ({x}, {y})!"
            else:
                state["ai_board"][x][y] = "O"
                state["message"] = f"Miss at ({x}, {y})!"
            
            state["last_shot"] = target
            state["current_turn"] = "ai"
            
            # 检查游戏是否结束
            if state["ai_ships"] == 0:
                state["game_over"] = True
                state["message"] = "You win! All enemy ships sunk!"
    
    return state

# AI回合节点
def ai_turn(state: GameState) -> GameState:
    if state["current_turn"] == "ai" and not state["game_over"]:
        # AI随机选择目标
        while True:
            x = random.randint(0, 9)
            y = random.randint(0, 9)
            if (x, y) not in state["ai_shots"]:
                break
                
        state["ai_shots"].append((x, y))
        if state["player_board"][x][y] == "S":  # 击中玩家船只
            state["player_board"][x][y] = "X"
            state["player_ships"] -= 1
            state["message"] = f"Enemy hit at ({x}, {y})!"
        else:
            state["player_board"][x][y] = "O"
            state["message"] = f"Enemy missed at ({x}, {y})!"
            
        state["last_shot"] = (x, y)
        state["current_turn"] = "player"
        
        # 检查游戏是否结束
        if state["player_ships"] == 0:
            state["game_over"] = True
            state["message"] = "You lose! All your ships sunk!"
    
    return state

# 构建游戏图
def build_graph(checkpointer=None):
    graph = StateGraph(GameState)
    
    graph.add_node("player_turn", player_turn)
    graph.add_node("ai_turn", ai_turn)
    
    graph.add_edge(START, "player_turn")
    graph.add_edge("player_turn", "ai_turn")
    graph.add_edge("ai_turn", "player_turn")
    graph.add_edge("player_turn", END)
    graph.add_edge("ai_turn", END)
    
    return graph.compile(checkpointer=checkpointer)

def render_board(board: List[List[str]], hide_ships: bool = False):
    """渲染游戏棋盘
    
    Args:
        board: 要渲染的棋盘
        hide_ships: 是否隐藏船只（用于显示敌方棋盘）
    """
    # 创建列布局
    cols = st.columns(len(board[0]) + 1)
    
    # 渲染列坐标
    with cols[0]:
        st.write("")  # 左上角空白
    for i, col in enumerate(cols[1:]):
        with col:
            st.write(str(i))
    
    # 渲染每一行
    for i, row in enumerate(board):
        cols = st.columns(len(row) + 1)
        with cols[0]:
            st.write(str(i))  # 行号
        for j, cell in enumerate(row):
            with cols[j + 1]:
                if hide_ships and cell == "S":  # 隐藏敌方船只
                    st.write("~")
                else:
                    st.write(cell)

# Streamlit主界面
def main():
    st.set_page_config(layout="wide", page_title="LangGraph Battleship")
    
    if "game_started" not in st.session_state:
        st.session_state.game_started = False
        st.session_state.thread_id = str(random.randint(1, 1000000))
    
    if not st.session_state.game_started:
        st.title("🚢 LangGraph Battleship")
        if st.button("Start Game"):
            st.session_state.game_started = True
            initial_state = init_game()
            checkpointer = MemorySaver()
            st.session_state.graph = build_graph(checkpointer=checkpointer)
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            st.session_state.game_state = st.session_state.graph.invoke(initial_state, config=config)
            st.rerun()
    else:
        st.title("Battleship")
        
        if "game_state" not in st.session_state:
            initial_state = init_game()
            checkpointer = MemorySaver()
            st.session_state.graph = build_graph(checkpointer=checkpointer)
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            st.session_state.game_state = st.session_state.graph.invoke(initial_state, config=config)
        
        # 显示游戏状态
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Your Board")
            render_board(st.session_state.game_state["player_board"])
            st.write(f"Your Ships: {st.session_state.game_state['player_ships']}")
        
        with col2:
            st.subheader("Enemy Board")
            render_board(st.session_state.game_state["ai_board"], hide_ships=True)
            st.write(f"Enemy Ships: {st.session_state.game_state['ai_ships']}")
        
        # 处理玩家操作
        if not st.session_state.game_state["game_over"]:
            if st.session_state.game_state["current_turn"] == "player":
                target = st.selectbox("Select target", [(x, y) for x in range(10) for y in range(10)])
                if st.button("Fire!"):
                    config = {"configurable": {"thread_id": st.session_state.thread_id}}
                    st.session_state.game_state = st.session_state.graph.invoke(
                        Command(resume=target), config=config)
                    st.rerun()
            else:
                st.write("AI's turn...")
                config = {"configurable": {"thread_id": st.session_state.thread_id}}
                st.session_state.game_state = st.session_state.graph.invoke(
                    Command(resume="ai_turn"), config=config)
                st.rerun()
        
        # 显示游戏结果
        if st.session_state.game_state["game_over"]:
            st.success(st.session_state.game_state["message"])
            if st.button("New Game"):
                st.session_state.game_started = False
                st.rerun()

if __name__ == "__main__":
    main() 