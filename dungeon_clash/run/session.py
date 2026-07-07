"""Resumable run session — the persistent, tick-by-tick form of a run.

Unlike :func:`dungeon_clash.run.engine.advance_run` (which plays a whole run in
one call), a :class:`RunSession` can be advanced a few turns at a time and
snapshotted between check-ins. That is what lets passive mode lazily catch up to
elapsed real time, and active mode take a single manual turn, over the *same*
run state. One tick == one combat turn; entering rooms and moving between floors
happen for free between ticks. When a run ends (death or extraction) its carried
resources are banked and a fresh run begins automatically.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from pydantic import BaseModel, ConfigDict

from dungeon_clash.content.schema import EnemyTemplate
from dungeon_clash.core import CombatAction, Combatant, CombatState, Enemy, Rng, is_breakdown, step
from dungeon_clash.core.events import Event
from dungeon_clash.core.models import ONE_X_BP
from dungeon_clash.core.rng import RngState
from dungeon_clash.core.stress import PANICKING_AT
from dungeon_clash.run.engine import (
    BREAKDOWN_GOLD_PENALTY_BP,
    BREAKDOWN_STRESS_AFTER,
    FIRST_CONTINUE_BONUS_BP,
    NEXT_CONTINUE_BONUS_BP,
    POST_WIN_HEAL,
    REST_COST,
    REST_HEAL,
    REST_RELIEF,
    _enemy_for,
    _heal,
    _rewards,
    _scaled,
)
from dungeon_clash.run.events import (
    Breakdown,
    EncounterStarted,
    Extracted,
    FloorCleared,
    Looted,
    RestTaken,
    RoomEntered,
    RunEnded,
    RunStarted,
)
from dungeon_clash.run.resources import Resources
from dungeon_clash.run.rooms import RoomType, generate_floor
from dungeon_clash.run.state import default_hero
from dungeon_clash.strategy import Control, decide_turn
from dungeon_clash.strategy.protocol import Strategy


@dataclass(frozen=True)
class LogEntry:
    tick: int
    event: Event


#: A run-session extract policy: given the session, bank the run or push deeper.
SessionExtractPolicy = Callable[["RunSession"], bool]


def default_extract_policy(session: RunSession) -> bool:
    """Bank the run when hurt or badly stressed; otherwise push deeper."""
    return session.hero.hp_pct < 0.4 or session.stress >= PANICKING_AT


class RunSession(BaseModel):
    """A run in progress, resumable and serializable."""

    model_config = ConfigDict(frozen=True)

    seed: int
    strategy_name: str
    hero: Combatant
    stress: int = 0
    resources: Resources = Resources()
    banked: Resources = Resources()  # meta: resources secured across runs (never lost)
    floor: int = 1
    room_index: int = 0
    floor_rooms: tuple[RoomType, ...]
    fight: CombatState | None = None
    kills: int = 0
    deaths: int = 0
    runs_completed: int = 0
    bonus_bp: int = ONE_X_BP
    tick: int = 0
    rng_state: RngState


def new_run_session(seed: int, strategy_name: str, *, hero: Combatant | None = None) -> RunSession:
    rng = Rng(seed)
    rooms = tuple(r.type for r in generate_floor(1, rng))
    return RunSession(
        seed=seed,
        strategy_name=strategy_name,
        hero=hero if hero is not None else default_hero(),
        floor_rooms=rooms,
        rng_state=rng.getstate(),
    )


@dataclass
class _Runner:
    """Mutable working state for advancing a run; rebuilt into a RunSession."""

    rng: Rng
    pool: Sequence[EnemyTemplate]
    extract_policy: SessionExtractPolicy
    seed: int
    strategy_name: str
    hero: Combatant
    stress: int
    resources: Resources
    banked: Resources
    floor: int
    room_index: int
    floor_rooms: list[RoomType]
    fight: CombatState | None
    kills: int
    deaths: int
    runs_completed: int
    bonus_bp: int
    tick: int
    log: list[LogEntry] = field(default_factory=list)

    @classmethod
    def load(
        cls, s: RunSession, *, pool: Sequence[EnemyTemplate], policy: SessionExtractPolicy
    ) -> _Runner:
        rng = Rng(s.seed)
        rng.setstate(s.rng_state)
        return cls(
            rng=rng,
            pool=pool,
            extract_policy=policy,
            seed=s.seed,
            strategy_name=s.strategy_name,
            hero=s.hero,
            stress=s.stress,
            resources=s.resources,
            banked=s.banked,
            floor=s.floor,
            room_index=s.room_index,
            floor_rooms=list(s.floor_rooms),
            fight=s.fight,
            kills=s.kills,
            deaths=s.deaths,
            runs_completed=s.runs_completed,
            bonus_bp=s.bonus_bp,
            tick=s.tick,
        )

    def snapshot(self) -> RunSession:
        return RunSession(
            seed=self.seed,
            strategy_name=self.strategy_name,
            hero=self.hero,
            stress=self.stress,
            resources=self.resources,
            banked=self.banked,
            floor=self.floor,
            room_index=self.room_index,
            floor_rooms=tuple(self.floor_rooms),
            fight=self.fight,
            kills=self.kills,
            deaths=self.deaths,
            runs_completed=self.runs_completed,
            bonus_bp=self.bonus_bp,
            tick=self.tick,
            rng_state=self.rng.getstate(),
        )

    def _emit(self, event: Event) -> None:
        self.log.append(LogEntry(self.tick, event))

    def _bank(self) -> None:
        self.banked = self.banked.gain(
            gold=self.resources.gold,
            ore=self.resources.ore,
            materials=self.resources.materials,
            crystals=self.resources.crystals,
        )

    def _fresh_run(self) -> None:
        self.runs_completed += 1
        self.hero = default_hero(self.hero.name)
        self.stress = 0
        self.resources = Resources()
        self.floor = 1
        self.bonus_bp = ONE_X_BP
        self.floor_rooms = [r.type for r in generate_floor(1, self.rng)]
        self.room_index = 0
        self.fight = None
        self._emit(RunStarted(run_number=self.runs_completed + 1, floor=1))

    # ── boundary transitions (free; no tick) ─────────────────────────────────
    def _boundary_step(self) -> None:
        if self.room_index >= len(self.floor_rooms):
            self._emit(FloorCleared(floor=self.floor))
            if self.extract_policy(self.snapshot()):
                self._bank()
                self._emit(Extracted(floor=self.floor))
                self._emit(RunEnded(reason="extracted", floor=self.floor))
                self._fresh_run()
            else:
                bump = (
                    FIRST_CONTINUE_BONUS_BP if self.bonus_bp == ONE_X_BP else NEXT_CONTINUE_BONUS_BP
                )
                self.floor += 1
                self.bonus_bp += bump
                self.floor_rooms = [r.type for r in generate_floor(self.floor, self.rng)]
                self.room_index = 0
            return

        room_type = self.floor_rooms[self.room_index]
        self._emit(RoomEntered(floor=self.floor, index=self.room_index, room_type=room_type.value))
        if room_type is RoomType.REST:
            if self.resources.gold >= REST_COST:
                before, after = self.stress, max(0, self.stress - REST_RELIEF)
                self.stress = after
                self.hero = _heal(self.hero, REST_HEAL)
                self.resources = self.resources.spend_gold(REST_COST)
                self._emit(RestTaken(stress_before=before, stress_after=after, cost=REST_COST))
            self.room_index += 1
        elif room_type is RoomType.CHEST:
            gold = _scaled(15 + self.floor * 5, self.bonus_bp)
            self.resources = self.resources.gain(gold=gold)
            self._emit(Looted(gold=gold))
            self.room_index += 1
        else:  # combat / elite / boss
            enemy: Enemy = _enemy_for(room_type, self.pool, self.rng)
            self.fight = CombatState(hero=self.hero, enemy=enemy, stress=self.stress)
            self._emit(EncounterStarted(name=enemy.name, hp=enemy.hp))

    def ensure_fight(self) -> None:
        guard = 0
        while self.fight is None and guard < 10_000:
            self._boundary_step()
            guard += 1

    # ── combat turns (each costs a tick) ─────────────────────────────────────
    def _breakdown(self) -> None:
        assert self.fight is not None
        lost = self.resources.gold * BREAKDOWN_GOLD_PENALTY_BP // ONE_X_BP
        self.resources = self.resources.spend_gold(lost)
        self.stress = BREAKDOWN_STRESS_AFTER
        self.hero = self.fight.hero
        self._emit(Breakdown(gold_lost=lost))
        self.fight = None
        self.room_index += 1

    def _resolve_end(self) -> None:
        assert self.fight is not None
        won = self.fight.winner == self.fight.hero.name
        if won:
            room_type = self.floor_rooms[self.room_index]
            self.hero = _heal(self.fight.hero, POST_WIN_HEAL)
            self.stress = self.fight.stress
            self.kills += 1
            gold, materials = _rewards(room_type, self.floor, self.bonus_bp)
            self.resources = self.resources.gain(gold=gold, materials=materials)
            self.fight = None
            self.room_index += 1
        else:
            self.deaths += 1
            self.resources = self.resources.on_death()
            self._bank()
            self._emit(RunEnded(reason="died", floor=self.floor))
            self._fresh_run()

    def _apply_combat(self, action: CombatAction) -> None:
        assert self.fight is not None
        self.fight, events = step(self.fight, action, self.rng)
        for event in events:
            self._emit(event)
        self.stress = self.fight.stress
        if self.fight.over:
            self._resolve_end()

    def passive_turn(self, strategy: Strategy) -> None:
        """One autonomous combat turn driven by the strategy."""
        assert self.fight is not None
        if is_breakdown(self.fight.stress):
            self._breakdown()
            self.tick += 1
            return
        decision = decide_turn(strategy, self.fight)
        for event in decision.events:
            self._emit(event)
        if decision.control is Control.FLEE:
            self.hero, self.stress = self.fight.hero, self.fight.stress
            self.fight = None
            self.room_index += 1
        else:
            assert decision.action is not None
            self._apply_combat(decision.action)
        self.tick += 1

    def active_turn(self, action: CombatAction) -> None:
        """One player-chosen combat turn."""
        assert self.fight is not None
        if is_breakdown(self.fight.stress):
            self._breakdown()
        else:
            self._apply_combat(action)
        self.tick += 1


def advance(
    session: RunSession,
    to_tick: int,
    *,
    strategy: Strategy,
    pool: Sequence[EnemyTemplate],
    extract_policy: SessionExtractPolicy | None = None,
) -> tuple[RunSession, list[LogEntry]]:
    """Advance the run autonomously until ``session.tick`` reaches ``to_tick``."""
    if to_tick <= session.tick:
        return session, []
    runner = _Runner.load(session, pool=pool, policy=extract_policy or default_extract_policy)
    while runner.tick < to_tick:
        if runner.fight is None:
            runner.ensure_fight()
        runner.passive_turn(strategy)
    return runner.snapshot(), runner.log


def advance_to_fight(
    session: RunSession,
    *,
    pool: Sequence[EnemyTemplate],
    extract_policy: SessionExtractPolicy | None = None,
) -> tuple[RunSession, list[LogEntry]]:
    """Walk free room/floor transitions until a fight is active (no tick spent).

    Used by active mode to have a foe on screen before the first key.
    """
    if session.fight is not None:
        return session, []
    runner = _Runner.load(session, pool=pool, policy=extract_policy or default_extract_policy)
    runner.ensure_fight()
    return runner.snapshot(), runner.log


def play_turn(
    session: RunSession,
    action: CombatAction,
    *,
    pool: Sequence[EnemyTemplate],
    extract_policy: SessionExtractPolicy | None = None,
) -> tuple[RunSession, list[LogEntry]]:
    """Take a single manual combat turn, first walking to the next fight."""
    runner = _Runner.load(session, pool=pool, policy=extract_policy or default_extract_policy)
    runner.ensure_fight()
    runner.active_turn(action)
    return runner.snapshot(), runner.log
