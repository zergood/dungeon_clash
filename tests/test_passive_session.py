"""T2/T8 — the passive engine: determinism, lazy==stepwise, round-trip."""

from __future__ import annotations

from dungeon_clash.content import load_enemies
from dungeon_clash.core import Combatant
from dungeon_clash.passive import EnemyAppeared, PassiveSession, advance, new_session
from dungeon_clash.strategy import cautious, flee_when_low
from dungeon_clash.strategy.events import Fled

POOL = list(load_enemies().values())


def _advance(session: PassiveSession, to: int) -> tuple[PassiveSession, list[object]]:
    return advance(session, to, strategy=cautious, enemy_pool=POOL)


def test_lazy_catch_up_equals_stepwise() -> None:
    """Advancing 25 ticks at once == advancing one tick 25 times."""
    start = new_session(7, "cautious")

    one_shot, log_one = _advance(start, 25)

    step_state = start
    log_step: list[object] = []
    for _ in range(25):
        step_state, entries = _advance(step_state, step_state.tick + 1)
        log_step.extend(entries)

    assert one_shot == step_state
    assert log_one == log_step


def test_advance_is_deterministic_per_seed() -> None:
    def play(seed: int) -> list[dict[str, object]]:
        _, log = _advance(new_session(seed, "cautious"), 30)
        return [e.event.model_dump() for e in log]  # type: ignore[attr-defined]

    assert play(11) == play(11)
    assert play(1) != play(2)


def test_session_round_trips_through_json() -> None:
    advanced, _ = _advance(new_session(3, "cautious"), 12)
    restored = PassiveSession.model_validate_json(advanced.model_dump_json())
    assert restored == advanced

    # And resuming from the restored snapshot is bit-identical (save/load safety).
    a, _ = _advance(advanced, 24)
    b, _ = _advance(restored, 24)
    assert a == b


def test_enemies_appear_and_are_defeated() -> None:
    final, log = _advance(new_session(5, "cautious"), 80)
    assert any(isinstance(e.event, EnemyAppeared) for e in log)
    assert final.kills >= 1


def test_no_op_advance_returns_same_state() -> None:
    s = new_session(1, "cautious")
    same, log = _advance(s, 0)
    assert same is s
    assert log == []


def test_fleeing_hero_disengages_each_tick() -> None:
    weak = Combatant(name="Hero", hp=20, max_hp=100, atk_bp=10_000, block_bp=3_000)
    session = new_session(2, "flee_when_low", hero=weak)
    final, log = advance(session, 3, strategy=flee_when_low, enemy_pool=POOL)

    assert final.tick == 3
    assert final.hero.hp == 20  # fled before taking a hit
    assert sum(isinstance(e.event, Fled) for e in log) == 3
