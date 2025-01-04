import streamlit as st
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal, Optional
import random
import time

# 游戏选项
CHOICES = ["Rock 🪨", "Paper 📄", "Scissors ✂️"]

# 定义游戏状态类型
class GameState(TypedDict):
    current_turn: Literal["player", "computer"]
    player_choice: Optional[str]
    computer_choice: Optional[str]
    message: str
    game_over: bool
    player_score: int
    computer_score: int
    last_player_choice: Optional[str]
    last_computer_choice: Optional[str]

def init_game() -> GameState:
    """初始化游戏状态"""
    return GameState(
        current_turn="player",
        player_choice=None,
        computer_choice=None,
        message="Choose your move!",
        game_over=False,
        player_score=0,
        computer_score=0,
        last_player_choice=None,
        last_computer_choice=None
    )

def determine_winner(player_choice: str, computer_choice: str) -> str:
    """判断胜负"""
    # 确保输入不为None
    if player_choice is None or computer_choice is None:
        return "error"
        
    if player_choice == computer_choice:
        return "tie"
    
    winning_moves = {
        "Rock 🪨": "Scissors ✂️",
        "Paper 📄": "Rock 🪨",
        "Scissors ✂️": "Paper 📄"
    }
    
    if winning_moves[player_choice] == computer_choice:
        return "player"
    return "computer"

def player_turn(state: GameState) -> GameState:
    """处理玩家回合"""
    if state["player_choice"] is None:
        return state
    
    state["current_turn"] = "computer"
    return state

def computer_turn(state: GameState) -> GameState:
    """处理电脑回合"""
    # 检查玩家选择是否有效
    if state["player_choice"] is None:
        state["message"] = "Error: Invalid player choice"
        state["current_turn"] = "player"
        return state
        
    # 电脑随机选择
    state["computer_choice"] = random.choice(CHOICES)
    
    # 保存这一轮的选择
    state["last_player_choice"] = state["player_choice"]
    state["last_computer_choice"] = state["computer_choice"]
    
    # 判断胜负
    winner = determine_winner(state["player_choice"], state["computer_choice"])
    
    # 更新分数和消息
    if winner == "player":
        state["player_score"] += 1
        state["message"] = f"You win! {state['player_choice']} beats {state['computer_choice']}"
    elif winner == "computer":
        state["computer_score"] += 1
        state["message"] = f"Computer wins! {state['computer_choice']} beats {state['player_choice']}"
    elif winner == "tie":
        state["message"] = f"It's a tie! Both chose {state['player_choice']}"
    else:
        state["message"] = "Error occurred during the game"
    
    # 重置当前选择
    state["player_choice"] = None
    state["computer_choice"] = None
    state["current_turn"] = "player"
    
    return state

def should_end(state: GameState) -> bool:
    """检查是否应该结束当前回合"""
    return state["current_turn"] == "player"

def build_graph() -> StateGraph:
    """构建游戏流程图"""
    # 创建状态图
    workflow = StateGraph(GameState)
    
    # 添加节点
    workflow.add_node("player_turn", player_turn)
    workflow.add_node("computer_turn", computer_turn)
    
    # 设置边和条件
    workflow.set_entry_point("player_turn")
    
    # 添加条件边
    workflow.add_edge("player_turn", "computer_turn")
    workflow.add_conditional_edges(
        "computer_turn",
        should_end,
        {
            True: END,
            False: "player_turn"
        }
    )
    
    # 编译图
    return workflow.compile()

def show_game_state():
    """显示当前游戏状态图"""
    st.markdown("### Game Flow")
    
    dot_graph = """
    digraph G {
        rankdir=LR;
        node [shape=box, style=rounded, fontname="Arial"];
        
        player [label="Player's Turn", color=blue];
        computer [label="Computer's Turn", color=red];
        
        player -> computer [color=blue];
        computer -> player [color=red];
    """
    
    # 根据当前状态添加高亮
    current_turn = st.session_state.game_state["current_turn"]
    if current_turn == "player":
        dot_graph += '    player [style="rounded,filled", fillcolor=lightblue];'
    else:
        dot_graph += '    computer [style="rounded,filled", fillcolor=lightpink];'
    
    dot_graph += "\n}"
    
    # 显示图形
    st.graphviz_chart(dot_graph)

def main():
    # 设置页面
    st.set_page_config(layout="wide", page_title="Rock Paper Scissors")
    
    # 初始化游戏状态
    if "game_started" not in st.session_state:
        st.session_state.game_started = False
    
    if not st.session_state.game_started:
        # 显示欢迎界面
        st.title("🎮 Rock Paper Scissors Game")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            ### Welcome to Rock Paper Scissors!
            
            Play against the computer in this classic game.
            
            #### Rules:
            - Rock 🪨 beats Scissors ✂️
            - Scissors ✂️ beats Paper 📄
            - Paper 📄 beats Rock 🪨
            
            Ready to play?
            """)
            
            if st.button("Start Game", use_container_width=True):
                st.session_state.game_started = True
                st.session_state.game_state = init_game()
                st.session_state.graph = build_graph()
                st.rerun()
    
    else:
        # 游戏主界面
        st.title("Rock Paper Scissors")
        
        if "game_state" not in st.session_state:
            st.session_state.game_state = init_game()
            st.session_state.graph = build_graph()
        
        # 显示分数
        col_score1, col_score2, _ = st.columns([1, 1, 1])
        with col_score1:
            st.metric("Your Score", st.session_state.game_state["player_score"])
        with col_score2:
            st.metric("Computer Score", st.session_state.game_state["computer_score"])
        
        # 显示游戏信息
        st.info(st.session_state.game_state["message"])
        
        # 创建三列布局
        col1, col2, col3 = st.columns([1.2, 1.2, 0.8])
        
        with col1:
            st.subheader("Make Your Choice")
            # 创建选择按钮
            for choice in CHOICES:
                if st.button(choice, key=f"choice_{choice}", use_container_width=True):
                    st.session_state.game_state["player_choice"] = choice
                    # 运行游戏流程
                    with st.spinner("Computer is thinking..."):
                        time.sleep(1)
                        st.session_state.game_state = st.session_state.graph.invoke(
                            st.session_state.game_state)
                    st.rerun()
        
        with col2:
            st.subheader("Last Round")
            if (st.session_state.game_state["last_player_choice"] is not None and 
                st.session_state.game_state["last_computer_choice"] is not None):
                st.write(f"Your choice: {st.session_state.game_state['last_player_choice']}")
                st.write(f"Computer's choice: {st.session_state.game_state['last_computer_choice']}")
            else:
                st.write("No moves made yet")
        
        with col3:
            st.subheader("Game Controls")
            # 显示游戏流程图
            show_game_state()
            if st.button("New Game", key="restart", use_container_width=True):
                st.session_state.game_state = init_game()
                st.rerun()

if __name__ == "__main__":
    main()
