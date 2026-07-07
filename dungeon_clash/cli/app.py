"""The ``dungeon`` command-line interface.

    dungeon start [--seed S] [--strategy NAME]   # begin a fresh run
    dungeon status                               # catch up to now, show state
    dungeon play                                 # take manual control (TUI)
    dungeon log [--last N] [--stats]             # read the run log

Runs traverse floors of rooms, accrue stress and resources, and push their luck
at each floor exit (GDD §6–§15). Passive mode never runs in the background:
``status`` lazily simulates whatever happened since you last looked and appends
it to the log (GDD §4.3); on death or extraction a fresh run starts automatically
and secured resources are banked.
"""

from __future__ import annotations

import json
import time
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from dungeon_clash import service
from dungeon_clash.adapters.persist import Store
from dungeon_clash.adapters.render import render_log_line
from dungeon_clash.core.stress import stress_state
from dungeon_clash.passive import STRATEGIES
from dungeon_clash.run.session import RunSession

cli = typer.Typer(add_completion=False, help="Dungeon Clash — a terminal dungeon crawler.")
console = Console()


def _store() -> Store:
    return Store(service.default_db_path())


def _print_log_row(row: object) -> None:
    detail = render_log_line(row["kind"], json.loads(row["payload"]))  # type: ignore[index]
    console.print(Text.assemble((f"t{row['tick']:>4}  ", "dim"), detail))  # type: ignore[index]


def _render_status(session: RunSession) -> None:
    if session.fight is not None:
        foe = session.fight.enemy
        facing = f"{foe.name} ({foe.hp}/{foe.max_hp} HP)"
        hero = session.fight.hero
    else:
        facing = "— (between rooms)"
        hero = session.hero
    res = session.resources
    body = (
        f"[bold]{hero.name}[/]  {hero.hp}/{hero.max_hp} HP    "
        f"stress {session.stress} ([magenta]{stress_state(session.stress).value}[/])\n"
        f"strategy : {session.strategy_name}\n"
        f"floor    : {session.floor}   room {session.room_index}/{len(session.floor_rooms)}"
        f"   (run #{session.runs_completed + 1}, turn {session.tick})\n"
        f"carried  : {res.gold}g  {res.materials}mat   banked: {session.banked.gold}g "
        f"{session.banked.materials}mat\n"
        f"kills    : {session.kills}    deaths: {session.deaths}\n"
        f"facing   : {facing}"
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
def play() -> None:
    """Take manual control of the current run (interactive TUI)."""
    from dungeon_clash.cli.play import PlayApp  # lazy: only pull in Textual for play

    with _store() as store:
        session = service.catch_up(store, now=time.time())
        if session is None:
            console.print("No run yet. Start one with [bold]dungeon start[/].")
            raise typer.Exit(code=1)
        PlayApp(store, session).run()


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
            session = RunSession.model_validate_json(row["snapshot"])
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
