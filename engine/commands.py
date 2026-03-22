"""
CommandsMixin — all player-facing command handlers.

Mixed into the Game class so these methods have full access to game state
(self.player, self.world, self.npcs, etc.) without cluttering game.py.
"""

from engine import renderer as R
from engine.combat import run_combat


class CommandsMixin:
    """All in-game commands the player can issue from the main prompt."""

    # ------------------------------------------------------------------ #
    #  look                                                                #
    # ------------------------------------------------------------------ #

    def _look(self):
        room = self.world.get_room(self.current_room_id)
        R.print_room_header(room.name)
        R.print_description(room.description)

        if room.exits:
            exits_str = ", ".join(
                f"{R.BRIGHT_WHITE}{d}{R.RESET}{R.DIM}{R.WHITE} → {self.world.rooms[rid].name}{R.RESET}"
                for d, rid in room.exits.items()
            )
            R.print_room_field("Exits", exits_str)

        npc_ids = [nid for nid in room.npc_ids if nid in self.npcs]
        if npc_ids:
            npc_names = ", ".join(
                f"{R.BRIGHT_YELLOW}{self.npcs[nid].display_name()}{R.RESET}"
                for nid in npc_ids
            )
            R.print_room_field("People", npc_names)

        alive = self.world.alive_enemies_in_room(self.current_room_id)
        if alive:
            enemy_names = ", ".join(
                f"{R.BRIGHT_RED}{e.name}{R.RESET}" for e in alive
            )
            R.print_room_field("Enemies", enemy_names)

        R.print_room_close()

    # ------------------------------------------------------------------ #
    #  go                                                                  #
    # ------------------------------------------------------------------ #

    def _go(self, direction: str):
        direction = direction.lower().strip()
        room = self.world.get_room(self.current_room_id)

        aliases = {"d": "down", "u": "up", "n": "north", "s": "south", "e": "east", "w": "west"}
        direction = aliases.get(direction, direction)

        if direction not in room.exits:
            # Try matching by destination room name
            for d, rid in room.exits.items():
                if direction in self.world.rooms[rid].name.lower():
                    direction = d
                    break
            else:
                valid = ", ".join(room.exits.keys()) or "none"
                R.print_error(f"You can't go '{direction}' from here. Valid exits: {valid}")
                return

        dest_id = room.exits[direction]
        self.current_room_id = dest_id
        dest = self.world.get_room(dest_id)
        R.print_info(f"You head {direction} toward {dest.name}.")
        print()
        self._look()
        self.quests.check_objectives(self.world, self.current_room_id)

    # ------------------------------------------------------------------ #
    #  talk                                                                #
    # ------------------------------------------------------------------ #

    def _talk(self, target: str):
        if not target:
            R.print_error("Talk to whom? e.g. 'talk mira'")
            return

        room = self.world.get_room(self.current_room_id)
        npc = self._find_npc(target, room.npc_ids)

        if npc is None:
            R.print_error(f"There's no one called '{target}' here.")
            return

        self._conversation_loop(npc)

    def _find_npc(self, query: str, npc_ids: list):
        query = query.lower()
        if query in npc_ids and query in self.npcs:
            return self.npcs[query]
        for nid in npc_ids:
            if nid not in self.npcs:
                continue
            npc = self.npcs[nid]
            if query in npc.name.lower() or query in npc.title.lower():
                return npc
        return None

    # ------------------------------------------------------------------ #
    #  attack                                                              #
    # ------------------------------------------------------------------ #

    def _attack(self, target: str):
        alive = self.world.alive_enemies_in_room(self.current_room_id)
        if not alive:
            R.print_info("There are no enemies here to fight.")
            return

        if target:
            filtered = [e for e in alive if target.lower() in e.name.lower()]
            if not filtered:
                R.print_error(f"No enemy called '{target}' here.")
                return
            enemies = filtered
        else:
            enemies = alive

        survived = run_combat(self.player, enemies)

        if not survived:
            self.running = False
            return

        self.quests.check_objectives(self.world, self.current_room_id)

    # ------------------------------------------------------------------ #
    #  status                                                              #
    # ------------------------------------------------------------------ #

    def _status(self):
        p = self.player
        print()
        R.print_separator()
        print(f"  {R.BOLD}{R.BRIGHT_WHITE}{p.name}{R.RESET}  —  {R.BRIGHT_CYAN}Level {p.level}{R.RESET}")
        print(f"  {R.DIM}HP:{R.RESET}     {R.hp_bar(p.hp, p.max_hp, 20)}")
        print(f"  {R.DIM}XP:{R.RESET}     {R.BRIGHT_CYAN}{p.xp}/{p.xp_next}{R.RESET}")
        print(f"  {R.DIM}Gold:{R.RESET}   {R.BRIGHT_YELLOW}{p.gold}{R.RESET}")
        print(f"  {R.DIM}Attack:{R.RESET} {R.BRIGHT_WHITE}{p.attack}{R.RESET}    {R.DIM}Defense:{R.RESET} {R.BRIGHT_WHITE}{p.defense}{R.RESET}")
        print(f"  {R.DIM}Weapon:{R.RESET} {R.BRIGHT_WHITE}{p.weapon_label}{R.RESET}")
        R.print_separator()

    # ------------------------------------------------------------------ #
    #  inventory                                                           #
    # ------------------------------------------------------------------ #

    def _inventory(self):
        if not self.player.inventory:
            R.print_info("Your inventory is empty.")
            return
        equipped_id = (self.player.equipped_weapon or {}).get("id")
        print()
        print(f"  {R.BOLD}{R.BRIGHT_WHITE}Inventory:{R.RESET}")
        for item in self.player.inventory:
            tag = (
                f"  {R.BRIGHT_GREEN}[equipped]{R.RESET}"
                if item["id"] == equipped_id else ""
            )
            print(
                f"   {R.BRIGHT_CYAN}·{R.RESET} {R.WHITE}{item['name']}{R.RESET}"
                f"  {R.DIM}{item.get('description', '')}{R.RESET}{tag}"
            )

    # ------------------------------------------------------------------ #
    #  use / equip                                                         #
    # ------------------------------------------------------------------ #

    def _use(self, item_name: str):
        if not item_name:
            R.print_error("Use what? e.g. 'use healing potion' or 'use dagger'")
            return

        item = self._find_inventory_item(item_name)
        if item is None:
            R.print_error(f"You don't have '{item_name}' in your inventory.")
            return

        if item.get("type") == "weapon":
            self._equip_weapon(item)
        elif item.get("type") == "consumable" and "heal" in item:
            actual = self.player.heal(item["heal"])
            self.player.remove_item(item["id"])
            R.print_success(f"You drink the {item['name']} and restore {actual} HP.")
            R.print_info(f"HP: {self.player.hp}/{self.player.max_hp}")
        else:
            R.print_warning(f"You can't use {item['name']} right now.")

    def _equip_weapon(self, item: dict):
        """Equip a weapon from inventory."""
        self.player.equip(item)
        dice = item.get("damage_dice", "?")
        bonus = item.get("damage_bonus", 0)
        suffix = f"+{bonus}" if bonus > 0 else (f"{bonus}" if bonus < 0 else "")
        R.print_success(f"You equip the {item['name']}. ({dice}{suffix})")

    def _find_inventory_item(self, query: str) -> dict | None:
        """Find an inventory item by partial name or id match."""
        q = query.lower()
        for item in self.player.inventory:
            if q in item["name"].lower() or q in item["id"].lower():
                return item
        return None
