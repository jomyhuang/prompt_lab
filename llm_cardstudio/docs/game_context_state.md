# 游戏上下文与状态设计

## 1. 游戏上下文模型

### 1.1 基础上下文结构
```python
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class GameContext(BaseModel):
    """游戏上下文基础模型"""
    game_id: str = Field(..., description="游戏唯一标识")
    start_time: datetime = Field(..., description="游戏开始时间")
    game_type: str = Field(..., description="游戏类型")
    players: Dict[str, "PlayerContext"] = Field(..., description="玩家上下文")
    current_turn: int = Field(0, description="当前回合数")
    current_phase: str = Field(..., description="当前游戏阶段")
    action_history: List["GameAction"] = Field(default_factory=list, description="行动历史")
    effect_queue: List["GameEffect"] = Field(default_factory=list, description="效果队列")
    
class PlayerContext(BaseModel):
    """玩家上下文模型"""
    player_id: str = Field(..., description="玩家ID")
    deck_info: "DeckContext" = Field(..., description="牌组信息")
    resources: "ResourceContext" = Field(..., description="资源信息")
    board_state: "BoardState" = Field(..., description="场面状态")
    hand_cards: List["Card"] = Field(default_factory=list, description="手牌")
    effects: List["Effect"] = Field(default_factory=list, description="持续效果")
```

### 1.2 上下文示例
```json
{
    "game_context": {
        "game_id": "GAME_001",
        "start_time": "2024-12-25T18:00:00",
        "game_type": "standard",
        "current_turn": 5,
        "current_phase": "main_phase",
        "players": {
            "player_1": {
                "player_id": "P1",
                "deck_info": {
                    "deck_id": "DECK_001",
                    "cards_remaining": 25,
                    "cards_drawn": 8
                },
                "resources": {
                    "health": 25,
                    "mana": {
                        "current": 5,
                        "max": 5,
                        "pending": 0
                    }
                },
                "board_state": {
                    "creatures": [
                        {
                            "card_id": "CARD_001",
                            "name": "烈焰战士",
                            "status": {
                                "attack": 3,
                                "health": 2,
                                "can_attack": true
                            }
                        }
                    ],
                    "enchantments": [
                        {
                            "card_id": "ENCH_001",
                            "name": "力量祝福",
                            "effects": ["creature_buff"]
                        }
                    ]
                }
            }
        }
    }
}
```

## 2. 状态管理系统

### 2.1 状态更新器
```python
class StateUpdater:
    """状态更新管理器"""
    
    def __init__(self, game_context: GameContext):
        self.context = game_context
        self.pending_updates = []
        self.update_history = []
        
    async def apply_action(self, action: GameAction) -> GameContext:
        """应用游戏行动"""
        # 验证行动
        if not self._validate_action(action):
            raise InvalidActionError("无效的行动")
            
        # 创建状态快照
        snapshot = self._create_snapshot()
        
        try:
            # 应用行动
            new_context = await self._process_action(action)
            
            # 处理触发效果
            new_context = await self._process_triggers(new_context)
            
            # 更新历史记录
            self.update_history.append({
                "action": action,
                "old_state": snapshot,
                "new_state": new_context
            })
            
            return new_context
            
        except Exception as e:
            # 回滚到快照
            self.context = snapshot
            raise StateUpdateError(f"状态更新失败: {e}")
```

### 2.2 状态查询器
```python
class StateQuery:
    """状态查询器"""
    
    def __init__(self, game_context: GameContext):
        self.context = game_context
        
    def get_player_state(self, player_id: str) -> Dict:
        """获取玩家状态"""
        player = self.context.players.get(player_id)
        if not player:
            raise PlayerNotFoundError(f"找不到玩家: {player_id}")
            
        return {
            "resources": player.resources.dict(),
            "board": player.board_state.dict(),
            "hand_size": len(player.hand_cards),
            "effects": [e.dict() for e in player.effects]
        }
        
    def get_game_state(self) -> Dict:
        """获取游戏状态"""
        return {
            "turn": self.context.current_turn,
            "phase": self.context.current_phase,
            "active_player": self._get_active_player(),
            "effect_queue": [e.dict() for e in self.context.effect_queue]
        }
```

## 3. 上下文持久化

### 3.1 存储管理器
```python
class ContextStorage:
    """上下文存储管理器"""
    
    async def save_context(self, context: GameContext):
        """保存游戏上下文"""
        context_data = context.dict()
        
        # 添加元数据
        context_data["metadata"] = {
            "save_time": datetime.now(),
            "version": "1.0"
        }
        
        # 保存到数据库
        await self._save_to_db(context_data)
        
    async def load_context(self, game_id: str) -> GameContext:
        """加载游戏上下文"""
        # 从数据库加载
        context_data = await self._load_from_db(game_id)
        
        # 验证数据完整性
        if not self._validate_context_data(context_data):
            raise CorruptedContextError("上下文数据损坏")
            
        return GameContext(**context_data)
```

