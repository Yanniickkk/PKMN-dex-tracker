"""Pokemon Moon: what it is, and the routes it brings.

Phase 2 step 1, the other half of :mod:`sun`. Everything the two of them share is in
:mod:`alola`, and what is left here is a name, a partner and a date.

The one thing this half decides on its own that the other cannot is which of a pair of
legendaries the story ends with, and that is step 4's. The clocks are the other: Moon runs
twelve hours out from the 3DS's, so a Sun player and a Moon player standing side by side are in
different halves of the day. Nothing in this step can record that, and by step 3 it decides
which encounters exist.
"""

from __future__ import annotations

from datetime import date

from ..games import BuildContext, GameRegistry
from ..models import AcquisitionMethod, DexEntry, GameData, TransferEdge
from . import alola

GAME_ID = "moon"

#: The other half of the pair.
PAIR_PARTNER = "sun"

#: What PokeAPI calls this game when it lists which version an encounter belongs to.
POKEAPI_VERSION = "moon"

#: The same day as its other half, which is the only kind of release date a pair has ever had.
RELEASED = date(2016, 11, 18)


#: Dex entries no amount of playing this release will fill, and why. Steps 4 to 7 fill it.
UNOBTAINABLE: dict[str, str] = {}


def build(context: BuildContext) -> GameData:
    """The game entity, the list it shows, and every way this game fills it."""
    entries = dex_entries(context)

    return GameData(
        game=alola.cartridge(
            game_id=GAME_ID,
            title="Pokémon Moon",
            version="Moon",
            released=RELEASED,
            national_dex_through=alola.SM_NATIONAL_DEX_THROUGH,
            pair_partner=PAIR_PARTNER,
        ),
        dex_entries=entries,
        acquisition_methods=acquisition_methods(context, entries),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """The Alola dex, the same 302 entries its other half shows: Rowlet to Marshadow.

    Not the list Ultra Sun and Ultra Moon show. Those add a hundred and one and scatter them
    through it, so the two lists disagree about what nearly every number after #023 means - the
    same thing the two Unova dexes do, and what Omega Ruby did to Ruby's with nine entries.

    Not the National Dex either, which these games do not have. The grid is still 802 tiles,
    because that is what the boxes here can hold; this list is what the game itself displays,
    and the grid can be switched to it.
    """
    return alola.dex_entries(
        context, game_id=GAME_ID, dex=alola.SM_DEX, unobtainable=UNOBTAINABLE
    )


def acquisition_methods(
    context: BuildContext,
    entries: list[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something here. Wild slots so far, and most of them are forms."""
    return alola.acquisition_methods(
        context, game_id=GAME_ID, version=POKEAPI_VERSION, entries=entries
    )


def edges() -> list[TransferEdge]:
    return alola.edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Moon EN boxart.png")
