"""Pokemon HOME: the node everything ends at, and the reason nothing comes back.

The second and last transfer-only node, and the one that closes the graph. Like :mod:`bank` it
is not a game - no dex of its own, no grass, nobody handing anything over - and it is in the
dataset so that the routes through it have something to point at. Registering it lights the one
edge that was still waiting, ``bank -> home``, which was the last held-back route in the
dataset.

It is a cloud service on a phone and on a Switch rather than an application on one console, and
it went on sale everywhere on the same day, which almost nothing in this dataset did. Bank was
Japan-only for six weeks; HOME was February 12th 2020 worldwide.

**What it is for, in one line: HOME is where the series stops being able to go back.** Bank
takes a Pokemon from a Generation 5 cartridge and will hand it to X; HOME takes one from Bank
and will never hand it to anything with a cartridge slot. Every route into it from the 3DS era
is one way, and the door itself shuts in February 2027 when Bank does. After that, a living dex
kept on the Switch and a living dex kept on a 3DS are two collections with nothing between them.

Within the Switch, though, it is the opposite of a dead end. The Switch version moves Pokemon
both ways with every core series game there, which is what :func:`home_edges` is: a deposit that
takes anything the game can hold and a withdrawal that hands back only what the game's own
Pokedex lists.

Three things it does that :func:`home_edges` deliberately does not cover, written down here so
that whoever builds those games does not reach for it out of habit:

* **Let's Go, Pikachu! and Let's Go, Eevee!** only take back a Pokemon that came from one of
  them in the first place, and anything that arrived in HOME from Bank or from Pokemon GO was
  converted to Sword and Shield's format on the way in and can never enter them at all. So the
  route out of HOME into Let's Go carries a set no filter here can name - not a species, not a
  generation, but where one particular Pokemon started - and the two halves of that pair are
  the only reason it matters.
* **Legends: Z-A** takes Pokemon in and gives nothing back to anything older, which is a shape
  no game has had before. Its TODO entry already says to check it against a live source first.
* **Pokemon GO** and the Switch releases of FireRed and LeafGreen send one way into HOME and are
  not games this dataset holds. GO has no Pokedex to fill and nothing is caught in it in the
  sense this tracker means; the Switch FireRed is a third entity beside the cartridge and the
  3DS Virtual Console release, and whether it belongs here is the same decision Generation 1
  needed and has not been made.

And one thing that is not a transfer at all: a Pokemon *visiting* Pokemon Champions never leaves
HOME. It comes back changed or it does not come back, but it is in HOME the whole time, so there
is no edge to draw.
"""

from __future__ import annotations

from datetime import date

from ..games import BuildContext, GameRegistry
from ..models import (
    AllSpeciesFilter,
    DexSource,
    Game,
    GameData,
    GameRelease,
    PresentInTargetDexFilter,
    TransferDirection,
    TransferEdge,
    TransferMechanism,
)

#: The transfer graph's node for Pokemon HOME.
NODE = "home"

#: Everywhere at once, which is rare enough here to be worth saying.
#:
#: This dataset keeps Japanese release dates because every game before Generation 6 reached
#: Japan first and the rest of the world months later. HOME had no such date to be first: iOS,
#: Android and the Switch, in every region, on one day.
RELEASED = date(2020, 2, 12)

#: Which generation's service this is.
#:
#: Generation 8, the way Bank is Generation 6's. It arrived three months after Sword and Shield
#: and was built for them - Brilliant Diamond and Shining Pearl, Legends: Arceus, Scarlet and
#: Violet and Legends: Z-A were each let in by a later version of it.
GENERATION = 8


def entity() -> Game:
    """HOME as the dataset holds it: a node, and nothing that resembles a game.

    The same shape :func:`bank.entity` has and for the same reasons. HOME does keep a Pokedex -
    Grand Oak's, of everything the player has ever put in it - and it is a record of what has
    been elsewhere rather than a list anybody is asked to fill here.
    """
    return Game(
        id=NODE,
        title="Pokémon HOME",
        version="HOME",
        generation=GENERATION,
        region="",
        release=GameRelease.SERVICE,
        released=RELEASED,
        national_dex_through=None,
        dex_source=DexSource.GAME_DEX,
    )


def build(context: BuildContext) -> GameData:
    """The node, with the empty dex that says what it is."""
    return GameData(game=entity())


def home_edges(game_id: str) -> list[TransferEdge]:
    """A Switch core series game that talks to HOME: the deposit, and the withdrawal beside it.

    Two one-way edges rather than one both-ways edge, as Bank's are, and here it is not only
    truer but the only thing that works. A both-ways edge carries one filter in both directions,
    and this filter is :class:`PresentInTargetDexFilter` - it asks whether the game being
    transferred *into* lists the species. Read backwards that question is asked of HOME, whose
    dex is empty, so a both-ways edge would have refused every deposit ever made.

    The deposit takes anything the game can hold, because HOME holds everything. The withdrawal
    is the whole point of the filter: Sword has no entry for Decidueye and HOME will not put one
    there, which is the first time in the series that where a Pokemon may go depends on a list
    rather than on a number or a generation.

    Not for every Switch game. The pairs this does not describe are in this module's own
    docstring, and each of them has a reason of its own.
    """
    return [
        TransferEdge(
            **{"from": game_id},
            to=NODE,
            mechanism=TransferMechanism.HOME,
            direction=TransferDirection.ONE_WAY,
            filter=AllSpeciesFilter(),
        ),
        TransferEdge(
            **{"from": NODE},
            to=game_id,
            mechanism=TransferMechanism.HOME,
            direction=TransferDirection.ONE_WAY,
            filter=PresentInTargetDexFilter(),
        ),
    ]


def register(registry: GameRegistry) -> None:
    """The node, and no routes of its own.

    Nothing leaves HOME that is not a game's own business, and every game that reaches it
    declares its side the way the Generation 6 cartridges declare Bank's. The one edge into it
    that exists today was declared by Bank, and it has been waiting since.
    """
    registry.register(NODE, build, node=True)
