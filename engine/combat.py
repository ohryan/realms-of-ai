"""
Turn-based combat system.
"""

import random
from .models import Player, EnemyInstance
from . import renderer as R


def run_combat(player: Player, enemies: list[EnemyInstance]) -> bool:
    """
    Run combat with a list of enemies (fought one at a time).
    Returns True if player survived, False if player died.
    """
    for enemy in enemies:
        if not enemy.is_alive:
            continue
        result = _fight_one(player, enemy)
        if result == "dead":
            return False
        if result == "fled":
            R.print_info("You escaped!")
            return True
        # "victory" — continue to next enemy

    return True


def _fight_one(player: Player, enemy: EnemyInstance) -> str:
    """
    Fight a single enemy. Returns 'victory', 'dead', or 'fled'.
    """
    R.print_combat_header(enemy.name)
    R.print_combat_action(f"{enemy.description}", R.WHITE)
    print()

    while True:
        # Show status
        player_hp = R.hp_bar(player.hp, player.max_hp, 16)
        enemy_hp = R.hp_bar(enemy.hp, enemy.max_hp, 16)
        print(f"  {R.BRIGHT_WHITE}{player.name:<14}{R.RESET} {player_hp}")
        print(f"  {R.BRIGHT_RED}{enemy.name:<14}{R.RESET} {enemy_hp}")
        print()

        # Player input
        try:
            cmd = input(f"  {R.BRIGHT_WHITE}[attack / flee]>{R.RESET} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            cmd = "flee"

        if cmd in ("flee", "f", "run"):
            if random.random() < 0.55:
                R.print_combat_action("You turn and bolt — the enemy doesn't follow!", R.BRIGHT_YELLOW)
                return "fled"
            else:
                R.print_combat_action("You try to flee but can't find an opening!", R.BRIGHT_YELLOW)
                # Enemy still gets an attack
                enemy_dmg = enemy.deal_damage()
                actual = player.take_damage(enemy_dmg)
                R.print_combat_action(
                    f"{enemy.name} catches you off guard and deals {actual} damage!",
                    R.BRIGHT_RED
                )
                if not player.is_alive:
                    _death_screen(player)
                    return "dead"
                print()
                continue

        elif cmd in ("attack", "a", "hit", "fight", ""):
            # Player attacks
            dmg = player.deal_damage(enemy.defense)
            actual_dmg = enemy.take_damage(dmg)
            R.print_combat_action(
                f"You strike {enemy.name} for {R.BRIGHT_WHITE}{actual_dmg}{R.RESET + R.WHITE} damage!",
                R.WHITE
            )

            if not enemy.is_alive:
                R.print_combat_action(
                    f"{enemy.name} collapses. Victory!",
                    R.BRIGHT_GREEN
                )
                # Reward
                if enemy.xp > 0:
                    levelled = player.gain_xp(enemy.xp)
                    R.print_success(f"+{enemy.xp} XP")
                    if levelled:
                        R.print_level_up(player.level)
                if enemy.gold > 0:
                    player.gold += enemy.gold
                    R.print_success(f"+{enemy.gold} gold")
                print()
                return "victory"

            # Enemy attacks back
            enemy_dmg = enemy.deal_damage()
            actual = player.take_damage(enemy_dmg)
            R.print_combat_action(
                f"{enemy.name} strikes back for {R.BRIGHT_RED}{actual}{R.RESET + R.WHITE} damage!",
                R.WHITE
            )

            if not player.is_alive:
                _death_screen(player)
                return "dead"

            print()

        else:
            R.print_error("Type 'attack' to fight or 'flee' to run.")


def _death_screen(player: Player):
    print()
    R.print_separator(R.BRIGHT_RED)
    print(f"\n  {R.BRIGHT_RED}☠  {player.name} has fallen.{R.RESET}")
    print(f"\n  {R.DIM}{R.WHITE}Your adventure ends here.{R.RESET}\n")
    R.print_separator(R.BRIGHT_RED)
