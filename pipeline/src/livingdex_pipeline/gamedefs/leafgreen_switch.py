"""Pokemon LeafGreen on the Nintendo Switch: the cartridge again, with one door instead of another.

Every step of Phase 2 in one file, because every one of them was answered in 2004 and none of
them was asked again. The dex, the grass, the gifts, the traders, the evolutions, the sprites
and the unobtainable list are :mod:`leafgreen`'s, imported rather than retyped: two copies of a
table is how one of them gets corrected and the other does not.

What this module holds is what the re-release changed - its name, the day it was sold, the shelf
it was sold on, and the two routes it has. :mod:`frlg_switch` is where those live for both
halves, and it is also where the reason these are separate entities at all is written down.
"""

from __future__ import annotations

from ..games import BuildContext, GameRegistry
from ..models import AcquisitionMethod, DexEntry, GameData, TransferEdge
from . import frlg_switch, kanto, leafgreen

GAME_ID = "leafgreen-switch"

#: The other half. The Switch one: local wireless reaches another Switch, and a Game Pak is not
#: one. The seven entries this half never grows are still filled from over there, exactly as
#: they are between the cartridges - it is the same trade in a console's radio instead of a
#: cable.
PAIR_PARTNER = "firered-switch"

#: What PokeAPI calls this game, which is what it called it before. The source has one LeafGreen
#: and this is a re-release of it, so asking about `leafgreen` is asking about this.
POKEAPI_VERSION = leafgreen.POKEAPI_VERSION


def build(context: BuildContext) -> GameData:
    entries = dex_entries(context)

    return GameData(
        game=frlg_switch.release(
            game_id=GAME_ID,
            title="Pokémon LeafGreen Version (Nintendo Switch)",
            version="LeafGreen",
            pair_partner=PAIR_PARTNER,
            sprite_set=kanto.GBA_PAIR_SPRITE_SET,
        ),
        dex_entries=entries,
        acquisition_methods=acquisition_methods(context, entries),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """The Kanto dex, and the cartridge's own unobtainable table under it."""
    return kanto.dex_entries(context, game_id=GAME_ID, unobtainable=leafgreen.UNOBTAINABLE)


def acquisition_methods(
    context: BuildContext,
    entries: list[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something here, which is every way there was."""
    return kanto.gba_pair_acquisition_methods(
        context,
        game_id=GAME_ID,
        version=POKEAPI_VERSION,
        entries=entries,
    )


def edges() -> list[TransferEdge]:
    return frlg_switch.edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    # The cover the eShop listing uses is the cover the box had.
    registry.register(GAME_ID, build, edges(), box_art="LeafGreen EN boxart.png")
