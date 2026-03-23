#!/usr/bin/env python3
"""
Realms of AI — A text-based adventure with AI-powered NPCs.
Each NPC is driven by Claude (claude-haiku-4-5 by default).
NPC behaviours, personalities, and available actions are defined in data/modules/<id>/npcs/*.md
"""

import json
import sys
from pathlib import Path

from anthropic import Anthropic

from engine import renderer as R
from engine.models import Player
from engine.world import World
from engine.npc import NPC
from engine.quest import QuestManager, COMPLETE
from engine.interpreter import interpret
from engine.narrator import Narrator
from engine.config import load_api_key, load_player_name
from engine.loader import select_module, build_npc_facts
from engine.commands import CommandsMixin
from engine.save import save_game, load_game, restore_player, delete_save


BASE_DIR = Path(__file__).parent


class Game(CommandsMixin):
    def __init__(self):
        self.running = True
        self.player: Player = None
        self.world: World = None
        self.npcs: dict[str, NPC] = {}
        self.quests: QuestManager = None
        self.client: Anthropic = None
        self.current_room_id: str = None
        self.narrator: Narrator = None
        self.module_id: str = None
        self.module_dir: Path = None
        self.save_path: Path = None

    # ------------------------------------------------------------------ #
    #  Startup                                                             #
    # ------------------------------------------------------------------ #

    def start(self):
        R.print_title()

        api_key = load_api_key(BASE_DIR)
        if not api_key:
            R.print_error("No API key provided. Exiting.")
            sys.exit(1)

        self.client = Anthropic(api_key=api_key)

        name = load_player_name(BASE_DIR)

        module = select_module(BASE_DIR)
        self.module_id = module["id"]
        self.module_dir = module["path"]
        self.save_path = self.module_dir / "save.json"

        # Load world
        world_data = json.loads((self.module_dir / "world.json").read_text())
        self.world = World(world_data, module_dir=self.module_dir)
        self.quests = QuestManager(self.world.quest_defs)

        memory_dir = self.module_dir / "memory"
        self.narrator = Narrator(memory_dir=memory_dir)

        # Load NPCs
        npcs_dir = self.module_dir / "npcs"
        for npc_id, npc_def in world_data["npcs"].items():
            md_path = npcs_dir / npc_def["file"]
            if not md_path.exists():
                R.print_warning(f"NPC file not found: {md_path}")
                continue
            self.npcs[npc_id] = NPC(
                npc_id=npc_id,
                data=npc_def,
                md_content=md_path.read_text(),
                client=self.client,
                memory_dir=memory_dir,
                game_facts=build_npc_facts(npc_id, world_data, self.module_dir),
            )

        # Check for a saved game
        save_data = load_game(self.save_path)
        if save_data:
            saved_name = save_data["player"]["name"]
            R.print_separator()
            R.print_info(f"A saved game was found for {R.BRIGHT_WHITE}{saved_name}{R.RESET}.")
            try:
                choice = input(
                    f"  {R.BRIGHT_WHITE}Continue saved game? (y/n): {R.RESET}"
                ).strip().lower()
            except (EOFError, KeyboardInterrupt):
                choice = "n"

            if choice in ("y", "yes", ""):
                self.player = restore_player(save_data)
                self.current_room_id = save_data["current_room_id"]
                self.quests.status = save_data["quests"]
                R.print_separator()
                R.print_success(f"Welcome back, {self.player.name}. Your adventure continues.")
                R.print_separator()
            else:
                self._start_new_game(name, world_data)
        else:
            self._start_new_game(name, world_data)

        print()
        self._look()

        while self.running and self.player.is_alive:
            self._tick()

        if not self.player.is_alive:
            # Player died — wipe the save so they can't reload into a dead state
            delete_save(self.save_path)

    def _start_new_game(self, name: str, world_data: dict):
        """Initialise a fresh player and apply the module's starting inventory."""
        self.player = Player(name=name)
        self.current_room_id = world_data["start_room"]
        for item_id in world_data.get("player_start", {}).get("inventory", []):
            template = self.world.get_item_template(item_id)
            if template:
                item = dict(template)
                self.player.add_item(item)
                if item.get("type") == "weapon" and self.player.equipped_weapon is None:
                    self.player.equip(item)
        R.print_separator()
        R.print_success(f"Welcome, {name}. Your adventure begins.")
        R.print_separator()

    # ------------------------------------------------------------------ #
    #  Main loop                                                           #
    # ------------------------------------------------------------------ #

    def _tick(self):
        R.print_status_bar(self.player)
        try:
            raw = input(f"{R.BRIGHT_WHITE}> {R.RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            self._do_save()
            self.running = False
            return

        if not raw:
            return

        parts = raw.split(None, 1)
        cmd = parts[0].lower()
        args = parts[1].strip() if len(parts) > 1 else ""

        match cmd:
            case "look" | "l":
                self._look()
            case "go" | "move" | "walk" | "n" | "s" | "e" | "w" | "u" | "d" | "up" | "down" | "north" | "south" | "east" | "west":
                self._go(args if args else cmd)
            case "talk" | "t" | "speak":
                self._talk(args)
            case "attack" | "a" | "fight" | "kill":
                self._attack(args)
            case "status" | "stats" | "s":
                self._status()
            case "inventory" | "inv" | "i":
                self._inventory()
            case "use":
                self._use(args)
            case "equip" | "wield" | "wear":
                self._use(args)  # _use routes weapons to _equip_weapon
            case "quests" | "q" | "journal":
                self.quests.show()
            case "memory" | "mem":
                self._show_memory(args)
            case "help" | "h" | "?":
                R.print_help()
            case "quit" | "exit" | "bye":
                self._do_save()
                R.print_info("Farewell, adventurer. Your progress has been saved.")
                self.running = False
            case _:
                self._interpret_and_run(raw)

    # ------------------------------------------------------------------ #
    #  Conversation                                                        #
    # ------------------------------------------------------------------ #

    def _conversation_loop(self, npc: "NPC"):
        display = npc.display_name()
        print()
        R.print_separator(R.BRIGHT_YELLOW)
        print(f"  {R.BRIGHT_YELLOW}Talking to: {display}{R.RESET}")
        R.print_separator(R.BRIGHT_YELLOW)
        R.print_info("Type your message. Type 'bye' to end the conversation.")

        max_turns = 20
        turn = 0

        while turn < max_turns:
            try:
                player_msg = input(f"\n  {R.BRIGHT_WHITE}[You]: {R.RESET}").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not player_msg:
                continue

            if player_msg.lower() in ("bye", "goodbye", "exit", "leave", "farewell"):
                R.print_player_say(player_msg)
                print()
                R.print_info(f"You end the conversation with {npc.name}.")
                break

            world_state = self._build_world_state()
            with R.thinking():
                npc_resp = npc.chat(player_msg, world_state, self)

            if npc_resp is None:
                break

            R.print_npc_say(npc.name, npc_resp.dialogue)

            for action in npc_resp.actions:
                self._process_npc_action(action, npc)

            turn += 1

            if npc_resp.end_conversation:
                print()
                R.print_info(f"The conversation with {npc.name} ends.")
                break

        print()
        R.print_separator(R.BRIGHT_YELLOW)

        # Fallback: if Claude forgot to fire complete_quest, give the reward anyway.
        self._auto_complete_quests(npc)

    def _auto_complete_quests(self, npc: "NPC"):
        for qid, qdef in self.quests.defs.items():
            if qdef.get("complete_npc") != npc.id:
                continue
            if self.quests.is_complete(qid):
                self.quests.give_reward(qid, self.player)
                R.print_quest_update(f"Quest complete: {qdef['name']}")

    def _process_npc_action(self, action, npc: "NPC"):
        t = action.type

        if t == "start_quest":
            qid = action.quest_id
            if qid and qid in self.quests.defs:
                self.quests.start(qid)

        elif t == "complete_quest":
            qid = action.quest_id
            if qid and qid in self.quests.defs:
                if self.quests.status.get(qid) in ("complete", "active"):
                    self.quests.status[qid] = COMPLETE
                    gold_override = action.value  # NPC can pass a negotiated amount
                    result = self.quests.give_reward(qid, self.player, gold_override=gold_override)
                    if result:
                        R.print_quest_update(f"Quest complete: {self.quests.defs[qid]['name']}")

        elif t == "sell_item":
            iid = self.world.resolve_item_id(action.item_id or "")
            price = action.value or 0
            if not iid:
                R.print_warning(f"(Couldn't find item '{action.item_id}' — sale not processed)")
                return
            template = self.world.get_item_template(iid)
            if not template:
                R.print_warning(f"(Item '{iid}' not found in world data — sale not processed)")
                return
            if self.player.gold < price:
                R.print_warning(
                    f"You don't have enough gold. (Need {price}, have {self.player.gold})"
                )
                npc.history.append({
                    "role": "user",
                    "content": f"[System: Player only has {self.player.gold} gold and cannot afford {price} gold.]",
                })
                return
            self.player.gold -= price
            self.player.add_item(dict(template))
            R.print_success(f"You bought {template['name']} for {price} gold.")

        elif t == "give_item":
            iid = self.world.resolve_item_id(action.item_id or "")
            if not iid:
                return
            template = self.world.get_item_template(iid)
            if not template:
                return
            self.player.add_item(dict(template))
            R.print_success(f"You received: {template['name']}")

    # ------------------------------------------------------------------ #
    #  Save                                                                #
    # ------------------------------------------------------------------ #

    def _do_save(self):
        """Persist current game state to disk."""
        if self.save_path is None or self.player is None:
            return
        ok = save_game(
            self.save_path,
            self.player,
            self.current_room_id,
            self.quests.status,
        )
        if not ok:
            R.print_warning("Could not write save file.")

    # ------------------------------------------------------------------ #
    #  AI helpers                                                          #
    # ------------------------------------------------------------------ #

    def _interpret_and_run(self, raw: str):
        """Use the LLM to interpret a free-form command and dispatch it."""
        with R.thinking():
            result = interpret(raw, self._build_interpreter_context(), self.client)

        if result is None:
            self._narrate(raw, "unknown")
            return

        match result.command:
            case "question":    self._narrate(raw, "question")
            case "out_of_game": self._narrate(raw, "out_of_game")
            case "unknown":     self._narrate(raw, "unknown")
            case "look":        self._look()
            case "go":          self._go(result.args)
            case "talk":        self._talk(result.args)
            case "attack":      self._attack(result.args)
            case "flee":        R.print_info("You're not in combat.")
            case "status":      self._status()
            case "inventory":   self._inventory()
            case "use":         self._use(result.args)
            case "equip":       self._use(result.args)
            case "quests":      self.quests.show()
            case "help":        R.print_help()
            case "quit":
                self._do_save()
                R.print_info("Farewell, adventurer. Your progress has been saved.")
                self.running = False
            case _:
                R.print_error(f"Not sure what you mean by '{raw}'. Type 'help' for commands.")

    def _narrate(self, question: str, input_type: str = "question"):
        """Route a non-command input to the narrator with the appropriate type."""
        room = self.world.get_room(self.current_room_id)
        context = self._build_room_context(room)
        with R.thinking():
            response = self.narrator.ask(question, context, self.client, input_type=input_type)
        if response:
            R.print_narrator_say(response)

    # ------------------------------------------------------------------ #
    #  Context builders                                                    #
    # ------------------------------------------------------------------ #

    def _show_memory(self, args: str):
        """Debug command — show persisted memory for NPCs and the current room."""
        print()
        R.print_separator()
        print(f"  {R.BOLD}{R.BRIGHT_WHITE}MEMORY{R.RESET}  {R.DIM}(persisted across sessions){R.RESET}")
        R.print_separator()

        # NPC memories
        any_npc = False
        for npc_id, npc in self.npcs.items():
            if not args or args.lower() in npc.name.lower():
                if npc.memory:
                    any_npc = True
                    print(f"\n  {R.BRIGHT_YELLOW}{npc.display_name()}{R.RESET}")
                    for fact in npc.memory:
                        print(f"   {R.DIM}·{R.RESET} {R.WHITE}{fact}{R.RESET}")
                else:
                    any_npc = True
                    print(f"\n  {R.BRIGHT_YELLOW}{npc.display_name()}{R.RESET}  {R.DIM}(no memories yet){R.RESET}")

        # Room memory for current room
        room = self.world.get_room(self.current_room_id)
        room_facts = self.narrator._load_room_memory(self.current_room_id)
        print(f"\n  {R.BRIGHT_CYAN}Room: {room.name}{R.RESET}")
        if room_facts:
            for fact in room_facts:
                print(f"   {R.DIM}·{R.RESET} {R.WHITE}{fact}{R.RESET}")
        else:
            print(f"   {R.DIM}(no room details established yet){R.RESET}")

        print()
        R.print_separator()

    def _build_world_state(self) -> dict:
        room = self.world.get_room(self.current_room_id)
        return {
            "player": {
                "name": self.player.name,
                "level": self.player.level,
                "hp": self.player.hp,
                "max_hp": self.player.max_hp,
                "gold": self.player.gold,
            },
            "room_name": room.name,
            "quest_summary": self.quests.summary_for_npc(self.world),
        }

    def _build_room_context(self, room) -> dict:
        alive = self.world.alive_enemies_in_room(room.id)
        return {
            "room_id": room.id,
            "room_name": room.name,
            "room_description": room.description,
            "room_guide": room.md_content,   # full .md for narrator guidance
            "exits": list(room.exits.keys()),
            "npcs": [self.npcs[nid].name for nid in room.npc_ids if nid in self.npcs],
            "enemies": [e.name for e in alive],
        }

    def _build_interpreter_context(self) -> dict:
        room = self.world.get_room(self.current_room_id)
        alive = self.world.alive_enemies_in_room(self.current_room_id)
        return {
            "room": room.name,
            "exits": list(room.exits.keys()),
            "npcs": [self.npcs[nid].name for nid in room.npc_ids if nid in self.npcs],
            "enemies": [e.name for e in alive],
            "inventory": [item["name"] for item in self.player.inventory],
        }


# ------------------------------------------------------------------ #
#  Entry point                                                         #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    game = Game()
    game.start()
