# GUI与Chain系统结合框架设计

## 1. 整体架构

### 1.1 系统架构图
```
[Streamlit GUI]
      ↓ ↑
[GUI Controller]
      ↓ ↑
[Chain Coordinator]
      ↓ ↑
[Agent System]
```

### 1.2 主要组件
```python
class GUIController:
    """GUI控制器，负责GUI与Chain系统的交互"""
    
    def __init__(self):
        self.chain_coordinator = ChainCoordinator()
        self.state_manager = StateManager()
        self.event_queue = asyncio.Queue()
        
    def initialize(self):
        """初始化GUI状态"""
        st.session_state.game_state = self.state_manager.get_initial_state()
        st.session_state.message_history = []
        st.session_state.effect_queue = []
```

## 2. GUI实现

### 2.1 主界面设计
```python
def render_main_interface():
    """渲染主界面"""
    st.title("卡牌游戏")
    
    # 分栏布局
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 游戏主区域
        render_game_board()
        
    with col2:
        # 对话和控制区域
        render_control_panel()

def render_game_board():
    """渲染游戏板面"""
    # 对手区域
    render_opponent_area()
    
    # 场地区域
    render_field_area()
    
    # 玩家区域
    render_player_area()
    
    # 手牌区域
    render_hand_cards()

def render_control_panel():
    """渲染控制面板"""
    # 对话历史
    st.markdown("### 对话历史")
    for msg in st.session_state.message_history:
        st.markdown(msg)
    
    # 输入区域
    user_input = st.text_input("输入指令")
    if user_input:
        process_user_input(user_input)
```

### 2.2 事件处理
```python
class GUIEventHandler:
    """GUI事件处理器"""
    
    def __init__(self, controller: GUIController):
        self.controller = controller
    
    async def handle_card_click(self, card_id: str):
        """处理卡牌点击"""
        if not st.session_state.selected_card:
            # 选择卡牌
            st.session_state.selected_card = card_id
            highlight_valid_targets(card_id)
        else:
            # 执行卡牌使用
            await self.controller.play_card(
                st.session_state.selected_card,
                card_id
            )
            st.session_state.selected_card = None
    
    async def handle_end_turn(self):
        """处理回合结束"""
        await self.controller.end_turn()
    
    def highlight_valid_targets(self, card_id: str):
        """高亮显示有效目标"""
        valid_targets = self.controller.get_valid_targets(card_id)
        st.session_state.valid_targets = valid_targets
```

## 3. Chain系统集成

### 3.1 Chain协调器
```python
class ChainCoordinator:
    """Chain系统协调器"""
    
    def __init__(self):
        self.game_master = GameMasterAgent()
        self.strategy = StrategyAgent()
        self.narrator = NarratorAgent()
        
        # 初始化各个Chain
        self.player_action_chain = PlayerActionChain(
            self.game_master,
            self.strategy,
            self.narrator
        )
        self.opponent_action_chain = OpponentActionChain(
            self.game_master,
            self.strategy,
            self.narrator
        )
        
    async def process_user_input(self, input_text: str) -> dict:
        """处理用户输入"""
        # 1. 解析用户意图
        intent = await self.game_master.parse_intent(input_text)
        
        # 2. 根据意图选择相应的Chain
        if intent["type"] == "play_card":
            result = await self.player_action_chain.run({
                "type": "play_card",
                "card_id": intent["card_id"],
                "target_id": intent.get("target_id")
            })
        elif intent["type"] == "end_turn":
            result = await self.process_turn_end()
            
        # 3. 更新GUI状态
        await self.update_gui_state(result)
        
        return result
```

### 3.2 状态管理器
```python
class StateManager:
    """状态管理器"""
    
    def __init__(self):
        self.state_history = []
        
    def get_current_state(self) -> dict:
        """获取当前状态"""
        return st.session_state.game_state
    
    def update_state(self, new_state: dict):
        """更新状态"""
        # 保存历史
        self.state_history.append(
            copy.deepcopy(st.session_state.game_state)
        )
        
        # 更新当前状态
        st.session_state.game_state = new_state
        
    def rollback_state(self):
        """回滚状态"""
        if self.state_history:
            st.session_state.game_state = self.state_history.pop()
```

