"""In-game trades for one game.

The other half of step 5, and the half no API answers. PokeAPI knows where a Pokemon is met
and how it evolves; it has nothing at all about the girl in Rustboro City who wants a Ralts.
So a game's trades are a table in that game's own file, the same way its gifts already are,
and what is here is only the machinery that turns the table into records.

Player-to-player trading is not this. That is a route in the transfer graph, and it is about
two games rather than about one.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .models import DexTarget, SourceCitation, TradeAcquisition


@dataclass(frozen=True)
class InGameTrade:
    """One NPC who will swap one Pokemon for another."""

    #: What the player receives.
    gets: str
    #: What the player has to hand over. The NPC will not take anything else.
    wants: str
    #: The town or place the trader stands in.
    location: str
    #: Who trades. The games record the trader as the original trainer of what they hand over,
    #: which is where this name comes from.
    npc: str | None = None
    #: What has to be true first, for a trade that is not open from the start.
    requirement: str | None = None


def trade_encounters(
    *,
    game_id: str,
    trades: Sequence[InGameTrade],
    citation: SourceCitation,
) -> list[TradeAcquisition]:
    """One record per trade, in the order the game's table lists them."""
    return [
        TradeAcquisition(
            game=game_id,
            target=DexTarget(species=trade.gets),
            location=trade.location,
            npc=trade.npc,
            wants=DexTarget(species=trade.wants),
            requirement=trade.requirement,
            source=citation,
        )
        for trade in trades
    ]
