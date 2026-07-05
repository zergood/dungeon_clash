"""Run structure — floors, rooms, resources, and push-your-luck (GDD §6–§11, §15).

Pure logic layered on the combat core: a run traverses generated floors of
rooms, fights through the same deterministic ``step``, tracks stress and
resources, and at each floor exit chooses to extract or push deeper. Death
costs a slice of carried resources but never permanent progress (GDD §10.3).

Depends on core/content; independent of storage and presentation (import-linter).
"""

from dungeon_clash.run.engine import advance_run, default_extract_policy
from dungeon_clash.run.resources import Resources
from dungeon_clash.run.rooms import Room, RoomType, generate_floor
from dungeon_clash.run.state import RunState, new_run

__all__ = [
    "Resources",
    "Room",
    "RoomType",
    "RunState",
    "advance_run",
    "default_extract_policy",
    "generate_floor",
    "new_run",
]
