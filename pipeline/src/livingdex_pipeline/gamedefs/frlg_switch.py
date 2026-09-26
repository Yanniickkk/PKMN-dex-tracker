"""What the two Nintendo Switch releases of FireRed and LeafGreen share.

The Kanto pair was sold again on 27 February 2026, eShop only, for the series' thirtieth
anniversary. These are those two, and they are entities of their own beside the Game Boy
Advance cartridges rather than instead of them.

**That is the opposite of the Virtual Console answer, and for the reason** :mod:`vc` **gives.**
There, the cartridge is not in the dataset at all: a Game Boy cartridge trades with another
Game Boy cartridge and reaches nothing else, so there was only ever one of the two worth
holding. Here both are worth holding, because both go somewhere. The cartridge migrates through
Pal Park into Generation 4 and from there up the whole chain; the Switch release reaches Pokemon
HOME and nothing else. One game, two ways out, and neither can stand in for the other - which is
what an entity in this dataset is for.

**Everything a player does is copied, because nothing a player does was changed.** The same 151
entries in the same order, the same grass, the same gifts and statics, the same nine traders,
the same sprite sheet, and the same Deoxys forme decided by which half you bought. These modules
ask :mod:`kanto` the same questions the cartridges ask it, with the same PokeAPI version name -
`firered` and `leafgreen` are what the source calls this game whatever it is sold on.

What is not copied is how it was sold, when, and where what is caught in it may go.

**The routes, and they are short.** Two Switch copies talk to each other over the console's own
local wireless, which stands in for both the Game Link Cable and the GBA Wireless Adapter - so
the pair still fills in each other's seven exclusives, exactly as the cartridges do. They reach
nothing else: not the cartridges, not the Nintendo Classics release of Pokemon XD. And from
October 2026, Pokemon HOME - **one way**. What is deposited there can be taken on to any later
game and can never come back.

**The one thing in the game that did change is not visible here, and that is a known question
rather than an oversight.** The Switch releases hand over the MysticTicket and the AuroraTicket
once the Hall of Fame is entered, where the originals only ever gave them out at distribution
events - which makes Lugia, Ho-Oh and Deoxys catchable by anybody who finishes the game. This
dataset already lists all three as ordinary static encounters on the cartridges, from PokeAPI's
location tables, with nothing to say that the boat to Navel Rock or Birth Island needed a ticket
nobody can be given any more. So the copy shows no difference where the real difference is. Ten
records across the five Generation 3 games are in that state, the Old Sea Map's Mew and the Eon
Ticket's pair among them, and correcting them is a decision about those games rather than about
these two.
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
from . import gba, home, kanto

#: The day both halves arrived on the eShop, worldwide and at the same hour.
RELEASED = date(2026, 2, 27)

#: The two of them, which is the whole of what either can trade with.
PAIR = ("firered-switch", "leafgreen-switch")


def release(
    *,
    game_id: str,
    title: str,
    version: str,
    pair_partner: str,
    sprite_set: str | None = None,
) -> Game:
    """One half of the pair as it was sold on the Switch.

    Generation 3 and Kanto, because that is what the game is - a shelf is not a generation. The
    National Dex is the cartridge's, 386 deep and opening after the Elite Four, and the number
    is kept even though far less of it can be reached here: what a game asks of a player is not
    changed by what its console can no longer be plugged into.
    """
    return Game(
        id=game_id,
        title=title,
        version=version,
        generation=gba.GENERATION,
        region=kanto.REGION,
        release=GameRelease.NINTENDO_CLASSICS,
        released=RELEASED,
        national_dex_through=gba.NATIONAL_DEX_THROUGH,
        dex_source=DexSource.NATIONAL_DEX,
        pair_partner=pair_partner,
        sprite_set=sprite_set,
    )


def edges(game_id: str) -> list[TransferEdge]:
    """The other half, and Pokemon HOME.

    The trade is the ordinary both-ways edge a pair has always had, carrying anything either
    half can hold. What is missing beside it is every Generation 3 cartridge: local wireless
    reaches another Switch running this same game and no Game Pak anywhere.

    HOME is one edge and not the two :func:`home.home_edges` gives, because the service only
    takes. Nothing is withdrawn into these games - not what left them, not anything else - so
    the second edge would describe a door that is not there. Legends: Z-A has the mirror image
    of this and for the mirror reason.
    """
    return [
        TransferEdge(
            **{"from": game_id},
            to=partner,
            mechanism=TransferMechanism.TRADE,
            direction=TransferDirection.BOTH_WAYS,
            filter=AllSpeciesFilter(),
        )
        for partner in PAIR
        if partner != game_id
    ] + [
        TransferEdge(
            **{"from": game_id},
            to=home.NODE,
            mechanism=TransferMechanism.HOME,
            direction=TransferDirection.ONE_WAY,
            filter=AllSpeciesFilter(),
        ),
    ]
