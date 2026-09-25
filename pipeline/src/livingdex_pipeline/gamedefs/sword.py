"""Pokemon Sword: what it is, and the three routes it brings.

Phase 2 steps 1 and 2 for this game, and nothing after them yet. What it says about itself is
here; what is true of both halves - Galar, the Expansion Pass and the way out - is in
:mod:`galar`.

**The half that splits more than its Pokemon.** Every pair since Red and Blue has divided a
list of species between its two halves and left the rest of the game alone. These two divide
the Gym Challenge as well: Bea fights out of Stow-on-Side here and Allister haunts it in the
other half, Gordie holds Circhester where Shield has Melony, and Bulbapedia counts version
exclusive Gym Badges among this pair's firsts. The Isle of Armor goes on to give each half its
own rival - Klara here, Avery there. None of that reaches a living dex; what does is the teams
those people bring, and that is steps 3 and 4.

What is left for this file is its name, that Shield is its other half, which version PokeAPI is
asked about, and three lists it shares with that half entry for entry.
"""

from __future__ import annotations

from ..games import BuildContext, GameRegistry
from ..models import DexEntry, GameData, TransferEdge
from . import galar

GAME_ID = "sword"

#: The other half. Which species that switch decides is step 4's answer; all that is claimed
#: here is that the two halves exist and know about each other.
PAIR_PARTNER = "shield"

#: What PokeAPI calls this game when it lists which version an encounter belongs to.
POKEAPI_VERSION = "sword"


def build(context: BuildContext) -> GameData:
    """The game entity and the three lists it shows. How any of it is filled is steps 3 onwards.

    The validator reports one error against this game until step 3 runs -
    ``every-entry-has-a-method``, saying its encounters have not been gathered yet - and that is
    the state the rule was written for rather than a fault to be worked around.
    """
    entries = dex_entries(context)

    return GameData(
        game=galar.cartridge(
            game_id=GAME_ID,
            title="Pokémon Sword",
            version="Sword",
            pair_partner=PAIR_PARTNER,
        ),
        dex_entries=entries,
        acquisition_methods=galar.acquisition_methods(
            context, game_id=GAME_ID, entries=entries
        ),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """Galar's 400, the Isle of Armor's 211 and the Crown Tundra's 210, as this game numbers them.

    The same three lists Shield shows, with the same numbers, which is what a version pair has
    always meant: the halves split what can be caught rather than what is listed. No
    ``unobtainable`` table yet - which entries this cartridge can never fill is what steps 3 to 7
    find out, and guessing at it now would be claiming to have looked.
    """
    return galar.dex_entries(
        context, game_id=GAME_ID, unobtainable=galar.unobtainable_in(GAME_ID)
    )


def edges() -> list[TransferEdge]:
    """The cable to Shield, and HOME in both directions.

    Registering this game lights nothing that was waiting, and :func:`galar.edges` says why that
    is the expected answer rather than a gap: HOME is the only door into Generation 8, and every
    older game that can reach this one was already reaching HOME.
    """
    return galar.edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Sword EN boxart.png")
