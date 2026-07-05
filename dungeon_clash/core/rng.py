"""Deterministic random number generation.

The whole architecture rests on reproducibility: same seed + same actions must
produce a bit-for-bit identical event stream on every platform. We therefore
funnel *all* randomness through this wrapper and expose only integer-based
primitives (``randrange`` under the hood). We never touch floating point here,
so results cannot drift between CPUs, OSes, or Python builds.

``random.Random`` (Mersenne Twister) is a stable, fully specified algorithm, so
a given seed and call sequence yields the same numbers everywhere.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")

#: Probabilities are expressed in basis points: 10_000 bp == 100%.
BASIS_POINTS = 10_000


class Rng:
    """A seeded, serializable source of deterministic randomness."""

    __slots__ = ("_r", "_seed")

    def __init__(self, seed: int) -> None:
        self._seed = seed
        self._r = random.Random(seed)

    @property
    def seed(self) -> int:
        """The seed this generator was created from (for logging/replay)."""
        return self._seed

    def chance(self, probability_bp: int) -> bool:
        """Return ``True`` with the given probability, expressed in basis points.

        ``chance(5500)`` succeeds 55% of the time. Purely integer comparison, so
        the outcome is deterministic across platforms.
        """
        if probability_bp <= 0:
            return False
        if probability_bp >= BASIS_POINTS:
            return True
        return self._r.randrange(BASIS_POINTS) < probability_bp

    def choice(self, options: Sequence[T]) -> T:
        """Pick one element uniformly at random from a non-empty sequence."""
        if not options:
            raise ValueError("cannot choose from an empty sequence")
        return options[self._r.randrange(len(options))]

    def getstate(self) -> tuple[object, ...]:
        """Opaque generator state, for snapshotting a run mid-flight."""
        return self._r.getstate()

    def setstate(self, state: tuple[object, ...]) -> None:
        """Restore generator state produced by :meth:`getstate`."""
        self._r.setstate(state)
