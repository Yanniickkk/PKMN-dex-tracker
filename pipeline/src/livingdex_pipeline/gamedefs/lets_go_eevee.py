"""Pokemon: Let's Go, Eevee!: what it is, and the three routes it brings.

Phase 2 steps 1 and 2 for this game and nothing after them yet. What it says about itself is
here; what is true of both halves is in :mod:`lets_go`.

**The half with no game behind it.** Its other half remakes Yellow, and this one remakes a game
that was never made: Bulbapedia calls it the first remake "whose title is not a longer version
of the remade game title in any language", which is a careful way of saying there was no
Pokemon Eevee to remake. The premise was built a second time around a different partner, and
that is the only difference between the two halves that reaches the data - a starter, the moves
it alone learns, and the handful of species each half's NPCs hand over.

What is left for this file is its name, that Let's Go, Pikachu! is its other half, which version
PokeAPI is asked about, and the same note about a starter that cannot leave.
"""

from __future__ import annotations

from ..games import BuildContext, GameRegistry
from ..models import DexEntry, GameData, TransferEdge
from . import lets_go

GAME_ID = "lets-go-eevee"

#: The other half. What the two of them split is step 4's and step 5's answer, and the answer
#: may well be "nothing that cannot also be traded for": these are the first core games
#: Bulbapedia calls free of mutually exclusive Pokemon.
PAIR_PARTNER = "lets-go-pikachu"

#: What PokeAPI calls this game when it lists which version an encounter belongs to.
POKEAPI_VERSION = "lets-go-eevee"


def build(context: BuildContext) -> GameData:
    """The game entity and the list it shows. How any of it is filled is steps 3 onwards.

    The partner Eevee is this half's one Pokemon that goes nowhere: not to the other half by
    cable, not into HOME. Its eight evolutions are a separate matter and step 5's - the partner
    cannot evolve at all, which is a fact about the form rather than about the family.
    """
    return GameData(
        game=lets_go.cartridge(
            game_id=GAME_ID,
            title="Pokémon: Let's Go, Eevee!",
            version="Let's Go, Eevee!",
            pair_partner=PAIR_PARTNER,
        ),
        dex_entries=dex_entries(context),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """The same 153 its other half shows, which is the whole of what the two agree about.

    Both halves number the list identically, so this is :func:`lets_go.dex_entries` with a game
    id and nothing else. What will eventually differ is the ``unobtainable`` table, and steps 4
    and 7 are what fill it.
    """
    return lets_go.dex_entries(context, game_id=GAME_ID)


def edges() -> list[TransferEdge]:
    """The cable to Let's Go, Pikachu!, and HOME in both directions.

    The cable is the same edge its other half declares, which is why the pair puts five routes
    into the graph and not six: the two halves make six declarations between them and two of
    them are the one both-ways trade, which the registry holds once.
    """
    return lets_go.edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Lets Go Eevee EN boxart.png")
