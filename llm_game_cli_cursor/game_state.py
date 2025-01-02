from typing import TypedDict, Annotated, List, Literal, Optional
from dataclasses import dataclass
from datetime import datetime
# import logging
import uuid

# # 配置日志
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

class GameState(TypedDict):
    """游戏状态类型定义
    
    专注于LangGraph图节点状态:
    - 游戏进度状态
    - 对话历史
    - 动作历史
    - 会话上下文
    """
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

class GameStateManager:
    """游戏状态管理器
    
    专注于LangGraph图节点状态管理:
    - 状态验证
    - 状态更新
    - 动作历史记录
    """
    def __init__(self):
        # self.logger = logging.getLogger(__name__)
        self.game_state = self.init_game_state()
    
    def validate_state(self, state: GameState) -> bool:
        """验证游戏状态的有效性"""
        try:
            if not isinstance(state["current_turn"], str):
                raise ValueError("current_turn must be string")
            if not isinstance(state["valid_actions"], list):
                raise ValueError("valid_actions must be list") 
            return True
        except Exception as e:
            self.logger.error(f"State validation failed: {str(e)}")
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
    #         self.logger.error(f"State update failed: {str(e)}")
    #         raise

    def init_game_state(self) -> GameState:
        """初始化游戏状态"""
        return GameState(
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

    def get_valid_actions(self, state: GameState) -> List[str]:
        """获取当前可用的动作列表"""
        return state["valid_actions"]

    # def add_message(self, state: GameState, role: str, content: str) -> GameState:
    #     """添加消息到历史记录"""
    #     new_state = state.copy()
    #     new_state["messages"].append({
    #         "role": role,
    #         "content": content,
    #         "timestamp": datetime.now().isoformat()
    #     })
    #     self.game_state = new_state
    #     return new_state

    def get_game_state(self) -> GameState:
        """获取当前游戏状态"""
        return self.game_state

    # def set_game_state(self, state: GameState):
    #     """设置当前游戏状态"""
    #     if self.validate_state(state):
    #         self.game_state = state 