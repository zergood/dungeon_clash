"""Temporary Phase-1/2 smoke demo.

Runs one fully deterministic fight, driven by a player-style *strategy*, so you
can see the core + strategy layer working end to end::

    dungeon              # default seed, a reference bot
    dungeon 12345        # explicit seed → identical replay every time
    dungeon 7 broken     # a deliberately buggy strategy → errors are logged

This is intentionally plain stdlib (no Typer/Rich yet). The real CLI is Phase 3.
"""

from __future__ import annotations

import sys

from dungeon_clash.content import load_enemies
from dungeon_clash.core import Combatant, CombatState, Rng
from dungeon_clash.core.events import AttackResolved, CombatDefeated
from dungeon_clash.strategy import cautious, run_combat
from dungeon_clash.strategy.events import Fled, InvalidAction, StrategyError
from dungeon_clash.strategy.protocol import Strategy


def _broken_strategy(state: CombatState) -> object:
    """A strategy with a bug — raises KeyError, as a player's might."""
    resources = {"gold": state.hero.hp}
    return resources["arcane_crystals"]  # KeyError: not in dict


def run_demo(seed: int, strategy: Strategy) -> None:
    rng = Rng(seed)
    hero = Combatant(name="Aeldric", hp=100, max_hp=100, atk_bp=11_000, block_bp=6_500)
    enemy = load_enemies()["orc_warrior"].spawn(rng)
    state = CombatState(hero=hero, enemy=enemy)

    print(f"Dungeon Clash — deterministic demo (seed={seed})")
    print(f"{hero.name} ({hero.hp} HP) vs {enemy.name} ({enemy.hp} HP)\n")

    final, log = run_combat(strategy, state, rng)
    for ev in log:
        if isinstance(ev, AttackResolved):
            guard = ev.defend_zone.display if ev.defend_zone else "—"
            print(
                f"  {ev.attacker} -> {ev.defender} [{ev.attack_zone.display}] "
                f"{ev.result.value:<7} {ev.damage:>3} dmg  "
                f"(guard {guard}; {ev.defender} @ {ev.defender_hp} HP)"
            )
        elif isinstance(ev, StrategyError):
            print(f"  [STRATEGY ERROR turn {ev.turn}: {ev.exc_type}: {ev.message}] turn skipped")
        elif isinstance(ev, InvalidAction):
            print(f"  [INVALID ACTION turn {ev.turn}: {ev.reason}] turn skipped")
        elif isinstance(ev, Fled):
            print(f"  {ev.who} flees the fight.")
        elif isinstance(ev, CombatDefeated):
            print(f"\n  {ev.winner} wins in {ev.turns} turns.")

    if not final.over:
        print("\n  (combat ended without a defeat — fled or capped)")


def app() -> None:
    """Entry point registered as the ``dungeon`` script."""
    seed = 1
    strategy: Strategy = cautious
    if len(sys.argv) > 1:
        try:
            seed = int(sys.argv[1])
        except ValueError:
            print(f"usage: dungeon [seed] [broken]  (got {sys.argv[1]!r})", file=sys.stderr)
            raise SystemExit(2) from None
    if len(sys.argv) > 2 and sys.argv[2] == "broken":
        strategy = _broken_strategy
    run_demo(seed, strategy)


if __name__ == "__main__":
    app()
