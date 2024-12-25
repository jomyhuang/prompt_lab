# LangGraph游戏系统设计

## 1. 状态定义

### 1.1 游戏状态
```python
from typing import Dict, List, Optional, TypedDict
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

class GameState(BaseModel):
    """游戏状态"""
    game_id: str
    turn: int
    phase: str
    active_player: str
    players: Dict[str, "PlayerState"]
    board: "BoardState"
    stack: List["Effect"]
    history: List["Action"]

class PlayerState(BaseModel):
    """玩家状态"""
    player_id: str
    life: int
    mana: Dict[str, int]
    hand: List["Card"]
    deck: List["Card"]
    board: List["Card"]

class BoardState(BaseModel):
    """场面状态"""
    creatures: List["Creature"]
    enchantments: List["Enchantment"]
    artifacts: List["Artifact"]
```

## 2. 节点定义

### 2.1 基础节点
```python
from langgraph.prebuilt import ToolExecutor
from langchain.chat_models import ChatOpenAI

async def phase_manager(state: GameState) -> GameState:
    """阶段管理节点"""
    # 处理阶段转换逻辑
    return state

async def rule_engine(state: GameState) -> GameState:
    """规则引擎节点"""
    # 处理规则检查和执行
    return state

async def combat_resolver(state: GameState) -> GameState:
    """战斗解析节点"""
    # 处理战斗结算
    return state

async def effect_processor(state: GameState) -> GameState:
    """效果处理节点"""
    # 处理效果触发和结算
    return state
```

### 2.2 决策节点
```python
async def action_selector(state: GameState) -> str:
    """行动选择节点"""
    # 根据状态选择下一个行动
    if state.phase == "combat":
        return "combat"
    elif len(state.stack) > 0:
        return "resolve_stack"
    else:
        return "main_phase"

async def player_action(state: GameState) -> GameState:
    """玩家行动节点"""
    llm = ChatOpenAI()
    response = await llm.ainvoke({
        "role": "system",
        "content": f"你是玩家 {state.active_player}，请根据当前状态选择最优行动"
    })
    # 处理玩家行动
    return state
```

## 3. 图定义

### 3.1 主游戏图
```python
from langgraph.graph import Graph, StateGraph

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
```

### 3.2 战斗图
```python
def create_combat_graph() -> StateGraph:
    """创建战斗流程图"""
    
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
```

## 4. 执行器定义

### 4.1 游戏执行器
```python
class GameExecutor:
    """游戏执行器"""
    
    def __init__(self):
        self.game_graph = create_game_graph()
        self.combat_graph = create_combat_graph()
        
    async def execute_game(self, initial_state: GameState) -> GameState:
        """执行游戏"""
        app = self.game_graph.compile()
        final_state = await app.ainvoke(initial_state)
        return final_state
    
    async def execute_combat(self, combat_state: GameState) -> GameState:
        """执行战斗"""
        app = self.combat_graph.compile()
        final_state = await app.ainvoke(combat_state)
        return final_state
```

## 5. 使用示例

### 5.1 游戏执行示例
```python
async def run_game():
    """运行游戏示例"""
    
    # 创建初始状态
    initial_state = GameState(
        game_id="GAME_001",
        turn=1,
        phase="start",
        active_player="P1",
        players={
            "P1": PlayerState(...),
            "P2": PlayerState(...)
        },
        board=BoardState(...),
        stack=[],
        history=[]
    )
    
    # 创建执行器
    executor = GameExecutor()
    
    # 执行游戏
    try:
        final_state = await executor.execute_game(initial_state)
        print(f"Game completed. Winner: {final_state.winner}")
    except Exception as e:
        print(f"Game error: {e}")
```

### 5.2 回合执行示例
```python
async def execute_turn(state: GameState) -> GameState:
    """执行单个回合"""
    
    # 定义回合图
    turn = StateGraph(GameState)
    
    # 添加回合阶段
    turn.add_node("untap", untap_step)
    turn.add_node("upkeep", upkeep_step)
    turn.add_node("draw", draw_step)
    turn.add_node("main1", main_phase)
    turn.add_node("combat", combat_phase)
    turn.add_node("main2", main_phase)
    turn.add_node("end", end_step)
    
    # 定义回合流程
    turn.add_edge("untap", "upkeep")
    turn.add_edge("upkeep", "draw")
    turn.add_edge("draw", "main1")
    turn.add_edge("main1", "combat")
    turn.add_edge("combat", "main2")
    turn.add_edge("main2", "end")
    turn.add_edge("end", END)
    
    # 编译和执行
    app = turn.compile()
    final_state = await app.ainvoke(state)
    return final_state
```

## 6. 最佳实践

### 6.1 状态管理
1. 状态不可变性
   - 每次更新创建新状态
   - 避免直接修改状态

2. 状态验证
   - 使用Pydantic验证
   - 确保状态一致性

3. 状态回滚
   - 保存状态快照
   - 支持状态恢复

### 6.2 图设计
1. 模块化
   - 拆分子图
   - 复用通用节点

2. 错误处理
   - 节点级错误处理
   - 图级错误恢复

3. 性能优化
   - 并行处理
   - 状态缓存

### 6.3 扩展性
1. 自定义节点
   - 支持新游戏机制
   - 灵活的规则扩展

2. 状态观察
   - 状态变化通知
   - 事件追踪

3. 调试支持
   - 详细的日志
   - 状态可视化

这个设计提供了：
1. 清晰的状态流转
2. 灵活的图结构
3. 完整的执行机制
4. 可扩展的架构

LangGraph的优势在于：
1. 更适合处理有状态流转的系统
2. 支持复杂的条件分支
3. 更好的并行处理
4. 更清晰的执行流程

您觉得这个基于LangGraph的设计如何？需要我详细解释某些部分吗？
