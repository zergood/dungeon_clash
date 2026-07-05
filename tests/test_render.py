"""T3 — the render adapter: event/state → Rich renderables."""

from __future__ import annotations

from rich.console import Console, RenderableType

from dungeon_clash.adapters.render import combat_view, hp_bar, render_event, render_log_line
from dungeon_clash.core.events import AttackResolved, AttackResult
from dungeon_clash.core.zones import Zone
from tests.conftest import make_enemy, make_hero


def _text(renderable: RenderableType, *, color: bool = False) -> str:
    console = Console(force_terminal=color, no_color=not color, width=80)
    with console.capture() as cap:
        console.print(renderable)
    return cap.get()


def test_attack_line_shows_actors_zone_and_damage() -> None:
    out = _text(
        render_log_line(
            "attack_resolved",
            {
                "attacker": "Aeldric",
                "defender": "Orc",
                "attack_zone": "H",
                "defend_zone": "T",
                "result": "hit",
                "damage": 24,
                "defender_hp": 90,
            },
        )
    )
    assert "Aeldric" in out
    assert "Orc" in out
    assert "24 dmg" in out
    assert "hit" in out


def test_each_kind_renders_distinctly() -> None:
    assert "defeats" in _text(
        render_log_line("combat_defeated", {"winner": "Aeldric", "loser": "Orc", "turns": 3})
    )
    assert "appears" in _text(render_log_line("enemy_appeared", {"name": "Orc", "hp": 50}))
    assert "STRATEGY ERROR" in _text(
        render_log_line("strategy_error", {"exc_type": "KeyError", "message": "'x'"})
    )
    assert "flees" in _text(render_log_line("fled", {"who": "Aeldric"}))
    assert "recovers" in _text(render_log_line("hero_down", {"deaths": 2}))
    assert "INVALID ACTION" in _text(render_log_line("invalid_action", {"reason": "two attacks"}))
    assert _text(render_log_line("mystery_kind", {})).strip() == "mystery_kind"


def test_render_event_delegates_to_log_line() -> None:
    ev = AttackResolved(
        attacker="Aeldric",
        defender="Orc",
        attack_zone=Zone.HEAD,
        defend_zone=None,
        result=AttackResult.HIT,
        damage=22,
        defender_hp=10,
    )
    assert "Aeldric" in _text(render_event(ev))


def test_hp_bar_reflects_health() -> None:
    assert "100/100" in _text(hp_bar(100, 100))
    assert "0/100" in _text(hp_bar(0, 100))


def test_combat_view_shows_fighters_and_zone_table() -> None:
    out = _text(combat_view(make_hero(), make_enemy()))
    assert "Hero" in out
    assert "Dummy" in out
    assert "Head" in out and "Torso" in out and "Legs" in out


def test_combat_view_without_enemy() -> None:
    out = _text(combat_view(make_hero(), None))
    assert "Hero" in out
    assert "no enemy" in out


def test_no_color_output_has_no_ansi_but_colored_does() -> None:
    payload = {
        "attacker": "A",
        "defender": "B",
        "attack_zone": "H",
        "defend_zone": "T",
        "result": "hit",
        "damage": 5,
        "defender_hp": 1,
    }
    plain = _text(render_log_line("attack_resolved", payload), color=False)
    colored = _text(render_log_line("attack_resolved", payload), color=True)
    assert "\x1b[" not in plain
    assert "\x1b[" in colored
