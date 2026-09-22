"""Pokemon Platinum: entity and edges.

Phase 2 step 1 for this game. Its dex, encounters and gifts are later steps; what is here is
enough for the app to offer it as a main game and to work out what can feed it.
"""

from __future__ import annotations

from datetime import date

from ..games import BuildContext, GameRegistry
from ..models import (
    DexSource,
    Game,
    GameData,
    GameRelease,
    TransferEdge,
)
from . import gba

GAME_ID = "platinum"


def build(_: BuildContext) -> GameData:
    return GameData(
        game=Game(
            id=GAME_ID,
            title="Pokémon Platinum Version",
            version="Platinum",
            released=date(2008, 9, 13),
            generation=4,
            region="Sinnoh",
            release=GameRelease.CARTRIDGE,
            national_dex_through=493,
            dex_source=DexSource.NATIONAL_DEX,
            # The third version of Diamond and Pearl rather than half of a pair.
            pair_partner=None,
        )
    )


def edges() -> list[TransferEdge]:
    # Pal Park moves a Generation 3 cartridge into a Generation 4 DS game, one way only, and
    # only carries what existed in Generation 3. Every cartridge, not only Emerald: the machine
    # asks for a Game Pak in the slot and does not care which one. This listed Emerald alone
    # from Phase 1, when Emerald was the only Generation 3 game there was, and Ruby and Sapphire
    # arrived later without it being widened - so both of them reached Platinum the long way
    # round, by trading into Emerald first.
    return gba.pal_park_edges(into=GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Platinum EN boxart.png")
