"""
Save / load game state.

What's saved:
  - Player stats, inventory, equipped weapon
  - Current room
  - Quest statuses

What's NOT saved (persisted separately):
  - NPC memories  → data/modules/<id>/memory/<npc>.json
  - Room memories → data/modules/<id>/memory/rooms/<room>.json

Save file location: data/modules/<module_id>/save.json
"""

import json
from pathlib import Path
from typing import Optional

from .models import Player

SAVE_VERSION = 1


def save_game(
    save_path: Path,
    player: Player,
    current_room_id: str,
    quest_statuses: dict,
) -> bool:
    """Write the current game state to disk. Returns True on success."""
    data = {
        "version": SAVE_VERSION,
        "current_room_id": current_room_id,
        "quests": quest_statuses,
        "player": {
            "name": player.name,
            "hp": player.hp,
            "max_hp": player.max_hp,
            "attack": player.attack,
            "defense": player.defense,
            "gold": player.gold,
            "level": player.level,
            "xp": player.xp,
            "xp_next": player.xp_next,
            "inventory": player.inventory,
            "equipped_weapon": player.equipped_weapon,
        },
    }
    try:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text(json.dumps(data, indent=2))
        return True
    except Exception:
        return False


def load_game(save_path: Path) -> Optional[dict]:
    """
    Load a save file. Returns the raw dict, or None if there's nothing to load.
    Silently discards saves from incompatible versions.
    """
    if not save_path.exists():
        return None
    try:
        data = json.loads(save_path.read_text())
        if data.get("version") != SAVE_VERSION:
            return None
        return data
    except Exception:
        return None


def restore_player(save_data: dict) -> Player:
    """Reconstruct a Player instance from saved data."""
    pd = save_data["player"]
    return Player(
        name=pd["name"],
        hp=pd["hp"],
        max_hp=pd["max_hp"],
        attack=pd["attack"],
        defense=pd["defense"],
        gold=pd["gold"],
        level=pd["level"],
        xp=pd["xp"],
        xp_next=pd["xp_next"],
        inventory=pd.get("inventory", []),
        equipped_weapon=pd.get("equipped_weapon"),
    )


def delete_save(save_path: Path):
    """Remove a save file (e.g. on player death)."""
    try:
        save_path.unlink(missing_ok=True)
    except Exception:
        pass
