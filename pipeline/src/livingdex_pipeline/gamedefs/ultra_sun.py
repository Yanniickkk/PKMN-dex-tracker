"""Pokemon Ultra Sun: what it is, and the routes it brings.

Phase 2 steps 1 and 2 for this game, and nothing after them yet. What it says about itself is
here; what is true of Alola - which is also what is true of the four Generation 7 cartridges,
for the reason that module gives - is in :mod:`alola`.

**The first second pair in the series to move the National Dex on.** A third version has never
done it and nor has a pair of sequels: Emerald added no species to Ruby and Sapphire's 386,
Platinum added none to Diamond and Pearl's 493, Black 2 and White 2 added none to Black and
White's 649. These two add five - Poipole, Naganadel, Stakataka, Blacephalon and Zeraora - so
the entity carries 807 where Sun and Moon carry 802, and the five are the whole reason a cable
between the two pairs has to be capped.

**And the first release in the series that was one day everywhere.** X and Y managed one day in
four regions and this dataset called that the end of the months a game used to spend out in
Japan alone; Sun and Moon slipped back, with Europe five days behind. These two went out in
eight regions on 17 November 2017, mainland China and Hong Kong and Taiwan among them, which
none of the twenty-six games before this one in the dataset can say - Generation 7 is where the
series gained Chinese at all.

What is left for this file is its name, that Ultra Moon is its other half, which version PokeAPI
is asked about, and that date.
"""

from __future__ import annotations

from datetime import date

from ..games import BuildContext, GameRegistry
from ..models import AcquisitionMethod, DexEntry, GameData, TransferEdge
from . import alola

GAME_ID = "ultra-sun"

#: The other half of the pair. Which species that switch decides is step 4's answer; all that is
#: claimed here is that the two halves exist and know about each other.
PAIR_PARTNER = "ultra-moon"

#: What PokeAPI calls this game when it lists which version an encounter belongs to.
POKEAPI_VERSION = "ultra-sun"

#: One day, in eight regions at once. There is no "the Japanese date" to prefer here, which is
#: the first time that sentence has been true in this dataset.
RELEASED = date(2017, 11, 17)


#: In the Alola dex and never in this cartridge, and what step 7 found about each.
#:
#: Eleven, and the other half keeps eleven. Not the same eighteen the first pair split, either:
#: the fossils are in both halves here, and Electrike, Baltoy and Skrelp are exclusives these
#: two invented.
#:
#: **Ten of the eleven were never handed out at all**, which is the finding and the opposite of
#: what the first pair found. Sun and Moon's exclusives were covered six times over - a basket
#: of Easter Eggs, a Korean giveaway, Lillie's own Vulpix - and every one of those distributions
#: says "S M" in its games column and means it. By the time these two shipped the giveaways had
#: moved on, so a Drampa or an Alolan Sandshrew that is missing here stays missing.
#:
#: The one exception is a Pokemon Bank giveaway of 2019, which covered all four cartridges.
ONLY_ON_ULTRA_MOON: dict[str, str | None] = {
    "oranguru": alola.handed_out(alola.BANK_HIDDEN_ABILITY),
    # Covered three times for Sun and Moon and not once for these two.
    "drampa": None,
    "sandshrew": None,
    # The two Ultra Beasts this half never meets, and nothing ever handed either out.
    "pheromosa": None,
    "celesteela": None,
    "stakataka": None,
    # Unova's two, as they were for the first pair.
    "vullaby": None,
    "petilil": None,
    # And three the second pair split that the first did not.
    "electrike": None,
    "baltoy": None,
    "skrelp": None,
}

#: Dex entries no amount of playing this release will fill, and why.
#:
#: Thirteen: the eleven the other half keeps, and the two neither can produce. Two fewer than
#: the first pair's fifteen, and for a good reason - **the fossils are not on this list.** All
#: four are revived at the Restoration Center on Route 8 in both halves, where Olivia stocked
#: two of the four per cartridge.
UNOBTAINABLE: dict[str, str] = {
    **alola.USUM_UNOBTAINABLE,
    **{
        species: alola.only_on("Ultra Moon", event)
        for species, event in ONLY_ON_ULTRA_MOON.items()
    },
}


def build(context: BuildContext) -> GameData:
    """The game entity and the list it shows. How any of it is filled is steps 3 onwards."""
    entries = dex_entries(context)

    return GameData(
        game=alola.cartridge(
            game_id=GAME_ID,
            title="Pokémon Ultra Sun",
            version="Ultra Sun",
            released=RELEASED,
            national_dex_through=alola.USUM_NATIONAL_DEX_THROUGH,
            pair_partner=PAIR_PARTNER,
            sprite_set=alola.SPRITE_SET,
        ),
        dex_entries=entries,
        acquisition_methods=acquisition_methods(context, entries),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """The Alola dex as these two show it: 403 entries, Rowlet to Zeraora.

    **Not Sun and Moon's 302 with a hundred and one added to the end.** Nothing was taken away
    and every one of the hundred and one was slotted in where it belongs, so the two lists part
    company at #024 - Pichu in the older one, Buneary in this - and **only the first 23 numbers
    still mean the same thing in both**. 279 of Sun and Moon's 302 numbers point at something
    else here.

    That is why :data:`alola.SM_DEX` and :data:`alola.USUM_DEX` are separate constants and why
    neither is ever called "the Alola dex". It is Johto's situation rather than Platinum's:
    Platinum kept Diamond's 151 and put four after them, and every number it shared meant what
    it always had.

    Not the National Dex either, which none of these four games has. The grid is 807 tiles
    because that is what the boxes here can hold; this list is what the Rotom Dex displays, and
    the grid can be switched to it.
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
    """Its trades with the other three cartridges, and Bank both ways.

    Registering this game is what lights the two routes Sun and Moon have each been declaring
    into an empty space since they were written, and neither of their files is touched to do it.
    """
    return alola.edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Ultra Sun EN boxart.png")
