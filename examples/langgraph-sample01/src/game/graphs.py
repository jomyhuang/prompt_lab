"""游戏图定义"""
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from .models import GameState
from .nodes import (
    phase_manager,
    rule_engine,
    combat_resolver,
    effect_processor,
    action_selector,
    player_action
)

def create_game_graph() -> StateGraph:
    """创建游戏流程图"""
    
    # 创建状态图
    workflow = StateGraph(GameState)
    
    # 添加节点
    workflow.add_node("phase_manager", phase_manager)
    workflow.add_node("rule_engine", rule_engine)
    workflow.add_node("combat_resolver", combat_resolver)
    workflow.add_node("effect_processor", effect_processor)
    workflow.add_node("action_selector", action_selector)
    workflow.add_node("player_action", player_action)
    
    # 定义边
    workflow.add_edge("phase_manager", "action_selector")
    workflow.add_edge("action_selector", "player_action")
    workflow.add_edge("player_action", "rule_engine")
    workflow.add_edge("rule_engine", "effect_processor")
    workflow.add_edge("effect_processor", "phase_manager")
    
    # 设置条件边
    workflow.add_conditional_edges(
        "action_selector",
        condition=lambda x: x["next_action"],
        handlers={
            "combat": "combat_resolver",
            "resolve_stack": "effect_processor",
            "main_phase": "player_action",
            "end_turn": END
        }
    )
    
    return workflow

def create_combat_graph() -> StateGraph:
    """创建战斗流程图"""
    
    async def declare_attackers(state: GameState) -> GameState:
        # TODO: 实现宣告攻击者逻辑
        return state
    
    async def declare_blockers(state: GameState) -> GameState:
        # TODO: 实现宣告阻挡者逻辑
        return state
    
    async def combat_damage(state: GameState) -> GameState:
        # TODO: 实现战斗伤害逻辑
        return state
    
    async def combat_effects(state: GameState) -> GameState:
        # TODO: 实现战斗效果逻辑
        return state
    
    combat = StateGraph(GameState)
    
    # 添加战斗相关节点
    combat.add_node("declare_attackers", declare_attackers)
    combat.add_node("declare_blockers", declare_blockers)
    combat.add_node("combat_damage", combat_damage)
    combat.add_node("combat_effects", combat_effects)
    
    # 定义战斗流程
    combat.add_edge("declare_attackers", "declare_blockers")
    combat.add_edge("declare_blockers", "combat_damage")
    combat.add_edge("combat_damage", "combat_effects")
    combat.add_edge("combat_effects", END)
    
    return combat
