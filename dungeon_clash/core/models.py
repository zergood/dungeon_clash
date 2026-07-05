"""Immutable state models for combat.

All models are frozen: ``step`` never mutates its input, it returns a fresh
state. That keeps the core pure and makes snapshotting (persistence, RL,
mode-switching) a matter of copying a value.

Scalar multipliers are stored in **basis points** (integers, 10_000 == 1.00x)
to keep every derived quantity bit-for-bit reproducible across platforms.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from dungeon_clash.core.zones import Zone

#: 10_000 basis points == 1.00x (or 100%).
ONE_X_BP = 10_000


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class Combatant(_Frozen):
    """A fighter — the hero or an enemy."""

    name: str
    hp: int = Field(ge=0)
    max_hp: int = Field(gt=0)
    #: Attack multiplier in basis points (11_000 == 1.10x). GDD §7.2.
    atk_bp: int = Field(ge=0)
    #: Fraction blocked when guarding the correct zone (6_500 == 65%). GDD §7.2.
    block_bp: int = Field(ge=0, le=ONE_X_BP)

    @property
    def hp_pct(self) -> float:
        """HP as 0.0–1.0. Presentation/strategy convenience only — never used in
        combat math (which stays integer)."""
        return self.hp / self.max_hp

    @property
    def alive(self) -> bool:
        return self.hp > 0

    def with_damage(self, amount: int) -> Combatant:
        """Return a copy with ``amount`` HP removed (clamped at 0)."""
        return self.model_copy(update={"hp": max(0, self.hp - amount)})


class Enemy(Combatant):
    """A combatant with a zone-attack bias (GDD §7.3).

    ``bias`` is the weighted pool the enemy draws its attack zone from; the same
    pool doubles as the source for its (imperfect) defense zone. Patterns are
    intentionally learnable and exploitable.
    """

    template_id: str
    bias: tuple[Zone, ...] = Field(min_length=1)


class CombatAction(_Frozen):
    """One combat turn's decision: where to strike, where to guard."""

    attack: Zone
    defend: Zone


class CombatState(_Frozen):
    """The complete state of a single combat encounter."""

    hero: Combatant
    enemy: Enemy
    turn: int = 1
    over: bool = False
    #: ``"hero"`` or ``"enemy"`` once ``over`` is True, else ``None``.
    winner: str | None = None
