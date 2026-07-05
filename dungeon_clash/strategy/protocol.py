"""The strategy interface.

Kept deliberately tiny and duck-typed: a strategy is anything callable that
takes the current state and returns intents. The same shape will later accept an
RL policy (``policy(obs) -> action`` wrapped to this signature), so "strategy as
code" and "strategy as policy" plug into one slot (TECH_STACK.md §10).
"""

from __future__ import annotations

from collections.abc import Callable

from dungeon_clash.core import CombatState

#: What a strategy may return each turn: a single intent (e.g. ``flee()``) or a
#: pair ``(attack(...), defend(...))``. Validated by the runner.
StrategyReturn = object

#: A strategy is any callable ``decide(state) -> StrategyReturn``.
Strategy = Callable[[CombatState], StrategyReturn]
