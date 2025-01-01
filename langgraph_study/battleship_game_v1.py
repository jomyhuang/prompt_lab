import streamlit as st
from typing import TypedDict, Annotated, List, Tuple, Optional
from langgraph.graph import StateGraph, START, END
import random
import numpy as np
import time

# 定义船只类型和大小
SHIPS = {
    "Aircraft Carrier": 5,
    "Battleship": 4,
    "Cruiser": 3,
    "Destroyer": 2
}

# 定义棋盘大小
BOARD_SIZE = 10

# 定义游戏状态
class GameState(TypedDict):
    player_board: List[List[str]]  # 玩家的棋盘
    computer_board: List[List[str]]  # 电脑的棋盘
    player_shots: List[List[str]]  # 玩家的射击记录
    computer_shots: List[List[str]]  # 电脑的射击记录
    player_ships: dict  # 玩家的船只位置
    computer_ships: dict  # 电脑的船只位置
    current_turn: str  # 当前回合：'player' 或 'computer'
    game_over: bool  # 游戏是否结束
    winner: Optional[str]  # 获胜者
    message: str  # 游戏消息

def create_empty_board() -> List[List[str]]:
    return [[" " for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

def is_valid_placement(board: List[List[str]], ship_size: int, start_row: int, 
                      start_col: int, is_horizontal: bool) -> bool:
    if is_horizontal:
        if start_col + ship_size > BOARD_SIZE:
            return False
        return all(board[start_row][start_col + i] == " " 
                  for i in range(ship_size))
    else:
        if start_row + ship_size > BOARD_SIZE:
            return False
        return all(board[start_row + i][start_col] == " " 
                  for i in range(ship_size))

def place_ship(board: List[List[str]], ship_name: str, ship_size: int, 
               start_row: int, start_col: int, is_horizontal: bool) -> List[Tuple[int, int]]:
    positions = []
    for i in range(ship_size):
        if is_horizontal:
            board[start_row][start_col + i] = "O"
            positions.append((start_row, start_col + i))
        else:
            board[start_row + i][start_col] = "O"
            positions.append((start_row + i, start_col))
    return positions

def place_ships_randomly(board: List[List[str]]) -> dict:
    ships_positions = {}
    for ship_name, ship_size in SHIPS.items():
        while True:
            is_horizontal = random.choice([True, False])
            if is_horizontal:
                start_row = random.randint(0, BOARD_SIZE - 1)
                start_col = random.randint(0, BOARD_SIZE - ship_size)
            else:
                start_row = random.randint(0, BOARD_SIZE - ship_size)
                start_col = random.randint(0, BOARD_SIZE - 1)
            
            if is_valid_placement(board, ship_size, start_row, start_col, is_horizontal):
                positions = place_ship(board, ship_name, ship_size, 
                                    start_row, start_col, is_horizontal)
                ships_positions[ship_name] = positions
                break
    return ships_positions

# 初始化游戏状态
def init_game() -> GameState:
    if 'game_state' in st.session_state:
        del st.session_state.game_state
    
    player_board = create_empty_board()
    computer_board = create_empty_board()
    
    player_ships = place_ships_randomly(player_board)
    computer_ships = place_ships_randomly(computer_board)
    
    return GameState(
        player_board=player_board,
        computer_board=computer_board,
        player_shots=create_empty_board(),
        computer_shots=create_empty_board(),
        player_ships=player_ships,
        computer_ships=computer_ships,
        current_turn='player',
        game_over=False,
        winner=None,
        message="Game started! Please select a position to attack."
    )

def check_ship_sunk(ships: dict, row: int, col: int) -> Optional[str]:
    for ship_name, positions in ships.items():
        if (row, col) in positions:
            # 检查这艘船是否所有位置都被击中
            return ship_name
    return None

def make_shot(state: GameState, row: int, col: int, is_player: bool) -> GameState:
    if is_player:
        target_board = state["computer_board"]
        shots_board = state["player_shots"]
        ships = state["computer_ships"]
        shooter = "Player"
    else:
        target_board = state["player_board"]
        shots_board = state["computer_shots"]
        ships = state["player_ships"]
        shooter = "Computer"

    if target_board[row][col] == "O":  # 击中
        shots_board[row][col] = "X"
        ship_name = check_ship_sunk(ships, row, col)
        if ship_name:
            state["message"] = f"{shooter} hit and sunk the {ship_name}!"
        else:
            state["message"] = f"{shooter} hit a ship!"
    else:  # 未击中
        shots_board[row][col] = "·"
        state["message"] = f"{shooter} missed the shot."

    return state

def check_winner(state: GameState) -> Optional[str]:
    # 检查是否所有船只都被击沉
    def all_ships_sunk(board: List[List[str]], shots: List[List[str]]) -> bool:
        return all(
            board[i][j] != "O" or shots[i][j] == "X"
            for i in range(BOARD_SIZE)
            for j in range(BOARD_SIZE)
        )

    if all_ships_sunk(state["computer_board"], state["player_shots"]):
        return "player"
    if all_ships_sunk(state["player_board"], state["computer_shots"]):
        return "computer"
    return None

# 玩家回合
def player_turn(state: GameState) -> GameState:
    if state["current_turn"] != "player":
        return state
    
    # 玩家的行动在UI中处理
    return state

# 电脑回合
def computer_turn(state: GameState) -> GameState:
    if state["current_turn"] != "computer" or state["game_over"]:
        return state
    
    # 简单的AI：随机选择一个未射击过的位置
    while True:
        row = random.randint(0, BOARD_SIZE - 1)
        col = random.randint(0, BOARD_SIZE - 1)
        if state["computer_shots"][row][col] == " ":
            state = make_shot(state, row, col, False)
            break
    
    # 检查是否获胜
    winner = check_winner(state)
    if winner:
        state["game_over"] = True
        state["winner"] = winner
        state["message"] += " Game over!"
        if winner == "computer":
            state["message"] += " Computer wins!"
        else:
            state["message"] += " Player wins!"
    else:
        state["current_turn"] = "player"
    
    return state

# 构建游戏流程图
def build_graph():
    workflow = StateGraph(GameState)
    
    # 添加节点
    workflow.add_node("player_turn", player_turn)
    workflow.add_node("computer_turn", computer_turn)
    
    # 添加边
    workflow.add_edge(START, "player_turn")
    workflow.add_edge("player_turn", "computer_turn")
    workflow.add_edge("computer_turn", END)
    
    return workflow.compile()

def make_move(row: int, col: int):
    if st.session_state.game_state["current_turn"] != "player" or \
       st.session_state.game_state["game_over"] or \
       st.session_state.game_state["player_shots"][row][col] != " ":
        return

    # 玩家射击
    st.session_state.game_state = make_shot(
        st.session_state.game_state, row, col, True)
    
    # 检查是否获胜
    winner = check_winner(st.session_state.game_state)
    if winner:
        st.session_state.game_state["game_over"] = True
        st.session_state.game_state["winner"] = winner
        st.session_state.game_state["message"] += " Game over!"
        if winner == "player":
            st.session_state.game_state["message"] += " Player wins!"
        else:
            st.session_state.game_state["message"] += " Computer wins!"
    else:
        st.session_state.game_state["current_turn"] = "computer"
        time.sleep(1)  # 延迟1秒
        # 运行游戏流程
        with st.spinner("Computer is thinking..."):
            time.sleep(1)  # 延迟1秒
            st.session_state.game_state = st.session_state.graph.invoke(
                st.session_state.game_state)
    
    st.rerun()

def render_board(board: List[List[str]], shots: List[List[str]], 
                show_ships: bool = True, board_type: str = "player") -> None:
    # 创建表头
    cols = st.columns([0.3] + [1] * BOARD_SIZE)  
    cols[0].markdown("&nbsp;")  # 空白占位
    for i in range(BOARD_SIZE):
        cols[i + 1].markdown(f"**{i}**")
    
    # 创建棋盘
    for i in range(BOARD_SIZE):
        cols = st.columns([0.3] + [1] * BOARD_SIZE)  
        cols[0].markdown(f"**{i}**")  # 行号
        for j in range(BOARD_SIZE):
            cell = ""
            if shots[i][j] != " ":
                if board_type == "player":  # 这是玩家的棋盘，显示电脑的攻击
                    if shots[i][j] == "X":  # 电脑命中
                        cell = "🔥"  # 火焰表示被击中
                    else:  # 电脑未命中
                        cell = "💨"  # 烟雾表示未命中
                else:  # 这是电脑的棋盘，显示玩家的攻击
                    if shots[i][j] == "X":  # 玩家命中
                        cell = "💥"  # 爆炸表示命中
                    else:  # 玩家未命中
                        cell = "🌊"  # 水花表示未命中
            elif show_ships and board[i][j] == "O":
                cell = "🚢"  # 使用船只表情代替 O
            
            if cell == "":
                cell = "⬜"  # 使用白色方块代替空格
            
            # 创建可点击的按钮或显示单元格
            if shots[i][j] == " " and not st.session_state.game_state["game_over"] and board_type == "computer":
                # 使用空格来增加按钮的宽度
                if cols[j + 1].button("     ", key=f"{board_type}_btn_{i}_{j}"):
                    make_move(i, j)
            else:
                cols[j + 1].markdown(cell)

def show_welcome_screen():
    st.title("🚢 Welcome to Battleship Game!")
    
    # 使用列来居中显示内容
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        ### About the Game
        Battleship is a classic strategy game where you compete against the computer to sink each other's fleet.
        
        ### Your Fleet
        - Aircraft Carrier (5 cells)
        - Battleship (4 cells)
        - Cruiser (3 cells)
        - Destroyer (2 cells)
        
        ### How to Play
        1. Your ships are automatically placed on your board
        2. Take turns with the computer to attack each other's fleet
        3. Click on the empty cells in the Attack Zone to make your move
        4. First to sink all enemy ships wins!
        
        ### Ready to Play?
        """)
        
        # 开始游戏按钮
        if st.button("Start Game", use_container_width=True):
            st.session_state.game_started = True
            st.session_state.game_state = init_game()
            st.session_state.graph = build_graph()
            st.rerun()

def main():
    # 设置页面宽度为宽屏模式
    st.set_page_config(layout="wide", page_title="Battleship Game")
    
    # 初始化游戏状态
    if "game_started" not in st.session_state:
        st.session_state.game_started = False
    
    # 显示欢迎界面或游戏界面
    if not st.session_state.game_started:
        show_welcome_screen()
    else:
        # 游戏主界面代码
        st.title("Battleship Game")
        
        if "game_state" not in st.session_state:
            st.session_state.game_state = init_game()
            st.session_state.graph = build_graph()
        
        # 使用容器来控制内容宽度
        with st.container():
            # 显示游戏信息
            col_info1, col_info2, _ = st.columns([1, 1, 1])
            with col_info1:
                st.info(st.session_state.game_state["message"])
            with col_info2:
                # 显示当前回合
                turn_text = "Player's Turn" if st.session_state.game_state["current_turn"] == "player" else "Computer's Turn"
                st.subheader(f"Current Turn: {turn_text}")
        
        # 创建三列来平行显示棋盘和说明，调整列宽比例
        col1, col2, col3 = st.columns([1.2, 1.2, 0.8])
        
        # 在左列显示玩家的棋盘
        with col1:
            st.subheader("Your Fleet")
            render_board(st.session_state.game_state["player_board"],
                        st.session_state.game_state["computer_shots"],
                        show_ships=True,
                        board_type="player")
            
            # 显示游戏流程图
            st.markdown("### Game Flow")
            # 使用 graphviz 创建图形
            dot_graph = """
            digraph G {
                rankdir=LR;
                node [shape=box, style=rounded, fontname="Arial"];
                
                start [label="START", color=gray];
                player [label="Player's Turn", color=blue];
                computer [label="Computer's Turn", color=red];
                end [label="END", color=gray];
                
                start -> player [color=gray];
                player -> computer [color=blue];
                computer -> end [color=red];
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
            
            # 显示当前状态信息
            with st.expander("Game State Details", expanded=False):
                state = st.session_state.game_state
                st.markdown(f"""
                - Current Turn: **{state['current_turn'].title()}**
                - Player Hits: **{sum(row.count('X') for row in state['player_shots'])}**
                - Computer Hits: **{sum(row.count('X') for row in state['computer_shots'])}**
                - Game Status: **{'In Progress' if not state['game_over'] else 'Game Over'}**
                """)
        
        # 在中间列显示电脑的棋盘
        with col2:
            st.subheader("Attack Zone")
            st.caption("Click empty cells to attack")
            render_board(st.session_state.game_state["computer_board"],
                        st.session_state.game_state["player_shots"],
                        show_ships=False,
                        board_type="computer")
        
        # 在右列显示说明
        with col3:
            st.subheader("Game Guide")
            
            # 使用卡片式布局来组织说明内容
            with st.expander("Legend", expanded=True):
                st.markdown("""
                🚢 : Your Ships  
                💥 : Your Hit  
                🌊 : Your Miss  
                🔥 : Computer's Hit  
                💨 : Computer's Miss  
                ⬜ : Unexplored Area
                """)
            
            with st.expander("Ships", expanded=True):
                st.markdown("""
                - Aircraft Carrier (5 cells)
                - Battleship (4 cells)
                - Cruiser (3 cells)
                - Destroyer (2 cells)
                """)
            
            with st.expander("Rules", expanded=True):
                st.markdown("""
                1. Take turns attacking enemy fleet
                2. Sink all enemy ships to win
                3. Ships can be placed horizontally or vertically
                """)
            
            # 添加一些空间
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 重置游戏按钮，使用列来居中显示
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                if st.button("New Game", key="restart", use_container_width=True):
                    st.session_state.game_state = init_game()
                    st.rerun()

if __name__ == "__main__":
    main()
