"""The active-mode Textual app (``dungeon play``).

Event-driven: nothing happens until you choose a zone. Each turn you pick an
attack zone then a defend zone (H/T/L); the fight resolves through the exact
same core as passive mode, and every turn is persisted — so quitting hands
control straight back to your strategy at the state you left (GDD §4.2/§4.3).
"""

from __future__ import annotations

import time

from textual import events
from textual.app import App, ComposeResult
from textual.widgets import RichLog, Static

from dungeon_clash import service
from dungeon_clash.active import ensure_enemy, play_turn
from dungeon_clash.adapters.persist import Store
from dungeon_clash.adapters.render import combat_view, render_event
from dungeon_clash.core import CombatAction, Zone
from dungeon_clash.passive import LogEntry, PassiveSession

_KEY_TO_ZONE = {"h": Zone.HEAD, "t": Zone.TORSO, "l": Zone.LEGS}


class PlayApp(App[None]):
    """Interactive control of the current run."""

    CSS = """
    #view { height: auto; padding: 1; }
    #log { height: 1fr; border: round $panel; }
    #prompt { height: auto; padding: 1; }
    """

    def __init__(self, store: Store, session: PassiveSession) -> None:
        super().__init__()
        self._store = store
        self.session = session
        self._pool = service.enemy_pool()
        self._phase = "attack"
        self._pending: Zone | None = None

    def compose(self) -> ComposeResult:
        yield Static(id="view")
        yield RichLog(id="log", wrap=True, markup=False)
        yield Static(id="prompt")

    def on_mount(self) -> None:
        self.session, entries = ensure_enemy(self.session, self._pool)
        service.persist_turn(self._store, self.session, entries, now=time.time())
        self._write(entries)
        self._refresh()

    def on_key(self, event: events.Key) -> None:
        key = event.key.lower()
        if key == "q":
            self.exit()
            return
        zone = _KEY_TO_ZONE.get(key)
        if zone is None:
            return

        if self._phase == "attack":
            self._pending = zone
            self._phase = "defend"
            self._refresh()
            return

        action = CombatAction(attack=self._pending, defend=zone)
        self._pending = None
        self._phase = "attack"

        self.session, entries = play_turn(self.session, action, self._pool)
        self.session, extra = ensure_enemy(self.session, self._pool)  # keep a foe on screen
        entries.extend(extra)
        service.persist_turn(self._store, self.session, entries, now=time.time())
        self._write(entries)
        self._refresh()

    def _write(self, entries: list[LogEntry]) -> None:
        log = self.query_one("#log", RichLog)
        for entry in entries:
            log.write(render_event(entry.event))

    def _refresh(self) -> None:
        self.query_one("#view", Static).update(combat_view(self.session.hero, self.session.enemy))
        if self._phase == "attack":
            prompt = "choose ATTACK zone"
        else:
            chosen = self._pending.display if self._pending else ""
            prompt = f"attack {chosen} — choose DEFEND zone"
        self.query_one("#prompt", Static).update(f"{prompt}    (H / T / L,  Q to quit)")
