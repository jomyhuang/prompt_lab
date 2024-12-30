import streamlit as st
import random
from typing import TypedDict, Literal, Optional, List
from langgraph.graph import StateGraph, END, START
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
import time
from poker_component import render_cards
from game_controls import render_action_buttons, render_game_stats, render_game_message

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
    player_info: Optional[dict]
    dealer_info: Optional[dict]
    checking: str

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
    
    # 发初始牌 - 玩家和庄家各两张
    player_cards = [deck.pop(), deck.pop()]
    dealer_cards = [deck.pop(), deck.pop()]  # 庄家也发两张牌
    
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
        dealer_wins=0,
        checking="checking_init"
    )

def player_turn(state: GameState) -> GameState:
    """处理玩家回合
    使用interrupt等待玩家操作,实现Human-in-loop模式
    """
    # 只在玩家回合且游戏未结束时等待操作
    if state["current_turn"] == "player" and not state["game_over"]:
        # 准备展示给玩家的游戏状态信息
        game_info = {
            "message": "Your turn! Hit or Stand? ---------RIGHT HERE",
            "player_info": {
                "cards": state["player_cards"],
                "score": state["player_score"]
            },
            "dealer_info": {
                "visible_card": state["dealer_cards"][0],  # 只显示第一张牌
                "hidden_cards": len(state["dealer_cards"]) - 1,  # 其余牌数
                "visible_score": calculate_hand([state["dealer_cards"][0]])  # 只计算可见牌的分数
            },
            "game_stats": {
                "player_wins": state["player_wins"],
                "dealer_wins": state["dealer_wins"]
            },
            "checking": "this is a test"
        }
        
        # 使用interrupt等待玩家操作
        print( f" action = !! beforeinterrupt")
        action = interrupt(game_info)
        print( f" action = !! interrupt {action}")
        
        # 处理玩家操作
        if action == "hit":
            # 抽一张牌
            new_card = state["deck"].pop()
            state["player_cards"].append(new_card)
            state["player_score"] = calculate_hand(state["player_cards"])
            
            state["checking"] = "this is a test after hit"
            # 检查是否爆牌
            if state["player_score"] > 21:
                state["message"] = f"Bust! You drew {new_card} and went over 21!"
                state["game_over"] = True
                state["dealer_wins"] += 1
            else:
                state["message"] = f"You drew {new_card}. Hit or Stand?"
                
        elif action == "stand":
            state["current_turn"] = "dealer"
            state["message"] = f"You stand with {state['player_score']}. Dealer's turn..."
    
    return state

def dealer_turn(state: GameState) -> GameState:
    """处理庄家回合"""
    if state["current_turn"] == "dealer" and not state["game_over"]:
        # 庄家继续抽牌直到17点或以上
        while state["dealer_score"] < 17:
            new_card = state["deck"].pop()
            state["dealer_cards"].append(new_card)
            state["dealer_score"] = calculate_hand(state["dealer_cards"])
            state["message"] += f"\nDealer drew {new_card}."
        
        # 判断胜负
        if state["dealer_score"] > 21:
            state["message"] = f"Dealer busts with {state['dealer_score']}! You win!"
            state["player_wins"] += 1
        elif state["dealer_score"] > state["player_score"]:
            state["message"] = f"Dealer wins with {state['dealer_score']} vs your {state['player_score']}!"
            state["dealer_wins"] += 1
        elif state["dealer_score"] < state["player_score"]:
            state["message"] = f"You win with {state['player_score']} vs dealer's {state['dealer_score']}!"
            state["player_wins"] += 1
        else:
            state["message"] = f"It's a tie at {state['player_score']}!"
        
        state["game_over"] = True
    
    return state

def should_end(state: GameState) -> bool:
    """检查是否应该结束当前回合"""
    # 只有在游戏结束时才返回True
    return state["game_over"]

def build_graph(checkpointer=None) -> StateGraph:
    """构建游戏流程图"""
    # 创建StateGraph
    workflow = StateGraph(GameState)
    
    # 添加节点
    workflow.add_node("player_turn", player_turn)
    workflow.add_node("dealer_turn", dealer_turn)
    
    # 设置边和条件
    workflow.add_edge(START, "player_turn")
    
    # 从player_turn可以:
    # 1. 继续留在player_turn (hit)
    # 2. 转到dealer_turn (stand)
    # 3. 游戏结束时直接到END
    workflow.add_conditional_edges(
        "player_turn",
        lambda x: "end" if x["game_over"] else ("dealer" if x["current_turn"] == "dealer" else "player"),
        {
            "player": "player_turn",  # hit时继续在player_turn
            "dealer": "dealer_turn",  # stand时转到dealer_turn
            "end": END  # 玩家爆牌时直接结束
        }
    )
    
    # 从dealer_turn可以:
    # 1. 结束游戏 (game_over为True)
    workflow.add_conditional_edges(
        "dealer_turn",
        should_end,
        {
            True: END,
            False: "player_turn"
        }
    )
    
    return workflow.compile(checkpointer=checkpointer)

