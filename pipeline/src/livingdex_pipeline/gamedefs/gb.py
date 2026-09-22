"""What every Generation 1 game shares, whichever region it is set in.

Red, Blue and Yellow are all Kanto, so this module and :mod:`kanto` cover the same three games
today - and they are still two modules, for the reason :mod:`ds` gives. What is here is the
generation: a dex of 151 and no National Dex behind it, three games that trade with each other,
a Time Capsule forward into Generation 2, and Poke Transporter out to Bank. What is in the
region is Kanto's own: its Pokedex, its towns, its trades.

The Time Capsule is the odd one. Every other route in this dataset either carries everything a
game can hold or is one way; this one goes both ways and refuses half of what the newer side
can offer, because a Generation 1 game has nowhere to put a Generation 2 Pokemon.
"""

from __future__ import annotations

from datetime import date

from ..models import (
    AllSpeciesFilter,
    Game,
    NationalDexRangeFilter,
    TransferDirection,
    TransferEdge,
    TransferMechanism,
)
from . import exclusives, vc

GENERATION = 1

#: The dex stops at Mew, and it is the game's own list rather than a National Dex: there was
#: nothing else yet for it to be a subset of.
DEX_THROUGH = 151

#: Every Generation 1 release that trades with every other. Green is not here: it was Japan's
#: and its Virtual Console release never left Japan, so this dataset would be claiming a game
#: most players cannot buy.
RELEASES = ("red", "blue", "yellow")

#: The Generation 2 releases each of these can open a Time Capsule with. Declared whether or
#: not they are in the dataset yet; the registry holds each edge back until the other end is
#: registered and the build says which are waiting.
GEN_2_RELEASES = ("gold", "silver", "crystal")


def release(
    *,
    game_id: str,
    title: str,
    version: str,
    region: str,
    released: date,
    pair_partner: str | None = None,
    sprite_set: str | None = None,
) -> Game:
    """One Generation 1 release, with the facts all three of them share filled in."""
    return vc.release(
        game_id=game_id,
        title=title,
        version=version,
        generation=GENERATION,
        region=region,
        released=released,
        dex_through=DEX_THROUGH,
        pair_partner=pair_partner,
        sprite_set=sprite_set,
    )


def link_trade_edges(game_id: str) -> list[TransferEdge]:
    """What this release trades with: every other Generation 1 release, both ways."""
    return [
        TransferEdge(
            **{"from": game_id},
            to=partner,
            mechanism=TransferMechanism.TRADE,
            direction=TransferDirection.BOTH_WAYS,
            filter=AllSpeciesFilter(),
        )
        for partner in RELEASES
        if partner != game_id
    ]


def time_capsule_edges(game_id: str) -> list[TransferEdge]:
    """The Time Capsule, between this release and each Generation 2 one.

    Both ways, and limited to the first 151 in both directions. Going forward that limit is no
    limit at all - a Generation 1 game has nothing else to send - and coming back it is the
    whole story: a Chikorita has no place in a game that has never heard of it.

    Declared here rather than by the Generation 2 side because the limit is a fact about this
    one. It is the same reasoning that leaves Pal Park with the Generation 4 game that receives.
    """
    return [
        TransferEdge(
            **{"from": game_id},
            to=partner,
            mechanism=TransferMechanism.TIME_CAPSULE,
            direction=TransferDirection.BOTH_WAYS,
            filter=NationalDexRangeFilter(**{"from": 1}, to=DEX_THROUGH),
        )
        for partner in GEN_2_RELEASES
    ]


def edges(game_id: str) -> list[TransferEdge]:
    """Every route one Generation 1 release brings.

    All three kinds together, deliberately. Platinum once declared its trades in one place and
    its Pal Park edges in another, and when Ruby and Sapphire arrived only the trades grew - so
    for two releases the dataset said Ruby reached Generation 4 by way of Emerald.
    """
    return [
        *link_trade_edges(game_id),
        *time_capsule_edges(game_id),
        vc.transporter_edge(game_id),
    ]


def only_on(partner: str, event: str | None = None) -> str:
    """Why an entry in this dex is not in this release, when the other half has it."""
    return exclusives.only_on(partner, generation=GENERATION, event=event)
