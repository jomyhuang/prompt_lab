# 游戏状态管理系统设计

## 1. 状态管理架构

### 1.1 状态管理器核心设计
```python
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

class GameState(BaseModel):
    """游戏状态数据模型"""
    version: str
    timestamp: datetime
    turn_number: int
    current_player: str
    phase: str
    player_state: Dict
    opponent_state: Dict
    field_state: Dict
    effect_queue: List[Dict]
    action_history: List[Dict]

class StateManager:
    """状态管理器"""
    
    def __init__(self):
        self.state_history: List[GameState] = []
        self.current_state: Optional[GameState] = None
        self.state_locks: Dict[str, bool] = {}
        self.pending_updates: List[Dict] = []
        
    async def update_state(self, update: Dict[str, Any]) -> GameState:
        """更新状态"""
        # 1. 验证更新
        if not self._validate_update(update):
            raise InvalidStateUpdateError("无效的状态更新")
            
        # 2. 创建新状态
        new_state = self._create_new_state(update)
        
        # 3. 保存历史
        self.state_history.append(self.current_state)
        
        # 4. 更新当前状态
        self.current_state = new_state
        
        # 5. 广播状态更新
        await self._broadcast_state_update(new_state)
        
        return new_state
    
    def rollback_state(self) -> GameState:
        """回滚到上一个状态"""
        if not self.state_history:
            raise NoHistoryError("没有可回滚的历史状态")
            
        self.current_state = self.state_history.pop()
        return self.current_state
```

### 1.2 状态验证器
```python
class StateValidator:
    """状态验证器"""
    
    def validate_state(self, state: GameState) -> bool:
        """验证状态的完整性和一致性"""
        try:
            # 1. 基础验证
            if not self._validate_basic_fields(state):
                return False
                
            # 2. 资源验证
            if not self._validate_resources(state):
                return False
                
            # 3. 游戏规则验证
            if not self._validate_game_rules(state):
                return False
                
            # 4. 效果队列验证
            if not self._validate_effect_queue(state):
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"状态验证失败: {e}")
            return False
```

## 2. 状态更新工具

### 2.1 状态更新工具类
```python
class StateUpdateTool:
    """状态更新工具"""
    
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        
    async def apply_card_play(self, card_id: str, target_id: Optional[str] = None) -> GameState:
        """应用出牌更新"""
        update = {
            "type": "card_play",
            "card_id": card_id,
            "target_id": target_id,
            "timestamp": datetime.now()
        }
        
        return await self.state_manager.update_state(update)
        
    async def apply_effect(self, effect: Dict) -> GameState:
        """应用效果更新"""
        update = {
            "type": "effect",
            "effect": effect,
            "timestamp": datetime.now()
        }
        
        return await self.state_manager.update_state(update)
```

### 2.2 状态同步工具
```python
class StateSyncTool:
    """状态同步工具"""
    
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.sync_queue = asyncio.Queue()
        
    async def sync_with_gui(self):
        """与GUI同步状态"""
        current_state = self.state_manager.current_state
        
        # 1. 更新游戏板面
        st.session_state.game_state = current_state.dict()
        
        # 2. 更新显示
        await self._update_display()
        
        # 3. 处理动画
        await self._process_animations()
        
    async def sync_with_chain(self, chain_result: Dict):
        """与Chain系统同步状态"""
        # 1. 提取状态更新
        state_updates = self._extract_state_updates(chain_result)
        
        # 2. 应用更新
        for update in state_updates:
            await self.state_manager.update_state(update)
```

## 3. 状态监控系统

### 3.1 状态监控器
```python
class StateMonitor:
    """状态监控器"""
    
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.alerts = []
        
    async def monitor_state_changes(self):
        """监控状态变化"""
        while True:
            # 1. 检查状态完整性
            if not await self._check_state_integrity():
                self._raise_alert("状态完整性检查失败")
                
            # 2. 检查状态一致性
            if not await self._check_state_consistency():
                self._raise_alert("状态一致性检查失败")
                
            # 3. 检查性能指标
            await self._check_performance_metrics()
            
            await asyncio.sleep(1)
```

