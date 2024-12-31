import streamlit as st
from typing import TypedDict, Annotated, List, Tuple, Optional, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
import random
import numpy as np
import time

def add_messages(messages: list) -> list:
    """添加消息到历史记录
    
    Args:
        messages: 消息列表
        
    Returns:
        更新后的消息列表
    """
    return messages

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
    """游戏状态类型定义
    
    Attributes:
        messages: 游戏消息历史
        current_turn: 当前回合
        game_over: 游戏是否结束
        player_board: 玩家的棋盘
        computer_board: 电脑的棋盘
        player_shots: 玩家的射击记录
        computer_shots: 电脑的射击记录
        player_ships: 玩家的船只位置
        computer_ships: 电脑的船只位置
        winner: 获胜者
        message: 当前消息
        last_action: 最后执行的动作
        phase: 游戏阶段
        player_info: 玩家信息
        computer_info: 电脑信息
        valid_actions: 当前可用的动作
        action_history: 动作历史记录
        thread_id: 会话ID
    """
    messages: List[dict]  # 游戏消息历史
    current_turn: Literal["player", "computer"]  # 当前回合
    game_over: bool  # 游戏是否结束
    player_board: List[List[str]]  # 玩家的棋盘
    computer_board: List[List[str]]  # 电脑的棋盘
    player_shots: List[List[str]]  # 玩家的射击记录
    computer_shots: List[List[str]]  # 电脑的射击记录
    player_ships: dict  # 玩家的船只位置
    computer_ships: dict  # 电脑的船只位置
    winner: Optional[str]  # 获胜者
    message: str  # 当前消息
    last_action: Optional[str]  # 最后执行的动作
    phase: Literal["setup", "playing", "game_over"]  # 游戏阶段
    player_info: dict  # 玩家信息
    computer_info: dict  # 电脑信息
    valid_actions: List[str]  # 当前可用的动作
    action_history: List[dict]  # 动作历史记录
    thread_id: str  # 会话ID

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
    """初始化游戏状态
    
    Returns:
        初始化的游戏状态
    """
    # 创建新的游戏状态
    player_board = create_empty_board()
    computer_board = create_empty_board()
    
    player_ships = place_ships_randomly(player_board)
    computer_ships = place_ships_randomly(computer_board)
    
    # 初始化玩家和电脑信息
    player_info = {
        "hits": 0,
        "misses": 0,
        "ships_sunk": 0
    }
    
    computer_info = {
        "hits": 0,
        "misses": 0,
        "ships_sunk": 0
    }
    
    # 初始化消息历史
    messages = [
        {"role": "system", "content": "游戏开始！"},
        {"role": "system", "content": "请选择一个位置进行攻击。"}
    ]
    
    return GameState(
        messages=messages,
        current_turn="player",
        game_over=False,
        player_board=player_board,
        computer_board=computer_board,
        player_shots=create_empty_board(),
        computer_shots=create_empty_board(),
        player_ships=player_ships,
        computer_ships=computer_ships,
        winner=None,
        message="游戏开始！请选择一个位置进行攻击。",
        last_action=None,
        phase="playing",
        player_info=player_info,
        computer_info=computer_info,
        valid_actions=["attack"],
        action_history=[],
        thread_id=str(random.randint(1, 1000000))
    )

def check_ship_sunk(ships: dict, row: int, col: int) -> Optional[str]:
    for ship_name, positions in ships.items():
        if (row, col) in positions:
            # 检查这艘船是否所有位置都被击中
            return ship_name
    return None

