"""Gifts and statics for one game, from PokeAPI.

Step 4 is everything handed to you or waiting for you: the starter, the revived fossil, the egg
in someone's arms, the legendary asleep at the end of a cave. PokeAPI files all of it under the
same encounter tables as the wild slots, so the fetching is the same work with different methods
taken out of it.

What PokeAPI knows is the method, the place and the level. What it does not know is *who* hands
it over, what you have to have done first, and whether a "gift" is a starter, a fossil or a
present from a stranger - `gift` is one word for all three. Those are facts about one game, so
they come from that game's own file as a table of :class:`GiftDetail`, and this module only
puts the two halves together.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

from .models import DexTarget, GiftAcquisition, GiftKind, SourceCitation
from .places import LocationNames, pretty
from .pokeapi import BASE_URL, PokeApiClient

log = logging.getLogger(__name__)

#: PokeAPI's encounter methods that are a gift or a static, and what this project calls them.
#:
#: ``gift`` covers starters, fossils and presents alike, so it lands on the most general of the
#: three; a game that knows better says so in its own table.
GIFT_METHODS: dict[str, GiftKind] = {
    "gift": GiftKind.NPC_GIFT,
    "gift-egg": GiftKind.EGG,
    "static": GiftKind.STATIC_ENCOUNTER,
    # One Pokemon standing in one spot, which is a static encounter however you reveal it. The
    # item it takes to see it comes through as a condition.
    "devon-scope": GiftKind.STATIC_ENCOUNTER,
    "squirt-bottle": GiftKind.STATIC_ENCOUNTER,
    "wailmer-pail": GiftKind.STATIC_ENCOUNTER,
    "pokeflute": GiftKind.STATIC_ENCOUNTER,
}

#: Methods that are a distribution event rather than anything in the game. Skipped with a word,
#: because "you had to be at a shop in Japan in 2003" is not a way to fill a dex today.
EVENT_METHODS = frozenset(
    {
        "colosseum-bonus-disc-jpn",
        "colosseum-bonus-disc-int",
        "event",
    }
)

#: Conditions that name an item you must be carrying or have chosen.
_ITEM = "item-"


@dataclass(frozen=True)
class GiftDetail:
    """What a game knows about one of its gifts that PokeAPI cannot say.

    Every field is optional: a game that has nothing to add about a static leaves it out of the
    table entirely and the record still carries its place and level.
    """

    #: Overrides what the method alone suggests - a starter and a fossil are both `gift`.
    kind: GiftKind | None = None
    #: Who hands it over, when someone does.
    npc: str | None = None
    #: What has to be true first. Replaces the item read off the encounter's conditions.
    requirement: str | None = None


def gift_encounters(
    api: PokeApiClient,
    *,
    game_id: str,
    version: str,
    species: list[str],
    retrieved_on: date,
    details: Mapping[str, GiftDetail] | None = None,
    refresh: bool = False,
    places: LocationNames | None = None,
) -> list[GiftAcquisition]:
    """Every gift and static in one game, as one record per place a Pokemon is given or waits.

    Unlike a wild slot there is nothing to add up: one of these is one Pokemon. Two rows that a
    player could not tell apart are still folded together, because PokeAPI does sometimes list
    the same encounter twice.
    """
    known = details or {}
    where = places or LocationNames(api, refresh=refresh)
    found: list[GiftAcquisition] = []
    seen: set[tuple] = set()

    for name in species:
        # Encounters hang off a Pokemon rather than a species, as they do for wild slots.
        pokemon = api.default_pokemon(name, refresh=refresh)
        url = f"{BASE_URL}/pokemon/{pokemon}/encounters"
        citation = SourceCitation(source="pokeapi", url=url, retrieved_on=retrieved_on)

        for area in api.encounters(pokemon, refresh=refresh):
            area_slug = area["location_area"]["name"]

            for version_details in area.get("version_details", []):
                if version_details["version"]["name"] != version:
                    continue

                for detail in version_details.get("encounter_details", []):
                    method = detail["method"]["name"]

                    if method in EVENT_METHODS:
                        log.info(
                            "%s in %s comes from a distribution event (%s), not from the game",
                            name,
                            game_id,
                            method,
                        )
                        continue

                    if method not in GIFT_METHODS:
                        continue

                    record = _record(
                        game_id=game_id,
                        species=name,
                        place=where.of(area_slug),
                        method=method,
                        detail=detail,
                        known=known.get(name, GiftDetail()),
                        citation=citation,
                    )

                    key = _identity(record)
                    if key in seen:
                        continue

                    seen.add(key)
                    found.append(record)

    return found


def _record(
    *,
    game_id: str,
    species: str,
    place: tuple[str, str | None],
    method: str,
    detail: dict,
    known: GiftDetail,
    citation: SourceCitation,
) -> GiftAcquisition:
    location, sub_area = place
    conditions = [one["name"] for one in detail.get("condition_values", [])]

    return GiftAcquisition(
        game=game_id,
        target=DexTarget(species=species),
        gift_kind=known.kind or GIFT_METHODS[method],
        # A gift record has one place and no room for a sub-area, so the two are read as one
        # line: "Route 119, Weather Institute".
        location=f"{location}, {sub_area}" if sub_area else location,
        npc=known.npc,
        # A gift comes at one level, so PokeAPI's range is a range of one.
        level=detail.get("min_level"),
        requirement=known.requirement or _item(conditions),
        source=citation,
    )


def _item(conditions: list[str]) -> str | None:
    """The item an encounter's conditions name, as a player would write it."""
    found = next((one for one in conditions if one.startswith(_ITEM)), None)

    return pretty(found.removeprefix(_ITEM)) if found else None


def _identity(record: GiftAcquisition) -> tuple:
    """Everything a player would use to tell two of these apart."""
    return (
        record.target.species,
        record.target.form,
        record.gift_kind,
        record.location,
        record.npc,
        record.level,
        record.requirement,
    )
