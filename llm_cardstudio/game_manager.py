import json
import os
import random
import time
import streamlit as st
from typing import Dict, List, Any, Tuple
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
        self.command_sequence_state = {
            'is_paused': False,
            'is_interrupted': False,
            'awaiting_selection': None,
            'current_command': None
        }
        
        # 初始化命令序列
        if 'command_sequence' not in st.session_state:
            st.session_state.command_sequence = {
                'commands': [],
                'current_index': 0,
                'is_executing': False
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
                "hp": 3,
                "energy": 3,
                "armor": 0
            },
            "opponent_stats": {
                "hp": 3,
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
        debug_utils.log("turn", "重置回合状态", {
            "回合数": self.game_state["turn_info"]["current_turn"],
            "玩家": active_player,
            "能量": max_energy,
            "攻击标记": False
        })
        
        self.add_game_message(
            f"🎯 **第{self.game_state['turn_info']['current_turn']}回合 - {'你的' if active_player == 'player' else '对手'}回合**\n"
            f"能量已重置为: {max_energy}"
        )

    def _process_next_turn(self):
        """处理回合切换"""
        current_player = self.game_state["turn_info"]["active_player"]
        next_player = "opponent" if current_player == "player" else "player"
        self.game_state["turn_info"]["active_player"] = next_player
        
        # 重置攻击标记
        self.game_state["has_attacked_this_turn"] = False
        
        debug_utils.log("game", "回合切换", {
            "当前玩家": current_player,
            "下一个玩家": next_player,
            "回合数": self.game_state["turn_info"]["current_turn"],
            "攻击标记": False
        })

    def start_game(self):
        """开始新游戏"""
        if not st.session_state.game_manager.selected_decks or \
                not st.session_state.game_manager.selected_decks.get("player") or \
                not st.session_state.game_manager.selected_decks.get("opponent"):
            print("错误：卡组信息不正确，无法开始游戏")
            return
        if self.game_state["gameloop_state"] != "welcome":
            print("错误：当前不在欢迎阶段，无法开始游戏")
            return

        self.game_state["gameloop_state"] = "start_game"
        return True

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

    def player_perform_attack(self, player_type: str = "player") -> bool:
        """玩家执行攻击动作
        
        Args:
            player_type: 攻击方，可选值："player" 或 "opponent"
            
        Returns:
            bool: 攻击是否成功执行
        """
        # 检查是否是第一回合
        if self.game_state["turn_info"]["current_turn"] == 1:
            self.add_game_message("❌ 第一回合不能进行攻击")
            debug_utils.log("attack", "攻击失败", {"原因": "第一回合不能攻击"})
            return False
            
        # 检查是否已经攻击过
        if self.game_state.get("has_attacked_this_turn", False):
            self.add_game_message("❌ 本回合已经攻击过了，每回合只能攻击一次")
            debug_utils.log("attack", "攻击失败", {"原因": "本回合已经攻击过"})
            return False

        # 检查己方场上是否有卡牌
        player_field = self.game_state["field_cards"][player_type]
        if not player_field:
            self.add_game_message("❌ 己方场上没有卡牌，不能攻击")
            debug_utils.log("attack", "攻击失败", {"原因": "场上没有卡牌"})
            return False

        # 重置命令序列状态
        self.command_sequence_state['is_interrupted'] = False
        self.command_sequence_state['is_paused'] = False
        self.command_sequence_state['awaiting_selection'] = None

        # 构建攻击命令序列
        command_sequence = []
        
        # 1. HMI选择攻击者
        command_sequence.append({
            "action": "SELECT_ATTACKER_HMI",
            "parameters": {
                "player_type": player_type,
                "can_skip": True  # 允许放弃选择
            },
            "duration": 0.5
        })
        
        # 2. HMI选择目标
        command_sequence.append({
            "action": "SELECT_TARGET_HMI",
            "parameters": {
                "player_type": player_type,
                "can_skip": True  # 允许放弃选择
            },
            "duration": 0.5
        })
        
        # 3. 执行攻击
        command_sequence.append({
            "action": "PERFORM_ATTACK",
            "parameters": {
                "player_type": player_type
            },
            "duration": 1.0
        })
        
        debug_utils.log("attack", "开始攻击流程", {
            "玩家类型": player_type,
            "命令序列": command_sequence
        })
        
        # 启动命令序列
        if command_sequence:
            success = self.start_command_sequence(command_sequence)

            return success
                
        return True

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
        
        # 检查游戏是否结束（除了欢迎和游戏结束状态外）
        if gameloop_state not in ["welcome", "start_game", "game_over", "restart_game"]:
            if self._check_game_over():
                self._process_game_over()
                return True
        
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
            
        elif gameloop_state == "game_over":
            # 游戏结束
            self._process_game_over()
            return True
            
        elif gameloop_state == "restart_game":
            # 重新开始游戏
            # self.game_state["gameloop_state"] = "welcome"
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
                        target_card_id=target_id
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
            self.game_state["gameloop_state"] = "next_turn"
            return True
            
        return False

    def start_command_sequence(self, commands: List[Dict]):
        """开始执行命令序列"""
        # 重置命令序列状态
        self.command_sequence_state['is_interrupted'] = False
        self.command_sequence_state['is_paused'] = False
        self.command_sequence_state['awaiting_selection'] = None
        self.command_sequence_state['current_command'] = None
        
        # 重置命令序列
        self.command_sequence['commands'] = commands
        self.command_sequence['current_index'] = 0
        self.command_sequence['is_executing'] = True
        
        print(f"开始执行命令序列，共 {len(commands)} 个命令")
        return True

    def process_next_command(self) -> bool:
        """处理序列中的下一个命令"""
        # 检查是否已经中断
        if self.command_sequence_state.get('is_interrupted'):
            print("命令序列已被中断")
            self.command_sequence['is_executing'] = False
            return False
            
        if not self.command_sequence['is_executing']:
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
                if not has_next_command:
                    break
        
        print("async_process_command_sequence_all: 命令序列已完成")
        # 命令序列为空,或者 执行完成
        self.command_sequence['commands'] = []
        self.command_sequence['current_index'] = 0
        self.command_sequence['is_executing'] = False


    async def async_process_next_command(self) -> bool:
        """处理序列中的下一个命令"""
        # 检查是否已经中断
        if self.command_sequence_state.get('is_interrupted'):
            print("命令序列已被中断")
            self.command_sequence['is_executing'] = False
            return False

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

    # 命令序列状态管理方法
    def pause_command_sequence(self):
        """暂停命令序列"""
        self.command_sequence_state['is_paused'] = True
        
    def resume_command_sequence(self):
        """恢复命令序列"""
        self.command_sequence_state['is_paused'] = False
        self.command_sequence_state['awaiting_selection'] = None
        
    def interrupt_command_sequence(self):
        """中断命令序列"""
        self.command_sequence_state['is_interrupted'] = True
        self.command_sequence_state['is_paused'] = False
        self.command_sequence_state['awaiting_selection'] = None
        
    def is_command_sequence_paused(self):
        """检查命令序列是否暂停"""
        return self.command_sequence_state.get('is_paused', False)
        
    def is_command_sequence_interrupted(self):
        """检查命令序列是否中断"""
        return self.command_sequence_state.get('is_interrupted', False)
        
    def get_awaiting_selection(self):
        """获取等待选择的状态"""
        return self.command_sequence_state.get('awaiting_selection')
        
    def set_awaiting_selection(self, selection_state):
        """设置等待选择的状态"""
        self.command_sequence_state['awaiting_selection'] = selection_state
        self.command_sequence_state['is_paused'] = True

    def handle_card_selection(self, selected_card_id: str = None):
        """处理卡牌选择结果
        
        Args:
            selected_card_id: 选中的卡牌ID,如果为None表示放弃选择
        """
        try:
            # 获取当前等待选择的状态
            selection_state = self.command_sequence_state.get('awaiting_selection')
            if not selection_state:
                print("没有等待中的卡牌选择")
                return
                
            selection_type = selection_state.get('type')
            
            if selected_card_id is None:
                # 如果放弃选择,中断命令序列
                self.add_game_message("❌ 已放弃当前行")
                self.interrupt_command_sequence()
                return
                
            # 根据不同的选择类型处理
            if selection_type == 'attacker':
                # 保存选中的攻击者
                self.game_state['selected_attacker'] = next(
                    (card for card in selection_state['valid_cards'] 
                     if str(card['id']) == str(selected_card_id)), 
                    None
                )
                self.add_game_message(f"✅ 选择了攻击者: {self.game_state['selected_attacker'].get('name', '未知卡牌')}")
                
            elif selection_type == 'target':
                # 保存选中的目标
                if selected_card_id == 'opponent_hero':
                    self.game_state['selected_target'] = {
                        'type': 'hero',
                        'owner': 'opponent'
                    }
                    self.add_game_message("✅ 选择了攻击目标: 对手英雄")
                else:
                    self.game_state['selected_target'] = next(
                        (card for card in selection_state['valid_cards'] 
                         if str(card['id']) == str(selected_card_id)), 
                        None
                    )
                    if self.game_state['selected_target']:
                        self.add_game_message(f"✅ 选择了攻击目标: {self.game_state['selected_target'].get('name', '未知卡牌')}")
                        
            elif selection_type in ['hand', 'opponent_hand']:
                # 保存选中的手牌
                selected_card = next(
                    (card for card in selection_state['valid_cards'] 
                     if str(card['id']) == str(selected_card_id)), 
                    None
                )
                if selected_card:
                    self.game_state['selected_hand_card'] = selected_card
                    self.add_game_message(f"✅ 选择了手牌: {selected_card.get('name', '未知卡牌')}")
            
            # 恢复命令序列执行
            self.resume_command_sequence()
            
        except Exception as e:
            print(f"处理卡牌选择失败: {str(e)}")
            # 发生错误时中断命令序列
            self.interrupt_command_sequence()

    def opponent_perform_attack(self, attacker_card_id: str, target_card_id: str) -> bool:
        """AI对手执行攻击动作
        
        Args:
            attacker_card_id: AI攻击者卡牌ID
            target_card_id: 目标卡牌ID (玩家场上的卡牌或英雄)
            
        Returns:
            bool: 攻击是否成功执行
        """
        try:
            # 检查是否已经攻击过
            if self.game_state.get("has_attacked_this_turn", False):
                self.add_game_message("❌ 本回合已经攻击过了")
                debug_utils.log("attack", "攻击失败", {"原因": "本回合已经攻击过"})
                return False

            # 获取攻击者卡牌
            attacker = next((card for card in self.game_state["field_cards"]["opponent"] 
                            if str(card["id"]) == str(attacker_card_id)), None)
            if not attacker:
                self.add_game_message("❌ 找不到AI攻击者卡牌")
                return False
            
            # 处理攻击目标
            if target_card_id == "opponent_hero":
                # 直接攻击英雄
                damage = attacker.get("attack", 0)
                self.game_state["player_stats"]["hp"] = max(0, self.game_state["player_stats"]["hp"] - damage)
                self.add_game_message(f"⚔️ {attacker['name']} 对玩家英雄造成了 {damage} 点伤害")
            else:
                # 攻击场上的卡牌
                target = next((card for card in self.game_state["field_cards"]["player"] 
                             if str(card["id"]) == str(target_card_id)), None)
                             
                if not target:
                    self.add_game_message("❌ 找不到目标卡牌")
                    return False
                
                # 计算互相伤害
                attacker_damage = attacker.get("attack", 0)
                target_damage = target.get("attack", 0)
                
                # 应用伤害
                target["health"] = max(0, target["health"] - attacker_damage)
                attacker["health"] = max(0, attacker["health"] - target_damage)
                
                self.add_game_message(
                    f"⚔️ {attacker['name']} 与 {target['name']} 进行了战斗\n"
                    f"{attacker['name']} 造成了 {attacker_damage} 点伤害\n"
                    f"{target['name']} 造成了 {target_damage} 点伤害"
                )
                
                # 检查卡牌是否死亡
                if target["health"] <= 0:
                    self.game_state["field_cards"]["player"].remove(target)
                    self.deck_state["player"]["discard_pile"].append(target)
                    self.add_game_message(f"💀 {target['name']} 被击败了")
                    
                if attacker["health"] <= 0:
                    self.game_state["field_cards"]["opponent"].remove(attacker)
                    self.deck_state["opponent"]["discard_pile"].append(attacker)
                    self.add_game_message(f"💀 {attacker['name']} 被击败了")
            
            # 设置攻击标记
            self.game_state["has_attacked_this_turn"] = True
            debug_utils.log("attack", "攻击标记已设置", {"has_attacked_this_turn": True})
                    
            return True
            
        except Exception as e:
            print(f"AI执行攻击失败: {str(e)}")
            return False

    def end_turn(self):
        """结束当前回合"""
        if self.game_state["gameloop_state"] != "player_turn":
            self.add_game_message("❌ 当前不是玩家回合")
            return False
        
        current_player = self.game_state["turn_info"]["active_player"]
        self.game_state[f"{current_player}_turn_state"] = "end_turn"
        return True

    def _process_game_over(self):
        """处理游戏结束"""
        self._player_phase_transition(1.0)
        
        winner = self.game_state.get("winner")
        print(f"游戏结束，获胜者: {winner}")
        
        if winner == "player":
            self.add_game_message("🏆 **游戏结束 - 你获胜了！**")
        elif winner == "opponent":
            self.add_game_message("🏆 **游戏结束 - 对手获胜！**")
        else:  # draw
            self.add_game_message("🤝 **游戏结束 - 双方平局！**")
            
        debug_utils.log("game", "游戏结束", {"获胜者": winner})
        
        # 设置游戏状态为重新开始
        self.game_state["gameloop_state"] = "restart_game"

    def _check_game_over(self) -> bool:
        """检查游戏是否结束
        
        Returns:
            bool: 如果游戏结束返回True，否则返回False
        """
        print(f"检查游戏结束 - 玩家生命值: {self.game_state['player_stats']['hp']}, 对手生命值: {self.game_state['opponent_stats']['hp']}")
        
        player_health = self.game_state["player_stats"]["hp"]
        opponent_health = self.game_state["opponent_stats"]["hp"]
        
        # 检查玩家生命值
        if player_health <= 0:
            print("玩家生命值归零，对手获胜")
            self.game_state["gameloop_state"] = "game_over"
            self.game_state["winner"] = "opponent"
            return True
            
        # 检查对手生命值
        if opponent_health <= 0:
            print("对手生命值归零，玩家获胜")
            self.game_state["gameloop_state"] = "game_over"
            self.game_state["winner"] = "player"
            return True
            
        return False
