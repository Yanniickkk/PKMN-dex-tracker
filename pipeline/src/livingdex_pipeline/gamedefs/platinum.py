"""Pokemon Platinum: entity and edges.

Phase 2 step 1 for this game. Its dex, encounters and gifts are later steps; what is here is
enough for the app to offer it as a main game and to work out what can feed it.

It reads from :mod:`sinnoh` now, the way Emerald reads from :mod:`hoenn`: a third version is
still one of the region's cartridges, and writing its region and its reach out by hand was how
its Pal Park edges got left behind when Ruby and Sapphire arrived.
"""

from __future__ import annotations

from datetime import date

from ..games import BuildContext, GameRegistry
from ..models import GameData, TransferEdge
from . import sinnoh

GAME_ID = "platinum"


def build(_: BuildContext) -> GameData:
    return GameData(
        game=sinnoh.cartridge(
            game_id=GAME_ID,
            title="Pokémon Platinum Version",
            version="Platinum",
            released=date(2008, 9, 13),
            # The third version of Diamond and Pearl rather than half of a pair.
            pair_partner=None,
        )
    )


def edges() -> list[TransferEdge]:
    return sinnoh.edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Platinum EN boxart.png")
