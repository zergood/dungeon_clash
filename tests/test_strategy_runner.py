"""T7 — the runner shields the engine from broken strategies."""

from __future__ import annotations

import signal
import time

import pytest

from dungeon_clash.core import CombatAction, CombatState, Zone
from dungeon_clash.strategy import Control, attack, decide_turn, defend, flee
from dungeon_clash.strategy.events import Fled, InvalidAction, StrategyError
from tests.conftest import make_enemy, make_hero


def _state() -> CombatState:
    return CombatState(hero=make_hero(), enemy=make_enemy(), turn=4)


def test_valid_pair_becomes_action() -> None:
    d = decide_turn(lambda s: (attack("HEAD"), defend("TORSO")), _state())
    assert d.control is Control.ACT
    assert d.action == CombatAction(attack=Zone.HEAD, defend=Zone.TORSO)
    assert d.events == []


def test_intent_order_does_not_matter() -> None:
    d = decide_turn(lambda s: (defend("LEGS"), attack("HEAD")), _state())
    assert d.action == CombatAction(attack=Zone.HEAD, defend=Zone.LEGS)


def test_lone_attack_or_defend_is_allowed() -> None:
    assert decide_turn(lambda s: attack("HEAD"), _state()).action == CombatAction(
        attack=Zone.HEAD, defend=None
    )
    assert decide_turn(lambda s: defend("HEAD"), _state()).action == CombatAction(
        attack=None, defend=Zone.HEAD
    )


def test_flee_produces_flee_control() -> None:
    d = decide_turn(lambda s: flee(), _state())
    assert d.control is Control.FLEE
    assert d.action is None
    assert isinstance(d.events[0], Fled)
    assert d.events[0].turn == 4


def test_exception_is_caught_and_logged_with_traceback() -> None:
    def boom(state: CombatState) -> object:
        return {"gold": 1}["arcane_crystals"]  # KeyError

    d = decide_turn(boom, _state())
    assert d.control is Control.ACT
    assert d.action == CombatAction()  # skipped turn: no strike, no guard
    err = d.events[0]
    assert isinstance(err, StrategyError)
    assert err.exc_type == "KeyError"
    assert err.turn == 4
    assert "KeyError" in err.traceback


@pytest.mark.parametrize(
    "strategy",
    [
        lambda s: 42,  # not an intent
        lambda s: (attack("HEAD"), attack("LEGS")),  # two attacks
        lambda s: (),  # empty
        lambda s: (flee(), attack("HEAD")),  # flee mixed with action
        lambda s: (attack("HEAD"), defend("LEGS"), defend("TORSO")),  # two defends
    ],
)
def test_malformed_returns_are_invalid_actions(strategy: object) -> None:
    d = decide_turn(strategy, _state())  # type: ignore[arg-type]
    assert d.control is Control.ACT
    assert d.action == CombatAction()
    assert isinstance(d.events[0], InvalidAction)
    assert d.events[0].turn == 4


def test_bare_intent_without_action_is_invalid() -> None:
    from dungeon_clash.strategy.intents import Intent

    d = decide_turn(lambda s: Intent(), _state())
    assert isinstance(d.events[0], InvalidAction)
    assert "no actionable intent" in d.events[0].reason


@pytest.mark.skipif(not hasattr(signal, "SIGALRM"), reason="SIGALRM (POSIX) required")
def test_slow_strategy_times_out() -> None:
    def slow(state: CombatState) -> object:
        end = time.time() + 5.0  # bounded so the test cannot hang if the guard fails
        while time.time() < end:
            pass
        return attack("HEAD"), defend("HEAD")

    d = decide_turn(slow, _state(), timeout_s=0.05)
    err = d.events[0]
    assert isinstance(err, StrategyError)
    assert d.action == CombatAction()  # turn skipped
