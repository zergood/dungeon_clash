"""Room types and deterministic floor generation (GDD §6.2).

Phase 5 uses a linear sequence of rooms per floor (a boss caps each floor).
Full branching maps with ``map_choice`` navigation come in a later slice.
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from dungeon_clash.core import Rng


class RoomType(StrEnum):
    COMBAT = "combat"
    ELITE = "elite"
    REST = "rest"
    CHEST = "chest"
    BOSS = "boss"


class Room(BaseModel):
    model_config = ConfigDict(frozen=True)
    type: RoomType


ROOMS_PER_FLOOR = 4

#: Weighted pool for the non-boss rooms of a floor.
_BODY_POOL: Sequence[RoomType] = (
    RoomType.COMBAT,
    RoomType.COMBAT,
    RoomType.ELITE,
    RoomType.REST,
    RoomType.CHEST,
)


def generate_floor(floor_num: int, rng: Rng) -> list[Room]:
    """A deterministic floor: a handful of rooms, then a boss."""
    body = [Room(type=rng.choice(_BODY_POOL)) for _ in range(ROOMS_PER_FLOOR - 1)]
    body.append(Room(type=RoomType.BOSS))
    return body