def make_shot(state: GameState, row: int, col: int, is_player: bool) -> GameState:
    """执行射击操作
    
    Args:
        state: 游戏状态
        row: 目标行
        col: 目标列
        is_player: 是否是玩家射击
        
    Returns:
        更新后的游戏状态
    """
    if is_player:
        target_board = state["computer_board"]
        shots_board = state["player_shots"]
        ships = state["computer_ships"]
        shooter = "玩家"
        info = state["player_info"]
    else:
        target_board = state["player_board"]
        shots_board = state["computer_shots"]
        ships = state["player_ships"]
        shooter = "电脑"
        info = state["computer_info"]

    if target_board[row][col] == "O":  # 击中
        shots_board[row][col] = "X"
        info["hits"] += 1
        ship_name = check_ship_sunk(ships, row, col)
        if ship_name:
            info["ships_sunk"] += 1
            state["message"] = f"{shooter}击中并击沉了{ship_name}！"
        else:
            state["message"] = f"{shooter}击中了一艘船！"
    else:  # 未命中
        shots_board[row][col] = "·"
        info["misses"] += 1
        state["message"] = f"{shooter}的攻击未命中。"

    return state

def check_game_winner(state: GameState) -> Optional[str]:
    """检查是否有获胜者
    
    Args:
        state: 游戏状态
        
    Returns:
        获胜者("player"或"computer")或None
    """
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

def check_winner(state: GameState) -> GameState:
    """检查获胜者的节点
    
    Args:
        state: 游戏状态
        
    Returns:
        更新后的游戏状态
    """
    print("进入节点: check_winner")
    winner = check_game_winner(state)
    if winner:
        state["game_over"] = True
        state["winner"] = winner
        state["phase"] = "game_over"
        win_message = "游戏结束！玩家获胜！" if winner == "player" else "游戏结束！电脑获胜！"
        state["messages"].append({
            "role": "system",
            "content": win_message
        })
        state["message"] = win_message
    else:
        # 切换回合
        state["current_turn"] = "computer" if state["current_turn"] == "player" else "player"
    
    return state

# 玩家回合
def player_turn(state: GameState) -> GameState:
    """玩家回合处理
    
    使用interrupt机制等待玩家操作
    """
    if state["current_turn"] != "player" or state["game_over"]:
        return state
    
    # 准备展示给玩家的游戏状态信息
    game_info = {
        "message": state["message"],
        "player_board": state["player_board"],
        "computer_board": state["computer_board"],
        "player_shots": state["player_shots"],
        "computer_shots": state["computer_shots"],
        "valid_actions": ["attack"],
        "phase": state["phase"]
    }
    
    # 使用interrupt等待玩家操作
    try:
        # 暂停执行，等待玩家输入
        action = interrupt(
            message=state["message"],
            data=game_info,
            expect_type=dict
        )
        
        # 处理玩家操作
        if isinstance(action, dict) and action.get("action") == "attack":
            row = action.get("row")
            col = action.get("col")
            if row is not None and col is not None:
                # 检查是否有效的攻击位置
                if state["player_shots"][row][col] == " ":
                    state = make_shot(state, row, col, True)
                    state["last_action"] = f"attack_{row}_{col}"
                    
                    # 检查是否获胜
                    winner = check_winner(state)
                    if winner:
                        state["game_over"] = True
                        state["winner"] = winner
                        state["phase"] = "game_over"
                        state["message"] += " 游戏结束！玩家获胜！"
                    else:
                        # 切换到电脑回合
                        state["current_turn"] = "computer"
                        
                        # 执行电脑回合
                        time.sleep(1)  # 添加延迟使游戏更自然
                        
                        # 电脑执行攻击
                        valid_positions = [
                            (i, j) 
                            for i in range(BOARD_SIZE) 
                            for j in range(BOARD_SIZE) 
                            if state["computer_shots"][i][j] == " "
                        ]
                        
                        if valid_positions:
                            comp_row, comp_col = random.choice(valid_positions)
                            state = make_shot(state, comp_row, comp_col, False)
                            state["last_action"] = f"attack_{comp_row}_{comp_col}"
                            
                            # 检查电脑是否获胜
                            winner = check_winner(state)
                            if winner:
                                state["game_over"] = True
                                state["winner"] = winner
                                state["phase"] = "game_over"
                                state["message"] += " 游戏结束！电脑获胜！"
                            else:
                                state["current_turn"] = "player"
                        else:
                            state["message"] = "没有可用的攻击位置！"
                            state["game_over"] = True
                            state["phase"] = "game_over"
                    
                    # 同步状态
                    st.session_state.game_state = state
                    st.session_state.need_rerun = True
                else:
                    st.warning("无效的攻击位置，请重新选择！")
        else:
            state["message"] = "请选择一个位置进行攻击！"
            state["phase"] = "playing"
            state["checking"] = "route"  # 标记需要路由
    except Exception as e:
        state["message"] = f"操作处理错误: {str(e)}"
        state["phase"] = "playing"
        state["checking"] = "route"  # 标记需要路由
    
    return state

