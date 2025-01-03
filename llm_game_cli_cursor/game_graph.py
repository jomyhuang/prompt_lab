from typing import Dict, Any, Optional, List, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from dataclasses import dataclass
from datetime import datetime
import logging
import uuid
import random

# # 配置日志
# logging.basicConfig(
#     level=logging.INFO,
#     # format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
#     format='%(levelname)s - %(message)s'
# )
logger = logging.getLogger(__name__)

# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.DEBUG)
# logger.addHandler(console_handler)

class GameState(TypedDict):
    """游戏状态类型定义
    
    专注于LangGraph图节点状态:
    - 游戏进度状态
    - 对话历史
    - 动作历史
    - 会话上下文
    """
    game_started: bool          # 游戏是否开始
    messages: List[dict]        # 对话历史记录
    current_turn: str           # 当前回合玩家
    game_over: bool            # 游戏是否结束 
    game_data: dict            # 游戏数据(棋盘/卡牌等)
    last_action: str           # 最后执行的动作
    phase: str                 # 游戏阶段
    valid_actions: List[str]   # 当前可用动作
    action_history: List[dict] # 动作历史
    thread_id: str             # 会话ID
    error: Optional[str]       # 错误信息

@dataclass 
class GameAction:
    """游戏动作数据类
    
    记录动作相关信息用于状态转换
    """
    action_type: str
    player_id: str
    timestamp: datetime
    data: dict

