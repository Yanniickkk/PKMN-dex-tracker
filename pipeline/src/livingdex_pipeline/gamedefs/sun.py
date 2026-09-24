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


#: In the Alola dex and never in this cartridge, and what step 7 found about each.
#:
#: Seven here and two more in the fossil table below, so nine in all - and the other half keeps
#: nine too, which is what a version pair looks like when it is written carefully. Those
#: eighteen are the whole of the difference between these two games: every other entry in the
#: 302 is in both.
#:
#: Worked out *after* the evolutions and eggs of step 5, as every list like this has been since
#: Black's file explained why. Mandibuzz is caught nowhere in Sun either, and it is not here,
#: because the Vullaby it comes from crosses the link and evolves on this side of it.
#:
#: The value is what a distribution ever did about it. Three of the seven were covered, and two
#: of those three by the same pair of giveaways - which is the finding, because those giveaways
#: went to *both* halves. Somebody at Pokemon put the four exclusives nobody could trade for
#: into one basket of Eggs and handed it to everyone.
ONLY_ON_MOON: dict[str, str | None] = {
    # The Egg basket: two of the four are Moon's, and this is one of them.
    "oranguru": alola.handed_out(alola.EASTER_EGGS, alola.KOREAN_EGGS, alola.BANK_HIDDEN_ABILITY),
    "drampa": alola.handed_out(alola.EASTER_EGGS, alola.KOREAN_EGGS),
    # Not the Sandshrew of Kanto, which Bank will hand over: the one on Mount Lanakila, which is
    # Alolan and is Moon's. The giveaway that covered it was Korean and lasted seven weeks.
    "sandshrew": alola.handed_out(
        "the Pokemon Sun & Moon Alolan Sandshrew in South Korea over May and June 2017"
    ),
    # The two Ultra Beasts this half never meets. Nothing ever handed either out, anywhere -
    # which is true of all four of the pair's Beasts and of nothing else in this table.
    "pheromosa": None,
    "celesteela": None,
    # Unova's two, on Route 3 and in the meadows, and neither has ever been given away for
    # these games. Cottonee's only distribution is Sword and Shield's Wild Area News.
    "vullaby": None,
    "petilil": None,
}

#: Dex entries no amount of playing this release will fill, and why.
#:
#: Ten: the nine the other half keeps, two of which are fossils, and the one neither of them can
#: produce. Magearna was the eleventh until step 7 read the page - see
#: :data:`alola.QR_MAGEARNA`.
#:
#: The fossils take their own sentence because a fossil is an item: Olivia sells the Skull and
#: the Cover in this half, and the Armor and the Plume can still cross the link in a traded
#: Pokemon's hands. Neither has ever been handed out for these games - the only distributions
#: Shieldon and Archen have ever had were a Japanese summer camp in 2012, for Black and White.
UNOBTAINABLE: dict[str, str] = {
    **alola.SM_UNOBTAINABLE,
    **{
        species: alola.fossil_only_on("Moon", fossil)
        for species, fossil in (("shieldon", "Armor Fossil"), ("archen", "Plume Fossil"))
    },
    **{species: alola.only_on("Moon", event) for species, event in ONLY_ON_MOON.items()},
}


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

    The unobtainable table is what step 7 added: the nine Moon keeps, the two fossils Olivia
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
        context,
        game_id=GAME_ID,
        version=POKEAPI_VERSION,
        entries=entries,
        reach=alola.SM_NATIONAL_DEX_THROUGH,
        gifts=alola.alola_gifts(GAME_ID),
        excluded=alola.alola_excluded(GAME_ID),
        recorded=alola.QR_MAGEARNA,
        version_group=alola.ALOLA_VERSION_GROUP,
        trades=alola.ALOLA_TRADES,
        form_changes=alola.alola_form_changes(context.forms_here()),
        eggs=True,
    )


def edges() -> list[TransferEdge]:
    return alola.edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Sun EN boxart.png")
