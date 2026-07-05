"""T8 — integration: a strategy plays a full fight through the core."""

from __future__ import annotations

from dungeon_clash.content import load_enemies
from dungeon_clash.core import Combatant, CombatState, Rng
from dungeon_clash.core.events import AttackResolved, CombatDefeated
from dungeon_clash.strategy import cautious, flee_when_low, run_combat
from dungeon_clash.strategy.events import Fled, StrategyError


def _fresh_fight(seed: int) -> tuple[CombatState, Rng]:
    rng = Rng(seed)
    hero = Combatant(name="Hero", hp=100, max_hp=100, atk_bp=11_000, block_bp=6_500)
    enemy = load_enemies()["skeleton_warrior"].spawn(rng)
    return CombatState(hero=hero, enemy=enemy), rng


def test_bot_fights_to_a_conclusion() -> None:
    state, rng = _fresh_fight(3)
    final, log = run_combat(cautious, state, rng)
    assert final.over
    assert final.winner in {"Hero", state.enemy.name}
    assert any(isinstance(e, CombatDefeated) for e in log)
    assert any(isinstance(e, AttackResolved) for e in log)


def test_run_combat_is_deterministic() -> None:
    def play() -> list[dict[str, object]]:
        state, rng = _fresh_fight(2024)
        _, log = run_combat(cautious, state, rng)
        return [e.model_dump() for e in log]

    assert play() == play()


def test_broken_strategy_never_crashes_and_still_resolves() -> None:
    def broken(state: CombatState) -> object:
        raise RuntimeError("oops")

    state, rng = _fresh_fight(1)
    final, log = run_combat(broken, state, rng)
    # Hero skips every turn but the enemy keeps swinging → hero loses, no crash.
    assert final.over
    assert final.winner == state.enemy.name
    assert any(isinstance(e, StrategyError) for e in log)


def test_flee_ends_combat_without_a_defeat() -> None:
    # Weak hero vs strong enemy → drops below 35% and flees.
    rng = Rng(5)
    hero = Combatant(name="Hero", hp=40, max_hp=40, atk_bp=10_000, block_bp=3_000)
    enemy = load_enemies()["orc_warrior"].spawn(rng)
    state = CombatState(hero=hero, enemy=enemy)

    final, log = run_combat(flee_when_low, state, rng)
    assert any(isinstance(e, Fled) for e in log)
    assert not final.over  # fled, nobody was defeated
    assert not any(isinstance(e, CombatDefeated) for e in log)
