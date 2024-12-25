# 行动阶段Agent Chain示例

## 1. 玩家行动阶段

### 1.1 玩家抽牌Chain
```python
class PlayerDrawPhaseChain(Chain):
    """玩家抽牌阶段处理链"""
    
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
        
        # 1. 执行抽牌
        draw_result = await self.game_master.execute_draw_phase("player", count=1)
        
        # 2. 触发抽牌相关效果
        draw_effects = await self.game_master.process_draw_effects(draw_result)
        
        # 3. 分析新的手牌
        hand_analysis = await self.strategy.analyze_hand(game_state["player"]["hand_cards"])
        
        # 4. 生成抽牌描述
        draw_description = await self.narrator.describe_draw_phase(draw_result, draw_effects)
        
        return {
            "draw_result": draw_result,
            "effects": draw_effects,
            "hand_analysis": hand_analysis,
            "description": draw_description
        }
```

### 1.2 玩家出牌Chain
```python
class PlayerPlayCardChain(Chain):
    """玩家出牌阶段处理链"""
    
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
        card_id = inputs["card_id"]
        target_id = inputs.get("target_id")
        
        # 1. 验证出牌合法性
        validation = await self.game_master.validate_play_card(card_id, target_id)
        if not validation["valid"]:
            raise InvalidActionError(validation["reason"])
            
        # 2. 获取策略建议
        strategy_advice = await self.strategy.analyze_card_play(
            card_id,
            target_id,
            game_state
        )
        
        # 3. 执行出牌
        play_result = await self.game_master.execute_play_card(card_id, target_id)
        
        # 4. 处理入场效果
        entry_effects = await self.game_master.process_entry_effects(play_result)
        
        # 5. 生成出牌描述
        play_description = await self.narrator.describe_card_play({
            "play": play_result,
            "effects": entry_effects,
            "strategy": strategy_advice
        })
        
        return {
            "play_result": play_result,
            "entry_effects": entry_effects,
            "strategy_advice": strategy_advice,
            "description": play_description
        }
```

## 2. 对手行动阶段

### 2.1 对手抽牌Chain
```python
class OpponentDrawPhaseChain(Chain):
    """对手抽牌阶段处理链"""
    
    async def _call(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        game_state = inputs["game_state"]
        
        # 1. 执行抽牌
        draw_result = await self.game_master.execute_draw_phase("opponent", count=1)
        
        # 2. 处理抽牌效果
        draw_effects = await self.game_master.process_draw_effects(draw_result)
        
        # 3. 生成描述（对手抽牌信息应该是隐藏的）
        draw_description = await self.narrator.describe_opponent_draw(draw_result)
        
        return {
            "draw_result": draw_result,
            "effects": draw_effects,
            "description": draw_description
        }
```

### 2.2 对手出牌Chain
```python
class OpponentPlayCardChain(Chain):
    """对手出牌阶段处理链"""
    
    async def _call(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        game_state = inputs["game_state"]
        
        # 1. AI决策选择要出的牌
        decision = await self.strategy.decide_opponent_play(game_state)
        
        # 2. 执行出牌
        play_result = await self.game_master.execute_play_card(
            decision["card_id"],
            decision["target_id"]
        )
        
        # 3. 处理入场效果
        entry_effects = await self.game_master.process_entry_effects(play_result)
        
        # 4. 生成描述
        play_description = await self.narrator.describe_opponent_play({
            "play": play_result,
            "effects": entry_effects
        })
        
        return {
            "play_result": play_result,
            "entry_effects": entry_effects,
            "description": play_description
        }
```

## 3. 完整示例流程

### 3.1 示例游戏状态
```python
game_state = {
    "turn_info": {
        "current_turn": 2,
        "current_player": "player",
        "phase": "action"
    },
    "player": {
        "health": 30,
        "mana": 2,
        "deck": {"remaining": 25},
        "hand_cards": [
            {
                "id": "card_1",
                "name": "见习法师",
                "cost": 2,
                "attack": 2,
                "health": 2,
                "effects": ["入场: 造成1点伤害"]
            }
        ],
        "field_cards": []
    },
    "opponent": {
        "health": 30,
        "mana": 2,
        "deck": {"remaining": 24},
        "hand_cards": ["hidden_card_1", "hidden_card_2"],
        "field_cards": [
            {
                "id": "card_3",
                "name": "小鬼",
                "attack": 1,
                "health": 1
            }
        ]
    }
}
```

