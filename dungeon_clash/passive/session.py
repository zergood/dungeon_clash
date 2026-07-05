"""Passive session state and its deterministic advancement."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

from dungeon_clash.content.schema import EnemyTemplate
from dungeon_clash.core import Combatant, CombatState, Enemy, Rng, step
from dungeon_clash.core.events import Event
from dungeon_clash.core.rng import RngState
from dungeon_clash.passive.events import EnemyAppeared, HeroDown
from dungeon_clash.strategy import Control, decide_turn
from dungeon_clash.strategy.protocol import Strategy


@dataclass(frozen=True)
class LogEntry:
    """One event stamped with the tick it happened on."""

    tick: int
    event: Event


class PassiveSession(BaseModel):
    """Everything needed to resume an autonomous run bit-for-bit."""

    model_config = ConfigDict(frozen=True)

    seed: int
    strategy_name: str
    hero: Combatant
    enemy: Enemy | None = None
    tick: int = 0
    kills: int = 0
    deaths: int = 0
    rng_state: RngState


def default_hero(name: str = "Aeldric") -> Combatant:
    """A standard starting hero (GDD Warrior-ish baseline)."""
    return Combatant(name=name, hp=100, max_hp=100, atk_bp=11_000, block_bp=6_500)


def new_session(seed: int, strategy_name: str, *, hero: Combatant | None = None) -> PassiveSession:
    """Create a fresh session with its RNG seeded and ready."""
    return PassiveSession(
        seed=seed,
        strategy_name=strategy_name,
        hero=hero if hero is not None else default_hero(),
        rng_state=Rng(seed).getstate(),
    )


def spawn_from(pool: Sequence[EnemyTemplate], rng: Rng) -> Enemy:
    """Draw and roll a fresh enemy from a pool (deterministic via ``rng``)."""
    return rng.choice(pool).spawn(rng)


def resolve_defeats(
    hero: Combatant, enemy: Enemy, kills: int, deaths: int, tick: int
) -> tuple[Combatant, Enemy | None, int, int, list[LogEntry]]:
    """Post-turn bookkeeping shared by passive and active modes.

    ``enemy`` is the just-stepped (non-None) enemy. Counts a kill and/or a death,
    recovers the hero (death penalties arrive in Phase 5), and clears the enemy
    so a fresh one spawns next turn.
    """
    entries: list[LogEntry] = []
    surviving: Enemy | None = enemy
    if not enemy.alive:
        kills += 1
        surviving = None
    if not hero.alive:
        deaths += 1
        hero = hero.model_copy(update={"hp": hero.max_hp})
        surviving = None
        entries.append(LogEntry(tick, HeroDown(deaths=deaths)))
    return hero, surviving, kills, deaths, entries


def advance(
    session: PassiveSession,
    to_tick: int,
    *,
    strategy: Strategy,
    enemy_pool: Sequence[EnemyTemplate],
) -> tuple[PassiveSession, list[LogEntry]]:
    """Simulate turns until ``session.tick`` reaches ``to_tick``.

    One tick == one combat turn. When there is no living enemy, a new one is
    drawn from ``enemy_pool`` (deterministically, via the session RNG) before
    the turn resolves. Fully reproducible: advancing 100 ticks at once equals
    advancing one tick a hundred times.
    """
    if to_tick <= session.tick:
        return session, []

    rng = Rng(session.seed)
    rng.setstate(session.rng_state)

    hero = session.hero
    enemy = session.enemy
    kills = session.kills
    deaths = session.deaths
    tick = session.tick
    log: list[LogEntry] = []

    while tick < to_tick:
        if enemy is None or not enemy.alive:
            enemy = spawn_from(enemy_pool, rng)
            log.append(LogEntry(tick, EnemyAppeared(name=enemy.name, hp=enemy.hp)))

        cstate = CombatState(hero=hero, enemy=enemy)
        decision = decide_turn(strategy, cstate)
        log.extend(LogEntry(tick, ev) for ev in decision.events)

        if decision.control is Control.FLEE:
            enemy = None  # hero disengages; a new foe arrives next tick
            tick += 1
            continue

        assert decision.action is not None
        cstate, events = step(cstate, decision.action, rng)
        log.extend(LogEntry(tick, ev) for ev in events)

        hero, enemy, kills, deaths, extra = resolve_defeats(
            cstate.hero, cstate.enemy, kills, deaths, tick
        )
        log.extend(extra)
        tick += 1

    new = session.model_copy(
        update={
            "hero": hero,
            "enemy": enemy,
            "kills": kills,
            "deaths": deaths,
            "tick": tick,
            "rng_state": rng.getstate(),
        }
    )
    return new, log
