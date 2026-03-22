"""
Quest tracking.
"""

from . import renderer as R

# Quest statuses
NOT_STARTED = "not_started"
ACTIVE = "active"
COMPLETE = "complete"   # objectives done, reward not yet given
REWARDED = "rewarded"   # reward given


class QuestManager:
    def __init__(self, quest_defs: dict):
        self.defs = quest_defs
        self.status: dict[str, str] = {qid: NOT_STARTED for qid in quest_defs}

    def start(self, quest_id: str):
        if self.status.get(quest_id) == NOT_STARTED:
            self.status[quest_id] = ACTIVE
            qname = self.defs[quest_id]["name"]
            R.print_quest_update(f"New quest started: {qname}")

    def check_objectives(self, world, current_room_id: str):
        """Check if any active quest objectives are now met."""
        for qid, qdef in self.defs.items():
            if self.status[qid] != ACTIVE:
                continue
            all_met = True
            for obj in qdef["objectives"]:
                if obj["type"] == "kill_all_in_room":
                    room_id = obj["room"]
                    if not world.all_enemies_dead_in_room(room_id):
                        all_met = False
                        break
            if all_met:
                self.status[qid] = COMPLETE
                qname = qdef["name"]
                R.print_quest_update(f"Objective complete: {qname} — return to claim your reward!")

    def give_reward(self, quest_id: str, player, gold_override: int = None) -> bool:
        """Give quest reward to player. Returns True if reward was given."""
        if self.status.get(quest_id) != COMPLETE:
            return False
        qdef = self.defs[quest_id]
        reward = qdef.get("reward", {})
        gold = gold_override if gold_override is not None else reward.get("gold", 0)
        xp = reward.get("xp", 0)
        player.gold += gold
        levelled = player.gain_xp(xp)
        self.status[quest_id] = REWARDED
        if gold:
            R.print_success(f"+{gold} gold")
        if xp:
            R.print_success(f"+{xp} XP")
        if levelled:
            R.print_level_up(player.level)
        return True

    def is_active(self, quest_id: str) -> bool:
        return self.status.get(quest_id) == ACTIVE

    def is_complete(self, quest_id: str) -> bool:
        return self.status.get(quest_id) == COMPLETE

    def is_rewarded(self, quest_id: str) -> bool:
        return self.status.get(quest_id) == REWARDED

    def summary_for_npc(self, world) -> str:
        """Human-readable quest state for NPC system prompts."""
        lines = []
        for qid, qdef in self.defs.items():
            status = self.status[qid]
            if status == NOT_STARTED:
                lines.append(f"Quest '{qdef['name']}': not yet offered")
            elif status == ACTIVE:
                # Check if objectives are actually met
                all_met = world.all_enemies_dead_in_room(qdef["objectives"][0].get("room", ""))
                if all_met:
                    lines.append(f"Quest '{qdef['name']}': COMPLETE — player has killed all rats and is awaiting your reward")
                else:
                    lines.append(f"Quest '{qdef['name']}': active (player working on it)")
            elif status == COMPLETE:
                lines.append(f"Quest '{qdef['name']}': COMPLETE — player has killed all rats and is awaiting your reward")
            elif status == REWARDED:
                lines.append(f"Quest '{qdef['name']}': already rewarded — do not offer again")
        return "\n".join(lines) if lines else "(no quests)"

    def show(self):
        has_any = False
        for qid, qdef in self.defs.items():
            status = self.status[qid]
            if status == NOT_STARTED:
                continue
            has_any = True
            from . import renderer as R
            name = qdef["name"]
            desc = qdef["description"]
            if status == ACTIVE:
                marker = f"{R.BRIGHT_YELLOW}[ACTIVE]{R.RESET}"
            elif status == COMPLETE:
                marker = f"{R.BRIGHT_GREEN}[COMPLETE - claim reward]{R.RESET}"
            elif status == REWARDED:
                marker = f"{R.DIM}{R.WHITE}[DONE]{R.RESET}"
            print(f"\n  {marker} {R.BRIGHT_WHITE}{name}{R.RESET}")
            print(f"  {R.DIM}{R.WHITE}{desc}{R.RESET}")
        if not has_any:
            R.print_info("No active quests.")
