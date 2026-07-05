"""T2 — property-based invariants (Hypothesis), IMPLEMENTATION_PLAN.md.

These check properties that must hold for *any* inputs: HP stays in bounds,
damage math is consistent, and state serialization round-trips.
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from dungeon_clash.core import CombatAction, Combatant, CombatState, Enemy, Rng, Zone, step
from dungeon_clash.core.combat import resolve_strike
from dungeon_clash.core.events import AttackResult
from dungeon_clash.core.zones import base_damage

zones = st.sampled_from(list(Zone))
atk_bp = st.integers(min_value=0, max_value=30_000)
block_bp = st.integers(min_value=0, max_value=10_000)
hp = st.integers(min_value=1, max_value=500)


class _AlwaysHit(Rng):
    def chance(self, probability_bp: int) -> bool:
        return True


@st.composite
def combatants(draw: st.DrawFn) -> Combatant:
    h = draw(hp)
    return Combatant(name="Hero", hp=h, max_hp=h, atk_bp=draw(atk_bp), block_bp=draw(block_bp))


@st.composite
def enemies(draw: st.DrawFn) -> Enemy:
    h = draw(hp)
    return Enemy(
        name="Foe",
        template_id="foe",
        hp=h,
        max_hp=h,
        atk_bp=draw(atk_bp),
        block_bp=draw(block_bp),
        bias=tuple(draw(st.lists(zones, min_size=1, max_size=4))),
    )


@given(az=zones, dz=zones, a=atk_bp, b=block_bp)
def test_resolve_damage_is_nonnegative(az: Zone, dz: Zone, a: int, b: int) -> None:
    dmg, _ = resolve_strike(az, dz, a, b, _AlwaysHit(0))
    assert dmg >= 0


@given(az=zones, a=st.integers(min_value=10_000, max_value=30_000), b=block_bp)
def test_blocking_never_increases_damage(az: Zone, a: int, b: int) -> None:
    """Guarding the struck zone never deals more than leaving it open."""
    unblocked, _ = resolve_strike(az, _other_zone(az), a, b, _AlwaysHit(0))
    blocked, result = resolve_strike(az, az, a, b, _AlwaysHit(0))
    assert result == AttackResult.BLOCKED
    assert blocked <= unblocked
    assert blocked >= 1  # GDD §7.2 floor


@given(az=zones, a=atk_bp)
def test_unguarded_hit_matches_formula(az: Zone, a: int) -> None:
    dmg, result = resolve_strike(az, _other_zone(az), a, 0, _AlwaysHit(0))
    assert result == AttackResult.HIT
    assert dmg == base_damage(az) * a // 10_000


@given(hero=combatants(), enemy=enemies(), az=zones, dz=zones, seed=st.integers(0, 2**31))
def test_step_keeps_hp_in_bounds(
    hero: Combatant, enemy: Enemy, az: Zone, dz: Zone, seed: int
) -> None:
    state = CombatState(hero=hero, enemy=enemy)
    new_state, _ = step(state, CombatAction(attack=az, defend=dz), Rng(seed))
    for c in (new_state.hero, new_state.enemy):
        assert 0 <= c.hp <= c.max_hp
    assert new_state.turn == state.turn + 1
    if new_state.over:
        assert new_state.winner in {hero.name, enemy.name}


@given(hero=combatants(), enemy=enemies())
def test_state_serialization_round_trips(hero: Combatant, enemy: Enemy) -> None:
    state = CombatState(hero=hero, enemy=enemy, turn=3)
    assert CombatState.model_validate(state.model_dump()) == state


def _other_zone(z: Zone) -> Zone:
    return Zone.HEAD if z is not Zone.HEAD else Zone.TORSO
