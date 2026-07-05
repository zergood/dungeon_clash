"""The run engine: traverse floors of rooms, fight, and push your luck."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from dungeon_clash.content.schema import EnemyTemplate
from dungeon_clash.core import Combatant, CombatState, Enemy, Rng, is_breakdown, step
from dungeon_clash.core.events import Event
from dungeon_clash.core.models import ONE_X_BP
from dungeon_clash.core.stress import PANICKING_AT
from dungeon_clash.run.events import (
    Breakdown,
    Extracted,
    FloorCleared,
    Looted,
    RestTaken,
    RoomEntered,
    RunEnded,
)
from dungeon_clash.run.rooms import Room, RoomType, generate_floor
from dungeon_clash.run.state import RunState
from dungeon_clash.strategy import Control, decide_turn
from dungeon_clash.strategy.protocol import Strategy

ExtractPolicy = Callable[[RunState], bool]

REST_COST = 30
REST_RELIEF = 25  # GDD §8.3
REST_HEAL = 50  # rest rooms also recover HP (GDD §6.2)
POST_WIN_HEAL = 22  # a short breather after each victory
BREAKDOWN_GOLD_PENALTY_BP = 3_000  # −30% gold on breakdown (GDD §8.1)
BREAKDOWN_STRESS_AFTER = 50
FIGHT_TURN_CAP = 500
FIRST_CONTINUE_BONUS_BP = 2_500  # first push: +25% (GDD §15.4)
NEXT_CONTINUE_BONUS_BP = 1_500  # each subsequent push: +15%


def _heal(hero: Combatant, amount: int) -> Combatant:
    return hero.model_copy(update={"hp": min(hero.max_hp, hero.hp + amount)})


def default_extract_policy(run: RunState) -> bool:
    """Extract when hurt or badly stressed; otherwise push deeper."""
    return run.hero.hp_pct < 0.4 or run.stress >= PANICKING_AT


def _scaled(base: int, bonus_bp: int) -> int:
    return base * bonus_bp // ONE_X_BP


def _rewards(room_type: RoomType, floor: int, bonus_bp: int) -> tuple[int, int]:
    """(gold, materials) for clearing a combat room, after the push-your-luck bonus."""
    if room_type is RoomType.ELITE:
        gold, materials = 20 + floor * 6, 2
    elif room_type is RoomType.BOSS:
        gold, materials = 40 + floor * 10, 4
    else:
        gold, materials = 8 + floor * 4, 1
    return _scaled(gold, bonus_bp), materials


def _enemy_for(room_type: RoomType, pool: Sequence[EnemyTemplate], rng: Rng) -> Enemy:
    base = rng.choice(pool).spawn(rng)
    if room_type is RoomType.ELITE:
        return base.model_copy(
            update={
                "hp": base.hp * 13 // 10,
                "max_hp": base.max_hp * 13 // 10,
                "atk_bp": base.atk_bp * 105 // 100,
                "stress_attack": base.stress_attack + 2,
            }
        )
    if room_type is RoomType.BOSS:
        return base.model_copy(
            update={
                "name": f"{base.name} (Boss)",
                "hp": base.hp * 14 // 10,
                "max_hp": base.max_hp * 14 // 10,
                "atk_bp": base.atk_bp * 110 // 100,
                "stress_attack": base.stress_attack + 4,
            }
        )
    return base


def _fight(
    hero: Combatant, stress: int, enemy: Enemy, strategy: Strategy, rng: Rng
) -> tuple[Combatant, int, str, list[Event]]:
    """Resolve a full encounter. Outcome: win | lose | flee | breakdown."""
    state = CombatState(hero=hero, enemy=enemy, stress=stress)
    events: list[Event] = []
    outcome = ""
    turns = 0
    while not state.over and turns < FIGHT_TURN_CAP:
        if is_breakdown(state.stress):
            outcome = "breakdown"
            break
        decision = decide_turn(strategy, state)
        events.extend(decision.events)
        if decision.control is Control.FLEE:
            outcome = "flee"
            break
        assert decision.action is not None
        state, evs = step(state, decision.action, rng)
        events.extend(evs)
        turns += 1
    if not outcome:
        outcome = (
            "win"
            if state.over and state.winner == hero.name
            else ("lose" if state.over else "flee")
        )
    return state.hero, state.stress, outcome, events


def _resolve_room(
    run: RunState, room: Room, strategy: Strategy, pool: Sequence[EnemyTemplate], rng: Rng
) -> tuple[RunState, list[Event]]:
    if room.type is RoomType.REST:
        if run.resources.gold < REST_COST:
            return run, []
        before, after = run.stress, max(0, run.stress - REST_RELIEF)
        run = run.model_copy(
            update={
                "stress": after,
                "hero": _heal(run.hero, REST_HEAL),
                "resources": run.resources.spend_gold(REST_COST),
            }
        )
        return run, [RestTaken(stress_before=before, stress_after=after, cost=REST_COST)]

    if room.type is RoomType.CHEST:
        gold = _scaled(15 + run.floor * 5, run.bonus_bp)
        return run.model_copy(update={"resources": run.resources.gain(gold=gold)}), [
            Looted(gold=gold)
        ]

    # COMBAT / ELITE / BOSS
    enemy = _enemy_for(room.type, pool, rng)
    hero, stress, outcome, events = _fight(run.hero, run.stress, enemy, strategy, rng)

    if outcome == "win":
        gold, materials = _rewards(room.type, run.floor, run.bonus_bp)
        run = run.model_copy(
            update={
                "hero": _heal(hero, POST_WIN_HEAL),
                "stress": stress,
                "kills": run.kills + 1,
                "resources": run.resources.gain(gold=gold, materials=materials),
            }
        )
    elif outcome == "lose":
        run = run.model_copy(
            update={
                "hero": hero,
                "stress": stress,
                "deaths": run.deaths + 1,
                "alive": False,
                "resources": run.resources.on_death(),
            }
        )
    elif outcome == "breakdown":
        lost = run.resources.gold * BREAKDOWN_GOLD_PENALTY_BP // ONE_X_BP
        run = run.model_copy(
            update={
                "hero": hero,
                "stress": BREAKDOWN_STRESS_AFTER,
                "resources": run.resources.spend_gold(lost),
            }
        )
        events.append(Breakdown(gold_lost=lost))
    else:  # flee
        run = run.model_copy(update={"hero": hero, "stress": stress})
    return run, events


def advance_run(
    run: RunState,
    strategy: Strategy,
    *,
    pool: Sequence[EnemyTemplate],
    extract_policy: ExtractPolicy | None = None,
    max_floors: int = 10,
) -> tuple[RunState, list[Event]]:
    """Play a run to its end: death, extraction, or the floor cap.

    Deterministic given the run's seed + RNG state. Between floors the strategy's
    ``extract_policy`` chooses to bank the run or push deeper for a bigger bonus.
    """
    policy = extract_policy or default_extract_policy
    rng = Rng(run.seed)
    rng.setstate(run.rng_state)
    events: list[Event] = []

    while run.alive and not run.extracted and run.floor <= max_floors:
        for index, room in enumerate(generate_floor(run.floor, rng)):
            events.append(RoomEntered(floor=run.floor, index=index, room_type=room.type.value))
            run, room_events = _resolve_room(run, room, strategy, pool, rng)
            events.extend(room_events)
            if not run.alive:
                break

        if not run.alive:
            events.append(RunEnded(reason="died", floor=run.floor))
            break

        events.append(FloorCleared(floor=run.floor))
        if policy(run):
            run = run.model_copy(update={"extracted": True})
            events.append(Extracted(floor=run.floor))
            events.append(RunEnded(reason="extracted", floor=run.floor))
            break

        bump = FIRST_CONTINUE_BONUS_BP if run.bonus_bp == ONE_X_BP else NEXT_CONTINUE_BONUS_BP
        run = run.model_copy(update={"floor": run.floor + 1, "bonus_bp": run.bonus_bp + bump})

    return run.model_copy(update={"rng_state": rng.getstate()}), events
