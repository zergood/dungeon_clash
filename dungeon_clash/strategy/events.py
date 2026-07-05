"""Strategy-layer events.

These subclass the core :class:`~dungeon_clash.core.events.Event` so they share
one homogeneous log with combat events — a strategy error and the enemy's hit
that followed it appear in the same stream (GDD §4.2: "Strategy exceptions are
logged with stack traces").
"""

from __future__ import annotations

from typing import Literal

from dungeon_clash.core.events import Event


class StrategyError(Event):
    """The strategy raised an exception; the turn was skipped."""

    kind: Literal["strategy_error"] = "strategy_error"
    turn: int
    exc_type: str
    message: str
    traceback: str


class InvalidAction(Event):
    """The strategy returned something that isn't a valid action; turn skipped."""

    kind: Literal["invalid_action"] = "invalid_action"
    turn: int
    reason: str


class Fled(Event):
    """The strategy chose to leave combat."""

    kind: Literal["fled"] = "fled"
    turn: int
    who: str
