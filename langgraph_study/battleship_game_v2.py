import streamlit as st
from typing import TypedDict, Annotated, List, Tuple, Optional, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
import random
import numpy as np
import time
import tempfile
from PIL import Image
import graphviz

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
        # {"role": "system", "content": "请选择一个位置进行攻击。"}
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

# 构建游戏流程图
def build_graph(checkpointer=None) -> StateGraph:
    """构建游戏流程图"""
    # 创建StateGraph
    workflow = StateGraph(GameState)
    
    # 添加节点
    workflow.add_node("init_state", init_state)
    workflow.add_node("route", route_state)
    workflow.add_node("player_action", player_action)  # 合并后的玩家动作节点
    workflow.add_node("computer_action", computer_action)
    workflow.add_node("handle_end", handle_game_over)
    
    # 设置边和条件
    workflow.add_edge(START, "init_state")
    workflow.add_edge("init_state", "route")
    
    workflow.add_conditional_edges(
        "route",
        lambda x: (
            "handle_end" if x["game_over"] else
            "player_action" if x["current_turn"] == "player" else
            "computer_action"
        )
    )
    
    # 从player_action直接到computer_action
    workflow.add_edge("player_action", "route")
    
    # 从computer_action回到route
    workflow.add_edge("computer_action", "route")
    
    workflow.add_edge("handle_end", END)
    
    if not checkpointer:
        print("no checkpointer error!")
        st.stop()

    return workflow.compile(checkpointer=checkpointer)

def init_state(state: GameState) -> GameState:
    """初始化状态
    
    Args:
        state: 游戏状态
        
    Returns:
        更新后的游戏状态
    """
    print("进入节点: init_state")
    return state

def route_state(state: GameState) -> GameState:
    """路由状态，决定下一步操作
    
    Args:
        state: 游戏状态
        
    Returns:
        更新后的游戏状态
    """
    print("进入节点: route_state")
    print(f"[route_state] Before interrupt ----")
    # 特别插入中断进入streamlit 刷新
    action = interrupt("interrput from route_state")
    print(f"[route_state] After interrupt ----")

    # 更新可用动作
    if state["current_turn"] == "player":
        state["valid_actions"] = ["attack"]
        state["message"] = "请选择一个位置进行攻击。"
    else:
        state["valid_actions"] = []
        state["message"] = "电脑回合..."
    
    # # 添加消息
    # state["messages"].append({
    #     "role": "system",
    #     "content": state["message"]
    # })
    
    return state