## 4. 状态同步系统

### 4.1 同步管理器
```python
class StateSynchronizer:
    """状态同步管理器"""
    
    def __init__(self, game_context: GameContext):
        self.context = game_context
        self.subscribers = set()
        
    async def subscribe(self, client_id: str):
        """订阅状态更新"""
        self.subscribers.add(client_id)
        
    async def broadcast_update(self, update: Dict):
        """广播状态更新"""
        for client_id in self.subscribers:
            await self._send_update(client_id, update)
            
    async def sync_client_state(self, client_id: str):
        """同步客户端状态"""
        client_state = self._get_client_state(client_id)
        await self._send_update(client_id, client_state)
```

## 5. 上下文示例场景

### 5.1 回合开始上下文
```json
{
    "turn_start_context": {
        "game_id": "GAME_001",
        "current_turn": 6,
        "phase": "start_phase",
        "active_player": {
            "player_id": "P1",
            "resources": {
                "mana": {
                    "current": 0,
                    "max": 6,
                    "pending": 1
                }
            },
            "start_effects": [
                {
                    "type": "draw_card",
                    "source": "turn_start"
                },
                {
                    "type": "gain_mana",
                    "amount": 1
                }
            ]
        },
        "effect_queue": [
            {
                "type": "phase_start",
                "effects": ["refresh_resources", "draw_card"]
            }
        ]
    }
}
```

### 5.2 战斗阶段上下文
```json
{
    "combat_phase_context": {
        "game_id": "GAME_001",
        "current_turn": 6,
        "phase": "combat_phase",
        "active_player": {
            "player_id": "P1",
            "board_state": {
                "creatures": [
                    {
                        "id": "CARD_001",
                        "can_attack": true,
                        "status": {
                            "attack": 3,
                            "health": 2,
                            "effects": ["first_strike"]
                        }
                    }
                ]
            }
        },
        "opponent": {
            "player_id": "P2",
            "board_state": {
                "creatures": [
                    {
                        "id": "CARD_002",
                        "status": {
                            "attack": 2,
                            "health": 3,
                            "effects": ["taunt"]
                        }
                    }
                ]
            }
        },
        "valid_actions": [
            {
                "type": "attack",
                "source": "CARD_001",
                "valid_targets": ["CARD_002"]
            }
        ]
    }
}
```

## 6. 状态变更示例

### 6.1 出牌状态变更
```json
{
    "play_card_state_change": {
        "action": {
            "type": "play_card",
            "card_id": "SPELL_001",
            "targets": ["CREATURE_001"]
        },
        "state_changes": [
            {
                "type": "resource_change",
                "resource": "mana",
                "change": -3,
                "new_value": 2
            },
            {
                "type": "card_movement",
                "card": "SPELL_001",
                "from": "hand",
                "to": "graveyard"
            },
            {
                "type": "creature_modification",
                "target": "CREATURE_001",
                "changes": {
                    "health": -2,
                    "status": ["damaged"]
                }
            }
        ],
        "triggered_effects": [
            {
                "source": "damage_trigger",
                "effect": "draw_card"
            }
        ]
    }
}
```

### 6.2 回合结束状态变更
```json
{
    "turn_end_state_change": {
        "phase_change": {
            "from": "main_phase",
            "to": "end_phase"
        },
        "state_changes": [
            {
                "type": "effect_resolution",
                "effects": [
                    {
                        "type": "end_of_turn",
                        "source": "continuous_effect",
                        "resolution": "remove_temporary_buffs"
                    }
                ]
            },
            {
                "type": "hand_check",
                "current_size": 8,
                "max_size": 7,
                "resolution": "discard_cards"
            }
        ],
        "next_turn_preparation": {
            "active_player": "P2",
            "phase": "start_phase",
            "pending_effects": []
        }
    }
}
```

## 7. 最佳实践

### 7.1 上下文管理原则
1. 保持状态一致性
2. 使用事务处理
3. 记录状态变化
4. 支持状态回滚

### 7.2 状态更新原则
1. 原子性操作
2. 验证每步更改
3. 维护更新历史
4. 处理异常情况

### 7.3 性能优化建议
1. 使用增量更新
2. 实现状态缓存
3. 异步处理更新
4. 优化存储结构

这个上下文和状态设计提供了：
1. 完整的上下文模型
2. 灵活的状态管理
3. 可靠的持久化机制
4. 高效的同步系统

您觉得这个设计如何？需要我详细解释某些部分吗？
