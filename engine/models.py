"""
Core data models for the game.
"""

from dataclasses import dataclass, field
from typing import Optional
import random

from .dice import roll as roll_dice


# Default unarmed weapon — used when nothing is equipped
UNARMED = {
    "id": "__unarmed__",
    "name": "Fists",
    "type": "weapon",
    "damage_dice": "1d3",
    "damage_bonus": 0,
    "description": "Your bare hands.",
}


@dataclass
class Player:
    name: str
    hp: int = 100
    max_hp: int = 100
    attack: int = 10          # strength/skill modifier added to every weapon roll
    defense: int = 4
    gold: int = 15
    level: int = 1
    xp: int = 0
    xp_next: int = 100
    inventory: list = field(default_factory=list)
    equipped_weapon: Optional[dict] = field(default=None)

    # ------------------------------------------------------------------ #
    #  Combat                                                              #
    # ------------------------------------------------------------------ #

    def take_damage(self, raw_damage: int) -> int:
        """Apply incoming damage after defense. Returns actual damage taken."""
        actual = max(1, raw_damage - self.defense + random.randint(-1, 2))
        self.hp = max(0, self.hp - actual)
        return actual

    def deal_damage(self, enemy_defense: int) -> int:
        """
        Roll the equipped weapon's damage dice, add attack modifier and any
        weapon bonus, then subtract enemy defense. Minimum 1.
        """
        weapon = self.equipped_weapon or UNARMED
        dice = weapon.get("damage_dice", "1d4")
        bonus = weapon.get("damage_bonus", 0)
        rolled = roll_dice(dice)
        actual = max(1, self.attack + rolled + bonus - enemy_defense)
        return actual

    # ------------------------------------------------------------------ #
    #  Equipment                                                           #
    # ------------------------------------------------------------------ #

    def equip(self, item: dict):
        """Equip a weapon. The item remains in inventory."""
        self.equipped_weapon = item

    def unequip(self):
        """Revert to unarmed."""
        self.equipped_weapon = None

    # ------------------------------------------------------------------ #
    #  Health                                                              #
    # ------------------------------------------------------------------ #

    def heal(self, amount: int) -> int:
        """Returns amount actually healed."""
        actual = min(amount, self.max_hp - self.hp)
        self.hp += actual
        return actual

    # ------------------------------------------------------------------ #
    #  Progression                                                         #
    # ------------------------------------------------------------------ #

    def gain_xp(self, amount: int) -> bool:
        """Returns True if levelled up."""
        self.xp += amount
        if self.xp >= self.xp_next:
            self.level_up()
            return True
        return False

    def level_up(self):
        self.level += 1
        self.xp -= self.xp_next
        self.xp_next = int(self.xp_next * 1.5)
        self.max_hp += 15
        self.hp = self.max_hp
        self.attack += 2
        self.defense += 1

    # ------------------------------------------------------------------ #
    #  Inventory                                                           #
    # ------------------------------------------------------------------ #

    def add_item(self, item: dict):
        self.inventory.append(item)

    def remove_item(self, item_id: str) -> Optional[dict]:
        for i, item in enumerate(self.inventory):
            if item["id"] == item_id:
                return self.inventory.pop(i)
        return None

    def has_item(self, item_id: str) -> bool:
        return any(item["id"] == item_id for item in self.inventory)

    # ------------------------------------------------------------------ #
    #  Properties                                                          #
    # ------------------------------------------------------------------ #

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    @property
    def weapon_label(self) -> str:
        """Display string for the equipped weapon, e.g. 'Rusty Dagger (1d4)'."""
        w = self.equipped_weapon or UNARMED
        dice = w.get("damage_dice", "?")
        bonus = w.get("damage_bonus", 0)
        suffix = f"+{bonus}" if bonus > 0 else (f"{bonus}" if bonus < 0 else "")
        return f"{w['name']} ({dice}{suffix})"


@dataclass
class EnemyInstance:
    id: str
    name: str
    hp: int
    max_hp: int
    attack: int
    defense: int
    xp: int
    gold: int
    description: str       # from ## Description in enemy .md
    md_content: str = ""   # full .md for future AI use (combat commentary, etc.)
    damage_dice: str = "1d6"

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, raw_damage: int) -> int:
        actual = max(1, raw_damage - self.defense + random.randint(-1, 2))
        self.hp = max(0, self.hp - actual)
        return actual

    def deal_damage(self) -> int:
        rolled = roll_dice(self.damage_dice)
        return self.attack + rolled


@dataclass
class Room:
    id: str
    name: str
    description: str       # from ## Description in room .md — shown to player
    exits: dict            # direction -> room_id
    npc_ids: list
    enemy_ids: list
    item_ids: list
    md_content: str = ""   # full .md — passed to narrator for richer context
