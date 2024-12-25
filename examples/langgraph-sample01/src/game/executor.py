"""游戏执行器"""
from typing import Dict, Any
from .models import GameState, PlayerState, BoardState, Card
from .graphs import create_game_graph, create_combat_graph

class GameExecutor:
    """游戏执行器"""
    
    def __init__(self):
        self.game_graph = create_game_graph()
        self.combat_graph = create_combat_graph()
        
    async def execute_game(self, initial_state: GameState) -> GameState:
        """执行游戏"""
        app = self.game_graph.compile()
        final_state = await app.ainvoke(initial_state)
        return final_state
    
    async def execute_combat(self, combat_state: GameState) -> GameState:
        """执行战斗"""
        app = self.combat_graph.compile()
        final_state = await app.ainvoke(combat_state)
        return final_state
    
    @staticmethod
    def create_initial_state(player1_deck: list[Card], player2_deck: list[Card]) -> GameState:
        """创建初始游戏状态"""
        return GameState(
            game_id="GAME_001",
            turn=1,
            phase="start",
            active_player="P1",
            players={
                "P1": PlayerState(
                    player_id="P1",
                    deck=player1_deck,
                    hand=player1_deck[:7],  # 起始手牌
                ),
                "P2": PlayerState(
                    player_id="P2",
                    deck=player2_deck,
                    hand=player2_deck[:7],  # 起始手牌
                ),
            },
            board=BoardState(),
            stack=[],
            history=[]
        )
