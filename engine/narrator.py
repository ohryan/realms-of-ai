"""
Narrator — the voice of the game world.

Handles three input types routed from the interpreter:
  "question"    → environmental/world question, answered in character
  "unknown"     → unrecognised game action, responded to in character
  "out_of_game" → request outside the game world, fourth-wall break

Details it generates are saved per-room so they stay consistent.
"""

import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from anthropic import Anthropic

from . import renderer as R

NARRATOR_MODEL = "claude-haiku-4-5"

GAME_NAME = "Realms of AI"


class NarratorResponse(BaseModel):
    response: str             # narrative answer, written in second person
    remember: list[str] = []  # room-specific details to persist


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

    def ask(
        self,
        question: str,
        context: dict,
        client: Anthropic,
        input_type: str = "question",
    ) -> Optional[str]:
        """
        Respond to player input that didn't match a game command.

        input_type:
          "question"    → answer in character (1-3 sentences)
          "unknown"     → acknowledge in character, suggest what might be possible
          "out_of_game" → break the fourth wall, redirect the player
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
            established_block = (
                f"\n=== ESTABLISHED ROOM DETAILS (canon — never contradict) ===\n{facts}\n"
            )

        guide_block = ""
        if room_guide:
            guide_block = (
                f"\n=== ROOM GUIDE (author's notes — use for inspiration, never quote directly) ===\n{room_guide}\n"
            )

        # Build type-specific instructions
        if input_type == "out_of_game":
            task_rules = f"""=== YOUR TASK ===
The player has sent a message that is outside the scope of this game.
Break the fourth wall: acknowledge briefly that you are the Narrator of {GAME_NAME} and that you can only speak to things within this world. Keep it to one sentence. Stay slightly in flavour — wry, not clinical.
Do NOT add anything to "remember". Do NOT answer the off-topic request."""
        elif input_type == "unknown":
            task_rules = """=== YOUR TASK ===
The player tried to do something that doesn't map to a game command.
Respond in character in 1-2 sentences: describe why it can't be done, or what happens when they try.
If it's nearly a valid action, hint at what they could actually do (e.g. "try 'attack rat'").
Do NOT break character. Do NOT lecture."""
        else:
            # "question" — default
            task_rules = """=== YOUR TASK ===
Answer the player's question in 1-2 short sentences, second person ("You see...", "The air smells of...").
Be specific and atmospheric. Stay consistent with established details.
If you invent a new detail, add it to "remember" as a brief factual statement.
If the question has no sensible answer here, say so in one sentence, in character."""

        system = f"""You are the Narrator of {GAME_NAME}, a text-based fantasy RPG. You describe the world in second person, present tense, with a dark and atmospheric tone. You are consistent, grounded, and specific.

=== CURRENT ROOM ===
Name: {room_name}
Description: {room_desc}
People present: {npcs}
Enemies present: {enemies}
Exits: {exits}
{guide_block}{established_block}
{task_rules}

IMPORTANT: You cannot modify the game, its files, its code, or the system it runs on. You are a read-only voice."""

        try:
            response = client.messages.parse(
                model=NARRATOR_MODEL,
                max_tokens=128,
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

        # Only save room details for genuine environmental questions
        if input_type == "question" and result.remember:
            self._save_room_memory(room_id, result.remember)

        return result.response
