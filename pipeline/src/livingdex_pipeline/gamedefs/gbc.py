"""What every Generation 2 game shares, whichever region it is set in.

Gold, Silver and Crystal are all Johto, so this module and :mod:`johto` cover the same three
games today - and they are still two modules, for the reason :mod:`ds` gives. What is here is
the generation: a dex of 251 and no National Dex behind it, three games that trade with each
other, and Poke Transporter out to Bank. What is in the region is Johto's own: its Pokedex, its
towns, its trades.

The Time Capsule is not here, and its absence is deliberate rather than an oversight. It is
declared by :mod:`gb`, from the Generation 1 side, because the limit on it is a fact about
that side: a Game Boy game has nowhere to put a Chikorita. Declaring it here as well would
give the registry the same route twice, and it is the same reasoning that leaves Pal Park with
the Generation 4 game that receives.

Kanto is playable in all three of these and is not a second region for the entity. A Gold
cartridge is a Johto game, as a HeartGold one is.
"""

from __future__ import annotations

from datetime import date

from ..models import AllSpeciesFilter, Game, TransferDirection, TransferEdge, TransferMechanism
from . import bank, exclusives, vc

GENERATION = 2

#: The dex stops at Celebi, and it is the game's own list rather than a National Dex: these
#: games have one Pokedex and it holds everything there was.
DEX_THROUGH = 251

#: PokeAPI's name for the list these games number by, which is the National Dex and not Johto's.
#:
#: Johto has a regional order - PokeAPI calls it ``original-johto``, and it starts at Chikorita -
#: and these games do list in it: the Pokedex opens in New Pokedex Mode, with the Johto first
#: partners at the front. But Bulbapedia is explicit that the New Pokedex numbers are shown
#: nowhere in the games. What is printed beside a Pokemon is the old number, so a Gold player
#: reads Chikorita as #152 and Bulbasaur as #001, and switching to Old Pokedex Mode reorders the
#: list to match.
#:
#: A dex entry here carries one number, and it is the one on the screen. So this dataset numbers
#: these games nationally, and the Johto order they happen to list in is not recorded - there is
#: no field for "listed like this, numbered like that", and inventing one would buy nothing a
#: player can see.
#:
#: HeartGold and SoulSilver are the other way round: their regional numbers *are* what the game
#: shows, so they carry ``updated-johto`` and its renumbering.
DEX = "national"

#: Every Generation 2 release that trades with every other.
#:
#: Three again, and the shape is Generation 1's exactly: a pair and a third version that trades
#: with both. What is missing is Green's counterpart - there is none, because the third version
#: here came out everywhere.
RELEASES = ("gold", "silver", "crystal")

#: The Generation 1 releases each of these opens a Time Capsule with. Named here because a
#: reader of this module will look for it, and the edges themselves belong to :mod:`gb`.
GEN_1_RELEASES = ("red", "blue", "yellow")

#: What these three games call a place PokeAPI names after a later one.
#:
#: PokeAPI keeps one name per location and it is the newest game's, which is right nearly
#: everywhere and wrong where a place was renamed. Ho-Oh waits on the roof of the Bell Tower in
#: HeartGold and on the roof of the Tin Tower here, and a Gold player reading "Bell Tower" is
#: being told the name of a game they are not playing.
#:
#: One entry, after reading all 83 places these two games use. The rest of Johto kept its name
#: into Generation 4 - Sprout Tower, the Burned Tower, the Ruins of Alph, Tohjo Falls - and
#: Kanto's half is the same list Red and Blue used. Anything found later goes here beside it,
#: and Crystal gets whatever is here for nothing, because it calls them what these two do.
#:
#: Keyed by PokeAPI's name rather than by the slug: it is the name that gets written down, and
#: a table that reads ``{"Bell Tower": "Tin Tower"}`` says what it does without a lookup.
RENAMED_PLACES = {"Bell Tower": "Tin Tower"}


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
    """One Generation 2 release, with the facts all three of them share filled in."""
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
    """What this release trades with: every other Generation 2 release, both ways.

    Not the Generation 1 ones. Those take the Time Capsule, which is a different mechanism with
    a different limit, and it is declared on the other side.
    """
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


def edges(game_id: str) -> list[TransferEdge]:
    """Every route one Generation 2 release brings: its own trades, and Bank.

    Both kinds together, for the reason :mod:`gb` gives: a game that declares its routes in two
    places grows one of them and not the other.
    """
    return [*link_trade_edges(game_id), bank.transporter_edge(game_id)]


def only_on(partner: str, event: str | None = None) -> str:
    """Why an entry in this dex is not in this release, when the other half has it."""
    return exclusives.only_on(partner, generation=GENERATION, event=event)
