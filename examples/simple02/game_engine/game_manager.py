from typing import Dict, Optional, Tuple
from models.game_state import GameState, GamePhase, Player, PlayerType
from models.card import Card, CardType
from .llm_manager import LLMManager
import random

class GameManager:
    def __init__(self, llm_manager: LLMManager):
        self.llm_manager = llm_manager
        self.game_state: Optional[GameState] = None
        
    def start_game(self, player_name: str) -> GameState:
        """开始新游戏"""
        # 创建玩家
        human_player = Player(
            id="p1",
            type=PlayerType.HUMAN,
            name=player_name
        )
        ai_player = Player(
            id="p2",
            type=PlayerType.AI,
            name="AI对手"
        )
        
        # 初始化游戏状态
        self.game_state = GameState(
            current_player=human_player,
            opponent=ai_player,
            current_phase=GamePhase.DRAW
        )
        
        # 初始发牌
        self._initial_draw()
        
        return self.game_state
    
    def process_user_action(self, user_input: str) -> Tuple[bool, str]:
        """处理用户输入的动作"""
        if not self.game_state:
            return False, "游戏尚未开始"
            
        # 使用LLM解析用户输入
        action = self.llm_manager.parse_user_action(user_input, self.game_state)
        
        # 验证动作是否合法
        if not self._validate_action(action):
            return False, "非法动作"
            
        # 执行动作
        success, message = self._execute_action(action)
        if success:
            self.game_state.add_log(message)
            
            # 检查游戏是否结束
            if self._check_game_end():
                return True, "游戏结束"
                
            # 如果玩家回合结束，执行AI回合
            if action.get("action_type") == "end_turn":
                self._execute_ai_turn()
                
        return success, message
    
    def _initial_draw(self):
        """初始发牌"""
        # 这里简化处理，实际游戏中需要真实的卡组
        for _ in range(5):
            self.game_state.current_player.hand.append(self._generate_random_card())
            self.game_state.opponent.hand.append(self._generate_random_card())
    
    def _validate_action(self, action: Dict) -> bool:
        """验证动作是否合法"""
        action_type = action.get("action_type")
        if not action_type:
            return False
            
        if action_type == "play_card":
            card_index = action.get("card_index")
            if card_index is None or card_index >= len(self.game_state.current_player.hand):
                return False
                
        elif action_type == "attack":
            if self.game_state.current_phase != GamePhase.BATTLE:
                return False
                
        return True
    
    def _execute_action(self, action: Dict) -> Tuple[bool, str]:
        """执行游戏动作"""
        action_type = action.get("action_type")
        
        if action_type == "play_card":
            return self._play_card(action)
        elif action_type == "attack":
            return self._perform_attack(action)
        elif action_type == "end_turn":
            return self._end_turn()
        elif action_type == "query_info":
            return True, self.llm_manager.generate_state_description(self.game_state)
            
        return False, "未知的动作类型"
    
    def _play_card(self, action: Dict) -> Tuple[bool, str]:
        """打出卡牌"""
        card_index = action.get("card_index")
        if card_index >= len(self.game_state.current_player.hand):
            return False, "无效的卡牌索引"
            
        card = self.game_state.current_player.hand.pop(card_index)
        self.game_state.current_player.field.append(card)
        
        return True, f"玩家打出了 {card.name}"
    
    def _perform_attack(self, action: Dict) -> Tuple[bool, str]:
        """执行攻击"""
        attacker_index = action.get("card_index")
        target_index = action.get("target_index")
        
        if attacker_index >= len(self.game_state.current_player.field):
            return False, "无效的攻击者"
            
        attacker = self.game_state.current_player.field[attacker_index]
        
        # 直接攻击生命值
        if target_index is None:
            damage = attacker.attack or 0
            self.game_state.opponent.life_points -= damage
            return True, f"{attacker.name} 直接攻击，造成 {damage} 点伤害"
            
        # 攻击对方卡牌
        if target_index >= len(self.game_state.opponent.field):
            return False, "无效的目标"
            
        target = self.game_state.opponent.field[target_index]
        damage = (attacker.attack or 0) - (target.defense or 0)
        
        if damage > 0:
            self.game_state.opponent.field.pop(target_index)
            self.game_state.opponent.graveyard.append(target)
            return True, f"{attacker.name} 攻击并消灭了 {target.name}"
        else:
            return True, f"{attacker.name} 攻击 {target.name} 但未能造成伤害"
    
    def _end_turn(self) -> Tuple[bool, str]:
        """结束回合"""
        # 交换当前玩家
        self.game_state.current_player, self.game_state.opponent = (
            self.game_state.opponent,
            self.game_state.current_player
        )
        
        # 重置阶段
        self.game_state.current_phase = GamePhase.DRAW
        self.game_state.turn_count += 1
        
        return True, "回合结束"
    
    def _execute_ai_turn(self):
        """执行AI回合"""
        # 获取AI动作
        ai_action = self.llm_manager.generate_ai_action(self.game_state)
        
        # 执行AI动作
        success, message = self._execute_action(ai_action)
        if success:
            self.game_state.add_log(f"AI: {message}")
    
    def _check_game_end(self) -> bool:
        """检查游戏是否结束"""
        return (self.game_state.current_player.life_points <= 0 or
                self.game_state.opponent.life_points <= 0)
    
    def _generate_random_card(self) -> Card:
        """生成随机卡牌（示例）"""
        card_types = list(CardType)
        return Card(
            id=f"card_{random.randint(1000, 9999)}",
            name=f"随机卡牌 #{random.randint(1, 100)}",
            type=random.choice(card_types),
            description="这是一张随机生成的卡牌",
            cost=random.randint(1, 5),
            attack=random.randint(100, 1000) if random.random() > 0.5 else None,
            defense=random.randint(100, 1000) if random.random() > 0.5 else None
        )
