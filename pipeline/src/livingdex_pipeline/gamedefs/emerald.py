"""Pokemon Emerald: entity and edges.

Emerald has no outgoing edge of its own here: Pal Park belongs to the Generation 4 game that
receives, and that is where it is declared.
"""

from __future__ import annotations

from ..games import BuildContext, GameRegistry
from ..models import DexSource, Game, GameData, GameRelease, TransferEdge

GAME_ID = "emerald"


def build(_: BuildContext) -> GameData:
    return GameData(
        game=Game(
            id=GAME_ID,
            title="Pokémon Emerald Version",
            version="Emerald",
            generation=3,
            region="Hoenn",
            release=GameRelease.CARTRIDGE,
            national_dex_through=386,
            dex_source=DexSource.NATIONAL_DEX,
            # The third version of Ruby and Sapphire rather than half of a pair.
            pair_partner=None,
        )
    )


def edges() -> list[TransferEdge]:
    return []


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Emerald EN boxart.jpg")
