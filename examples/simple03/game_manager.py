"""
游戏状态管理模块
"""
class GameManager:
    def __init__(self):
        self.player_hp = 30
        self.ai_hp = 30
        self.current_turn = 'player'
        self.game_log = []
    
    def update_hp(self, target: str, amount: int):
        """更新生命值"""
        if target == 'player':
            self.player_hp += amount
        else:
            self.ai_hp += amount
        
        self.check_game_over()
    
    def check_game_over(self) -> bool:
        """检查游戏是否结束"""
        if self.player_hp <= 0:
            self.game_log.append("游戏结束：AI获胜")
            return True
        elif self.ai_hp <= 0:
            self.game_log.append("游戏结束：玩家获胜")
            return True
        return False
    
    def switch_turn(self):
        """切换回合"""
        self.current_turn = 'ai' if self.current_turn == 'player' else 'player'
        self.game_log.append(f"现在是 {self.current_turn} 的回合")