# 电脑回合
def computer_turn(state: GameState) -> GameState:
    """电脑回合处理
    
    实现简单的AI策略
    """
    if state["current_turn"] != "computer" or state["game_over"]:
        return state
    
    try:
        # 简单的AI：随机选择一个未射击过的位置
        valid_positions = [
            (i, j) 
            for i in range(BOARD_SIZE) 
            for j in range(BOARD_SIZE) 
            if state["computer_shots"][i][j] == " "
        ]
        
        if valid_positions:
            row, col = random.choice(valid_positions)
            state = make_shot(state, row, col, False)
            state["last_action"] = f"attack_{row}_{col}"
            
            # 检查是否获胜
            winner = check_winner(state)
            if winner:
                state["game_over"] = True
                state["winner"] = winner
                state["phase"] = "game_over"
                state["message"] += " 游戏结束！电脑获胜！"
            else:
                state["current_turn"] = "player"
                state["phase"] = "playing"
                state["checking"] = "route"  # 标记需要路由
        else:
            state["message"] = "没有可用的攻击位置！"
            state["game_over"] = True
            state["phase"] = "game_over"
            state["checking"] = "route"  # 标记需要路由
    except Exception as e:
        state["messages"].append({
            "role": "error",
            "content": f"电脑回合错误: {str(e)}"
        })
        state["current_turn"] = "player"
    
    # 添加延迟，使游戏更自然
    time.sleep(1)
    
    return state

# 构建游戏流程图
def build_graph(checkpointer=None) -> StateGraph:
    """构建游戏流程图
    
    使用LangGraph构建海战棋游戏的状态转换图:
    
    1. 创建基于GameState的StateGraph
    2. 添加各个游戏节点
    3. 设置节点间的边和条件
    
    游戏流程:
    START -> route -> player_action -> process_attack -> check_winner -> computer_action -> END
    
    状态转换规则:
    - route节点:
      * 检查游戏状态
      * 决定下一步行动
    - player_action节点:
      * 等待玩家输入
      * 验证动作有效性
    - process_attack节点:
      * 处理攻击结果
      * 更新游戏状态
    - check_winner节点:
      * 检查是否有获胜者
      * 决定游戏是否结束
    - computer_action节点:
      * 执行电脑的回合
      * 处理攻击结果
    
    Args:
        checkpointer: 可选的状态检查点保存器
        
    Returns:
        编译后的游戏流程图
    """
    # 创建StateGraph
    workflow = StateGraph(GameState)
    
    # 添加节点
    workflow.add_node("route", route_state)  # 路由节点
    workflow.add_node("player_action", player_action)  # 玩家动作节点
    workflow.add_node("process_attack", process_attack)  # 处理攻击节点
    workflow.add_node("check_winner", check_winner)  # 检查获胜节点
    workflow.add_node("computer_action", computer_action)  # 电脑动作节点
    workflow.add_node("handle_end", handle_game_over)  # 游戏结束节点
    
    # 设置边和条件
    # 从START开始到route
    workflow.add_edge(START, "route")
    
    # 从route到各个节点
    workflow.add_conditional_edges(
        "route",
        router
    )
    
    # 从player_action到process_attack
    workflow.add_edge("player_action", "process_attack")
    
    # 从process_attack到check_winner
    workflow.add_edge("process_attack", "check_winner")
    
    # 从check_winner根据结果转向
    workflow.add_conditional_edges(
        "check_winner",
        lambda x: "handle_end" if x["game_over"] else "computer_action"
    )
    
    # 从computer_action回到route
    workflow.add_edge("computer_action", "route")
    
    # 结束节点
    workflow.add_edge("handle_end", END)
    
    # 编译图
    app = workflow.compile()
    
    # 配置递归限制和状态管理器
    app.recursion_limit = 100  # 增加递归限制
    if checkpointer:
        app.state_manager = checkpointer
    
    return app