### 3.2 状态恢复系统
```python
class StateRecoverySystem:
    """状态恢复系统"""
    
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        
    async def handle_error(self, error: Exception):
        """处理错误"""
        try:
            # 1. 记录错误
            logger.error(f"状态错误: {error}")
            
            # 2. 尝试回滚
            await self._attempt_rollback()
            
            # 3. 如果回滚失败，尝试状态重建
            if not self.state_manager.current_state:
                await self._rebuild_state()
                
        except Exception as e:
            logger.critical(f"状态恢复失败: {e}")
            raise StateRecoveryError("无法恢复状态")
```

## 4. 使用示例

### 4.1 在Chain中使用状态管理
```python
class GameChain(Chain):
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.state_update_tool = StateUpdateTool(state_manager)
        
    async def _call(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # 1. 获取当前状态
            current_state = self.state_manager.current_state
            
            # 2. 执行Chain逻辑
            result = await self._execute_chain_logic(inputs)
            
            # 3. 更新状态
            new_state = await self.state_update_tool.apply_chain_result(result)
            
            # 4. 同步GUI
            await self.state_manager.sync_with_gui()
            
            return {
                "result": result,
                "new_state": new_state
            }
            
        except Exception as e:
            # 错误处理
            await self.state_manager.handle_error(e)
            raise
```

### 4.2 在GUI中使用状态管理
```python
class GUIController:
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.sync_tool = StateSyncTool(state_manager)
        
    async def handle_user_action(self, action: Dict):
        """处理用户行动"""
        try:
            # 1. 验证行动
            if not self._validate_action(action):
                raise InvalidActionError("无效的用户行动")
                
            # 2. 更新状态
            new_state = await self.state_manager.update_state({
                "type": "user_action",
                "action": action
            })
            
            # 3. 同步显示
            await self.sync_tool.sync_with_gui()
            
        except Exception as e:
            # 错误处理
            await self.state_manager.handle_error(e)
            st.error(f"操作失败: {e}")
```

## 5. 状态一致性保证

### 5.1 状态锁定机制
```python
class StateLock:
    """状态锁定机制"""
    
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.locks = {}
        
    async def acquire_lock(self, component: str) -> bool:
        """获取状态锁"""
        if self.locks.get(component):
            return False
            
        self.locks[component] = True
        return True
        
    async def release_lock(self, component: str):
        """释放状态锁"""
        self.locks[component] = False
```

### 5.2 状态事务
```python
class StateTransaction:
    """状态事务"""
    
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.changes = []
        
    async def begin_transaction(self):
        """开始事务"""
        self.snapshot = copy.deepcopy(self.state_manager.current_state)
        
    async def commit_transaction(self):
        """提交事务"""
        try:
            # 应用所有更改
            for change in self.changes:
                await self.state_manager.update_state(change)
                
            self.changes = []
            
        except Exception as e:
            # 回滚
            await self.rollback_transaction()
            raise
            
    async def rollback_transaction(self):
        """回滚事务"""
        self.state_manager.current_state = self.snapshot
        self.changes = []
```

## 6. 最佳实践

### 6.1 状态更新原则
1. 所有状态更新必须通过StateManager进行
2. 使用事务处理复杂的状态更新
3. 保持状态更新的原子性
4. 实现状态回滚机制

### 6.2 状态验证原则
1. 每次更新前后都进行状态验证
2. 使用类型检查确保数据格式正确
3. 实现业务规则验证
4. 保持错误处理的完整性

### 6.3 性能优化
1. 使用状态缓存
2. 批量处理状态更新
3. 异步处理非关键更新
4. 优化状态同步机制

这个状态管理系统提供了：
1. 完整的状态管理机制
2. 可靠的状态验证
3. 强大的错误恢复
4. 灵活的工具支持
5. 清晰的使用示例

您觉得这个状态管理设计如何？需要我详细解释某些部分吗？
