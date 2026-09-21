"""Wild encounter slots for one game, from PokeAPI.

The module docstring in :mod:`pokeapi` says encounter detail is what scrapers are for. That was
written before anyone looked: PokeAPI carries the games' own encounter tables - area, method,
level range and slot chance, per version - and they are structured, consistent and citable.
Scraping a wiki for the same numbers would be slower, more fragile and no more true. What
PokeAPI does not carry is weather, and Generation 3 has no encounters that depend on it.

What it does not answer is gifts, statics and in-game trades. Those are steps 4 and 5 - see
:mod:`gifts` for the first of them - and the methods that stand for them are skipped here
rather than quietly turned into wild slots.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

from .models import (
    DexTarget,
    EncounterMethod,
    LevelRange,
    SourceCitation,
    WildAcquisition,
)
from .places import LocationNames
from .pokeapi import BASE_URL, PokeApiClient

log = logging.getLogger(__name__)

#: PokeAPI's encounter methods that are a wild slot, and what this project calls them.
WILD_METHODS: dict[str, EncounterMethod] = {
    "walk": EncounterMethod.WALK,
    "surf": EncounterMethod.SURF,
    "old-rod": EncounterMethod.OLD_ROD,
    "good-rod": EncounterMethod.GOOD_ROD,
    "super-rod": EncounterMethod.SUPER_ROD,
    "rock-smash": EncounterMethod.ROCK_SMASH,
    "headbutt": EncounterMethod.HEADBUTT,
    "headbutt-low": EncounterMethod.HEADBUTT,
    "headbutt-normal": EncounterMethod.HEADBUTT,
    "headbutt-high": EncounterMethod.HEADBUTT,
    "honey-tree": EncounterMethod.HONEY_TREE,
    # Still a wild encounter, but not one of the named ways of starting one.
    "seaweed": EncounterMethod.OTHER,
    "feebas-tile-fishing": EncounterMethod.OTHER,
    "roaming-grass": EncounterMethod.OTHER,
    "roaming-water": EncounterMethod.OTHER,
    "grass-spots": EncounterMethod.OTHER,
    "cave-spots": EncounterMethod.OTHER,
    "surf-spots": EncounterMethod.OTHER,
    "bridge-spots": EncounterMethod.OTHER,
    "super-rod-spots": EncounterMethod.SUPER_ROD,
    "dark-grass": EncounterMethod.WALK,
    "rough-terrain": EncounterMethod.WALK,
}

#: Prefixes of PokeAPI condition values this project has a field for.
_TIME = "time-"
_SEASON = "season-"


@dataclass
class _Slot:
    """Slots of one kind in one place, being added up."""

    lowest: int
    highest: int
    chance: int
    conditions: tuple[str, ...]


def wild_encounters(
    api: PokeApiClient,
    *,
    game_id: str,
    version: str,
    species: list[str],
    retrieved_on: date,
    refresh: bool = False,
    places: LocationNames | None = None,
) -> list[WildAcquisition]:
    """Every wild slot in one game, for the species given, as one record per place and method.

    PokeAPI lists a slot per level, so a Pokemon on one route appears several times over. They
    are added back up here: one record per place, method and set of conditions, carrying the
    whole level range and the chance of meeting it at all.
    """
    places = places or LocationNames(api, refresh=refresh)
    found: list[WildAcquisition] = []
    seen: set[tuple] = set()

    for name in species:
        # Encounters hang off a Pokemon rather than a species, and for anything with forms the
        # two are spelled differently.
        pokemon = api.default_pokemon(name, refresh=refresh)
        url = f"{BASE_URL}/pokemon/{pokemon}/encounters"
        citation = SourceCitation(source="pokeapi", url=url, retrieved_on=retrieved_on)

        for area in api.encounters(pokemon, refresh=refresh):
            area_slug = area["location_area"]["name"]

            for version_details in area.get("version_details", []):
                if version_details["version"]["name"] != version:
                    continue

                for slot in _add_up(version_details.get("encounter_details", [])):
                    location, sub_area = places.of(area_slug)
                    record = _record(
                        game_id=game_id,
                        species=name,
                        location=location,
                        sub_area=sub_area,
                        slot=slot,
                        citation=citation,
                    )

                    # Two of PokeAPI's methods can land on one of ours - a roamer is listed
                    # once for grass and once for water - and two records a player cannot tell
                    # apart are one record. Their chances are not added: they are two ways of
                    # meeting the same thing, not two slots in one table.
                    key = _identity(record)
                    if key in seen:
                        continue

                    seen.add(key)
                    found.append(record)

    return found


def _add_up(details: list[dict]) -> list[_Slot]:
    """One slot per method and set of conditions, with the levels and chances added together."""
    grouped: dict[tuple[str, tuple[str, ...]], _Slot] = {}

    for detail in details:
        method = detail["method"]["name"]
        if method not in WILD_METHODS:
            # Gifts, statics and trades come with their own steps and their own records.
            continue

        conditions = tuple(sorted(one["name"] for one in detail.get("condition_values", [])))
        key = (method, conditions)
        low, high = detail["min_level"], detail["max_level"]
        chance = detail.get("chance") or 0

        if key in grouped:
            slot = grouped[key]
            slot.lowest = min(slot.lowest, low)
            slot.highest = max(slot.highest, high)
            slot.chance += chance
        else:
            grouped[key] = _Slot(lowest=low, highest=high, chance=chance, conditions=conditions)

    return [_named(method, slot) for (method, _), slot in grouped.items()]


def _named(method: str, slot: _Slot) -> _Slot:
    slot.conditions = (method, *slot.conditions)
    return slot


def _record(
    *,
    game_id: str,
    species: str,
    location: str,
    sub_area: str | None,
    slot: _Slot,
    citation: SourceCitation,
) -> WildAcquisition:
    method, *conditions = slot.conditions
    time_of_day = _condition(conditions, _TIME)
    season = _condition(conditions, _SEASON)

    for condition in conditions:
        if not condition.startswith((_TIME, _SEASON)):
            # Slot 2 cartridges, radar, story progress: real restrictions this project has no
            # field for. Logged rather than dropped without a word.
            log.info("%s in %s has an unmapped condition: %s", species, location, condition)

    return WildAcquisition(
        game=game_id,
        target=DexTarget(species=species),
        location=location,
        sub_area=sub_area,
        method=WILD_METHODS[method],
        levels=LevelRange(minimum=slot.lowest, maximum=slot.highest),
        # Slot chances are out of a hundred and add up per method, so the sum is the chance of
        # meeting this Pokemon at all. Clamped, because a source that says 120 is wrong rather
        # than certain.
        rate_percent=min(slot.chance, 100) or None,
        time_of_day=time_of_day,
        season=season,
        source=citation,
    )


def _condition(conditions: list[str], prefix: str) -> str | None:
    found = next((one for one in conditions if one.startswith(prefix)), None)
    return found[len(prefix) :] if found else None


def _identity(record: WildAcquisition) -> tuple:
    """Everything a player would use to tell two slots apart."""
    return (
        record.target.species,
        record.target.form,
        record.location,
        record.sub_area,
        record.method,
        record.levels.minimum,
        record.levels.maximum,
        record.rate_percent,
        record.time_of_day,
        record.season,
    )
