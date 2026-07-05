"""T9 — CLI smoke tests via Typer's runner."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from dungeon_clash.cli.app import cli

runner = CliRunner()


@pytest.fixture(autouse=True)
def _isolated_home(tmp_path: object, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DUNGEON_CLASH_HOME", str(tmp_path))
    monkeypatch.setenv("DUNGEON_CLASH_SECONDS_PER_TICK", "0.001")  # fast catch-up


def test_full_flow() -> None:
    assert runner.invoke(cli, ["start", "--seed", "4", "--strategy", "cautious"]).exit_code == 0
    assert runner.invoke(cli, ["status"]).exit_code == 0
    assert runner.invoke(cli, ["log", "--last", "5"]).exit_code == 0
    assert runner.invoke(cli, ["log", "--stats"]).exit_code == 0


def test_status_before_start_exits_nonzero() -> None:
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 1
    assert "No run yet" in result.stdout


def test_start_with_unknown_strategy_exits_2() -> None:
    result = runner.invoke(cli, ["start", "--strategy", "does_not_exist"])
    assert result.exit_code == 2


def test_stats_render_after_run() -> None:
    runner.invoke(cli, ["start", "--seed", "1"])
    runner.invoke(cli, ["status"])
    result = runner.invoke(cli, ["log", "--stats"])
    assert result.exit_code == 0
    assert "turns simulated" in result.stdout