def player_action(state: GameState) -> GameState:
    """合并后的玩家动作节点，包含攻击处理和胜负检查"""
    print("进入合并后的player_action节点")
    if state["current_turn"] != "player" or state["game_over"]:
        return state
    
    # 使用interrupt等待玩家操作
    print("[player_action] before player_action interrupt")
    action = interrupt("waiting for player action...")
    print("[player_action] after player_action interrupt", action)
    
    # 处理玩家操作
    if isinstance(action, dict):
        print(f"收到玩家操作: {action}")
        if action.get("action") == "attack":
            row = action.get("row")
            col = action.get("col")
            if row is not None and col is not None:
                # 检查是否有效的攻击位置
                if state["player_shots"][row][col] == " ":
                    # 处理攻击
                    state = make_shot(state, row, col, True)
                    state["last_action"] = action
                    state["messages"].append({
                        "role": "player",
                        "content": f"玩家攻击位置: ({row}, {col})"
                    })
                    
                    # 检查是否获胜
                    winner = check_game_winner(state)
                    if winner:
                        state["game_over"] = True
                        state["winner"] = winner
                        state["phase"] = "game_over"
                        state["message"] = "游戏结束！玩家获胜！"
                        state["messages"].append({
                            "role": "system",
                            "content": state["message"]
                        })
                    else:
                        state["current_turn"] = "computer"
                        state["message"] = "轮到电脑回合"
                        state["messages"].append({
                            "role": "system",
                            "content": state["message"]
                        })
                else:
                    state["message"] = "无效的攻击位置，请重新选择！"
                    state["messages"].append({
                        "role": "system",
                        "content": state["message"]
                    })
            else:
                print(f"无效的行列值: row={row}, col={col}")
                # st.stop()
        else:
            print(f"无效的action类型: {action.get('action')}")
            state["message"] = "无效的操作指令"
            state["messages"].append({
                "role": "system",
                "content": state["message"]
            })
            # st.stop()
    else:
        print(f"收到非字典类型的action: {type(action)}")
        # state["message"] = "请选择一个位置进行攻击"
        # state["messages"].append({
        #     "role": "system",
        #     "content": state["message"]
        # })
        # # st.stop()

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
        print("电脑回合被跳过：当前不是电脑回合或游戏已结束")
        return state
    
    # 电脑AI逻辑
    valid_positions = [
        (i, j) 
        for i in range(BOARD_SIZE) 
        for j in range(BOARD_SIZE) 
        if state["computer_shots"][i][j] == " "
    ]
    
    print(f"电脑可选的攻击位置数量: {len(valid_positions)}")
    
    if valid_positions:
        row, col = random.choice(valid_positions)
        print(f"电脑选择的攻击位置: ({row}, {col})")
        state = make_shot(state, row, col, False)
        
        # 记录动作
        state["last_action"] = {
            "action": "attack",
            "row": row,
            "col": col
        }
        
        state["messages"].append({
            "role": "computer",
            "content": f"电脑攻击位置: ({row}, {col})"
        })
        
        # 检查是否获胜
        winner = check_game_winner(state)
        if winner:
            print(f"电脑获胜！获胜者: {winner}")
            state["game_over"] = True
            state["winner"] = winner
            state["phase"] = "game_over"
            state["message"] = "游戏结束！电脑获胜！"
            state["messages"].append({
                "role": "system",
                "content": state["message"]
            })
        else:
            print("电脑回合结束，轮到玩家回合")
            state["current_turn"] = "player"
            state["message"] = "轮到玩家回合"
            state["messages"].append({
                "role": "system",
                "content": state["message"]
            })
    else:
        print("没有可用的攻击位置，游戏结束")
        state["message"] = "没有可用的攻击位置！"
        state["game_over"] = True
        state["phase"] = "game_over"
        state["messages"].append({
            "role": "system",
            "content": state["message"]
        })
    
    # 添加延迟使游戏更自然
    time.sleep(1)
    
    return state

def handle_player_action(command: Command):
    """处理玩家操作并同步状态"""
    # 验证命令有效性
    if not isinstance(command, Command):
        raise ValueError("Invalid command type")
        
    # 获取当前状态
    state = st.session_state.game_state
    
    # 创建配置
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    
    # 使用graph.invoke恢复执行
    print(f"[handle_player_action] Before invoke ----", command)
    result = st.session_state.graph.invoke(command, config=config)
    print(f"[handle_player_action] After invoke ----")
    
    # 验证并同步状态
    if isinstance(result, dict):
        st.session_state.game_state = result
        st.session_state.need_rerun = True
    else:
        raise ValueError("Invalid state returned from graph")

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
        return None

    # 创建攻击动作
    action = {
        "action": "attack",
        "row": row,
        "col": col
    }
    
    # 返回 Command 对象
    return Command(resume=action)

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
                        handle_player_action(command)
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
        
        # 显示游戏流程图
        st.markdown("### 游戏流程")
        if "graph" in st.session_state:
            render_game_flow("start")
        else:
            st.info("点击开始游戏后显示流程图")
        
        # 开始游戏按钮
        if st.button("开始游戏", use_container_width=True):
            st.session_state.game_started = True
            init_game_state = init_game()
            st.session_state.checkpointer = MemorySaver()
            st.session_state.thread_id = str(random.randint(1, 1000000))
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            st.session_state.config = config
            st.session_state.graph = build_graph(checkpointer=st.session_state.checkpointer)
            st.session_state.action_history = []
            print(f"[main] initial invoke ----")
            st.session_state.game_state = st.session_state.graph.invoke(init_game_state, config=config)
            print(f"[main] after initial invoke ----")
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
    
    # 初始化所有需要的 session_state 变量
    if "game_started" not in st.session_state:
        st.session_state.game_started = False
    if "need_rerun" not in st.session_state:
        st.session_state.need_rerun = False    

    # 显示欢迎界面或游戏界面
    if not st.session_state.game_started:
        show_welcome_screen()
    else:
        # 游戏主界面
        render_game_interface()
        
        # 创建配置
        config = {"configurable": {"thread_id": st.session_state.thread_id}}

        # 调用图的 invoke 方法执行游戏流程
        # resume="XXX" 传入是interruptd的return值, 通常为Command(),会继续往下一个state
        # TODO: 如果需要resume才resume
        print(f"[main] Before invoke ----")
        st.session_state.game_state = st.session_state.graph.invoke(
            Command(resume=None), 
            config=config)
        print(f"[main] After invoke ----")
            
    # 检查是否需要重新渲染
    if st.session_state.need_rerun:
        st.session_state.need_rerun = False
        print(f"[main] need_rerun ----", time.time())
        st.rerun()

