"""Combat zones: where you attack and where you defend.

Values come straight from GDD §7.1. Hit chances are stored in **basis points**
(integer, 10_000 == 100%) so all combat math stays integer and deterministic.
"""

from __future__ import annotations

from enum import StrEnum
from typing import NamedTuple


class ZoneStats(NamedTuple):
    base_damage: int
    hit_chance_bp: int


class Zone(StrEnum):
    """The three targetable body zones."""

    HEAD = "H"
    TORSO = "T"
    LEGS = "L"

    @property
    def display(self) -> str:
        return self.name


#: GDD §7.1 — HEAD: 22 dmg / 55%, TORSO: 14 / 75%, LEGS: 8 / 92%.
ZONE_STATS: dict[Zone, ZoneStats] = {
    Zone.HEAD: ZoneStats(base_damage=22, hit_chance_bp=5_500),
    Zone.TORSO: ZoneStats(base_damage=14, hit_chance_bp=7_500),
    Zone.LEGS: ZoneStats(base_damage=8, hit_chance_bp=9_200),
}


def base_damage(zone: Zone) -> int:
    return ZONE_STATS[zone].base_damage


def hit_chance_bp(zone: Zone) -> int:
    return ZONE_STATS[zone].hit_chance_bp