def show_game_state():
    """显示游戏流程图"""
    st.markdown("### Game Flow")
    
    dot_graph = """
    digraph G {
        rankdir=LR;
        node [shape=box, style=rounded, fontname="Arial"];
        
        start [label="START", color=gray];
        player [label="Player's Turn", color=blue];
        dealer [label="Dealer's Turn", color=red];
        end [label="END", color=gray];
        
        start -> player [color=gray];
        player -> dealer [label="Stand", color=blue];
        player -> player [label="Hit", color=blue];
        dealer -> end [label="Game Over", color=red];
    """
    
    # 根据当前状态添加高亮
    current_turn = st.session_state.game_state["current_turn"]
    game_over = st.session_state.game_state["game_over"]
    
    if game_over:
        # 游戏结束时,显示结果
        player_score = st.session_state.game_state["player_score"]
        dealer_score = st.session_state.game_state["dealer_score"]
        
        if player_score > 21:
            result = "Player Bust!"
        elif dealer_score > 21:
            result = "Dealer Bust!"
        elif player_score > dealer_score:
            result = "Player Wins!"
        elif dealer_score > player_score:
            result = "Dealer Wins!"
        else:
            result = "Tie Game!"
            
        dot_graph += f'    end [label="END\\n{result}", style="rounded,filled", fillcolor=lightgray];'
    elif current_turn == "player":
        dot_graph += '    player [style="rounded,filled", fillcolor=lightblue];'
    else:
        dot_graph += '    dealer [style="rounded,filled", fillcolor=lightpink];'
    
    dot_graph += "\n}"
    
    # 显示图形
    st.graphviz_chart(dot_graph)

def main():
    # 设置页面
    st.set_page_config(layout="wide", page_title="LangGraph Blackjack")
    
    # 初始化游戏状态
    if "game_started" not in st.session_state:
        st.session_state.game_started = False
        st.session_state.thread_id = str(random.randint(1, 1000000))
    
    if not st.session_state.game_started:
        # 显示欢迎界面
        st.title("🎰 LangGraph Blackjack")
        
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
                initial_state = init_game()
                # 创建带checkpointer的graph
                checkpointer = MemorySaver()
                st.session_state.graph = build_graph(checkpointer=checkpointer)
                # 使用graph.invoke初始化游戏状态
                config = {"configurable": {"thread_id": st.session_state.thread_id}}
                st.session_state.game_state = st.session_state.graph.invoke(initial_state, config=config)
                print(" st.session_state.game_state = !!")
                print( st.session_state.game_state )
                print( "checking = !!", st.session_state.game_state["checking"])
                st.rerun()
    
    else:
        # 游戏主界面
        st.title("Blackjack")
        
        if "game_state" not in st.session_state:
            initial_state = init_game()
            checkpointer = MemorySaver()
            st.session_state.graph = build_graph(checkpointer=checkpointer)
            # 使用graph.invoke初始化游戏状态
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            st.session_state.game_state = st.session_state.graph.invoke(initial_state, config=config)
            
        # 显示分数
        render_game_stats(st.session_state.game_state["player_wins"], 
                         st.session_state.game_state["dealer_wins"])
        
        # 显示游戏信息
        if st.session_state.game_state["game_over"]:
            # 游戏结束时,显示结果
            player_score = st.session_state.game_state["player_score"]
            dealer_score = st.session_state.game_state["dealer_score"]
            
            if player_score > 21:
                render_game_message("游戏结束 - 你爆牌了! 庄家获胜!", "error")
            elif dealer_score > 21:
                render_game_message("游戏结束 - 庄家爆牌! 你赢了!", "success")
            elif player_score > dealer_score:
                render_game_message(f"游戏结束 - 你赢了! (你的点数: {player_score}, 庄家点数: {dealer_score})", "success")
            elif dealer_score > player_score:
                render_game_message(f"游戏结束 - 庄家获胜! (庄家点数: {dealer_score}, 你的点数: {player_score})", "error")
            else:
                render_game_message(f"游戏结束 - 平局! (双方点数: {player_score})", "warning")
        else:
            render_game_message(st.session_state.game_state["message"], "info")
        
        # 创建三列布局
        col1, col2, col3 = st.columns([1.2, 1.2, 0.8])
        
        with col1:
            st.subheader("Your Hand")
            render_cards(st.session_state.game_state['player_cards'])
            st.write(f"Score: {st.session_state.game_state['player_score']}")
            
            if not st.session_state.game_state["game_over"]:
                # 使用新的按钮组件并获取返回值
                action = render_action_buttons(disabled=False)
                
                # 处理按钮点击事件
                if action == "hit":
                    with st.spinner("Dealing card..."):
                        time.sleep(0.5)
                        config = {"configurable": {"thread_id": st.session_state.thread_id}}
                        st.session_state.game_state = st.session_state.graph.invoke(
                            Command(resume="hit"), config=config)
                        print("after invoke resume")
                        print(st.session_state.game_state)
                    st.rerun()
                
                elif action == "stand":
                    with st.spinner("Dealer's turn..."):
                        time.sleep(0.5)
                        config = {"configurable": {"thread_id": st.session_state.thread_id}}
                        st.session_state.game_state = st.session_state.graph.invoke(
                            Command(resume="stand"), config=config)
                    st.rerun()
        
        with col2:
            st.subheader("Dealer's Hand")
            if st.session_state.game_state["game_over"]:
                render_cards(st.session_state.game_state['dealer_cards'])
                st.write(f"Score: {st.session_state.game_state['dealer_score']}")
            else:
                # 只显示第一张牌,其他牌显示背面
                render_cards(st.session_state.game_state['dealer_cards'], hidden=True)
                st.write("Score: ?")
        
        with col3:
            st.subheader("Game Controls")

            if st.button("New Game", key="restart", use_container_width=True):
                initial_state = init_game()
                # 保持胜场记录
                initial_state["player_wins"] = st.session_state.game_state["player_wins"]
                initial_state["dealer_wins"] = st.session_state.game_state["dealer_wins"]
                # 使用graph.invoke重新开始游戏
                config = {"configurable": {"thread_id": st.session_state.thread_id}}
                st.session_state.game_state = st.session_state.graph.invoke(initial_state, config=config)
                st.rerun()
            
            with st.expander("Game State", expanded=False):
                    st.json(st.session_state.game_state)

        with st.container():
            show_game_state()
                
if __name__ == "__main__":
    main()
