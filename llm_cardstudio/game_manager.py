import json
import os
import random
import time
import streamlit as st
from typing import Dict, List, Any, Tuple, Optional
from re import T
from debug_utils import debug_utils
import asyncio

class GameManager:
    def __init__(self):
        """初始化游戏管理器"""
        self.load_cards()
        self.selected_decks = None
        self._initialize_game_state()
        
        # 初始化命令处理器
        from llm_commands_interaction import CommandProcessor
        self.commands_processor = CommandProcessor(self)

        # 初始化命令序列状态
        if 'command_sequence' not in st.session_state:
            st.session_state.command_sequence = {
                'commands': [],
                'current_index': 0,
                'is_executing': False,
                'is_paused': False  # 添加暂停状态标志
            }
            
        # 初始化游戏消息
        if 'game_messages' not in st.session_state:
            st.session_state.game_messages = []
            
        self.command_sequence = st.session_state.command_sequence
        self.game_messages = st.session_state.game_messages

    def set_commands_processor(self, processor):
        """设置命令处理器实例"""
        self.commands_processor = processor

    def _initialize_game_state(self):
        """初始化游戏状态"""
        # 初始化游戏状态
        self.game_state = {
            "gameloop_state": "welcome",  # 游戏主循环状态
            "player_stats": {
                "hp": 20,
                "energy": 3,
                "armor": 0
            },
            "opponent_stats": {
                "hp": 20,
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

    def play_card(self, card_id: str, player_type: str = "player") -> bool:
        """使用卡牌
        
        Args:
            card_id: 卡牌ID
            player_type: 玩家类型 ("player" 或 "opponent")
            
        Returns:
            bool: 是否成功使用卡牌
        """
        try:
            # 调试日志
            debug_utils.log("card", "尝试使用卡牌", {
                "card_id": card_id,
                "player_type": player_type
            })
            
            # 获取手牌
            hand_cards = self.game_state['hand_cards'][player_type]
            
            # # 调试日志
            # debug_utils.log("card", "当前手牌", {
            #     "hand_cards": [{"id": c.get("id")} for c in hand_cards]
            # })
            
            # 查找卡牌并移动卡牌
            card = None
            for i, c in enumerate(hand_cards):
                if str(c.get('id', '')) == str(card_id):
                    card = c
                    break
                    
            if not card:
                print(f"未找到卡牌: {card_id}")
                debug_utils.log("card", "未找到卡牌", {
                    "查找ID": card_id,
                    "可用卡牌": [{"id": c.get("id")} for c in hand_cards]
                })
                return False
                
            # 检查是否有足够的法力值
            # think: 检查条件与计算处理放到handle_move_card 或这里?
            # if self.game_state[f'{player_type}_stats']['energy'] < card.get('cost', 0):
            #     self.add_game_message("法力值不足")
            #     return False
                
            # # 扣除法力值
            # self.game_state[f'{player_type}_stats']['energy'] -= card.get('cost', 0)
            
            # 添加到场上(使用handle_move_card)
            # self.game_state['hand_cards'][player_type].remove(card)
            # self.game_state['field_cards'][player_type].append(card)
            
            # # 调试日志
            # debug_utils.log("card", "使用卡牌", {
            #     "card": {"id": card.get("id")},
            #     "remaining_energy": self.game_state[f'{player_type}_stats']['energy']
            # })
            
            # 处理卡牌命令
            command_sequence = self.commands_processor.get_playcard_commands(card_id, card, player_type, "phase_playcard")

            # 启动命令序列
            if command_sequence:
                success = self.start_command_sequence(command_sequence)
                if not success:
                    print(f"处理卡牌命令失败: {card_id}")
            
            return True
            
        except Exception as e:
            print(f"使用卡牌失败: {str(e)}")
            debug_utils.log("card", "使用卡牌出错", {"error": str(e)})
            return False

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
        self.add_game_message(f"👤 **{'你' if first_player == 'player' else '对手'}先手**")
        debug_utils.log("game", "决定先手", {"先手玩家": first_player})
        
        # 设置先手玩家
        self.game_state["turn_info"]["active_player"] = first_player

    def _process_new_turn(self):
        """处理新回合"""
        self._player_phase_transition(0.5)
        self.game_state["turn_info"]["current_turn"] += 1
        active_player = self.game_state["turn_info"]["active_player"]
        
        # 重置能量规则 - 基础能量为3，每回合+1，最大10点
        base_energy = 3
        turn_bonus = self.game_state["turn_info"]["current_turn"] - 1
        max_energy = min(10, base_energy + turn_bonus)
        self.game_state[f"{active_player}_stats"]["energy"] = max_energy
        
        # 重置攻击标记
        self.game_state["has_attacked_this_turn"] = False
        
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

    def _ai_thinking(self, message, duration=0.5):
        """模拟AI思考过程
        Args:
            message: 思考内容提示
            duration: 思考时间（秒）
        """
        self.add_game_message(f"🤖AI 正在思考: {message}")
        self._player_phase_transition(duration)

    def save_game(self, save_name):
        """保存游戏状态到文件
        
        Args:
            save_name: 存档名称
            
        Returns:
            tuple: (bool, str) - (是否成功, 成功/错误信息)
        """
        try:
            # 确保存档目录存在
            save_dir = os.path.join(os.path.dirname(__file__), "saves")
            os.makedirs(save_dir, exist_ok=True)
            
            # 准备保存数据
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            save_data = {
                "info": {
                    "save_time": current_time,
                    "save_name": save_name,
                    "turn": self.game_state.get("turn_info", {}).get("current_turn", 0),
                    "player_hp": self.game_state.get("player_stats", {}).get("hp", 0),
                    "opponent_hp": self.game_state.get("opponent_stats", {}).get("hp", 0)
                },
                "game_state": self.game_state,
                "deck_state": self.deck_state,
                "selected_decks": self.selected_decks
            }
            
            # 保存到文件
            save_path = os.path.join(save_dir, f"{save_name}.json")
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
                
            debug_utils.log("game", "保存游戏成功", {
                "存档名称": save_name,
                "存档路径": save_path,
                "保存时间": current_time
            })
            return True, f"游戏已保存到: {save_name}"
            
        except Exception as e:
            debug_utils.log("game", "保存游戏失败", {"错误": str(e)})
            return False, f"保存失败: {str(e)}"

    def load_game(self, save_name):
        """从文件加载游戏状态
        
        Args:
            save_name: 存档名称
            
        Returns:
            tuple: (bool, str) - (是否成功, 成功/错误信息)
        """
        try:
            # 构建存档路径
            save_dir = os.path.join(os.path.dirname(__file__), "saves")
            save_path = os.path.join(save_dir, f"{save_name}.json")
            
            # 检查文件是否存在
            if not os.path.exists(save_path):
                return False, f"存档文件不存在: {save_name}"
            
            # 读取存档文件
            with open(save_path, "r", encoding="utf-8") as f:
                save_data = json.load(f)
            
            # 验证必要的游戏数据
            if "game_state" not in save_data or "deck_state" not in save_data:
                return False, "存档数据缺少必要的游戏状态数据"
            
            # 使用深拷贝恢复游戏状态
            import copy
            self.game_state = copy.deepcopy(save_data["game_state"])
            self.deck_state = copy.deepcopy(save_data["deck_state"])
            
            # 检查并处理可选数据
            warning_messages = []
            
            if "selected_decks" not in save_data:
                warning_messages.append("警告: 存档中缺少卡组选择数据")
                self.selected_decks = None
            else:
                self.selected_decks = copy.deepcopy(save_data["selected_decks"])
            
            # 获取存档信息（如果有的话）
            info = save_data.get("info", {})
            save_time = info.get("save_time", "未知时间")
            turn = self.game_state.get("turn_info", {}).get("current_turn", 0)
            player_hp = self.game_state.get("player_stats", {}).get("hp", 0)
            opponent_hp = self.game_state.get("opponent_stats", {}).get("hp", 0)
            
            if not info:
                warning_messages.append("警告: 存档中缺少详细信息数据")
            
            debug_utils.log("game", "加载游戏成功", {
                "存档名称": save_name,
                "存档路径": save_path,
                "警告信息": warning_messages if warning_messages else "无"
                # "游戏状态": self.game_state
            })
            
            success_message = [f"成功加载存档: {save_name}",
                             f"保存时间: {save_time}",
                             f"回合数: {turn}",
                             f"玩家生命: {player_hp}",
                             f"对手生命: {opponent_hp}"]
            
            if warning_messages:
                success_message.extend(warning_messages)
            
            return True, "\n".join(success_message)
            
        except json.JSONDecodeError:
            return False, "存档文件格式错误"
        except Exception as e:
            debug_utils.log("game", "加载游戏失败", {"错误": str(e)})
            return False, f"加载失败: {str(e)}"

    def get_save_files(self):
        """获取所有存档文件列表
        
        Returns:
            list: 存档文件名列表（不含.json后缀）
        """
        try:
            save_dir = os.path.join(os.path.dirname(__file__), "saves")
            if not os.path.exists(save_dir):
                return []
                
            # 获取所有.json文件并去掉后缀
            save_files = [f[:-5] for f in os.listdir(save_dir) if f.endswith('.json')]
            return sorted(save_files)
            
        except Exception as e:
            debug_utils.log("game", "获取存档列表失败", {"错误": str(e)})
            return []

    def opponent_perform_attack(self, attacker_card_id: str, target_card_id: str = None, player_type: str = "opponent") -> bool:
        """执行攻击动作
        
        Args:
            attacker_card_id: 攻击者卡牌ID
            target_card_id: 目标卡牌ID，如果为None或为"opponent_hero"则直接攻击对手
            player_type: 攻击方，可选值："player" 或 "opponent"
            
        Returns:
            bool: 攻击是否成功执行
        """
        # 检查是否是第一回合
        if self.game_state["turn_info"]["current_turn"] == 1:
            self.add_game_message("❌ 第一回合不能进行攻击")
            return False
            
        # 检查是否已经攻击过
        if self.game_state.get("has_attacked_this_turn", False):
            self.add_game_message("❌ 本回合已经攻击过了")
            return False
            
        # 获取攻击者卡牌
        attacker_field = self.game_state["field_cards"][player_type]
        attacker_card = next((card for card in attacker_field if card["id"] == attacker_card_id), None)
        if not attacker_card:
            self.add_game_message("❌ 找不到指定的攻击者卡牌")
            return False
            
        # 获取目标卡牌（如果有）
        target_card = None
        if target_card_id and target_card_id != "opponent_hero":
            opponent_type = "opponent" if player_type == "player" else "player"
            opponent_field = self.game_state["field_cards"][opponent_type]
            target_card = next((card for card in opponent_field if card["id"] == target_card_id), None)
            if not target_card:
                self.add_game_message("❌ 找不到指定的目标卡牌")
                return False

        # 构建攻击命令序列
        command_sequence = []
        
        # 1. 选择攻击者
        command_sequence.append({
            "action": "SELECT_ATTACKER",
            "parameters": {
                "card_id": attacker_card["id"],
                "player_type": player_type
            },
            "duration": 0.5
        })
        
        # 2. 如果有目标卡牌，选择目标
        if target_card:
            command_sequence.append({
                "action": "SELECT_TARGET",
                "parameters": {
                    "card_id": target_card["id"],
                    "target_type": "opponent" if player_type == "player" else "player"
                },
                "duration": 0.5
            })
        else:
            # 直接攻击英雄
            command_sequence.append({
                "action": "SELECT_TARGET",
                "parameters": {
                    "target_type": "opponent_hero"
                },
                "duration": 0.5
            })
        
        # 3. 执行攻击
        command_sequence.append({
            "action": "PERFORM_ATTACK",
            "parameters": {
                "attacker_id": attacker_card["id"],
                "target_id": target_card["id"] if target_card else None,
                "player_type": player_type
            },
            "duration": 1.0
        })
        
        # 启动命令序列
        if command_sequence:
            success = self.start_command_sequence(command_sequence)
            # 记录已攻击标记
            self.game_state["has_attacked_this_turn"] = True
                
        return True

    def player_perform_attack(self, attacker_card_id: str = None, target_card_id: str = None, player_type: str = "player") -> bool:
        """玩家执行攻击
        
        Args:
            attacker_id: 攻击者卡牌ID,如果为None则需要选择
            target_id: 目标卡牌ID,如果为None则需要选择
            
        Returns:
            bool: 攻击是否成功执行
        """

        # 构建命令序列
        command_sequence = []
        prepare_attack = True

        # 1. 检查是否是第一回合
        if self.game_state["turn_info"]["current_turn"] == 1:
            command_sequence.append({
                "action": "SHOW_MESSAGE",
                "parameters": {
                    "message": "❌ 第一回合不能进行攻击"
                }
            })
            prepare_attack = False
            
        # 2. 检查是否已经攻击过
        if self.game_state.get("has_attacked_this_turn", False):
            command_sequence.append({
                "action": "SHOW_MESSAGE",
                "parameters": {
                    "message": "❌ 本回合已经攻击过了"
                }
            })
            prepare_attack = False

        # 3. 检查场上是否至少一张以上的卡牌
        player_field = self.game_state["field_cards"][player_type]
        if not player_field:
            command_sequence.append({
                "action": "SHOW_MESSAGE",
                "parameters": {
                    "message": "❌ 没有可攻击的卡牌，无法攻击"
                }
            })
            prepare_attack = False

        if prepare_attack:
            # 如果没有指定攻击者,添加选择攻击者命令
            if not attacker_card_id:
                command_sequence.append({
                    "action": "SELECT_ATTACKER_HMI",
                    "parameters": {
                        "player_type": player_type
                    }
                })
                
            # 如果没有指定目标,添加选择目标命令
            if not target_card_id:
                command_sequence.append({
                    "action": "SELECT_TARGET_HMI",
                    "parameters": {
                        "player_type": player_type,
                        "target_type": "opponent"
                    }
                })
                
            # 添加执行攻击命令
            command_sequence.append({
                "action": "PERFORM_ATTACK",
                "parameters": {
                    "attacker_id": attacker_card_id,
                    "target_id": target_card_id,
                    "player_type": player_type
                }
            })
            
        # 启动命令序列
        if command_sequence:
            success = self.start_command_sequence(command_sequence)
            if prepare_attack:
                # 记录已攻击标记
                self.game_state["has_attacked_this_turn"] = True

            return success
        
        return False


    def ai_decide_attack(self):
        """AI决定是否攻击
        
        Returns:
            bool: 是否执行攻击
        """
        # 目前使用随机决策，50%概率攻击
        return random.random() < 0.5

    def ai_decide_playcard(self):
        """AI决定是否打出卡牌
        
        Returns:
            bool: 是否执行打出卡牌
        """
        # 目前使用随机决策，50%概率打出卡牌 
        return random.random() < 0.5

    def _process_gameloop_state(self):
        """处理游戏主循环状态"""
        gameloop_state = self.game_state.get("gameloop_state", "welcome")
        print(f"处理游戏主循环状态: {gameloop_state}")
        
        if gameloop_state == "welcome":
            # 等待玩家按下开始游戏按钮
            return False
            
        elif gameloop_state == "start_game":
            # 游戏开始初始化
            self._process_game_start()
            self.game_state["gameloop_state"] = "deal_cards"
            return True
            
        elif gameloop_state == "deal_cards":
            # 发牌阶段
            self._process_deal_cards()
            self.game_state["gameloop_state"] = "determine_first"
            return True
            
        elif gameloop_state == "determine_first":
            # 决定首轮玩家
            self._process_determine_first()
            self.game_state["gameloop_state"] = "new_turn"
            return True
            
        elif gameloop_state == "new_turn":
            # 新回合开始
            self._process_new_turn()
            if self.game_state["turn_info"]["active_player"] == "player":
                self.game_state["gameloop_state"] = "player_turn"
                self.game_state["player_turn_state"] = "start"
            else:
                self.game_state["gameloop_state"] = "opponent_turn"
                self.game_state["opponent_turn_state"] = "start"
            return True
            
        elif gameloop_state == "player_turn":
            # 玩家回合
            if self._process_player_turn():
                self.game_state["gameloop_state"] = "next_turn"
                return True
            
        elif gameloop_state == "opponent_turn":
            # 对手回合
            if self._process_opponent_turn():
                self.game_state["gameloop_state"] = "next_turn"
                return True

        elif gameloop_state == "next_turn":
            # 进入下一回合
            self._process_next_turn()
            self.game_state["gameloop_state"] = "new_turn"
            return True
            
        elif gameloop_state == "end_game":
            # 游戏结束
            self._process_end_game()
            self.game_state["gameloop_state"] = "welcome"
            return True

        # 返回 状态是否变更?
        return False

    def _process_player_turn(self):
        """处理玩家回合
        Returns:
            bool: 如果回合结束返回True，否则返回False
        """
        # 获取当前玩家回合状态
        player_turn_state = self.game_state.get("player_turn_state", "start")
        print(f"处理玩家回合状态: {player_turn_state}")
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
            print("玩家行动阶段 action")
            # 玩家行动阶段
            # 等待玩家操作，由界面控制
            return False
            
        elif player_turn_state == "end_turn":
            # 回合结束阶段
            self.add_game_message("🔄 **你的回合结束了**")
            # self.game_state["player_turn_state"] = "start"
            return True
            
        return False

    def _process_opponent_turn(self):
        """处理对手回合"""
        opponent_turn_state = self.game_state.get("opponent_turn_state", "start")
        print(f"处理对手回合状态: {opponent_turn_state}")
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
            # self._ai_thinking("思考要使用哪张卡牌...")
            self.game_state["opponent_turn_state"] = "action"
            return False
            
        elif opponent_turn_state == "action":
            # AI行动阶段
            self._ai_thinking("正在计算最佳行动...")
            
            if self.ai_decide_playcard():
                print("对手回合 action 打牌")
                # 对手简单AI：随机打一张手牌
                opponent_hand = self.game_state["hand_cards"]["opponent"]
                if opponent_hand:
                    # 筛选能量足够的卡牌
                    playable_cards = [
                        card for card in opponent_hand 
                        if card.get("cost", 0) <= self.game_state["opponent_stats"]["energy"]
                    ]
                    
                    if playable_cards:
                        card_to_play = random.choice(playable_cards)
                        # 使用卡牌
                        self.play_card(card_to_play["id"], "opponent")
            else:
                print("🤖 对手不想打牌")
                        
            self.game_state["opponent_turn_state"] = "action_2"
            return False

        elif opponent_turn_state == "action_2":
            
            # 使用完手牌后，AI决定是否攻击
            self._ai_thinking("思考是否发起攻击...", 0.5)
            if self.ai_decide_attack():
                print("对手回合 action_2 发起攻击")
                # 获取AI场上的卡牌
                ai_field_cards = self.game_state["field_cards"]["opponent"]
                if not ai_field_cards:
                    # 如果场上没有卡牌，则无法攻击
                    self.add_game_message("🤖 对手场上没有可用于攻击的卡牌")
                else:
                    # 随机选择一张攻击卡牌
                    attacker_card = random.choice(ai_field_cards)
                    
                    # 获取可能的攻击目标
                    player_field_cards = self.game_state["field_cards"]["player"]
                    possible_targets = ["opponent_hero"]  # 始终可以攻击英雄
                    if player_field_cards:
                        # 如果玩家场上有卡牌，将它们加入可能的目标
                        possible_targets.extend([card["id"] for card in player_field_cards])
                    
                    # 随机选择攻击目标
                    target_id = random.choice(possible_targets)
                    
                    # 执行攻击
                    attack_success = self.opponent_perform_attack(
                        attacker_card_id=attacker_card["id"],
                        target_card_id=target_id,
                        player_type="opponent"
                    )
                    
                    if attack_success:
                        self.add_game_message(f"🤖 对手使用 {attacker_card['name']} 发起攻击")
            else:
                print("🤖 对手不想发起攻击")
            
            self.game_state["opponent_turn_state"] = "end_turn"
            return False
            
        elif opponent_turn_state == "end_turn":
            # 回合结束阶段
            self._ai_thinking("回合结束...", 1.5)
            self.add_game_message("🔄 **对手回合结束**")
            # self.game_state["opponent_turn_state"] = "start"
            self.game_state["gameloop_state"] = "next_turn"
            return True
            
        # print(f"对手回合状态处理结束 {opponent_turn_state}")

        return False

    def start_command_sequence(self, commands: List[Dict]):
        """开始执行命令序列"""
        self.command_sequence['commands'] = commands
        self.command_sequence['current_index'] = 0
        self.command_sequence['is_executing'] = True
        print(f"开始执行命令序列，共 {len(commands)} 个命令")
        # asyncio.create_task(self.async_process_command_sequence_all(commands))
        # print("启动asyncio命令序列-----")

    def process_next_command(self) -> bool:
        """处理序列中的下一个命令"""
        if not self.command_sequence['is_executing'] or self.is_command_sequence_paused():
            return False
            
        commands = self.command_sequence['commands']
        current_index = self.command_sequence['current_index']
        
        if current_index >= len(commands):
            self.add_game_message("命令序列执行完成")
            print("命令序列执行完成")
            self.command_sequence['is_executing'] = False
            self.command_sequence['current_index'] = 0
            return False
            
        command = commands[current_index]
        print(f"执行命令 {current_index + 1}/{len(commands)}: {command['action']}")
        
        # 执行命令
        success = self.commands_processor.process_single_command(command)
        
        if success:
            # 只有在命令序列未暂停时才递增索引
            if not self.is_command_sequence_paused():
                self.command_sequence['current_index'] += 1
            self.add_game_message(f"✅ 命令执行成功: {command['action']}")
        else:
            self.add_game_message(f"❌ 命令失败中断序列: {command['action']}")
            self.command_sequence['is_executing'] = False
            
        return success
        
    def is_executing_commands(self) -> bool:
        """检查是否正在执行命令序列"""
        return self.command_sequence['is_executing']
        
    def get_current_command_progress(self) -> Tuple[int, int]:
        """获取当前命令执行进度"""
        total = len(self.command_sequence['commands'])
        current = self.command_sequence['current_index']
        return current, total

    async def async_process_command_sequence_all(self, commands: List[Dict]):
        """异步处理命令序列"""
        if not self.is_executing_commands():
            return
        
        print("开始执行命令序列 async_process_command_sequence_all")

        """开始执行命令序列"""
        self.command_sequence['commands'] = commands
        self.command_sequence['current_index'] = 0
        self.command_sequence['is_executing'] = True
        print(f"开始执行命令序列，共 {len(commands)} 个命令")

        commands = self.command_sequence['commands']
  
        """异步处理命令序列"""
        while self.command_sequence['is_executing']:
                has_next_command =  self.process_next_command()
                await asyncio.sleep(0)
                # has_next_command =  self.async_process_next_command()
                # command = commands[self.command_sequence['current_index']]
                # duration = command.get('duration', 1)
                # # if duration > 0:
                # #     await asyncio.sleep(duration)
                # #     # time.sleep(duration)
                if not has_next_command:
                    break
        
        print("async_process_command_sequence_all: 命令序列已完成")
        # 命令序列为空,或者 执行完成
        self.command_sequence['commands'] = []
        self.command_sequence['current_index'] = 0
        self.command_sequence['is_executing'] = False


    async def async_process_next_command(self) -> bool:
        """处理序列中的下一个命令"""
        if not self.command_sequence['is_executing']:
            return False

        commands = self.command_sequence['commands']
        current_index = self.command_sequence['current_index']

        if current_index >= len(commands):
            self.add_game_message("命令序列执行完成")
            print("命令序列执行完成")
            self.command_sequence['is_executing'] = False
            return False # 返回False表示执行完成

        command = commands[current_index]
        self.command_sequence['current_index'] += 1
        
        #  处理单个命令，并且等待其完成
        await self.commands_processor.async_process_single_command(command)

        print(f"执行命令: {current_index + 1}/{len(commands)} {command['action']}")
        self.add_game_message(f"执行命令: {current_index + 1}/{len(commands)} {command['action']}")
        
        return True  # 返回True 表示还有命令需要执行

    def pause_command_sequence(self):
        """暂停命令序列执行"""
        print("暂停命令序列执行")
        self.command_sequence['is_paused'] = True
        
    def resume_command_sequence(self):
        """恢复命令序列执行"""
        print("恢复命令序列执行")
        self.command_sequence['is_paused'] = False
        
    def is_command_sequence_paused(self) -> bool:
        """检查命令序列是否暂停"""
        return self.command_sequence.get('is_paused', False)
        
    def handle_card_selection(self, selected_card_id: str) -> bool:
        """处理卡牌选择
        
        Args:
            selected_card_id: 选中的卡牌ID
            
        Returns:
            bool: 是否成功处理选择
        """
        try:
            # 检查是否处于等待选择状态
            selection_state = self.game_state.get('awaiting_selection')
            if not selection_state:
                print("当前不在等待选择状态")
                return False
                
            selection_type = selection_state.get('type')
            player_type = selection_state.get('player_type')
            
            if selection_type == 'attacker':
                # 验证选择的攻击者是否有效
                valid_cards = selection_state.get('valid_cards', [])
                selected_card = next((card for card in valid_cards if card['id'] == selected_card_id), None)
                
                if not selected_card:
                    self.add_game_message("❌ 无效的攻击者选择")
                    return False
                    
                # 保存选择的攻击者
                self.game_state['selected_attacker'] = selected_card
                self.add_game_message(f"✅ 选择了攻击者: {selected_card.get('name', '未知卡牌')}")
                
            elif selection_type == 'target':
                # 验证选择的目标是否有效
                valid_targets = selection_state.get('valid_targets', [])
                
                if selected_card_id == 'opponent_hero':
                    # 处理选择英雄作为目标
                    self.game_state['selected_target'] = {
                        'type': 'hero',
                        'owner': 'opponent'
                    }
                    self.add_game_message("✅ 选择了攻击目标: 对手英雄")
                else:
                    # 验证选择的目标卡牌
                    selected_target = next((target for target in valid_targets if target['id'] == selected_card_id), None)
                    if not selected_target:
                        self.add_game_message("❌ 无效的目标选择")
                        return False
                        
                    self.game_state['selected_target'] = selected_target
                    self.add_game_message(f"✅ 选择了攻击目标: {selected_target.get('name', '未知卡牌')}")
            
            # 清除等待选择状态
            self.game_state.pop('awaiting_selection', None)
            
            # 恢复命令序列执行
            self.resume_command_sequence()
            
            return True
            
        except Exception as e:
            print(f"处理卡牌选择失败: {str(e)}")
            return False

    def interrupt_command_sequence(self):
        """中断当前命令序列"""
        # 清空命令序列
        self.command_sequence['commands'] = []
        self.command_sequence['current_index'] = 0
        self.command_sequence['is_executing'] = False
        self.command_sequence['is_paused'] = False
        
        # 清空卡牌选择状态
        self.selected_attacker = None
        self.selected_target = None
        
        # 添加中断消息到游戏日志
        debug_utils.log("game", "命令序列已中断")
