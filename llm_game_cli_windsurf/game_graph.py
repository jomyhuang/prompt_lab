from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.types import interrupt, Command
from game_state import GameState, GameAction
import logging

logger = logging.getLogger(__name__)

def player_turn(state: GameState) -> GameState:
    """玩家回合处理
    
    等待玩家输入并更新状态
    
    Args:
        state: 当前游戏状态
        
    Returns:
        更新后的状态
    """
    logger.info("Processing player turn")
    
    # 使用interrupt暂停图执行,等待玩家输入
    return interrupt("等待玩家输入...")

def system_turn(state: GameState) -> GameState:
    """系统回合处理
    
    处理系统逻辑并更新状态
    
    Args:
        state: 当前游戏状态
        
    Returns:
        更新后的状态
    """
    logger.info("Processing system turn")
    
    # 在这里实现系统回合逻辑
    # 例如: AI决策、状态更新等
    
    return state

def should_end(state: GameState) -> bool:
    """检查是否应该结束游戏
    
    Args:
        state: 当前游戏状态
        
    Returns:
        是否应该结束
    """
    return state["game_over"]

def route_next(state: GameState) -> Literal["player_turn", "system_turn", END]:
    """路由到下一个节点
    
    Args:
        state: 当前游戏状态
        
    Returns:
        下一个节点名称
    """
    if should_end(state):
        return END
    elif state["current_turn"] == "player":
        return "player_turn"
    else:
        return "system_turn"

def build_game_graph(checkpointer=None) -> StateGraph:
    """构建游戏流程图
    
    使用LangGraph构建状态转换图:
    
    1. 创建基于GameState的StateGraph
    2. 添加玩家回合和系统回合节点
    3. 设置节点间的边和条件
    
    游戏流程:
    START -> route -> player_turn/system_turn -> END
    
    Args:
        checkpointer: 状态检查点保存器
        
    Returns:
        编译后的游戏流程图
    """
    # 创建图
    workflow = StateGraph(GameState)
    
    # 添加节点
    workflow.add_node("player_turn", player_turn)
    workflow.add_node("system_turn", system_turn)
    workflow.add_node("route", route_next)
    
    # 设置边
    workflow.set_entry_point("route")
    workflow.add_edge("route", "player_turn")
    workflow.add_edge("route", "system_turn")
    workflow.add_edge("player_turn", "route")
    workflow.add_edge("system_turn", "route")
    workflow.add_edge("route", END)
    
    # 编译图
    return workflow.compile(checkpointer=checkpointer)
