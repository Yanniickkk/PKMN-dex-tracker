"""Pokemon Silver: everything but the smoke test.

Phase 2 steps 1 to 7 for this game: the 251 entries it asks a player to fill, every wild slot
that fills one across both halves of its map, everything the game hands over or leaves standing
in one spot, what its seven traders will swap for, what evolves into what here, which babies
only the day care brings, the sprite sheet a player of it actually saw, and where the
seventeen entries it cannot produce could ever have come from.

This is the Virtual Console release rather than the 1999 cartridge, and it is the only Silver in
this dataset - see :mod:`vc` for why. Everything it shares with Gold is in
:mod:`johto`, which is about the region rather than the generation: HeartGold and
SoulSilver are set there too.
Everything it shares with Crystal is in :mod:`gbc`. What is left is its name, which game is its
other half, and which version PokeAPI is asked about.
"""

from __future__ import annotations

from datetime import date

from ..games import BuildContext, GameRegistry
from ..models import AcquisitionMethod, DexEntry, GameData, TransferEdge
from . import johto

GAME_ID = "silver"

#: The other half of the pair. Which species that switch decides is step 4's answer, not this
#: step's; all that is claimed here is that the two halves exist and know about each other.
PAIR_PARTNER = "gold"

#: What PokeAPI calls this game when it lists which version an encounter belongs to. It is the
#: whole difference between this file and its partner's.
POKEAPI_VERSION = "silver"

#: The Virtual Console release, worldwide on one day - which the cartridge was not: Japan had it
#: in 1999 and Europe waited until 2001. The entity is the 3DS one, so it is the 2017 date that
#: belongs here.
RELEASED = date(2017, 9, 22)

#: Where this game's own battle sprites live in the sprite repository.
#:
#: Its own, not the pair's, which is the first time in this dataset that a pair has not shared a
#: sheet. Gold and Silver drew all 251 twice over - the Meganium on one screen is not the drawing
#: on the other - so a sheet here belongs to a game rather than to a pair, and Crystal will bring
#: a third.
#:
#: ``transparent`` for the reason Generation 1's sheets give, and checked again rather than
#: assumed: the default Generation 2 sheet is a 40x40 palette image with no alpha chunk, so every
#: sprite would arrive in a white box. The transparent set is 56x56 with a ``tRNS`` chunk - not
#: the 96x96 Generation 1's transparent set gives, which is the reason to keep checking.
SPRITE_SET = "generation-ii/silver/transparent"

#: In the Johto dex and never in this release, and what step 7 found about each.
#:
#: Six, mirroring the other half exactly. Three of them are Johto's own and three are Kanto's,
#: which is what a pair does with a map this size.
#:
#: Worked out *after* the trades, the eggs and the contest of steps 4 and 5 rather than from the
#: encounter tables alone, and every one of those steps took something off this list. Ekans is
#: the Goldenrod Game Corner's here and Sandshrew is the other half's, so neither is a gap;
#: Weedle and Caterpie are both in the Bug-Catching Contest whichever version is playing; and
#: Ariados, Ursaring and Persian evolve from something that comes over the link.
#:
#: Every value is None, the way Red's and Blue's are. Not one of the twelve species the two
#: halves keep from each other was ever handed out for a Virtual Console release: what these
#: have is for the Generation 3 games or later, and the only Generation 2 distributions at all
#: were the Celebis and Mews that went onto cartridges.
ONLY_ON_GOLD: dict[str, str | None] = {
    "growlithe": None,
    "mankey": None,
    "spinarak": None,
    "gligar": None,
    "teddiursa": None,
    "mantine": None,
}

#: Dex entries no amount of playing this release will fill, and why.
#:
#: Seventeen: the six above, and eleven that neither half can produce - three Kanto first
#: partners nobody hands over, two fossils nobody revives, four legendaries standing nowhere in
#: either region, Mew and Celebi.
UNOBTAINABLE: dict[str, str] = {
    **johto.GBC_PAIR_UNOBTAINABLE,
    **{species: johto.gbc_only_on("Gold", event) for species, event in ONLY_ON_GOLD.items()},
}


def build(context: BuildContext) -> GameData:
    entries = dex_entries(context)

    return GameData(
        game=johto.gbc_release(
            game_id=GAME_ID,
            title="Pokémon Silver Version",
            version="Silver",
            released=RELEASED,
            pair_partner=PAIR_PARTNER,
            sprite_set=SPRITE_SET,
        ),
        dex_entries=entries,
        acquisition_methods=acquisition_methods(context, entries),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """The 251 this game asks for, Bulbasaur #001 to Celebi #251.

    National numbering rather than Johto's own, which is not what the region's name for its dex
    would suggest. These games list in the Johto order and print the old numbers beside it, so
    the numbers a player reads are national ones; :mod:`gbc` carries the reasoning.

    Here it is the whole of it. A living dex in this game is 251 tiles, not 251 of something
    larger, because there is no National Dex behind this list to be a part of - this *is* the
    National Dex, as far as these games ever knew it.

    The unobtainable table is what step 7 added: the other half's six, and eleven neither half
    can produce.
    """
    return johto.gbc_dex_entries(context, game_id=GAME_ID, unobtainable=UNOBTAINABLE)


def acquisition_methods(
    context: BuildContext,
    entries: list[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something here: caught, handed over, traded for, evolved or hatched.

    The gift table is the pair's, with one thing picked out per version: which wing the Radio
    Tower Director hands over, and therefore which of the two birds this half meets in the
    middle of its story rather than after the Elite Four. Everything else the two halves share.
    """
    return johto.gbc_acquisition_methods(
        context,
        game_id=GAME_ID,
        version=POKEAPI_VERSION,
        entries=entries,
        gifts=johto.gbc_gifts(POKEAPI_VERSION),
        version_group=johto.GBC_PAIR_VERSION_GROUP,
        trades=johto.GBC_TRADES,
        eggs=johto.GBC_EGGS,
    )


def edges() -> list[TransferEdge]:
    return johto.gbc_edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Silver EN boxart.png")
