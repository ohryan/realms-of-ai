"""
ANSI/BBS-style terminal renderer.
"""

import shutil

# ANSI codes
RESET       = "\033[0m"
BOLD        = "\033[1m"
DIM         = "\033[2m"

BLACK       = "\033[30m"
RED         = "\033[31m"
GREEN       = "\033[32m"
YELLOW      = "\033[33m"
BLUE        = "\033[34m"
MAGENTA     = "\033[35m"
CYAN        = "\033[36m"
WHITE       = "\033[37m"

BRIGHT_RED      = "\033[91m"
BRIGHT_GREEN    = "\033[92m"
BRIGHT_YELLOW   = "\033[93m"
BRIGHT_BLUE     = "\033[94m"
BRIGHT_MAGENTA  = "\033[95m"
BRIGHT_CYAN     = "\033[96m"
BRIGHT_WHITE    = "\033[97m"

# Box-drawing
H = "─"
V = "│"
TL = "╔"
TR = "╗"
BL = "╚"
BR = "╝"
LJ = "╠"
RJ = "╣"
TJ = "╦"
BJ = "╩"
CR = "╬"


def _term_width() -> int:
    return min(shutil.get_terminal_size((72, 24)).columns, 72)


def _box_line(char: str, width: int) -> str:
    return TL + H * (width - 2) + TR if char == "top" else \
           LJ + H * (width - 2) + RJ if char == "mid" else \
           BL + H * (width - 2) + BR


def _pad(text: str, width: int) -> str:
    """Pad text to fill a box row (strips ANSI for length calc)."""
    import re
    clean = re.sub(r"\033\[[0-9;]*m", "", text)
    padding = width - 2 - len(clean)
    return V + " " + text + " " * max(0, padding - 1) + V


def print_title():
    w = _term_width()
    title_lines = [
        "",
        f"{BRIGHT_CYAN}  ██████╗ ███████╗ █████╗ ██╗     ███╗   ███╗███████╗{RESET}",
        f"{BRIGHT_CYAN}  ██╔══██╗██╔════╝██╔══██╗██║     ████╗ ████║██╔════╝{RESET}",
        f"{BRIGHT_CYAN}  ██████╔╝█████╗  ███████║██║     ██╔████╔██║███████╗{RESET}",
        f"{BRIGHT_CYAN}  ██╔══██╗██╔══╝  ██╔══██║██║     ██║╚██╔╝██║╚════██║{RESET}",
        f"{BRIGHT_CYAN}  ██║  ██║███████╗██║  ██║███████╗██║ ╚═╝ ██║███████║{RESET}",
        f"{BRIGHT_CYAN}  ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚══════╝{RESET}",
        "",
        f"{YELLOW}                  O F   A I{RESET}",
        f"{DIM}{WHITE}         A Text-Based Adventure with Living NPCs{RESET}",
        "",
    ]
    print()
    for line in title_lines:
        print(line)
    print_separator()


def print_separator(color: str = DIM + CYAN):
    w = _term_width()
    print(f"{color}{H * w}{RESET}")


def print_room_header(name: str):
    w = _term_width()
    inner = w - 4
    name_display = f"{BOLD}{BRIGHT_CYAN}{name}{RESET}"
    import re
    clean_len = len(re.sub(r"\033\[[0-9;]*m", "", name_display))
    padding = max(0, inner - clean_len)
    print()
    print(f"{CYAN}{TL}{H * (w-2)}{TR}{RESET}")
    print(f"{CYAN}{V}{RESET}  {name_display}{' ' * padding}  {CYAN}{V}{RESET}")
    print(f"{CYAN}{LJ}{H * (w-2)}{RJ}{RESET}")


def print_room_close():
    w = _term_width()
    print(f"{CYAN}{BL}{H * (w-2)}{BR}{RESET}")


def print_description(text: str):
    w = _term_width()
    inner = w - 4
    words = text.split()
    line = ""
    for word in words:
        if len(line) + len(word) + 1 > inner:
            print(f"{CYAN}{V}{RESET}  {WHITE}{line}{RESET}")
            line = word
        else:
            line = (line + " " + word).strip()
    if line:
        print(f"{CYAN}{V}{RESET}  {WHITE}{line}{RESET}")


def print_room_field(label: str, value: str, color: str = WHITE):
    print(f"{CYAN}{V}{RESET}  {DIM}{WHITE}{label}:{RESET} {color}{value}{RESET}")


