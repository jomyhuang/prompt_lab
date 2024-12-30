import streamlit as st
import random
from typing import TypedDict, Literal, Optional, List
from langgraph.graph import StateGraph, END
import graphviz
import time

# 定义卡牌
SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

# 定义游戏状态类型
class GameState(TypedDict):
    current_turn: Literal["player", "dealer"]
    player_cards: List[str]
    dealer_cards: List[str]
    deck: List[str]
    message: str
    game_over: bool
    player_score: int
    dealer_score: int
    last_action: Optional[str]
    player_wins: int
    dealer_wins: int

def calculate_hand(cards: List[str]) -> int:
    """计算手牌点数"""
    value = 0
    aces = 0
    
    for card in cards:
        rank = card[:-1]  # 移除花色
        if rank in ["J", "Q", "K"]:
            value += 10
        elif rank == "A":
            aces += 1
        else:
            value += int(rank)
    
    # 处理A的点数
    for _ in range(aces):
        if value + 11 <= 21:
            value += 11
        else:
            value += 1
            
    return value

def init_game() -> GameState:
    """初始化游戏状态"""
    # 创建新牌组
    deck = [f"{rank}{suit}" for suit in SUITS for rank in RANKS]
    random.shuffle(deck)
    
    # 发初始牌
    player_cards = [deck.pop(), deck.pop()]
    dealer_cards = [deck.pop()]
    
    return GameState(
        current_turn="player",
        player_cards=player_cards,
        dealer_cards=dealer_cards,
        deck=deck,
        message="Your turn! Hit or Stand?",
        game_over=False,
        player_score=calculate_hand(player_cards),
        dealer_score=calculate_hand(dealer_cards),
        last_action=None,
        player_wins=0,
        dealer_wins=0
    )

def player_turn(state: GameState) -> GameState:
    """处理玩家回合"""
    if state["last_action"] is None:
        return state
        
    if state["last_action"] == "hit":
        # 抽一张牌
        state["player_cards"].append(state["deck"].pop())
        state["player_score"] = calculate_hand(state["player_cards"])
        
        # 检查是否爆牌
        if state["player_score"] > 21:
            state["message"] = "Bust! Dealer wins!"
            state["game_over"] = True
            state["dealer_wins"] += 1
            return state
            
        state["message"] = "Your turn! Hit or Stand?"
        
    elif state["last_action"] == "stand":
        state["current_turn"] = "dealer"
        state["message"] = "Dealer's turn..."
        
    return state

def dealer_turn(state: GameState) -> GameState:
    """处理庄家回合"""
    # 庄家继续抽牌直到17点或以上
    while state["dealer_score"] < 17:
        state["dealer_cards"].append(state["deck"].pop())
        state["dealer_score"] = calculate_hand(state["dealer_cards"])
    
    # 判断胜负
    if state["dealer_score"] > 21:
        state["message"] = "Dealer busts! You win!"
        state["player_wins"] += 1
    elif state["dealer_score"] > state["player_score"]:
        state["message"] = f"Dealer wins with {state['dealer_score']}!"
        state["dealer_wins"] += 1
    elif state["dealer_score"] < state["player_score"]:
        state["message"] = f"You win with {state['player_score']}!"
        state["player_wins"] += 1
    else:
        state["message"] = "It's a tie!"
    
    state["game_over"] = True
    return state

def should_end(state: GameState) -> bool:
    """检查是否应该结束当前回合"""
    return state["game_over"] or state["current_turn"] == "player"

def build_graph() -> StateGraph:
    """构建游戏流程图"""
    workflow = StateGraph(GameState)
    
    # 添加节点
    workflow.add_node("player_turn", player_turn)
    workflow.add_node("dealer_turn", dealer_turn)
    
    # 设置边和条件
    workflow.set_entry_point("player_turn")
    
    workflow.add_edge("player_turn", "dealer_turn")
    workflow.add_conditional_edges(
        "dealer_turn",
        should_end,
        {
            True: END,
            False: "player_turn"
        }
    )
    
    return workflow.compile()

