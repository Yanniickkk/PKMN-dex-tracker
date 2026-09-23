"""Pokemon White: what it is, the routes it brings, and the list it shows.

Phase 2 steps 1 to 7 for this game. What it says about itself is here; what is true of
every Unova game - the 156 entries included, which both halves number alike - is in
:mod:`unova`, and what is true of the five cartridges that send into it is in :mod:`ds`.

What is left for this file is its name, that Black is its other half, and which version PokeAPI
is asked about. The area the pair disagree about is described from Black's side: White Forest
stands where Black City does, and what it holds - a dozen species from older generations, and
which of them appear depending on who has moved in - is what step 3 will have to read carefully.
"""

from __future__ import annotations

from datetime import date

from ..games import BuildContext, GameRegistry
from ..models import AcquisitionMethod, DexEntry, GameData, TransferEdge
from . import unova

GAME_ID = "white"

#: The other half of the pair. Which species that switch decides is step 4's answer, not this
#: step's; all that is claimed here is that the two halves exist and know about each other.
PAIR_PARTNER = "black"

#: What PokeAPI calls this game when it lists which version an encounter belongs to. It is the
#: whole difference between this file and its partner's.
POKEAPI_VERSION = "white"

#: The same day as Black, as every pair in this dataset has been.
RELEASED = date(2010, 9, 18)


#: In the Unova dex and never in this half, which of the two does have it, and what step 7 found.
#:
#: Seven, mirroring the other half exactly - which is what a version pair is. They are still
#: entries to fill, and the link between the two halves is how.
#:
#: Worked out after the trades and evolutions of step 5 rather than from the encounter tables,
#: and this generation is the clearest case yet for why. Cottonee and Petilil look exactly like
#: two more of these - each is in one half's grass and not the other's - and neither is here,
#: because Dye in Nacrene City swaps each half the one it is missing.
#:
#: The events are the surprise. Generation 4's four exclusives had nothing at all; here, both
#: of the legendaries Black keeps were handed out, and every one of those distributions was
#: aimed at the half that could not catch it. What no distribution ever covered is the ordinary
#: five - two whole lines and a pair of birds - which nobody made a fuss of.
ELSEWHERE_IN_GENERATION_5: dict[str, tuple[str, str | None]] = {
    "gothita": ("Black", None),
    "gothorita": ("Black", None),
    "gothitelle": ("Black", None),
    "vullaby": ("Black", None),
    "mandibuzz": ("Black", None),
    # The forces of nature: one roams each half, and the giveaway covered the other.
    "tornadus": (
        "Black",
        unova.handed_out("the Milos Island Tornadus over Wi-Fi in December 2011")
        + ", in Japan and South Korea and nowhere else",
    ),
    # And the cover legendaries the same way round. White's box has Zekrom on it and Black's
    # has Reshiram, so this is the one entry in the pair that a player can see is missing from
    # the outside.
    "reshiram": (
        "Black",
        unova.handed_out(
            "Ash's Reshiram in Japan in the summer of 2011",
            "the Spring 2012 Reshiram over Wi-Fi",
        ),
    ),
}

#: Dex entries no amount of playing this release will fill, and why.
#:
#: Thirteen: the six neither half can fill, and the seven the other half keeps.
UNOBTAINABLE: dict[str, str] = {
    **unova.BW_UNOBTAINABLE,
    **{
        species: unova.only_on(partner, event)
        for species, (partner, event) in ELSEWHERE_IN_GENERATION_5.items()
    },
}


def build(context: BuildContext) -> GameData:
    entries = dex_entries(context)

    return GameData(
        game=unova.cartridge(
            game_id=GAME_ID,
            title="Pokémon White Version",
            version="White",
            released=RELEASED,
            pair_partner=PAIR_PARTNER,
            sprite_set=unova.SPRITE_SET,
        ),
        dex_entries=entries,
        acquisition_methods=acquisition_methods(context, entries),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """The Unova dex, the same 156 entries and numbering both halves show.

    Both halves show one list, as every pair in this dataset does. What they disagree about is
    which of those entries a player can fill, and the unobtainable table is that answer: six
    neither half reaches and seven this one leaves to the other.
    """
    return unova.bw_dex_entries(context, game_id=GAME_ID, unobtainable=UNOBTAINABLE)


def acquisition_methods(
    context: BuildContext,
    entries: list[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something here. Wild slots so far, read for this version alone."""
    return unova.bw_acquisition_methods(
        context,
        game_id=GAME_ID,
        version=POKEAPI_VERSION,
        entries=entries,
    )


def edges() -> list[TransferEdge]:
    return unova.edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="White EN boxart.png")
