"""Run-level events, layered onto the shared core event stream."""

from __future__ import annotations

from typing import Literal

from dungeon_clash.core.events import Event


class RunStarted(Event):
    kind: Literal["run_started"] = "run_started"
    run_number: int
    floor: int


class RoomEntered(Event):
    kind: Literal["room_entered"] = "room_entered"
    floor: int
    index: int
    room_type: str


class EncounterStarted(Event):
    kind: Literal["encounter_started"] = "encounter_started"
    name: str
    hp: int


class RestTaken(Event):
    kind: Literal["rest_taken"] = "rest_taken"
    stress_before: int
    stress_after: int
    cost: int


class Looted(Event):
    kind: Literal["looted"] = "looted"
    gold: int


class FloorCleared(Event):
    kind: Literal["floor_cleared"] = "floor_cleared"
    floor: int


class Extracted(Event):
    kind: Literal["extracted"] = "extracted"
    floor: int


class Breakdown(Event):
    """Stress hit the cap: the hero flees the room and loses gold (GDD §8.1)."""

    kind: Literal["breakdown"] = "breakdown"
    gold_lost: int


class RunEnded(Event):
    kind: Literal["run_ended"] = "run_ended"
    reason: str  # "extracted" | "died"
    floor: int
