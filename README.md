# Dungeon Clash

Console-native ASCII dungeon crawler with **strategy-as-code**. See
[`dungeon_clash_GDD.md`](dungeon_clash_GDD.md) for the design, and
[`TECH_STACK.md`](TECH_STACK.md) / [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md)
for the engineering plan.

## Status

**Phase 1** — deterministic combat core (see IMPLEMENTATION_PLAN.md for the roadmap).

The architecture separates a **deterministic, headless simulation core** from all
presentation, persistence, RL, and networking. The core is a pure function of
`(state, action, seeded_rng)`, so every run is bit-for-bit reproducible — the
foundation for combat logs, passive catch-up simulation, RL environments, and
MMO replay anti-cheat. This boundary is enforced in CI by `import-linter`.

```
dungeon_clash/
  core/       # deterministic engine: rng, zones, models, events, combat
  content/    # game data as validated TOML (enemies, …)
  cli/        # entry points (Phase 1: a stdlib smoke demo)
  adapters/   # render / persist / rlenv  (later phases)
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

## Try the deterministic demo

```bash
uv run dungeon           # default seed
uv run dungeon 12345     # explicit seed → identical replay every run
```
