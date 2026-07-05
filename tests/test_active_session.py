"""T8 — active mode: manual turns and passive↔active continuity."""

from __future__ import annotations

from dungeon_clash import service
from dungeon_clash.active import ensure_enemy, play_turn
from dungeon_clash.adapters.persist import Store
from dungeon_clash.content import load_enemies
from dungeon_clash.core import CombatAction, Zone
from dungeon_clash.passive import PassiveSession, new_session

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


def test_mode_switch_round_trip_preserves_progress() -> None:
    with Store() as store:
        service.start_session(store, seed=3, strategy_name="cautious", now=0.0)

        # passive catch-up: 5 ticks
        passive = service.catch_up(store, now=10.0, secs_per_tick=2.0)
        assert passive is not None
        assert passive.tick == 5

        # active: player takes 2 manual turns, persisted
        session = PassiveSession.model_validate_json(store.get_session()["snapshot"])
        for _ in range(2):
            session, entries = play_turn(
                session, CombatAction(attack=Zone.HEAD, defend=Zone.HEAD), POOL
            )
            service.persist_turn(store, session, entries, now=100.0)
        assert session.tick == 7

        # passive resumes from exactly where active left off (tick 7), +5 ticks
        resumed = service.catch_up(store, now=110.0, secs_per_tick=2.0)
        assert resumed is not None
        assert resumed.tick == 12
        assert resumed.seed == 3
