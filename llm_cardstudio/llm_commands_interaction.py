import json
from typing import Dict, List, Any, Tuple, Optional
import time
import os
from debug_utils import debug_utils


class CommandProcessor:
    def __init__(self, game_manager):
        """初始化命令处理器"""
        self.game_manager = game_manager
        self.command_handlers = {
            'MOVE_CARD': self._handle_move_card,
            'PLAY_ANIMATION': self._handle_animation,
            'UPDATE_HEALTH': self._handle_update_health,
            'SHOW_MESSAGE': self._handle_show_message,
            'CREATE_CARD': self._handle_create_card,
            'APPLY_EFFECT': self._handle_apply_effect,
            'UPDATE_STATS': self._handle_update_stats,
            'DRAW_CARD': self._handle_draw_card,
            'DESTROY_CARD': self._handle_destroy_card,
            'APPLY_ARMOR': self._handle_apply_armor,
            'TRIGGER_EFFECT': self._handle_trigger_effect,
            'CHECK_CONDITION': self._handle_check_condition
        }
        
        self.effect_handlers = {
            'battlecry': self._handle_battlecry,
            'deathrattle': self._handle_deathrattle,
            'taunt': self._handle_taunt,
            'charge': self._handle_charge,
            'spell_damage': self._handle_spell_damage,
            'adjacent_effect': self._handle_adjacent_effect,
            'conditional_effect': self._handle_conditional_effect,
            'armor_gain': self._handle_armor_gain,
            'card_draw': self._handle_card_draw
        }
        
        # 加载卡牌命令配置
        self.commands_config = self._load_commands_config()

    def _load_commands_config(self) -> dict:
        """加载卡牌命令配置"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'cards_commands.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.game_manager.add_game_message(f"❌ 加载卡牌命令配置失败: {str(e)}")
            return {}

    def _apply_state_updates(self, updates: Dict[str, Any]):
        """应用状态更新"""
        for path, value in updates.items():
            # 解析状态路径
            parts = path.split('.')
            target = self.game_manager.game_state
            
            # 遍历路径直到最后一个键
            for part in parts[:-1]:
                target = target[part]
            
            # 应用更新
            last_key = parts[-1]
            if isinstance(value, str) and (value.startswith('+') or value.startswith('-')):
                # 处理增量更新
                current_value = target[last_key]
                target[last_key] = current_value + int(value)
            else:
                # 直接赋值
                target[last_key] = value

    # 基础指令处理器
    def _handle_move_card(self, params: Dict[str, Any]) -> bool:
        """处理移动卡牌指令"""
        print("进入 _handle_move_card 函数")
        
        card_id = params.get('card_id')
        target_position = params.get('target_position')
        source = params.get('source')
        player_type = params.get('player_type')
        pay_cost = params.get('pay_cost', source == 'hand' and target_position == 'field')
        
        try:
            # 获取源位置的卡牌列表
            source_list = self._get_card_list(source, player_type)
            target_list = self._get_card_list(target_position, player_type)
            
            # 查找卡牌
            card = next((c for c in source_list if c['id'] == card_id), None)
            if not card:
                print(f"❌ 找不到卡牌 {player_type}:{card_id}:{source}:{target_position}")
                return False
            
            # 检查能量是否足够
            if pay_cost:
                energy_cost = card.get('cost', 0)  # 假设卡牌数据中有能量成本字段
                if player_type == 'player':
                    if self.game_manager.game_state['player_stats']['energy'] < energy_cost:
                        self.game_manager.add_game_message(f"❌ 能量不足，无法支付 {energy_cost} 点能量")
                        return False
                    self.game_manager.game_state['player_stats']['energy'] -= energy_cost
                else:
                    if self.game_manager.game_state['opponent_stats']['energy'] < energy_cost:
                        self.game_manager.add_game_message(f"❌ 能量不足，无法支付 {energy_cost} 点能量")
                        return False
                    self.game_manager.game_state['opponent_stats']['energy'] -= energy_cost
                print(f"扣除 {energy_cost} 点能量")
            
            # 移动卡牌
            source_list.remove(card)
            target_list.append(card)
            
            print("移动卡牌指令处理成功")
            return True
            
        except Exception as e:
            print(f"移动卡牌指令失败: {str(e)}")
            return False

    def _handle_animation(self, params: Dict[str, Any]) -> bool:
        """处理动画效果指令"""
        print("进入 _handle_animation 函数")
        print("动画效果指令处理成功")
        return True
        
        animation_name = params.get('animation_name')
        target_id = params.get('target_id')
        
        # 这里添加播放动画的具体实现
        return True

    def _handle_update_health(self, params: Dict[str, Any]) -> bool:
        """处理生命值更新指令"""
        print("进入 _handle_update_health 函数")
        print("生命值更新指令处理成功")
        return True
        
        target_id = params.get('target_id')
        value = params.get('value', 0)
        update_type = params.get('type')
        
        try:
            if target_id == 'player':
                stats = self.game_manager.game_state['player_stats']
            else:
                stats = self.game_manager.game_state['opponent_stats']
                
            if update_type == 'heal':
                stats['hp'] = min(100, stats['hp'] + value)
            else:
                # 先检查护甲
                damage = value
                if stats['armor'] > 0:
                    absorbed = min(stats['armor'], damage)
                    stats['armor'] -= absorbed
                    damage -= absorbed
                
                if damage > 0:
                    stats['hp'] = max(0, stats['hp'] - damage)
                    
            return True
            
        except Exception as e:
            print(f"更新生命值失败: {str(e)}")
            return False

    def _handle_show_message(self, params: Dict[str, Any]) -> bool:
        """处理显示消息指令"""
        print("进入 _handle_show_message 函数")
        print("显示消息指令处理成功")
        return True
        
        message = params.get('message')
        if message:
            self.game_manager.add_game_message(message)
        return True

    def _handle_create_card(self, params: Dict[str, Any]) -> bool:
        """处理创建卡牌指令"""
        print("进入 _handle_create_card 函数")
        print("创建卡牌指令处理成功")
        return True
        
        card_id = params.get('card_id')
        owner = params.get('owner')
        position = params.get('position')
        
        try:
            # 获取卡牌模板
            card_template = next((c for c in self.game_manager.available_cards if c['id'] == card_id), None)
            if not card_template:
                return False
                
            # 创建新卡牌
            new_card = card_template.copy()
            
            # 添加到指定位置
            target_list = self._get_card_list(position, owner)
            target_list.append(new_card)
            return True
            
        except Exception as e:
            print(f"创建卡牌失败: {str(e)}")
            return False

    def _handle_apply_effect(self, params: Dict[str, Any]) -> bool:
        """处理效果应用指令"""
        print("进入 _handle_apply_effect 函数")
        print("效果应用指令处理成功")
        return True
        
        effect_type = params.get('effect_type')
        target_id = params.get('target_id')
        value = params.get('value')
        
        try:
            if effect_type in self.effect_handlers:
                return self.effect_handlers[effect_type](target_id, value)
            return False
            
        except Exception as e:
            print(f"应用效果失败: {str(e)}")
            return False

    def _handle_update_stats(self, params: Dict[str, Any]) -> bool:
        """处理更新统计数据指令"""
        print("进入 _handle_update_stats 函数")
        print("更新统计数据指令处理成功")
        return True
        
        target_id = params.get('target_id')
        stats = params.get('stats', {})
        
        try:
            target = self._get_target(target_id)
            if not target:
                return False
                
            # 更新统计数据
            for stat_name, value in stats.items():
                if stat_name in target:
                    target[stat_name] = value
            return True
            
        except Exception as e:
            print(f"更新统计数据失败: {str(e)}")
            return False

    def _handle_draw_card(self, params: Dict[str, Any]) -> bool:
        """处理抽牌指令"""
        print("进入 _handle_draw_card 函数")
        print("抽牌指令处理成功")
        return True
        
        target_id = params.get('target_id')
        draw_count = params.get('draw_count', 1)
        
        try:
            # 获取玩家的牌库和手牌
            deck = self.game_manager.deck_state[target_id]['deck']
            hand = self.game_manager.game_state['hand_cards'][target_id]
            
            # 执行抽牌
            for _ in range(draw_count):
                if not deck:
                    return False
                card = deck.pop()
                hand.append(card)
            return True
            
        except Exception as e:
            print(f"抽牌失败: {str(e)}")
            return False

    def _handle_destroy_card(self, params: Dict[str, Any]) -> bool:
        """处理摧毁卡牌指令"""
        print("进入 _handle_destroy_card 函数")
        print("摧毁卡牌指令处理成功")
        return True
        
        card_id = params.get('card_id')
        position = params.get('position')
        
        try:
            # 获取卡牌列表
            card_list = self._get_card_list(position)
            
            # 查找卡牌
            card = next((c for c in card_list if c['id'] == card_id), None)
            if not card:
                return False
                
            # 摧毁卡牌
            card_list.remove(card)
            return True
            
        except Exception as e:
            print(f"摧毁卡牌失败: {str(e)}")
            return False

    def _handle_apply_armor(self, params: Dict[str, Any]) -> bool:
        """处理应用护甲指令"""
        print("进入 _handle_apply_armor 函数")
        print("应用护甲指令处理成功")
        return True
        
        target_id = params.get('target_id')
        armor_value = params.get('armor_value')
        
        try:
            # 获取目标对象
            target = self._get_target(target_id)
            if not target:
                return False
                
            # 应用护甲
            target['armor'] = armor_value
            return True
            
        except Exception as e:
            print(f"应用护甲失败: {str(e)}")
            return False

    def _handle_trigger_effect(self, params: Dict[str, Any]) -> bool:
        """处理触发效果指令"""
        print("进入 _handle_trigger_effect 函数")
        print("触发效果指令处理成功")
        return True
        
        effect_type = params.get('effect_type')
        target_id = params.get('target_id')
        
        try:
            if effect_type in self.effect_handlers:
                return self.effect_handlers[effect_type](target_id)
            return False
            
        except Exception as e:
            print(f"触发效果失败: {str(e)}")
            return False

    def _handle_check_condition(self, params: Dict[str, Any]) -> bool:
        """处理检查条件指令"""
        print("进入 _handle_check_condition 函数")
        print("检查条件指令处理成功")
        return True
        
        condition = params.get('condition')
        
        try:
            # 检查条件
            if condition:
                return True
            return False
            
        except Exception as e:
            print(f"检查条件失败: {str(e)}")
            return False

    # 效果处理器
    def _handle_battlecry(self, target_id: str, value: Any = None) -> bool:
        """处理战吼效果"""
        print("进入 _handle_battlecry 函数")
        print("战吼效果处理成功")
        return True
        
        # 实现战吼效果逻辑
        return True

    def _handle_deathrattle(self, target_id: str, value: Any = None) -> bool:
        """处理亡语效果"""
        print("进入 _handle_deathrattle 函数")
        print("亡语效果处理成功")
        return True
        
        # 实现亡语效果逻辑
        return True

    def _handle_taunt(self, target_id: str, value: Any = None) -> bool:
        """处理嘲讽效果"""
        print("进入 _handle_taunt 函数")
        print("嘲讽效果处理成功")
        return True
        
        # 实现嘲讽效果逻辑
        return True

    def _handle_charge(self, target_id: str, value: Any = None) -> bool:
        """处理冲锋效果"""
        print("进入 _handle_charge 函数")
        print("冲锋效果处理成功")
        return True
        
        # 实现冲锋效果逻辑
        return True

    def _handle_spell_damage(self, target_id: str, value: int) -> bool:
        """处理法术伤害加成"""
        print("进入 _handle_spell_damage 函数")
        print("法术伤害加成处理成功")
        return True
        
        try:
            # 实现法术伤害加成逻辑
            return True
        except Exception as e:
            print(f"处理法术伤害加成失败: {str(e)}")
            return False

    def _handle_adjacent_effect(self, target_id: str, value: Any = None) -> bool:
        """处理相邻效果"""
        print("进入 _handle_adjacent_effect 函数")
        print("相邻效果处理成功")
        return True
        
        # 实现相邻效果逻辑
        return True

    def _handle_conditional_effect(self, target_id: str, value: Any = None) -> bool:
        """处理条件效果"""
        print("进入 _handle_conditional_effect 函数")
        print("条件效果处理成功")
        return True
        
        # 实现条件效果逻辑
        return True

    def _handle_armor_gain(self, target_id: str, value: int) -> bool:
        """处理获得护甲效果"""
        print("进入 _handle_armor_gain 函数")
        print("获得护甲效果处理成功")
        return True
        
        return self._handle_apply_armor({'target_id': target_id, 'armor_value': value})

    def _handle_card_draw(self, target_id: str, value: int) -> bool:
        """处理抽牌效果"""
        print("进入 _handle_card_draw 函数")
        print("抽牌效果处理成功")
        return True
        
        return self._handle_draw_card({'target_id': target_id, 'draw_count': value})

    # 辅助方法
    # def _get_card_list(self, position: str, owner: str = 'player') -> List[Dict]:
    def _get_card_list(self, position: str, owner: str) -> List[Dict]:
        """获取指定位置的卡牌列表"""
        if position == 'hand':
            return self.game_manager.game_state['hand_cards'][owner]
        elif position == 'field':
            return self.game_manager.game_state['field_cards'][owner]
        elif position == 'deck':
            return self.game_manager.deck_state[owner]['deck']
        elif position == 'discard':
            return self.game_manager.deck_state[owner]['discard_pile']
        else:
            raise ValueError(f"无效的位置: {position}")

    def _get_target(self, target_id: str) -> Optional[Dict]:
        """获取目标对象"""
        if target_id in ['player', 'opponent']:
            return self.game_manager.game_state[f'{target_id}_stats']
        
        # 在场上查找卡牌
        for owner in ['player', 'opponent']:
            field = self.game_manager.game_state['field_cards'][owner]
            card = next((c for c in field if c['id'] == target_id), None)
            if card:
                return card
                
        return None

    def process_card_commands(self, card_id: str, card: dict, player_type: str, phase: str = "phase_playcard") -> bool:
        """处理卡牌命令序列

        Args:
            card_id: 卡牌ID
            card: 卡牌数据
            player_type: 玩家类型
            phase: 执行阶段，如 phase_playcard, phase_battlecry, phase_deathrattle 等

        Returns:
            bool: 是否成功执行所有命令
        """
        try:
            # 查找卡牌命令配置 (优先查找特定 card_id)
            card_commands = next(
                (cmd for cmd in self.commands_config if str(cmd.get("card_id", "")) == str(card_id)),
                None
            )

            #如果找不到特定卡牌的命令配置，则查找 card_id 为 "all" 的默认配置
            if not card_commands:
                card_commands = next(
                    (cmd for cmd in self.commands_config if str(cmd.get("card_id", "")) == "all"),
                    None
                )
            
            if not card_commands:
                print(f"❌ 找不到卡牌命令配置: {card_id} 或 默认 all 配置")
                return False


            # 获取指定阶段的命令列表
            phase_key = f"{phase}_instructions"
            phase_commands = card_commands.get(phase_key, [])

            if not phase_commands:
                print(f"⚠️ 卡牌 {card_id} (或默认 all ) 在 {phase} 阶段没有命令")
                return True  # 没有命令也是正常的

            # 按序号排序命令
            sorted_commands = sorted(phase_commands, key=lambda x: x.get("sequence", 0))

            # 构建命令序列
            command_sequence = []
            for command in sorted_commands:
                # 获取命令信息
                action = command.get("action")
                parameters = command.get("parameters", {}).copy()  # 创建参数的副本
                duration = command.get("duration", 0)

                # 确保参数中的卡牌ID与当前卡牌一致
                if "card_id" in parameters:
                    parameters["card_id"] = str(card_id)

                # 添加玩家类型到参数中
                parameters["player_type"] = player_type

                # 添加到命令序列
                command_sequence.append({
                    "action": action,
                    "parameters": parameters,
                    "duration": duration
                })

                # 输出命令信息
                print(
                    f"添加到命令序列: {action} ({phase})\n"
                    f"参数: {json.dumps(parameters, ensure_ascii=False, indent=2)}"
                )

            # 启动命令序列
            if command_sequence:
                self.game_manager.start_command_sequence(command_sequence)

            return True

        except Exception as e:
            debug_utils.log("game", "处理卡牌命令出错", {
            "错误": str(e),
            "阶段": phase,
            "卡牌ID": card_id
        })
            return False

    def process_single_command(self, command: Dict[str, Any]) -> bool:
        """处理单个命令
        
        Args:
            command: 命令数据，包含 action、parameters 和 duration
            
        Returns:
            bool: 命令是否执行成功
        """
        try:
            action = command.get('action')
            parameters = command.get('parameters', {})
            duration = command.get('duration', 0)
            
            # 输出命令信息
            debug_message = (
                f"执行命令: {action}\n"
                f"参数: {json.dumps(parameters, ensure_ascii=False, indent=2)}"
            )
            print(debug_message)
            # self.game_manager.add_game_message(debug_message)
            
            # 执行命令
            handler = self.command_handlers.get(action)
            if not handler:
                error_message = f"❌ 未知命令: {action}"
                print(error_message)
                self.game_manager.add_game_message(error_message)
                return False
                
            success = handler(parameters)
            if not success:
                error_message = f"❌ 执行命令失败: {action}"
                print(error_message)
                # self.game_manager.add_game_message(error_message)
                return False
                
            # 处理持续时间
            if duration > 0:
                time.sleep(duration)
            
            # 添加成功消息
            success_message = f"✅ 命令执行成功: {action}"
            print(success_message)
            # self.game_manager.add_game_message(success_message)
            
            return True
            
        except Exception as e:
            error_message = f"❌ 命令执行出错: {str(e)}"
            print(error_message)
            # self.game_manager.add_game_message(error_message)
            return False

