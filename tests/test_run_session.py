"""T2/T8 — the resumable RunSession that the CLI runs on."""

from __future__ import annotations

from dungeon_clash import service
from dungeon_clash.adapters.persist import Store
from dungeon_clash.content.schema import EnemyTemplate
from dungeon_clash.core import CombatAction, Combatant, Zone
from dungeon_clash.run.session import (
    RunSession,
    advance,
    advance_to_fight,
    new_run_session,
    play_turn,
)
from dungeon_clash.service import enemy_pool
from dungeon_clash.strategy import cautious, flee_when_low

POOL = enemy_pool()


def _advance(session: RunSession, to: int) -> tuple[RunSession, list[object]]:
    return advance(session, to, strategy=cautious, pool=POOL)


def test_lazy_catch_up_equals_stepwise() -> None:
    start = new_run_session(7, "cautious")
    one_shot, log_one = _advance(start, 30)

    stepwise = start
    log_step: list[object] = []
    for _ in range(30):
        stepwise, entries = _advance(stepwise, stepwise.tick + 1)
        log_step.extend(entries)

    assert one_shot == stepwise
    assert log_one == log_step


def test_advance_is_deterministic_per_seed() -> None:
    def play(seed: int) -> list[dict[str, object]]:
        _, log = _advance(new_run_session(seed, "cautious"), 40)
        return [e.event.model_dump() for e in log]  # type: ignore[attr-defined]

    assert play(11) == play(11)
    assert play(1) != play(2)


def test_session_round_trips_and_resumes_identically() -> None:
    advanced, _ = _advance(new_run_session(3, "cautious"), 15)
    restored = RunSession.model_validate_json(advanced.model_dump_json())
    assert restored == advanced

    a, _ = _advance(advanced, 30)
    b, _ = _advance(restored, 30)
    assert a == b


def test_advance_to_fight_puts_a_foe_on_screen() -> None:
    s0 = new_run_session(5, "cautious")
    assert s0.fight is None
    s1, entries = advance_to_fight(s0, pool=POOL)
    assert s1.fight is not None
    assert entries  # at least an encounter_started

    s2, again = advance_to_fight(s1, pool=POOL)
    assert s2 is s1 and again == []  # already fighting


def test_runs_bank_resources_and_restart() -> None:
    # Cautious dies often; over many ticks several runs complete and bank loot.
    final, _ = _advance(new_run_session(1, "cautious"), 300)
    assert final.runs_completed >= 1
    assert final.banked.gold > 0


def test_advance_to_lower_tick_is_a_noop() -> None:
    s = new_run_session(1, "cautious")
    same, log = _advance(s, 0)
    assert same is s
    assert log == []


def test_passive_breakdown_is_logged() -> None:
    terror = EnemyTemplate(
        template_id="banshee",
        name="Banshee",
        hp_min=3_000,
        hp_max=3_000,
        atk_bp=300,
        block_bp=0,
        bias=(Zone.HEAD,),
        stress_attack=40,
    )
    _, log = advance(new_run_session(1, "cautious"), 20, strategy=cautious, pool=[terror])
    assert any(e.event.kind == "breakdown" for e in log)


def test_passive_flee_is_logged() -> None:
    weak = Combatant(name="Aeldric", hp=20, max_hp=110, atk_bp=12_500, block_bp=6_500)
    session = new_run_session(1, "flee_when_low", hero=weak)
    _, log = advance(session, 5, strategy=flee_when_low, pool=POOL)
    assert any(e.event.kind == "fled" for e in log)


def test_active_turn_can_break_down() -> None:
    session, _ = advance_to_fight(new_run_session(1, "cautious"), pool=POOL)
    assert session.fight is not None
    breaking = session.model_copy(
        update={"fight": session.fight.model_copy(update={"stress": 100})}
    )
    _, log = play_turn(breaking, CombatAction(attack=Zone.HEAD, defend=Zone.HEAD), pool=POOL)
    assert any(e.event.kind == "breakdown" for e in log)


def test_mode_switch_round_trip_preserves_progress() -> None:
    with Store() as store:
        service.start_session(store, seed=3, strategy_name="cautious", now=0.0)

        passive = service.catch_up(store, now=10.0, secs_per_tick=2.0)  # +5 ticks
        assert passive is not None
        assert passive.tick == 5

        # Active: two manual turns, each persisted (wall-clock frozen).
        row = store.get_session()
        assert row is not None
        session = RunSession.model_validate_json(row["snapshot"])
        for _ in range(2):
            session, entries = play_turn(
                session, CombatAction(attack=Zone.HEAD, defend=Zone.HEAD), pool=POOL
            )
            service.persist_turn(store, session, entries, now=100.0)
        assert session.tick == 7

        resumed = service.catch_up(store, now=110.0, secs_per_tick=2.0)  # +5 ticks
        assert resumed is not None
        assert resumed.tick == 12
        assert resumed.seed == 3
