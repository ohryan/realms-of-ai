# Creating a Module for Realms of AI

This document tells you how to build a playable module for Realms of AI — a text-based RPG where every NPC is powered by Claude.

Hand this file to Claude Code (or any capable AI assistant) along with a description of the world you want to create. It will produce all the files you need.

---

## The Core Principle

Every section of a module has two parts:

- **`world.json`** — mechanical data only (numbers, IDs, relationships, flags)
- **`.md` files** — everything narrative (descriptions, atmosphere, lore, AI guidance)

The `.md` files are what make your module come alive. The JSON just tells the engine how the pieces fit together.

---

## Directory Structure

```
data/modules/<module_id>/
├── module.json          ← metadata (name, description, author)
├── world.json           ← mechanical data only — no descriptions
├── rooms/
│   └── <room_id>.md     ← one file per room
├── enemies/
│   └── <enemy_name>.md  ← one file per enemy type (shared by instances)
├── items/
│   └── <item_id>.md     ← one file per item
├── quests/
│   └── <quest_id>.md    ← one file per quest
└── npcs/
    └── <npc_id>.md      ← one file per NPC
```

---

## Step 1 — module.json

```json
{
  "id": "my_module",
  "name": "Human-readable title",
  "description": "One or two sentences shown in the module selection menu.",
  "author": "Your name",
  "version": "1.0"
}
```

The `id` field must match the directory name exactly.

---

## Step 2 — world.json

This file is **mechanical data only**. No descriptions go here — those live in `.md` files.

### Top-level structure

```json
{
  "start_room": "<room_id>",
  "player_start": {
    "inventory": ["item_id"]
  },
  "rooms":   { ... },
  "enemies": { ... },
  "items":   { ... },
  "npcs":    { ... },
  "quests":  { ... }
}
```

`player_start.inventory` is optional. The first weapon in the list is auto-equipped.

---

### Rooms

```json
"rooms": {
  "room_id": {
    "name": "Display Name",
    "file": "room_id.md",
    "exits": {
      "north": "other_room_id",
      "down":  "cellar_id"
    },
    "npcs":    ["npc_id_1", "npc_id_2"],
    "enemies": ["enemy_instance_id_1"],
    "items":   []
  }
}
```

**Exit directions:** `north`, `south`, `east`, `west`, `up`, `down`.

Be consistent: if room A exits north to B, room B should exit south to A.

**Rooms must be connected.** The `start_room` must exist. Every room referenced in an exit must also exist.

---

### Enemies

Each entry is an *instance*, not a type. If you want three goblins, define `goblin_1`, `goblin_2`, `goblin_3`. Multiple instances can share the same `.md` file.

```json
"enemies": {
  "enemy_instance_id": {
    "name":        "Display Name",
    "file":        "enemy_type.md",
    "hp":          20,
    "max_hp":      20,
    "attack":      5,
    "damage_dice": "1d6",
    "defense":     2,
    "xp":          40,
    "gold":        10
  }
}
```

**`damage_dice`** — the die rolled and added to `attack` each hit. Standard notation: `1d4`, `2d6`, `1d8+2`. Defaults to `1d6` if omitted.

**Stat guidelines:**

| Difficulty  | HP    | Attack | damage_dice | Defense | XP  | Gold |
|-------------|-------|--------|-------------|---------|-----|------|
| Trivial     | 8–12  | 2–3    | 1d3         | 0–1     | 15  | 0    |
| Easy        | 15–25 | 3–5    | 1d4         | 1–2     | 30  | 5    |
| Medium      | 30–50 | 6–9    | 1d6         | 3–4     | 60  | 15   |
| Hard        | 60+   | 10–16  | 1d8 or 2d6  | 5–8     | 120 | 30   |

Player starts with 100 HP, 10 attack, 4 defense, equipped with their starting weapon.

---

### Items

```json
"items": {
  "item_id": {
    "id":          "item_id",
    "name":        "Display Name",
    "file":        "item_id.md",
    "type":        "consumable",
    "heal":        40,
    "base_price":  20
  }
}
```

**Item types:**

| Type | Required fields | Effect |
|---|---|---|
| `consumable` | `heal` (int) | Restores HP on use. Removed from inventory. |
| `weapon` | `damage_dice`, `damage_bonus` (int) | Equippable. Changes damage roll. |

