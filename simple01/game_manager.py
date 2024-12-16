import json
import os
import random
import time
import streamlit as st
from debug_utils import debug_utils

class GameManager:
    def __init__(self):
        """初始化游戏管理器"""
        self.load_cards()
        self.selected_decks = None
        self._initialize_game_state()

    def _initialize_game_state(self):
        """初始化游戏状态"""
        # 初始化游戏状态
        self.game_state = {
            "gameloop_state": "welcome",  # 游戏主循环状态
            "player_stats": {
                "hp": 100,
                "energy": 3,
                "armor": 0
            },
            "opponent_stats": {
                "hp": 100,
                "energy": 3,
                "armor": 0
            },
            "turn_info": {
                "current_turn": 0,
                "active_player": None
            },
            "field_cards": {
                "player": [],    # 我方场上的卡牌
                "opponent": []   # 对手场上的卡牌
            },
            "hand_cards": {
                "player": [],    # 我方手牌
                "opponent": []   # 对手手牌
            },
            "log": []
        }
        
        # 初始化卡组状态
        self.deck_state = {
            "player": {
                "deck": [],
                "draw_history": [],
                "discard_pile": []
            },
            "opponent": {
                "deck": [],
                "draw_history": [],
                "discard_pile": []
            }
        }

    def load_cards(self):
        """加载卡牌数据"""
        try:
            cards_path = os.path.join(os.path.dirname(__file__), 'cards.json')
            with open(cards_path, 'r', encoding='utf-8') as f:
                self.available_cards = json.load(f)
            debug_utils.log("game", "加载卡牌数据成功", {
                "卡牌数量": len(self.available_cards),
                "卡牌列表": [card["name"] for card in self.available_cards]
            })
        except Exception as e:
            debug_utils.log("game", "加载卡牌数据出错", {"错误": str(e)})
            self.available_cards = []

    def get_available_cards(self):
        """获取手牌列表"""
        return self.game_state["hand_cards"]["player"]

    def get_field_cards(self):
        """获取场上的卡牌列表"""
        return self.game_state.get('field_cards', {})

    def play_card(self, card_name):
        """使用卡牌"""
        # 获取卡牌信息
        card = next((card for card in self.game_state["hand_cards"]["player"] if card["name"] == card_name), None)
        if not card:
            self.add_game_message("❌ 找不到指定的卡牌")
            return False
            
        # 检查能量是否足够
        card_cost = card.get("cost", 0)
        current_energy = self.game_state["player_stats"]["energy"]
        if current_energy < card_cost:
            self.add_game_message(f"⚡ 能量不足: 需要{card_cost}点能量，当前能量: {current_energy}")
            return False
            
        # 扣除能量
        self.game_state["player_stats"]["energy"] -= card_cost
        
        # 从手牌移除并放到场上
        self.game_state["hand_cards"]["player"].remove(card)
        self.game_state["field_cards"]["player"].append(card)
        
        # 处理卡牌效果
        self._process_card_effects(card)
        
        # 记录使用卡牌的消息
        card_message = [
            f"✨ 使用卡牌 **{card['name']}**",
            f"  - 类型: {card['type']}",
            f"  - 费用: {card_cost}",
            f"  - 攻击: {card.get('attack', 0)}",
            f"  - 生命: {card.get('health', 0)}",
            f"  - 效果: {card.get('effect', '无')}",
            f"  - 剩余能量: {self.game_state['player_stats']['energy']}"
        ]
        self.add_game_message("\n".join(card_message))
        
        debug_utils.log("game", "使用卡牌", {
            "卡牌": card,
            "剩余能量": self.game_state["player_stats"]["energy"]
        })
        
        return True

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
            **self.game_state,
            "deck_state": self.deck_state
        }

    def get_deck_state(self):
        """获取卡组状态"""
        return self.deck_state

    def draw_card(self, player_type: str):
        """从卡组抽取一张卡
        
        Args:
            player_type: 玩家类型 ("player" 或 "opponent")
        """
        if not self.deck_state[player_type]["deck"]:
            return None
            
        card = self.deck_state[player_type]["deck"].pop()
        self.deck_state[player_type]["draw_history"].append(card)
        self.game_state["hand_cards"][player_type].append(card)
        return card
    
    def discard_card(self, player_type: str, card):
        """将卡牌放入弃牌堆
        
        Args:
            player_type: 玩家类型 ("player" 或 "opponent")
            card: 要丢弃的卡牌
        """
        if card in self.game_state["hand_cards"][player_type]:
            self.game_state["hand_cards"][player_type].remove(card)
            self.deck_state[player_type]["discard_pile"].append(card)

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

    def add_game_message(self, message):
        """添加游戏消息到聊天记录"""
        if "messages" in st.session_state:
            st.session_state.messages.append({
                "role": "assistant",
                "content": message
            })

    def _player_phase_transition(self, duration=0.5):
        """模拟玩家回合阶段切换的过渡效果"""
        time.sleep(duration)

    def _process_gameloop_state(self):
        """处理游戏主循环状态"""
        gameloop_state = self.game_state.get("gameloop_state", "welcome")
        
        if gameloop_state == "welcome":
            # 等待玩家按下开始游戏按钮
            return False
            
        elif gameloop_state == "start_game":
            # 游戏开始初始化
            self._process_game_start()
            self.game_state["gameloop_state"] = "deal_cards"
            st.rerun()
            return True
            
        elif gameloop_state == "deal_cards":
            # 发牌阶段
            self._process_deal_cards()
            self.game_state["gameloop_state"] = "determine_first"
            st.rerun()
            return True
            
        elif gameloop_state == "determine_first":
            # 决定首轮玩家
            self._process_determine_first()
            self.game_state["gameloop_state"] = "new_turn"
            st.rerun()
            return True
            
        elif gameloop_state == "new_turn":
            # 新回合开始
            self._process_new_turn()
            if self.game_state["turn_info"]["active_player"] == "player":
                self.game_state["gameloop_state"] = "player_turn"
            else:
                self.game_state["gameloop_state"] = "opponent_turn"
            st.rerun()
            return True
            
        elif gameloop_state == "player_turn":
            # 玩家回合
            if self._process_player_turn():
                self.game_state["gameloop_state"] = "next_turn"
                
            st.rerun()
            return True
            
        elif gameloop_state == "opponent_turn":
            # 对手回合
            if self._process_opponent_turn():
                self.game_state["gameloop_state"] = "next_turn"
            st.rerun()
            return True
            
        elif gameloop_state == "next_turn":
            # 进入下一回合
            self._process_next_turn()
            self.game_state["gameloop_state"] = "new_turn"
            st.rerun()
            return True
            
        elif gameloop_state == "end_game":
            # 游戏结束
            self._process_end_game()
            self.game_state["gameloop_state"] = "welcome"
            st.rerun()
            return True
            
        return False

    def _process_game_start(self):
        """处理游戏开始阶段"""
        self._player_phase_transition(1.0)
        self.add_game_message("🎮 **游戏初始化...**")
        debug_utils.log("game", "游戏初始化")
        
        # 重新初始化游戏状态
        self._initialize_game_state()
        
        # 如果有选择的卡组，初始化玩家和对手的卡组
        if self.selected_decks:
            # 获取完整的卡牌信息
            player_cards = []
            opponent_cards = []
            
            # 将卡牌ID转换为完整的卡牌信息
            for card_id in self.selected_decks["player"]:
                card = next((c for c in self.available_cards if c["id"] == card_id), None)
                if card:
                    player_cards.append(card.copy())
                    
            for card_id in self.selected_decks["opponent"]:
                card = next((c for c in self.available_cards if c["id"] == card_id), None)
                if card:
                    opponent_cards.append(card.copy())
            
            # 随机打乱卡组
            random.shuffle(player_cards)
            random.shuffle(opponent_cards)
            
            # 设置卡组
            self.deck_state["player"]["deck"] = player_cards
            self.deck_state["opponent"]["deck"] = opponent_cards
            
            debug_utils.log("game", "卡组初始化", {
                "玩家卡组数量": len(player_cards),
                "对手卡组数量": len(opponent_cards)
            })
        else:
            debug_utils.log("game", "警告：没有选择卡组")

    def _process_deal_cards(self):
        """处理发牌阶段"""
        self._player_phase_transition(1.0)
        self.add_game_message("🎴 **发放初始手牌...**")
        debug_utils.log("game", "发放初始手牌")
        
        # 双方各抽3张牌
        for _ in range(3):
            self.draw_card("player")
            self.draw_card("opponent")

    def _process_determine_first(self):
        """决定首轮玩家"""
        self._player_phase_transition(1.0)
        # 暂时默认玩家先手
        first_player = "player"
        self.add_game_message(f"🎲 **{'你' if first_player == 'player' else '对手'}先手**")
        debug_utils.log("game", "决定先手", {"先手玩家": first_player})
        
        # 设置先手玩家
        self.game_state["turn_info"]["active_player"] = first_player

    def _process_new_turn(self):
        """处理新回合"""
        self._player_phase_transition(0.5)
        self.game_state["turn_info"]["current_turn"] += 1
        active_player = self.game_state["turn_info"]["active_player"]
        
        # 重置能量
        max_energy = min(10, self.game_state["turn_info"]["current_turn"])
        self.game_state[f"{active_player}_stats"]["energy"] = max_energy
        
        self.add_game_message(
            f"🎯 **第{self.game_state['turn_info']['current_turn']}回合 - {'你的' if active_player == 'player' else '对手'}回合**\n"
            f"能量已重置为: {max_energy}"
        )

    def _process_next_turn(self):
        """处理回合切换"""
        current_player = self.game_state["turn_info"]["active_player"]
        next_player = "opponent" if current_player == "player" else "player"
        self.game_state["turn_info"]["active_player"] = next_player
        
        debug_utils.log("game", "回合切换", {
            "当前玩家": current_player,
            "下一个玩家": next_player,
            "回合数": self.game_state["turn_info"]["current_turn"]
        })

    def _process_end_game(self):
        """处理游戏结束"""
        self._player_phase_transition(1.0)
        winner = self._determine_winner()
        self.add_game_message(f"🏆 **游戏结束 - {'你' if winner == 'player' else '对手'}获胜！**")
        debug_utils.log("game", "游戏结束", {"获胜者": winner})

    def _determine_winner(self):
        """判断获胜者"""
        if self.game_state["player_stats"]["hp"] <= 0:
            return "opponent"
        elif self.game_state["opponent_stats"]["hp"] <= 0:
            return "player"
        return None

    def start_game(self):
        """开始新游戏"""
        self.game_state["gameloop_state"] = "start_game"
        self._process_gameloop_state()

    def _process_player_turn(self):
        """处理玩家回合
        Returns:
            bool: 如果回合结束返回True，否则返回False
        """
        # 获取当前玩家回合状态
        player_turn_state = self.game_state.get("player_turn_state", "start")
        
        if player_turn_state == "start":
            # 回合开始阶段
            self.add_game_message("🎮 **你的回合开始了！**")
            self.game_state["player_turn_state"] = "draw_card"
            return False
            
        elif player_turn_state == "draw_card":
            # 抽牌阶段
            self.add_game_message("🎴 **抽取一张卡牌**")
            self.draw_card("player")
            self.game_state["player_turn_state"] = "action"
            return False
            
        elif player_turn_state == "action":
            # 玩家行动阶段
            # 等待玩家操作，由界面控制
            return False
            
        elif player_turn_state == "end_turn":
            # 回合���束阶段
            self.add_game_message("🔄 **你的回合结束了**")
            self.game_state["player_turn_state"] = "start"
            return True
            
        return False

    def _process_opponent_turn(self):
        """处理对手回合"""
        # 获取当前对手回合状态
        opponent_turn_state = self.game_state.get("opponent_turn_state", "start")
        
        if opponent_turn_state == "start":
            # 回合开始阶段
            self.add_game_message("🤖 **对手回合开始...**")
            self._ai_thinking("正在分析局势...")
            self.game_state["opponent_turn_state"] = "draw_card"
            return False
            
        elif opponent_turn_state == "draw_card":
            # 抽牌阶段
            self.add_game_message("🎴 **对手抽取了一张卡牌**")
            self.draw_card("opponent")
            self._ai_thinking("思考要使用哪张卡牌...")
            self.game_state["opponent_turn_state"] = "action"
            return False
            
        elif opponent_turn_state == "action":
            # AI行动阶段
            self._ai_thinking("正在计算最佳行动...")
            
            # 对手简单AI：随机打出一张手牌
            opponent_hand = self.game_state["hand_cards"]["opponent"]
            if opponent_hand:
                card_to_play = random.choice(opponent_hand)
                self.game_state["hand_cards"]["opponent"].remove(card_to_play)
                self.game_state["field_cards"]["opponent"].append(card_to_play)
                self.add_game_message(f"🎴 对手使用了 {card_to_play['name']}")
            
            self.game_state["opponent_turn_state"] = "end_turn"
            return False
            
        elif opponent_turn_state == "end_turn":
            # 回合结束阶段
            self._ai_thinking("回合结束...")
            self.add_game_message("🔄 **对手回合结束**")
            self.game_state["opponent_turn_state"] = "start"
            self.game_state["gameloop_state"] = "next_turn"
            return True
            
        return False

    def _ai_thinking(self, message, duration=0.5):
        """模拟AI思考过程
        Args:
            message: 思考内容提示
            duration: 思考时间（秒）
        """
        self.add_game_message(f"💭 {message}")
        self._player_phase_transition(duration)
