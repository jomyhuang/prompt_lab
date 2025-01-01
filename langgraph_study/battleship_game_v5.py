import streamlit as st
import random
from typing import TypedDict, Literal, Optional, List, Dict
from langgraph.graph import StateGraph, END, START
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
import time

# 定义游戏常量
BOARD_SIZE = 8
SHIP_SIZES = {
    "航空母舰": 5,
    "战列舰": 4,
    "巡洋舰": 3,
    "驱逐舰": 2
}

# 定义游戏状态类型
class GameState(TypedDict):
    """游戏状态类型定义
    
    属性:
        current_turn: 当前回合的玩家(player或computer)
        player_board: 玩家的棋盘
        computer_board: 电脑的棋盘
        player_shots: 玩家的射击记录
        computer_shots: 电脑的射击记录
        message: 游戏消息
        game_over: 游戏是否结束
        winner: 获胜者
        player_ships: 玩家的船只位置
        computer_ships: 电脑的船只位置
        player_wins: 玩家胜场
        computer_wins: 电脑胜场
        setup_phase: 是否在布置阶段
        current_ship: 当前正在布置的船
        checking: 状态检查标记
    """
    current_turn: Literal["player", "computer"]
    player_board: List[List[str]]
    computer_board: List[List[str]]
    player_shots: List[tuple]
    computer_shots: List[tuple]
    message: str
    game_over: bool
    winner: Optional[str]
    player_ships: Dict[str, List[tuple]]
    computer_ships: Dict[str, List[tuple]]
    player_wins: int
    computer_wins: int
    setup_phase: bool
    current_ship: Optional[str]
    checking: str

