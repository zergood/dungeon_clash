"""Passive-mode events, layered onto the shared core event stream."""

from __future__ import annotations

from typing import Literal

from dungeon_clash.core.events import Event


class EnemyAppeared(Event):
    """A fresh enemy was drawn from the floor pool."""

    kind: Literal["enemy_appeared"] = "enemy_appeared"
    name: str
    hp: int


class HeroDown(Event):
    """The hero was defeated in passive mode and recovered to fight on.

    Death penalties (GDD §10.3) arrive with the full run structure (Phase 5); in
    Phase 3 the hero simply recovers so the passive loop keeps going.
    """

    kind: Literal["hero_down"] = "hero_down"
    deaths: int
