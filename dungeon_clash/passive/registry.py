"""Named strategies for passive sessions.

A running session stores its strategy by *name* (a function can't be persisted).
Phase 3 resolves names against the built-in reference bots; loading a player's
own strategy from a file arrives in a later phase.
"""

from __future__ import annotations

from dungeon_clash.strategy import aggressive, cautious, flee_when_low
from dungeon_clash.strategy.protocol import Strategy

STRATEGIES: dict[str, Strategy] = {
    "aggressive": aggressive,
    "cautious": cautious,
    "flee_when_low": flee_when_low,
}


def resolve_strategy(name: str) -> Strategy:
    try:
        return STRATEGIES[name]
    except KeyError:
        raise ValueError(
            f"unknown strategy {name!r}; available: {', '.join(sorted(STRATEGIES))}"
        ) from None
