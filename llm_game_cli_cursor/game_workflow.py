from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
import logging
from game_state import GameState, GameAction

logger = logging.getLogger(__name__)

class GameWorkflow:
    """游戏工作流管理器
    
    处理游戏流程的构建和执行
    """
    def __init__(self, checkpointer: Optional[MemorySaver] = None):
        self.checkpointer = checkpointer
        self.logger = logging.getLogger(__name__)
        
    def build_graph(self) -> StateGraph:
        """构建游戏流程图
        
        Returns:
            StateGraph: 构建好的状态图
            
        Raises:
            RuntimeError: 图构建失败时抛出
        """
        try:
            # 1. 创建状态图
            workflow = StateGraph(GameState)
            
            # 2. 添加节点
            workflow.add_node("init", self._init_state)
            workflow.add_node("route", self._route_state)
            workflow.add_node("player", self._player_turn)
            workflow.add_node("ai", self._ai_turn)
            workflow.add_node("end", self._end_game)
            
            # 3. 设置边和条件
            workflow.set_entry_point("init")
            workflow.add_edge("init", "route")
            workflow.add_edge("route", "player")
            workflow.add_edge("route", "ai")
            workflow.add_edge("player", "route")
            workflow.add_edge("ai", "route")
            workflow.add_edge("route", "end")
            
            # 4. 添加条件流转
            workflow.add_conditional_edges(
                "route",
                self._route_condition,
                {
                    "player": "player",
                    "ai": "ai",
                    "end": END
                }
            )
            
            if not self.checkpointer:
                raise ValueError("build graph error, checkpointer is required")
            
            return workflow.compile(checkpointer=self.checkpointer)
            
        except Exception as e:
            self.logger.error(f"Failed to build graph: {str(e)}")
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
            state["current_turn"] = "player"
            
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
        print("[route_state] After interrupt ----")
        
        # 更新可用动作
        if state["current_turn"] == "player":
            state["valid_actions"] = ["play", "end_turn"]
            state["message"] = "请选择行动"
        else:
            state["valid_actions"] = []
            state["message"] = "AI回合..."
            
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
            return "ai"
    
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
            "message": state["message"],
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