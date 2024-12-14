from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
from .card import Card

class GamePhase(Enum):
    DRAW = "draw"
    MAIN = "main"
    BATTLE = "battle"
    END = "end"

class PlayerType(Enum):
    HUMAN = "human"
    AI = "ai"

@dataclass
class Player:
    id: str
    type: PlayerType
    name: str
    life_points: int = 4000
    deck: List[Card] = None
    hand: List[Card] = None
    field: List[Card] = None
    graveyard: List[Card] = None

    def __post_init__(self):
        self.deck = self.deck or []
        self.hand = self.hand or []
        self.field = self.field or []
        self.graveyard = self.graveyard or []

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "life_points": self.life_points,
            "hand_size": len(self.hand),
            "field_cards": [card.to_dict() for card in self.field],
            "graveyard_size": len(self.graveyard)
        }

@dataclass
class GameState:
    current_player: Player
    opponent: Player
    current_phase: GamePhase
    turn_count: int = 1
    game_log: List[str] = None

    def __post_init__(self):
        self.game_log = self.game_log or []

    def to_dict(self) -> Dict:
        return {
            "current_player": self.current_player.to_dict(),
            "opponent": self.opponent.to_dict(),
            "current_phase": self.current_phase.value,
            "turn_count": self.turn_count,
            "last_actions": self.game_log[-5:] if self.game_log else []
        }

    def add_log(self, message: str):
        self.game_log.append(f"Turn {self.turn_count}: {message}")
