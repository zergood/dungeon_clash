"""T1 — unit tests for core primitives: RNG determinism and zones."""

from __future__ import annotations

import pytest

from dungeon_clash.core import Rng, Zone
from dungeon_clash.core.rng import BASIS_POINTS
from dungeon_clash.core.zones import base_damage, hit_chance_bp


def test_seed_is_exposed() -> None:
    assert Rng(seed=777).seed == 777


def test_chance_boundaries_are_deterministic() -> None:
    rng = Rng(0)
    assert rng.chance(0) is False
    assert rng.chance(-5) is False
    assert rng.chance(BASIS_POINTS) is True
    assert rng.chance(BASIS_POINTS + 1) is True


def test_chance_is_reproducible_for_a_seed() -> None:
    a = [Rng(5).chance(5_000) for _ in range(1)]
    b = [Rng(5).chance(5_000) for _ in range(1)]
    assert a == b


def test_chance_frequency_is_roughly_calibrated() -> None:
    rng = Rng(123)
    hits = sum(rng.chance(3_000) for _ in range(10_000))
    assert 2_600 <= hits <= 3_400  # ~30% within a generous band


def test_choice_picks_from_sequence() -> None:
    rng = Rng(1)
    picks = {rng.choice(["a", "b", "c"]) for _ in range(50)}
    assert picks <= {"a", "b", "c"}


def test_choice_on_empty_sequence_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        Rng(1).choice([])


def test_getstate_setstate_round_trip() -> None:
    rng = Rng(42)
    rng.chance(5_000)  # advance the stream
    snapshot = rng.getstate()
    before = [rng.chance(5_000) for _ in range(20)]
    rng.setstate(snapshot)
    after = [rng.chance(5_000) for _ in range(20)]
    assert before == after


def test_zone_display_and_tables() -> None:
    assert Zone.HEAD.display == "HEAD"
    assert base_damage(Zone.HEAD) == 22
    assert hit_chance_bp(Zone.LEGS) == 9_200
