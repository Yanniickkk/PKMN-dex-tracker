"""What every Generation 6 cartridge shares, whichever region it is set in.

X and Y are Kalos; Omega Ruby and Alpha Sapphire are Hoenn again, twelve years on. So the seam
:mod:`ds` describes is back after a generation that had nothing on either side of it: what is
true of the hardware and the generation lives here, and what a player would call the game - its
Pokedex, its towns, its day care, its trades - stays with the region.

Named for the generation rather than for the machine, which every module before :mod:`unova`
was. The machine is the 3DS, and the 3DS carries three sets of games that share nothing else:
Generation 6, Generation 7, and the Virtual Console releases of Generations 1 and 2. They have
different dexes, different trade sets and different routes out, so a file called ``n3ds`` would
have to say "except in Sun and Moon" about nearly everything in it. :mod:`unova` predicted this:
the pattern of naming a generation after its console stops when the console outlives the
generation.

What is new here is the way out. Every generation so far ended at a cartridge - Pal Park, the
Poke Transfer, Poke Transporter, each one way and each landing somewhere a player still had to
own. These four talk to Pokemon Bank themselves, in both directions, and that is the first time
in this dataset a living dex can be kept somewhere that is not a game. Not symmetrically: Bank
takes anything these games hold and hands back only what has never been outside Generations 3
to 6, which is why the route out and the route back are two edges here.
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
from . import bank, exclusives

GENERATION = 6

#: The National Dex of this generation stops at Volcanion.
#:
#: Seventy-two more than Generation 5, and the smallest step the series has taken. What the
#: number does not say is that three of those seventy-two - Diancie, Hoopa and Volcanion - are
#: in the dex and were never in the games: they have a slot, a number and no way in but an
#: event. Step 7 is where that is written down.
NATIONAL_DEX_THROUGH = 721

#: Every Generation 6 cartridge that trades with every other.
#:
#: All four, freely and in every direction. The Player Search System, the GTS and Wonder Trade
#: are one network across the generation, and Omega Ruby trades with X as easily as with Alpha
#: Sapphire. A game declares the whole set whether or not the others are built yet: the registry
#: holds an edge back until both ends exist.
CARTRIDGES = ("x", "y", "omega-ruby", "alpha-sapphire")


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
    """One Generation 6 cartridge, with the facts all four of them share filled in."""
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
    """What this cartridge trades with, both ways and carrying anything it can hold.

    Only its own generation, as Generation 5's did. Backwards there is nothing at all: no
    cartridge of any earlier generation can be plugged into a 3DS beside this one, and what
    stands where Pal Park and the Poke Transfer stood is Bank, which is not a game.
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


def edges(game_id: str) -> list[TransferEdge]:
    """Every route one Generation 6 cartridge brings: its trades, and Bank both ways.

    Two kinds and not three. Every generation since the third has had something carrying the
    one before it forward, declared by the game that receives; this one has no such thing,
    because what carries Generation 5 forward is Poke Transporter into Bank and Bank is the
    thing these games talk to. A Pokemon caught in Black reaches X by being transported into
    Bank and withdrawn here - two routes, both already written, and neither of them between two
    cartridges.

    Bank is two edges rather than one, because the deposit and the withdrawal do not agree.
    These four cartridges will take back anything whose history is Generations 3 to 6 and
    nothing else, so a Pokemon out of a Virtual Console Gold reaches Bank and stops there as far
    as this generation is concerned. The window is Bank's own fact and is written in its file.

    Both kinds together for the reason :mod:`gb` gives: a game that declares its routes in two
    places grows one of them and not the other.
    """
    return [
        *link_trade_edges(game_id),
        *bank.bank_edges(game_id, withdrawal=bank.GENERATION_6_WITHDRAWAL),
    ]


def only_on(partner: str, event: str | None = None) -> str:
    """Why an entry in this dex is not in this cartridge, when the other half has it.

    The same sentence every generation before this uses, with this one's number in it.
    """
    return exclusives.only_on(partner, generation=GENERATION, event=event)
