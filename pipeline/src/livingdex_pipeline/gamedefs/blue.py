"""Pokemon Blue: everything but the smoke test.

Phase 2 steps 1 to 7 for this game: the 151 entries it asks a player to fill, every wild slot
that fills one, everything the game hands over or leaves standing in a corner, what its nine
traders will swap for, what evolves into what here, the sprite sheet a player of it actually
saw, and where the seven entries it cannot produce could ever have come from.

This is the Virtual Console release rather than the 1996 cartridge, and it is the only Blue in
this dataset - see :mod:`vc` for why. Everything it shares with Red is in :mod:`kanto`, which
is about the region rather than the generation: FireRed and LeafGreen are set there too.
Everything it shares with Yellow is in :mod:`gb`. What is left is its name, which game is its
other half, and which version PokeAPI is asked about.
"""

from __future__ import annotations

from datetime import date

from ..games import BuildContext, GameRegistry
from ..models import AcquisitionMethod, DexEntry, GameData, TransferEdge
from . import kanto

GAME_ID = "blue"

#: The other half of the pair. Which species that switch decides is step 4's answer, not this
#: step's; all that is claimed here is that the two halves exist and know about each other.
PAIR_PARTNER = "red"

#: What PokeAPI calls this game when it lists which version an encounter belongs to. It is the
#: whole difference between this file and its partner's.
POKEAPI_VERSION = "blue"

#: The Virtual Console release, worldwide on the same day. The cartridge is 1996 and is not what
#: this entity is: what a player can still buy and still transfer out of is this one.
RELEASED = date(2016, 2, 27)


#: In the Kanto dex and never in this release, and what step 7 found about each.
#:
#: Six, mirroring the other half exactly - which is what a version pair is. They are still
#: entries to fill, and the link between the two halves is how.
#:
#: Worked out *after* the trades and evolutions of step 5 rather than from the encounter tables
#: alone, deliberately. Sandslash is caught nowhere here either, but it evolves from a Sandshrew
#: that comes over the link, so it is not on this list - the distinction that once put Banette
#: on Ruby's list.
#:
#: Every value is None, and this time the emptiness is almost structural. Not one of the twelve
#: species the two halves keep from each other was ever distributed for a Virtual Console
#: release; what they have is for Gold and Silver, for the Generation 3 games, or for later
#: ones still. Only Mew ever got a Virtual Console distribution at all.
ONLY_ON_RED: dict[str, str | None] = {
    "ekans": None,
    "oddish": None,
    "mankey": None,
    "growlithe": None,
    "scyther": None,
    "electabuzz": None,
}

#: Dex entries no amount of playing this release will fill, and why.
#:
#: A reason rather than a gap: the validator can tell "we checked and it cannot be caught" from
#: "we have not gathered this yet", and only the second is a fault.
UNOBTAINABLE: dict[str, str] = {
    "mew": kanto.GB_MEW_REASON,
    **{species: kanto.gb_only_on("Red", event) for species, event in ONLY_ON_RED.items()},
}


def build(context: BuildContext) -> GameData:
    entries = dex_entries(context)

    return GameData(
        game=kanto.gb_release(
            game_id=GAME_ID,
            title="Pokémon Blue Version",
            version="Blue",
            released=RELEASED,
            pair_partner=PAIR_PARTNER,
            sprite_set=kanto.GB_PAIR_SPRITE_SET,
        ),
        dex_entries=entries,
        acquisition_methods=acquisition_methods(context, entries),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """The Kanto dex, the same 151 entries and numbering all four Kanto games show.

    Here it is the whole of it. A living dex in Blue is 151 tiles, not 151 of something
    larger, because there is no National Dex in this generation to be a part of.

    The unobtainable table is what step 7 added: the other half's six exclusives, and Mew.
    """
    return kanto.dex_entries(context, game_id=GAME_ID, unobtainable=UNOBTAINABLE)


def acquisition_methods(
    context: BuildContext,
    entries: list[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something here: caught, handed over, traded for or evolved."""
    return kanto.gb_pair_acquisition_methods(
        context,
        game_id=GAME_ID,
        version=POKEAPI_VERSION,
        entries=entries,
    )


def edges() -> list[TransferEdge]:
    return kanto.gb_edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Blue EN boxart.png")
