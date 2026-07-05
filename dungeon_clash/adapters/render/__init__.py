"""Rendering adapter — turns domain state and events into Rich renderables.

This is the single source of truth for "what a hit looks like". The passive CLI
log and the active Textual UI both render through here, so the two modes never
drift. Everything is a pure function of (event | state) → Rich renderable;
events carry semantics, not pre-formatted strings, so a future graphics client
can animate the same stream (TECH_STACK.md §9).
"""

from dungeon_clash.adapters.render.format import (
    combat_view,
    hp_bar,
    render_event,
    render_log_line,
    zone_table,
)
from dungeon_clash.adapters.render.sprites import sprite

__all__ = [
    "combat_view",
    "hp_bar",
    "render_event",
    "render_log_line",
    "sprite",
    "zone_table",
]
