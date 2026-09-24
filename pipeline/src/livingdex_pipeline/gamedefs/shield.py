"""Pokemon Shield: what it is, and the three routes it brings.

Phase 2 steps 1 and 2 for this game, and nothing after them yet. What it says about itself is
here; what is true of both halves is in :mod:`galar`.

**The half whose mascot is the one thing it cannot trade for.** Zamazenta is on the box and
Zacian is on the other, and this is the second pair in the series - after Black 2 and White 2 -
whose mascot cannot be had before the Hall of Fame without trading for it. That is a fact about
when rather than whether, so it belongs to step 4 and is written down here so that step does not
have to find it twice.

What is left for this file is its name, that Sword is its other half, which version PokeAPI is
asked about, and three lists it shares with that half entry for entry.
"""

from __future__ import annotations

from ..games import BuildContext, GameRegistry
from ..models import DexEntry, GameData, TransferEdge
from . import galar

GAME_ID = "shield"

#: The other half. Which species that switch decides is step 4's answer; all that is claimed
#: here is that the two halves exist and know about each other.
PAIR_PARTNER = "sword"

#: What PokeAPI calls this game when it lists which version an encounter belongs to.
POKEAPI_VERSION = "shield"


def build(context: BuildContext) -> GameData:
    """The game entity and the three lists it shows. Its other half's file says the rest."""
    entries = dex_entries(context)

    return GameData(
        game=galar.cartridge(
            game_id=GAME_ID,
            title="Pokémon Shield",
            version="Shield",
            pair_partner=PAIR_PARTNER,
        ),
        dex_entries=entries,
        acquisition_methods=galar.acquisition_methods(
            context, game_id=GAME_ID, entries=entries
        ),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """The same 821 entries across the same three lists its other half shows.

    Both halves number them identically. What the two will disagree about is which of the 584
    each can actually produce, and that is steps 3 to 5; step 7 turns whatever is left over into
    a reason on the entry.
    """
    return galar.dex_entries(context, game_id=GAME_ID)


def edges() -> list[TransferEdge]:
    """The cable to Sword, and HOME in both directions.

    The cable is the same edge its other half declares, which is why the pair puts five routes
    into the graph and not six: the two halves make six declarations between them and two of
    them are the one both-ways trade, which the registry holds once.
    """
    return galar.edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Shield EN boxart.png")
