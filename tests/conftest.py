"""Shared fixtures and factories for the test suite."""

from __future__ import annotations

import pytest

from dungeon_clash.core import Combatant, Enemy, Rng
from dungeon_clash.core.zones import Zone


@pytest.fixture
def rng() -> Rng:
    """A fresh, fixed-seed RNG so every test is reproducible."""
    return Rng(seed=1234)


def make_hero(hp: int = 100, atk_bp: int = 11_000, block_bp: int = 6_500) -> Combatant:
    return Combatant(name="Hero", hp=hp, max_hp=hp, atk_bp=atk_bp, block_bp=block_bp)


def make_enemy(
    hp: int = 80,
    atk_bp: int = 10_000,
    block_bp: int = 5_000,
    bias: tuple[Zone, ...] = (Zone.HEAD, Zone.TORSO, Zone.LEGS),
) -> Enemy:
    return Enemy(
        name="Dummy",
        template_id="dummy",
        hp=hp,
        max_hp=hp,
        atk_bp=atk_bp,
        block_bp=block_bp,
        bias=bias,
    )
