"""Every game the pipeline knows how to build.

Phase 2 adds one module here per game and one line to :func:`register_all`. Registration is
explicit rather than a side effect of importing, so the set of games a build covers is readable
in one place.
"""

from __future__ import annotations

from ..games import GameRegistry
from . import (
    black,
    black2,
    blue,
    crystal,
    diamond,
    emerald,
    firered,
    gold,
    heartgold,
    leafgreen,
    pearl,
    platinum,
    red,
    ruby,
    sapphire,
    silver,
    soulsilver,
    white,
    white2,
    yellow,
)

# In the order they came out: the pair that started it and its own third version, the Johto
# pair and its third version, then the Hoenn pair, the Kanto pair, the third version after
# them, the Sinnoh pair and its third version, the Johto pair that closes Generation 4, the
# pair that opens Generation 5, and the sequels to it - which are a second pair rather than a
# third version, and the only ones in the series.
MODULES = [
    red,
    blue,
    yellow,
    gold,
    silver,
    crystal,
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
    black,
    white,
    black2,
    white2,
]


def register_all(registry: GameRegistry) -> None:
    for module in MODULES:
        module.register(registry)
