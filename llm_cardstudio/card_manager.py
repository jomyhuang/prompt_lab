import json
import os
import random
class CardManager:
    def __init__(self, card_data_file="cards.json"):
        self.all_cards = self._load_cards(card_data_file) # 加载所有卡牌
        self.cards = [] # 当前用户的手牌
    def _load_cards(self, card_data_file):
        # 加载预设的卡牌数据
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(dir_path, card_data_file)
        try:
           with open(file_path, 'r', encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
             return {}
    def draw_cards(self, num_cards):
        """
        从牌库中抽取指定数量的卡牌
        """
        if not self.all_cards:
            return

        if len(self.all_cards) < num_cards:
          selected_cards = random.sample(self.all_cards,len(self.all_cards)) #如果总卡牌数量 小于要抽取卡牌数量，则抽取所有的卡牌
        else:
           selected_cards = random.sample(self.all_cards, num_cards)

        self.cards.extend(selected_cards)