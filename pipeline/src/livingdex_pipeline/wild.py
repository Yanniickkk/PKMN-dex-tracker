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
from dataclasses import dataclass, replace

from . import conditions
from .forms import targets_of
from .models import (
    DexTarget,
    EncounterMethod,
    Form,
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
    # Generation 6's. A horde is five at once; the flower patches are three tables that differ
    # by the colour of the flowers standing in them, and the colour is the requirement rather
    # than three methods; the Berry Fields' trees each hold one species by the colour of the
    # tree. The five ambushes are one method for the reason `EncounterMethod` gives.
    "horde": EncounterMethod.HORDE,
    "red-flowers": EncounterMethod.FLOWER_PATCH,
    "yellow-flowers": EncounterMethod.FLOWER_PATCH,
    "purple-flowers": EncounterMethod.FLOWER_PATCH,
    "berry-trees": EncounterMethod.BERRY_TREE,
    "ceiling-ambush": EncounterMethod.AMBUSH,
    "ground-ambush": EncounterMethod.AMBUSH,
    "sky-ambush": EncounterMethod.AMBUSH,
    "rustling-bush-ambush": EncounterMethod.AMBUSH,
    "trash-can-ambush": EncounterMethod.AMBUSH,
    # Alola's two. An SOS ally is the method rather than the thing it was called by: what a
    # player has to do is bring a wild Pokemon low and wait, wherever they are standing. The
    # compound - an ally called by something met in a bubbling spot - stays an SOS slot for the
    # reason the Super Rod one does: the ally is the part that produces this species, and where
    # it was called is said in the requirement.
    "sos": EncounterMethod.SOS,
    "sos-from-bubbling-spot": EncounterMethod.SOS,
    # And Alola's moving spots, which the source gives as one method and calls after the only
    # one of them that is in water. Haina Desert's sand clouds and Route 2's rustling grass
    # arrive under the same name, so the name this project uses is the family's.
    "bubbling-spots": EncounterMethod.MOVING_SPOT,
    # Let's Go's three, each with the rarer table beside it that the source spells
    # ``-special``. The rarity is said in :data:`METHOD_REQUIREMENTS` rather than in the name:
    # it is the same place and the same way of meeting something, met less often.
    "overworld": EncounterMethod.OVERWORLD,
    "overworld-special": EncounterMethod.OVERWORLD,
    "overworld-water": EncounterMethod.OVERWORLD_WATER,
    "overworld-water-special": EncounterMethod.OVERWORLD_WATER,
    "overworld-flying": EncounterMethod.OVERWORLD_FLYING,
    "overworld-flying-special": EncounterMethod.OVERWORLD_FLYING,
    # Galar's six, and four of them are an overworld spawn with something said beside it. The
    # Wild Area is Let's Go's idea grown up: what is standing there is visible, and the source
    # separates the ones that wander a fixed patch, the ones that come up out of the ground or
    # the swamp, and the ones that chase a player who steps into their water. Three places to
    # look is a method; how the thing behaves once it is looked at is a sentence.
    "wanderer": EncounterMethod.OVERWORLD,
    "wanderer-water": EncounterMethod.OVERWORLD_WATER,
    "overworld-dirt": EncounterMethod.OVERWORLD,
    "chase-water": EncounterMethod.OVERWORLD_WATER,
    # And the two that are neither a table nor a place: a Max Raid is a beam of light over a den
    # and four trainers against one Dynamax Pokemon, with one throw at the end of it, and a
    # Dynamax Adventure is the Crown Tundra's cave run that ends in a choice of legendary. Both
    # produce species that are nowhere else in these games, which is why neither is `other`.
    "max-raid": EncounterMethod.MAX_RAID,
    "dynamax-adventure": EncounterMethod.DYNAMAX_ADVENTURE,
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
    # Which flowers, which is the whole difference between the three tables.
    "red-flowers": "In a patch of red flowers",
    "yellow-flowers": "In a patch of yellow flowers",
    "purple-flowers": "In a patch of purple flowers",
    # And what it is that jumps out, which the one ambush method does not say by itself.
    "ceiling-ambush": "Dropping from the ceiling",
    "ground-ambush": "Bursting out of the ground",
    "sky-ambush": "Swooping down out of the sky",
    "rustling-bush-ambush": "Out of a rustling bush",
    "trash-can-ambush": "Out of a bin",
    # Where the Pokemon that calls for help was met, which an SOS slot does not say by itself.
    "sos-from-bubbling-spot": "Called by something met in a bubbling spot",
    # And how often, for Let's Go's second table. Every slot in those games is listed at a
    # hundred percent because what a player meets is decided when the overworld is populated
    # rather than when a battle starts, so the chance column cannot carry this and the sentence
    # has to. It is the difference between the Pidgey on Route 1 and the Chansey on Route 1.
    "overworld-special": "A rare spawn: it appears far less often than the rest of the table",
    "overworld-water-special": (
        "A rare spawn: it appears far less often than the rest of the table"
    ),
    "overworld-flying-special": (
        "A rare spawn: it appears far less often than the rest of the table"
    ),
    # Galar's four, which are what its overworld methods carry that the three enum values do
    # not. The source's own descriptions, in a player's words.
    "wanderer": "Standing in one fixed spot rather than anywhere in the area",
    "wanderer-water": "Floating in one fixed spot rather than anywhere on the water",
    "overworld-dirt": "Coming up out of the ground or out of the swamp",
    "chase-water": "It gives chase as soon as the water is entered",
}