**Weapon example:**
```json
"short_sword": {
  "id":           "short_sword",
  "name":         "Short Sword",
  "file":         "short_sword.md",
  "type":         "weapon",
  "damage_dice":  "1d6",
  "damage_bonus": 1,
  "base_price":   35
}
```

Player damage = `attack stat + weapon dice roll + damage_bonus - enemy defense`. Minimum 1.

---

### NPCs

References to NPC files. The personality and behaviour live in the `.md` file (Step 4).

```json
"npcs": {
  "npc_id": {
    "name":           "Display Name",
    "title":          "optional subtitle shown next to name",
    "persuadability": 5,
    "file":           "npc_id.md"
  }
}
```

**Persuadability (1–10):** How open the NPC is to negotiation and charm.
- 1–3: Resistant. Holds firm. Only yields to exceptional arguments.
- 4–6: Moderate. Open to reason.
- 7–10: Eager negotiator. Enjoys the sport of it.

---

### Quests

```json
"quests": {
  "quest_id": {
    "id":          "quest_id",
    "name":        "Display Name",
    "file":        "quest_id.md",
    "giver_npc":   "npc_id",
    "objectives": [
      {
        "id":          "objective_id",
        "description": "Shown in quest log.",
        "type":        "kill_all_in_room",
        "room":        "room_id"
      }
    ],
    "reward": {
      "gold": 50,
      "xp":   100
    },
    "complete_npc": "npc_id"
  }
}
```

**Objective types:**
- `kill_all_in_room` — complete when all enemies in the specified room are dead.

**Quest flow:**
1. `giver_npc` starts the quest via the `start_quest` action in conversation.
2. Player completes objectives.
3. Player returns to `complete_npc` (can be the same or different NPC).
4. That NPC triggers `complete_quest` — reward is given automatically.

The reward gold can be negotiated by a persuadable NPC. XP is always the full amount.

---

## Step 3 — Room .md Files

Each room has one `.md` file. The `## Description` section is shown to the player when they look around. All other sections are guidance for the narrator AI — richer atmosphere means more interesting answers to player questions.

### Template

```markdown
# Room Name

## Description
Shown to the player on 'look'. Present tense. Atmospheric.
Do not mention exits or people — those are added automatically.

## Atmosphere
What the room feels like beyond the visible. Sounds, smells, temperature.
What a stranger might feel standing here. The narrator draws on this.

## Notable Features
- Specific objects or details the narrator can describe or reveal
- Each bullet is something a player could ask about
- Be specific enough that descriptions are consistent across sessions

## Secrets
Things the narrator can hint at or reveal when players ask specific questions.
Things that are true but not immediately obvious.
Don't reveal these unprompted — only when earned.

## Sounds and Smells
Sensory details. The narrator uses these to make the room feel inhabited.
```

---

## Step 4 — Enemy .md Files

One file per enemy *type* — multiple instances can share the same file (e.g. all three goblins use `goblin.md`).

### Template

```markdown
# Enemy Name

## Description
One or two sentences shown at the start of combat.
Visceral and specific. Sets the tone for the fight.

## Combat Behavior
How this creature fights. Aggressive or cautious? Tactical or frenzied?
Does it retreat? Does it have a pattern? This shapes future AI combat commentary.

## Combat Flavor
Specific attack descriptions the system can draw on:
- It lunges forward, claws extended.
- A wild swing that clips your shoulder.

## Lore
What a knowledgeable person might know about this creature.
The narrator can draw on this if asked. Optional.
```

---

## Step 5 — Item .md Files

Short files. Mostly for flavor — the player sees these in their inventory and when examining items.

### Template

```markdown
# Item Name

## Description
One or two sentences. What the player sees when they look at it.
Write it as the item itself, not its stats.

## Lore
Where it came from, who made it, why it matters. Optional.
The narrator can reference this if asked about the item.
```

---

## Step 6 — Quest .md Files

The narrative layer over the mechanical quest definition.

### Template

```markdown
# Quest Name

## Description
Shown in the player's quest log. One or two sentences.
What the player knows they're supposed to do.

## Background
The full story. Why does this quest exist?
What happened before the player arrived?
This gives NPCs context for realistic, motivated dialogue.

## Narrative Notes
Guidance for NPCs involved in this quest.
- How should the giver feel when asking for help?
- How should they react when it's done?
- Is there subtext? Guilt? Relief? Anger?
- What should the player feel during and after?
```

---

## Step 7 — NPC .md Files

