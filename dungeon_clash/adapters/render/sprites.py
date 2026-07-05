"""ASCII sprites, looked up by a stable id (enemy template_id or a role).

Assets are keyed by id, not embedded in game logic (TECH_STACK.md §9 rule 2),
so a future graphical client can map the same ids to real art.
"""

from __future__ import annotations

from rich.text import Text

_SPRITES: dict[str, list[str]] = {
    "hero": [
        r"  \O/  ",
        r"   |   ",
        r"  /|\  ",
        r"  / \  ",
    ],
    "goblin_scout": [
        r"  ,-.  ",
        r" (o.o) ",
        r"  )=(  ",
        r" /| |\ ",
    ],
    "skeleton_warrior": [
        r"  (*)  ",
        r"  \|/  ",
        r"   |   ",
        r"  / \  ",
    ],
    "orc_warrior": [
        r" _____ ",
        r"(O   O)",
        r" \___/ ",
        r" |||||  ",
    ],
}

_DEFAULT = [
    r"  ???  ",
    r" (o o) ",
    r"  \_/  ",
    r"  / \  ",
]


def sprite(sprite_id: str) -> Text:
    """Return the sprite for an id (falling back to a generic figure)."""
    lines = _SPRITES.get(sprite_id, _DEFAULT)
    return Text("\n".join(lines))
