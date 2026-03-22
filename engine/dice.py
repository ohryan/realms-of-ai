"""
Dice notation parser and roller.

Supports standard RPG notation:
  "1d6"     — roll one six-sided die
  "2d8"     — roll two eight-sided dice and sum
  "1d6+2"   — roll 1d6, add 2
  "2d4-1"   — roll 2d4, subtract 1

Valid die sizes: 2, 3, 4, 6, 8, 10, 12, 20, 100
"""

import random
import re

_PATTERN = re.compile(r"^(\d+)d(\d+)([+-]\d+)?$", re.IGNORECASE)

VALID_SIDES = {2, 3, 4, 6, 8, 10, 12, 20, 100}


def roll(notation: str) -> int:
    """
    Parse and roll a dice notation string. Returns the total as an integer.
    Raises ValueError if the notation is invalid.
    """
    m = _PATTERN.match(notation.strip())
    if not m:
        raise ValueError(f"Invalid dice notation: '{notation}'")

    num_dice = int(m.group(1))
    sides = int(m.group(2))
    modifier = int(m.group(3)) if m.group(3) else 0

    if num_dice < 1:
        raise ValueError(f"Must roll at least 1 die: '{notation}'")
    if sides not in VALID_SIDES:
        raise ValueError(f"Unsupported die size d{sides}. Valid: {sorted(VALID_SIDES)}")

    total = sum(random.randint(1, sides) for _ in range(num_dice)) + modifier
    return max(0, total)  # floor at 0; caller applies their own floor


def describe(notation: str) -> str:
    """Human-readable label, e.g. '2d6+1' → '2d6+1'."""
    return notation.strip()
