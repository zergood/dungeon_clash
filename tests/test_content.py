"""T6 — content validation and referential integrity (IMPLEMENTATION_PLAN.md)."""

from __future__ import annotations

from dungeon_clash.content import load_enemies
from dungeon_clash.core import Enemy, Rng


def test_all_enemies_load_and_validate() -> None:
    enemies = load_enemies()
    assert enemies, "no enemies loaded"


def test_enemy_ids_are_unique_and_match_keys() -> None:
    enemies = load_enemies()
    for key, template in enemies.items():
        assert key == template.template_id


def test_enemy_hp_ranges_are_sane() -> None:
    for template in load_enemies().values():
        assert 0 < template.hp_min <= template.hp_max
        assert template.bias  # non-empty pool


def test_spawn_is_deterministic_and_in_range() -> None:
    template = load_enemies()["orc_warrior"]
    a = template.spawn(Rng(99))
    b = template.spawn(Rng(99))
    assert isinstance(a, Enemy)
    assert a == b  # same seed → same roll
    assert template.hp_min <= a.hp <= template.hp_max
    assert a.hp == a.max_hp
