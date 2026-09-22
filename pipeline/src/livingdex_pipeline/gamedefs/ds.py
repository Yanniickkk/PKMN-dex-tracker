"""What every Generation 4 cartridge shares, whichever region it is set in.

Diamond, Pearl and Platinum are Sinnoh; HeartGold and SoulSilver are Johto. What they have in
common is the hardware and the generation: the same wireless trading between all five, the same
National Dex ending at Arceus, the same Pal Park taking a Game Boy Advance cartridge out of the
slot underneath. Those facts live here rather than in a region, for the reason :mod:`gba` gives.

What stays with a region is everything a player would call the game: its Pokedex, its towns, its
day care, its trades.
"""

from __future__ import annotations

from datetime import date

from ..models import (
    AllSpeciesFilter,
    DexSource,
    Game,
    GameRelease,
    TransferDirection,
    TransferEdge,
    TransferMechanism,
)
from . import exclusives, gba

GENERATION = 4

#: The National Dex of this generation stops at Arceus.
NATIONAL_DEX_THROUGH = 493

#: Every Generation 4 cartridge that trades with every other, over DS wireless. All five share
#: one Union Room, and a game declares the whole set whether or not the others are built yet.
CARTRIDGES = ("diamond", "pearl", "platinum", "heartgold", "soulsilver")


def cartridge(
    *,
    game_id: str,
    title: str,
    version: str,
    region: str,
    released: date,
    sprite_set: str | None = None,
    pair_partner: str | None = None,
) -> Game:
    """One Generation 4 cartridge, with the facts all five of them share filled in."""
    return Game(
        id=game_id,
        title=title,
        version=version,
        generation=GENERATION,
        region=region,
        release=GameRelease.CARTRIDGE,
        released=released,
        national_dex_through=NATIONAL_DEX_THROUGH,
        dex_source=DexSource.NATIONAL_DEX,
        pair_partner=pair_partner,
        sprite_set=sprite_set,
    )


def link_trade_edges(game_id: str) -> list[TransferEdge]:
    """What this cartridge trades with, both ways and carrying anything it can hold."""
    return [
        TransferEdge(
            **{"from": game_id},
            to=partner,
            mechanism=TransferMechanism.TRADE,
            direction=TransferDirection.BOTH_WAYS,
            filter=AllSpeciesFilter(),
        )
        for partner in CARTRIDGES
        if partner != game_id
    ]


def only_on(partner: str, event: str | None = None) -> str:
    """Why an entry in this dex is not in this cartridge, when the other half has it.

    The same sentence Generation 3 uses, with this generation's number in it. Which is the
    point of :mod:`exclusives`: Diamond once would have told a player to trade one in from a
    Generation 3 game, because the wording was copied rather than shared.
    """
    return exclusives.only_on(partner, generation=GENERATION, event=event)


def edges(game_id: str) -> list[TransferEdge]:
    """Every route one Generation 4 cartridge brings: its trades, and Pal Park into it.

    Both together, deliberately. Platinum declared its trades in one place and its Pal Park
    edges in another, and when Ruby and Sapphire arrived only the trades grew - so for two
    releases the dataset said Ruby reached Generation 4 by way of Emerald. A game that has both
    kinds of route should not be able to remember only one of them.
    """
    return [*link_trade_edges(game_id), *gba.pal_park_edges(into=game_id)]
