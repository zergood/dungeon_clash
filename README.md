# Dungeon Clash

Console-native ASCII dungeon crawler with **strategy-as-code**. See
[`dungeon_clash_GDD.md`](dungeon_clash_GDD.md) for the design, and
[`TECH_STACK.md`](TECH_STACK.md) / [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md)
for the engineering plan.

## Status

**Phase 3** — persistence + passive mode + CLI (see IMPLEMENTATION_PLAN.md for the roadmap).
Done so far: deterministic combat core (1), strategy-as-code + sandbox (2),
SQLite persistence, lazy passive catch-up, and the `dungeon` CLI (3).

The architecture separates a **deterministic, headless simulation core** from all
presentation, persistence, RL, and networking. The core is a pure function of
`(state, action, seeded_rng)`, so every run is bit-for-bit reproducible — the
foundation for combat logs, passive catch-up simulation, RL environments, and
MMO replay anti-cheat. This boundary is enforced in CI by `import-linter`.

```
dungeon_clash/
  core/       # deterministic engine: rng, zones, models, events, combat
  content/    # game data as validated TOML (enemies, …)
  strategy/   # strategy-as-code: intents, runner, sandbox, reference bots
  passive/    # autonomous lazy-catch-up simulation (no daemon)
  adapters/   # persist (SQLite); render / rlenv come in later phases
  service.py  # application service wiring passive ↔ storage ↔ clock
  cli/        # the `dungeon` CLI (Typer + Rich)
```

## Develop

```bash
uv venv
uv pip install -e '.[dev,cli]'

uv run ruff check .
uv run mypy
uv run lint-imports          # architectural boundary contracts
uv run pytest                # unit + property + determinism + content tests
```

## Try it

```bash
uv run dungeon start --seed 5 --strategy cautious   # begin a passive run
# ...come back later...
uv run dungeon status                               # lazily catches up to now
uv run dungeon log --last 10                         # recent combat log
uv run dungeon log --stats                           # aggregate statistics
```

Passive mode never runs in the background: `status` deterministically simulates
whatever happened since you last looked and appends it to the log. Nothing is
lost if you never check in (GDD §4.3). The save file lives under
`$DUNGEON_CLASH_HOME` (defaults to an XDG data dir).
