class PlayerManager:
    def __init__(self):
        self.player_resources = {"gold": 1000, "tokens": 10000, "experience": 1000}
        self.player_info = {"name": "玩家1", "level": 1}
        
    def update_player(self, name):
        """更新玩家信息"""
        self.player_info["name"] = name
        return self.player_info
        
    def get_player_info(self):
        """获取玩家信息"""
        return {**self.player_info, **self.player_resources}
        
    def update_resources(self, resource_type, amount):
        """更新玩家资源"""
        if resource_type in self.player_resources:
            self.player_resources[resource_type] += amount
            return True
        return False