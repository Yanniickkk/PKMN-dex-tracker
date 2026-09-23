"""Wild encounter slots for one game, from PokeAPI.

The module docstring in :mod:`pokeapi` says encounter detail is what scrapers are for. That was
written before anyone looked: PokeAPI carries the games' own encounter tables - area, method,
level range, slot chance and the state of the world each slot is filled in, per version - and
they are structured, consistent and citable. Scraping a wiki for the same numbers would be
slower, more fragile and no more true.

What it does not answer is gifts, statics and in-game trades. Those are steps 4 and 5 - see
:mod:`gifts` for the first of them - and the methods that stand for them are skipped here
rather than quietly turned into wild slots.

It is also not complete, which took until Generation 2 to find out. PokeAPI carries nothing at
all for the Bug-Catching Contest, and a Scyther in Gold comes from nowhere else - so a game may
also bring slots written down by hand, cited to whoever was read. That is a last resort and it
is meant to stay one: a table here cannot be re-fetched, cannot be checked against the game, and
goes stale without saying so.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

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
    # Generation 5's four moving spots and the darker grass beside the ordinary kind. PokeAPI
    # calls them all "spots"; a player calls them rustling grass, a dust cloud, a ripple and a
    # shadow, and each one is a different table in a different place.
    "dark-grass": EncounterMethod.DARK_GRASS,
    "grass-spots": EncounterMethod.RUSTLING_GRASS,
    "cave-spots": EncounterMethod.DUST_CLOUD,
    "surf-spots": EncounterMethod.RIPPLING_WATER,
    "bridge-spots": EncounterMethod.BRIDGE_SHADOW,
    # The one compound case. Fishing in a ripple wants both the rod and the ripple, and the rod
    # is the half a player can be missing - so it stays a Super Rod slot and the water it is
    # cast into is said in the requirement, by :data:`METHOD_REQUIREMENTS`.
    "super-rod-spots": EncounterMethod.SUPER_ROD,
    # Still a wild encounter, but not one of the named ways of starting one.
    "seaweed": EncounterMethod.OTHER,
    "feebas-tile-fishing": EncounterMethod.OTHER,
    "roaming-grass": EncounterMethod.OTHER,
    "roaming-water": EncounterMethod.OTHER,
    "rough-terrain": EncounterMethod.WALK,
}

#: What a method says about a slot that its name does not carry once it is mapped.
#:
#: Only where a PokeAPI method means two things and this project's enum can hold one of them.
#: The sentence lands in the same field a condition would, because to a player it is the same
#: kind of fact: something has to be true before the slot is there at all.
METHOD_REQUIREMENTS: dict[str, str] = {
    "super-rod-spots": "Cast into rippling water",
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
    refresh: bool = False,
    places: LocationNames | None = None,
    gates: Mapping[str, str] | None = None,
) -> list[WildAcquisition]:
    """Every wild slot in one game, for the species given, as one record per place and method.

    PokeAPI lists a row per level and per state of the world, so a Pokemon on one route appears
    several times over. They are added back up here: one record per place, method and state,
    carrying the whole level range and the chance of meeting it at all.

    Each record is cited to the exact url it came out of, on the day that url was fetched -
    which the cache remembers, so rebuilding a dataset from unchanged pages does not quietly
    re-date every claim in it.

    ``gates`` is what a whole place asks of a player before any of its slots can be reached,
    keyed by the place's name. PokeAPI marks conditions on a row rather than on a location, so
    a door that is locked from the outside is invisible to it: the Nature Preserve in Unova is
    an ordinary forest full of ordinary tables, and it is behind a plane ride nobody is offered
    until the regional dex is filled. A player told to walk into a place they cannot enter has
    been told nothing.
    """
    places = places or LocationNames(api, refresh=refresh)
    gates = gates or {}
    found: list[WildAcquisition] = []
    seen: set[tuple] = set()

    for name in species:
        # Encounters hang off a Pokemon rather than a species, and for anything with forms the
        # two are spelled differently.
        pokemon = api.default_pokemon(name, refresh=refresh)
        url = f"{BASE_URL}/pokemon/{pokemon}/encounters"
        citation = SourceCitation(source="pokeapi", url=url, retrieved_on=api.retrieved_on(url))

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
                        gate=gates.get(location),
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

    return _merged(_without_redundant_conditions(_without_unconditional_twins(found)))


def _add_up(details: list[dict], *, species: str) -> dict[tuple[str, _State], _Slot]:
    """One slot per method and state of the world, levels and chances added together."""
    grouped: dict[tuple[str, _State], _Slot] = {}

    for detail in details:
        method = detail["method"]["name"]
        if method not in WILD_METHODS:
            # Gifts, statics and trades come with their own steps and their own records.
            continue

        conditions = sorted(one["name"] for one in detail.get("condition_values", []))
        key = (method, _state(conditions, species=species, method=method))
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


def _state(values: list[str], *, species: str, method: str) -> _State:
    """What a row's conditions say about when it holds this species.

    The method can say something too, where PokeAPI's is narrower than ours: fishing in a
    ripple is a Super Rod slot here, and where the rod is cast would be lost otherwise.
    """
    said = conditions.requirement(values, subject=species)
    by_method = METHOD_REQUIREMENTS.get(method)
    requirement = " and ".join(one for one in (by_method, said) if one) or None

    return _State(
        time_of_day=conditions.of(values, conditions.TIME),
        season=conditions.of(values, conditions.SEASON),
        requirement=requirement,
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
    gate: str | None = None,
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
        # The way in comes first: it is the thing a player cannot do anything about, and what
        # the row itself asks for only matters once they are standing there.
        requirement=conditions.joined(gate, state.requirement),
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


def _merged(records: list[WildAcquisition]) -> list[WildAcquisition]:
    """Fold together records a player has no way of telling apart.

    Dropping a room the source has no name for leaves several records alike in species, place,
    method and the state of the world, differing only in levels and odds: Boldore stands in
    three of Victory Road's unnamed rooms at slightly different levels, and three rows that all
    read "Victory Road, walking" are three ways of saying one thing.

    The level range is widened to cover all of them and the odds are the best of them rather
    than their sum - a player is in one room at a time, so meeting it is as likely as the room
    they are standing in makes it, and adding the rooms up would promise something the game
    never offers.
    """
    merged: dict[tuple, WildAcquisition] = {}

    for record in records:
        key = (*_where(record), record.time_of_day, record.season, record.requirement)
        already = merged.get(key)

        if already is None:
            merged[key] = record
            continue

        merged[key] = already.model_copy(
            update={
                "levels": LevelRange(
                    minimum=min(already.levels.minimum, record.levels.minimum),
                    maximum=max(already.levels.maximum, record.levels.maximum),
                ),
                "rate_percent": _best(already.rate_percent, record.rate_percent),
            }
        )

    return list(merged.values())


def _best(left: float | None, right: float | None) -> float | None:
    known = [one for one in (left, right) if one is not None]

    return max(known) if known else None


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


@dataclass(frozen=True)
class RecordedSlot:
    """One wild slot a source other than PokeAPI knows about.

    Everything a PokeAPI row would have carried, filled in by hand: where it is, how it is met,
    what levels it comes at and how often. ``requirement`` is what makes the slot possible at
    all - being in a contest, in this generation's one case - because the field is the same one
    a swarm or a radio channel lands in.
    """

    species: str
    location: str
    lowest: int
    highest: int
    method: EncounterMethod = EncounterMethod.WALK
    sub_area: str | None = None
    rate_percent: float | None = None
    requirement: str | None = None


def recorded_encounters(
    *,
    game_id: str,
    slots: Sequence[RecordedSlot],
    species: Sequence[str],
    citation: SourceCitation,
) -> list[WildAcquisition]:
    """Wild slots written down by hand, for a part of a game PokeAPI does not carry.

    One record per slot, filtered to what this game's living dex asks for - a table that lists
    ten species for a dex that wants eight should not add the other two.

    The citation is the game file's to give, and it is not a PokeAPI url. That is the whole
    difference between these records and every other wild slot: a reader can see where the
    numbers came from and go and check them.
    """
    wanted = set(species)

    return [
        WildAcquisition(
            game=game_id,
            target=DexTarget(species=slot.species),
            location=slot.location,
            sub_area=slot.sub_area,
            method=slot.method,
            levels=LevelRange(minimum=slot.lowest, maximum=slot.highest),
            rate_percent=slot.rate_percent,
            requirement=slot.requirement,
            source=citation,
        )
        for slot in slots
        if slot.species in wanted
    ]
