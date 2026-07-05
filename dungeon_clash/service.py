"""Application service: wires the passive engine to storage and the clock.

This is the seam the CLI (and later the TUI) calls. It owns the *impure* bits —
where the save file lives, what "now" is, how wall-clock maps to ticks — so the
passive engine underneath stays a pure, reproducible function. Time is always
passed in, never read here, which keeps the service testable without sleeping.
"""

from __future__ import annotations

import os
from pathlib import Path

from dungeon_clash.adapters.persist import LogRow, Store
from dungeon_clash.content import load_enemies
from dungeon_clash.content.schema import EnemyTemplate
from dungeon_clash.core.events import AttackResolved, CombatDefeated
from dungeon_clash.passive import (
    EnemyAppeared,
    LogEntry,
    PassiveSession,
    advance,
    new_session,
    resolve_strategy,
)

#: How much real time one autonomous turn represents. Deliberately coarse so a
#: glance shows visible progress; overridable via the environment.
DEFAULT_SECONDS_PER_TICK = 2.0


def seconds_per_tick() -> float:
    raw = os.environ.get("DUNGEON_CLASH_SECONDS_PER_TICK")
    return float(raw) if raw else DEFAULT_SECONDS_PER_TICK


def default_db_path() -> Path:
    """Save-file location: ``$DUNGEON_CLASH_HOME`` or an XDG data dir."""
    home = os.environ.get("DUNGEON_CLASH_HOME")
    base = Path(home) if home else Path.home() / ".local" / "share" / "dungeon_clash"
    return base / "save.db"


def enemy_pool() -> list[EnemyTemplate]:
    """The current pool of enemies to draw from (Phase 5 makes this per-floor)."""
    return list(load_enemies().values())


def _to_row(entry: LogEntry) -> LogRow:
    """Denormalize an event for indexed/aggregatable storage."""
    ev = entry.event
    actor: str | None = None
    damage: int | None = None
    if isinstance(ev, AttackResolved):
        actor, damage = ev.attacker, ev.damage
    elif isinstance(ev, CombatDefeated):
        actor = ev.winner
    elif isinstance(ev, EnemyAppeared):
        actor = ev.name
    return LogRow(
        tick=entry.tick, kind=ev.kind, actor=actor, damage=damage, payload=ev.model_dump_json()
    )


def start_session(store: Store, *, seed: int, strategy_name: str, now: float) -> PassiveSession:
    """Begin a fresh passive run, replacing any existing one."""
    resolve_strategy(strategy_name)  # validate up front (raises on unknown)
    store.reset()
    session = new_session(seed, strategy_name)
    store.save_session(
        seed=seed,
        strategy_name=strategy_name,
        tick=0,
        last_checked_at=now,
        snapshot=session.model_dump_json(),
    )
    return session


def catch_up(
    store: Store, *, now: float, secs_per_tick: float | None = None
) -> PassiveSession | None:
    """Advance the stored session to reflect elapsed real time, then persist.

    Returns the up-to-date session, or ``None`` if no run has been started. Only
    whole ticks are consumed; the sub-tick remainder is carried forward, so no
    time is ever lost (GDD §4.3).
    """
    row = store.get_session()
    if row is None:
        return None

    spt = secs_per_tick if secs_per_tick is not None else seconds_per_tick()
    session = PassiveSession.model_validate_json(row["snapshot"])
    elapsed = float(now) - float(row["last_checked_at"])
    gained = max(0, int(elapsed / spt))
    target = session.tick + gained

    strategy = resolve_strategy(session.strategy_name)
    pool = list(load_enemies().values())
    session, entries = advance(session, target, strategy=strategy, enemy_pool=pool)

    if entries:
        store.append_log([_to_row(e) for e in entries])
    consumed = gained * spt
    store.save_session(
        seed=session.seed,
        strategy_name=session.strategy_name,
        tick=session.tick,
        last_checked_at=float(row["last_checked_at"]) + consumed,
        snapshot=session.model_dump_json(),
    )
    return session


def persist_turn(
    store: Store, session: PassiveSession, entries: list[LogEntry], *, now: float
) -> None:
    """Persist one active-mode turn.

    Wall-clock is reset to ``now`` so time the player spent at the keyboard is
    consumed by play, not double-counted as passive simulation afterwards.
    """
    if entries:
        store.append_log([_to_row(e) for e in entries])
    store.save_session(
        seed=session.seed,
        strategy_name=session.strategy_name,
        tick=session.tick,
        last_checked_at=now,
        snapshot=session.model_dump_json(),
    )