## 4. 效果展示系统

### 4.1 效果渲染器
```python
class EffectRenderer:
    """效果渲染器"""
    
    def __init__(self):
        self.effect_queue = []
        
    async def add_effect(self, effect: dict):
        """添加效果到队列"""
        self.effect_queue.append(effect)
        
    async def render_effects(self):
        """渲染效果"""
        while self.effect_queue:
            effect = self.effect_queue.pop(0)
            
            # 根据效果类型选择渲染方式
            if effect["type"] == "damage":
                await self._render_damage(effect)
            elif effect["type"] == "heal":
                await self._render_heal(effect)
            elif effect["type"] == "card_play":
                await self._render_card_play(effect)
                
            # 等待动画完成
            await asyncio.sleep(0.5)
    
    async def _render_damage(self, effect: dict):
        """渲染伤害效果"""
        target_id = effect["target_id"]
        damage = effect["value"]
        
        # 创建伤害动画
        st.session_state.animations.append({
            "type": "damage",
            "target": target_id,
            "value": damage
        })
```

### 4.2 动画管理器
```python
class AnimationManager:
    """动画管理器"""
    
    def __init__(self):
        self.current_animations = []
        
    def add_animation(self, animation: dict):
        """添加动画"""
        self.current_animations.append(animation)
        
    def update_animations(self):
        """更新动画状态"""
        completed = []
        
        for anim in self.current_animations:
            anim["progress"] += 0.1
            if anim["progress"] >= 1:
                completed.append(anim)
                
        # 移除完成的动画
        for anim in completed:
            self.current_animations.remove(anim)
```

## 5. 使用示例

### 5.1 初始化
```python
def main():
    # 初始化控制器
    controller = GUIController()
    controller.initialize()
    
    # 渲染主界面
    render_main_interface()
    
    # 启动事件循环
    asyncio.run(event_loop())

async def event_loop():
    """事件循环"""
    while True:
        # 处理事件队列
        while not controller.event_queue.empty():
            event = await controller.event_queue.get()
            await process_event(event)
            
        # 更新动画
        controller.animation_manager.update_animations()
        
        # 重新渲染
        st.experimental_rerun()
        
        await asyncio.sleep(0.1)
```

### 5.2 用户交互示例
```python
async def process_user_interaction():
    """处理用户交互示例"""
    # 1. 用户点击手牌
    card_id = "card_1"
    await event_handler.handle_card_click(card_id)
    
    # 2. 显示可选目标
    valid_targets = controller.get_valid_targets(card_id)
    highlight_valid_targets(valid_targets)
    
    # 3. 用户选择目标
    target_id = "opponent_card_1"
    await event_handler.handle_card_click(target_id)
    
    # 4. 执行行动并展示效果
    result = await controller.chain_coordinator.process_user_input({
        "type": "play_card",
        "card_id": card_id,
        "target_id": target_id
    })
    
    # 5. 渲染效果
    await controller.effect_renderer.render_effects(result["effects"])
```

## 6. 关键设计点

### 6.1 状态同步
- 使用StreamLit的session_state管理状态
- Chain系统的状态更新通过StateManager同步到GUI
- 支持状态回滚机制

### 6.2 事件处理
- 异步事件队列处理用户输入
- Chain系统的执行结果通过事件传递给GUI
- 效果和动画的异步渲染

### 6.3 错误处理
- GUI层面的输入验证
- Chain系统的执行错误处理
- 状态回滚机制

### 6.4 性能优化
- 异步处理用户输入
- 批量处理效果更新
- 动画系统的性能优化

这个框架设计实现了：
1. GUI与Chain系统的松耦合
2. 清晰的状态管理机制
3. 流畅的效果展示系统
4. 完整的错误处理机制
