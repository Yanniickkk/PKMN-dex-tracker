"""Every game the pipeline knows how to build.

Phase 2 adds one module here per game and one line to :func:`register_all`. Registration is
explicit rather than a side effect of importing, so the set of games a build covers is readable
in one place.
"""

from __future__ import annotations

from ..games import GameRegistry
from . import (
    alpha_sapphire,
    bank,
    black,
    black2,
    blue,
    crystal,
    diamond,
    emerald,
    firered,
    gold,
    heartgold,
    home,
    leafgreen,
    lets_go_eevee,
    lets_go_pikachu,
    moon,
    omega_ruby,
    pearl,
    platinum,
    red,
    ruby,
    sapphire,
    shield,
    silver,
    soulsilver,
    sun,
    sword,
    ultra_moon,
    ultra_sun,
    white,
    white2,
    x,
    y,
    yellow,
)

# In the order they came out: the pair that started it and its own third version, the Johto
# pair and its third version, then the Hoenn pair, the Kanto pair, the third version after
# them, the Sinnoh pair and its third version, the Johto pair that closes Generation 4, the
# pair that opens Generation 5, the sequels to it - which are a second pair rather than a
# third version, and the only ones in the series - the pair that opens Generation 6, the first
# the whole world got on the same day, and the remakes that close it, which are the Hoenn pair
# again a year later and twelve years on, and the pair that opens Generation 7 - the first
# games since Generation 2 with no National Pokedex - the second pair of that generation, and
# then the two that close it on a different console in a different region: Kanto for the fifth
# time, Yellow remade and a game that never existed remade beside it. Then the pair that opens
# Generation 8 on the same console, which is the first in the series whose boxes hold a list
# rather than everything up to a number.
#
# Then the two nodes, out of that order and at the end, because neither is a game. Bank came out
# between the two Generation 6 pairs and HOME six years after it. They are here for the same
# reason the games are: the registry is what puts a node in the dataset, and fifteen routes had
# been waiting for one or the other.
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
    x,
    y,
    omega_ruby,
    alpha_sapphire,
    sun,
    moon,
    ultra_sun,
    ultra_moon,
    lets_go_pikachu,
    lets_go_eevee,
    sword,
    shield,
    bank,
    home,
]


def register_all(registry: GameRegistry) -> None:
    for module in MODULES:
        module.register(registry)
