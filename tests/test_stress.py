"""T1/T2 — the stress system: thresholds and combat effects (GDD §8)."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from dungeon_clash.core import CombatAction, CombatState, Enemy, Rng, Zone, step
from dungeon_clash.core.combat import _stressed_action
from dungeon_clash.core.events import StressChanged
from dungeon_clash.core.stress import (
    BREAKDOWN_AT,
    StressState,
    clamp_stress,
    is_breakdown,
    stress_state,
)
from tests.conftest import make_hero

_ORDER = [StressState.CALM, StressState.RATTLED, StressState.PANICKING, StressState.BREAKING]


class _RecordHit(Rng):
    """Always-hit RNG that records the hit probabilities it was asked about."""

    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed)
        self.probs: list[int] = []

    def chance(self, probability_bp: int) -> bool:
        self.probs.append(probability_bp)
        return True


def _enemy(stress_attack: int = 0, bias: tuple[Zone, ...] = (Zone.HEAD,)) -> Enemy:
    return Enemy(
        name="Foe",
        template_id="foe",
        hp=200,
        max_hp=200,
        atk_bp=10_000,
        block_bp=0,
        bias=bias,
        stress_attack=stress_attack,
    )


def test_threshold_states() -> None:
    assert stress_state(0) is StressState.CALM
    assert stress_state(39) is StressState.CALM
    assert stress_state(40) is StressState.RATTLED
    assert stress_state(69) is StressState.RATTLED
    assert stress_state(70) is StressState.PANICKING
    assert stress_state(89) is StressState.PANICKING
    assert stress_state(90) is StressState.BREAKING
    assert stress_state(100) is StressState.BREAKING
    assert is_breakdown(BREAKDOWN_AT)
    assert not is_breakdown(BREAKDOWN_AT - 1)


def test_clamp() -> None:
    assert clamp_stress(-10) == 0
    assert clamp_stress(150) == 100
    assert clamp_stress(55) == 55


@given(a=st.integers(0, 200), b=st.integers(0, 200))
def test_state_is_monotonic_in_stress(a: int, b: int) -> None:
    if a <= b:
        assert _ORDER.index(stress_state(min(a, 100))) <= _ORDER.index(stress_state(min(b, 100)))


def test_rattled_reduces_head_hit_chance() -> None:
    hero, enemy = make_hero(), _enemy()
    action = CombatAction(attack=Zone.HEAD, defend=Zone.TORSO)

    calm = _RecordHit(1)
    step(CombatState(hero=hero, enemy=enemy, stress=0), action, calm)
    rattled = _RecordHit(1)
    step(CombatState(hero=hero, enemy=enemy, stress=50), action, rattled)

    assert calm.probs[0] == 5_500  # HEAD base
    assert rattled.probs[0] == 4_500  # −10 percentage points


def test_terrifying_enemy_raises_stress_and_emits_event() -> None:
    hero = make_hero()
    enemy = _enemy(stress_attack=12)
    # Hero guards LEGS while the enemy strikes HEAD → it lands and inflicts stress.
    action = CombatAction(attack=Zone.TORSO, defend=Zone.LEGS)
    new_state, events = step(CombatState(hero=hero, enemy=enemy, stress=0), action, _RecordHit(3))

    assert new_state.stress == 12
    changed = [e for e in events if isinstance(e, StressChanged)]
    assert changed and changed[0].delta == 12
    assert changed[0].state == "calm"


def test_one_blow_kill_relieves_stress() -> None:
    hero = make_hero(atk_bp=40_000)
    enemy = Enemy(
        name="Weak",
        template_id="weak",
        hp=5,
        max_hp=5,
        atk_bp=0,
        block_bp=0,
        bias=(Zone.HEAD,),
    )
    action = CombatAction(attack=Zone.HEAD, defend=Zone.HEAD)
    new_state, _ = step(CombatState(hero=hero, enemy=enemy, stress=20), action, _RecordHit(1))
    assert new_state.stress == 15  # killed from full HP → −5


def test_stressed_action_effects() -> None:
    action = CombatAction(attack=Zone.HEAD, defend=Zone.HEAD)
    # Calm/Rattled leave the action untouched.
    assert _stressed_action(action, StressState.CALM, Rng(1)) == action
    assert _stressed_action(action, StressState.RATTLED, Rng(1)) == action
    # Panicking keeps the attack but randomizes the guard.
    panicked = _stressed_action(action, StressState.PANICKING, Rng(1))
    assert panicked.attack is Zone.HEAD
    assert _stressed_action(action, StressState.PANICKING, Rng(1)) == panicked  # deterministic
    # Breaking ignores the chosen action entirely.
    broken = _stressed_action(action, StressState.BREAKING, Rng(2))
    assert broken.attack is not None and broken.defend is not None
    assert _stressed_action(action, StressState.BREAKING, Rng(2)) == broken
