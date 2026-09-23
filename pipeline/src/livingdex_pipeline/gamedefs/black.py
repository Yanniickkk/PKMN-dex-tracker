"""Pokemon Black: what it is, the routes it brings, and the list it shows.

Phase 2 steps 1 to 7 for this game. What it says about itself is here; what is true of
every Unova game - the 156 entries included, which both halves number alike - is in
:mod:`unova`, and what is true of the five cartridges that send into it is in :mod:`ds`.

What is left for this file is its name, that White is its other half, and which version PokeAPI
is asked about - and one warning for the steps after this one. Black City and White Forest stand
in the same place on the map and are not the same kind of place: the city holds shops and
trainers and no wild Pokemon at all, and the forest holds a dozen species from older generations
that Black has nowhere else. So this half of the pair is short of more than the usual handful of
exclusives, and the difference is a whole area rather than a swap. That is step 3's business,
not this one's.
"""

from __future__ import annotations

from datetime import date

from ..games import BuildContext, GameRegistry
from ..models import AcquisitionMethod, DexEntry, GameData, TransferEdge
from . import unova

GAME_ID = "black"

#: The other half of the pair. Which species that switch decides is step 4's answer, not this
#: step's; all that is claimed here is that the two halves exist and know about each other.
PAIR_PARTNER = "white"

#: What PokeAPI calls this game when it lists which version an encounter belongs to. It is the
#: whole difference between this file and its partner's.
POKEAPI_VERSION = "black"

#: Japan, September 2010 - and the last pair in this dataset to arrive on the DS the way the
#: four before them did, a year before the 3DS could have played them.
RELEASED = date(2010, 9, 18)


#: In the Unova dex and never in this half, which games do have it, and what step 7 found.
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
#: of the legendaries White keeps were handed out, and every one of those distributions was
#: aimed at the half that could not catch it. What no distribution ever covered is the ordinary
#: five - two whole lines and a pair of birds - which nobody made a fuss of.
#:
#: The names were one name each until the sequels were written. Four cartridges in one
#: generation means a version exclusive can be in more than one other place, and five of these
#: seven now are: Solosis is in White and in White 2, and Zekrom is in White and in Black 2.
#: Thundurus is the one that did not grow - the sequels do not have it either, and what they
#: have instead is a 3DS download.
ELSEWHERE_IN_GENERATION_5: dict[str, tuple[tuple[str, ...], str | None]] = {
    "solosis": (("White", "White 2"), None),
    "duosion": (("White", "White 2"), None),
    "reuniclus": (("White", "White 2"), None),
    "rufflet": (("White", "White 2"), None),
    "braviary": (("White", "White 2"), None),
    # The forces of nature: one roams each half, and the giveaway covered the other.
    "thundurus": (
        ("White",),
        unova.handed_out("the Milos Island Thundurus over Wi-Fi in December 2011")
        + ", in Japan and South Korea and nowhere else",
    ),
    # And the cover legendaries the same way round. Black's box has Reshiram on it and White's
    # has Zekrom, so this is the one entry in the pair that a player can see is missing from
    # the outside.
    "zekrom": (
        ("White", "Black 2"),
        unova.handed_out(
            "Ash's Zekrom in Japan in the summer of 2011",
            "the Spring 2012 Zekrom over Wi-Fi",
        ),
    ),
}

#: Dex entries no amount of playing this release will fill, and why.
#:
#: Thirteen: the six neither half can fill, and the seven the other half keeps.
UNOBTAINABLE: dict[str, str] = {
    **unova.BW_UNOBTAINABLE,
    **{
        species: unova.only_on(elsewhere, event)
        for species, (elsewhere, event) in ELSEWHERE_IN_GENERATION_5.items()
    },
}


def build(context: BuildContext) -> GameData:
    entries = dex_entries(context)

    return GameData(
        game=unova.cartridge(
            game_id=GAME_ID,
            title="Pokémon Black Version",
            version="Black",
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
    registry.register(GAME_ID, build, edges(), box_art="Black EN boxart.png")
