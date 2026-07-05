"""Player-facing action helpers and the intent objects they produce.

A strategy returns *intents* — declarative "I want to attack HEAD and guard
TORSO" — not a raw :class:`~dungeon_clash.core.CombatAction`. The runner
normalizes intents into a concrete action. Helpers accept either the full zone
name (``"HEAD"``) or its letter (``"H"``), case-insensitively, matching how the
GDD shows strategies (``attack("HEAD"), defend("TORSO")``). A bad zone raises
``ValueError`` right inside the player's strategy, where the traceback is most
useful.
"""

from __future__ import annotations

from dataclasses import dataclass

from dungeon_clash.core import Zone

_NAME_TO_ZONE = {z.name: z for z in Zone} | {z.value: z for z in Zone}


def to_zone(value: str | Zone) -> Zone:
    """Normalize a zone name/letter/enum into a :class:`Zone`."""
    if isinstance(value, Zone):
        return value
    key = value.strip().upper()
    try:
        return _NAME_TO_ZONE[key]
    except KeyError:
        raise ValueError(
            f"unknown zone {value!r}; expected one of HEAD/TORSO/LEGS (or H/T/L)"
        ) from None


@dataclass(frozen=True, slots=True)
class Intent:
    """Base class for strategy intents."""


@dataclass(frozen=True, slots=True)
class AttackIntent(Intent):
    zone: Zone


@dataclass(frozen=True, slots=True)
class DefendIntent(Intent):
    zone: Zone


@dataclass(frozen=True, slots=True)
class FleeIntent(Intent):
    """Leave combat entirely (keeps resources — GDD §5.3)."""


def attack(zone: str | Zone) -> AttackIntent:
    """Intend to strike the given zone."""
    return AttackIntent(to_zone(zone))


def defend(zone: str | Zone) -> DefendIntent:
    """Intend to guard the given zone."""
    return DefendIntent(to_zone(zone))


def flee() -> FleeIntent:
    """Intend to leave combat."""
    return FleeIntent()
