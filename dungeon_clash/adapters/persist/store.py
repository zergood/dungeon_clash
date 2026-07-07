"""SQLite-backed persistence for a passive run.

One save file holds a single active session (row ``id = 1``), an append-only
event log, and a small key/value meta table for cross-session progress. The log
is denormalized with ``kind``/``actor``/``damage`` columns so ``dungeon
log --stats`` is plain SQL aggregation; the full event is kept as JSON in
``payload`` for faithful display.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import Self

_SCHEMA = """
CREATE TABLE IF NOT EXISTS session (
    id             INTEGER PRIMARY KEY CHECK (id = 1),
    seed           INTEGER NOT NULL,
    strategy_name  TEXT    NOT NULL,
    tick           INTEGER NOT NULL,
    last_checked_at REAL   NOT NULL,
    snapshot       TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS event_log (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    tick    INTEGER NOT NULL,
    kind    TEXT    NOT NULL,
    actor   TEXT,
    damage  INTEGER,
    payload TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class LogRow:
    """A denormalized log entry ready for insertion."""

    tick: int
    kind: str
    actor: str | None
    damage: int | None
    payload: str


class Store:
    """A thin, typed wrapper over a SQLite save file."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        if isinstance(path, Path):
            path.parent.mkdir(parents=True, exist_ok=True)
            path = str(path)
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        self._conn.close()

    # ── session ────────────────────────────────────────────────────────────
    def get_session(self) -> sqlite3.Row | None:
        cur = self._conn.execute("SELECT * FROM session WHERE id = 1")
        row: sqlite3.Row | None = cur.fetchone()
        return row

    def save_session(
        self,
        *,
        seed: int,
        strategy_name: str,
        tick: int,
        last_checked_at: float,
        snapshot: str,
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO session (id, seed, strategy_name, tick, last_checked_at, snapshot)
            VALUES (1, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                seed = excluded.seed,
                strategy_name = excluded.strategy_name,
                tick = excluded.tick,
                last_checked_at = excluded.last_checked_at,
                snapshot = excluded.snapshot
            """,
            (seed, strategy_name, tick, last_checked_at, snapshot),
        )
        self._conn.commit()

    def reset(self) -> None:
        """Drop the current session and its log (used by ``dungeon start``)."""
        self._conn.execute("DELETE FROM session")
        self._conn.execute("DELETE FROM event_log")
        self._conn.commit()

    # ── event log ──────────────────────────────────────────────────────────
    def append_log(self, rows: list[LogRow]) -> None:
        self._conn.executemany(
            "INSERT INTO event_log (tick, kind, actor, damage, payload) VALUES (?, ?, ?, ?, ?)",
            [(r.tick, r.kind, r.actor, r.damage, r.payload) for r in rows],
        )
        self._conn.commit()

    def read_log(self, last: int | None = None) -> list[sqlite3.Row]:
        if last is None:
            cur = self._conn.execute("SELECT * FROM event_log ORDER BY id")
            return cur.fetchall()
        cur = self._conn.execute(
            "SELECT * FROM (SELECT * FROM event_log ORDER BY id DESC LIMIT ?) ORDER BY id",
            (last,),
        )
        return cur.fetchall()

    def count_log(self) -> int:
        cur = self._conn.execute("SELECT COUNT(*) AS n FROM event_log")
        return int(cur.fetchone()["n"])

    def stats(self, hero_name: str) -> dict[str, int]:
        """Aggregate combat stats (GDD §4.2), computed in SQL."""

        def scalar(sql: str, *params: object) -> int:
            cur = self._conn.execute(sql, params)
            return int(cur.fetchone()[0] or 0)

        return {
            "turns": scalar("SELECT COALESCE(MAX(tick), -1) + 1 FROM event_log"),
            "enemies_seen": scalar(
                "SELECT COUNT(*) FROM event_log WHERE kind = 'encounter_started'"
            ),
            "kills": scalar(
                "SELECT COUNT(*) FROM event_log WHERE kind = 'combat_defeated' AND actor = ?",
                hero_name,
            ),
            "deaths": scalar(
                "SELECT COUNT(*) FROM event_log WHERE kind = 'run_ended' AND actor = 'died'"
            ),
            "damage_dealt": scalar(
                "SELECT SUM(damage) FROM event_log WHERE kind = 'attack_resolved' AND actor = ?",
                hero_name,
            ),
            "damage_taken": scalar(
                "SELECT SUM(damage) FROM event_log "
                "WHERE kind = 'attack_resolved' AND actor IS NOT NULL AND actor != ?",
                hero_name,
            ),
        }

    # ── meta ───────────────────────────────────────────────────────────────
    def meta_get(self, key: str) -> str | None:
        cur = self._conn.execute("SELECT value FROM meta WHERE key = ?", (key,))
        row = cur.fetchone()
        return None if row is None else str(row["value"])

    def meta_set(self, key: str, value: str) -> None:
        self._conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) "
            "ON CONFLICT (key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        self._conn.commit()
