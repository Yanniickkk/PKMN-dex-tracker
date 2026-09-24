"""Pokemon: Let's Go, Pikachu!: what it is, and the three routes it brings.

Phase 2 steps 1 to 3 for this game and nothing after them yet. What it says about itself is
here; what is true of both halves is in :mod:`lets_go`, and what turns out to be true of Kanto
rather than of these two will move to :mod:`kanto` as the steps that find it run.

**A remake of Yellow, which is a remake nothing else in the series is.** Red, Blue, Gold,
Silver, Ruby and Sapphire have all been remade; a third version never had been. The Japanese
title says it exactly - ``Pocket Monsters: Let's Go! Pikachu`` is ``Pocket Monsters: Pikachu``
with two words in front of it - and the partner on the shoulder that Yellow invented is the
whole premise rather than a detail.

What is left for this file is its name, that Let's Go, Eevee! is its other half, which version
PokeAPI is asked about, and a note about a starter that cannot leave.
"""

from __future__ import annotations

from ..games import BuildContext, GameRegistry
from ..models import DexEntry, GameData, TransferEdge
from . import lets_go

GAME_ID = "lets-go-pikachu"

#: The other half, and the only thing this game can reach by cable.
#:
#: What the two halves split is six lines each way - :data:`lets_go.ONLY_ON` - which is the
#: smallest split a Kanto pair has had and an ordinary one. Step 1 guessed otherwise, from
#: Bulbapedia's line about these being the first core games "to not feature mutually exclusive
#: Pokemon": it read that as every version exclusive being available from an NPC in the other
#: half, and step 5 found that the traders hand over Alolan forms and nothing else. Mutually
#: exclusive is about one save file rather than two cartridges, and what earns these two the
#: line is that both Hitmons are rare spawns on Victory Road and both fossils turn up again in
#: Cerulean Cave. The choices went; the version exclusives did not.
PAIR_PARTNER = "lets-go-eevee"

#: What PokeAPI calls this game when it lists which version an encounter belongs to.
POKEAPI_VERSION = "lets-go-pikachu"


def build(context: BuildContext) -> GameData:
    """The game entity and the list it shows. How any of it is filled is steps 3 onwards.

    The partner Pikachu is the one Pokemon in this game that goes nowhere: it cannot be traded
    to the other half and cannot be put into HOME, which no starter before it could say. That is
    a fact about a form rather than about the game, so it waits for step 8 - it is written down
    twice here and in :func:`lets_go.trade_edges` so that whoever reaches either does not have
    to rediscover it.
    """
    entries = dex_entries(context)

    return GameData(
        game=lets_go.cartridge(
            game_id=GAME_ID,
            title="Pokémon: Let's Go, Pikachu!",
            version="Let's Go, Pikachu!",
            pair_partner=PAIR_PARTNER,
        ),
        dex_entries=entries,
        acquisition_methods=lets_go.acquisition_methods(
            context, game_id=GAME_ID, version=POKEAPI_VERSION, entries=entries
        ),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """Kanto's 151 in the order they have been in since 1996, and two that are not Kanto's.

    The ``unobtainable`` table is :data:`lets_go.UNOBTAINABLE`, shared with the other half, and
    step 4 found it as short as this game's own file guessed it would be - three of 153, and not
    one of them a version exclusive. Bulbapedia calls these the first core games with no
    mutually exclusive Pokemon and the gifts keep to it; what is left is a Mew behind a
    controller and the two species only the GO Park can bring.
    """
    return lets_go.dex_entries(
        context, game_id=GAME_ID, unobtainable=lets_go.unobtainable_in(GAME_ID)
    )


def edges() -> list[TransferEdge]:
    """The cable to Let's Go, Eevee!, and HOME in both directions.

    Registering this game lights nothing that was waiting: no game in the dataset has ever
    declared a route into it, because none of them has one. The two HOME edges are the first in
    the dataset that HOME does not hand back on its own terms, and the second of them carries
    the origin that :mod:`lets_go` explains.
    """
    return lets_go.edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Lets Go Pikachu EN boxart.png")
