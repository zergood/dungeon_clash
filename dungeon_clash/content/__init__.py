"""Content layer: game data as validated files, not hardcoded Python.

Enemies, relics, weapons, events live as data (TOML) validated by Pydantic
schemas. This keeps balancing in data and makes community-contributed content
(GDD v4) a matter of shipping a validated file, not code.

Like ``core``, this package must not depend on any presentation framework
(enforced by import-linter).
"""

from dungeon_clash.content.loader import load_enemies
from dungeon_clash.content.schema import EnemyTemplate

__all__ = ["EnemyTemplate", "load_enemies"]
