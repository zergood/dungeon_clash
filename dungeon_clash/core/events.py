"""Combat events — the structured record the core emits instead of printing.

The core never renders. It returns typed events, and every consumer (terminal
renderer, passive log, RL reward function, MMO replay) derives what it needs
from the same stream. Events carry semantics (zone, damage, result), not
pre-formatted strings, so a graphical client can animate them later (§9) and a
reward function can score them (§10).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict

from dungeon_clash.core.zones import Zone


class AttackResult(StrEnum):
    HIT = "hit"  # landed on an unguarded zone — full damage
    BLOCKED = "blocked"  # landed on the guarded zone — reduced damage
    MISS = "miss"  # failed the zone's hit-chance roll


class Event(BaseModel):
    """Base class for all combat events."""

    model_config = ConfigDict(frozen=True)
    kind: str


class AttackResolved(Event):
    """One combatant's strike against the other."""

    kind: Literal["attack_resolved"] = "attack_resolved"
    attacker: str
    defender: str
    attack_zone: Zone
    #: The zone the defender guarded, or ``None`` if they guarded nothing.
    defend_zone: Zone | None
    result: AttackResult
    damage: int
    defender_hp: int


class CombatDefeated(Event):
    """A combatant reached 0 HP; the fight is over."""

    kind: Literal["combat_defeated"] = "combat_defeated"
    loser: str
    winner: str
    turns: int


class StressChanged(Event):
    """The hero's stress moved, possibly crossing a threshold (GDD §8)."""

    kind: Literal["stress_changed"] = "stress_changed"
    stress: int
    delta: int
    state: str