def show_game_state():
    """显示游戏流程图"""
    dot = graphviz.Digraph()
    dot.node("Player's Turn", "Player's Turn")
    dot.node("Dealer's Turn", "Dealer's Turn")
    
    # 添加边
    dot.edge("Player's Turn", "Dealer's Turn", "Stand")
    dot.edge("Player's Turn", "Player's Turn", "Hit")
    dot.edge("Dealer's Turn", "End", "Game Over")
    
    st.graphviz_chart(dot)

def main():
    # 设置页面
    st.set_page_config(layout="wide", page_title="Blackjack")
    
    # 初始化游戏状态
    if "game_started" not in st.session_state:
        st.session_state.game_started = False
    
    if not st.session_state.game_started:
        # 显示欢迎界面
        st.title("🎰 Blackjack")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            ### Welcome to Blackjack!
            
            Try to beat the dealer by getting a hand value closer to 21.
            
            #### Rules:
            - Number cards (2-10) are worth their face value
            - Face cards (J, Q, K) are worth 10
            - Aces are worth 1 or 11, whichever is better
            - If you go over 21, you bust and lose
            
            Ready to play?
            """)
            
            if st.button("Start Game", use_container_width=True):
                st.session_state.game_started = True
                st.session_state.game_state = init_game()
                st.session_state.graph = build_graph()
                st.rerun()
    
    else:
        # 游戏主界面
        st.title("Blackjack")
        
        if "game_state" not in st.session_state:
            st.session_state.game_state = init_game()
            st.session_state.graph = build_graph()
        
        # 显示分数
        col_score1, col_score2, _ = st.columns([1, 1, 1])
        with col_score1:
            st.metric("Your Wins", st.session_state.game_state["player_wins"])
        with col_score2:
            st.metric("Dealer Wins", st.session_state.game_state["dealer_wins"])
        
        # 显示游戏信息
        st.info(st.session_state.game_state["message"])
        
        # 创建三列布局
        col1, col2, col3 = st.columns([1.2, 1.2, 0.8])
        
        with col1:
            st.subheader("Your Hand")
            st.write(f"Cards: {' '.join(st.session_state.game_state['player_cards'])}")
            st.write(f"Score: {st.session_state.game_state['player_score']}")
            
            if not st.session_state.game_state["game_over"]:
                col_hit, col_stand = st.columns(2)
                with col_hit:
                    if st.button("Hit", key="hit", use_container_width=True):
                        st.session_state.game_state["last_action"] = "hit"
                        with st.spinner("Dealing card..."):
                            time.sleep(0.5)
                            st.session_state.game_state = st.session_state.graph.invoke(
                                st.session_state.game_state)
                        st.rerun()
                
                with col_stand:
                    if st.button("Stand", key="stand", use_container_width=True):
                        st.session_state.game_state["last_action"] = "stand"
                        with st.spinner("Dealer's turn..."):
                            time.sleep(0.5)
                            st.session_state.game_state = st.session_state.graph.invoke(
                                st.session_state.game_state)
                        st.rerun()
        
        with col2:
            st.subheader("Dealer's Hand")
            if st.session_state.game_state["game_over"]:
                st.write(f"Cards: {' '.join(st.session_state.game_state['dealer_cards'])}")
                st.write(f"Score: {st.session_state.game_state['dealer_score']}")
            else:
                # 只显示第一张牌
                st.write(f"Cards: {st.session_state.game_state['dealer_cards'][0]} ?")
                st.write("Score: ?")
        
        with col3:
            st.subheader("Game Controls")
            # 显示游戏流程图
            show_game_state()
            if st.button("New Game", key="restart", use_container_width=True):
                # 保持胜场记录，但重置其他状态
                player_wins = st.session_state.game_state["player_wins"]
                dealer_wins = st.session_state.game_state["dealer_wins"]
                st.session_state.game_state = init_game()
                st.session_state.game_state["player_wins"] = player_wins
                st.session_state.game_state["dealer_wins"] = dealer_wins
                st.rerun()

if __name__ == "__main__":
    main()
