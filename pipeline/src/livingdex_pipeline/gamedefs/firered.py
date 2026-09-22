"""Pokemon FireRed: entity, edges, dex, wild encounters, gifts and statics.

Phase 2 steps 1 to 4 for this game. Trades, evolutions and sprites are later steps; what is here
is the 151 entries it asks a player to fill, every wild slot that fills one, and everything the
game hands over or leaves standing in a corner.

Everything it shares with LeafGreen is in :mod:`kanto`, the dex included - the two of them
number those 151 entries identically. Everything it shares with the Hoenn cartridges is in
:mod:`gba`. What is left is its name, which cartridge is its other half, and which version
PokeAPI is asked about.
"""

from __future__ import annotations

from datetime import date

from ..games import BuildContext, GameRegistry
from ..models import AcquisitionMethod, DexEntry, GameData, TransferEdge
from . import kanto

GAME_ID = "firered"

#: The other half of the pair. Which species that switch decides is step 4's answer, not this
#: step's; all that is claimed here is that the two halves exist and know about each other.
PAIR_PARTNER = "leafgreen"

#: What PokeAPI calls this game when it lists which version an encounter belongs to. It is the
#: whole difference between this file and its partner's.
POKEAPI_VERSION = "firered"

#: In the Kanto dex and never in this cartridge, and what step 7 found about each.
#:
#: Seven, mirroring the other half exactly - which is what a version pair is. They are still
#: entries to fill, and the link cable between the two halves is how.
#:
#: Worked out *after* the trades and evolutions of step 5 rather than from the encounter tables
#: alone, deliberately. Doing it the other way round is what once put Banette on Ruby's list and
#: Dusclops on Sapphire's: both are caught nowhere, both evolve from something the cartridge has,
#: and reading only the grass could not tell the difference.
#: The value is the event that handed one out, where there was one. Pinsir is the only one of
#: the fourteen exclusives across the pair that no Generation 3 distribution ever covered.
ONLY_ON_LEAFGREEN: dict[str, str | None] = {
    "sandshrew": kanto.handed_out(kanto.TRADE_AND_BATTLE_DAY),
    "vulpix": kanto.handed_out(kanto.TRADE_AND_BATTLE_DAY),
    "bellsprout": kanto.handed_out(kanto.EGG_PRESENT, kanto.THIRD_CAMPAIGN),
    "slowpoke": kanto.handed_out(kanto.TRADE_AND_BATTLE_DAY, kanto.THIRD_CAMPAIGN),
    "staryu": kanto.handed_out(kanto.TRADE_AND_BATTLE_DAY),
    "magmar": kanto.handed_out(kanto.THIRD_CAMPAIGN),
    "pinsir": None,
}

#: Dex entries no amount of playing this cartridge will fill, and why.
#:
#: A reason rather than a gap: the validator can tell "we checked and it cannot be caught" from
#: "we have not gathered this yet", and only the second is a fault.
UNOBTAINABLE: dict[str, str] = {
    "mew": kanto.GBA_MEW_REASON,
    **{
        species: kanto.gba_only_on("LeafGreen", event)
        for species, event in ONLY_ON_LEAFGREEN.items()
    },
}


def build(context: BuildContext) -> GameData:
    entries = dex_entries(context)

    return GameData(
        game=kanto.gba_cartridge(
            game_id=GAME_ID,
            title="Pokémon FireRed Version",
            version="FireRed",
            released=date(2004, 1, 29),
            pair_partner=PAIR_PARTNER,
            sprite_set=kanto.GBA_PAIR_SPRITE_SET,
        ),
        dex_entries=entries,
        acquisition_methods=acquisition_methods(context, entries),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """The Kanto dex, the same 151 entries and numbering both halves show.

    The unobtainable table is what step 5 added: the seven the other half keeps, and the one
    nothing in any Generation 3 game produces.
    """
    return kanto.dex_entries(context, game_id=GAME_ID, unobtainable=UNOBTAINABLE)


def acquisition_methods(
    context: BuildContext,
    entries: list[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something here. At this step: caught in the wild, or handed over."""
    return kanto.gba_pair_acquisition_methods(
        context,
        game_id=GAME_ID,
        version=POKEAPI_VERSION,
        entries=entries,
    )


def edges() -> list[TransferEdge]:
    return kanto.gba_edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="FireRed EN boxart.png")
