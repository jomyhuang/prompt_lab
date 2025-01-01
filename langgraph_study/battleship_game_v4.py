import streamlit as st
import random
from typing import Annotated, TypedDict, Literal, List, Dict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver

# 游戏常量
BOARD_SIZE = 8
EMPTY = "🌊"  # 空海域
SHIP = "🚢"   # 船只
HIT = "💥"    # 命中
MISS = "❌"   # 未命中
HIDDEN = "⬜" # 隐藏的格子

# 定义游戏状态
class GameState(TypedDict):
    messages: Annotated[list, add_messages]  # 游戏消息记录
    current_turn: Literal["player", "computer"]  # 当前回合
    game_over: bool  # 游戏是否结束
    player_board: List[List[str]]  # 玩家的棋盘
    computer_board: List[List[str]]  # 电脑的棋盘
    computer_ships: List[Dict]  # 电脑的船只位置
    player_ships: List[Dict]  # 玩家的船只位置
    last_hit: Dict  # 最后一次命中位置
    player_wins: int  # 玩家胜场
    computer_wins: int  # 电脑胜场

def create_empty_board() -> List[List[str]]:
    """创建空棋盘"""
    return [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

def place_ships(board: List[List[str]], num_ships: int = 3) -> List[Dict]:
    """放置船只"""
    ships = []
    for _ in range(num_ships):
        while True:
            x = random.randint(0, BOARD_SIZE-1)
            y = random.randint(0, BOARD_SIZE-1)
            if board[x][y] == EMPTY:
                board[x][y] = SHIP
                ships.append({"x": x, "y": y, "sunk": False})
                break
    return ships

def init_game() -> GameState:
    """初始化游戏状态"""
    player_board = create_empty_board()
    computer_board = create_empty_board()
    
    return GameState(
        messages=["游戏开始! 请输入攻击坐标 (格式: x,y)"],
        current_turn="player",
        game_over=False,
        player_board=player_board,
        computer_board=computer_board,
        computer_ships=place_ships(computer_board),
        player_ships=place_ships(player_board),
        last_hit={"x": -1, "y": -1, "sunk": True},
        player_wins=0,
        computer_wins=0
    )

def check_game_over(state: GameState) -> bool:
    """检查游戏是否结束"""
    return (all(ship["sunk"] for ship in state["player_ships"]) or 
            all(ship["sunk"] for ship in state["computer_ships"]))

def player_turn(state: GameState) -> GameState:
    """玩家回合，使用human-in-loop机制"""
    print("=== 进入 player_turn 节点 ===")
    # 只在玩家回合且游戏未结束时等待操作
    if state["current_turn"] == "player" and not state["game_over"]:
        # 准备展示给玩家的游戏状态信息
        game_info = {
            "message": "你的回合! 请输入攻击坐标 (格式: x,y)",
            "player_board": state["player_board"],
            "computer_board": state["computer_board"],
            "game_stats": {
                "player_wins": state["player_wins"],
                "computer_wins": state["computer_wins"]
            }
        }
        
        # 使用interrupt等待玩家操作
        action = interrupt(game_info)
        
        try:
            x, y = map(int, action.split(","))
            if not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE):
                state["messages"].append("坐标超出范围,请输入0-7之间的数字")
                return state
                
            if state["computer_board"][x][y] in [HIT, MISS]:
                state["messages"].append(f"这个{x}, {y}位置已经攻击过了,请选择其他位置")
                return state
                
            # 执行攻击
            hit = False
            for ship in state["computer_ships"]:
                if ship["x"] == x and ship["y"] == y:
                    hit = True
                    ship["sunk"] = True
                    break
                    
            state["computer_board"][x][y] = HIT if hit else MISS
            state["messages"].append(f"你的攻击坐标 ({x},{y}): {'命中!' if hit else '未命中'}")
            
            if hit:
                state["messages"].append("你击沉了一艘敌舰!")
                
            if check_game_over(state):
                state["game_over"] = True
                state["messages"].append("恭喜! 你赢了!")
                state["player_wins"] += 1
            else:
                state["current_turn"] = "computer"
                
        except ValueError:
            state["messages"].append("无效的坐标格式,请使用x,y格式(例如:3,4)")
        
    return state

def computer_turn(state: GameState) -> GameState:
    """电脑回合"""
    print("=== 进入 computer_turn 节点 ===")
    if state["current_turn"] == "computer" and not state["game_over"]:
        # 选择攻击位置
        if not state["last_hit"]["sunk"]:
            # 如果上次命中但未击沉,尝试周围位置
            x, y = state["last_hit"]["x"], state["last_hit"]["y"]
            directions = [(0,1), (0,-1), (1,0), (-1,0)]
            random.shuffle(directions)
            for dx, dy in directions:
                new_x, new_y = x + dx, y + dy
                if (0 <= new_x < BOARD_SIZE and 
                    0 <= new_y < BOARD_SIZE and 
                    state["player_board"][new_x][new_y] in [EMPTY, SHIP]):
                    x, y = new_x, new_y
                    break
        else:
            # 随机选择位置
            while True:
                x = random.randint(0, BOARD_SIZE-1)
                y = random.randint(0, BOARD_SIZE-1)
                if state["player_board"][x][y] in [EMPTY, SHIP]:
                    break
        
        # 执行攻击
        hit = state["player_board"][x][y] == SHIP
        state["player_board"][x][y] = HIT if hit else MISS
        state["messages"].append(f"电脑攻击坐标 ({x},{y}): {'命中!' if hit else '未命中'}")
        
        # 更新last_hit状态
        if hit:
            state["last_hit"] = {"x": x, "y": y, "sunk": False}
            for ship in state["player_ships"]:
                if ship["x"] == x and ship["y"] == y:
                    ship["sunk"] = True
                    state["last_hit"]["sunk"] = True
                    state["messages"].append("电脑击沉了你的一艘船!")
                    break
        else:
            state["last_hit"]["sunk"] = True
        
        if check_game_over(state):
            state["game_over"] = True
            state["messages"].append("游戏结束! 电脑赢了!")
            state["computer_wins"] += 1
        else:
            state["current_turn"] = "player"
            state["messages"].append("轮到你了! 请输入攻击坐标 (x,y)")
    
    return state

