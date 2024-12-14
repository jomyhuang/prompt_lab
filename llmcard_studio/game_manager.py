class GameManager:
    def __init__(self):
       self.game_state = {"player_health": 100, "opponent_health": 100, "turn": "player", "log":[]}

    def start_turn(self):
        if self.game_state["turn"] == "player":
            self.game_state["turn"] = "opponent"
            ai_action = self.ai_action()
            return ai_action
        else:
            self.game_state["turn"] = "player"
            return None

    def process_action(self, action):
        """处理玩家或AI的动作"""
        try:
            # 尝试解析JSON格式的动作
            if isinstance(action, str):
                import json
                try:
                    action = json.loads(action)
                except json.JSONDecodeError:
                    # 如果不是JSON格式，使用旧的处理方式
                    if "attack" in action and action.split("attack")[1].strip().isdigit():
                        damage = int(action.split("attack")[1].strip())
                        return self._process_attack(damage)
                    return None

            # 处理JSON格式的动作
            if isinstance(action, dict):
                action_type = action.get("action", "").lower()
                if action_type == "attack":
                    damage = action.get("parameters", {}).get("damage", 10)
                    return self._process_attack(damage)
                elif action_type == "heal":
                    heal_amount = action.get("parameters", {}).get("amount", 5)
                    return self._process_heal(heal_amount)
            
            return None
        except Exception as e:
            self.game_state["log"].append(f"错误：{str(e)}")
            return f"发生错误：{str(e)}"

    def _process_attack(self, damage):
        """处理攻击动作"""
        if self.game_state["turn"] == "player":
            self.game_state["opponent_health"] -= damage
            self.game_state["log"].append(f"玩家攻击，造成 {damage}点伤害")
            return f"玩家攻击，造成{damage}点伤害"
        else:
            self.game_state["player_health"] -= damage
            self.game_state["log"].append(f"AI攻击，造成 {damage}点伤害")
            return f"AI攻击，造成{damage}点伤害"

    def _process_heal(self, amount):
        """处理治疗动作"""
        if self.game_state["turn"] == "player":
            self.game_state["player_health"] = min(100, self.game_state["player_health"] + amount)
            self.game_state["log"].append(f"玩家治疗，恢复 {amount}点生命")
            return f"玩家治疗，恢复{amount}点生命"
        else:
            self.game_state["opponent_health"] = min(100, self.game_state["opponent_health"] + amount)
            self.game_state["log"].append(f"AI治疗，恢复 {amount}点生命")
            return f"AI治疗，恢复{amount}点生命"

    def ai_action(self):
        """AI的行动逻辑"""
        if self.game_state["opponent_health"] > 50:
            return self.process_action({"action": "attack", "parameters": {"damage": 10}})
        else:
            return self.process_action({"action": "attack", "parameters": {"damage": 5}})

    def check_win(self):
        if self.game_state["player_health"] <= 0:
            return "opponent"
        if self.game_state["opponent_health"] <= 0:
            return "player"
        return None
