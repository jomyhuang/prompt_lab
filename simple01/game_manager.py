import json
import os
import random

class GameManager:
    def __init__(self):
        self.game_state = {
            "player_stats": {
                "hp": 100,
                "energy": 3,
                "armor": 0
            },
            "turn_info": {
                "current_turn": 1,
                "phase": "player_turn"
            },
            "field_cards": [],
            "hand_cards": [],  
            "log": []
        }
        self.load_cards()
        self.init_hand_cards()  

    def load_cards(self):
        """加载卡牌数据"""
        try:
            cards_path = os.path.join(os.path.dirname(__file__), 'cards.json')
            with open(cards_path, 'r', encoding='utf-8') as f:
                self.available_cards = json.load(f)
        except Exception as e:
            print(f"加载卡牌数据出错: {e}")
            self.available_cards = []

    def init_hand_cards(self):
        """初始化手牌"""
        self.game_state["hand_cards"] = self.available_cards.copy()

    def get_available_cards(self):
        """获取手牌列表"""
        return self.game_state["hand_cards"]

    def get_field_cards(self):
        """获取场上的卡牌列表"""
        return self.game_state.get('field_cards', [])

    def play_card(self, card_name):
        """使用卡牌"""
        # 检查能量是否足够
        cost = next((c.get('mana_cost', 0) for c in self.game_state["hand_cards"] if c['name'] == card_name), 0)
        if self.game_state['player_stats']['energy'] < cost:
            return f"能量不足: 需要{cost}点能量"

        # 从手牌中查找卡牌
        card = next((c for c in self.game_state["hand_cards"] if c['name'] == card_name), None)
        if not card:
            return f"找不到卡牌: {card_name}"

        # 扣除能量
        self.game_state['player_stats']['energy'] -= cost

        # 从手牌中移除
        self.game_state["hand_cards"].remove(card)
        print("移除手牌:", card_name)

        # 创建场上卡牌对象
        field_card = {
            'name': card['name'],
            'effect': card.get('effect', ''),
            'status': 'active',
            'type': card.get('type', ''),
            'description': card.get('description', '')
        }

        # 添加到场上
        self.game_state['field_cards'].append(field_card)
        print("添加到场上:", card_name)

        # 显示当前场上卡牌
        field_card_names = [card['name'] for card in self.game_state['field_cards']]
        print("当前场上卡牌:", ", ".join(field_card_names))

        # 处理卡牌效果
        effect_result = self._process_card_effects(card)

        # 返回成功状态和效果
        return {"status": "success", "message": effect_result}

    def _process_card_effects(self, card):
        """处理卡牌效果"""
        effects = card.get('effects', [])
        results = []
        
        for effect in effects:
            effect_type = effect.get('type')
            if effect_type == '伤害':
                damage = effect.get('damage', 0)
                self.game_state['log'].append(f"造成{damage}点伤害")
                results.append(f"造成{damage}点伤害")
            elif effect_type == '治疗':
                heal = effect.get('heal', 0)
                self.game_state['player_stats']['hp'] = min(
                    100, 
                    self.game_state['player_stats']['hp'] + heal
                )
                self.game_state['log'].append(f"恢复{heal}点生命值")
                results.append(f"恢复{heal}点生命值")
            elif effect_type == '吸血':
                damage = card.get('attack', 0) // 2
                self.game_state['player_stats']['hp'] = min(
                    100, 
                    self.game_state['player_stats']['hp'] + damage
                )
                self.game_state['log'].append(f"吸血{damage}点")
                results.append(f"吸血{damage}点")
            elif effect_type == '反伤':
                self.game_state['player_stats']['armor'] += effect.get('damage', 0)
                self.game_state['log'].append(f"获得{effect.get('damage', 0)}点护甲")
                results.append(f"获得{effect.get('damage', 0)}点护甲")

        return ", ".join(results)

    def get_game_state(self):
        """获取完整的游戏状态"""
        return {
            "player_stats": {
                "hp": self.game_state['player_stats']['hp'],
                "energy": self.game_state['player_stats']['energy'],
                "armor": self.game_state['player_stats']['armor']
            },
            "turn_info": {
                "current_turn": self.game_state['turn_info']['current_turn'],
                "phase": self.game_state['turn_info']['phase']
            },
            "field_cards": self.game_state['field_cards'],
            "hand_cards": self.game_state['hand_cards'],
            "log": self.game_state['log']
        }

    def update_game_state(self, action_result):
        """更新游戏状态"""
        if isinstance(action_result, dict):
            # 如果是卡牌使用动作
            if action_result.get('action') == 'play_card':
                card_name = action_result.get('parameters', {}).get('card_name')
                if card_name:
                    result = self.play_card(card_name)
                    self.game_state['log'].append(result)
        
        # 回合结束时恢复能量
        if self.game_state['turn_info']['phase'] == 'end_turn':
            self.game_state['player_stats']['energy'] = min(
                10, 
                self.game_state['player_stats']['energy'] + 2
            )
            self.game_state['turn_info']['current_turn'] += 1
            self.game_state['turn_info']['phase'] = 'player_turn'
        
        return self.game_state
