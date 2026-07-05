"""The ``dungeon`` command-line interface (Phase 3).

    dungeon start [--seed S] [--strategy NAME]   # begin a passive run
    dungeon status                               # catch up to now, show state
    dungeon log [--last N] [--stats]             # read the combat log

Passive mode never runs in the background: ``status`` lazily simulates whatever
happened since you last looked and appends it to the log (GDD §4.3).
"""

from __future__ import annotations

import json
import time
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from dungeon_clash import service
from dungeon_clash.adapters.persist import Store
from dungeon_clash.passive import STRATEGIES, PassiveSession

cli = typer.Typer(add_completion=False, help="Dungeon Clash — a terminal dungeon crawler.")
console = Console()


def _store() -> Store:
    return Store(service.default_db_path())


def _format_event(kind: str, payload: dict[str, object]) -> str:
    if kind == "attack_resolved":
        guard = payload.get("defend_zone") or "—"
        return (
            f"{payload['attacker']} → {payload['defender']} "
            f"[{payload['attack_zone']}] {payload['result']} "
            f"{payload['damage']} dmg (guard {guard})"
        )
    if kind == "combat_defeated":
        return f"{payload['winner']} defeats {payload['loser']} (turn {payload['turns']})"
    if kind == "enemy_appeared":
        return f"a {payload['name']} appears ({payload['hp']} HP)"
    if kind == "hero_down":
        return f"the hero falls and recovers (death #{payload['deaths']})"
    if kind == "strategy_error":
        return f"STRATEGY ERROR {payload['exc_type']}: {payload['message']} — turn skipped"
    if kind == "invalid_action":
        return f"INVALID ACTION: {payload['reason']} — turn skipped"
    if kind == "fled":
        return f"{payload['who']} flees"
    return kind


def _print_log_row(row: object) -> None:
    detail = _format_event(row["kind"], json.loads(row["payload"]))  # type: ignore[index]
    console.print(f"[dim]t{row['tick']:>4}[/]  {detail}")  # type: ignore[index]


def _render_status(session: PassiveSession) -> None:
    enemy = (
        f"{session.enemy.name} ({session.enemy.hp}/{session.enemy.max_hp} HP)"
        if session.enemy is not None
        else "— (between fights)"
    )
    body = (
        f"[bold]{session.hero.name}[/]  {session.hero.hp}/{session.hero.max_hp} HP\n"
        f"strategy : {session.strategy_name}\n"
        f"turn     : {session.tick}\n"
        f"kills    : {session.kills}    deaths: {session.deaths}\n"
        f"facing   : {enemy}"
    )
    console.print(Panel(body, title="Dungeon Clash — status", expand=False))


@cli.command()
def start(
    seed: Annotated[int, typer.Option(help="RNG seed for a reproducible run.")] = 1,
    strategy: Annotated[
        str, typer.Option(help=f"One of: {', '.join(sorted(STRATEGIES))}.")
    ] = "cautious",
) -> None:
    """Begin a fresh passive run (replaces any existing one)."""
    with _store() as store:
        try:
            session = service.start_session(
                store, seed=seed, strategy_name=strategy, now=time.time()
            )
        except ValueError as exc:
            console.print(f"[red]{exc}[/]")
            raise typer.Exit(code=2) from None
    console.print(f"[green]Started[/] a run: seed={seed}, strategy={strategy}.")
    _render_status(session)


@cli.command()
def status() -> None:
    """Catch up to the present and show the hero's state."""
    with _store() as store:
        session = service.catch_up(store, now=time.time())
        if session is None:
            console.print("No run yet. Start one with [bold]dungeon start[/].")
            raise typer.Exit(code=1)
        last = store.read_log(last=6)
        _render_status(session)
        if last:
            console.print("\n[dim]recent:[/]")
            for row in last:
                _print_log_row(row)


@cli.command()
def log(
    last: Annotated[int | None, typer.Option(help="Show only the last N entries.")] = None,
    stats: Annotated[bool, typer.Option(help="Show aggregate statistics instead.")] = False,
) -> None:
    """Read the combat log, or aggregate statistics with --stats."""
    with _store() as store:
        row = store.get_session()
        if row is None:
            console.print("No run yet. Start one with [bold]dungeon start[/].")
            raise typer.Exit(code=1)

        if stats:
            session = PassiveSession.model_validate_json(row["snapshot"])
            s = store.stats(session.hero.name)
            table = Table(title="Statistics", show_header=False)
            table.add_row("turns simulated", str(s["turns"]))
            table.add_row("enemies seen", str(s["enemies_seen"]))
            table.add_row("kills", str(s["kills"]))
            table.add_row("deaths", str(s["deaths"]))
            table.add_row("damage dealt", str(s["damage_dealt"]))
            table.add_row("damage taken", str(s["damage_taken"]))
            console.print(table)
            return

        rows = store.read_log(last=last)
        if not rows:
            console.print("[dim]log is empty — run [bold]dungeon status[/] to advance time[/]")
            return
        for r in rows:
            _print_log_row(r)


def app() -> None:
    """Entry point registered as the ``dungeon`` script."""
    cli()


if __name__ == "__main__":
    app()
