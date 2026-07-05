"""Load and validate content files into typed models."""

from __future__ import annotations

import tomllib
from importlib.resources import files

from dungeon_clash.content.schema import EnemyTemplate


def _load_toml(name: str) -> dict[str, object]:
    resource = files("dungeon_clash.content.data").joinpath(name)
    with resource.open("rb") as fh:
        return tomllib.load(fh)


def load_enemies() -> dict[str, EnemyTemplate]:
    """Return all enemy templates, keyed by ``template_id``.

    Raises if any entry is malformed or if two entries share an id — referential
    integrity is a load-time guarantee (see the content tests).
    """
    raw = _load_toml("enemies.toml")
    entries = raw.get("enemy", [])
    if not isinstance(entries, list):
        raise ValueError("enemies.toml: 'enemy' must be an array of tables")

    result: dict[str, EnemyTemplate] = {}
    for entry in entries:
        template = EnemyTemplate.model_validate(entry)
        if template.template_id in result:
            raise ValueError(f"duplicate enemy template_id: {template.template_id}")
        result[template.template_id] = template
    return result