def route_state(state: GameState) -> GameState:
    """路由状态，决定下一步操作
    
    Args:
        state: 游戏状态
        
    Returns:
        更新后的游戏状态
    """
    print("进入节点: route_state")
    # 更新可用动作
    if state["current_turn"] == "player":
        state["valid_actions"] = ["attack"]
    
    # 添加消息
    if not state["game_over"]:
        if state["current_turn"] == "player":
            state["messages"].append({
                "role": "system",
                "content": "请选择一个位置进行攻击。"
            })
        else:
            state["messages"].append({
                "role": "system",
                "content": "电脑回合..."
            })
    
    return state

def router(state: GameState) -> str:
    """路由函数，决定下一个节点
    
    Args:
        state: 游戏状态
        
    Returns:
        下一个节点的名称
    """
    print("进入节点: router")
    if state["game_over"]:
        return "handle_end"
    elif state["current_turn"] == "player":
        return "player_action"
    else:
        return "computer_action"

def player_action(state: GameState) -> GameState:
    """处理玩家动作的节点
    
    使用interrupt机制等待玩家输入
    
    Args:
        state: 游戏状态
        
    Returns:
        更新后的游戏状态
    """
    print("进入节点: player_action")
    if state["current_turn"] != "player" or state["game_over"]:
        return state
    
    # 准备展示给玩家的游戏状态信息
    game_info = {
        "message": state["message"],
        "player_board": state["player_board"],
        "computer_board": state["computer_board"],
        "player_shots": state["player_shots"],
        "computer_shots": state["computer_shots"],
        "valid_actions": state["valid_actions"],
        "phase": state["phase"]
    }
    
    # 使用interrupt等待玩家操作
    action = interrupt("请选择一个位置进行攻击。", data=game_info)
    
    # 如果收到了玩家的动作
    if isinstance(action, Command):
        # 记录动作
        state["action_history"].append({
            "turn": "player",
            "action": action.data
        })
        
        # 更新最后动作
        state["last_action"] = action.data
        
        # 添加消息
        state["messages"].append({
            "role": "player",
            "content": f"玩家选择攻击位置: ({action.data.get('row', '?')}, {action.data.get('col', '?')})"
        })
    
    return state

def process_attack(state: GameState) -> GameState:
    """处理攻击动作的节点
    
    Args:
        state: 游戏状态
        
    Returns:
        更新后的游戏状态
    """
    print("进入节点: process_attack")
    if not state["last_action"]:
        return state
        
    try:
        action = state["last_action"]
        if isinstance(action, dict) and action.get("action") == "attack":
            row = action.get("row")
            col = action.get("col")
            if row is not None and col is not None:
                # 检查是否有效的攻击位置
                if state["player_shots"][row][col] == " ":
                    state = make_shot(state, row, col, True)
                    state["messages"].append({
                        "role": "system",
                        "content": state["message"]
                    })
    except Exception as e:
        state["messages"].append({
            "role": "error",
            "content": f"攻击处理错误: {str(e)}"
        })
    
    return state

