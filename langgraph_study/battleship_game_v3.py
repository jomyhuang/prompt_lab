import streamlit as st
from typing import TypedDict, Annotated, List, Tuple, Optional, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
import random
import numpy as np
import time

# 定义船只类型和大小
SHIPS = {
    "航空母舰": 5,
    "战列舰": 4, 
    "巡洋舰": 3,
    "驱逐舰": 2
}

# 定义棋盘大小
BOARD_SIZE = 10

# 定义游戏状态
class GameState(TypedDict):
    messages: Annotated[List[dict], "游戏消息历史"]
    current_turn: Literal["player", "computer"]
    game_over: bool
    player_board: List[List[str]]
    computer_board: List[List[str]]
    player_shots: List[List[str]]
    computer_shots: List[List[str]]
    player_ships: dict
    computer_ships: dict
    winner: Optional[str]
    message: str
    checking: str

def create_empty_board() -> List[List[str]]:
    return [[" " for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

def is_valid_placement(board: List[List[str]], ship_size: int, 
                      start_row: int, start_col: int, 
                      is_horizontal: bool) -> bool:
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

def place_ship(board: List[List[str]], ship_size: int,
               start_row: int, start_col: int, 
               is_horizontal: bool) -> List[Tuple[int, int]]:
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
            
            if is_valid_placement(board, ship_size, start_row, 
                                start_col, is_horizontal):
                positions = place_ship(board, ship_size, start_row, 
                                    start_col, is_horizontal)
                ships_positions[ship_name] = positions
                break
    return ships_positions

def init_game() -> GameState:
    player_board = create_empty_board()
    computer_board = create_empty_board()
    
    player_ships = place_ships_randomly(player_board)
    computer_ships = place_ships_randomly(computer_board)
    
    messages = [
        {"role": "system", "content": "游戏开始！"},
        {"role": "system", "content": "请选择一个位置进行攻击。"}
    ]
    
    # 确保所有必需字段都被初始化
    return {
        "messages": messages,
        "current_turn": "player",
        "game_over": False,
        "player_board": player_board,
        "computer_board": computer_board,
        "player_shots": create_empty_board(),
        "computer_shots": create_empty_board(),
        "player_ships": player_ships,
        "computer_ships": computer_ships,
        "winner": None,
        "message": "游戏开始！请选择一个位置进行攻击。",
        "checking": "init_completed"  # 确保checking字段被初始化
    }

def check_ship_sunk(ships: dict, shots: List[List[str]]) -> Optional[str]:
    for ship_name, positions in ships.items():
        if all(shots[row][col] == "X" for row, col in positions):
            return ship_name
    return None

def make_shot(state: GameState, row: int, col: int, 
              is_player: bool) -> GameState:
    if is_player:
        target_board = state["computer_board"]
        shots_board = state["player_shots"]
        ships = state["computer_ships"]
        shooter = "玩家"
    else:
        target_board = state["player_board"]
        shots_board = state["computer_shots"]
        ships = state["player_ships"]
        shooter = "电脑"

    # 检查是否击中
    is_hit = target_board[row][col] == "O"
    shots_board[row][col] = "X" if is_hit else "M"
    
    # 更新消息
    message = f"{shooter}攻击了 ({row}, {col}): "
    message += "击中!" if is_hit else "未击中"
    
    # 检查是否有船被击沉
    sunk_ship = check_ship_sunk(ships, shots_board)
    if sunk_ship:
        message += f" {sunk_ship}被击沉!"
    
    # 确保更新至少一个字段
    state["message"] = message
    state["player_shots"] = shots_board if is_player else state["player_shots"]
    state["computer_shots"] = shots_board if not is_player else state["computer_shots"]
    
    return state

def player_turn(state: GameState) -> GameState:
    print("进入 player_turn 节点")
    # 强制更新checking字段
    state["checking"] = "player_turn"
    
    if state["current_turn"] == "player" and not state["game_over"]:
        # 更新message字段
        state["message"] = "轮到你的回合"
        
        # 准备展示信息
        game_info = {
            "message": state["message"],
            "player_board": state["player_board"],
            "computer_board": state["computer_board"],
            "player_shots": state["player_shots"],
            "computer_shots": state["computer_shots"]
        }
        
        # 等待玩家输入
        print("调用interrupt前，当前状态：", state)
        action = interrupt(game_info)
        print("interrupt返回结果：", action)
        row, col = map(int, action.split(","))
        
        # 验证输入
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            state["message"] = "无效的位置,请重试"
            return state
            
        if state["player_shots"][row][col] != " ":
            state["message"] = "该位置已经攻击过,请重试"
            return state
        
        # 执行攻击
        state = make_shot(state, row, col, True)
        
        # 检查是否获胜
        all_computer_ships_sunk = all(
            check_ship_sunk(state["computer_ships"], state["player_shots"])
            for _ in state["computer_ships"]
        )
        
        if all_computer_ships_sunk:
            state["winner"] = "player"
            state["game_over"] = True
            state["message"] = "游戏结束,你赢了!"
        else:
            state["current_turn"] = "computer"
            state["message"] = "轮到电脑的回合"
    
    # 确保至少更新一个字段
    if not any(key in state for key in ['current_turn', 'game_over', 'player_board', 'computer_board', 'player_shots', 'computer_shots', 'player_ships', 'computer_ships', 'winner', 'message', 'checking']):
        state["checking"] = "player_turn_completed"
    
    print("退出 player_turn 节点")
    return state

def computer_turn(state: GameState) -> GameState:
    print("进入 computer_turn 节点")
    # 强制更新checking字段
    state["checking"] = "computer_turn"
    
    if state["current_turn"] == "computer" and not state["game_over"]:
        # 随机选择攻击位置
        while True:
            row = random.randint(0, BOARD_SIZE - 1)
            col = random.randint(0, BOARD_SIZE - 1)
            if state["computer_shots"][row][col] == " ":
                break
                
        # 执行攻击
        state = make_shot(state, row, col, False)
        
        # 检查是否获胜
        all_player_ships_sunk = all(
            check_ship_sunk(state["player_ships"], state["computer_shots"])
            for _ in state["player_ships"]
        )
        
        if all_player_ships_sunk:
            state["winner"] = "computer"
            state["game_over"] = True
            state["message"] = "游戏结束,电脑赢了!"
        else:
            state["current_turn"] = "player"
            state["message"] = "轮到你的回合"
    
    # 确保至少更新一个字段
    if not any(key in state for key in ['current_turn', 'game_over', 'player_board', 'computer_board', 'player_shots', 'computer_shots', 'player_ships', 'computer_ships', 'winner', 'message', 'checking']):
        state["checking"] = "computer_turn_completed"
    
    print("退出 computer_turn 节点")
    return state

def build_graph(checkpointer=None) -> StateGraph:
    print("开始构建状态图")
    """构建游戏流程图"""
    graph = StateGraph(GameState)
    
    # 添加节点
    graph.add_node("player_turn", player_turn)
    graph.add_node("computer_turn", computer_turn)
    
    # 添加边
    graph.add_edge(START, "player_turn")
    graph.add_edge("player_turn", "computer_turn")
    graph.add_edge("computer_turn", "player_turn")
    
    # 添加结束条件
    def should_end(state: GameState) -> Literal["player_turn", "computer_turn", END]:
        if state["game_over"]:
            return END
        elif state["current_turn"] == "player":
            return "player_turn"
        else:
            return "computer_turn"
    
    graph.add_conditional_edges("player_turn", should_end)
    graph.add_conditional_edges("computer_turn", should_end)
    
    # 编译图
    print("状态图构建完成")
    return graph.compile(checkpointer=checkpointer)

def render_board(board: List[List[str]], shots: List[List[str]], 
                show_ships: bool = True) -> None:
    """渲染棋盘
    
    Args:
        board: 棋盘数据
        shots: 射击记录
        show_ships: 是否显示船只
    """
    # 显示列标题
    st.write("  " + " ".join(str(i) for i in range(BOARD_SIZE)))
    
    # 显示棋盘内容
    for i in range(BOARD_SIZE):
        row = [str(i)]  # 行标题
        for j in range(BOARD_SIZE):
            if shots[i][j] != " ":
                # 显示射击结果
                cell = "💥" if shots[i][j] == "X" else "💧"
            elif show_ships and board[i][j] == "O":
                # 显示船只
                cell = "🚢"
            else:
                # 显示空白
                cell = "⬜"
            row.append(cell)
        st.write(" ".join(row))

def main():
    """主游戏循环"""
    st.title("海战棋")
    
    # 初始化会话状态
    if "state" not in st.session_state:
        print("初始化游戏状态...")
        st.session_state.state = init_game()
        print("初始化后的状态：", st.session_state.state)
        
        # 初始化checkpointer
        st.session_state.checkpointer = MemorySaver()
        
        # 生成thread_id
        st.session_state.thread_id = str(random.randint(1, 1000000))
        print("生成的thread_id：", st.session_state.thread_id)
        
        # 构建图时传入checkpointer
        print("构建状态图...")
        st.session_state.graph = build_graph(checkpointer=st.session_state.checkpointer)
        
        # 第一次调用invoke，传入初始状态
        print("第一次调用invoke...")
        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        st.session_state.state = st.session_state.graph.invoke(
            st.session_state.state,
            config=config
        )
        print("第一次invoke后的状态：", st.session_state.state)
    
    # 显示游戏状态
    st.write(f"当前消息: {st.session_state.state['message']}")
    
    # 显示棋盘
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("你的棋盘")
        render_board(
            st.session_state.state["player_board"],
            st.session_state.state["computer_shots"],
            show_ships=True
        )
    
    with col2:
        st.subheader("对手的棋盘")
        render_board(
            st.session_state.state["computer_board"],
            st.session_state.state["player_shots"],
            show_ships=False
        )
    
    # 玩家输入
    if not st.session_state.state["game_over"]:
        if st.session_state.state["current_turn"] == "player":
            row = st.number_input("输入攻击行号(0-9):", 0, 9)
            col = st.number_input("输入攻击列号(0-9):", 0, 9)
            if st.button("攻击"):
                print("调用 interrupt 前")
                command = Command(resume=f"{row},{col}")
                config = {"configurable": {"thread_id": st.session_state.thread_id}}
                print(f"准备调用 invoke, 参数: {command}, {config}")
                result = st.session_state.graph.invoke(
                    command,
                    config=config
                )
                print(f"invoke 返回结果: {result}")
                st.session_state.state = result
                st.rerun()
    else:
        if st.button("重新开始"):
            st.session_state.state = init_game()
            st.rerun()

if __name__ == "__main__":
    main()
