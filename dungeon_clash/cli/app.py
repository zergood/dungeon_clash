"""Temporary Phase-1 smoke demo.

Runs one fully deterministic fight so you can see the core working end to end::

    dungeon            # default seed
    dungeon 12345      # explicit seed → identical replay every time

This is intentionally plain stdlib (no Typer/Rich yet). The real CLI is Phase 3.
"""

from __future__ import annotations

import sys

from dungeon_clash.content import load_enemies
from dungeon_clash.core import CombatAction, Combatant, CombatState, Rng, Zone, step
from dungeon_clash.core.events import AttackResolved, CombatDefeated


def _scripted_action(state: CombatState) -> CombatAction:
    """A tiny hardcoded strategy: chip safely when hurt, swing big when healthy."""
    if state.hero.hp_pct < 0.35:
        return CombatAction(attack=Zone.LEGS, defend=Zone.HEAD)
    return CombatAction(attack=Zone.TORSO, defend=Zone.HEAD)


def run_demo(seed: int) -> None:
    rng = Rng(seed)
    hero = Combatant(name="Aeldric", hp=100, max_hp=100, atk_bp=11_000, block_bp=6_500)
    enemy = load_enemies()["orc_warrior"].spawn(rng)
    state = CombatState(hero=hero, enemy=enemy)

    print(f"Dungeon Clash — deterministic demo (seed={seed})")
    print(f"{hero.name} ({hero.hp} HP) vs {enemy.name} ({enemy.hp} HP)\n")

    while not state.over:
        state, events = step(state, _scripted_action(state), rng)
        for ev in events:
            if isinstance(ev, AttackResolved):
                print(
                    f"  turn {state.turn - 1:>2}: {ev.attacker} -> {ev.defender} "
                    f"[{ev.attack_zone.display}] {ev.result.value:<7} "
                    f"{ev.damage:>3} dmg  ({ev.defender} @ {ev.defender_hp} HP)"
                )
            elif isinstance(ev, CombatDefeated):
                print(f"\n  {ev.winner} wins in {ev.turns} turns.")


def app() -> None:
    """Entry point registered as the ``dungeon`` script."""
    seed = 1
    if len(sys.argv) > 1:
        try:
            seed = int(sys.argv[1])
        except ValueError:
            print(f"usage: dungeon [seed]  (got {sys.argv[1]!r})", file=sys.stderr)
            raise SystemExit(2) from None
    run_demo(seed)


if __name__ == "__main__":
    app()