class GameGraph:
    """游戏工作流管理器
    
    处理游戏流程的构建和执行,并管理游戏状态
    """
    def __init__(self, checkpointer: Optional[MemorySaver] = None, thread_id: str = None):
        if checkpointer is None:
            checkpointer = MemorySaver()
            logger.info("checkpointer is None, use GameGraph MemorySaver")
        
        if thread_id is None:
            thread_id = str(random.randint(1, 1000000))
            logger.info("thread_id is None, use GameGraph uuid")

        self.checkpointer = checkpointer
        self.thread_id = thread_id
        self.game_state = self.init_game_state()
        self.graph = self.build_graph()
       
    def init_game_state(self) -> GameState:
        """初始化游戏状态"""
        logger.info(f"[init_game_state] init game state")
        return GameState(
            game_started=False,
            messages=[],
            current_turn="player",
            game_over=False,
            game_data={},
            last_action="",
            phase="init",
            valid_actions=["start"],
            action_history=[],
            thread_id=str(uuid.uuid4()),
            error=None
        )

    def validate_state(self, state: GameState) -> bool:
        """验证游戏状态的有效性"""
        try:
            if not isinstance(state["current_turn"], str):
                raise ValueError("current_turn must be string")
            if not isinstance(state["valid_actions"], list):
                raise ValueError("valid_actions must be list") 
            return True
        except Exception as e:
            logger.error(f"State validation failed: {str(e)}")
            raise

    # def update_state(self, state: GameState, action: GameAction) -> GameState:
    #     """更新游戏状态"""
    #     try:
    #         new_state = state.copy()
    #         new_state["last_action"] = action.action_type
    #         new_state["action_history"].append({
    #             "type": action.action_type,
    #             "player": action.player_id,
    #             "time": action.timestamp.isoformat(),
    #             "data": action.data
    #         })
    #         self.game_state = new_state
    #         return new_state
    #     except Exception as e:
    #         logger.error(f"State update failed: {str(e)}")
    #         raise

    def get_game_state(self) -> GameState:
        """获取当前游戏状态"""
        return self.game_state

    def set_game_state(self, state: GameState):
        """设置当前游戏状态"""
        if self.validate_state(state):
            self.game_state = state
            logger.info("game_state set: new value")

    def build_graph(self) -> StateGraph:
        """构建游戏流程图
        
        Returns:
            StateGraph: 构建好的状态图
            
        Raises:
            RuntimeError: 图构建失败时抛出
        """

    # # 创建StateGraph
    # workflow = StateGraph(GameState)
    
    # # 添加节点
    # workflow.add_node("init_state", init_state)
    # workflow.add_node("route", route_state)
    # workflow.add_node("player_action", player_action)  # 合并后的玩家动作节点
    # workflow.add_node("computer_action", computer_action)
    # workflow.add_node("handle_end", handle_game_over)
    
    # # 设置边和条件
    # workflow.add_edge(START, "init_state")
    # workflow.add_edge("init_state", "route")
    
    # workflow.add_conditional_edges(
    #     "route",
    #     lambda x: (
    #         "handle_end" if x["game_over"] else
    #         "player_action" if x["current_turn"] == "player" else
    #         "computer_action"
    #     )
    # )
    
    # # 从player_action直接到computer_action
    # workflow.add_edge("player_action", "route")
    
    # # 从computer_action回到route
    # workflow.add_edge("computer_action", "route")
    
    # workflow.add_edge("handle_end", END)


        try:
            # 1. 创建状态图
            graph = StateGraph(GameState)
            
            # 2. 添加节点
            graph.add_node("init", self._init_state)
            graph.add_node("welcome", self._welcome_state)
            graph.add_node("route", self._route_state)
            graph.add_node("player", self._player_turn)
            graph.add_node("ai", self._ai_turn)
            graph.add_node("end", self._end_game)
            
            # 3. 设置边和条件
            # one-way turn
            graph.add_edge(START, "init")
            graph.add_edge("init", "welcome")
            graph.add_edge("welcome", "route")
            graph.add_edge("route", "player")
            graph.add_edge("player", "ai")
            graph.add_edge("ai", "end")
            graph.add_edge("end", END)

            # route to player and ai turn
            # graph.add_edge(START, "init")
            # graph.add_edge("init", "route")
            # graph.add_edge("route", "player")
            # graph.add_edge("player", "ai")
            # graph.add_edge("ai", "end")
            # graph.add_edge("end", END)

            # graph.add_edge("route", "player")
            # graph.add_edge("route", "ai")

            # graph.add_edge("player", "route")
            # graph.add_edge("ai", "route")
            # graph.add_edge("route", "end")
            # graph.add_edge("end", END)

            
            # # 4. 添加条件流转
            # graph.add_conditional_edges(
            #     "route",
            #     self._route_condition,
            #     {
            #         "player": "player",
            #         "ai": "ai",
            #         "end": "end"
            #     }
            # )
            
            if not self.checkpointer:
                logger.error("build graph error, checkpointer is required")
                raise ValueError("build graph error, checkpointer is required")
            
            return graph.compile(checkpointer=self.checkpointer)
            
        except Exception as e:
            logger.error(f"Failed to build graph: {str(e)}")
            raise RuntimeError(f"Graph build failed: {str(e)}")
    
    def _init_state(self, state: GameState) -> GameState:
        """初始化游戏状态
        
        Args:
            state: 初始状态
            
        Returns:
            GameState: 初始化后的状态
        """
        print("[init_state] 进入初始化节点")
        
        # 如果是新游戏，设置初始状态
        if not state["game_started"]:
            state["game_started"] = True
            state["phase"] = "init"
            state["message"] = "游戏开始！请选择你的行动。"
            state["valid_actions"] = ["play", "end_turn"]
            state["current_turn"] = "start"

        return state
    
    def _welcome_state(self, state: GameState) -> GameState:
        """欢迎状态，显示欢迎信息
        
        Args:
            state: 当前状态
            
        Returns:
            GameState: 更新后的状态
        """
        print("[welcome_state] 进入欢迎状态节点")
        return state
    
    def _route_state(self, state: GameState) -> GameState:
        """路由状态，决定下一步操作
        
        Args:
            state: 当前状态
            
        Returns:
            GameState: 更新后的状态
        """
        print("[route_state] 进入路由节点")
        print("[route_state] Before interrupt ----")
        # 使用interrupt等待UI更新
        action = interrupt("interrupt from route_state")
        print("[route_state] After interrupt ---- action:", action)
        
        # 更新可用动作
        if action == "start":
            state["current_turn"] = "player"
        elif state["current_turn"] == "player":
            state["valid_actions"] = ["play", "end_turn"]
            state["message"] = "请选择行动"
        elif state["current_turn"] == "ai":
            state["valid_actions"] = []
            state["message"] = "AI回合..."
        else:
            state["valid_actions"] = ["start"]
            state["message"] = "游戏开始！请选择你的行动。"
            
        return state
    
    def _route_condition(self, state: GameState) -> str:
        """路由条件判断
        
        Args:
            state: 当前状态
            
        Returns:
            str: 下一个节点名称
        """
        if state["game_over"]:
            return "end"
        elif state["current_turn"] == "player":
            return "player"
        else:
            return "player"
    
    def _player_turn(self, state: GameState) -> GameState:
        """玩家回合处理
        
        Args:
            state: 当前状态
            
        Returns:
            GameState: 更新后的状态
        """
        print("[player_turn] 进入玩家回合节点")
        if state["current_turn"] != "player" or state["game_over"]:
            return state
            
        # 准备游戏信息
        game_info = {
            # "message": state["messages"][-1],
            "valid_actions": state["valid_actions"],
            "game_data": state["game_data"]
        }
        
        # 使用interrupt等待玩家操作
        print("[player_turn] Before interrupt ----")
        action = interrupt(game_info)
        print("[player_turn] After interrupt ----", action)
        
        # 处理玩家操作
        if isinstance(action, dict):
            action_type = action.get("action")
            if action_type == "end_turn":
                state["current_turn"] = "ai"
                state["message"] = "回合结束"
            elif action_type == "play":
                # 处理玩家出牌等操作
                pass
                
        return state
    
    def _ai_turn(self, state: GameState) -> GameState:
        """AI回合处理
        
        Args:
            state: 当前状态
            
        Returns:
            GameState: 更新后的状态
        """
        print("[ai_turn] 进入AI回合节点")
        if state["current_turn"] != "ai" or state["game_over"]:
            return state
            
        # AI决策逻辑
        # TODO: 实现具体的AI决策
        
        # 回合结束
        state["current_turn"] = "player"
        state["message"] = "AI回合结束"
        
        return state
    
    def _end_game(self, state: GameState) -> GameState:
        """处理游戏结束
        
        Args:
            state: 当前状态
            
        Returns:
            GameState: 更新后的状态
        """
        print("[end_game] 进入游戏结束节点")
        state["message"] = "游戏结束"
        return state 