"""Pokemon Ultra Moon: what it is, and the routes it brings.

Phase 2 steps 1 and 2, the other half of :mod:`ultra_sun`. Everything the four Alola cartridges
share is in :mod:`alola`, and what is left here is a name, a partner and a date.

The clocks are this half's own quirk, as they were Moon's: Ultra Moon runs twelve hours out from
the 3DS's, so two players standing side by side are in different halves of the day. Nothing in
this step can record that, and by step 3 it decides which encounters exist.

The two things a reader of this file should know are :mod:`ultra_sun`'s and are not repeated
here: these two are the first second pair to move the National Dex on, and the first release in
the series that was one day in every region at once.
"""

from __future__ import annotations

from datetime import date

from ..games import BuildContext, GameRegistry
from ..models import AcquisitionMethod, DexEntry, GameData, TransferEdge
from . import alola

GAME_ID = "ultra-moon"

#: The other half of the pair.
PAIR_PARTNER = "ultra-sun"

#: What PokeAPI calls this game when it lists which version an encounter belongs to.
POKEAPI_VERSION = "ultra-moon"

#: The same day as its other half, which is the only kind of release date a pair has ever had.
RELEASED = date(2017, 11, 17)


#: In the Alola dex and never in this cartridge, and what step 7 found about each.
#:
#: Eleven, mirroring the other half, and ten of them were never handed out at all - which is
#: :mod:`ultra_sun`'s note and the whole of what step 7 found about this pair.
#:
#: Passimian is the one exception, and it is the same exception: a Pokemon Bank giveaway in 2019
#: that covered all four cartridges. Turtonator was covered four times over for Sun and Moon,
#: Kiawe's own among them, and not once for these two.
ONLY_ON_ULTRA_SUN: dict[str, str | None] = {
    "passimian": alola.handed_out(alola.BANK_HIDDEN_ABILITY),
    "turtonator": None,
    "vulpix": None,
    "buzzwole": None,
    "kartana": None,
    "blacephalon": None,
    "rufflet": None,
    "cottonee": None,
    "houndour": None,
    "golett": None,
    "clauncher": None,
}

#: Dex entries no amount of playing this release will fill, and why.
#:
#: Thirteen, the same count as the other half: eleven it keeps, and Marshadow and Zeraora. The
#: fossils are not here, for the reason :mod:`ultra_sun` gives.
UNOBTAINABLE: dict[str, str] = {
    **alola.USUM_UNOBTAINABLE,
    **{
        species: alola.only_on("Ultra Sun", event)
        for species, event in ONLY_ON_ULTRA_SUN.items()
    },
}


def build(context: BuildContext) -> GameData:
    """The game entity and the list it shows. How any of it is filled is steps 3 onwards."""
    entries = dex_entries(context)

    return GameData(
        game=alola.cartridge(
            game_id=GAME_ID,
            title="Pokémon Ultra Moon",
            version="Ultra Moon",
            released=RELEASED,
            national_dex_through=alola.USUM_NATIONAL_DEX_THROUGH,
            pair_partner=PAIR_PARTNER,
        ),
        dex_entries=entries,
        acquisition_methods=acquisition_methods(context, entries),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """The Alola dex, the same 403 entries and numbering its other half shows.

    Both halves show one list, as every pair in this dataset does. What they disagree about is
    which of those entries a player can fill, and that is the unobtainable table's answer - step
    7's, once steps 3 to 5 have said what each half really holds.

    How far this list has moved from Sun and Moon's is :mod:`ultra_sun`'s note, and it is worth
    reading before anything downstream compares the two by number.
    """
    return alola.dex_entries(
        context, game_id=GAME_ID, dex=alola.USUM_DEX, unobtainable=UNOBTAINABLE
    )


def acquisition_methods(
    context: BuildContext,
    entries: list[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something here: caught, handed over, traded for, evolved or hatched.

    The rest of the tables are the steps that gather them: what is handed over, what an NPC
    swaps for, what evolves into what, and how a form is come by. A table this does not pass is
    a step that has not run, which is what :func:`alola.acquisition_methods` means by leaving
    one out.
    """
    return alola.acquisition_methods(
        context,
        game_id=GAME_ID,
        version=POKEAPI_VERSION,
        entries=entries,
        reach=alola.USUM_NATIONAL_DEX_THROUGH,
        gifts=alola.usum_gifts(GAME_ID),
        excluded=alola.usum_excluded(GAME_ID),
        version_group=alola.USUM_VERSION_GROUP,
        trades=alola.USUM_TRADES,
        form_changes=alola.usum_form_changes(context.forms_here()),
        eggs=True,
    )


def edges() -> list[TransferEdge]:
    """Its trades with the other three cartridges, and Bank both ways."""
    return alola.edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Ultra Moon EN boxart.png")
