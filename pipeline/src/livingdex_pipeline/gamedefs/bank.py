"""Pokemon Bank: the node itself, the routes into it, and the one thing it will not hand back.

Bank is not a game. It is three thousand boxes on somebody else's server, with no dex of its
own, no grass and nobody handing anything over, and in this dataset it is a node in the transfer
graph and nothing else: an entity with an empty dex, so that the routes through it have
something to point at. Every release that reaches it has declared its side of the route since
Phase 2, and the registry held each one back until this file existed. Adding it lights fourteen
of them at once.

There are two ways in rather than one, and which a game gets is the line between the cartridge
era and what came after. Everything up to Generation 5 reaches Bank through Poke Transporter,
one way and permanently: a Pokemon goes in and the game it came from never sees it again.
Generation 6 onward talks to Bank itself, because Bank was written for those games and the
older ones were let in through a side door. So Bank is the end of the line for Black and a
shelf for X.

The Transporter route lived in :mod:`vc` until Generation 5 needed it too, which had the
history backwards. Poke Transporter shipped in December 2013 to move Black, White, Black 2 and
White 2 into Bank; the Virtual Console releases were only given to it three years later. It is
a fact about Bank rather than about the Virtual Console, so it is written here and both sides
ask for it.

And the thing it will not hand back, which is the whole reason :class:`HistoryWindow` exists.
Bank takes a Pokemon from a Virtual Console Red as readily as from Black, and it will not put
that one into X - nor will it put back anything that has ever been in Sun. The Generation 6
games cannot read what either end writes, so a deposit and a withdrawal are not one route run
backwards, and they are written here as two one-way edges rather than as one both-ways edge.
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
    HistoryWindow,
    SpeciesFilter,
    TransferDirection,
    TransferEdge,
    TransferMechanism,
)

#: The transfer graph's node for Pokemon Bank.
NODE = "bank"

#: Japan, on Christmas Day 2013. Europe and the Americas waited until February, because the
#: servers fell over in the first days and the western release was pulled and rescheduled.
#:
#: The Japanese date, like every other release here. It is also the date that puts Bank where it
#: belongs in a list: a month after X and Y, which are the games it was built for.
RELEASED = date(2013, 12, 25)

#: Which generation's service this is.
#:
#: Generation 6, and the number is doing real work rather than filling a required field: it is
#: why Bank talks to eight games and then stops. It was built for X and Y, given Sun and Moon
#: three years later, and never given anything after them - Generation 8 got HOME instead, and
#: Bank's last job is to empty itself into it.
GENERATION = 6

#: What Bank will hand to a Generation 6 game: only a Pokemon whose whole history is Generations
#: 3 to 6.
#:
#: Bulbapedia writes this as one sentence with two halves - anything that has ever been in a
#: Generation 7 game, or that was transferred from a Generation 1 or 2 game, cannot be moved to
#: the Generation 6 games - and both halves say the same thing from either end: X and Omega Ruby
#: cannot read what those games write, and Bank knows it. It draws a white square around such a
#: Pokemon while a Generation 6 game is connected, which is as near as it comes to saying so.
#:
#: The floor of 3 is not a guess. A Generation 3 Pokemon can be sitting in Bank, having come the
#: long way through Pal Park, the Poke Transfer and Transporter, and X will take it.
#:
#: What this costs the graph is the whole reason for writing it down. Without it the dataset
#: would say a Pokemon caught in a Virtual Console Red can be walked into X in two moves, which
#: is false, and which is exactly the shape of route a player would try and lose an evening to.
GENERATION_6_WITHDRAWAL = HistoryWindow(**{"from": 3}, to=GENERATION)


def entity() -> Game:
    """Bank as the dataset holds it: a node, and nothing that resembles a game.

    No National Dex and no dex of its own, which is what an empty entry list means here. Bank
    does show a National Pokedex, of what a player has registered in the games connected to it,
    and registering is not obtaining: nothing is ever caught in Bank.

    No region either. Every game in this dataset is set somewhere and this one is set nowhere,
    so the field is left empty rather than filled with a word that would read as a place.
    """
    return Game(
        id=NODE,
        title="Pokémon Bank",
        version="Bank",
        generation=GENERATION,
        region="",
        release=GameRelease.SERVICE,
        released=RELEASED,
        national_dex_through=None,
        dex_source=DexSource.GAME_DEX,
    )


def build(context: BuildContext) -> GameData:
    """The node, with the empty dex that says what it is.

    A builder that asks its context nothing, which no other entry in the registry does. It is
    here because the registry is how anything gets into the dataset at all, and because the
    validator's ``transfer-edges-connect-known-games`` counts a node as known only when there is
    a game file for it.
    """
    return GameData(game=entity())


def transporter_edge(game_id: str) -> TransferEdge:
    """Poke Transporter into Pokemon Bank: the one route out of a game that cannot trade on.

    One way, and permanently. The filter is everything the game can hold, because Transporter
    does not choose by species: what it refuses is a Pokemon holding an item, one that knows an
    HM move, and an egg, and none of those is a species.
    """
    return TransferEdge(
        **{"from": game_id},
        to=NODE,
        mechanism=TransferMechanism.POKE_TRANSPORTER,
        direction=TransferDirection.ONE_WAY,
        filter=AllSpeciesFilter(),
    )


def bank_edges(
    game_id: str,
    *,
    withdrawal: HistoryWindow | None = None,
    carries: SpeciesFilter | None = None,
) -> list[TransferEdge]:
    """A game that talks to Bank itself: the deposit, and the withdrawal beside it.

    Two one-way edges rather than one both-ways edge, and the difference is not bookkeeping.
    Bank takes anything a game can hold; what it gives back is narrower, in two ways that have
    nothing to do with each other. ``withdrawal`` is where a Pokemon may have *been* - the
    Generation 6 games refuse anything from outside their own stretch of the series. ``carries``
    is what it may *be*: Sun and Moon will not take the five species Ultra Sun and Ultra Moon
    introduced, whatever route they came by.

    A both-ways edge says one thing about both directions, and in every case so far the two
    directions disagree.

    This is the first place in this dataset where a living dex can be kept somewhere that is not
    a game, and the asymmetry is what that costs: a player can put anything on the shelf and
    cannot take all of it back off.
    """
    return [
        TransferEdge(
            **{"from": game_id},
            to=NODE,
            mechanism=TransferMechanism.BANK,
            direction=TransferDirection.ONE_WAY,
            filter=AllSpeciesFilter(),
        ),
        TransferEdge(
            **{"from": NODE},
            to=game_id,
            mechanism=TransferMechanism.BANK,
            direction=TransferDirection.ONE_WAY,
            filter=carries or AllSpeciesFilter(),
            history=withdrawal,
        ),
    ]


def edges() -> list[TransferEdge]:
    """What Bank brings of its own: the way out, into HOME.

    One way, and the only route in this dataset whose far end empties the near one - a Pokemon
    moved from Bank into HOME cannot be moved back. After February 2027 nothing can be moved at
    all: the service was given an end date in August 2026, which makes this edge the last door
    out of every 3DS game here rather than one route among several.

    Held back until HOME is written, like every edge whose other end is not here yet.
    """
    return [
        TransferEdge(
            **{"from": NODE},
            to="home",
            mechanism=TransferMechanism.HOME,
            direction=TransferDirection.ONE_WAY,
            filter=AllSpeciesFilter(),
        )
    ]


def register(registry: GameRegistry) -> None:
    registry.register(NODE, build, edges(), node=True)
