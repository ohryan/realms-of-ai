"""
Narrator — the voice of the game world.
Handles freeform environmental questions from the main prompt.
Details it generates are saved per-room so they stay consistent.
"""

import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from anthropic import Anthropic

from . import renderer as R

NARRATOR_MODEL = "claude-haiku-4-5"


class NarratorResponse(BaseModel):
    response: str           # the narrative answer, written in second person
    remember: list[str] = []  # room-specific details to persist (e.g. "A faded wanted poster hangs on the east wall")


class Narrator:
    def __init__(self, memory_dir: Path):
        self.memory_dir = memory_dir
        self._cache: dict[str, list[str]] = {}  # room_id -> loaded facts

    # ------------------------------------------------------------------ #
    #  Memory                                                              #
    # ------------------------------------------------------------------ #

    def _room_memory_path(self, room_id: str) -> Path:
        return self.memory_dir / "rooms" / f"{room_id}.json"

    def _load_room_memory(self, room_id: str) -> list[str]:
        if room_id in self._cache:
            return self._cache[room_id]
        path = self._room_memory_path(room_id)
        if path.exists():
            try:
                facts = json.loads(path.read_text())
                self._cache[room_id] = facts
                return facts
            except Exception:
                pass
        self._cache[room_id] = []
        return []

    def _save_room_memory(self, room_id: str, new_facts: list[str]):
        if not new_facts:
            return
        existing = self._load_room_memory(room_id)
        for fact in new_facts:
            fact = fact.strip()
            if fact and not any(fact.lower() in e.lower() for e in existing):
                existing.append(fact)
        self._cache[room_id] = existing
        path = self._room_memory_path(room_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(existing, indent=2))

    # ------------------------------------------------------------------ #
    #  Narration                                                           #
    # ------------------------------------------------------------------ #

    def ask(self, question: str, context: dict, client: Anthropic) -> Optional[str]:
        """
        Answer an environmental question in the voice of the game world.
        Returns the narrative response string, or None on error.
        """
        room_id = context.get("room_id", "unknown")
        room_name = context.get("room_name", "Unknown")
        room_desc = context.get("room_description", "")
        room_guide = context.get("room_guide", "")
        npcs = ", ".join(context.get("npcs", [])) or "none"
        enemies = ", ".join(context.get("enemies", [])) or "none"
        exits = ", ".join(context.get("exits", [])) or "none"

        established = self._load_room_memory(room_id)
        established_block = ""
        if established:
            facts = "\n".join(f"- {f}" for f in established)
            established_block = f"\n=== ESTABLISHED ROOM DETAILS (canon — never contradict) ===\n{facts}\n"

        guide_block = ""
        if room_guide:
            guide_block = f"\n=== ROOM GUIDE (author's notes — use for inspiration, never quote directly) ===\n{room_guide}\n"

        system = f"""You are the narrator of a text-based fantasy RPG. You describe the world in second person, present tense, with a dark and atmospheric tone. You are consistent, grounded, and specific. You do not invent things that contradict the room's established description.

=== CURRENT ROOM ===
Name: {room_name}
Description: {room_desc}
People present: {npcs}
Enemies present: {enemies}
Exits: {exits}
{guide_block}{established_block}
=== RULES ===
- Answer in 1-3 sentences, second person ("You see...", "The wall is...").
- Be specific and atmospheric. Draw on the room guide's atmosphere and secrets when relevant.
- Stay consistent with the room description and any established details.
- If you invent a specific detail (a name carved in wood, a stain on the floor, a smell), add it to "remember" as a brief factual statement so it persists.
- If the question has no sensible answer in this room, say so briefly and in character."""

        try:
            response = client.messages.parse(
                model=NARRATOR_MODEL,
                max_tokens=256,
                system=system,
                messages=[{"role": "user", "content": question}],
                output_format=NarratorResponse,
            )
        except Exception as e:
            R.print_error(f"API error: {e}")
            return None

        result = response.parsed_output
        if result is None:
            return None

        if result.remember:
            self._save_room_memory(room_id, result.remember)

        return result.response
