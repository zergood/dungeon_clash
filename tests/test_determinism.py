"""T4 — determinism / replay, the cornerstone test (IMPLEMENTATION_PLAN.md).

Same seed + same actions must produce a byte-for-byte identical event stream.
This single guarantee underpins traceable combat logs, passive catch-up
simulation, and MMO replay anti-cheat.
"""

from __future__ import annotations

from dungeon_clash.core import CombatAction, Combatant, CombatState, Enemy, Rng, Zone, step
from dungeon_clash.core.events import Event


def _fixed_strategy(state: CombatState) -> CombatAction:
    if state.hero.hp_pct < 0.4:
        return CombatAction(attack=Zone.LEGS, defend=Zone.HEAD)
    return CombatAction(attack=Zone.TORSO, defend=Zone.HEAD)


def _play_out(seed: int) -> list[dict[str, object]]:
    rng = Rng(seed)
    hero = Combatant(name="Hero", hp=90, max_hp=90, atk_bp=11_000, block_bp=6_500)
    enemy = Enemy(
        name="Orc",
        template_id="orc",
        hp=100,
        max_hp=100,
        atk_bp=10_500,
        block_bp=5_500,
        bias=(Zone.HEAD, Zone.HEAD, Zone.TORSO),
    )
    state = CombatState(hero=hero, enemy=enemy)
    log: list[Event] = []
    guard = 0
    while not state.over and guard < 1000:
        state, events = step(state, _fixed_strategy(state), rng)
        log.extend(events)
        guard += 1
    return [e.model_dump() for e in log]


def test_same_seed_same_actions_identical_log() -> None:
    assert _play_out(42) == _play_out(42)


def test_different_seeds_generally_diverge() -> None:
    # Not a hard guarantee, but with these stats the RNG stream clearly differs.
    assert _play_out(1) != _play_out(2)


def test_fight_terminates() -> None:
    log = _play_out(2024)
    assert log, "fight produced no events"
    assert log[-1]["kind"] == "combat_defeated"