def print_npc_say(name: str, text: str):
    w = _term_width()
    print()
    # Wrap text
    import re
    max_w = w - len(name) - 5
    words = text.split()
    lines = []
    line = ""
    for word in words:
        if len(line) + len(word) + 1 > max_w:
            lines.append(line)
            line = word
        else:
            line = (line + " " + word).strip()
    if line:
        lines.append(line)

    first = True
    for l in lines:
        prefix = f"{BRIGHT_YELLOW}{name}{RESET}{WHITE}:{RESET} " if first else " " * (len(name) + 2)
        print(f"  {prefix}{WHITE}{l}{RESET}")
        first = False


def print_player_say(text: str):
    print(f"\n  {DIM}{WHITE}[You]:{RESET} {BRIGHT_WHITE}{text}{RESET}")


def print_combat_header(enemy_name: str):
    print()
    print(f"  {BRIGHT_RED}⚔  COMBAT: {enemy_name}  ⚔{RESET}")
    print_separator(DIM + RED)


def print_combat_action(text: str, color: str = WHITE):
    print(f"  {color}{text}{RESET}")


def hp_bar(current: int, maximum: int, width: int = 20) -> str:
    filled = int((current / maximum) * width)
    bar = "█" * filled + "░" * (width - filled)
    if current / maximum > 0.5:
        color = BRIGHT_GREEN
    elif current / maximum > 0.25:
        color = BRIGHT_YELLOW
    else:
        color = BRIGHT_RED
    return f"{color}[{bar}]{RESET} {current}/{maximum}"


def print_status_bar(player):
    w = _term_width()
    hp_display = hp_bar(player.hp, player.max_hp, 16)
    print()
    print_separator()
    print(
        f"  {BRIGHT_WHITE}{player.name}{RESET}  "
        f"{DIM}HP{RESET} {hp_display}  "
        f"{BRIGHT_YELLOW}◈ {player.gold}g{RESET}  "
        f"{BRIGHT_CYAN}Lv.{player.level}{RESET}  "
        f"{DIM}XP {player.xp}/{player.xp_next}{RESET}"
    )
    print_separator()


def print_info(text: str):
    print(f"\n  {BRIGHT_CYAN}▶{RESET} {WHITE}{text}{RESET}")


def print_success(text: str):
    print(f"\n  {BRIGHT_GREEN}✔{RESET} {BRIGHT_WHITE}{text}{RESET}")


def print_warning(text: str):
    print(f"\n  {BRIGHT_YELLOW}!{RESET} {YELLOW}{text}{RESET}")


def print_error(text: str):
    print(f"\n  {BRIGHT_RED}✘{RESET} {RED}{text}{RESET}")


def print_quest_update(text: str):
    print(f"\n  {BRIGHT_MAGENTA}◆ QUEST:{RESET} {BRIGHT_WHITE}{text}{RESET}")


def print_level_up(level: int):
    print(f"\n  {BRIGHT_YELLOW}★★★  LEVEL UP! You are now Level {level}!  ★★★{RESET}")


def print_help():
    commands = [
        ("look / l",           "Examine the current room"),
        ("go <dir>",           "Move in a direction (up, down, north, etc.)"),
        ("talk <name>",        "Speak with an NPC"),
        ("attack / a",         "Attack the nearest enemy"),
        ("attack <name>",      "Attack a specific enemy"),
        ("flee",               "Attempt to flee from combat"),
        ("status / s",         "Show your character stats"),
        ("inventory / i",      "Show your inventory"),
        ("use <item>",         "Use an item from inventory"),
        ("quests / q",         "Show active and completed quests"),
        ("help",               "Show this help"),
        ("quit",               "Exit the game"),
    ]
    print()
    w = _term_width()
    print(f"{CYAN}{TL}{H * (w-2)}{TR}{RESET}")
    header = f"{BOLD}{BRIGHT_CYAN}COMMANDS{RESET}"
    import re
    cl = len(re.sub(r"\033\[[0-9;]*m", "", header))
    print(f"{CYAN}{V}{RESET}  {header}{' ' * (w - 4 - cl)}{CYAN}{V}{RESET}")
    print(f"{CYAN}{LJ}{H * (w-2)}{RJ}{RESET}")
    for cmd, desc in commands:
        cmd_s = f"{BRIGHT_WHITE}{cmd:<18}{RESET}"
        desc_s = f"{DIM}{WHITE}{desc}{RESET}"
        import re
        cl2 = len(re.sub(r"\033\[[0-9;]*m", "", cmd_s + desc_s))
        pad = max(0, w - 4 - cl2)
        print(f"{CYAN}{V}{RESET}  {cmd_s}{desc_s}{' ' * pad}{CYAN}{V}{RESET}")
    print(f"{CYAN}{BL}{H * (w-2)}{BR}{RESET}")
