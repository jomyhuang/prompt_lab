"""游戏模型定义"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class CardType(str, Enum):
    """卡牌类型"""
    CREATURE = "creature"
    SPELL = "spell"
    ENCHANTMENT = "enchantment"
    ARTIFACT = "artifact"

class GamePhase(str, Enum):
    """游戏阶段"""
    START = "start"
    MAIN1 = "main1"
    COMBAT = "combat"
    MAIN2 = "main2"
    END = "end"

class Card(BaseModel):
    """卡牌基类"""
    card_id: str
    name: str
    type: CardType
    cost: Dict[str, int]
    text: str

class Creature(Card):
    """生物卡"""
    power: int
    toughness: int
    can_attack: bool = True
    damage_taken: int = 0

class Effect(BaseModel):
    """效果"""
    source_id: str
    effect_type: str
    target_ids: List[str]
    duration: Optional[int]

class Action(BaseModel):
    """行动"""
    action_type: str
    player_id: str
    source_id: str
    target_ids: List[str]
    timestamp: datetime

class PlayerState(BaseModel):
    """玩家状态"""
    player_id: str
    life: int = Field(default=20)
    mana: Dict[str, int] = Field(default_factory=lambda: {"total": 0, "current": 0})
    hand: List[Card] = Field(default_factory=list)
    deck: List[Card] = Field(default_factory=list)
    board: List[Card] = Field(default_factory=list)

class BoardState(BaseModel):
    """场面状态"""
    creatures: List[Creature] = Field(default_factory=list)
    enchantments: List[Card] = Field(default_factory=list)
    artifacts: List[Card] = Field(default_factory=list)

class GameState(BaseModel):
    """游戏状态"""
    game_id: str
    turn: int = Field(default=1)
    phase: GamePhase = Field(default=GamePhase.START)
    active_player: str
    players: Dict[str, PlayerState]
    board: BoardState = Field(default_factory=BoardState)
    stack: List[Effect] = Field(default_factory=list)
    history: List[Action] = Field(default_factory=list)
