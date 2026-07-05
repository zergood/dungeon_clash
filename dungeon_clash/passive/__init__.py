"""Passive mode — the hero fights autonomously under the player's strategy.

This layer is pure advancement logic: given a session and a target tick count,
:func:`advance` deterministically simulates the intervening turns and returns
the new session plus a log. It performs no I/O and reads no clock — wall-clock
time is translated to a tick target by the application service, so the engine
stays reproducible (same seed + same tick target → same result), which is what
makes "never punish absence" (GDD §4.3) a lazy catch-up rather than a daemon.

May depend on core/content/strategy, but not on persistence or presentation
(enforced by import-linter).
"""

from dungeon_clash.passive.events import EnemyAppeared, HeroDown
from dungeon_clash.passive.registry import STRATEGIES, resolve_strategy
from dungeon_clash.passive.session import LogEntry, PassiveSession, advance, new_session

__all__ = [
    "STRATEGIES",
    "EnemyAppeared",
    "HeroDown",
    "LogEntry",
    "PassiveSession",
    "advance",
    "new_session",
    "resolve_strategy",
]
