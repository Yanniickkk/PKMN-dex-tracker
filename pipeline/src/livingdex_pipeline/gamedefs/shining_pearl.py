"""Pokemon Shining Pearl: what it is, and the three routes it brings.

Phase 2 steps 1 to 7 for this game, and nothing after them yet. What it says about itself is
here; what is true of both halves - Sinnoh on a Switch, and the way out - is in :mod:`bdsp`.

The half that reads as the quieter one and is not: Pearl's list against Diamond's is the oldest
kind of difference this dataset holds, and it survived the remake intact. What is left for this
file is its name, that Brilliant Diamond is its other half, and which version PokeAPI is asked
about.
"""

from __future__ import annotations

from ..games import BuildContext, GameRegistry
from ..models import DexEntry, GameData, TransferEdge
from . import bdsp

GAME_ID = "shining-pearl"

#: The other half. Which species that switch decides is step 4's answer; all that is claimed
#: here is that the two halves exist and know about each other.
PAIR_PARTNER = "brilliant-diamond"

#: What PokeAPI calls this game when it lists which version an encounter belongs to.
POKEAPI_VERSION = "shining-pearl"


def build(context: BuildContext) -> GameData:
    """The game entity, the 151 it shows, and every wild slot that fills one."""
    entries = dex_entries(context)

    return GameData(
        game=bdsp.cartridge(
            game_id=GAME_ID,
            title="Pokémon Shining Pearl",
            version="Shining Pearl",
            pair_partner=PAIR_PARTNER,
        ),
        dex_entries=entries,
        acquisition_methods=bdsp.acquisition_methods(
            context, game_id=GAME_ID, entries=entries
        ),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """The Sinnoh dex as this game numbers it: Turtwig #001 to Manaphy #151.

    The same 151 in the same order that Brilliant Diamond shows, which is what a version pair
    has always meant - the halves split what can be *caught*, not what is listed. No
    Five of them this half can never fill, which is what step 7 added: the four the other
    half keeps, and the one nothing in either produces.
    """
    return bdsp.dex_entries(
        context, game_id=GAME_ID, unobtainable=bdsp.unobtainable_in(GAME_ID)
    )


def edges() -> list[TransferEdge]:
    """The cable to Brilliant Diamond, and HOME in both directions."""
    return bdsp.edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Shining Pearl EN boxart.png")
