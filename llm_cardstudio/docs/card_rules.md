# 卡牌规则系统设计

## 1. 卡牌数据模型

### 1.1 基础卡牌模型
```python
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class CardEffect(BaseModel):
    """卡牌效果模型"""
    effect_type: str = Field(..., description="效果类型")
    target_type: str = Field(..., description="目标类型")
    value: float = Field(..., description="效果数值")
    condition: Optional[Dict] = Field(None, description="触发条件")
    duration: Optional[int] = Field(None, description="持续回合")
    
class CardTrigger(BaseModel):
    """卡牌触发器模型"""
    trigger_type: str = Field(..., description="触发类型")
    condition: Dict = Field(..., description="触发条件")
    effects: List[CardEffect] = Field(..., description="触发效果")

class Card(BaseModel):
    """卡牌基础模型"""
    id: str = Field(..., description="卡牌唯一ID")
    name: str = Field(..., description="卡牌名称")
    description: str = Field(..., description="卡牌描述")
    cost: int = Field(..., description="费用")
    card_type: str = Field(..., description="卡牌类型")
    rarity: str = Field(..., description="稀有度")
    effects: List[CardEffect] = Field(default_factory=list, description="卡牌效果")
    triggers: List[CardTrigger] = Field(default_factory=list, description="卡牌触发器")
    keywords: List[str] = Field(default_factory=list, description="关键词")
```

### 1.2 卡牌规则定义示例
```python
# 生物卡牌
creature_card = {
    "id": "CARD_001",
    "name": "烈焰战士",
    "description": "战吼：对敌方随从造成2点伤害",
    "cost": 3,
    "card_type": "creature",
    "rarity": "rare",
    "effects": [
        {
            "effect_type": "damage",
            "target_type": "enemy_creature",
            "value": 2,
            "condition": {"trigger": "battlecry"}
        }
    ],
    "triggers": [],
    "keywords": ["battlecry"]
}

# 法术卡牌
spell_card = {
    "id": "CARD_002",
    "name": "火球术",
    "description": "造成4点伤害，如果目标是随从，额外造成2点伤害",
    "cost": 4,
    "card_type": "spell",
    "rarity": "common",
    "effects": [
        {
            "effect_type": "damage",
            "target_type": "any",
            "value": 4
        },
        {
            "effect_type": "damage",
            "target_type": "creature",
            "value": 2,
            "condition": {"target_type": "creature"}
        }
    ],
    "triggers": [],
    "keywords": []
}

# 装备卡牌
equipment_card = {
    "id": "CARD_003",
    "name": "炎魔之剑",
    "description": "装备者攻击时，对相邻随从造成1点伤害",
    "cost": 2,
    "card_type": "equipment",
    "rarity": "epic",
    "effects": [],
    "triggers": [
        {
            "trigger_type": "on_attack",
            "condition": {"equipped": True},
            "effects": [
                {
                    "effect_type": "damage",
                    "target_type": "adjacent_creatures",
                    "value": 1
                }
            ]
        }
    ],
    "keywords": []
}
```

## 2. 规则解析系统

### 2.1 规则解析器
```python
class RuleParser:
    """规则解析器"""
    
    def parse_card_rules(self, card: Card) -> Dict:
        """解析卡牌规则"""
        rules = {
            "basic_rules": self._parse_basic_rules(card),
            "effect_rules": self._parse_effects(card.effects),
            "trigger_rules": self._parse_triggers(card.triggers),
            "keyword_rules": self._parse_keywords(card.keywords)
        }
        return rules
        
    def _parse_basic_rules(self, card: Card) -> Dict:
        """解析基础规则"""
        return {
            "playable_condition": {
                "mana_required": card.cost,
                "card_type_restrictions": self._get_type_restrictions(card.card_type)
            }
        }
        
    def _parse_effects(self, effects: List[CardEffect]) -> List[Dict]:
        """解析效果规则"""
        parsed_effects = []
        for effect in effects:
            parsed_effects.append({
                "type": effect.effect_type,
                "resolution_steps": self._get_effect_steps(effect),
                "targeting_rules": self._get_targeting_rules(effect),
                "value_calculation": self._get_value_calculation(effect)
            })
        return parsed_effects
```

### 2.2 规则验证器
```python
class RuleValidator:
    """规则验证器"""
    
    def validate_card_play(self, card: Card, game_state: Dict) -> bool:
        """验证出牌规则"""
        # 检查基础规则
        if not self._validate_basic_rules(card, game_state):
            return False
            
        # 检查目标选择
        if not self._validate_targeting(card, game_state):
            return False
            
        # 检查特殊条件
        if not self._validate_conditions(card, game_state):
            return False
            
        return True
        
    def _validate_basic_rules(self, card: Card, game_state: Dict) -> bool:
        """验证基础规则"""
        # 检查费用
        if game_state["player"]["mana"] < card.cost:
            return False
            
        # 检查卡牌类型限制
        if not self._check_type_restrictions(card, game_state):
            return False
            
        return True
```

