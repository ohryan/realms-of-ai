"""
World state: rooms, enemies, items, quests. Loaded from world.json + per-section .md files.
"""

from pathlib import Path

from .models import Room, EnemyInstance
from .md_utils import extract_section, load_md


class World:
    def __init__(self, data: dict, module_dir: Path = None):
        self._raw = data
        self._module_dir = module_dir

        # Build rooms
        self.rooms: dict[str, Room] = {}
        for room_id, rd in data["rooms"].items():
            md_content = self._load_section_md("rooms", rd.get("file", ""))
            description = (
                extract_section(md_content, "Description")
                or rd.get("description", "")
            )
            self.rooms[room_id] = Room(
                id=room_id,
                name=rd["name"],
                description=description,
                exits=rd.get("exits", {}),
                npc_ids=rd.get("npcs", []),
                enemy_ids=list(rd.get("enemies", [])),
                item_ids=list(rd.get("items", [])),
                md_content=md_content,
            )

        # Build enemy instances (mutable, can be killed)
        self.enemies: dict[str, EnemyInstance] = {}
        for eid, ed in data["enemies"].items():
            md_content = self._load_section_md("enemies", ed.get("file", ""))
            description = (
                extract_section(md_content, "Description")
                or ed.get("description", "")
            )
            self.enemies[eid] = EnemyInstance(
                id=eid,
                name=ed["name"],
                hp=ed["hp"],
                max_hp=ed["max_hp"],
                attack=ed["attack"],
                defense=ed["defense"],
                xp=ed["xp"],
                gold=ed["gold"],
                description=description,
                md_content=md_content,
                damage_dice=ed.get("damage_dice", "1d6"),
            )

        # Item templates — description injected from .md if available
        raw_items = data.get("items", {})
        self.item_templates: dict[str, dict] = {}
        for item_id, item in raw_items.items():
            entry = dict(item)
            md_content = self._load_section_md("items", item.get("file", ""))
            if md_content:
                desc = extract_section(md_content, "Description")
                if desc:
                    entry["description"] = desc
                entry["md_content"] = md_content
            self.item_templates[item_id] = entry

        # Quest definitions — description injected from .md if available
        raw_quests = data.get("quests", {})
        self.quest_defs: dict[str, dict] = {}
        for qid, qdef in raw_quests.items():
            entry = dict(qdef)
            md_content = self._load_section_md("quests", qdef.get("file", ""))
            if md_content:
                desc = extract_section(md_content, "Description")
                if desc:
                    entry["description"] = desc
                entry["md_content"] = md_content
            self.quest_defs[qid] = entry

        # NPC definitions
        self.npc_defs: dict[str, dict] = data.get("npcs", {})

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _load_section_md(self, subdir: str, filename: str) -> str:
        """Load a .md file from module_dir/<subdir>/<filename>."""
        if not self._module_dir or not filename:
            return ""
        return load_md(self._module_dir / subdir / filename)

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def get_room(self, room_id: str) -> Room:
        return self.rooms[room_id]

    def alive_enemies_in_room(self, room_id: str) -> list[EnemyInstance]:
        room = self.rooms[room_id]
        return [
            self.enemies[eid]
            for eid in room.enemy_ids
            if eid in self.enemies and self.enemies[eid].is_alive
        ]

    def all_enemies_dead_in_room(self, room_id: str) -> bool:
        room = self.rooms[room_id]
        enemy_ids = [eid for eid in room.enemy_ids if eid in self.enemies]
        if not enemy_ids:
            return True
        return all(not self.enemies[eid].is_alive for eid in enemy_ids)

    def get_item_template(self, item_id: str) -> dict:
        return self.item_templates.get(item_id, {})

    def resolve_item_id(self, raw: str) -> str | None:
        """
        Map what an NPC returned to a real item_id.
        Tries exact match first, then case-insensitive name/id match.
        Returns the canonical item_id, or None if nothing matches.
        """
        if not raw:
            return None
        # 1. Exact match
        if raw in self.item_templates:
            return raw
        # 2. Case-insensitive id or name match
        raw_l = raw.lower().replace(" ", "_")
        for iid, item in self.item_templates.items():
            if iid.lower() == raw_l:
                return iid
            if item.get("name", "").lower() == raw.lower():
                return iid
        # 3. Slug match (e.g. "Healing Potion" → "healing_potion")
        slug = raw.lower().replace(" ", "_")
        if slug in self.item_templates:
            return slug
        return None
