from typing import TypedDict, List, Literal, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import logging
import uuid

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GameState(TypedDict):
    """游戏状态类型定义
    
    Attributes:
        session_id: 会话ID
        current_turn: 当前回合
        messages: 对话消息历史
        game_over: 游戏是否结束
        last_action: 最后执行的动作
        game_data: 游戏相关数据
        player_data: 玩家相关数据
        ui_state: UI状态
    """
    session_id: str
    current_turn: Literal["player", "system"]
    messages: List[Dict[str, str]]
    game_over: bool
    last_action: Optional[str]
    game_data: Dict[str, Any]
    player_data: Dict[str, Any]
    ui_state: Dict[str, Any]

@dataclass
class GameAction:
    """游戏动作数据类
    
    Attributes:
        action_type: 动作类型
        action_data: 动作数据
        timestamp: 时间戳
    """
    action_type: str
    action_data: Dict[str, Any]
    timestamp: datetime = datetime.now()

class GameStateManager:
    """游戏状态管理器
    
    处理游戏状态的初始化、更新和持久化
    """
    def __init__(self):
        self.state: GameState = self.init_state()
        
    def init_state(self) -> GameState:
        """初始化游戏状态"""
        return GameState(
            session_id=str(uuid.uuid4()),
            current_turn="system",
            messages=[],
            game_over=False,
            last_action=None,
            game_data={},
            player_data={},
            ui_state={"require_update": False}
        )
    
    def update_state(self, action: GameAction) -> GameState:
        """更新游戏状态
        
        Args:
            action: 游戏动作
            
        Returns:
            更新后的游戏状态
        """
        logger.info(f"Updating state with action: {action}")
        
        # 根据动作类型更新状态
        if action.action_type == "message":
            self.state["messages"].append(action.action_data)
        elif action.action_type == "game_action":
            self.state["last_action"] = action.action_data.get("action")
            self.state["game_data"].update(action.action_data)
        elif action.action_type == "player_action":
            self.state["player_data"].update(action.action_data)
        
        # 切换回合
        self.state["current_turn"] = "player" if self.state["current_turn"] == "system" else "system"
        
        # 标记UI需要更新
        self.state["ui_state"]["require_update"] = True
        
        return self.state
    
    def get_state(self) -> GameState:
        """获取当前游戏状态"""
        return self.state
    
    def save_state(self, filepath: str) -> bool:
        """保存游戏状态到文件
        
        Args:
            filepath: 保存路径
            
        Returns:
            是否保存成功
        """
        try:
            # 实现状态保存逻辑
            return True
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            return False
    
    def load_state(self, filepath: str) -> bool:
        """从文件加载游戏状态
        
        Args:
            filepath: 加载路径
            
        Returns:
            是否加载成功
        """
        try:
            # 实现状态加载逻辑
            return True
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return False
