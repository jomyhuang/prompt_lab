from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

class CardType(Enum):
    MONSTER = "monster"
    SPELL = "spell"
    TRAP = "trap"

class CardAttribute(Enum):
    FIRE = "fire"
    WATER = "water"
    EARTH = "earth"
    WIND = "wind"
    LIGHT = "light"
    DARK = "dark"

@dataclass
class Card:
    id: str
    name: str
    type: CardType
    description: str
    cost: int
    attribute: Optional[CardAttribute] = None
    attack: Optional[int] = None
    defense: Optional[int] = None
    level: Optional[int] = None
    effects: List[str] = None

    def __post_init__(self):
        if self.effects is None:
            self.effects = []

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "cost": self.cost,
            "attribute": self.attribute.value if self.attribute else None,
            "attack": self.attack,
            "defense": self.defense,
            "level": self.level,
            "effects": self.effects
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Card':
        return cls(
            id=data["id"],
            name=data["name"],
            type=CardType(data["type"]),
            description=data["description"],
            cost=data.get("cost", 0),
            attribute=CardAttribute(data["attribute"]) if data.get("attribute") else None,
            attack=data.get("attack"),
            defense=data.get("defense"),
            level=data.get("level"),
            effects=data.get("effects", [])
        )
