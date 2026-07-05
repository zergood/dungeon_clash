"""T10 — the Textual active-mode app, driven by a Pilot."""

from __future__ import annotations

from dungeon_clash.adapters.persist import Store
from dungeon_clash.cli.play import PlayApp
from dungeon_clash.passive import new_session


async def test_two_key_turn_resolves_and_persists() -> None:
    with Store() as store:
        app = PlayApp(store, new_session(4, "cautious"))
        async with app.run_test() as pilot:
            start = app.session.tick
            await pilot.press("t")  # choose attack zone (Torso)
            await pilot.press("h")  # choose defend zone (Head) → resolve turn
            assert app.session.tick == start + 1
            await pilot.press("q")

        row = store.get_session()
        assert row is not None
        assert row["tick"] >= start + 1


async def test_mount_spawns_an_enemy_to_face() -> None:
    with Store() as store:
        app = PlayApp(store, new_session(1, "cautious"))
        async with app.run_test():
            assert app.session.enemy is not None  # a foe is waiting on mount


async def test_q_quits_without_resolving_a_turn() -> None:
    with Store() as store:
        app = PlayApp(store, new_session(2, "cautious"))
        async with app.run_test() as pilot:
            start = app.session.tick
            await pilot.press("q")
        assert app.session.tick == start  # quitting mid-selection resolves nothing


async def test_unrelated_key_is_ignored() -> None:
    with Store() as store:
        app = PlayApp(store, new_session(2, "cautious"))
        async with app.run_test() as pilot:
            start = app.session.tick
            await pilot.press("x")  # not a zone key → no-op
            assert app.session.tick == start