@dataclass(frozen=True)
class _State:
    """The state of the world one row of an encounter table is filled in."""

    time_of_day: str | None
    season: str | None
    #: Galar's, and the first generation whose weather decides what is standing there.
    weather: str | None
    requirement: str | None
    #: The Max Raid difficulty this row is for, before :func:`_folded_stars` turns a run of them
    #: into one sentence. Not part of what makes two records different to a player.
    stars: int | None = None


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
    version: str | Sequence[str],
    species: list[str],
    refresh: bool = False,
    forms: Sequence[Form] = (),
    places: LocationNames | None = None,
    gates: Mapping[str, str] | None = None,
    not_counted: Mapping[str, str] | None = None,
) -> list[WildAcquisition]:
    """Every wild slot in one game, for the species given, as one record per place and method.

    PokeAPI lists a row per level and per state of the world, so a Pokemon on one route appears
    several times over. They are added back up here: one record per place, method and state,
    carrying the whole level range and the chance of meeting it at all.

    Each record is cited to the exact url it came out of, on the day that url was fetched -
    which the cache remembers, so rebuilding a dataset from unchanged pages does not quietly
    re-date every claim in it.

    ``not_counted`` is why a whole place's slots are real and still do not answer "can I get one
    here", keyed the same way. Kalos's Friend Safari is the first: eighteen areas of ordinary
    tables that want another person's 3DS. The records are kept - they are true, and a player
    with a friend can use them - and they are left out of what the dataset counts as obtainable.

    ``gates`` is what a whole place asks of a player before any of its slots can be reached,
    keyed by the place's name. PokeAPI marks conditions on a row rather than on a location, so
    a door that is locked from the outside is invisible to it: the Nature Preserve in Unova is
    an ordinary forest full of ordinary tables, and it is behind a plane ride nobody is offered
    until the regional dex is filled. A player told to walk into a place they cannot enter has
    been told nothing.

    ``version`` is usually one name and may be several, which Galar is the first to need: the
    source files the Isle of Armor and the Crown Tundra as versions of their own, so a Sword
    player's grass is ``sword``, ``the-isle-of-armor-sword`` and ``the-crown-tundra-sword``
    together. Reading only the first would lose two thirds of the game and nothing would say so.

    ``forms`` is this game's own form table, and passing it is how a game says that some of what
    its grass holds is a form rather than a species. Alola is the first that needs it and needs
    it badly: every Rattata on Route 1 is the Alolan one, the Kantonian is nowhere in the game,
    and a record saying "Rattata, Route 1" would be wrong about the only Rattata there. A game
    that leaves it out asks about each species' default Pokemon and nothing else, which is what
    every game before Generation 7 does.
    """
    places = places or LocationNames(api, refresh=refresh)
    wanted_versions = (version,) if isinstance(version, str) else tuple(version)
    gates = gates or {}
    uncounted = not_counted or {}
    found: list[WildAcquisition] = []
    seen: set[tuple] = set()

    known_forms = {one.id for one in forms}

    for name in species:
        # Encounters hang off a Pokemon rather than a species, and a species can be several.
        for pokemon, target in targets_of(api, name, known_forms, refresh=refresh):
            url = f"{BASE_URL}/pokemon/{pokemon}/encounters"
            citation = SourceCitation(
                source="pokeapi", url=url, retrieved_on=api.retrieved_on(url)
            )

            for area in api.encounters(pokemon, refresh=refresh):
                area_slug = area["location_area"]["name"]

                for version_details in area.get("version_details", []):
                    if version_details["version"]["name"] not in wanted_versions:
                        continue

                    slots = _folded_stars(
                        _add_up(version_details.get("encounter_details", []), species=name)
                    )

                    for (method, state), slot in slots.items():
                        location, sub_area = places.of(area_slug)
                        record = _record(
                            game_id=game_id,
                            target=target,
                            location=location,
                            sub_area=sub_area,
                            method=method,
                            state=state,
                            slot=slot,
                            citation=citation,
                            gate=gates.get(location),
                            does_not_count=uncounted.get(location),
                        )

                        # Two of PokeAPI's methods can land on one of ours - a roamer is listed
                        # once for grass and once for water - and two records a player cannot
                        # tell apart are one record. Their chances are not added: they are two
                        # ways of meeting the same thing, not two slots in one table.
                        key = _identity(record)
                        if key in seen:
                            continue

                        seen.add(key)
                        found.append(record)

    return _merged(
        _without_pointless_weather(
            _without_redundant_conditions(_without_unconditional_twins(found))
        )
    )


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
    said = conditions.requirement(
        values,
        subject=species,
        skip=(conditions.TIME, conditions.SEASON, conditions.WEATHER, conditions.RATING),
    )
    by_method = METHOD_REQUIREMENTS.get(method)
    # Through the same joiner a list of conditions goes through, so that a method's sentence
    # and a condition's do not collide: "A rare spawn ... and Only once the Articuno" reads as
    # two sentences that ran into each other, which is the thing that function is for.
    requirement = conditions.joined(by_method, said)

    return _State(
        time_of_day=conditions.of(values, conditions.TIME),
        season=conditions.of(values, conditions.SEASON),
        weather=conditions.of(values, conditions.WEATHER),
        requirement=requirement,
        stars=conditions.stars(values),
    )


