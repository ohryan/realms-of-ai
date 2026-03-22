# Realms of AI

A BBS-style text RPG where every NPC is a live conversation with Claude AI.

Not scripted responses. Not dialogue trees. Talk to characters in plain English — they have personalities, agendas, and memories. They'll negotiate prices, give quests, and remember what you said last session. A stubborn innkeeper holds firm no matter how hard you push. A jovial merchant haggles with you for the sport of it.

The game underneath is classic: rooms, combat, inventory, quests. The difference is who you meet along the way.

---

## Requirements

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/) with credits loaded
- A terminal that supports ANSI colour (any modern Linux/macOS terminal)

> **Note:** This game uses the Anthropic API directly — it is separate from a Claude.ai subscription. You'll need to add credits at [console.anthropic.com](https://console.anthropic.com/). Costs are very low (each NPC reply uses `claude-haiku-4-5`).

---

## Installation

```bash
git clone <repo-url>
cd ai-game
pip install -r requirements.txt
python game.py
```

On first run you'll be asked for your Anthropic API key and your character's name. Both are saved to `data/config.json` so you only need to enter them once.

---

## How to Play

The game runs entirely in the terminal. Type commands at the `>` prompt.

### Movement

```
look          — describe the current room
go north      — move in a direction (north/south/east/west/up/down)
north         — shorthand, works on its own
```

### Talking to NPCs

```
talk mira     — start a conversation with an NPC
```

Once in conversation, type anything in plain English. End with `bye`.

NPCs can:
- Give you quests
- Sell items (and negotiate on price if you push them)
- Give rewards when objectives are complete
- Remember things you've told them across sessions

### Combat

```
attack        — attack the nearest enemy
attack rat    — attack a specific enemy by name
flee          — attempt to escape (55% chance)
```

Combat is turn-based. You attack, they attack back. Each weapon rolls its own die — a dagger rolls `1d4`, a sword rolls `1d6`, and so on.

### Inventory and Items

```
inventory     — list what you're carrying
use potion    — drink a consumable
equip sword   — equip a weapon
status        — show HP, XP, gold, and equipped weapon
```

### Quests

```
quests        — open the quest journal
```

### Freeform Input

You don't have to use exact commands. The game uses Claude to interpret natural language — *"head down to the cellar"* works just as well as `go down`. If your input doesn't match any command, the narrator AI answers it as an environmental question instead:

```
> Is there anything written on the wall?
> What does it smell like in here?
> Who is that woman behind the bar?
```

### Other Commands

```
help          — show command reference
quit          — exit the game
```

---

## Gameplay Loop

1. **Enter a room** — read the description, note exits, NPCs, and enemies
2. **Talk to NPCs** — learn about the world, accept quests, buy supplies
3. **Explore** — move between rooms, ask the narrator questions
4. **Fight** — clear enemies to complete objectives
5. **Return** — bring results back to the quest giver for your reward

Characters level up from XP, gaining HP, attack, and defense with each level.

---

## Modules

The game ships with one module: **The Rusty Flagon** — a tavern with a rat problem, a weary innkeeper, and a stranded merchant.

Each module is a self-contained adventure in `data/modules/<module_id>/`. If more than one module is installed, the game presents a selection menu at startup.

### Module Structure

```
data/modules/<module_id>/
├── module.json          ← title, description, author
├── world.json           ← rooms, enemies, items, quests (mechanical data)
├── rooms/               ← one .md per room
├── enemies/             ← one .md per enemy type
├── items/               ← one .md per item
├── quests/              ← one .md per quest
└── npcs/                ← one .md per NPC
```

`world.json` holds the numbers — stats, exits, rewards, relationships. The `.md` files hold everything narrative — descriptions, atmosphere, lore, and AI guidance. The richer the `.md` files, the more alive the module feels.

### Creating a Module

The full specification is in [`CREATE_MODULE.md`](CREATE_MODULE.md).

The fastest way to create a module is to ask Claude Code:

> Read CREATE_MODULE.md, then create a module called `iron_mine` — an abandoned mine where a foreman's ghost gives a quest, a trapped survivor sells supplies, and something wrong lives at the bottom of the shaft.

Claude Code will generate all the files and put them in the right place. You can also use regular Claude (claude.ai) by pasting the contents of `CREATE_MODULE.md` along with your description — you'll just need to copy the files manually.

---

## Project Structure

```
game.py                  ← entry point, main game loop
engine/
  combat.py              ← turn-based combat
  commands.py            ← player command handlers (mixin)
  config.py              ← API key and player name persistence
  dice.py                ← dice notation parser (1d6, 2d4+1, etc.)
  interpreter.py         ← LLM-powered natural language → command mapping
  loader.py              ← module discovery and world initialisation
  md_utils.py            ← .md file parser (extract sections)
  models.py              ← Player, EnemyInstance, Room dataclasses
  narrator.py            ← narrator AI for environmental questions
  npc.py                 ← NPC class with Claude conversation loop
  quest.py               ← quest state tracking and rewards
  renderer.py            ← ANSI/BBS-style terminal output
  world.py               ← world state loaded from world.json + .md files
data/
  config.json            ← saved API key and player name (gitignored)
  modules/
    the_rusty_flagon/    ← included module
```

---

## License

MIT
