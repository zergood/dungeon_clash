"""Active mode — the player takes manual control of the current run.

Pure turn logic shared with passive mode via the same session model and
bookkeeping. The TUI adapter renders this; mode-switching is just: advance the
same :class:`~dungeon_clash.passive.PassiveSession`, persist, and let the
strategy resume from the exact state you left (GDD §4.3).

Depends on core/content/passive; independent of storage and presentation
(enforced by import-linter).
"""

from dungeon_clash.active.session import ensure_enemy, play_turn

__all__ = ["ensure_enemy", "play_turn"]
