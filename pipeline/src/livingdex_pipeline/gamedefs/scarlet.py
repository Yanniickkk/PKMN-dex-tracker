"""Pokemon Scarlet: what it is, and the three routes it brings.

Phase 2 steps 1 to 5 and 7 for this game; the pictures and the forms are still to come.
What it says about itself is here; what is true of both halves - Paldea, the Hidden Treasure
of Area Zero and the way out - is in :mod:`paldea`.

**The half whose past is the exclusive.** Every pair since Red and Blue splits a list of species
between its two halves; these two split a *tense*. The ancient Paradox Pokemon are here - Great
Tusk, Scream Tail, Brute Bonnet, Flutter Mane, Slither Wing, Sandy Shocks, Roaring Moon and
Koraidon - and Violet gets the future's Iron ones. The professor goes with them: Sada here and
Turo there, Arven's mother against his father, which is a thing no pair before this split.

What is left for this file is its name, that Violet is its other half, which version PokeAPI is
asked about, and three lists it shares with that half entry for entry.
"""

from __future__ import annotations

from collections.abc import Sequence

from ..games import BuildContext, GameRegistry
from ..models import AcquisitionMethod, DexEntry, Game, GameData, TransferEdge
from . import paldea

GAME_ID = "scarlet"

#: The other half. Which species that switch decides is step 4's answer, and here it is a softer
#: answer than usual - :mod:`paldea` says why. All that is claimed here is that the two halves
#: exist and know about each other.
PAIR_PARTNER = "violet"

#: What PokeAPI calls this game when it lists which version an encounter belongs to.
#:
#: One of three names the source has for this half, and the plain one. The other two are the
#: expansions', and :data:`paldea.VERSIONS` holds all three, because reading only this one would
#: lose Kitakami and the Terarium without saying so.
POKEAPI_VERSION = "scarlet"


def entity() -> Game:
    """This half as the dataset holds it, with everything the two of them agree about filled
    in by :func:`paldea.cartridge`."""
    return paldea.cartridge(
        game_id=GAME_ID,
        title="Pokémon Scarlet",
        version="Scarlet",
        pair_partner=PAIR_PARTNER,
    )


def build(context: BuildContext) -> GameData:
    """The game entity and the three lists it shows. How any of it is filled is steps 3 onwards.

    Steps 3 to 5 have run, so every way this game hands a player a Pokemon is here: the wild,
    the fixed encounters, the statics, the twenty-one trades, the evolutions and the eggs.
    """
    entries = dex_entries(context)

    return GameData(
        game=entity(),
        dex_entries=entries,
        acquisition_methods=found(context, entries=entries),
    )


def found(
    context: BuildContext,
    *,
    entries: Sequence[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way this half produces anything, in the order the steps were written.

    The eggs come last and are worked out from what the rest came to, which is why they are not
    simply another entry in the list: a picnic can only be asked for what nothing else here
    produces.
    """
    caught = [
        *acquisition_methods(context, entries=entries),
        *handed_over(context, entries=entries),
    ]

    return [
        *caught,
        *paldea.swapped_and_evolved(
            context, game_id=GAME_ID, entries=entries, found=caught
        ),
    ]


def acquisition_methods(
    context: BuildContext,
    *,
    entries: Sequence[DexEntry],
) -> list[AcquisitionMethod]:
    """Every wild slot this half has, off the fifty pages that carry one of these tables.

    :func:`paldea.acquisition_methods` does the work for both halves, because the pages are the
    same pages: what differs between them is which rows have this half's letter coloured in.
    """
    return paldea.acquisition_methods(context, game_id=GAME_ID, entries=entries)


def handed_over(
    context: BuildContext,
    *,
    entries: Sequence[DexEntry],
) -> list[AcquisitionMethod]:
    """Everything this half hands over or leaves standing in one spot.

    Three of them are its own - the box legendary and two of the four Paradox Pokemon the
    Indigo Disk splits - and :data:`paldea.STATICS` is where that split is written down.
    """
    return paldea.handed_over(context, game_id=GAME_ID, entries=entries)


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """Paldea's 400, Kitakami's 200 and Blueberry's 243, as this game numbers them.

    The same three lists Violet shows, with the same numbers, which is what a version pair
    has always meant: the halves split what can be caught rather than what is listed.

    The ``unobtainable`` table is step 7's answer - the other half's twenty, and the two
    neither half produces - and :func:`paldea.unobtainable_in` is where the reasons live.
    """
    return paldea.dex_entries(
        context, game_id=GAME_ID, unobtainable=paldea.unobtainable_in(GAME_ID)
    )


def edges() -> list[TransferEdge]:
    """The cable to Violet, and HOME in both directions.

    Registering this game lights nothing that was waiting, and :func:`paldea.edges` says why
    that is the expected answer rather than a gap.
    """
    return paldea.edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Scarlet EN boxart.png")
