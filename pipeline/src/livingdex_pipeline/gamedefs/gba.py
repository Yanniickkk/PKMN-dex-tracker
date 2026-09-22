"""What every Generation 3 cartridge shares, whichever region it is set in.

Ruby, Sapphire and Emerald are Hoenn; FireRed and LeafGreen are Kanto. What they have in common
is not the region at all - it is the hardware and the generation: the same link cable between
all five, the same National Dex ending at Deoxys, the same one-way trip into a Generation 4 DS
game. Those facts live here so that adding the Kanto pair did not mean copying them out of
:mod:`hoenn`, which is where they were written first and where they never belonged.

What stays with a region is everything a player would call the game: its Pokedex, its towns, its
day care, its trades. Those are in :mod:`hoenn` and :mod:`kanto`.
"""

from __future__ import annotations

from datetime import date

from ..models import (
    AllSpeciesFilter,
    DexSource,
    Game,
    GameRelease,
    NationalDexRangeFilter,
    TransferDirection,
    TransferEdge,
    TransferMechanism,
)

GENERATION = 3

#: The National Dex opens after the Elite Four in all five, and stops at Deoxys.
NATIONAL_DEX_THROUGH = 386

#: Every Generation 3 cartridge that trades with every other over a link cable.
#:
#: Colosseum and XD trade with them as well, but they are not in the plan, so nothing here
#: claims them. A game declares the whole set whether or not the others are built yet: the
#: registry holds an edge back until both ends exist, and adding a cartridge later lights its
#: routes up without anyone editing the games that were already written.
CARTRIDGES = ("ruby", "sapphire", "emerald", "firered", "leafgreen")


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
    """One Generation 3 cartridge, with the facts all five of them share filled in.

    ``pair_partner`` is what separates Ruby from Emerald: the halves of a pair name each other,
    and a third version names nobody.
    """
    return Game(
        id=game_id,
        title=title,
        version=version,
        generation=GENERATION,
        region=region,
        release=GameRelease.CARTRIDGE,
        released=released,
        # The number rather than a yes or no: the dex builder has to know where it stops.
        national_dex_through=NATIONAL_DEX_THROUGH,
        dex_source=DexSource.NATIONAL_DEX,
        pair_partner=pair_partner,
        sprite_set=sprite_set,
    )


def link_trade_edges(game_id: str) -> list[TransferEdge]:
    """What this cartridge can send and receive over a link cable.

    Trading inside a generation goes both ways and carries anything the game can hold, so one
    edge per partner says it all. Both ends may declare the same edge; they collapse into one,
    so neither game has to know whether the other got there first.

    Pal Park into Generation 4 is not here. It is one way, and it belongs to the game that
    receives - that is where the National Dex limit it applies is a fact about the receiver.
    """
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

    A version exclusive is still an entry you have to fill, and the transfer graph is how -
    which is the whole reason the two halves declare a route to each other.

    ``event`` is what step 7 found. It does not change that the cartridge cannot produce one; it
    answers the next question, which is where one could ever have come from.

    Shared by both pairs: a Hoenn exclusive and a Kanto one are the same kind of fact, and the
    sentence a player reads should not depend on which cartridge they happened to buy.
    """
    reason = f"{partner} only in Generation 3; trade one in"

    return f"{reason}. {event[0].upper()}{event[1:]}" if event else reason


def pal_park_edges(*, into: str) -> list[TransferEdge]:
    """Every Generation 3 cartridge migrating into one Generation 4 game.

    Pal Park asks for a Game Pak in the slot and does not care which of the five it is, so all
    five routes exist or none do. Declared by the receiving game rather than by the cartridges:
    the limit the route carries - nothing above 386, because nothing above it existed yet - is a
    fact about what Generation 4 will accept, and the cartridge has no opinion about it.

    One way, and permanently: a Pokemon that has been migrated can never go back.
    """
    return [
        TransferEdge(
            **{"from": cartridge_id},
            to=into,
            mechanism=TransferMechanism.PAL_PARK,
            direction=TransferDirection.ONE_WAY,
            filter=NationalDexRangeFilter(**{"from": 1}, to=NATIONAL_DEX_THROUGH),
        )
        for cartridge_id in CARTRIDGES
    ]
