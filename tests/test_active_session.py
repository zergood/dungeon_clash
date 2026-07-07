"""T8 — the (superseded) simple active module: manual turns over an enemy loop.

The run-session that the CLI actually uses is exercised in test_run_session.py;
these keep the reusable per-turn helpers covered.
"""

from __future__ import annotations

from dungeon_clash.active import ensure_enemy, play_turn
from dungeon_clash.content import load_enemies
from dungeon_clash.core import CombatAction, Zone
from dungeon_clash.passive import new_session

POOL = list(load_enemies().values())


def test_ensure_enemy_spawns_then_is_idempotent() -> None:
    s0 = new_session(3, "cautious")
    assert s0.enemy is None
    s1, entries = ensure_enemy(s0, POOL)
    assert s1.enemy is not None
    assert len(entries) == 1

    s2, entries2 = ensure_enemy(s1, POOL)
    assert s2 is s1  # already have a live foe
    assert entries2 == []


def test_play_turn_advances_and_is_deterministic() -> None:
    s0 = new_session(7, "cautious")
    action = CombatAction(attack=Zone.HEAD, defend=Zone.HEAD)

    a, log_a = play_turn(s0, action, POOL)
    b, log_b = play_turn(s0, action, POOL)
    assert a == b  # same session + action → same outcome
    assert a.tick == s0.tick + 1
    assert [e.event.model_dump() for e in log_a] == [e.event.model_dump() for e in log_b]
