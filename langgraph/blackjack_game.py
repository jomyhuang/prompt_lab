# Import required libraries
import streamlit as st
import random
from typing import TypedDict, Literal, Optional, List
from langgraph.graph import StateGraph, END, START
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
import time
from poker_component import render_cards
from game_controls import render_action_buttons, render_game_stats, render_game_message

# Define card suits and ranks
SUITS = ["♠", "♥", "♦", "♣"]  # 黑桃 红心 方块 梅花
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]  # A到K的点数

# Define game state type
class GameState(TypedDict):
    """Game state type definition.
    
    Attributes:
        current_turn: Current player's turn (player or dealer)
        player_cards: List of player's cards
        dealer_cards: List of dealer's cards
        deck: Remaining cards in deck
        message: Game message
        game_over: Whether game is over
        player_score: Player's current score
        dealer_score: Dealer's current score
        last_action: Last action taken
        player_wins: Number of player wins
        dealer_wins: Number of dealer wins
        player_info: Player information dictionary
        dealer_info: Dealer information dictionary
        checking: State check flag
    """
    current_turn: Literal["player", "dealer"]  # 当前回合的玩家(player或dealer)
    player_cards: List[str]  # 玩家手牌列表
    dealer_cards: List[str]  # 庄家手牌列表
    deck: List[str]  # 剩余牌堆
    message: str  # 游戏消息
    game_over: bool  # 游戏是否结束
    player_score: int  # 玩家当前点数
    dealer_score: int  # 庄家当前点数
    last_action: Optional[str]  # 最后执行的动作
    player_wins: int  # 玩家胜场数
    dealer_wins: int  # 庄家胜场数
    player_info: Optional[dict]  # 玩家信息字典
    dealer_info: Optional[dict]  # 庄家信息字典
    checking: str  # 检查状态标记

def calculate_hand(cards: List[str]) -> int:
    """Calculate hand value.
    
    Calculation rules:
    - Number cards (2-10) are worth their face value
    - Face cards (J Q K) are worth 10
    - Aces are worth 1 or 11, whichever is more advantageous
    
    Args:
        cards: List of cards to calculate
        
    Returns:
        int: Total hand value
    """
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
    """Initialize game state.
    
    Creates a new game state including:
    1. Shuffling and creating a new deck
    2. Dealing initial cards to player and dealer
    3. Initializing game-related states
    
    Returns:
        GameState: Initialized game state
    """
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
    """Handle player's turn with Human-in-loop implementation.
    
    This is a key Human-in-loop node that uses langgraph's interrupt mechanism
    for human-computer interaction. When it's player's turn, the game flow
    pauses here waiting for player input.
    
    Workflow:
    1. Check if it's player's turn and game is not over
    2. Prepare game state info to show player (cards, scores, etc)
    3. Use interrupt to pause execution, wait for player action (hit/stand)
    4. Update game state based on player's action
    5. Return updated state to continue game flow
    
    Human-in-loop implementation points:
    - Use interrupt() function to pause execution
    - Package game state as dictionary to pass to frontend
    - Wait for player selection in UI
    - Resume with Command(resume=action)
    
    Args:
        state: Current game state
        
    Returns:
        Updated game state
    """
    # 只在玩家回合且游戏未结束时等待操作
    if state["current_turn"] == "player" and not state["game_over"]:
        # 准备展示给玩家的游戏状态信息
        # game_info = {
        #     "message": "Your turn! Hit or Stand?",
        #     "player_info": {
        #         "cards": state["player_cards"],
        #         "score": state["player_score"]
        #     },
        #     "dealer_info": {
        #         "visible_card": state["dealer_cards"][0],  # 只显示第一张牌
        #         "hidden_cards": len(state["dealer_cards"]) - 1,  # 其余牌数
        #         "visible_score": calculate_hand([state["dealer_cards"][0]])  # 只计算可见牌的分数
        #     },
        #     "game_stats": {
        #         "player_wins": state["player_wins"],
        #         "dealer_wins": state["dealer_wins"]
        #     }
        # }
        
        # 使用interrupt等待玩家操作
        # 此处会暂停执行 直到收到玩家的操作指令
        # action = interrupt(game_info)
        # 检查: 目前传入值为exceptiong 捕获的value值, 用途状况不明
        action = interrupt("interrupt from player_turn ----")
        
        # 处理玩家操作
        if action == "hit":
            # 抽一张牌
            new_card = state["deck"].pop()
            state["player_cards"].append(new_card)
            state["player_score"] = calculate_hand(state["player_cards"])
            
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
    """Handle dealer's turn.
    
    Dealer follows a fixed strategy:
    - Continue drawing cards until score is 17 or higher
    - Then stop and determine the winner
    
    Args:
        state: Current game state
        
    Returns:
        Updated game state
    """
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
    """Check if current round should end.
    
    Args:
        state: Current game state
        
    Returns:
        bool: Whether game should end
    """
    return state["game_over"]

def build_graph(checkpointer=None) -> StateGraph:
    """Build game flow graph.
    
    Uses LangGraph to build state transition graph for Blackjack:
    
    1. Create StateGraph based on GameState
    2. Add player turn and dealer turn nodes
    3. Set up edges and conditions between nodes
    
    Game flow:
    START -> player_turn -> dealer_turn -> END
    
    State transition rules:
    - player_turn node:
      * hit: stay in player_turn
      * stand: go to dealer_turn
      * bust: go directly to END
    - dealer_turn node:
      * game over: go to END
      * otherwise: return to player_turn
    
    Args:
        checkpointer: Optional state checkpoint saver
        
    Returns:
        Compiled game flow graph
    """
    # 创建StateGraph
    workflow = StateGraph(GameState)
    
    # 添加节点
    workflow.add_node("player_turn", player_turn)  # 玩家回合节点
    workflow.add_node("dealer_turn", dealer_turn)  # 庄家回合节点
    
    # 设置边和条件
    workflow.add_edge(START, "player_turn")  # 游戏从玩家回合开始
    
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
    """Show game flow graph.
    
    Uses Graphviz to visualize current game state and flow:
    1. Display basic game flow graph structure
    2. Highlight current node based on state
    3. Show result when game is over
    """
    st.markdown("### Game Flow")
    
    # 基本图结构定义
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
        # 游戏结束时 显示结果
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
            # 游戏结束时, 显示结果
            player_score = st.session_state.game_state["player_score"]
            dealer_score = st.session_state.game_state["dealer_score"]
            
            if player_score > 21:
                render_game_message("Game Over - You busted! Dealer wins!", "error")
            elif dealer_score > 21:
                render_game_message("Game Over - Dealer busted! You win!", "success")
            elif player_score > dealer_score:
                render_game_message(f"Game Over - You win! (Your score: {player_score}, Dealer's score: {dealer_score})", "success")
            elif dealer_score > player_score:
                render_game_message(f"Game Over - Dealer wins! (Dealer's score: {dealer_score}, Your score: {player_score})", "error")
            else:
                render_game_message(f"Game Over - It's a tie! (Both scores: {player_score})", "warning")
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
                # 只显示第一张牌, 其他牌显示背面
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
