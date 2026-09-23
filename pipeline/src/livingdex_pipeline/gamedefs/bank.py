"""Pokemon Bank, Poke Transporter into it, and the games that talk to it themselves.

Bank is not a game: it is a box on somebody else's server, with no dex of its own, no grass and
nobody handing anything over. In this dataset it is a node in the transfer graph and nothing
else, and it is not written yet - every release that reaches it declares the route anyway, and
the registry holds each edge back until the node exists. The day Bank is added they light up
without anyone editing the games.

There are two routes rather than one, and which a game gets is the line between the cartridge
era and what came after. Everything up to Generation 5 reaches Bank through Poke Transporter,
one way and permanently: a Pokemon goes in and the game it came from never sees it again.
Generation 6 onward talks to Bank directly, in both directions, because Bank was written for
those games and the older ones were let in through a side door. So Bank is the end of the line
for Black and a box on the shelf for X.

The Transporter route lived in :mod:`vc` until Generation 5 needed it too, which had the
history backwards. Poke Transporter shipped in December 2013 to move Black, White, Black 2 and
White 2 into Bank;
the Virtual Console releases were only given to it three years later. It is a fact about Bank
rather than about the Virtual Console, so it is written here and both sides ask for it.
"""

from __future__ import annotations

from ..models import AllSpeciesFilter, TransferDirection, TransferEdge, TransferMechanism

#: The transfer graph's node for Pokemon Bank.
NODE = "bank"


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


def bank_edge(game_id: str) -> TransferEdge:
    """Pokemon Bank itself: a box a game deposits into and withdraws from.

    Both ways, which is what makes Generation 6 different from the four games Transporter was
    built for. Black can push into Bank and never pull anything back; X deposits and withdraws,
    so a living dex can be kept in Bank rather than only sent there - the first time in this
    dataset that is true of anywhere that is not a game.

    The filter is everything the game can hold, for the same reason Transporter's is: what Bank
    refuses is a Pokemon it has no room for and an egg, and neither of those is a species.
    """
    return TransferEdge(
        **{"from": game_id},
        to=NODE,
        mechanism=TransferMechanism.BANK,
        direction=TransferDirection.BOTH_WAYS,
        filter=AllSpeciesFilter(),
    )