def _record(
    *,
    game_id: str,
    target: DexTarget,
    location: str,
    sub_area: str | None,
    method: str,
    state: _State,
    slot: _Slot,
    citation: SourceCitation,
    gate: str | None = None,
    does_not_count: str | None = None,
) -> WildAcquisition:
    return WildAcquisition(
        game=game_id,
        target=target,
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
        weather=conditions.WEATHER_NAMES.get(state.weather, state.weather),
        # The way in comes first: it is the thing a player cannot do anything about, and what
        # the row itself asks for only matters once they are standing there.
        requirement=conditions.joined(gate, state.requirement),
        does_not_count=does_not_count,
        source=citation,
    )


def _folded_stars(slots: dict[tuple[str, _State], _Slot]) -> dict[tuple[str, _State], _Slot]:
    """A run of Max Raid difficulties on otherwise identical rows, as one sentence.

    The source gives a den's table one row per star rating, so a species that can be raided at
    three, four and five stars arrives as three rows differing in nothing else. Five records
    apiece would bury a den under its own difficulty settings; what a player wants to read is
    "at 3 to 5 stars", which is what the rating is - a number, and this is the range of it.

    The odds are the best of the run rather than their sum, for the reason :func:`_merged` gives
    about rooms: a raid is one den at one rating, so meeting it is as likely as the rating being
    played makes it.
    """
    runs: dict[tuple[str, _State], tuple[_Slot, int, int]] = {}

    for (method, state), slot in slots.items():
        if state.stars is None:
            runs[(method, state)] = (slot, 0, 0)
            continue

        key = (method, replace(state, stars=None))
        found = runs.get(key)

        if found is None:
            runs[key] = (slot, state.stars, state.stars)
            continue

        already, lowest, highest = found
        runs[key] = (
            _Slot(
                lowest=min(already.lowest, slot.lowest),
                highest=max(already.highest, slot.highest),
                chance=max(already.chance, slot.chance),
            ),
            min(lowest, state.stars),
            max(highest, state.stars),
        )

    folded: dict[tuple[str, _State], _Slot] = {}
    for (method, state), (slot, lowest, highest) in runs.items():
        if not highest:
            folded[(method, state)] = slot
            continue

        said = conditions.star_range(lowest, highest)
        folded[(method, replace(state, requirement=conditions.joined(state.requirement, said)))] = (
            slot
        )

    return folded


def _without_pointless_weather(records: list[WildAcquisition]) -> list[WildAcquisition]:
    """Drop the weather from a slot that is there whatever the weather.

    Galar is the first region whose weather decides what is standing in front of a player, and
    the source writes a row per state of the sky - so a Rookidee that flies over Rolling Fields
    in all nine arrives as nine records that differ in one word. Nine rows saying "and also when
    it is foggy" tell a player nothing to act on.

    The nine are not the same nine everywhere: a place the sun never leaves has no snow table,
    and demanding all nine would leave a species there marked as weather-dependent forever. So
    what counts as "whatever the weather" is measured per place and method, from every weather
    this game lists there at all.
    """
    everywhere: dict[tuple, set[str]] = {}
    for record in records:
        if record.weather is not None:
            everywhere.setdefault(_weather_key(record), set()).add(record.weather)

    by_slot: dict[tuple, list[WildAcquisition]] = {}
    for record in records:
        by_slot.setdefault(_but_the_weather(record), []).append(record)

    kept: list[WildAcquisition] = []
    for group in by_slot.values():
        weathers = {one.weather for one in group if one.weather is not None}
        possible = everywhere.get(_weather_key(group[0]), set())

        if not weathers or weathers < possible:
            kept.extend(group)
            continue

        kept.append(
            group[0].model_copy(
                update={
                    "weather": None,
                    "levels": LevelRange(
                        minimum=min(one.levels.minimum for one in group),
                        maximum=max(one.levels.maximum for one in group),
                    ),
                    "rate_percent": _best_of(one.rate_percent for one in group),
                }
            )
        )

    return kept


def _weather_key(record: WildAcquisition) -> tuple:
    """The place and the way in, which is what a set of weathers belongs to."""
    return (record.location, record.sub_area, record.method)


def _but_the_weather(record: WildAcquisition) -> tuple:
    """Everything a player would use to tell two slots apart except the state of the sky."""
    return (
        *_where(record),
        record.time_of_day,
        record.season,
        record.requirement,
        record.does_not_count,
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
        key = (
            *_where(record),
            record.time_of_day,
            record.season,
            record.weather,
            record.requirement,
        )
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


def _best_of(rates) -> float | None:
    known = [one for one in rates if one is not None]

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
        record.weather,
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