def computer_action(state: GameState) -> GameState:
    """处理电脑动作的节点
    
    Args:
        state: 游戏状态
        
    Returns:
        更新后的游戏状态
    """
    print("进入节点: computer_action")
    if state["current_turn"] != "computer" or state["game_over"]:
        return state
    
    try:
        # 电脑AI逻辑
        valid_positions = [
            (i, j) 
            for i in range(BOARD_SIZE) 
            for j in range(BOARD_SIZE) 
            if state["computer_shots"][i][j] == " "
        ]
        
        if valid_positions:
            row, col = random.choice(valid_positions)
            state = make_shot(state, row, col, False)
            
            # 记录动作
            state["action_history"].append({
                "turn": "computer",
                "action": {
                    "action": "attack",
                    "row": row,
                    "col": col
                }
            })
            
            state["messages"].append({
                "role": "system",
                "content": state["message"]
            })
            
            # 检查是否获胜
            winner = check_game_winner(state)
            if winner:
                state["game_over"] = True
                state["winner"] = winner
                state["phase"] = "game_over"
                win_message = "游戏结束！电脑获胜！"
                state["messages"].append({
                    "role": "system",
                    "content": win_message
                })
                state["message"] = win_message
            else:
                state["current_turn"] = "player"
        else:
            state["messages"].append({
                "role": "system",
                "content": "没有可用的攻击位置！"
            })
            state["game_over"] = True
            state["phase"] = "game_over"
            
    except Exception as e:
        state["messages"].append({
            "role": "error",
            "content": f"电脑回合错误: {str(e)}"
        })
        state["current_turn"] = "player"
    
    # 添加延迟使游戏更自然
    time.sleep(1)
    
    return state

def handle_player_action(action: dict):
    """处理玩家操作并同步状态
    
    Args:
        action: 玩家操作信息
    """
    try:
        # 获取当前状态
        state = st.session_state.game_state
        
        # 验证动作
        if action.get("action") == "attack":
            row = action.get("row")
            col = action.get("col")
            if row is not None and col is not None:
                # 检查是否有效的攻击位置
                if state["player_shots"][row][col] == " ":
                    # 执行玩家攻击
                    state = make_shot(state, row, col, True)
                    state["last_action"] = action
                    
                    # 检查是否获胜
                    winner = check_game_winner(state)
                    if winner:
                        state["game_over"] = True
                        state["winner"] = winner
                        state["phase"] = "game_over"
                        state["message"] = "游戏结束！玩家获胜！"
                    else:
                        # 切换到电脑回合
                        state["current_turn"] = "computer"
                        
                        # 执行电脑回合
                        time.sleep(1)  # 添加延迟使游戏更自然
                        
                        # 电脑执行攻击
                        valid_positions = [
                            (i, j) 
                            for i in range(BOARD_SIZE) 
                            for j in range(BOARD_SIZE) 
                            if state["computer_shots"][i][j] == " "
                        ]
                        
                        if valid_positions:
                            comp_row, comp_col = random.choice(valid_positions)
                            state = make_shot(state, comp_row, comp_col, False)
                            state["last_action"] = {
                                "action": "attack",
                                "row": comp_row,
                                "col": comp_col
                            }
                            
                            # 检查电脑是否获胜
                            winner = check_game_winner(state)
                            if winner:
                                state["game_over"] = True
                                state["winner"] = winner
                                state["phase"] = "game_over"
                                state["message"] = "游戏结束！电脑获胜！"
                            else:
                                state["current_turn"] = "player"
                        else:
                            state["message"] = "没有可用的攻击位置！"
                            state["game_over"] = True
                            state["phase"] = "game_over"
                    
                    # 同步状态
                    st.session_state.game_state = state
                    st.session_state.need_rerun = True
                else:
                    st.warning("无效的攻击位置，请重新选择！")
        else:
            state["message"] = "请选择一个位置进行攻击！"
            state["phase"] = "playing"
            state["checking"] = "route"  # 标记需要路由
    except Exception as e:
        st.error(f"操作处理错误: {str(e)}")

def handle_game_over(state: GameState) -> GameState:
    """处理游戏结束
    
    显示游戏结果并更新状态
    """
    print("进入节点: handle_game_over")
    if state["winner"] == "player":
        state["message"] = "游戏结束！玩家获胜！"
    else:
        state["message"] = "游戏结束！电脑获胜！"
    return state

def make_move(row: int, col: int):
    """处理玩家移动
    
    Args:
        row: 目标行
        col: 目标列
    """
    if st.session_state.game_state["current_turn"] != "player" or \
       st.session_state.game_state["game_over"] or \
       st.session_state.game_state["player_shots"][row][col] != " ":
        return

    # 创建攻击动作
    action = {
        "action": "attack",
        "row": row,
        "col": col
    }
    
    # 创建 Command 对象并返回
    return Command(
        name="player_action",
        data=action,
        kwargs={}
    )

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
                    command = make_move(i, j)
                    if isinstance(command, Command):
                        st.session_state.game_state["last_action"] = command.data
                        st.session_state.need_rerun = True
            else:
                cols[j + 1].markdown(cell)

