"""Carried resources and the asymmetric death penalty (GDD §10)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Resources(BaseModel):
    """Temporary resources carried within a run (never permanent progress)."""

    model_config = ConfigDict(frozen=True)

    gold: int = Field(default=0, ge=0)
    ore: int = Field(default=0, ge=0)
    materials: int = Field(default=0, ge=0)
    crystals: int = Field(default=0, ge=0)

    def gain(
        self, *, gold: int = 0, ore: int = 0, materials: int = 0, crystals: int = 0
    ) -> Resources:
        return self.model_copy(
            update={
                "gold": self.gold + gold,
                "ore": self.ore + ore,
                "materials": self.materials + materials,
                "crystals": self.crystals + crystals,
            }
        )

    def spend_gold(self, amount: int) -> Resources:
        return self.model_copy(update={"gold": max(0, self.gold - amount)})

    def on_death(self) -> Resources:
        """Lose gold −50%, everything else −25% (GDD §10.3). Meta is untouched."""
        return Resources(
            gold=self.gold // 2,
            ore=self.ore * 3 // 4,
            materials=self.materials * 3 // 4,
            crystals=self.crystals * 3 // 4,
        )
