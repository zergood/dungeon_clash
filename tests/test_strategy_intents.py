"""Unit tests for strategy intents and action helpers."""

from __future__ import annotations

import pytest

from dungeon_clash.core import Zone
from dungeon_clash.strategy import AttackIntent, DefendIntent, FleeIntent, attack, defend, flee
from dungeon_clash.strategy.intents import to_zone


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("HEAD", Zone.HEAD),
        ("head", Zone.HEAD),
        ("  Torso ", Zone.TORSO),
        ("L", Zone.LEGS),
        (Zone.HEAD, Zone.HEAD),
    ],
)
def test_to_zone_accepts_names_letters_and_enum(value: str | Zone, expected: Zone) -> None:
    assert to_zone(value) == expected


def test_to_zone_rejects_unknown() -> None:
    with pytest.raises(ValueError, match="unknown zone"):
        to_zone("HAED")


def test_helpers_build_intents() -> None:
    assert attack("HEAD") == AttackIntent(Zone.HEAD)
    assert defend("legs") == DefendIntent(Zone.LEGS)
    assert isinstance(flee(), FleeIntent)


def test_reference_bots_return_valid_intents() -> None:
    from dungeon_clash.core import CombatState
    from dungeon_clash.strategy import aggressive
    from tests.conftest import make_enemy, make_hero

    state = CombatState(hero=make_hero(), enemy=make_enemy())
    assert aggressive(state) == (AttackIntent(Zone.HEAD), DefendIntent(Zone.HEAD))
