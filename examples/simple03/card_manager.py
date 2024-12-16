"""
卡牌管理模块
"""
import json
import random

class CardManager:
    def __init__(self):
        self.deck = self._load_cards()
        self.player_hand = []
        self.ai_hand = []
        self.draw_initial_hands()
    
    def _load_cards(self):
        """从JSON文件加载卡牌数据"""
        try:
            with open('cards.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载卡牌失败: {e}")
            return []
    
    def draw_card(self, target: str):
        """抽取卡牌"""
        if not self.deck:
            return None
        
        card = random.choice(self.deck)
        if target == 'player':
            self.player_hand.append(card)
        else:
            self.ai_hand.append(card)
        return card
    
    def draw_initial_hands(self):
        """初始抽牌"""
        for _ in range(3):
            self.draw_card('player')
            self.draw_card('ai')
    
    def play_card(self, card_name: str, target: str) -> dict:
        """使用卡牌"""
        hand = self.player_hand if target == 'player' else self.ai_hand
        for card in hand:
            if card['name'] == card_name:
                hand.remove(card)
                return card
        return None
