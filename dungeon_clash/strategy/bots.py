"""Example strategies — reference bots for tests, demos, and dummies.

These are exactly the kind of function a player writes (GDD §5.1): a plain
callable over ``state`` returning intents.
"""

from __future__ import annotations

from dungeon_clash.core import CombatState
from dungeon_clash.strategy.intents import (
    AttackIntent,
    DefendIntent,
    FleeIntent,
    attack,
    defend,
    flee,
)


def aggressive(state: CombatState) -> tuple[AttackIntent, DefendIntent]:
    """All offense: swing for the head, guard the head."""
    return attack("HEAD"), defend("HEAD")


def cautious(state: CombatState) -> tuple[AttackIntent, DefendIntent]:
    """Balanced: torso damage, head guard; go for the head to finish."""
    if state.enemy.hp < 15:
        return attack("HEAD"), defend("TORSO")
    return attack("TORSO"), defend("HEAD")


def flee_when_low(state: CombatState) -> tuple[AttackIntent, DefendIntent] | FleeIntent:
    """Leave the fight before dying (GDD §5.1)."""
    if state.hero.hp_pct < 0.35:
        return flee()
    return attack("TORSO"), defend("HEAD")