Each NPC has one `.md` file. This is the character sheet Claude reads before every conversation. Write it as if briefing an actor — they need to understand the character, not just follow rules.

### Template

```markdown
# Name

## Description
One paragraph. Physical appearance, demeanour, role in the world.
What a stranger would notice first.

## Personality
How they speak. What they care about. What they want.
What gets under their skin. How they treat strangers.
Use specific, concrete details — not "friendly" but "laughs at their own jokes before finishing them".

## Persuadability: X/10
What persuades THIS character specifically.
What doesn't work. What they respond to.
What their hard limits are.

## Available Actions
List only actions this NPC can take. The game engine only processes these.

- start_quest: <quest_id>
- complete_quest: <quest_id>
- sell_item: <item_id>
- give_item: <item_id>

## Knowledge
Bullet list of things this NPC knows about the world.
Be specific. Also note what they *don't* know — it's just as important.

## Notes (optional)
Relationships with other NPCs, secrets they keep, things they'll never say.
```

---

### Available Action Reference

| Action | When to trigger | Required fields |
|---|---|---|
| `start_quest: <id>` | Player clearly agrees to take the quest | quest_id |
| `complete_quest: <id>` | Acknowledging a completed quest | quest_id, optionally `value` (gold) if negotiated |
| `sell_item: <id>` | Player agrees to buy | item_id, `value` (final price in gold) |
| `give_item: <id>` | Giving something freely | item_id |

**Important:** Claude triggers these when the conversation makes it narratively appropriate. The more specific your Available Actions section, the more reliably it fires.

---

## Tips for Good Modules

**Rooms**
- Write descriptions that reward curiosity. The narrator AI can expand on them, but the base description sets the tone.
- The `## Secrets` section is where you hide things for curious players to discover — a stain, a gap in the wall, a name carved in wood.
- Limit rooms to what you can make interesting. 3 compelling rooms beat 10 empty ones.

**Enemies**
- The `## Combat Behavior` and `## Combat Flavor` sections will power future AI combat commentary. Write them now even if not used yet.
- Multiple instances sharing one `.md` file is fine — they'll have the same character, just different HP.
- Enemies that guard something meaningful are more satisfying than encounters that exist just to fill space.

**Items**
- `## Lore` is optional but adds depth. A sword with a story is more interesting than a sword with stats.
- Item descriptions should read like the player is looking at the thing, not reading a label.

**Quests**
- The `## Narrative Notes` in the quest file should be specific about *emotional* beats, not just mechanical flow.
- Let the `complete_npc`'s reaction to completion mean something. That's what the AI is for.
- One clear goal is better than three vague ones.

**NPCs**
- The best NPCs have a want. What do they need? What are they afraid of? What are they hiding?
- Give them opinions about other NPCs and places. Cross-references make the world feel real.
- Resist making every NPC a quest-giver. A character who just *exists* and has things to say adds richness.

**The `.md` files are the heart of your module.** Spend more time on them than on the JSON. A mediocre `world.json` with excellent character and room files will play better than the reverse.

---

## Validation Checklist

Before testing your module, verify:

- [ ] `module.json` exists with a valid `id` matching the directory name
- [ ] `start_room` exists in `rooms`
- [ ] Every room's `file` exists in `rooms/`
- [ ] Every room referenced in an exit exists
- [ ] Every enemy ID in a room's `enemies` list exists in `enemies`
- [ ] Every enemy's `file` exists in `enemies/`
- [ ] Every NPC ID in a room's `npcs` list exists in `npcs`
- [ ] Every NPC's `file` exists in `npcs/`
- [ ] Every item's `file` exists in `items/`
- [ ] Every quest's `file` exists in `quests/`
- [ ] Every quest's `giver_npc` and `complete_npc` exist in `npcs`
- [ ] Every quest objective's `room` exists in `rooms`
- [ ] Every item referenced in NPC `.md` Available Actions exists in `items`
- [ ] All `quest_id` values in NPC `.md` files match a key in `quests`
- [ ] All `damage_dice` values use valid notation (`1d6`, `2d4+1`, etc.)

---

## Example Prompt for Claude Code

> Read CREATE_MODULE.md, then create a complete module called `lighthouse` set in an abandoned lighthouse on a stormy coast. There should be 4 rooms, a ghost NPC who gives a quest, a merchant who arrived by shipwreck, and a sea creature as the final enemy. Make the ghost tragic, not threatening. All files should be production-ready and pass the validation checklist.