def should_end(state: GameState) -> bool:
    """检查是否应该结束当前回合"""
    print("=== 检查 should_end 条件 ===")
    return state["game_over"]

def build_graph(checkpointer=None) -> StateGraph:
    """构建游戏流程图
    
    游戏流程:
    START -> player_turn -> computer_turn -> END
    
    状态转换规则:
    - player_turn节点:
      * 继续攻击: 留在player_turn
      * 攻击完成: 转到computer_turn
      * 游戏结束: 直接到END
    - computer_turn节点:
      * 游戏结束: 到END
      * 否则: 返回player_turn
    """
    # 创建StateGraph
    workflow = StateGraph(GameState)
    
    # 添加节点
    workflow.add_node("player_turn", player_turn)
    workflow.add_node("computer_turn", computer_turn)
    
    # 设置边和条件
    workflow.add_edge(START, "player_turn")
    
    # 从player_turn可以:
    workflow.add_conditional_edges(
        "player_turn",
        lambda x: "end" if x["game_over"] else ("computer" if x["current_turn"] == "computer" else "player"),
        {
            "player": "player_turn",
            "computer": "computer_turn",
            "end": END
        }
    )
    
    # 从computer_turn可以:
    workflow.add_conditional_edges(
        "computer_turn",
        should_end,
        {
            True: END,
            False: "player_turn"
        }
    )
    
    return workflow.compile(checkpointer=checkpointer)

def render_board(board: List[List[str]], hide_ships: bool = False):
    """渲染棋盘"""
    # 列标题
    cols = st.columns([0.5] + [1] * BOARD_SIZE)
    cols[0].write("")
    for i in range(BOARD_SIZE):
        cols[i+1].write(str(i))
    
    # 棋盘内容
    for i in range(BOARD_SIZE):
        cols = st.columns([0.5] + [1] * BOARD_SIZE)
        cols[0].write(str(i))
        for j in range(BOARD_SIZE):
            cell = board[i][j]
            if hide_ships and cell == SHIP:
                cell = HIDDEN
            cols[j+1].write(cell)

def render_game_stats(player_wins: int, computer_wins: int):
    """渲染游戏统计信息"""
    st.markdown(f"""
    ### 游戏统计
    - 玩家胜场: {player_wins}
    - 电脑胜场: {computer_wins}
    """)

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

def main():
    # 设置页面
    st.set_page_config(layout="wide", page_title="海战棋 V4")
    
    # 初始化游戏状态
    if "game_started" not in st.session_state:
        st.session_state.game_started = False
        st.session_state.thread_id = str(random.randint(1, 1000000))
    
    if not st.session_state.game_started:
        # 显示欢迎界面
        st.title("🚢 海战棋 V4")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            ### 欢迎来到海战棋!
            
            尝试击沉所有敌方船只来获得胜利。
            
            #### 规则:
            - 每方有3艘船
            - 输入坐标(x,y)来进行攻击
            - 🌊 表示空海域
            - 💥 表示命中
            - ❌ 表示未命中
            - ⬜ 表示未探索区域
            
            准备好了吗?
            """)
            
            if st.button("开始游戏", use_container_width=True):
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
        st.title("海战棋 V4")
        
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
        for msg in st.session_state.game_state["messages"][-3:]:
            print(msg)
            render_game_message(msg.content)
        
        # 创建三列布局
        col1, col2, col3 = st.columns([1.2, 1.2, 0.8])
        
        with col1:
            st.subheader("你的棋盘")
            render_board(st.session_state.game_state["player_board"])
            
        with col2:
            st.subheader("电脑的棋盘")
            render_board(st.session_state.game_state["computer_board"], hide_ships=True)
            
        with col3:
            st.subheader("游戏控制")
            if not st.session_state.game_state["game_over"]:
                # 玩家回合时显示输入框
                if st.session_state.game_state["current_turn"] == "player":
                    coord_input = st.text_input("输入攻击坐标 (x,y):", key="coord_input")
                    if st.button("攻击", use_container_width=True):
                        config = {"configurable": {"thread_id": st.session_state.thread_id}}
                        st.session_state.game_state = st.session_state.graph.invoke(
                            Command(resume=coord_input), config=config)
                        st.rerun()
                else:
                    st.info("电脑正在思考...")
                    config = {"configurable": {"thread_id": st.session_state.thread_id}}
                    st.session_state.game_state = st.session_state.graph.invoke(
                        Command(resume="computer_turn"), config=config)
                    st.rerun()
            
            if st.button("新游戏", key="restart", use_container_width=True):
                initial_state = init_game()
                # 保持胜场记录
                initial_state["player_wins"] = st.session_state.game_state["player_wins"]
                initial_state["computer_wins"] = st.session_state.game_state["computer_wins"]
                # 使用graph.invoke重新开始游戏
                config = {"configurable": {"thread_id": st.session_state.thread_id}}
                st.session_state.game_state = st.session_state.graph.invoke(initial_state, config=config)
                st.rerun()

if __name__ == "__main__":
    main()
