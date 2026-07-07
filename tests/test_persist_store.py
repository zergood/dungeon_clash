"""T1 — SQLite store: sessions, append-only log, SQL stats, meta."""

from __future__ import annotations

from dungeon_clash.adapters.persist import LogRow, Store


def test_session_save_is_upsert() -> None:
    with Store() as store:
        assert store.get_session() is None
        store.save_session(
            seed=1, strategy_name="cautious", tick=5, last_checked_at=100.0, snapshot='{"a":1}'
        )
        row = store.get_session()
        assert row is not None
        assert row["tick"] == 5
        assert row["snapshot"] == '{"a":1}'

        store.save_session(
            seed=1, strategy_name="cautious", tick=9, last_checked_at=200.0, snapshot="{}"
        )
        row = store.get_session()
        assert row is not None
        assert row["tick"] == 9  # updated, not duplicated


def _sample_rows() -> list[LogRow]:
    return [
        LogRow(0, "encounter_started", "Orc", None, "{}"),
        LogRow(0, "attack_resolved", "Hero", 10, "{}"),
        LogRow(0, "attack_resolved", "Orc", 5, "{}"),
        LogRow(1, "combat_defeated", "Hero", None, "{}"),
        LogRow(1, "run_ended", "died", None, "{}"),
    ]


def test_log_append_read_and_ordering() -> None:
    with Store() as store:
        store.append_log(_sample_rows())
        assert store.count_log() == 5

        last2 = store.read_log(last=2)
        assert [r["kind"] for r in last2] == ["combat_defeated", "run_ended"]

        allrows = store.read_log()
        assert next(r["kind"] for r in allrows) == "encounter_started"


def test_stats_are_computed_in_sql() -> None:
    with Store() as store:
        store.append_log(_sample_rows())
        s = store.stats("Hero")
        assert s["damage_dealt"] == 10
        assert s["damage_taken"] == 5
        assert s["kills"] == 1
        assert s["deaths"] == 1
        assert s["enemies_seen"] == 1
        assert s["turns"] == 2  # max tick 1, +1


def test_stats_on_empty_log() -> None:
    with Store() as store:
        s = store.stats("Hero")
        assert s == {
            "turns": 0,
            "enemies_seen": 0,
            "kills": 0,
            "deaths": 0,
            "damage_dealt": 0,
            "damage_taken": 0,
        }


def test_reset_clears_session_and_log() -> None:
    with Store() as store:
        store.save_session(
            seed=1, strategy_name="cautious", tick=1, last_checked_at=0.0, snapshot="{}"
        )
        store.append_log(_sample_rows())
        store.reset()
        assert store.get_session() is None
        assert store.count_log() == 0


def test_meta_kv_upserts() -> None:
    with Store() as store:
        assert store.meta_get("total_kills") is None
        store.meta_set("total_kills", "3")
        assert store.meta_get("total_kills") == "3"
        store.meta_set("total_kills", "7")
        assert store.meta_get("total_kills") == "7"
