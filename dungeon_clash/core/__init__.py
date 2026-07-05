"""Deterministic, headless simulation core.

This package MUST NOT import any presentation, persistence, RL, or web
framework (enforced by import-linter, see pyproject.toml). Everything here is a
pure function of explicit inputs plus a seeded RNG, so any run is bit-for-bit
reproducible from its seed — the foundation for combat logs, passive catch-up
simulation, RL environments, and MMO replay anti-cheat.
"""

from dungeon_clash.core.combat import step
from dungeon_clash.core.events import AttackResolved, CombatDefeated, Event
from dungeon_clash.core.models import CombatAction, Combatant, CombatState, Enemy
from dungeon_clash.core.rng import Rng
from dungeon_clash.core.zones import Zone

__all__ = [
    "AttackResolved",
    "CombatAction",
    "CombatDefeated",
    "CombatState",
    "Combatant",
    "Enemy",
    "Event",
    "Rng",
    "Zone",
    "step",
]
