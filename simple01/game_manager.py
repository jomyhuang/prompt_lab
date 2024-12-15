import json
import os
import random
import time
import streamlit as st
from debug_utils import debug_utils

class GameManager:
    def __init__(self):
        """初始化游戏管理器"""
        self._initialize_game_state(active_player=None)
        self.load_cards()
        # 移除init_hand_cards的调用，因为现在手牌发放由游戏开始流程控制
        # self.init_hand_cards()

    def _initialize_game_state(self, active_player=None):
        """初始化游戏状态
        Args:
            active_player: 当前行动玩家，默认为None
        """
        # 初始化游戏状态
        self.game_state = {
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
                "phase": None,
                "active_player": active_player
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
                "deck_size": 30,
                "draw_history": [],
                "discard_pile": []
            },
            "opponent": {
                "deck": [],
                "deck_size": 30,
                "draw_history": [],
                "discard_pile": []
            }
        }
        
        # 加载卡牌并初始化卡组
        self._initialize_decks()


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

    def _initialize_decks(self):
        """初始化玩家和对手的卡组"""
        # TODO: 从配置或数据库加载卡组数据
        self.deck_state["player"]["deck"] = self.available_cards.copy()
        self.deck_state["opponent"]["deck"] = self.available_cards.copy()

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

    def _process_player_turn(self):
        """处理玩家回合"""
        # 获取当前玩家回合状态
        player_turn_state = self.game_state.get("player_turn_state", "start")
        
        if player_turn_state == "start":
            # 回合开始
            self._player_phase_transition()
            self.game_state["turn_info"]["current_turn"] += 1
            # 重置能量
            self.game_state["player_stats"]["energy"] = min(10, self.game_state["turn_info"]["current_turn"])
            self.add_game_message(
                f"🎯 **第{self.game_state['turn_info']['current_turn']}回合 - 你的回合**\n能量已重置为: {self.game_state['player_stats']['energy']}"
            )
            debug_utils.log("game", "玩家回合开始")
            self.game_state["player_turn_state"] = "draw_card"
            st.rerun()
            return True
            
        elif player_turn_state == "draw_card":
            # 抽牌阶段过渡
            self._player_phase_transition()
            # 抽一张牌
            drawn_card = self.draw_card("player")
            if drawn_card:
                self.add_game_message("📤 你抽了一张牌")
                debug_utils.log("game", "玩家抽牌", {"抽到的牌": drawn_card})
            
            self.game_state["player_turn_state"] = "action"
            st.rerun()
            return True
            
        elif player_turn_state == "action":
            # 玩家行动阶段，返回False表示等待玩家操作
            return False
            
        elif player_turn_state == "end_turn":
            # 结束回合过渡
            self._player_phase_transition()
            # 结束回合
            self.add_game_message("⏱️ **你的回合结束**")
            debug_utils.log("game", "玩家回合结束")
            
            # 清理回合状态
            self.game_state.pop("player_turn_state", None)
            
            # 自动结束玩家回合
            self.end_turn()
            st.rerun()
            return True
        
        return False

    def end_turn(self):
        """结束当前回合，进入对手回合"""
        current_player = self.game_state["turn_info"]["active_player"]
        
        # 记录日志
        debug_utils.log("game", "结束回合", {
            "当前玩家": current_player,
            "回合数": self.game_state["turn_info"]["current_turn"]
        })
        
        # 切换玩家
        next_player = "opponent" if current_player == "player" else "player"
        self.game_state["turn_info"]["active_player"] = next_player
        
        # 如果是对手回合，执行对手AI行动
        if next_player == "opponent":
            # 添加回合开始消息
            self.add_game_message(
                f"🔄 **第{self.game_state['turn_info']['current_turn']}回合 - 对手回合**"
            )
            self._process_opponent_turn()
        else:
            # 处理玩家回合
            self._process_player_turn()

    def _ai_think(self, duration=1.0):
        """模拟AI思考
        
        Args:
            duration: 思考时间（秒）
        """
        time.sleep(duration)

    def _process_opponent_turn(self):
        """处理对手回合"""
        # 获取当前对手回合状态
        opponent_turn_state = self.game_state.get("opponent_turn_state", "start")
        
        if opponent_turn_state == "start":
            # 回合开始
            self.add_game_message("🎮 **对手回合开始**")
            debug_utils.log("game", "对手回合开始")
            self.game_state["opponent_turn_state"] = "draw_card"
            st.rerun()
            return
            
        elif opponent_turn_state == "draw_card":
            # AI思考
            self._ai_think(1.0)
            
            # 抽一张牌
            drawn_card = self.draw_card("opponent")
            if drawn_card:
                self.add_game_message("📤 对手抽了一张牌")
                debug_utils.log("game", "对手抽牌", {"抽到的牌": drawn_card})
            
            self.game_state["opponent_turn_state"] = "action"
            st.rerun()
            return
            
        elif opponent_turn_state == "action":
            # AI思考
            self._ai_think(1.5)
            
            # 简单AI：随机打出一张手牌
            opponent_hand = self.game_state["hand_cards"]["opponent"]
            if opponent_hand:
                played_card = random.choice(opponent_hand)
                self.game_state["hand_cards"]["opponent"].remove(played_card)
                self.game_state["field_cards"]["opponent"].append(played_card)
                
                card_message = [
                    f"🎴 对手使用了 **{played_card['name']}**",
                    f"  - 类型: {played_card['type']}",
                    f"  - 费用: {played_card.get('cost', 0)}",
                    f"  - 攻击: {played_card.get('attack', 0)}",
                    f"  - 生命: {played_card.get('health', 0)}",
                    f"  - 效果: {played_card.get('effect', '无')}"
                ]
                self.add_game_message("\n".join(card_message))
                debug_utils.log("game", "对手出牌", {"打出的牌": played_card})
            else:
                self.add_game_message("🤔 对手没有可用的手牌")
            
            self.game_state["opponent_turn_state"] = "end_turn"
            st.rerun()
            return
            
        elif opponent_turn_state == "end_turn":
            # AI思考
            self._ai_think(1.0)
            
            # 结束回合
            self.add_game_message("⏱️ **对手回合结束**")
            
            # 清理回合状态
            self.game_state.pop("opponent_turn_state", None)
            
            # 自动结束对手回合
            self.end_turn()
            st.rerun()
            return

    def _process_game_start(self):
        """处理游戏开始阶段"""
        # 获取当前游戏开始阶段状态
        game_start_state = self.game_state.get("game_start_state", "start_game")
        
        if game_start_state == "start_game":
            # 初始化游戏状态
            self._player_phase_transition(1.0)
            self.add_game_message("🎮 **游戏初始化...**")
            debug_utils.log("game", "游戏初始化")
            
            # 使用统一的初始化函数，active_player为None等待determine_first阶段设置
            self._initialize_game_state(active_player=None)
            
            self.game_state["game_start_state"] = "deal_cards"
            st.rerun()
            return True
            
        elif game_start_state == "deal_cards":
            # 发牌阶段
            self._player_phase_transition(1.0)
            self.add_game_message("🎴 **发放初始手牌...**")
            debug_utils.log("game", "发放初始手牌")
            
            # 双方各抽3张牌
            for _ in range(3):
                self.draw_card("player")
                self.draw_card("opponent")
            
            self.game_state["game_start_state"] = "determine_first"
            st.rerun()
            return True
            
        elif game_start_state == "determine_first":
            # 决定先手
            self._player_phase_transition(1.0)
            # 暂时默认玩家先手
            first_player = "player"
            self.add_game_message(f"🎲 **{'你' if first_player == 'player' else '对手'}先手**")
            debug_utils.log("game", "决定先手", {"先手玩家": first_player})
            
            # 设置先手玩家
            self.game_state["turn_info"]["active_player"] = first_player
            
            # 清理开始阶段状态
            self.game_state.pop("game_start_state", None)
            
            # 进入第一个回合
            self.end_turn()
            st.rerun()
            return True
            
        return False

    def start_game(self):
        """开始新游戏"""
        self.game_state["game_start_state"] = "start_game"
        self._process_game_start()
