"""T1/T8/T12 — run structure: floors, rooms, resources, push-your-luck."""

from __future__ import annotations

from dungeon_clash.content.schema import EnemyTemplate
from dungeon_clash.core import Combatant, Enemy, Rng, Zone
from dungeon_clash.run import (
    Resources,
    Room,
    RoomType,
    advance_run,
    generate_floor,
    new_run,
)
from dungeon_clash.run.engine import _fight, _resolve_room
from dungeon_clash.service import enemy_pool
from dungeon_clash.strategy import cautious, flee_when_low

POOL = enemy_pool()


def _strong_hero() -> Combatant:
    return Combatant(name="Hero", hp=500, max_hp=500, atk_bp=30_000, block_bp=8_000)


# ── resources / floor generation (T1) ──────────────────────────────────────────
def test_death_penalty_is_asymmetric() -> None:
    r = Resources(gold=100, ore=8, materials=8, crystals=8)
    d = r.on_death()
    assert d.gold == 50  # −50%
    assert (d.ore, d.materials, d.crystals) == (6, 6, 6)  # −25%


def test_floor_generation_is_deterministic_with_boss_last() -> None:
    floor = generate_floor(1, Rng(1))
    assert len(floor) == 4
    assert floor[-1].type is RoomType.BOSS
    assert generate_floor(1, Rng(1)) == generate_floor(1, Rng(1))


def test_rest_room_heals_and_relieves_stress() -> None:
    hurt = Combatant(name="Hero", hp=50, max_hp=110, atk_bp=12_500, block_bp=6_500)
    run = new_run(1, hero=hurt).model_copy(update={"stress": 50, "resources": Resources(gold=100)})
    after, events = _resolve_room(run, Room(type=RoomType.REST), cautious, POOL, Rng(1))
    assert after.stress == 25  # −25
    assert after.hero.hp > run.hero.hp  # healed
    assert after.resources.gold == 70  # −30 gold
    assert any(e.kind == "rest_taken" for e in events)


# ── run flow (T8) ──────────────────────────────────────────────────────────────
def test_run_is_deterministic() -> None:
    def play(seed: int) -> list[dict[str, object]]:
        _, log = advance_run(new_run(seed), cautious, pool=POOL)
        return [e.model_dump() for e in log]

    assert play(1) == play(1)
    assert play(1) != play(2)


def test_extract_policy_banks_the_run() -> None:
    run, log = advance_run(
        new_run(1, hero=_strong_hero()), cautious, pool=POOL, extract_policy=lambda r: True
    )
    assert run.extracted
    assert run.floor == 1  # banked after clearing the first floor
    assert run.resources.gold > 0
    assert any(e.kind == "extracted" for e in log)
    assert any(e.kind == "run_ended" and e.reason == "extracted" for e in log)


def test_continue_pushes_deeper_and_grows_the_bonus() -> None:
    run, log = advance_run(
        new_run(1, hero=_strong_hero()),
        cautious,
        pool=POOL,
        extract_policy=lambda r: False,
        max_floors=3,
    )
    assert run.floor >= 2
    assert run.bonus_bp > 10_000  # push-your-luck bonus accrued
    assert any(e.kind == "floor_cleared" for e in log)


def test_breakdown_flees_and_costs_gold() -> None:
    class _AlwaysHit(Rng):
        def chance(self, probability_bp: int) -> bool:
            return True

    hero = Combatant(name="Hero", hp=500, max_hp=500, atk_bp=1_000, block_bp=0)
    terror = Enemy(
        name="Banshee",
        template_id="banshee",
        hp=2_000,
        max_hp=2_000,
        atk_bp=500,
        block_bp=0,
        bias=(Zone.HEAD,),
        stress_attack=50,
    )
    _, stress, outcome, _ = _fight(hero, 0, terror, cautious, _AlwaysHit(0))
    assert outcome == "breakdown"
    assert stress >= 100


def test_fleeing_combat_keeps_resources_and_survives() -> None:
    hurt = Combatant(name="Hero", hp=20, max_hp=110, atk_bp=12_500, block_bp=6_500)
    run = new_run(1, hero=hurt)
    after, _ = _resolve_room(run, Room(type=RoomType.COMBAT), flee_when_low, POOL, Rng(1))
    assert after.alive
    assert after.kills == run.kills  # no kill credited
    assert after.resources == run.resources  # no reward on a flee


def test_resolve_room_handles_breakdown() -> None:
    class _AlwaysHit(Rng):
        def chance(self, probability_bp: int) -> bool:
            return True

    terror = EnemyTemplate(
        template_id="banshee",
        name="Banshee",
        hp_min=2_000,
        hp_max=2_000,
        atk_bp=500,
        block_bp=0,
        bias=(Zone.HEAD,),
        stress_attack=50,
    )
    tank = Combatant(name="Hero", hp=500, max_hp=500, atk_bp=1_000, block_bp=0)
    run = new_run(1, hero=tank).model_copy(update={"resources": Resources(gold=100)})
    after, events = _resolve_room(
        run, Room(type=RoomType.COMBAT), cautious, [terror], _AlwaysHit(0)
    )

    assert any(e.kind == "breakdown" for e in events)
    assert after.stress == 50  # recovered to below the cap after fleeing
    assert after.resources.gold == 70  # lost 30% gold


def test_fight_reports_flee_outcome() -> None:
    hurt = Combatant(name="Hero", hp=20, max_hp=110, atk_bp=12_500, block_bp=6_500)
    enemy = Enemy(
        name="Foe",
        template_id="foe",
        hp=80,
        max_hp=80,
        atk_bp=10_000,
        block_bp=5_000,
        bias=(Zone.HEAD,),
    )
    _, _, outcome, _ = _fight(hurt, 0, enemy, flee_when_low, Rng(1))
    assert outcome == "flee"


# ── balance simulation (T12, soft) ──────────────────────────────────────────────
def test_runs_always_terminate_and_both_outcomes_occur() -> None:
    reasons: set[str] = set()
    for seed in range(60):
        run, log = advance_run(new_run(seed), cautious, pool=POOL)
        ended = [e for e in log if e.kind == "run_ended"]
        assert ended or run.floor > 10  # every run terminates
        if ended:
            reasons.add(ended[0].reason)
    # A punishing-but-fair game: some runs die, some bank out.
    assert "died" in reasons
    assert "extracted" in reasons