## 3. 效果处理系统

### 3.1 效果执行器
```python
class EffectExecutor:
    """效果执行器"""
    
    def execute_effect(self, effect: CardEffect, game_state: Dict) -> Dict:
        """执行卡牌效果"""
        # 获取效果处理器
        processor = self._get_effect_processor(effect.effect_type)
        
        # 处理效果前检查
        if not processor.pre_process_check(effect, game_state):
            raise EffectExecutionError("效果执行前检查失败")
            
        # 执行效果
        result = processor.process(effect, game_state)
        
        # 处理效果后更新
        game_state = processor.post_process_update(effect, game_state, result)
        
        return {
            "result": result,
            "updated_state": game_state
        }
```

### 3.2 效果处理器示例
```python
class DamageEffectProcessor:
    """伤害效果处理器"""
    
    def pre_process_check(self, effect: CardEffect, game_state: Dict) -> bool:
        """执行前检查"""
        # 检查目标是否有效
        if not self._validate_target(effect, game_state):
            return False
            
        # 检查伤害值是否有效
        if not self._validate_damage_value(effect):
            return False
            
        return True
        
    def process(self, effect: CardEffect, game_state: Dict) -> Dict:
        """处理伤害效果"""
        target = self._get_target(effect, game_state)
        damage = self._calculate_damage(effect, game_state)
        
        # 应用伤害
        target["health"] -= damage
        
        # 检查死亡
        if self._check_death(target):
            self._handle_death(target, game_state)
            
        return {
            "damage_dealt": damage,
            "target_status": target["health"]
        }
```

## 4. 规则模板系统

### 4.1 效果模板
```python
EFFECT_TEMPLATES = {
    "damage": {
        "template": "{value}点伤害",
        "parameters": ["value"],
        "resolution_steps": [
            "计算最终伤害值",
            "应用伤害",
            "检查死亡",
            "触发相关效果"
        ]
    },
    "heal": {
        "template": "恢复{value}点生命值",
        "parameters": ["value"],
        "resolution_steps": [
            "计算治疗量",
            "应用治疗",
            "触发相关效果"
        ]
    }
}
```

### 4.2 触发器模板
```python
TRIGGER_TEMPLATES = {
    "on_play": {
        "description": "在打出时",
        "timing": "play",
        "priority": 1
    },
    "on_death": {
        "description": "在死亡时",
        "timing": "death",
        "priority": 2
    }
}
```

## 5. 规则文本生成器

### 5.1 描述生成器
```python
class RuleTextGenerator:
    """规则文本生成器"""
    
    def generate_card_text(self, card: Card) -> str:
        """生成卡牌规则文本"""
        text_parts = []
        
        # 添加关键词
        if card.keywords:
            text_parts.append(self._generate_keyword_text(card.keywords))
            
        # 添加效果描述
        if card.effects:
            text_parts.append(self._generate_effect_text(card.effects))
            
        # 添加触发器描述
        if card.triggers:
            text_parts.append(self._generate_trigger_text(card.triggers))
            
        return " ".join(text_parts)
```

## 6. 使用示例

### 6.1 创建新卡牌
```python
# 创建卡牌实例
new_card = Card(
    id="CARD_004",
    name="元素使者",
    description="战吼：根据你的剩余法力值造成等量伤害",
    cost=5,
    card_type="creature",
    rarity="legendary",
    effects=[
        CardEffect(
            effect_type="damage",
            target_type="enemy_creature",
            value="remaining_mana",
            condition={"trigger": "battlecry"}
        )
    ],
    keywords=["battlecry"]
)

# 解析规则
rule_parser = RuleParser()
card_rules = rule_parser.parse_card_rules(new_card)

# 生成规则文本
text_generator = RuleTextGenerator()
card_text = text_generator.generate_card_text(new_card)
```

### 6.2 执行卡牌效果
```python
# 创建游戏状态
game_state = {
    "player": {
        "mana": 7,
        "remaining_mana": 2
    },
    "target": {
        "id": "enemy_1",
        "health": 5
    }
}

# 执行效果
effect_executor = EffectExecutor()
result = effect_executor.execute_effect(new_card.effects[0], game_state)
```

## 7. 最佳实践

### 7.1 规则定义原则
1. 保持规则清晰明确
2. 使用标准化的模板
3. 考虑规则间的互动
4. 注意边界情况

### 7.2 效果处理原则
1. 严格按步骤执行
2. 保持状态一致性
3. 处理所有异常情况
4. 记录效果执行过程

### 7.3 性能优化建议
1. 缓存常用规则解析结果
2. 优化效果处理流程
3. 减少不必要的状态更新
4. 使用高效的数据结构

这个规则系统设计提供了：
1. 完整的卡牌数据模型
2. 灵活的规则解析系统
3. 可扩展的效果处理系统
4. 标准化的规则模板
5. 清晰的文本生成器

您觉得这个规则系统设计如何？需要我详细解释某些部分吗？
