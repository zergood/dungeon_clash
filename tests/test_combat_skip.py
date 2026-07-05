"""Core behaviour for optional attack/defend (skipped turns, no-guard)."""

from __future__ import annotations

from dungeon_clash.core import CombatAction, CombatState, Rng, Zone, step
from dungeon_clash.core.combat import resolve_strike
from dungeon_clash.core.events import AttackResolved, AttackResult
from tests.conftest import make_enemy, make_hero


class _AlwaysHit(Rng):
    def chance(self, probability_bp: int) -> bool:
        return True


def test_skipped_turn_deals_no_hero_damage_but_enemy_still_acts() -> None:
    state = CombatState(hero=make_hero(hp=100), enemy=make_enemy(hp=80, atk_bp=10_000))
    new_state, events = step(state, CombatAction(), _AlwaysHit(0))

    attacks = [e for e in events if isinstance(e, AttackResolved)]
    assert len(attacks) == 1  # only the enemy's strike is logged
    assert attacks[0].attacker == "Dummy"
    assert new_state.enemy.hp == 80  # hero never struck
    assert new_state.hero.hp < 100  # enemy did


def test_no_guard_means_hit_is_never_blocked() -> None:
    # defend_zone=None can never equal the attack zone → HIT, not BLOCKED.
    dmg_open, result_open = resolve_strike(Zone.HEAD, None, 10_000, 6_500, _AlwaysHit(0))
    dmg_guarded, result_guarded = resolve_strike(Zone.HEAD, Zone.HEAD, 10_000, 6_500, _AlwaysHit(0))

    assert result_open is AttackResult.HIT
    assert result_guarded is AttackResult.BLOCKED
    assert dmg_open > dmg_guarded