### 3.2 玩家回合示例
```python
async def example_player_turn():
    # 初始化协调器
    coordinator = ActionPhaseCoordinator()
    
    # 1. 玩家抽牌阶段
    draw_result = await coordinator.player_draw_chain.run({
        "game_state": game_state
    })
    print("玩家抽牌:")
    print(draw_result["description"])  # "你抽到了一张'见习法师'。"
    
    # 2. 玩家出牌阶段
    play_result = await coordinator.player_play_chain.run({
        "game_state": game_state,
        "card_id": "card_1",
        "target_id": "card_3"  # 目标是对手的小鬼
    })
    
    print("\n玩家出牌:")
    print(play_result["description"])
    # 输出示例：
    # "你使用了见习法师（2/2）。
    # 入场效果触发：对小鬼造成1点伤害。
    # 小鬼被消灭了！
    # 策略分析：这是一个不错的选择，成功清除了对手的威胁。"
```

### 3.3 对手回合示例
```python
async def example_opponent_turn():
    coordinator = ActionPhaseCoordinator()
    
    # 1. 对手抽牌阶段
    draw_result = await coordinator.opponent_draw_chain.run({
        "game_state": game_state
    })
    print("对手抽牌:")
    print(draw_result["description"])  # "对手从牌库抽了一张牌。"
    
    # 2. 对手出牌阶段
    play_result = await coordinator.opponent_play_chain.run({
        "game_state": game_state
    })
    
    print("\n对手出牌:")
    print(play_result["description"])
    # 输出示例：
    # "对手使用了火焰术士（2/3）。
    # 入场效果触发：对你的见习法师造成1点伤害。
    # 你的见习法师现在是2/1。"
```

## 4. 效果处理系统

### 4.1 入场效果处理器
```python
class EntryEffectProcessor:
    """入场效果处理器"""
    
    async def process_effect(self, effect: dict, game_state: dict) -> dict:
        effect_type = effect["type"]
        
        if effect_type == "damage":
            return await self._process_damage_effect(effect, game_state)
        elif effect_type == "heal":
            return await self._process_heal_effect(effect, game_state)
        elif effect_type == "buff":
            return await self._process_buff_effect(effect, game_state)
        else:
            raise UnknownEffectError(f"未知的效果类型: {effect_type}")
    
    async def _process_damage_effect(self, effect: dict, game_state: dict) -> dict:
        """处理伤害效果"""
        target = self._get_target(effect["target_id"], game_state)
        damage = effect["value"]
        
        # 应用伤害
        target["health"] -= damage
        
        # 检查死亡
        if target["health"] <= 0:
            await self._handle_death(target, game_state)
            
        return {
            "type": "damage",
            "target": target["id"],
            "value": damage,
            "result": "death" if target["health"] <= 0 else "alive"
        }
```

### 4.2 效果队列管理器
```python
class EffectQueueManager:
    """效果队列管理器"""
    
    def __init__(self):
        self.effect_queue = []
        self.processor = EntryEffectProcessor()
    
    async def add_effect(self, effect: dict):
        """添加效果到队列"""
        self.effect_queue.append(effect)
    
    async def process_queue(self, game_state: dict) -> List[dict]:
        """处理效果队列"""
        results = []
        
        while self.effect_queue:
            effect = self.effect_queue.pop(0)
            result = await self.processor.process_effect(effect, game_state)
            results.append(result)
            
            # 检查是否触发了新的效果
            triggered_effects = await self._check_triggers(result, game_state)
            self.effect_queue.extend(triggered_effects)
        
        return results
```

## 5. 关键设计要点

### 5.1 状态验证
- 每次行动前都要验证合法性
- 检查资源是否足够
- 验证目标是否有效

### 5.2 效果处理
- 使用队列管理效果触发顺序
- 支持效果的连锁触发
- 处理效果之间的相互影响

### 5.3 AI决策
- 考虑场面状态
- 评估行动价值
- 预测对手反应

### 5.4 信息隐藏
- 对手手牌信息对玩家不可见
- 某些效果的具体内容可能需要隐藏
- 战略分析不应泄露对手信息

这个示例展示了一个完整的行动阶段流程，包括：
1. 抽牌和效果触发
2. 出牌决策和执行
3. 入场效果处理
4. AI对手的决策过程

每个环节都有相应的Chain处理，并且通过协调器来管理整个流程。效果系统使用队列来管理复杂的效果触发序列，确保游戏规则的正确执行。
