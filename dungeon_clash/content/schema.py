"""Pydantic schemas for game content.

Validation happens at load time, so malformed content fails fast (and, later,
fails a contributor's PR in CI — GDD v4).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from dungeon_clash.core.models import Enemy
from dungeon_clash.core.rng import Rng
from dungeon_clash.core.zones import Zone


class EnemyTemplate(BaseModel):
    """A data-defined enemy. HP is a range (GDD §12.2); the concrete value is
    rolled deterministically at spawn time."""

    model_config = ConfigDict(frozen=True)

    template_id: str
    name: str
    hp_min: int = Field(gt=0)
    hp_max: int = Field(gt=0)
    #: Attack multiplier in basis points (10_500 == 1.05x).
    atk_bp: int = Field(ge=0)
    #: Block fraction in basis points (5_500 == 55%).
    block_bp: int = Field(ge=0, le=10_000)
    bias: tuple[Zone, ...] = Field(min_length=1)

    def model_post_init(self, _context: object) -> None:
        if self.hp_max < self.hp_min:
            raise ValueError(f"{self.template_id}: hp_max ({self.hp_max}) < hp_min ({self.hp_min})")

    def spawn(self, rng: Rng) -> Enemy:
        """Roll a concrete :class:`Enemy` from this template.

        HP is drawn deterministically from ``[hp_min, hp_max]`` via the passed
        RNG, so spawning is part of the reproducible run.
        """
        span = self.hp_max - self.hp_min + 1
        hp = self.hp_min + rng.choice(range(span))
        return Enemy(
            name=self.name,
            template_id=self.template_id,
            hp=hp,
            max_hp=hp,
            atk_bp=self.atk_bp,
            block_bp=self.block_bp,
            bias=self.bias,
        )
