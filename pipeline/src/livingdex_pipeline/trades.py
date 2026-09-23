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
    #: The town or place the trader stands in.
    location: str
    #: What the player has to hand over. The NPC will not take anything else - unless this is
    #: left out, which is the trader who will take whatever is in the party.
    wants: str | None = None
    #: Which form of :attr:`gets`, when the trader hands over a particular one.
    #:
    #: Alola is the first region where one does: the trader in Tapu Village wants a Haunter and
    #: gives an Alolan Graveler, and "Graveler" would name the wrong rock. Unova has the other
    #: case and still cannot use it - Kyle's Basculin in Driftveil City is one stripe in Black
    #: and the other in White, and which is which is not written anywhere this dataset has read.
    form: str | None = None
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
            target=DexTarget(species=trade.gets, form=trade.form),
            location=trade.location,
            npc=trade.npc,
            wants=DexTarget(species=trade.wants) if trade.wants else None,
            requirement=trade.requirement,
            source=citation,
        )
        for trade in trades
    ]
