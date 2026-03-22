"""
ANSI/BBS-style terminal renderer.
"""

import re
import shutil
import sys
import threading

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


def _strip_ansi(text: str) -> str:
    return re.sub(r"\033\[[0-9;]*m", "", text)


def _box_line(char: str, width: int) -> str:
    return TL + H * (width - 2) + TR if char == "top" else \
           LJ + H * (width - 2) + RJ if char == "mid" else \
           BL + H * (width - 2) + BR


# ------------------------------------------------------------------ #
#  Thinking spinner                                                    #
# ------------------------------------------------------------------ #

_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class _Spinner:
    """Context manager that shows an animated spinner while work is in progress."""

    def __init__(self, msg: str = ""):
        self._msg = msg
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        i = 0
        while not self._stop.is_set():
            frame = _SPINNER_FRAMES[i % len(_SPINNER_FRAMES)]
            sys.stdout.write(f"\r  {DIM}{WHITE}{frame}  {self._msg}{RESET}")
            sys.stdout.flush()
            i += 1
            self._stop.wait(0.08)
        # Erase the spinner line
        sys.stdout.write("\r" + " " * (len(self._msg) + 8) + "\r")
        sys.stdout.flush()

    def __enter__(self):
        self._t.start()
        return self

    def __exit__(self, *_):
        self._stop.set()
        self._t.join()


def thinking(msg: str = "thinking...") -> _Spinner:
    """Usage:  with R.thinking(): do_slow_thing()"""
    return _Spinner(msg)


# ------------------------------------------------------------------ #
#  Title / intro                                                       #
# ------------------------------------------------------------------ #

def print_title():
    C  = BRIGHT_CYAN
    Y  = BRIGHT_YELLOW
    D  = DIM + WHITE
    Rs = RESET

    robot = [
        f"                {C}╔═══════════╗{Rs}",
        f"               {C}╔╣{Rs} {Y}◉{Rs}       {Y}◉{Rs} {C}╠╗{Rs}",
        f"               {C}║╚═══════════╝║{Rs}",
        f"               {C}║{Rs}   {D}───────{Rs}   {C}║{Rs}",
        f"               {C}║{Rs}  {D}─ ─ ─ ─ ─{Rs}  {C}║{Rs}",
        f"              {C}╔╩═════════════╩╗{Rs}",
        f"              {C}║{Rs}  {D}┌───────────┐{Rs}  {C}║{Rs}",
        f"              {C}║{Rs}  {D}│ ░ ░ ░ ░ ░ │{Rs}  {C}║{Rs}",
        f"              {C}║{Rs}  {D}└───────────┘{Rs}  {C}║{Rs}",
        f"              {C}╚══════╤═════╤══════╝{Rs}",
        f"                     {C}│{Rs}     {C}│{Rs}",
        f"                   {C}──┘{Rs}     {C}└──{Rs}",
        "",
    ]

    title_lines = [
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
    for line in robot:
        print(line)
    for line in title_lines:
        print(line)
    print_separator()


# ------------------------------------------------------------------ #
#  Structural elements                                                 #
# ------------------------------------------------------------------ #

def print_separator(color: str = DIM + CYAN):
    w = _term_width()
    print(f"{color}{H * w}{RESET}")


def print_room_header(name: str):
    w = _term_width()
    name_display = f"{BOLD}{BRIGHT_CYAN}{name}{RESET}"
    clean_len = len(_strip_ansi(name_display))
    # inner content width = w - 2 (borders) - 2 (left pad) - 2 (right pad)
    padding = max(0, w - 6 - clean_len)
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


# ------------------------------------------------------------------ #
#  Dialogue                                                            #
# ------------------------------------------------------------------ #

def print_npc_say(name: str, text: str):
    """NPC dialogue in bright yellow."""
    w = _term_width()
    prefix_len = len(name) + 2   # "Name: "
    max_w = w - prefix_len - 4

    words = text.split()
    lines, line = [], ""
    for word in words:
        if len(line) + len(word) + 1 > max_w:
            lines.append(line)
            line = word
        else:
            line = (line + " " + word).strip()
    if line:
        lines.append(line)

    print()
    first = True
    for l in lines:
        prefix = f"{BRIGHT_YELLOW}{name}{RESET}{WHITE}:{RESET} " if first \
                 else " " * (prefix_len)
        print(f"  {prefix}{WHITE}{l}{RESET}")
        first = False


def print_narrator_say(text: str):
    """Narrator response — distinct magenta header, dimmed body text."""
    w = _term_width()
    label = "Narrator"
    prefix_len = len(label) + 2  # "Narrator: "
    max_w = w - prefix_len - 4

    words = text.split()
    lines, line = [], ""
    for word in words:
        if len(line) + len(word) + 1 > max_w:
            lines.append(line)
            line = word
        else:
            line = (line + " " + word).strip()
    if line:
        lines.append(line)

    print()
    first = True
    for l in lines:
        prefix = f"{BRIGHT_MAGENTA}{label}{RESET}{DIM}{WHITE}:{RESET} " if first \
                 else " " * prefix_len
        print(f"  {prefix}{DIM}{WHITE}{l}{RESET}")
        first = False


def print_player_say(text: str):
    print(f"\n  {DIM}{WHITE}[You]:{RESET} {BRIGHT_WHITE}{text}{RESET}")


# ------------------------------------------------------------------ #
#  Combat                                                              #
# ------------------------------------------------------------------ #

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


# ------------------------------------------------------------------ #
#  Status bar                                                          #
# ------------------------------------------------------------------ #

def print_status_bar(player):
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


# ------------------------------------------------------------------ #
#  Info messages                                                       #
# ------------------------------------------------------------------ #

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


# ------------------------------------------------------------------ #
#  Help                                                                #
# ------------------------------------------------------------------ #

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
    cl = len(_strip_ansi(header))
    padding = max(0, w - 6 - cl)
    print(f"{CYAN}{V}{RESET}  {header}{' ' * padding}  {CYAN}{V}{RESET}")
    print(f"{CYAN}{LJ}{H * (w-2)}{RJ}{RESET}")
    for cmd, desc in commands:
        cmd_s  = f"{BRIGHT_WHITE}{cmd:<18}{RESET}"
        desc_s = f"{DIM}{WHITE}{desc}{RESET}"
        cl2 = len(_strip_ansi(cmd_s + desc_s))
        pad = max(0, w - 6 - cl2)
        print(f"{CYAN}{V}{RESET}  {cmd_s}{desc_s}{' ' * pad}  {CYAN}{V}{RESET}")
    print(f"{CYAN}{BL}{H * (w-2)}{BR}{RESET}")
