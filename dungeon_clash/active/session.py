"""Manual, player-driven turn advancement for active mode."""

from __future__ import annotations

from collections.abc import Sequence

from dungeon_clash.content.schema import EnemyTemplate
from dungeon_clash.core import CombatAction, CombatState, Rng, step
from dungeon_clash.passive.events import EnemyAppeared
from dungeon_clash.passive.session import LogEntry, PassiveSession, resolve_defeats, spawn_from


def ensure_enemy(
    session: PassiveSession, pool: Sequence[EnemyTemplate]
) -> tuple[PassiveSession, list[LogEntry]]:
    """Make sure there is a living enemy to fight, spawning one if needed.

    Uses (and advances) the session RNG so the encounter the player faces is the
    same one the passive strategy would have met.
    """
    if session.enemy is not None and session.enemy.alive:
        return session, []
    rng = Rng(session.seed)
    rng.setstate(session.rng_state)
    enemy = spawn_from(pool, rng)
    updated = session.model_copy(update={"enemy": enemy, "rng_state": rng.getstate()})
    return updated, [LogEntry(session.tick, EnemyAppeared(name=enemy.name, hp=enemy.hp))]


def play_turn(
    session: PassiveSession, action: CombatAction, pool: Sequence[EnemyTemplate]
) -> tuple[PassiveSession, list[LogEntry]]:
    """Resolve one player-chosen turn against the current enemy.

    Shares the exact combat and bookkeeping of passive mode (same core
    ``step``), so switching modes never changes the rules — only who decides.
    """
    session, entries = ensure_enemy(session, pool)
    assert session.enemy is not None

    rng = Rng(session.seed)
    rng.setstate(session.rng_state)
    cstate = CombatState(hero=session.hero, enemy=session.enemy)
    cstate, events = step(cstate, action, rng)
    entries.extend(LogEntry(session.tick, ev) for ev in events)

    hero, enemy, kills, deaths, extra = resolve_defeats(
        cstate.hero, cstate.enemy, session.kills, session.deaths, session.tick
    )
    entries.extend(extra)

    updated = session.model_copy(
        update={
            "hero": hero,
            "enemy": enemy,
            "kills": kills,
            "deaths": deaths,
            "tick": session.tick + 1,
            "rng_state": rng.getstate(),
        }
    )
    return updated, entries