def create_empty_board() -> List[List[str]]:
    """创建空棋盘"""
    return [["~" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

def validate_state(state: GameState) -> bool:
    """验证游戏状态的完整性"""
    required_fields = [
        "current_turn", "player_board", "computer_board",
        "player_shots", "computer_shots", "message",
        "game_over", "winner", "player_ships", "computer_ships",
        "player_wins", "computer_wins", "setup_phase",
        "current_ship", "checking"
    ]
    
    # 检查必要字段
    for field in required_fields:
        if field not in state:
            print(f"状态缺少必要字段: {field}")
            return False
    
    # 验证棋盘大小
    if (len(state["player_board"]) != BOARD_SIZE or 
        len(state["computer_board"]) != BOARD_SIZE):
        print("棋盘大小不正确")
        return False
    
    # 验证回合
    if state["current_turn"] not in ["player", "computer"]:
        print("无效的回合状态")
        return False
    
    return True

def has_adjacent_ship(board: List[List[str]], x: int, y: int) -> bool:
    """检查指定位置是否有相邻的船只"""
    directions = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    ]
    
    for dx, dy in directions:
        new_x, new_y = x + dx, y + dy
        if (0 <= new_x < BOARD_SIZE and 
            0 <= new_y < BOARD_SIZE and 
            board[new_y][new_x] == "O"):
            return True
    return False

def is_valid_ship_placement(board: List[List[str]], start_x: int, start_y: int, 
                          size: int, horizontal: bool) -> bool:
    """检查船只放置是否有效
    
    检查:
    1. 边界限制
    2. 重叠检查
    3. 相邻船只检查
    """
    # 边界检查
    if horizontal:
        if start_x + size > BOARD_SIZE:
            return False
        positions = [(start_x + i, start_y) for i in range(size)]
    else:
        if start_y + size > BOARD_SIZE:
            return False
        positions = [(start_x, start_y + i) for i in range(size)]
    
    # 重叠和相邻检查
    for x, y in positions:
        if board[y][x] != "~" or has_adjacent_ship(board, x, y):
            return False
    
    return True

def place_ship(board: List[List[str]], ship_positions: List[tuple], symbol: str = "O") -> None:
    """在棋盘上放置船只"""
    for x, y in ship_positions:
        board[y][x] = symbol

def get_ship_positions(start_x: int, start_y: int, size: int, horizontal: bool) -> List[tuple]:
    """获取船只占据的位置"""
    if horizontal:
        return [(start_x + i, start_y) for i in range(size)]
    return [(start_x, start_y + i) for i in range(size)]

def init_game() -> GameState:
    """初始化游戏状态
    
    创建新的游戏状态,包括:
    1. 创建空棋盘
    2. 初始化游戏相关状态
    3. 设置布置阶段
    
    Returns:
        GameState: 初始化的游戏状态
    """
    return GameState(
        current_turn="player",
        player_board=create_empty_board(),
        computer_board=create_empty_board(),
        player_shots=[],
        computer_shots=[],
        message="请布置你的船只!",
        game_over=False,
        winner=None,
        player_ships={},
        computer_ships={},
        player_wins=0,
        computer_wins=0,
        setup_phase=True,
        current_ship="航空母舰",
        checking="checking_init"
    )

def setup_phase(state: GameState) -> GameState:
    """处理船只布置阶段"""
    print("====== 进入setup_phase节点 ======")
    print(f"当前状态: {state}")
    
    # 验证状态
    if not validate_state(state):
        print("状态验证失败,尝试修复状态...")
        # 修复缺失的字段而不是直接结束游戏
        if "winner" not in state:
            state["winner"] = None
        if "checking" not in state:
            state["checking"] = "checking_init"
        # 重新验证
        if not validate_state(state):
            print("状态修复失败")
            state["message"] = "游戏状态错误"
            state["game_over"] = True
            return state
        print("状态修复成功")
    
    if state["setup_phase"]:
        # 准备布置信息
        setup_info = {
            "message": f"请布置{state['current_ship']} (大小: {SHIP_SIZES[state['current_ship']]}格)",
            "board": state["player_board"],
            "current_ship": state["current_ship"],
            "ship_size": SHIP_SIZES[state["current_ship"]]
        }
        
        print("准备调用interrupt等待玩家布置...")
        print(f"interrupt参数: {setup_info}")
        action = interrupt(setup_info)
        print(f"interrupt返回值: {action}")
        
        # 解析布置动作
        try:
            x, y, horizontal = action
            print(f"解析布置动作: x={x}, y={y}, horizontal={horizontal}")
            ship_size = SHIP_SIZES[state["current_ship"]]
            
            # 验证并执行布置
            if is_valid_ship_placement(state["player_board"], x, y, ship_size, horizontal):
                positions = get_ship_positions(x, y, ship_size, horizontal)
                state["player_ships"][state["current_ship"]] = positions
                place_ship(state["player_board"], positions)
                print(f"成功放置{state['current_ship']}在位置{positions}")
                
                # 检查是否完成所有船只布置
                placed_ships = list(state["player_ships"].keys())
                remaining_ships = [s for s in SHIP_SIZES.keys() if s not in placed_ships]
                
                if remaining_ships:
                    state["current_ship"] = remaining_ships[0]
                    state["message"] = f"请布置{state['current_ship']}"
                    print(f"继续布置下一艘船: {state['current_ship']}")
                else:
                    print("所有玩家船只布置完成,开始布置电脑船只")
                    # 布置电脑的船只
                    for ship_name, size in SHIP_SIZES.items():
                        while True:
                            x = random.randint(0, BOARD_SIZE-1)
                            y = random.randint(0, BOARD_SIZE-1)
                            horizontal = random.choice([True, False])
                            if is_valid_ship_placement(state["computer_board"], x, y, size, horizontal):
                                positions = get_ship_positions(x, y, size, horizontal)
                                state["computer_ships"][ship_name] = positions
                                place_ship(state["computer_board"], positions)
                                print(f"电脑放置{ship_name}在位置{positions}")
                                break
                    
                    state["setup_phase"] = False
                    state["message"] = "游戏开始! 轮到你的回合"
                    print("布置阶段完成,进入游戏阶段")
            else:
                state["message"] = "无效的布置位置,请重试"
                print(f"无效的布置位置: x={x}, y={y}, horizontal={horizontal}")
        except Exception as e:
            print(f"处理布置动作时出错: {str(e)}")
            state["message"] = "布置操作无效,请重试"
    
    print(f"离开setup_phase节点, 状态: setup_phase={state['setup_phase']}, game_over={state['game_over']}")
    return state

def player_turn(state: GameState) -> GameState:
    """处理玩家回合
    
    这是一个Human-in-loop节点,使用langgraph的interrupt机制
    等待玩家的射击操作。
    
    工作流程:
    1. 检查是否玩家回合且游戏未结束
    2. 准备游戏状态信息
    3. 使用interrupt暂停执行,等待玩家射击
    4. 处理射击结果
    5. 更新游戏状态
    
    Args:
        state: 当前游戏状态
        
    Returns:
        更新后的游戏状态
    """
    print("====== 进入player_turn节点 ======")
    if state["current_turn"] == "player" and not state["game_over"]:
        # 准备游戏状态信息
        game_info = {
            "message": "你的回合,请选择射击位置",
            "player_board": state["player_board"],
            "computer_board": state["computer_board"],
            "player_shots": state["player_shots"]
        }
        
        # 使用interrupt等待玩家射击
        print("准备调用interrupt等待玩家射击...")
        print(f"interrupt参数: 'waiting for player shot'")
        action = interrupt("waiting for player shot")
        print(f"interrupt返回值: {action}")
        print(f"收到玩家射击动作: {action}")
        
        # 处理射击
        x, y = action
        
        # 检查是否有效射击
        if (x, y) not in state["player_shots"]:
            state["player_shots"].append((x, y))
            
            # 检查是否击中
            hit = False
            for ship_positions in state["computer_ships"].values():
                if (x, y) in ship_positions:
                    state["computer_board"][y][x] = "X"
                    hit = True
                    break
            
            if hit:
                state["message"] = "击中!"
                # 检查是否获胜
                if all(state["computer_board"][y][x] == "X" 
                      for positions in state["computer_ships"].values() 
                      for x, y in positions):
                    state["game_over"] = True
                    state["winner"] = "player"
                    state["player_wins"] += 1
                    state["message"] = "恭喜! 你赢了!"
            else:
                state["computer_board"][y][x] = "O"
                state["message"] = "未击中"
                state["current_turn"] = "computer"
        else:
            state["message"] = "该位置已经射击过,请选择其他位置"
    
    print("====== 离开player_turn节点 ======")        
    return state

def computer_turn(state: GameState) -> GameState:
    """处理电脑回合
    
    电脑使用简单的随机策略:
    1. 随机选择未射击过的位置
    2. 执行射击
    3. 检查结果并更新状态
    
    Args:
        state: 当前游戏状态
        
    Returns:
        更新后的游戏状态
    """
    print("====== 进入computer_turn节点 ======")
    if state["current_turn"] == "computer" and not state["game_over"]:
        # 电脑随机射击
        while True:
            x = random.randint(0, BOARD_SIZE-1)
            y = random.randint(0, BOARD_SIZE-1)
            if (x, y) not in state["computer_shots"]:
                break
        
        print(f"电脑选择射击位置: ({x}, {y})")
        state["computer_shots"].append((x, y))
        
        # 检查是否击中
        hit = False
        for ship_positions in state["player_ships"].values():
            if (x, y) in ship_positions:
                state["player_board"][y][x] = "X"
                hit = True
                break
        
        if hit:
            state["message"] = f"电脑击中了 ({x}, {y})!"
            # 检查是否获胜
            if all(state["player_board"][y][x] == "X" 
                  for positions in state["player_ships"].values() 
                  for x, y in positions):
                state["game_over"] = True
                state["winner"] = "computer"
                state["computer_wins"] += 1
                state["message"] = "游戏结束 - 电脑赢了!"
        else:
            state["player_board"][y][x] = "O"
            state["message"] = f"电脑未击中 ({x}, {y})"
        
        state["current_turn"] = "player"
    
    print("====== 离开computer_turn节点 ======")
    return state

def should_end(state: GameState) -> bool:
    """检查当前回合是否应该结束
    
    Args:
        state: 当前游戏状态
        
    Returns:
        bool: 是否应该结束
    """
    return state["game_over"]

def build_graph(checkpointer=None) -> StateGraph:
    """构建游戏流程图"""
    print("开始构建游戏流程图...")
    
    # 创建StateGraph
    workflow = StateGraph(GameState)
    print("创建StateGraph完成")
    
    # 添加节点
    workflow.add_node("setup_node", setup_phase)
    workflow.add_node("player_node", player_turn)
    workflow.add_node("computer_node", computer_turn)
    print("添加节点完成: setup_node, player_node, computer_node")
    
    # 设置边和条件
    workflow.add_edge(START, "setup_node")
    print("添加起始边: START -> setup_node")
    
    # 定义路由函数
    def setup_router(state: GameState) -> str:
        """布置阶段路由"""
        print(f"setup_router - setup_phase={state['setup_phase']}, game_over={state['game_over']}")
        if state["game_over"]:
            print("游戏结束,转到END")
            return "end"
        if not state["setup_phase"]:
            print("布置完成,转到player_node")
            return "player_node"
        print("继续布置,保持在setup_node")
        return "setup_node"
    
    def player_router(state: GameState) -> str:
        """玩家回合路由"""
        print(f"player_router - game_over: {state['game_over']}")
        if state["game_over"]:
            print("游戏结束,转到END")
            return "end"
        if state["current_turn"] == "computer":
            print("轮到电脑,转到computer_node")
            return "computer_node"
        print("继续玩家回合,保持在player_node")
        return "player_node"
    
    def computer_router(state: GameState) -> str:
        """电脑回合路由"""
        print(f"computer_router - game_over: {state['game_over']}")
        if state["game_over"]:
            print("游戏结束,转到END")
            return "end"
        if state["current_turn"] == "player":
            print("轮到玩家,转到player_node")
            return "player_node"
        print("继续电脑回合,保持在computer_node")
        return "computer_node"
    
    # 添加条件边
    workflow.add_conditional_edges(
        "setup_node",
        setup_router,
        {
            "setup_node": "setup_node",
            "player_node": "player_node",
            "end": END
        }
    )
    print("添加setup_node条件边完成")
    
    workflow.add_conditional_edges(
        "player_node",
        player_router,
        {
            "player_node": "player_node",
            "computer_node": "computer_node",
            "end": END
        }
    )
    print("添加player_node条件边完成")
    
    workflow.add_conditional_edges(
        "computer_node",
        computer_router,
        {
            "computer_node": "computer_node",
            "player_node": "player_node",
            "end": END
        }
    )
    print("添加computer_node条件边完成")
    
    print("图构建完成,准备编译...")
    compiled_graph = workflow.compile(checkpointer=checkpointer)
    print("图编译完成")
    
    return compiled_graph

def render_board(board: List[List[str]], hide_ships: bool = False):
    """渲染游戏棋盘"""
    # 创建表头
    cols = st.columns([0.5] + [1] * BOARD_SIZE)
    cols[0].write("")
    for i in range(BOARD_SIZE):
        cols[i + 1].write(str(i))
    
    # 渲染棋盘
    for y in range(BOARD_SIZE):
        cols = st.columns([0.5] + [1] * BOARD_SIZE)
        cols[0].write(str(y))
        for x in range(BOARD_SIZE):
            cell = board[y][x]
            if hide_ships and cell == "O":
                cell = "~"
            cols[x + 1].write(cell)

def render_game_message(message: str, status: str = "info"):
    """渲染游戏消息"""
    if status == "error":
        st.error(message)
    elif status == "success":
        st.success(message)
    elif status == "warning":
        st.warning(message)
    else:
        st.info(message)

def render_game_stats(player_wins: int, computer_wins: int):
    """渲染游戏统计"""
    col1, col2 = st.columns(2)
    col1.metric("玩家胜场", player_wins)
    col2.metric("电脑胜场", computer_wins)

def main():
    # 设置页面
    st.set_page_config(layout="wide", page_title="战舰游戏 v5")
    
    # 初始化游戏状态
    if "game_started" not in st.session_state:
        st.session_state.game_started = False
        st.session_state.thread_id = str(random.randint(1, 1000000))
    
    if not st.session_state.game_started:
        # 显示欢迎界面
        st.title("🚢 战舰游戏 v5")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            ### 欢迎来到战舰游戏!
            
            尝试击沉所有敌方战舰来取得胜利。
            
            #### 规则:
            - 每位玩家有4艘不同大小的战舰
            - 轮流射击对方的棋盘
            - 击中显示为X,未击中显示为O
            - 首先击沉对方所有战舰的一方获胜
            
            准备好了吗?
            """)
            
            if st.button("开始游戏", use_container_width=True):
                st.session_state.game_started = True
                initial_state = init_game()
                # 创建带checkpointer的graph
                checkpointer = MemorySaver()
                st.session_state.graph = build_graph(checkpointer=checkpointer)
                # 使用graph.invoke初始化游戏状态,设置递归限制
                config = {
                    "configurable": {
                        "thread_id": st.session_state.thread_id,
                        "recursion_limit": 100  # 在config中设置递归限制
                    }
                }
                print("准备调用graph.invoke初始化游戏...")
                print(f"invoke参数 - initial_state: {initial_state}")
                print(f"invoke参数 - config: {config}")
                st.session_state.game_state = st.session_state.graph.invoke(initial_state, config=config)
                print(f"invoke返回值: {st.session_state.game_state}")
                st.rerun()
    
    else:
        # 游戏主界面
        st.title("战舰游戏")
        
        if "game_state" not in st.session_state:
            initial_state = init_game()
            checkpointer = MemorySaver()
            st.session_state.graph = build_graph(checkpointer=checkpointer)
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            st.session_state.game_state = st.session_state.graph.invoke(initial_state, config=config)
        
        # 显示游戏统计
        render_game_stats(st.session_state.game_state["player_wins"],
                         st.session_state.game_state["computer_wins"])
        
        # 显示游戏信息
        render_game_message(st.session_state.game_state["message"])
        
        # 创建三列布局
        col1, col2, col3 = st.columns([1.2, 1.2, 0.8])
        
        with col1:
            st.subheader("你的棋盘")
            render_board(st.session_state.game_state["player_board"])
            
        with col2:
            st.subheader("对方棋盘")
            render_board(st.session_state.game_state["computer_board"], hide_ships=True)
            
            if not st.session_state.game_state["game_over"]:
                if st.session_state.game_state["setup_phase"]:
                    # 布置阶段的控制
                    current_ship = st.session_state.game_state["current_ship"]
                    ship_size = SHIP_SIZES[current_ship]
                    
                    col1, col2 = st.columns(2)
                    x = col1.number_input("X坐标", 0, BOARD_SIZE-1, key="ship_x")
                    y = col2.number_input("Y坐标", 0, BOARD_SIZE-1, key="ship_y")
                    horizontal = st.checkbox("水平放置", key="ship_horizontal")
                    
                    if st.button("放置战舰", use_container_width=True):
                        config = {
                            "configurable": {
                                "thread_id": st.session_state.thread_id,
                                "recursion_limit": 100
                            }
                        }
                        print("准备调用graph.invoke处理放置战舰...")
                        print(f"invoke参数 - Command(resume=(x, y, horizontal)): {(x, y, horizontal)}")
                        print(f"invoke参数 - config: {config}")
                        st.session_state.game_state = st.session_state.graph.invoke(
                            Command(resume=(x, y, horizontal)), config=config)
                        print(f"invoke返回值: {st.session_state.game_state}")
                        st.rerun()
                
                elif st.session_state.game_state["current_turn"] == "player":
                    # 玩家回合的控制
                    col1, col2 = st.columns(2)
                    shot_x = col1.number_input("射击X坐标", 0, BOARD_SIZE-1, key="shot_x")
                    shot_y = col2.number_input("射击Y坐标", 0, BOARD_SIZE-1, key="shot_y")
                    
                    if st.button("发射!", use_container_width=True):
                        config = {
                            "configurable": {
                                "thread_id": st.session_state.thread_id,
                                "recursion_limit": 100
                            }
                        }
                        print("准备调用graph.invoke处理玩家射击...")
                        print(f"invoke参数 - Command(resume=(shot_x, shot_y)): {(shot_x, shot_y)}")
                        print(f"invoke参数 - config: {config}")
                        st.session_state.game_state = st.session_state.graph.invoke(
                            Command(resume=(shot_x, shot_y)), config=config)
                        print(f"invoke返回值: {st.session_state.game_state}")
                        
                        # 如果轮到电脑回合,自动执行
                        if (not st.session_state.game_state["game_over"] and 
                            st.session_state.game_state["current_turn"] == "computer"):
                            print("准备调用graph.invoke处理电脑回合...")
                            print(f"invoke参数 - Command(resume=None)")
                            print(f"invoke参数 - config: {config}")
                            st.session_state.game_state = st.session_state.graph.invoke(
                                Command(resume=None), config=config)
                            print(f"invoke返回值: {st.session_state.game_state}")
                        st.rerun()
        
        with col3:
            st.subheader("游戏控制")
            
            if st.button("新游戏", key="restart", use_container_width=True):
                initial_state = init_game()
                # 保持胜场记录
                initial_state["player_wins"] = st.session_state.game_state["player_wins"]
                initial_state["computer_wins"] = st.session_state.game_state["computer_wins"]
                # 使用graph.invoke重新开始游戏
                config = {
                    "configurable": {
                        "thread_id": st.session_state.thread_id,
                        "recursion_limit": 100
                    }
                }
                print("准备调用graph.invoke重新开始游戏...")
                print(f"invoke参数 - initial_state: {initial_state}")
                print(f"invoke参数 - config: {config}")
                st.session_state.game_state = st.session_state.graph.invoke(initial_state, config=config)
                print(f"invoke返回值: {st.session_state.game_state}")
                st.rerun()
            
            with st.expander("游戏状态", expanded=False):
                st.json(st.session_state.game_state)

if __name__ == "__main__":
    main() 