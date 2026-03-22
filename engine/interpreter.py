"""
Natural language command interpreter.
Falls back to this when the player's input doesn't match a known command.
Uses claude-haiku to classify intent and map to a structured game action.
"""

from typing import Optional
from pydantic import BaseModel
from anthropic import Anthropic

from . import renderer as R

INTERPRETER_MODEL = "claude-haiku-4-5"


class InterpretedCommand(BaseModel):
    command: str
    # look | go | talk | attack | flee | status | inventory | use | equip |
    # quests | help | quit | question | out_of_game
    args: str = ""


def interpret(
    raw_input: str,
    context: dict,
    client: Anthropic,
) -> Optional[InterpretedCommand]:
    """
    Classify a free-form player input and map it to a game command.

    command types:
      - A real game command  → execute it
      - "question"           → environmental/world question, send to narrator
      - "out_of_game"        → request has nothing to do with the game world
    """
    exits = ", ".join(context.get("exits", [])) or "none"
    npcs = ", ".join(context.get("npcs", [])) or "none"
    enemies = ", ".join(context.get("enemies", [])) or "none"
    inventory = ", ".join(context.get("inventory", [])) or "empty"

    system = f"""You are a command interpreter for a text-based RPG. Your job is to classify the player's input into exactly one of the categories below.

Current room: {context.get("room", "unknown")}
Exits: {exits}
People here: {npcs}
Enemies here: {enemies}
Player inventory: {inventory}

=== COMMAND MAPPING ===
Map actions, statements, and typos to the closest game command. Be very liberal:
  look         → examine / describe / inspect / look around / what's here
  go <dir>     → move / head / walk / go (direction from exits: {exits})
  talk <name>  → speak / chat / ask / approach (person from: {npcs})
  attack <name>→ fight / hit / strike / kill (enemy from: {enemies})
  flee         → run / escape / retreat
  status       → health / stats / how am I doing / check health
  inventory    → items / what do I have / pack / bag
  use <item>   → drink / eat / wield / equip / use (item from: {inventory})
  quests       → journal / missions / objectives
  help         → commands / what can I do
  quit         → exit / leave / goodbye

=== QUESTION vs COMMAND ===
If the input is a QUESTION about the game world, environment, or lore — return command "question".
Examples: "Is there anything on the wall?", "What does the tavern smell like?", "Is the cellar door locked?"

=== OUT OF GAME ===
If the input has nothing to do with the game world (asking for poems, math, real-world facts,
general conversation, system requests) — return command "out_of_game".
Examples: "Write me a poem", "What's 2+2?", "Tell me a joke", "Who wrote this game?"

=== AMBIGUOUS ACTIONS ===
If the player states an intent that maps loosely to a command, use the command.
"I would like to use my sword" → use sword
"Let's head downstairs" → go down
"I want to talk to the old woman" → talk mira"""

    try:
        response = client.messages.parse(
            model=INTERPRETER_MODEL,
            max_tokens=64,
            system=system,
            messages=[{"role": "user", "content": raw_input}],
            output_format=InterpretedCommand,
        )
    except Exception:
        return None

    return response.parsed_output
