"""The strategy runner: safely turn a player's strategy into combat actions.

``decide_turn`` calls the strategy inside a guard: any exception, timeout, or
malformed return becomes a logged event and a skipped turn — the engine never
crashes because your code did. ``run_combat`` drives a full fight by feeding the
resulting actions into the deterministic core.
"""

from __future__ import annotations

import signal
import traceback
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import StrEnum

from dungeon_clash.core import CombatAction, CombatState, Rng, step
from dungeon_clash.core.events import Event
from dungeon_clash.strategy.events import Fled, InvalidAction, StrategyError
from dungeon_clash.strategy.intents import AttackIntent, DefendIntent, FleeIntent, Intent
from dungeon_clash.strategy.protocol import Strategy

#: The action used when a turn is skipped: the hero neither strikes nor guards.
_SKIP = CombatAction(attack=None, defend=None)


class Control(StrEnum):
    ACT = "act"  # perform ``action`` via the core
    FLEE = "flee"  # leave combat


@dataclass(frozen=True)
class TurnDecision:
    """The runner's verdict for one turn."""

    control: Control
    action: CombatAction | None
    events: list[Event] = field(default_factory=list)


class _InvalidIntent(Exception):
    """Raised internally when a strategy's return can't be normalized."""


class _Timeout(Exception):
    """Raised when a strategy exceeds its time budget."""


@contextmanager
def _time_limit(seconds: float | None) -> Iterator[None]:
    """Best-effort wall-clock guard (POSIX main thread only).

    A hard, portable timeout is a v2 concern (subprocess/WASM sandbox); this
    soft guard keeps a runaway loop from hanging the in-process v1 engine on the
    platforms that support ``SIGALRM``.
    """
    if seconds is None or not hasattr(signal, "SIGALRM"):
        yield
        return

    def _handler(signum: int, frame: object) -> None:
        raise _Timeout(f"strategy exceeded {seconds:g}s")

    previous = signal.signal(signal.SIGALRM, _handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def _normalize(result: object) -> CombatAction | FleeIntent:
    """Turn a strategy's return value into a concrete action or a flee.

    Accepts a single intent or a tuple/list of intents. Raises
    :class:`_InvalidIntent` with a human-readable reason for anything else.
    """
    intents = list(result) if isinstance(result, (tuple, list)) else [result]

    if not intents:
        raise _InvalidIntent("strategy returned no intents")
    if any(not isinstance(i, Intent) for i in intents):
        raise _InvalidIntent("strategy must return attack()/defend()/flee() intents")

    flees = [i for i in intents if isinstance(i, FleeIntent)]
    attacks = [i for i in intents if isinstance(i, AttackIntent)]
    defends = [i for i in intents if isinstance(i, DefendIntent)]

    if flees:
        if len(intents) != 1:
            raise _InvalidIntent("flee() must be the only intent")
        return flees[0]

    if len(attacks) > 1 or len(defends) > 1:
        raise _InvalidIntent("at most one attack() and one defend() per turn")
    if not attacks and not defends:
        raise _InvalidIntent("no actionable intent")

    return CombatAction(
        attack=attacks[0].zone if attacks else None,
        defend=defends[0].zone if defends else None,
    )


def decide_turn(
    strategy: Strategy, state: CombatState, *, timeout_s: float | None = None
) -> TurnDecision:
    """Ask the strategy what to do this turn, never propagating its failures.

    On exception/timeout → a :class:`StrategyError` event and a skipped turn.
    On a malformed return → an :class:`InvalidAction` event and a skipped turn.
    On ``flee()`` → :class:`Fled` and a FLEE control.
    """
    try:
        with _time_limit(timeout_s):
            result = strategy(state)
    except Exception as exc:
        return TurnDecision(
            control=Control.ACT,
            action=_SKIP,
            events=[
                StrategyError(
                    turn=state.turn,
                    exc_type=type(exc).__name__,
                    message=str(exc),
                    traceback=traceback.format_exc(),
                )
            ],
        )

    try:
        normalized = _normalize(result)
    except _InvalidIntent as inv:
        return TurnDecision(
            control=Control.ACT,
            action=_SKIP,
            events=[InvalidAction(turn=state.turn, reason=str(inv))],
        )

    if isinstance(normalized, FleeIntent):
        return TurnDecision(
            control=Control.FLEE,
            action=None,
            events=[Fled(turn=state.turn, who=state.hero.name)],
        )

    return TurnDecision(control=Control.ACT, action=normalized)


def run_combat(
    strategy: Strategy,
    state: CombatState,
    rng: Rng,
    *,
    timeout_s: float | None = None,
    max_turns: int = 1000,
) -> tuple[CombatState, list[Event]]:
    """Play a full fight with ``strategy`` in control of the hero.

    Returns the final state and the complete event log (strategy-layer events
    interleaved with combat events). ``max_turns`` is a safety backstop against
    non-terminating fights; reaching it stops the loop (the caller can inspect
    ``state.over``).
    """
    log: list[Event] = []
    turns = 0
    while not state.over and turns < max_turns:
        decision = decide_turn(strategy, state, timeout_s=timeout_s)
        log.extend(decision.events)
        if decision.control is Control.FLEE:
            break
        assert decision.action is not None  # ACT always carries an action
        state, events = step(state, decision.action, rng)
        log.extend(events)
        turns += 1
    return state, log
