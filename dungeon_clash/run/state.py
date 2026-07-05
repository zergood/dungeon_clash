"""The persistent state of a single dungeon run."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from dungeon_clash.core import Combatant, Rng
from dungeon_clash.core.models import ONE_X_BP
from dungeon_clash.core.rng import RngState
from dungeon_clash.run.resources import Resources


class RunState(BaseModel):
    """Everything needed to resume a run bit-for-bit."""

    model_config = ConfigDict(frozen=True)

    seed: int
    hero: Combatant
    stress: int = 0
    resources: Resources = Field(default_factory=Resources)
    floor: int = 1
    kills: int = 0
    deaths: int = 0
    alive: bool = True
    extracted: bool = False
    #: Push-your-luck multiplier on resource gains (10_000 == 1.00x). GDD §15.4.
    bonus_bp: int = ONE_X_BP
    rng_state: RngState


def default_hero(name: str = "Aeldric") -> Combatant:
    return Combatant(name=name, hp=110, max_hp=110, atk_bp=12_500, block_bp=6_500)


def new_run(seed: int, *, hero: Combatant | None = None) -> RunState:
    return RunState(
        seed=seed,
        hero=hero if hero is not None else default_hero(),
        rng_state=Rng(seed).getstate(),
    )
