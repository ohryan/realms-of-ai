# Realms of AI

A text RPG where the characters are actually alive.

Every NPC is a real conversation with Claude AI. Not dialogue trees. Not canned responses. You talk to them in plain English and they talk back — with personality, opinions, and memory. A stubborn innkeeper won't budge no matter how you push her. A merchant haggles with you for the fun of it. They invent details about themselves mid-conversation and remember them next time you play.

The game underneath is classic: rooms, combat, inventory, quests. The difference is who you meet along the way.

---

## Make your own adventure

Realms of AI is designed to be modded. Each adventure is a **module** — a folder of text files that defines a world. You can build your own without touching any code.

The easiest way is to describe your world to Claude Code or Claude.ai and let it generate the files:

> Read CREATE_MODULE.md, then create a module called `iron_mine` — an abandoned mine where a foreman's ghost gives a quest, a trapped survivor sells supplies, and something wrong lives at the bottom of the shaft.

That's it. The full spec is in [`CREATE_MODULE.md`](CREATE_MODULE.md) if you want to understand what's possible or write one by hand.

A module looks like this:

```
data/modules/your_module/
├── module.json          ← title, description, author
├── world.json           ← rooms, enemies, items, quests (the numbers)
├── npcs/                ← one .md per NPC (the personality, the voice)
├── rooms/               ← one .md per room
├── enemies/             ← one .md per enemy type
├── items/               ← one .md per item
└── quests/              ← one .md per quest
```

The `.md` files are where the life is. The richer the NPC files, the more alive the characters feel.

---

## What's included

- **The Rusty Flagon** — a tavern with a rat problem, a weary innkeeper, and a merchant who loves to negotiate
- **Abandoned Space Station** — a derelict station, an alien incursion, and a commander who needs your help

---

## Requirements

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/) with credits loaded
- A terminal that supports ANSI colour (any modern Linux/macOS terminal)

> Realms of AI uses the Anthropic API directly — separate from a Claude.ai subscription. You'll need to add credits at [console.anthropic.com](https://console.anthropic.com/). Costs are very low (all AI calls use `claude-haiku-4-5`).

---

## Installation

```bash
git clone https://github.com/ohryan/realms-of-ai.git
cd realms-of-ai
pip install -r requirements.txt
python game.py
```

First run asks for your API key and character name. Both are saved so you only enter them once.

---

## How to Play

Type commands at the `>` prompt. You don't have to be exact — the game understands natural language.

**Movement**
```
look / go north / north
```

**Talking**
```
talk mira
```
Type anything in plain English once in conversation. End with `bye`. NPCs can give quests, sell items, negotiate prices, and remember what you've told them.

**Combat**
```
attack / attack rat / flee
```
Turn-based. Each weapon rolls its own die — a dagger rolls `1d4`, a sword `1d6`, a heavy axe `1d10`.

**Items and status**
```
inventory / use potion / equip sword / status
```

**Quests**
```
quests
```

**Freeform**

Anything that isn't a command goes to the narrator AI:
```
> Is there anything written on the wall?
> What does it smell like in here?
```

**Other**
```
help / quit
```

Progress is saved on exit and resumed next session.

---

## License

MIT
