"""Pokemon Platinum: entity and edges.

Phase 2 step 1 for this game. Its dex, encounters and gifts are later steps; what is here is
enough for the app to offer it as a main game and to work out what can feed it.
"""

from __future__ import annotations

from ..games import BuildContext, GameRegistry
from ..models import (
    DexSource,
    Game,
    GameData,
    GameRelease,
    NationalDexRangeFilter,
    TransferDirection,
    TransferEdge,
    TransferMechanism,
)

GAME_ID = "platinum"


def build(_: BuildContext) -> GameData:
    return GameData(
        game=Game(
            id=GAME_ID,
            title="Pokémon Platinum Version",
            version="Platinum",
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
    return [
        # Pal Park moves Generation 3 cartridges into a Generation 4 DS game, one way only,
        # and only carries what existed in Generation 3.
        TransferEdge(
            **{"from": "emerald"},
            to=GAME_ID,
            mechanism=TransferMechanism.PAL_PARK,
            direction=TransferDirection.ONE_WAY,
            filter=NationalDexRangeFilter(**{"from": 1}, to=386),
        ),
    ]


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Platinum EN boxart.png")
