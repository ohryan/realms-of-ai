"""
NPC class with AI-powered conversation via Claude.
"""

import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from anthropic import Anthropic

from . import renderer as R

# Default model — haiku is fast/cheap for frequent NPC conversations.
# Players use their own API key, so cost matters.
NPC_MODEL = "claude-haiku-4-5"


class NPCAction(BaseModel):
    type: str  # start_quest | complete_quest | sell_item | give_item
    quest_id: Optional[str] = None
    item_id: Optional[str] = None
    value: Optional[int] = None  # gold price for sell_item


class NPCResponse(BaseModel):
    dialogue: str
    actions: list[NPCAction] = []
    end_conversation: bool = False
    remember: list[str] = []  # new facts to persist about this NPC across sessions


class NPC:
    def __init__(self, npc_id: str, data: dict, md_content: str, client: Anthropic, memory_dir: Path, game_facts: list[str] = None):
        self.id = npc_id
        self.name = data["name"]
        self.title = data.get("title", "")
        self.persuadability = data.get("persuadability", 5)
        self.md_content = md_content
        self.client = client
        self.history: list[dict] = []
        self.game_facts: list[str] = game_facts or []  # authoritative facts from world.json

        self.memory_dir = memory_dir
        self.memory: list[str] = self._load_memory()

    # ------------------------------------------------------------------ #
    #  Memory                                                              #
    # ------------------------------------------------------------------ #

    def _memory_path(self) -> Path:
        return self.memory_dir / f"{self.id}.json"

    def _load_memory(self) -> list[str]:
        path = self._memory_path()
        if path.exists():
            try:
                return json.loads(path.read_text())
            except Exception:
                return []
        return []

    def _save_memory(self, new_facts: list[str]):
        if not new_facts:
            return
        # Deduplicate: skip if an existing memory already covers this fact
        for fact in new_facts:
            fact = fact.strip()
            if fact and not any(m.lower() in fact.lower() for m in self.memory):
                self.memory.append(fact)

        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self._memory_path().write_text(json.dumps(self.memory, indent=2))

    def _game_facts_block(self) -> str:
        if not self.game_facts:
            return ""
        facts = "\n".join(f"- {f}" for f in self.game_facts)
        return f"\n=== GAME FACTS (authoritative — always use these exact values, never contradict them) ===\n{facts}\n"

    def _memory_block(self) -> str:
        if not self.memory:
            return ""
        facts = "\n".join(f"- {f}" for f in self.memory)
        return f"\n=== ESTABLISHED FACTS (canon — always use these, never contradict them) ===\n{facts}\n"

    # ------------------------------------------------------------------ #
    #  Prompt building                                                     #
    # ------------------------------------------------------------------ #

    def _persuade_note(self) -> str:
        p = self.persuadability
        if p <= 3:
            return (
                f"Your persuadability is {p}/10. "
                "You are very resistant to persuasion and negotiation. "
                "Hold firm on your positions unless the player makes an exceptionally compelling case."
            )
        elif p <= 6:
            return (
                f"Your persuadability is {p}/10. "
                "You are open to reasonable arguments but don't fold easily."
            )
        else:
            return (
                f"Your persuadability is {p}/10. "
                "You enjoy negotiation and are quite open to creative arguments and good stories."
            )

    def _build_system_prompt(self, world_state: dict) -> str:
        player = world_state["player"]
        room_name = world_state["room_name"]
        quest_summary = world_state.get("quest_summary", "(no quests)")

        return f"""You are {self.name} in a text-based fantasy RPG. Stay completely in character at all times. Never reveal you are an AI or break the fourth wall.

{self.md_content}
{self._game_facts_block()}{self._memory_block()}
=== CURRENT WORLD STATE ===
Player name: {player['name']}
Player level: {player['level']}
Player HP: {player['hp']}/{player['max_hp']}
Player gold: {player['gold']} gold
Current location: {room_name}

Quest status:
{quest_summary}

=== RESPONSE RULES ===
- "dialogue": What {self.name} says aloud. Keep it concise — 1 to 3 sentences max. Natural, in-character speech.
- "actions": Game actions to trigger. Only include when they fit naturally.
- "end_conversation": Set to true only when you (the character) are saying goodbye.
- "remember": Add a brief factual statement for anything worth remembering across sessions. This includes: personal facts you reveal about yourself, things the player told you, agreements or deals made, how the player treated you, or anything else that should colour future conversations. Only add things not already in Established Facts. Leave empty if nothing new came up.

=== ACTION TYPES ===
Only use action types listed in your Available Actions section.
- start_quest: Trigger when the player has clearly agreed to take a quest. Include quest_id.
- complete_quest: Trigger when acknowledging a completed quest. Include quest_id. If you negotiated a different reward amount with the player, include value (gold amount); otherwise omit it and the default reward is used.
- sell_item: Trigger when the player has clearly agreed to buy something. Include item_id and value (final price in gold after any negotiation).
- give_item: Trigger when giving something for free. Include item_id.

{self._persuade_note()}"""

    # ------------------------------------------------------------------ #
    #  Conversation                                                        #
    # ------------------------------------------------------------------ #

    def chat(self, player_message: str, world_state: dict, game) -> Optional[NPCResponse]:
        """Send a message to this NPC and get a response. Returns None on API error."""
        self.history.append({"role": "user", "content": player_message})

        try:
            response = self.client.messages.parse(
                model=NPC_MODEL,
                max_tokens=512,
                system=self._build_system_prompt(world_state),
                messages=list(self.history),
                output_format=NPCResponse,
            )
        except Exception as e:
            R.print_error(f"API error: {e}")
            self.history.pop()
            return None

        npc_resp = response.parsed_output
        if npc_resp is None:
            R.print_error("The NPC seems lost in thought... (failed to parse response)")
            self.history.pop()
            return None

        # Persist any new facts the NPC revealed
        if npc_resp.remember:
            self._save_memory(npc_resp.remember)

        # Store dialogue only in history (not raw JSON)
        self.history.append({"role": "assistant", "content": npc_resp.dialogue})

        return npc_resp

    def display_name(self) -> str:
        return f"{self.name}" + (f" {self.title}" if self.title else "")
