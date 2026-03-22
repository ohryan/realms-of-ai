"""
Module discovery, selection, and world initialisation helpers.
"""

import json
import sys
from pathlib import Path

from engine import renderer as R
from engine.md_utils import extract_section, load_md


def select_module(base_dir: Path) -> dict:
    """
    Scans data/modules/ for valid modules and returns the chosen one as a dict:
      { "id": str, "path": Path, "name": str, "description": str, "author": str }

    If only one module exists it is selected automatically.
    If multiple exist the player is shown a menu.
    """
    modules_dir = base_dir / "data" / "modules"
    modules = []

    for path in sorted(modules_dir.iterdir()):
        if not path.is_dir():
            continue
        world_path = path / "world.json"
        if not world_path.exists():
            continue

        meta = {}
        meta_path = path / "module.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text())
            except Exception:
                pass

        modules.append({
            "id": path.name,
            "path": path,
            "name": meta.get("name", path.name),
            "description": meta.get("description", ""),
            "author": meta.get("author", ""),
        })

    if not modules:
        R.print_error("No modules found in data/modules/. Exiting.")
        sys.exit(1)

    if len(modules) == 1:
        chosen = modules[0]
        R.print_info(f"Loading module: {chosen['name']}")
        R.print_separator()
        return chosen

    # Multiple modules — show a menu
    print()
    R.print_separator()
    print(f"  {R.BOLD}{R.BRIGHT_WHITE}SELECT A MODULE{R.RESET}")
    R.print_separator()

    for i, m in enumerate(modules, 1):
        print(f"\n  {R.BRIGHT_CYAN}[{i}]{R.RESET} {R.BRIGHT_WHITE}{m['name']}{R.RESET}")
        if m["description"]:
            print(f"      {R.DIM}{R.WHITE}{m['description']}{R.RESET}")
        if m["author"]:
            print(f"      {R.DIM}by {m['author']}{R.RESET}")

    print()
    while True:
        try:
            raw = input(f"  {R.BRIGHT_WHITE}Choose [1-{len(modules)}]: {R.RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(modules):
                R.print_separator()
                return modules[idx]
        except ValueError:
            pass
        R.print_error(f"Enter a number between 1 and {len(modules)}.")


def build_npc_facts(npc_id: str, world_data: dict, module_dir: Path) -> list[str]:
    """
    Build a list of authoritative game-facts for an NPC, derived from world.json.
    These are injected into the NPC's system prompt so Claude always knows
    canonical prices, quest rewards, etc.
    """
    facts = []

    for qid, qdef in world_data.get("quests", {}).items():
        if qdef.get("complete_npc") == npc_id:
            reward = qdef.get("reward", {})
            gold = reward.get("gold", 0)
            xp = reward.get("xp", 0)
            facts.append(
                f"You promised {gold} gold as the reward for the quest \"{qdef['name']}\" "
                f"(quest id: {qid}). This is the default; you may negotiate, but be aware "
                f"of your persuadability score."
            )
        if qdef.get("giver_npc") == npc_id:
            facts.append(
                f"You are the one who offers the quest \"{qdef['name']}\" (quest id: {qid})."
            )

    npc_md_path = module_dir / "npcs" / world_data["npcs"][npc_id]["file"]
    npc_md_text = load_md(npc_md_path)

    for item_id, item in world_data.get("items", {}).items():
        if item_id in npc_md_text:
            # Load description from item's .md file, fall back to inline field
            item_md = load_md(module_dir / "items" / item.get("file", ""))
            description = extract_section(item_md, "Description") or item.get("description", item["name"])
            price = item.get("base_price", 0)
            facts.append(
                f"You sell: {item['name']} (item_id: \"{item_id}\") — {description} "
                f"Base price: {price} gold."
            )

    return facts
