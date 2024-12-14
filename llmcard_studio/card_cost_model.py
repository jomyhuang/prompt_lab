class CardCostModel:
    def __init__(self):
        self.attack_base_cost = 1
        self.defense_base_cost = 1
        self.health_base_cost = 0.5
        self.mana_base_cost = 0.5
        self.damage_base_cost = 0.1
        self.effect_base_cost = 1.0
        self.resource_base_cost = 0.7
        self.attributes_weight = 0.5
        self.effects_weight = 0.6
        self.rules_weight = 0.7
        self.card_type_base_costs = {
            "Monster": {"CreationTokenCost": 100, "RuleCalculationTokenCost": 50, "ResourceCost": 0},
            "Spell": {"CreationTokenCost": 150, "RuleCalculationTokenCost": 150, "ResourceCost": 100},
            "Trap": {"CreationTokenCost": 200, "RuleCalculationTokenCost": 200, "ResourceCost": 50},
        }
        self.max_attack = 100
        self.max_defense = 100
        self.max_health = 200
        self.max_mana_cost = 10

    def calculate_difficulty_score(self, card, ai_cost=0):
        total_cost = 0
        attribute_cost = 0
        effect_cost = 0
        resource_cost = 0
        tokens_cost = 0
        card_type = card.get("type","Monster")

        if card_type in self.card_type_base_costs:
            tokens_cost = self.card_type_base_costs[card_type]["CreationTokenCost"] + self.card_type_base_costs[card_type]["RuleCalculationTokenCost"]
            resource_cost = self.card_type_base_costs[card_type]["ResourceCost"]
        attribute_cost += card.get("attack",0) * self.attack_base_cost
        attribute_cost += card.get("defense", 0) * self.defense_base_cost
        attribute_cost += card.get("health",0) * self.health_base_cost
        attribute_cost += card.get("mana_cost",0) * self.mana_base_cost

        effects = card.get("effects", [])

        for effect in effects:
            effect_type = effect.get("type")
            if effect_type == "吸血":
               effect_cost += card.get("attack",0) * self.effect_base_cost
            elif effect_type == "伤害":
               effect_cost += effect.get("damage", 0) * self.damage_base_cost

        total_cost = attribute_cost + effect_cost + resource_cost
        total_token_cost = tokens_cost
        total_card_cost = total_cost + total_token_cost + ai_cost

        total_attributes_value = 0
        total_attributes_value += card.get("attack",0)
        total_attributes_value +=  card.get("defense", 0)
        total_attributes_value +=  card.get("health",0)
        total_attributes_value += card.get("mana_cost",0)
        total_effects_value = 0
        for effect in effects:
             effect_type = effect.get("type")
             if effect_type == "吸血":
                total_effects_value += card.get("attack", 0)
             elif effect_type == "伤害":
                  total_effects_value +=  effect.get("damage", 0)

        total_rules_value = 0

        difficulty_score = total_card_cost + total_attributes_value * self.attributes_weight + total_effects_value * self.effects_weight + total_rules_value * self.rules_weight
        return difficulty_score
