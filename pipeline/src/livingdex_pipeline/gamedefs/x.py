"""Pokemon X: what it is, and the routes it brings.

Phase 2 step 1 for this game, and nothing after it yet. What it says about itself is here; what
is true of Kalos is in :mod:`kalos`, and what is true of the four cartridges of its generation -
the trades between all of them, the National Dex to Volcanion, Bank standing where the Poke
Transfer stood - is in :mod:`gen6`.

What is left for this file is its name, that Y is its other half, which version PokeAPI is asked
about, and the day it came out - which is the same day everywhere. X and Y were the first games
in the series to be released worldwide at once, so the release date this dataset keeps for
every other game, the Japanese one, is for these two simply the date. Nothing else in
:mod:`gamedefs` can say that.

One warning for the steps after this one: the Pokedex this game shows is three Pokedexes.
Central, Coastal and Mountain Kalos are separate lists with separate numbering, handed over one
at a time as a player crosses the region, and no one of them is "the Kalos dex". Step 2 has to
decide what a dex list means when a game has three of them, and this step claims nothing about
it.
"""

from __future__ import annotations

from datetime import date

from ..games import BuildContext, GameRegistry
from ..models import AcquisitionMethod, DexEntry, GameData, TransferEdge
from . import kalos

GAME_ID = "x"

#: The other half of the pair. Which species that switch decides is step 4's answer, not this
#: step's; all that is claimed here is that the two halves exist and know about each other.
PAIR_PARTNER = "y"

#: What PokeAPI calls this game when it lists which version an encounter belongs to. It is the
#: whole difference between this file and its partner's.
POKEAPI_VERSION = "x"

#: Japan, America, Europe and Australia on one day in October 2013 - the first time in the
#: series, and the end of the months every game before this one spent out in Japan and nowhere
#: else. Black and White were six of them.
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
#: Sixteen, and the other half keeps sixteen too - which is what a version pair has always
#: looked like. It did not look like this an hour before it was written: counting the Friend
#: Safari as a way to get one left X with three and Y with ten, because a Safari holds whatever
#: a stranger's friend code decided and pays no attention to which cartridge is asking. The
#: Safari is recorded and not counted, :data:`kalos.NOT_COUNTED` says why, and the pair came
#: back into balance on its own.
#:
#: The seven marked ``IN_A_SAFARI`` are the ones a Safari really can hold, so the reason says
#: so: a player with the right friend has a way, and it is not one this dataset will promise.
#:
#: Four of the sixteen were handed out, and three of those four on the same day: the 2014 Korean
#: World Championship Series gave X players a Heracross, a Manectric and a Tyranitar and Y
#: players the three that half is missing. A distribution that covers a version exclusive is
#: not new - Black and White's legendaries were the same - but one that covers three at once,
#: chosen for the half that cannot catch them, is a deliberate piece of work.
#:
#: Worked out after the evolutions and eggs of step 5 rather than from the encounter tables, for
#: the reason Black's file gives. Half of this list arrives by breeding or evolving something
#: else, and a table written a step earlier would have been wrong about it.
ELSEWHERE_IN_GENERATION_6: dict[str, str | None] = {
    "aromatisse": None,
    "cloyster": IN_A_SAFARI,
    "dragalge": None,
    "electrike": None,
    "heracross": _safari_and(
        "the Summer 2014 Heracross over Nintendo Network in America",
        "the 2014 Korean World Championship Series Heracross",
    ),
    "larvitar": None,
    "liepard": IN_A_SAFARI,
    "manectric": _safari_and("the 2014 Korean World Championship Series Manectric"),
    "pupitar": IN_A_SAFARI,
    "purrloin": None,
    "shellder": None,
    "skrelp": None,
    "spritzee": IN_A_SAFARI,
    "throh": IN_A_SAFARI,
    "tyranitar": kalos.handed_out(
        "the Pokemon Center Battle Championship Tyranitar in Japan",
        "the 2014 Korean World Championship Series Tyranitar",
        "the XY&Z Tyranitar in South Korea two years later",
    ),
    # The one a player can see from the outside: Yveltal is on the other box. It is also the
    # only entry here a distribution handed out at level 100.
    "yveltal": kalos.handed_out(
        "the XY&Z Yveltal in Japan from November 2015",
        "the Descartes Yveltal in Europe",
        "the Pokemon the Series: XYZ Yveltal in America",
    ),
}

#: Dex entries no amount of playing this release will fill, and why.
#:
#: Nineteen: the sixteen the other half keeps, and the three neither half can produce.
UNOBTAINABLE: dict[str, str] = {
    **kalos.XY_UNOBTAINABLE,
    **{
        species: kalos.gen6_only_on("Y", event)
        for species, event in ELSEWHERE_IN_GENERATION_6.items()
    },
}


def build(context: BuildContext) -> GameData:
    """The game entity and the lists it shows. How any of them is filled is steps 3 to 8."""
    entries = dex_entries(context)

    return GameData(
        game=kalos.gen6_cartridge(
            game_id=GAME_ID,
            title="Pokémon X",
            version="X",
            released=RELEASED,
            pair_partner=PAIR_PARTNER,
            sprite_set=kalos.XY_SPRITE_SET,
        ),
        dex_entries=entries,
        acquisition_methods=acquisition_methods(context, entries),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """All three Kalos Pokedexes, the same 457 entries and numbering both halves show.

    Both halves show the same three lists, as every pair in this dataset does with its one.
    What they disagree about is which of those entries a player can fill, and the unobtainable
    table is that answer: three this one leaves to the other half.
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
    registry.register(GAME_ID, build, edges(), box_art="X EN boxart.png")
