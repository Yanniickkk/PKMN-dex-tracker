"""Pokemon: Let's Go, Pikachu!: what it is, and the three routes it brings.

Phase 2 steps 1 and 2 for this game and nothing after them yet. What it says about itself is
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

#: The other half. Unlike every pair since Red and Blue, what the two halves split is not the
#: question step 4 usually answers: Bulbapedia lists these as the first core games "to not
#: feature mutually exclusive Pokemon", because every version exclusive here can also be had
#: from an NPC in the other half, over and over. Whether that holds for all of them is step 5's
#: to check; all that is claimed here is that the two halves exist and know about each other.
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
    return GameData(
        game=lets_go.cartridge(
            game_id=GAME_ID,
            title="Pokémon: Let's Go, Pikachu!",
            version="Let's Go, Pikachu!",
            pair_partner=PAIR_PARTNER,
        ),
        dex_entries=dex_entries(context),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """Kanto's 151 in the order they have been in since 1996, and two that are not Kanto's.

    No ``unobtainable`` table yet. What this half cannot produce is step 4's question and step
    7's answer, and there is reason to think the list will be short in a way no pair before it
    managed: Bulbapedia calls these the first core games with no mutually exclusive Pokemon,
    because every version exclusive can also be had from an NPC in the other half over and over.
    Passing an empty table here rather than guessing is the same choice :mod:`alola` makes about
    a step that has not run.
    """
    return lets_go.dex_entries(context, game_id=GAME_ID)


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
