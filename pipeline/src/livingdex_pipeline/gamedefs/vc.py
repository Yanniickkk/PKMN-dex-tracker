"""What every Virtual Console release shares.

Generations 1 and 2 are in this dataset as their 3DS Virtual Console releases and not as the
cartridges they were in 1996. That is a decision about what this tracker is for rather than
about what is true: a Game Boy cartridge trades with another Game Boy cartridge and reaches
nothing else, so a Pokemon caught on one can never join a living dex kept anywhere later. The
Virtual Console releases can, through Poke Transporter into Pokemon Bank, and that one route is
the whole reason they are here.

So there is no ``red-vc`` beside a ``red``. There is one Red, it is the 3DS one, and its
release says so. A file that needs to know which it is asks the entity rather than the id.

What each generation brings of its own - how far its dex reaches, which games trade with which,
whether there is a Time Capsule - stays with that generation.
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

#: The transfer graph's node for Pokemon Bank. Not a game, and not written yet: every release
#: here declares the route to it and the registry holds each one back until the node exists.
BANK = "bank"


def release(
    *,
    game_id: str,
    title: str,
    version: str,
    generation: int,
    region: str,
    released: date,
    dex_through: int,
    pair_partner: str | None = None,
    sprite_set: str | None = None,
) -> Game:
    """One Virtual Console release.

    ``released`` is the date the 3DS release came out rather than the cartridge's, because that
    is what this entity is. Red is 1996 and 2016 both, and only one of those is the thing a
    player can still buy and transfer out of.

    ``dex_through`` is how far the game's own Pokedex reaches, and it is not a National Dex:
    Generations 1 and 2 have only the one list. The entity says so, and a living dex in these
    games is that list and nothing more.
    """
    return Game(
        id=game_id,
        title=title,
        version=version,
        generation=generation,
        region=region,
        release=GameRelease.VIRTUAL_CONSOLE,
        released=released,
        # The first games in this dataset with no National Dex. `national_dex_through` is the
        # number a living dex here aims at, and for these it is the game's own dex - which the
        # dex builder reads from the entries instead.
        national_dex_through=None,
        dex_source=DexSource.GAME_DEX,
        pair_partner=pair_partner,
        sprite_set=sprite_set,
    )


def transporter_edge(game_id: str) -> TransferEdge:
    """Poke Transporter into Pokemon Bank: the route these releases exist for.

    One way, and permanently. The filter is everything the game can hold, because Transporter
    does not choose: what it refuses is a Pokemon holding an item or one that knows an HM move,
    and neither of those is a species.
    """
    return TransferEdge(
        **{"from": game_id},
        to=BANK,
        mechanism=TransferMechanism.POKE_TRANSPORTER,
        direction=TransferDirection.ONE_WAY,
        filter=AllSpeciesFilter(),
    )
