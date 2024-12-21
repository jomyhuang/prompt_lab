import json
from typing import Dict, List, Any, Optional
import time

class CommandProcessor:
    def __init__(self, game_manager):
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
        
        # 效果处理器映射
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

    def process_llm_output(self, llm_response: str) -> bool:
        """处理LLM输出的指令集"""
        try:
            # 解析LLM输出为Python字典
            instructions_data = json.loads(llm_response)
            
            # 验证基本结构
            if not all(key in instructions_data for key in ['card_id', 'instructions', 'state_updates']):
                print("❌ 指令格式错误: 缺少必要字段")
                return False
            
            # 按序号排序指令
            sorted_instructions = sorted(
                instructions_data['instructions'],
                key=lambda x: x.get('sequence', 0)
            )
            
            # 执行指令序列
            for instruction in sorted_instructions:
                success = self._execute_instruction(instruction)
                if not success:
                    return False
                
                # 执行动画延迟
                if 'duration' in instruction:
                    time.sleep(instruction['duration'])
            
            # 更新游戏状态
            self._apply_state_updates(instructions_data['state_updates'])
            
            return True
            
        except json.JSONDecodeError:
            print("❌ 指令解析错误: 无效的JSON格式")
            return False
        except Exception as e:
            print(f"❌ 执行错误: {str(e)}")
            return False

    def _execute_instruction(self, instruction: Dict[str, Any]) -> bool:
        """执行单个指令"""
        action = instruction.get('action')
        if action not in self.command_handlers:
            print(f"❌ 未知指令: {action}")
            return False
            
        handler = self.command_handlers[action]
        return handler(instruction.get('parameters', {}))

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
        card_id = params.get('card_id')
        target_position = params.get('target_position')
        source = params.get('source')
        
        try:
            # 获取源位置的卡牌列表
            source_list = self._get_card_list(source)
            target_list = self._get_card_list(target_position)
            
            # 查找卡牌
            card = next((c for c in source_list if c['id'] == card_id), None)
            if not card:
                return False
                
            # 移动卡牌
            source_list.remove(card)
            target_list.append(card)
            return True
            
        except Exception as e:
            print(f"移动卡牌失败: {str(e)}")
            return False

    def _handle_animation(self, params: Dict[str, Any]) -> bool:
        """处理动画效果指令"""
        animation_name = params.get('animation_name')
        target_id = params.get('target_id')
        
        # 这里添加播放动画的具体实现
        return True

    def _handle_update_health(self, params: Dict[str, Any]) -> bool:
        """处理生命值更新指令"""
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
        message = params.get('message')
        if message:
            self.game_manager.add_game_message(message)
        return True

    def _handle_create_card(self, params: Dict[str, Any]) -> bool:
        """处理创建卡牌指令"""
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

    # 新增指令处理器
    def _handle_update_stats(self, params: Dict[str, Any]) -> bool:
        """处理更新统计数据指令"""
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
        card_id = params.get('card_id')
        
        try:
            # 在场上查找卡牌
            for owner in ['player', 'opponent']:
                field = self.game_manager.game_state['field_cards'][owner]
                card = next((c for c in field if c['id'] == card_id), None)
                if card:
                    # 移除卡牌
                    field.remove(card)
                    # 添加到弃牌堆
                    self.game_manager.deck_state[owner]['discard_pile'].append(card)
                    return True
            return False
            
        except Exception as e:
            print(f"摧毁卡牌失败: {str(e)}")
            return False

    def _handle_apply_armor(self, params: Dict[str, Any]) -> bool:
        """处理应用护甲指令"""
        target_id = params.get('target_id')
        armor_value = params.get('armor_value', 0)
        
        try:
            if target_id in ['player', 'opponent']:
                stats = self.game_manager.game_state[f'{target_id}_stats']
                stats['armor'] = max(0, stats['armor'] + armor_value)
                return True
            return False
            
        except Exception as e:
            print(f"应用护甲失败: {str(e)}")
            return False

    def _handle_trigger_effect(self, params: Dict[str, Any]) -> bool:
        """处理触发效果指令"""
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
        condition = params.get('condition')
        target_id = params.get('target_id')
        
        try:
            target = self._get_target(target_id)
            if not target:
                return False
                
            # 这里添加条件检查的具体实现
            # 返回条件是否满足
            return True
            
        except Exception as e:
            print(f"检查条件失败: {str(e)}")
            return False

    # 效果处理器
    def _handle_battlecry(self, target_id: str, value: Any = None) -> bool:
        """处理战吼效果"""
        # 实现战吼效果逻辑
        return True

    def _handle_deathrattle(self, target_id: str, value: Any = None) -> bool:
        """处理亡语效果"""
        # 实现亡语效果逻辑
        return True

    def _handle_taunt(self, target_id: str, value: Any = None) -> bool:
        """处理嘲讽效果"""
        # 实现嘲讽效果逻辑
        return True

    def _handle_charge(self, target_id: str, value: Any = None) -> bool:
        """处理冲锋效果"""
        # 实现冲锋效果逻辑
        return True

    def _handle_spell_damage(self, target_id: str, value: int) -> bool:
        """处理法术伤害加成"""
        try:
            if target_id in ['player', 'opponent']:
                stats = self.game_manager.game_state[f'{target_id}_stats']
                stats['spell_damage'] = max(0, stats.get('spell_damage', 0) + value)
                return True
            return False
        except Exception as e:
            print(f"处理法术伤害加成失败: {str(e)}")
            return False

    def _handle_adjacent_effect(self, target_id: str, value: Any = None) -> bool:
        """处理相邻效果"""
        # 实现相邻效果逻辑
        return True

    def _handle_conditional_effect(self, target_id: str, value: Any = None) -> bool:
        """处理条件效果"""
        # 实现条件效果逻辑
        return True

    def _handle_armor_gain(self, target_id: str, value: int) -> bool:
        """处理获得护甲效果"""
        return self._handle_apply_armor({'target_id': target_id, 'armor_value': value})

    def _handle_card_draw(self, target_id: str, value: int) -> bool:
        """处理抽牌效果"""
        return self._handle_draw_card({'target_id': target_id, 'draw_count': value})

    # 辅助方法
    def _get_card_list(self, position: str, owner: str = 'player') -> List[Dict]:
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

# 使用示例
"""
# 初始化
game_manager = GameManager()
command_processor = CommandProcessor(game_manager)

# 处理指令
success = command_processor.process_llm_output(llm_output)
"""
