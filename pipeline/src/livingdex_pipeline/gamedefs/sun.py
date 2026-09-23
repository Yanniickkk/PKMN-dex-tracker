"""Pokemon Sun: what it is, and the routes it brings.

Phase 2 step 1 for this game, and nothing after it yet. What it says about itself is here; what
is true of Alola - which is also what is true of the four Generation 7 cartridges, for the
reason that module gives - is in :mod:`alola`.

The first game in this dataset with no Pokedex of its own worth the name: no National Dex, only
Alola's 302, and the list a player used to read in the game now lives in Pokemon Bank. The
entity still says 802, because what a living dex here asks for is everything the boxes can hold
and not everything the dex app will list.

What it is left to say for itself is its name, that Moon is its other half, which version
PokeAPI is asked about, and the day it came out - which was one day for nearly everybody, five
days before Europe.
"""

from __future__ import annotations

from datetime import date

from ..games import BuildContext, GameRegistry
from ..models import AcquisitionMethod, DexEntry, GameData, TransferEdge
from . import alola

GAME_ID = "sun"

#: The other half of the pair. Which species that switch decides is step 4's answer; all that is
#: claimed here is that the two halves exist and know about each other.
PAIR_PARTNER = "moon"

#: What PokeAPI calls this game when it lists which version an encounter belongs to.
POKEAPI_VERSION = "sun"

#: Japan, North America and most of the world on one day; Europe on the twenty-third. The
#: Japanese date this dataset keeps is the date almost everybody saw, as it was for X and Y.
RELEASED = date(2016, 11, 18)


#: Dex entries no amount of playing this release will fill, and why. Steps 4 to 7 fill it.
UNOBTAINABLE: dict[str, str] = {}


def build(context: BuildContext) -> GameData:
    """The game entity, the list it shows, and every way this game fills it."""
    entries = dex_entries(context)

    return GameData(
        game=alola.cartridge(
            game_id=GAME_ID,
            title="Pokémon Sun",
            version="Sun",
            released=RELEASED,
            national_dex_through=alola.SM_NATIONAL_DEX_THROUGH,
            pair_partner=PAIR_PARTNER,
        ),
        dex_entries=entries,
        acquisition_methods=acquisition_methods(context, entries),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """The Alola dex as Sun and Moon show it: 302 entries, Rowlet to Marshadow.

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
    registry.register(GAME_ID, build, edges(), box_art="Sun EN boxart.png")
