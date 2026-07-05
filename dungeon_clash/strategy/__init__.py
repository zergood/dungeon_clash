"""Strategy layer — "strategy as code".

A strategy is a plain callable ``decide(state) -> intents`` the player writes.
It sits *above* the deterministic core: it chooses what to do, the core resolves
what happens. Player-facing helpers (:func:`attack`, :func:`defend`,
:func:`flee`) build lightweight intent objects; the runner validates them,
turns them into a :class:`~dungeon_clash.core.CombatAction`, and — crucially —
never lets a broken strategy crash the engine. Exceptions and invalid returns
are caught, logged as events (with a traceback), and the turn is skipped.
This is by design: debugging your strategy is part of the game (GDD §4.2).

This package may depend on ``core`` but not on any presentation or persistence
layer (enforced by import-linter).
"""

from dungeon_clash.strategy.bots import aggressive, cautious, flee_when_low
from dungeon_clash.strategy.events import Fled, InvalidAction, StrategyError
from dungeon_clash.strategy.intents import (
    AttackIntent,
    DefendIntent,
    FleeIntent,
    Intent,
    attack,
    defend,
    flee,
)
from dungeon_clash.strategy.protocol import Strategy
from dungeon_clash.strategy.runner import Control, TurnDecision, decide_turn, run_combat

__all__ = [
    "AttackIntent",
    "Control",
    "DefendIntent",
    "Fled",
    "FleeIntent",
    "Intent",
    "InvalidAction",
    "Strategy",
    "StrategyError",
    "TurnDecision",
    "aggressive",
    "attack",
    "cautious",
    "decide_turn",
    "defend",
    "flee",
    "flee_when_low",
    "run_combat",
]