def show_welcome_screen():
    """显示欢迎界面"""
    st.title("🚢 欢迎来到海战棋游戏！")
    
    # 使用列来居中显示内容
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        ### 关于游戏
        海战棋是一个经典的策略游戏，你将与电脑对战，互相寻找并击沉对方的舰队。
        
        ### 你的舰队
        - 航空母舰 (5格)
        - 战列舰 (4格)
        - 巡洋舰 (3格)
        - 驱逐舰 (2格)
        
        ### 游戏规则
        1. 你的舰船会自动放置在棋盘上
        2. 与电脑轮流攻击对方的舰队
        3. 点击攻击区域的空白格子进行攻击
        4. 首先击沉所有敌方舰船的一方获胜！
        
        ### 准备好了吗？
        """)
        
        # 开始游戏按钮
        if st.button("开始游戏", use_container_width=True):
            st.session_state.game_started = True
            st.session_state.game_state = init_game()
            st.session_state.graph = build_graph()
            st.session_state.need_rerun = True

def reset_game():
    """重置游戏状态"""
    if "game_state" in st.session_state:
        del st.session_state.game_state
    if "graph" in st.session_state:
        del st.session_state.graph
    st.session_state.thread_id = str(random.randint(1, 1000000))
    st.session_state.need_rerun = True  # 设置需要重新渲染的标志

def main():
    """主游戏循环
    
    使用 LangGraph 驱动游戏流程
    """
    # 设置页面宽度为宽屏模式
    st.set_page_config(layout="wide", page_title="海战棋游戏")
    
    # 初始化游戏状态
    if "game_started" not in st.session_state:
        st.session_state.game_started = False
        st.session_state.thread_id = str(random.randint(1, 1000000))
        st.session_state.need_rerun = False
    
    # 创建 checkpointer
    if "checkpointer" not in st.session_state:
        st.session_state.checkpointer = MemorySaver()
    
    try:
        # 显示欢迎界面或游戏界面
        if not st.session_state.game_started:
            show_welcome_screen()
        else:
            # 游戏主界面
            render_game_interface()
            
            # 获取游戏图和状态
            if "game_state" not in st.session_state:
                st.session_state.game_state = init_game()
                st.session_state.graph = build_graph()
            
            # 使用 LangGraph 驱动游戏流程
            try:
                # 调用图的 invoke 方法执行游戏流程
                result = st.session_state.graph.invoke({
                    "messages": st.session_state.game_state["messages"],
                    "current_turn": st.session_state.game_state["current_turn"],
                    "game_over": st.session_state.game_state["game_over"],
                    "player_board": st.session_state.game_state["player_board"],
                    "computer_board": st.session_state.game_state["computer_board"],
                    "player_shots": st.session_state.game_state["player_shots"],
                    "computer_shots": st.session_state.game_state["computer_shots"],
                    "player_ships": st.session_state.game_state["player_ships"],
                    "computer_ships": st.session_state.game_state["computer_ships"],
                    "winner": st.session_state.game_state["winner"],
                    "message": st.session_state.game_state["message"],
                    "last_action": st.session_state.game_state["last_action"],
                    "phase": st.session_state.game_state["phase"],
                    "player_info": st.session_state.game_state["player_info"],
                    "computer_info": st.session_state.game_state["computer_info"],
                    "valid_actions": st.session_state.game_state["valid_actions"],
                    "action_history": st.session_state.game_state["action_history"],
                    "thread_id": st.session_state.game_state["thread_id"]
                })
                
                # 更新游戏状态
                if isinstance(result, dict):
                    st.session_state.game_state.update(result)
                    
                # 检查是否需要重新渲染
                if st.session_state.need_rerun:
                    st.session_state.need_rerun = False
                    st.rerun()
                    
            except Exception as e:
                st.error(f"游戏流程错误: {str(e)}")
        
    except Exception as e:
        st.error(f"游戏运行错误: {str(e)}")

def render_game_interface():
    """渲染游戏主界面"""
    st.title("海战棋游戏")
    
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
            turn_text = "玩家回合" if st.session_state.game_state["current_turn"] == "player" else "电脑回合"
            st.subheader(f"当前回合: {turn_text}")
    
    # 创建三列来平行显示棋盘和说明
    col1, col2, col3 = st.columns([1.2, 1.2, 0.8])
    
    # 在左列显示玩家的棋盘
    with col1:
        st.subheader("你的舰队")
        render_board(st.session_state.game_state["player_board"],
                    st.session_state.game_state["computer_shots"],
                    show_ships=True,
                    board_type="player")
        
        # 显示游戏流程图
        st.markdown("### 游戏流程")
        render_game_flow(st.session_state.game_state["current_turn"])
        
        # 显示当前状态信息
        with st.expander("游戏状态详情", expanded=False):
            render_game_state(st.session_state.game_state)
    
    # 在中间列显示电脑的棋盘
    with col2:
        st.subheader("攻击区域")
        st.caption("点击空白格子进行攻击")
        render_board(st.session_state.game_state["computer_board"],
                    st.session_state.game_state["player_shots"],
                    show_ships=False,
                    board_type="computer")
    
    # 在右列显示说明
    with col3:
        render_game_guide()
        
        # 重置游戏按钮
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            if st.button("新游戏", key="restart", use_container_width=True):
                reset_game()

def render_game_flow(current_turn: str):
    """渲染游戏流程图
    
    Args:
        current_turn: 当前回合
    """
    dot_graph = """
    digraph G {
        rankdir=LR;
        node [shape=box, style=rounded, fontname="Arial"];
        
        start [label="开始", color=gray];
        player [label="玩家回合", color=blue];
        computer [label="电脑回合", color=red];
        end [label="结束", color=gray];
        
        start -> player [color=gray];
        player -> computer [color=blue];
        computer -> end [color=red];
    """
    
    # 根据当前状态添加高亮
    if current_turn == "player":
        dot_graph += '    player [style="rounded,filled", fillcolor=lightblue];'
    else:
        dot_graph += '    computer [style="rounded,filled", fillcolor=lightpink];'
    
    dot_graph += "\n}"
    
    # 显示图形
    st.graphviz_chart(dot_graph)

def render_game_state(state: GameState):
    """渲染游戏状态信息
    
    Args:
        state: 游戏状态
    """
    st.markdown(f"""
    - 当前回合: **{state['current_turn']}**
    - 玩家命中: **{state['player_info']['hits']}**
    - 玩家未命中: **{state['player_info']['misses']}**
    - 玩家击沉: **{state['player_info']['ships_sunk']}**
    - 电脑命中: **{state['computer_info']['hits']}**
    - 电脑未命中: **{state['computer_info']['misses']}**
    - 电脑击沉: **{state['computer_info']['ships_sunk']}**
    - 游戏状态: **{'进行中' if not state['game_over'] else '已结束'}**
    - 游戏阶段: **{state['phase']}**
    """)

def render_game_guide():
    """渲染游戏指南"""
    st.subheader("游戏指南")
    
    # 使用卡片式布局来组织说明内容
    with st.expander("图例说明", expanded=True):
        st.markdown("""
        🚢 : 你的舰船  
        💥 : 命中  
        🌊 : 未命中  
        🔥 : 被命中  
        💨 : 被未命中  
        ⬜ : 未探索区域
        """)
    
    with st.expander("舰船说明", expanded=True):
        st.markdown("""
        - 航空母舰 (5格)
        - 战列舰 (4格)
        - 巡洋舰 (3格)
        - 驱逐舰 (2格)
        """)
    
    with st.expander("规则说明", expanded=True):
        st.markdown("""
        1. 轮流攻击敌方舰队
        2. 击沉所有敌方舰船获胜
        3. 舰船可以水平或垂直放置
        """)

if __name__ == "__main__":
    main()
