"""Babies from the day care.

Pichu, Igglybuff and Azurill are in Emerald's dex and there is no way to meet one: they hatch
from an egg the day care hands over, and nothing else in the game produces them. That is not a
gift, not a wild slot, not an evolution and not a trade, so it is its own kind rather than one
of the four bent to fit.

Like in-game trades, no API carries it. Which parent lays which baby is a fact about a
generation more than about a game - the incense a Generation IV parent has to hold is the sort
of thing that changes, so a game says it rather than this module assuming it - and the table
lives in the game's own file.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .models import BreedingAcquisition, DexTarget, SourceCitation


@dataclass(frozen=True)
class EggFrom:
    """What has to be in the day care for one baby to turn up."""

    #: Any one of these works. A Pichu hatches from a Pikachu or from a Raichu, and naming only
    #: the first would make the other look like a way that does not exist.
    parents: Sequence[str]
    #: What else has to be true - the incense a Generation IV parent has to hold, say.
    requirement: str | None = None


def breeding_encounters(
    *,
    game_id: str,
    day_care: str,
    eggs: Mapping[str, EggFrom],
    citation: SourceCitation,
) -> list[BreedingAcquisition]:
    """One record per baby, in the order the game's table lists them."""
    return [
        BreedingAcquisition(
            game=game_id,
            target=DexTarget(species=baby),
            parents=[DexTarget(species=parent) for parent in egg.parents],
            location=day_care,
            requirement=egg.requirement,
            source=citation,
        )
        for baby, egg in eggs.items()
    ]
