"""Pokemon Y: what it is, and the routes it brings.

Phase 2 step 1 for this game, and nothing after it yet. Everything it shares with X is in
:mod:`kalos`, and everything it shares with the four cartridges of its generation is in
:mod:`gen6`. What is left is its name, that X is its other half, and which version PokeAPI is
asked about.

The pair is as evenly matched as any in the series and more so than most: one legendary each,
one fossil each, one Mega Stone each for a starter neither half chose, and a handful of
ordinary species swapped between the two. What that costs a player is step 4's answer; what it
means here is that the two files differ by four lines and a date they share.
"""

from __future__ import annotations

from datetime import date

from ..games import BuildContext, GameRegistry
from ..models import AcquisitionMethod, DexEntry, GameData, TransferEdge
from . import kalos

GAME_ID = "y"

#: The other half of the pair.
PAIR_PARTNER = "x"

#: What PokeAPI calls this game when it lists which version an encounter belongs to.
POKEAPI_VERSION = "y"

#: The same day as X, and the same day everywhere: October 2013 was the first time the series
#: released a pair worldwide at once. Written out here rather than read from the other half,
#: which is what every pair in this dataset does - a game states its own facts even when they
#: happen to match.
RELEASED = date(2013, 10, 12)


#: What is added to the reason for an entry a Friend Safari does hold.
#:
#: It is not a second way of putting the same thing: the trade is a way a player can go and
#: arrange, and this is a way that depends on whose friend code is in somebody's 3DS. Saying so
#: is better than either pretending the Safari is not there or counting it as an answer.
IN_A_SAFARI = "a Friend Safari can hold one, which takes somebody else's 3DS and their friend code"

def _safari_and(*events: str) -> str:
    """Both halves of the truth for one entry: a Safari might hold one, and a giveaway did."""
    return kalos.with_event(IN_A_SAFARI, kalos.handed_out(*events))


#: In the Kalos dexes and never in this half, and which one does have it.
#:
#: Sixteen, mirroring X exactly. X's file explains why that took a second pass: the Friend
#: Safari is recorded and not counted, and until it was, these two lists were ten and three.
#:
#: Four were handed out, and the mirror holds there too: the 2014 Korean World Championship
#: Series gave Y players an Aggron, a Houndoom and a Pinsir on the same two days it gave X
#: players the three this half catches.
#:
#: Worked out after the evolutions and eggs of step 5, for the reason X's file gives.
ELSEWHERE_IN_GENERATION_6: dict[str, str | None] = {
    "aggron": kalos.handed_out("the 2014 Korean World Championship Series Aggron"),
    "aron": None,
    "clauncher": None,
    "clawitzer": None,
    "houndoom": kalos.handed_out("the 2014 Korean World Championship Series Houndoom"),
    "houndour": None,
    "lairon": None,
    "mightyena": IN_A_SAFARI,
    "pinsir": _safari_and(
        "the Summer 2014 Pinsir over Nintendo Network in America",
        "the 2014 Korean World Championship Series Pinsir",
    ),
    "poochyena": None,
    "sawk": IN_A_SAFARI,
    "slurpuff": None,
    "starmie": None,
    "staryu": None,
    "swirlix": IN_A_SAFARI,
    # And the cover legendary, which is the one a player can see from the outside.
    "xerneas": kalos.handed_out(
        "the XY&Z Xerneas in Japan from October 2015",
        "the Pokemon the Series: XYZ Xerneas in America",
        "the Descartes Xerneas in Europe",
    ),
}

#: Dex entries no amount of playing this release will fill, and why.
#:
#: Nineteen: the sixteen the other half keeps, and the three neither half can produce.
UNOBTAINABLE: dict[str, str] = {
    **kalos.XY_UNOBTAINABLE,
    **{
        species: kalos.gen6_only_on("X", event)
        for species, event in ELSEWHERE_IN_GENERATION_6.items()
    },
}


def build(context: BuildContext) -> GameData:
    """The game entity and the lists it shows. How any of them is filled is steps 3 to 8."""
    entries = dex_entries(context)

    return GameData(
        game=kalos.gen6_cartridge(
            game_id=GAME_ID,
            title="Pokémon Y",
            version="Y",
            released=RELEASED,
            pair_partner=PAIR_PARTNER,
            sprite_set=kalos.XY_SPRITE_SET,
        ),
        dex_entries=entries,
        acquisition_methods=acquisition_methods(context, entries),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """All three Kalos Pokedexes, the same 457 entries and numbering X shows.

    Ten of them are X's to fill rather than this half's, which the unobtainable table says.
    """
    return kalos.gen6_dex_entries(context, game_id=GAME_ID, unobtainable=UNOBTAINABLE)


def acquisition_methods(
    context: BuildContext,
    entries: list[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something here. Wild slots so far, read for this version alone."""
    return kalos.gen6_acquisition_methods(
        context,
        game_id=GAME_ID,
        version=POKEAPI_VERSION,
        entries=entries,
    )


def edges() -> list[TransferEdge]:
    return kalos.gen6_edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Y EN boxart.png")
