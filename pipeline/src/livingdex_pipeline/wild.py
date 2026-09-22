"""Wild encounter slots for one game, from PokeAPI.

The module docstring in :mod:`pokeapi` says encounter detail is what scrapers are for. That was
written before anyone looked: PokeAPI carries the games' own encounter tables - area, method,
level range, slot chance and the state of the world each slot is filled in, per version - and
they are structured, consistent and citable. Scraping a wiki for the same numbers would be
slower, more fragile and no more true.

What it does not answer is gifts, statics and in-game trades. Those are steps 4 and 5 - see
:mod:`gifts` for the first of them - and the methods that stand for them are skipped here
rather than quietly turned into wild slots.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from . import conditions
from .models import (
    DexTarget,
    EncounterMethod,
    LevelRange,
    SourceCitation,
    WildAcquisition,
)
from .places import LocationNames
from .pokeapi import BASE_URL, PokeApiClient

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


@dataclass(frozen=True)
class _State:
    """The state of the world one row of an encounter table is filled in."""

    time_of_day: str | None
    season: str | None
    requirement: str | None


@dataclass
class _Slot:
    """Rows of one kind in one place, being added up."""

    lowest: int
    highest: int
    chance: int


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

    PokeAPI lists a row per level and per state of the world, so a Pokemon on one route appears
    several times over. They are added back up here: one record per place, method and state,
    carrying the whole level range and the chance of meeting it at all.
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

                slots = _add_up(version_details.get("encounter_details", []), species=name)

                for (method, state), slot in slots.items():
                    location, sub_area = places.of(area_slug)
                    record = _record(
                        game_id=game_id,
                        species=name,
                        location=location,
                        sub_area=sub_area,
                        method=method,
                        state=state,
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

    return _without_redundant_conditions(_without_unconditional_twins(found))


def _add_up(details: list[dict], *, species: str) -> dict[tuple[str, _State], _Slot]:
    """One slot per method and state of the world, levels and chances added together."""
    grouped: dict[tuple[str, _State], _Slot] = {}

    for detail in details:
        method = detail["method"]["name"]
        if method not in WILD_METHODS:
            # Gifts, statics and trades come with their own steps and their own records.
            continue

        conditions = sorted(one["name"] for one in detail.get("condition_values", []))
        key = (method, _state(conditions, species=species))
        low, high = detail["min_level"], detail["max_level"]
        chance = detail.get("chance") or 0

        if key in grouped:
            slot = grouped[key]
            slot.lowest = min(slot.lowest, low)
            slot.highest = max(slot.highest, high)
            slot.chance += chance
        else:
            grouped[key] = _Slot(lowest=low, highest=high, chance=chance)

    return grouped


def _state(values: list[str], *, species: str) -> _State:
    """What a row's conditions say about when it holds this species."""
    return _State(
        time_of_day=conditions.of(values, conditions.TIME),
        season=conditions.of(values, conditions.SEASON),
        requirement=conditions.requirement(values, subject=species),
    )


def _record(
    *,
    game_id: str,
    species: str,
    location: str,
    sub_area: str | None,
    method: str,
    state: _State,
    slot: _Slot,
    citation: SourceCitation,
) -> WildAcquisition:
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
        time_of_day=state.time_of_day,
        season=state.season,
        requirement=state.requirement,
        source=citation,
    )


def _without_unconditional_twins(records: list[WildAcquisition]) -> list[WildAcquisition]:
    """Drop a slot that another slot describes more fully.

    PokeAPI writes a roamer down twice, once for grass and once for water, and Generation 3's
    only three conditioned slots are exactly that: Latias roams Hoenn at level 40 a quarter of
    the time on both rows, and only one of the two says she is not loose until the Elite Four
    are beaten. Two rows alike in place, level and chance are one encounter written twice, and
    the row that names the condition is the one that read the game properly.
    """
    fuller = {_twin(record) for record in records if record.requirement is not None}

    return [
        record
        for record in records
        if record.requirement is not None or _twin(record) not in fuller
    ]


def _without_redundant_conditions(records: list[WildAcquisition]) -> list[WildAcquisition]:
    """Drop a conditional slot where the same place already holds the species without it.

    Stunky stands in the grass on Route 206 whatever is in the Game Boy Advance slot, and five
    more rows saying "and also with Ruby in the slot, and also with Sapphire" tell a player
    nothing they can act on. Gengar is the other case: it is in Sinnoh's grass *only* in
    dual-slot mode, nothing there is unconditional, and all five of its rows stay.
    """
    unconditional = {_where(record) for record in records if record.requirement is None}

    return [
        record
        for record in records
        if record.requirement is None or _where(record) not in unconditional
    ]


def _twin(record: WildAcquisition) -> tuple:
    """Everything about a slot except what has to be true for it."""
    return (
        *_where(record),
        record.levels.minimum,
        record.levels.maximum,
        record.rate_percent,
        record.time_of_day,
        record.season,
    )


def _where(record: WildAcquisition) -> tuple:
    """The place and the way in: what makes two slots the same opportunity."""
    return (
        record.target.species,
        record.target.form,
        record.location,
        record.sub_area,
        record.method,
    )


def _identity(record: WildAcquisition) -> tuple:
    """Everything a player would use to tell two slots apart."""
    return (*_twin(record), record.requirement)
