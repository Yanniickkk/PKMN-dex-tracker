"""Pokemon Bank, and Poke Transporter into it.

Bank is not a game: it is a box on somebody else's server, with no dex of its own, no grass and
nobody handing anything over. In this dataset it is a node in the transfer graph and nothing
else, and it is not written yet - every release that reaches it declares the route anyway, and
the registry holds each edge back until the node exists. The day Bank is added they light up
without anyone editing the games.

The route lived in :mod:`vc` until Generation 5 needed it too, which had the history backwards.
Poke Transporter shipped in December 2013 to move Black, White, Black 2 and White 2 into Bank;
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
