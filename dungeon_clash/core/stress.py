"""Stress: thresholds and their combat effects (GDD §8).

Stress is a transparent 0–100 resource with *threshold* states rather than a
hidden bleeding number — you are Calm, Rattled, Panicking, or Breaking, and each
state has one readable consequence. Kept as pure functions so the effect is
predictable and testable (a top complaint the GDD calls out in §4.1).
"""

from __future__ import annotations

from enum import StrEnum

#: Base threshold breakpoints (GDD §8.1). Helmets shift these in a later phase.
RATTLED_AT = 40
PANICKING_AT = 70
BREAKING_AT = 90
BREAKDOWN_AT = 100
MAX_STRESS = 100

#: Rattled reduces HEAD hit chance by 10 percentage points (1_000 bp).
RATTLED_HEAD_PENALTY_BP = 1_000
#: Killing an enemy outright relieves a little stress (GDD §8.3).
ONE_BLOW_RELIEF = 5


class StressState(StrEnum):
    CALM = "calm"  # 0–39: no penalties
    RATTLED = "rattled"  # 40–69: −10% HEAD hit chance
    PANICKING = "panicking"  # 70–89: defense zone randomly shifts
    BREAKING = "breaking"  # 90–99: strategy ignored, acts randomly


def stress_state(stress: int) -> StressState:
    """Map a stress value to its (ordered) threshold state."""
    if stress >= BREAKING_AT:
        return StressState.BREAKING
    if stress >= PANICKING_AT:
        return StressState.PANICKING
    if stress >= RATTLED_AT:
        return StressState.RATTLED
    return StressState.CALM


def clamp_stress(stress: int) -> int:
    """Keep stress within ``[0, MAX_STRESS]``."""
    return max(0, min(MAX_STRESS, stress))


def is_breakdown(stress: int) -> bool:
    """At the cap the hero breaks down and flees (GDD §8.1) — a run-level effect."""
    return stress >= BREAKDOWN_AT
