"""Formatters: events and combat state → Rich renderables."""

from __future__ import annotations

from rich.console import Group, RenderableType
from rich.table import Table
from rich.text import Text

from dungeon_clash.adapters.render.sprites import sprite
from dungeon_clash.core.events import Event
from dungeon_clash.core.models import Combatant, Enemy
from dungeon_clash.core.zones import ZONE_STATS, Zone

_RESULT_STYLE = {"hit": "bold", "blocked": "yellow", "miss": "dim"}


def hp_bar(hp: int, max_hp: int, width: int = 20) -> Text:
    """A colored HP bar: green when healthy, yellow, then red when low."""
    hp = max(0, hp)
    ratio = hp / max_hp if max_hp else 0.0
    filled = round(ratio * width)
    color = "green" if ratio > 0.5 else "yellow" if ratio > 0.25 else "red"
    bar = Text()
    bar.append("█" * filled, style=color)
    bar.append("░" * (width - filled), style="grey37")
    bar.append(f" {hp}/{max_hp}")
    return bar


def zone_table() -> Table:
    """The static reference table of zones (GDD §7.1)."""
    table = Table(title=None, show_edge=False, pad_edge=False)
    table.add_column("zone")
    table.add_column("dmg", justify="right")
    table.add_column("hit", justify="right")
    labels = {Zone.HEAD: "[H] Head", Zone.TORSO: "[T] Torso", Zone.LEGS: "[L] Legs"}
    for zone, stats in ZONE_STATS.items():
        table.add_row(labels[zone], str(stats.base_damage), f"{stats.hit_chance_bp // 100}%")
    return table


def _fighter_block(sprite_id: str, name: str, hp: int, max_hp: int) -> Group:
    return Group(sprite(sprite_id), Text(name, style="bold"), hp_bar(hp, max_hp))


def combat_view(hero: Combatant, enemy: Enemy | None) -> RenderableType:
    """The hero-vs-enemy panel: sprites, HP bars, and the zone reference."""
    layout = Table.grid(expand=True, padding=(0, 4))
    layout.add_column()
    layout.add_column()
    hero_block = _fighter_block("hero", hero.name, hero.hp, hero.max_hp)
    if enemy is not None:
        enemy_block: RenderableType = _fighter_block(
            enemy.template_id, enemy.name, enemy.hp, enemy.max_hp
        )
    else:
        enemy_block = Text("(no enemy — between fights)", style="dim")
    layout.add_row(hero_block, enemy_block)
    return Group(layout, Text(), zone_table())


def render_log_line(kind: str, payload: dict[str, object]) -> Text:
    """Format one log entry (from a live event or a stored payload) as Text.

    The single formatter shared by the passive CLI log and the active TUI, so
    the two modes render identically.
    """
    if kind == "attack_resolved":
        result = str(payload["result"])
        guard = payload.get("defend_zone") or "—"
        line = Text.assemble(
            (f"{payload['attacker']}", "bold"),
            f" → {payload['defender']} [{payload['attack_zone']}] ",
            (result, _RESULT_STYLE.get(result, "")),
            f" {payload['damage']} dmg (guard {guard})",
        )
        return line
    if kind == "combat_defeated":
        return Text(
            f"{payload['winner']} defeats {payload['loser']} (turn {payload['turns']})",
            style="bold",
        )
    if kind == "enemy_appeared":
        return Text(f"a {payload['name']} appears ({payload['hp']} HP)", style="cyan")
    if kind == "hero_down":
        return Text(f"the hero falls and recovers (death #{payload['deaths']})", style="red")
    if kind == "stress_changed":
        arrow = "↓" if str(payload["delta"]).startswith("-") else "↑"
        return Text(f"stress {arrow} {payload['stress']} ({payload['state']})", style="magenta")
    if kind == "strategy_error":
        return Text(
            f"STRATEGY ERROR {payload['exc_type']}: {payload['message']} — turn skipped",
            style="bold red",
        )
    if kind == "invalid_action":
        return Text(f"INVALID ACTION: {payload['reason']} — turn skipped", style="red")
    if kind == "fled":
        return Text(f"{payload['who']} flees", style="italic")
    if kind == "run_started":
        return Text(
            f"═══ run #{payload['run_number']} begins (floor {payload['floor']}) ═══", style="bold"
        )
    if kind == "room_entered":
        return Text(f"— floor {payload['floor']}: {payload['room_type']} room", style="dim")
    if kind == "encounter_started":
        return Text(f"a {payload['name']} blocks the way ({payload['hp']} HP)", style="cyan")
    if kind == "rest_taken":
        return Text(
            f"rest: stress {payload['stress_before']}→{payload['stress_after']} "
            f"(−{payload['cost']} gold)",
            style="green",
        )
    if kind == "looted":
        return Text(f"looted {payload['gold']} gold", style="yellow")
    if kind == "floor_cleared":
        return Text(f"floor {payload['floor']} cleared", style="bold cyan")
    if kind == "extracted":
        return Text(
            f"extracted from floor {payload['floor']} — resources banked", style="bold green"
        )
    if kind == "breakdown":
        return Text(f"BREAKDOWN — fled, lost {payload['gold_lost']} gold", style="bold red")
    if kind == "run_ended":
        return Text(f"run ended ({payload['reason']}) on floor {payload['floor']}", style="bold")
    return Text(kind)


def render_event(event: Event) -> Text:
    """Render a live event object (delegates to :func:`render_log_line`)."""
    return render_log_line(event.kind, event.model_dump())
