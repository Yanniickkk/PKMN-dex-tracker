"""Pokemon Brilliant Diamond: what it is, and the three routes it brings.

Phase 2 steps 1 to 7 for this game, and nothing after them yet. What it says about itself is
here; what is true of both halves - Sinnoh on a Switch, and the way out - is in :mod:`bdsp`.

Diamond is in this dataset already, and this is not that entity with a newer date on it. It is
a different game: a different studio built it, it is Generation 8 rather than 4, its way out is
HOME rather than a link cable and Pal Park, and the Pokemon it contains are not quite the same
set. Two entities, the way the cartridge Crystal and the Virtual Console Crystal would have been
if that decision had gone the other way - except that here both are real and both are held.

What is left for this file is its name, that Shining Pearl is its other half, and which version
PokeAPI is asked about.
"""

from __future__ import annotations

from ..games import BuildContext, GameRegistry
from ..models import DexEntry, GameData, TransferEdge
from . import bdsp

GAME_ID = "brilliant-diamond"

#: The other half. Which species that switch decides is step 4's answer; all that is claimed
#: here is that the two halves exist and know about each other.
PAIR_PARTNER = "shining-pearl"

#: What PokeAPI calls this game when it lists which version an encounter belongs to.
#:
#: It will not be asked about encounters: the source has none for this game, which is what the
#: reading before Generation 8's remaining games found. It still names the version for
#: everything else that is asked by version.
POKEAPI_VERSION = "brilliant-diamond"


def build(context: BuildContext) -> GameData:
    """The game entity, the 151 it shows, and every wild slot that fills one.

    The validator reports one error against this game until step 3 runs -
    ``every-entry-has-a-method``, saying its encounters have not been gathered yet - and that is
    the state the rule was written for rather than a fault to be worked around.
    """
    entries = dex_entries(context)

    return GameData(
        game=bdsp.cartridge(
            game_id=GAME_ID,
            title="Pokémon Brilliant Diamond",
            version="Brilliant Diamond",
            pair_partner=PAIR_PARTNER,
        ),
        dex_entries=entries,
        acquisition_methods=bdsp.acquisition_methods(
            context, game_id=GAME_ID, entries=entries
        ),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """The Sinnoh dex as this game numbers it: Turtwig #001 to Manaphy #151.

    The same 151 in the same order that Shining Pearl shows, which is what a version pair has
    always meant - the halves split what can be *caught*, not what is listed. No
    Five of them this half can never fill, which is what step 7 added: the four the other
    half keeps, and the one nothing in either produces.
    """
    return bdsp.dex_entries(
        context, game_id=GAME_ID, unobtainable=bdsp.unobtainable_in(GAME_ID)
    )


def edges() -> list[TransferEdge]:
    """The cable to Shining Pearl, and HOME in both directions.

    Registering this game lights nothing that was waiting, and that is the expected answer
    rather than a gap for the same reason it was with Sword: HOME is the only door Generation 8
    has, and every older game that can reach this one was already reaching HOME.
    """
    return bdsp.edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Brilliant Diamond EN boxart.png")
