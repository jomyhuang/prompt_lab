# 回合切换Agent Chain示例

## 1. 回合切换流程

### 1.1 玩家回合结束Chain
```python
class PlayerTurnEndChain(Chain):
    """玩家回合结束处理链"""
    
    def __init__(
        self,
        game_master: GameMasterAgent,
        strategy: StrategyAgent,
        narrator: NarratorAgent
    ):
        self.game_master = game_master
        self.strategy = strategy
        self.narrator = narrator
        
    async def _call(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        # 获取当前游戏状态
        game_state = inputs["game_state"]
        
        # 1. 执行回合结束效果
        end_turn_effects = await self.game_master.execute_end_turn_effects(game_state)
        
        # 2. 生成回合总结
        turn_summary = await self.narrator.summarize_turn(game_state["turn_events"])
        
        # 3. 更新游戏状态
        new_state = await self.game_master.update_game_state({
            "type": "end_turn",
            "player": "player",
            "effects": end_turn_effects
        })
        
        return {
            "effects": end_turn_effects,
            "summary": turn_summary,
            "new_state": new_state
        }
```

### 1.2 对手回合开始Chain
```python
class OpponentTurnStartChain(Chain):
    """对手回合开始处理链"""
    
    def __init__(
        self,
        game_master: GameMasterAgent,
        strategy: StrategyAgent,
        narrator: NarratorAgent
    ):
        self.game_master = game_master
        self.strategy = strategy
        self.narrator = narrator
        
    async def _call(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        game_state = inputs["game_state"]
        
        # 1. 执行回合开始效果
        start_effects = await self.game_master.execute_start_turn_effects(game_state)
        
        # 2. 抽牌阶段
        draw_result = await self.game_master.execute_draw_phase("opponent")
        
        # 3. 获得法力值
        mana_result = await self.game_master.execute_mana_phase("opponent")
        
        # 4. 生成回合开始描述
        turn_start_desc = await self.narrator.describe_turn_start({
            "effects": start_effects,
            "draw": draw_result,
            "mana": mana_result
        })
        
        return {
            "start_effects": start_effects,
            "draw_result": draw_result,
            "mana_result": mana_result,
            "description": turn_start_desc
        }
```

## 2. 完整示例流程

### 2.1 回合切换协调器
```python
class TurnSwitchCoordinator:
    """回合切换协调器"""
    
    def __init__(self):
        self.game_master = GameMasterAgent()
        self.strategy = StrategyAgent()
        self.narrator = NarratorAgent()
        
        # 初始化Chain
        self.player_end_chain = PlayerTurnEndChain(
            self.game_master,
            self.strategy,
            self.narrator
        )
        self.opponent_start_chain = OpponentTurnStartChain(
            self.game_master,
            self.strategy,
            self.narrator
        )
        
    async def handle_turn_switch(self, game_state: dict) -> dict:
        """处理回合切换"""
        # 1. 处理玩家回合结束
        end_result = await self.player_end_chain.run({
            "game_state": game_state
        })
        
        # 2. 处理对手回合开始
        start_result = await self.opponent_start_chain.run({
            "game_state": end_result["new_state"]
        })
        
        # 3. 生成完整的切换描述
        switch_description = await self.narrator.generate_narration({
            "type": "turn_switch",
            "end_result": end_result,
            "start_result": start_result
        })
        
        return {
            "end_result": end_result,
            "start_result": start_result,
            "description": switch_description
        }
```

## 3. 使用示例

### 3.1 具体场景示例
```python
# 示例游戏状态
game_state = {
    "turn_info": {
        "current_turn": 3,
        "current_player": "player",
        "phase": "end_turn"
    },
    "player": {
        "health": 30,
        "mana": 0,
        "hand_cards": [...],
        "field_cards": [
            {"id": "card_1", "name": "战士", "attack": 2, "health": 3},
            {"id": "card_2", "name": "弓箭手", "attack": 1, "health": 1}
        ]
    },
    "opponent": {
        "health": 25,
        "mana": 0,
        "hand_cards": [...],
        "field_cards": [
            {"id": "card_3", "name": "守卫", "attack": 1, "health": 4}
        ]
    },
    "turn_events": [
        {"type": "play_card", "card_id": "card_1", "timestamp": 1640425200},
        {"type": "attack", "attacker": "card_2", "target": "opponent", "damage": 1}
    ]
}

# 执行回合切换
async def example_turn_switch():
    coordinator = TurnSwitchCoordinator()
    result = await coordinator.handle_turn_switch(game_state)
    
    # 输出结果示例
    print("回合切换结果:")
    print("\n1. 玩家回合结束:")
    print(f"- 结算效果: {result['end_result']['effects']}")
    print(f"- 回合总结: {result['end_result']['summary']}")
    
    print("\n2. 对手回合开始:")
    print(f"- 开始效果: {result['start_result']['start_effects']}")
    print(f"- 抽牌结果: {result['start_result']['draw_result']}")
    print(f"- 法力值: {result['start_result']['mana_result']}")
    
    print("\n3. 完整描述:")
    print(result['description'])
```

### 3.2 示例输出
```
回合切换结果:

1. 玩家回合结束:
- 结算效果: [
    {"type": "buff_fade", "card_id": "card_1", "buff": "临时攻击力+1"},
    {"type": "status_clear", "target": "all_field_cards"}
]
- 回合总结: "在这个回合中，你部署了一名战士，并用弓箭手对敌方英雄造成了1点伤害。"

2. 对手回合开始:
- 开始效果: [
    {"type": "buff_gain", "card_id": "card_3", "buff": "回合开始防御+1"}
]
- 抽牌结果: {"cards_drawn": 1, "deck_remaining": 20}
- 法力值: {"current": 4, "total": 4}

3. 完整描述:
"你的回合结束了。战士身上的临时增益消失，场上所有单位的状态被重置。
这个回合你成功部署了一名战士，并用弓箭手打出了关键的伤害。

现在是对手的回合。
对手的守卫获得了回合开始的防御增益。
对手抽了一张牌，获得了4点法力值。"
```

## 4. 关键点说明

### 4.1 状态管理
- 每个Chain都负责管理自己的状态转换
- 使用游戏主持Agent确保状态转换的合法性
- 通过协调器确保状态的一致性

### 4.2 错误处理
```python
try:
    result = await coordinator.handle_turn_switch(game_state)
except GameStateError as e:
    # 处理游戏状态错误
    logger.error(f"游戏状态错误: {e}")
    # 尝试恢复到上一个有效状态
    game_state = await game_master.rollback_to_last_valid_state()
except ChainExecutionError as e:
    # 处理Chain执行错误
    logger.error(f"Chain执行错误: {e}")
    # 执行错误恢复流程
    await error_recovery_procedure()
```

### 4.3 性能优化
- 使用异步处理提高响应速度
- 实现状态缓存减少计算开销
- 批量处理效果减少更新次数

### 4.4 扩展性考虑
- Chain设计支持插入新的处理步骤
- Agent接口支持添加新的行为
- 事件系统支持自定义效果
