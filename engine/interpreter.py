"""
Natural language command interpreter.
Falls back to this when the player's input doesn't match a known command.
Uses claude-haiku to map intent to a structured game action.
"""

from typing import Optional
from pydantic import BaseModel
from anthropic import Anthropic

from . import renderer as R

INTERPRETER_MODEL = "claude-haiku-4-5"


class InterpretedCommand(BaseModel):
    command: str   # look | go | talk | attack | flee | status | inventory | use | quests | help | quit | unknown
    args: str = ""


def interpret(
    raw_input: str,
    context: dict,
    client: Anthropic,
) -> Optional[InterpretedCommand]:
    """
    Map a free-form player input to a structured game command.
    Returns None on API error.
    """
    exits = ", ".join(context.get("exits", [])) or "none"
    npcs = ", ".join(context.get("npcs", [])) or "none"
    enemies = ", ".join(context.get("enemies", [])) or "none"
    inventory = ", ".join(context.get("inventory", [])) or "empty"

    system = f"""You are a command interpreter for a text-based RPG. Map the player's input to exactly one game command.

Current room: {context.get("room", "unknown")}
Exits: {exits}
People here: {npcs}
Enemies here: {enemies}
Player inventory: {inventory}

Available commands:
- look         → examine the room (also: describe, inspect, examine, look around, etc.)
- go <dir>     → move in a direction (exits: {exits})
- talk <name>  → speak to an NPC (people here: {npcs})
- attack <name>→ attack an enemy (enemies here: {enemies})
- flee         → escape from combat
- status       → show player stats
- inventory    → show inventory
- use <item>   → use an item
- quests       → show quest log
- help         → show help
- quit         → quit the game
- unknown      → if the input truly cannot map to any command

Return the single best matching command and any arguments. Be liberal in interpretation — "head downstairs" is "go down", "chat with the old woman" is "talk mira", "check my health" is "status"."""

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
