"""T8 — application service: start, lazy catch-up, remainder carry."""

from __future__ import annotations

import pytest

from dungeon_clash import service
from dungeon_clash.adapters.persist import Store


def test_start_then_catch_up_advances_by_elapsed() -> None:
    with Store() as store:
        service.start_session(store, seed=1, strategy_name="cautious", now=1000.0)
        # 20s later at 2s/tick → 10 ticks.
        session = service.catch_up(store, now=1020.0, secs_per_tick=2.0)
        assert session is not None
        assert session.tick == 10
        assert store.count_log() > 0


def test_catch_up_without_session_returns_none() -> None:
    with Store() as store:
        assert service.catch_up(store, now=1.0, secs_per_tick=2.0) is None


def test_start_rejects_unknown_strategy() -> None:
    with Store() as store, pytest.raises(ValueError, match="unknown strategy"):
        service.start_session(store, seed=1, strategy_name="nope", now=0.0)


def test_sub_tick_remainder_is_carried_forward() -> None:
    with Store() as store:
        service.start_session(store, seed=1, strategy_name="cautious", now=0.0)
        session = service.catch_up(store, now=3.0, secs_per_tick=2.0)  # 1 tick, 1s left over
        assert session is not None
        assert session.tick == 1
        row = store.get_session()
        assert row is not None
        assert row["last_checked_at"] == 2.0  # consumed one tick's worth, remainder kept


def test_two_catch_ups_equal_one_big_one() -> None:
    def collect(offsets: list[float]) -> tuple[int, list[tuple[int, str, int | None]]]:
        with Store() as store:
            service.start_session(store, seed=9, strategy_name="cautious", now=0.0)
            for now in offsets:
                service.catch_up(store, now=now, secs_per_tick=2.0)
            row = store.get_session()
            assert row is not None
            log = [(r["tick"], r["kind"], r["damage"]) for r in store.read_log()]
            return int(row["tick"]), log

    assert collect([40.0]) == collect([20.0, 40.0])
