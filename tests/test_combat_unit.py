"""T1 — unit tests for combat math and resolution (IMPLEMENTATION_PLAN.md)."""

from __future__ import annotations

from dungeon_clash.core import CombatAction, CombatState, Rng, Zone, step
from dungeon_clash.core.combat import resolve_strike
from dungeon_clash.core.events import AttackResolved, AttackResult, CombatDefeated
from dungeon_clash.core.zones import base_damage
from tests.conftest import make_enemy, make_hero


class _AlwaysHit(Rng):
    def chance(self, probability_bp: int) -> bool:
        return True


class _AlwaysMiss(Rng):
    def chance(self, probability_bp: int) -> bool:
        return False


def test_damage_formula_unguarded() -> None:
    # 22 base * 1.50x = 33, unguarded → full damage.
    dmg, result = resolve_strike(
        Zone.HEAD, Zone.TORSO, atk_bp=15_000, block_bp=5_000, rng=_AlwaysHit(0)
    )
    assert result == AttackResult.HIT
    assert dmg == base_damage(Zone.HEAD) * 15_000 // 10_000 == 33


def test_damage_formula_blocked_reduces_by_block_pct() -> None:
    # 14 base * 1.00x = 14, blocked at 65% → max(1, 14 * 0.35) = 4 (integer floor).
    dmg, result = resolve_strike(
        Zone.TORSO, Zone.TORSO, atk_bp=10_000, block_bp=6_500, rng=_AlwaysHit(0)
    )
    assert result == AttackResult.BLOCKED
    assert dmg == max(1, 14 * (10_000 - 6_500) // 10_000) == 4


def test_blocked_damage_floors_at_one() -> None:
    # Tiny hit fully blocked still deals at least 1 (GDD §7.2 max(1, ...)).
    dmg, result = resolve_strike(
        Zone.LEGS, Zone.LEGS, atk_bp=1_000, block_bp=10_000, rng=_AlwaysHit(0)
    )
    assert result == AttackResult.BLOCKED
    assert dmg == 1


def test_miss_deals_no_damage() -> None:
    dmg, result = resolve_strike(
        Zone.HEAD, Zone.LEGS, atk_bp=20_000, block_bp=0, rng=_AlwaysMiss(0)
    )
    assert result == AttackResult.MISS
    assert dmg == 0


def test_step_emits_two_attacks_and_advances_turn() -> None:
    state = CombatState(hero=make_hero(), enemy=make_enemy())
    action = CombatAction(attack=Zone.TORSO, defend=Zone.HEAD)
    new_state, events = step(state, action, Rng(7))

    attacks = [e for e in events if isinstance(e, AttackResolved)]
    assert len(attacks) == 2
    assert attacks[0].attacker == "Hero"
    assert attacks[1].attacker == "Dummy"
    assert new_state.turn == 2


def test_step_does_not_mutate_input_state() -> None:
    state = CombatState(hero=make_hero(hp=100), enemy=make_enemy(hp=80))
    action = CombatAction(attack=Zone.HEAD, defend=Zone.TORSO)
    step(state, action, _AlwaysHit(0))
    # Original is untouched — the core is pure.
    assert state.hero.hp == 100
    assert state.enemy.hp == 80
    assert state.turn == 1


def test_fight_ends_with_defeat_event() -> None:
    # Weak enemy, hero always hits → enemy dies, CombatDefeated emitted.
    state = CombatState(hero=make_hero(atk_bp=30_000), enemy=make_enemy(hp=5, atk_bp=0))
    action = CombatAction(attack=Zone.HEAD, defend=Zone.HEAD)
    new_state, events = step(state, action, _AlwaysHit(0))

    assert new_state.over
    assert new_state.winner == "Hero"
    assert any(isinstance(e, CombatDefeated) for e in events)


def test_stepping_finished_combat_raises() -> None:
    state = CombatState(hero=make_hero(), enemy=make_enemy(), over=True, winner="Hero")
    action = CombatAction(attack=Zone.HEAD, defend=Zone.HEAD)
    try:
        step(state, action, Rng(0))
    except ValueError:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected ValueError when stepping finished combat")
