"""
Persistent configuration — API key and player name.
Stored in data/config.json (gitignored).
"""

import json
from pathlib import Path

from engine import renderer as R


def load_api_key(base_dir: Path) -> str:
    """
    Returns the Anthropic API key using this priority:
      1. ANTHROPIC_API_KEY environment variable
      2. data/config.json (previously saved)
      3. Prompt the user and save for next time
    """
    import os

    config_path = base_dir / "data" / "config.json"

    # 1. Environment variable always wins
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if key:
        return key

    # 2. Saved config
    if config_path.exists():
        try:
            key = json.loads(config_path.read_text()).get("api_key", "").strip()
            if key:
                R.print_info("API key loaded from saved config.")
                return key
        except Exception:
            pass

    # 3. Prompt and save
    R.print_info("Enter your Anthropic API key:")
    key = input("  > ").strip()
    if key:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        # Merge with any existing config (e.g. player_name already saved)
        config = {}
        if config_path.exists():
            try:
                config = json.loads(config_path.read_text())
            except Exception:
                pass
        config["api_key"] = key
        config_path.write_text(json.dumps(config, indent=2))
        R.print_success("API key saved to data/config.json")

    return key


def load_player_name(base_dir: Path) -> str:
    """
    Returns the player's character name.
    Loads from data/config.json if previously saved; otherwise prompts.
    """
    config_path = base_dir / "data" / "config.json"
    config = {}

    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
        except Exception:
            pass

    name = config.get("player_name", "").strip()
    if name:
        R.print_info(f"Welcome back, {name}.")
        return name

    R.print_info("Enter your character's name:")
    name = input("  > ").strip() or "Stranger"

    config["player_name"] = name
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2))
    return name