def render_game_interface():
    """渲染游戏主界面"""
    st.title("海战棋游戏")
    
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
        with st.expander("游戏状态详情", expanded=True):
            render_game_state(st.session_state.game_state)
    
    # 在中间列显示电脑的棋盘
    with col2:
        st.subheader("攻击区域")
        st.caption("点击空白格子进行攻击")
        render_board(st.session_state.game_state["computer_board"],
                    st.session_state.game_state["player_shots"],
                    show_ships=False,
                    board_type="computer")
    
    # 在右列显示说明和消息
    with col3:
        render_game_guide()  # 显示游戏指南
        render_game_messages()  # 显示游戏消息
        
        # 重置游戏按钮
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            if st.button("新游戏", key="restart", use_container_width=True):
                reset_game()

def render_game_flow(current_turn: str):
    """使用LangGraph API和Graphviz渲染游戏状态图
    
    Args:
        current_turn: 当前回合
    """
    # 获取LangGraph的状态图
    graph = st.session_state.graph.get_graph()
    
    # 将状态图转换为Graphviz格式
    try:
        # 使用graphviz.Digraph创建图形
        dot = graphviz.Digraph()
        dot.attr(rankdir='LR', fontname='Arial')
        
        # 添加节点
        for node in graph.nodes:
            if node == current_turn:
                dot.node(node, style='filled', fillcolor='lightblue' if node == 'player_turn' else 'lightpink')
            else:
                dot.node(node)
        
        # 添加边
        for edge in graph.edges:
            dot.edge(edge.source, edge.target)
        
        # 显示图形
        st.graphviz_chart(dot)
        
    except Exception as e:
        st.error(f"无法生成状态图: {str(e)}")

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
    # 使用一个折叠面板包含所有说明信息
    with st.expander("游戏指南", expanded=False):
        # 图例说明
        st.markdown("### 图例说明")
        st.markdown("""
        🚢 : 你的舰船  
        💥 : 命中  
        🌊 : 未命中  
        🔥 : 被命中  
        💨 : 被未命中  
        ⬜ : 未探索区域
        """)
        
        # 舰船说明
        st.markdown("### 舰船说明")
        st.markdown("""
        - 航空母舰 (5格)
        - 战列舰 (4格)
        - 巡洋舰 (3格)
        - 驱逐舰 (2格)
        """)
        
        # 规则说明
        st.markdown("### 规则说明")
        st.markdown("""
        1. 轮流攻击敌方舰队
        2. 击沉所有敌方舰船获胜
        3. 舰船可以水平或垂直放置
        """)

def render_game_messages():
    """使用st.chatbox渲染游戏消息"""
    st.subheader("游戏消息")
    if "game_state" in st.session_state and "messages" in st.session_state.game_state:
        messages = st.session_state.game_state["messages"]
        if messages:
            # 使用固定高度的容器来显示消息
            with st.container(height=500):  # 设置固定高度为400px
                # 使用st.chatbox显示消息
                with st.chat_message("system"):
                    st.markdown("<small>游戏消息记录：</small>", unsafe_allow_html=True)
                
                for msg in messages:
                    # 根据消息角色设置不同的样式
                    if msg["role"] == "player":
                        with st.chat_message("user"):
                            st.markdown(f"<small>玩家: {msg['content']}</small>", unsafe_allow_html=True)
                    elif msg["role"] == "computer":
                        with st.chat_message("assistant"):
                            st.markdown(f"<small>电脑: {msg['content']}</small>", unsafe_allow_html=True)
                    else:  # system
                        with st.chat_message("system"):
                            st.markdown(f"<small>系统: {msg['content']}</small>", unsafe_allow_html=True)
        else:
            with st.container(height=500):  # 设置较小的固定高度
                with st.chat_message("system"):
                    st.markdown("<small>暂无游戏消息</small>", unsafe_allow_html=True)
    else:
        with st.container(height=500):  # 设置较小的固定高度
            with st.chat_message("system"):
                st.markdown("<small>游戏尚未开始</small>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
