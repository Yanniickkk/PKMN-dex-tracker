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


#: In the Alola dex and never in this cartridge, and what step 7 found about each.
#:
#: Seven, and two fossils below them, mirroring the other half exactly - and worked out the same
#: way: after the evolutions and eggs of step 5, so that nothing arrives here merely because it
#: is caught nowhere.
#:
#: Three of the seven were covered by a distribution, as three of Sun's were, and two of those
#: three by the same two baskets of Eggs. The third is the one this half is best known for
#: lacking, and it was covered four times over.
ONLY_ON_SUN: dict[str, str | None] = {
    # The other two of the Egg basket.
    "passimian": alola.handed_out(alola.EASTER_EGGS, alola.KOREAN_EGGS, alola.BANK_HIDDEN_ABILITY),
    # And the one with a fourth giveaway of its own: Kiawe's, from the animation, which went out
    # in Japan twice and in South Korea once over the summer of 2017.
    "turtonator": alola.handed_out(
        alola.EASTER_EGGS, alola.KOREAN_EGGS, "Kiawe's Turtonator in the summer of 2017"
    ),
    # Not the Vulpix of Kanto, which Bank will hand over: the Alolan one on Mount Lanakila, in
    # Sun. It is the most given-away entry in either half's table - a Pokemon Center in Sapporo
    # in the snow of 2016, a Korean giveaway in the spring, and Lillie's own over the summer.
    "vulpix": alola.handed_out(
        "the Pokemon Center Sapporo Alolan Vulpix over the winter of 2016",
        "the Pokemon Sun & Moon Alolan Vulpix in South Korea in the spring",
        "Lillie's Alolan Vulpix in Japan and South Korea that summer",
    ),
    # This half's two Ultra Beasts, and nothing ever handed either out.
    "buzzwole": None,
    "kartana": None,
    # Unova's two again, the other way round.
    "rufflet": None,
    "cottonee": None,
}

#: Dex entries no amount of playing this release will fill, and why.
#:
#: Ten, the same count as the other half: the nine Sun keeps, two of them fossils, and Marshadow.
#:
#: Cranidos and Tirtouga are the fossils Olivia does not stock here, and the Skull and Cover can
#: still come across held by a traded Pokemon. Like Sun's pair, the only distribution either has
#: ever had was the Pokemon Adventure Camp in Japan in 2012, for Black and White.
UNOBTAINABLE: dict[str, str] = {
    **alola.SM_UNOBTAINABLE,
    **{
        species: alola.fossil_only_on("Sun", fossil)
        for species, fossil in (("cranidos", "Skull Fossil"), ("tirtouga", "Cover Fossil"))
    },
    **{species: alola.only_on("Sun", event) for species, event in ONLY_ON_SUN.items()},
}


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

    The unobtainable table is what step 7 added: the nine Sun keeps, the two fossils Olivia
    does not stock in this half, and the one entry neither half of the pair produces.
    """
    return alola.dex_entries(
        context, game_id=GAME_ID, dex=alola.SM_DEX, unobtainable=UNOBTAINABLE
    )


def acquisition_methods(
    context: BuildContext,
    entries: list[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something here: caught, handed over, traded for, evolved or hatched.

    Step 7 added the last of them, and it is the only record in this game that no source this
    pipeline reads has a row for: the Magearna a QR Code unlocks.
    """
    return alola.acquisition_methods(
        context, game_id=GAME_ID, version=POKEAPI_VERSION, entries=entries
    )


def edges() -> list[TransferEdge]:
    return alola.edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Moon EN boxart.png")
