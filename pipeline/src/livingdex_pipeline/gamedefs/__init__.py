"""Every game the pipeline knows how to build.

Phase 2 adds one module here per game and one line to :func:`register_all`. Registration is
explicit rather than a side effect of importing, so the set of games a build covers is readable
in one place.
"""

from __future__ import annotations

from ..games import GameRegistry
from . import (
    blue,
    diamond,
    emerald,
    firered,
    heartgold,
    leafgreen,
    pearl,
    platinum,
    red,
    ruby,
    sapphire,
    soulsilver,
    yellow,
)

# In the order they came out: the pair that started it and its own third version, then the
# Hoenn pair, the Kanto pair, the third version that followed them, the Sinnoh pair and its
# third version, and the Johto pair that closes Generation 4.
MODULES = [
    red,
    blue,
    yellow,
    ruby,
    sapphire,
    firered,
    leafgreen,
    emerald,
    diamond,
    pearl,
    platinum,
    heartgold,
    soulsilver,
]


def register_all(registry: GameRegistry) -> None:
    for module in MODULES:
        module.register(registry)
