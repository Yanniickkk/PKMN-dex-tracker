"""Turning PokeAPI's encounter tables into wild slots.

PokeAPI lists one row per level, so the arithmetic here - adding chances up, keeping the widest
level range, leaving gifts and statics alone - is the whole of step 3 for every game.
"""

from __future__ import annotations

from datetime import date

from livingdex_pipeline.models import EncounterMethod
from livingdex_pipeline.wild import wild_encounters

TODAY = date(2026, 9, 21)


def slot(
    method: str, low: int, high: int, chance: int, conditions: list[str] | None = None
) -> dict:
    return {
        "min_level": low,
        "max_level": high,
        "chance": chance,
        "method": {"name": method},
        "condition_values": [{"name": one} for one in (conditions or [])],
    }


def area(name: str, version: str, details: list[dict]) -> dict:
    return {
        "location_area": {"name": name},
        "version_details": [{"version": {"name": version}, "encounter_details": details}],
    }


class FakeApi:
    """PokeAPI with the two endpoints this needs, and nothing else."""

    def __init__(self, encounters: dict[str, list], locations: dict[str, tuple[str, str]]) -> None:
        self._encounters = encounters
        #: area slug -> (location slug, location's English name)
        self._locations = locations
        self.asked: list[str] = []

    def default_pokemon(self, species: str, *, refresh: bool = False) -> str:
        return species

    def encounters(self, pokemon: str, *, refresh: bool = False) -> list:
        return self._encounters.get(pokemon, [])

    def resource(self, path: str, *, refresh: bool = False) -> dict:
        self.asked.append(path)

        if path.startswith("location-area/"):
            area_slug = path.removeprefix("location-area/")
            return {"location": {"name": self._locations[area_slug][0]}}

        location_slug = path.removeprefix("location/")
        name = next(one for one in self._locations.values() if one[0] == location_slug)[1]

        return {"names": [{"language": {"name": "en"}, "name": name}]}


def build(encounters: dict[str, list], locations: dict[str, tuple[str, str]], version="emerald"):
    return wild_encounters(
        FakeApi(encounters, locations),
        game_id="emerald",
        version=version,
        species=list(encounters),
        retrieved_on=TODAY,
    )


ROUTE_101 = {"hoenn-route-101-area": ("hoenn-route-101", "Route 101")}


def test_slots_of_one_kind_in_one_place_become_one_record() -> None:
    # PokeAPI lists a row per level. A player wants "levels 2 to 4, 40% of the time".
    found = build(
        {
            "poochyena": [
                area(
                    "hoenn-route-101-area",
                    "emerald",
                    [
                        slot("walk", 2, 2, 20),
                        slot("walk", 3, 3, 10),
                        slot("walk", 4, 4, 10),
                    ],
                )
            ]
        },
        ROUTE_101,
    )

    assert len(found) == 1
    assert found[0].levels.minimum == 2
    assert found[0].levels.maximum == 4
    assert found[0].rate_percent == 40
    assert found[0].method is EncounterMethod.WALK
    assert found[0].location == "Route 101"
    assert found[0].sub_area is None


def test_two_ways_of_meeting_it_in_one_place_stay_apart() -> None:
    found = build(
        {
            "tentacool": [
                area(
                    "hoenn-route-101-area",
                    "emerald",
                    [slot("surf", 5, 35, 60), slot("old-rod", 5, 10, 70)],
                )
            ]
        },
        ROUTE_101,
    )

    assert {one.method for one in found} == {EncounterMethod.SURF, EncounterMethod.OLD_ROD}


def test_another_version_is_not_this_game() -> None:
    found = build(
        {"poochyena": [area("hoenn-route-101-area", "ruby", [slot("walk", 2, 2, 20)])]},
        ROUTE_101,
    )

    assert found == []


def test_gifts_and_statics_are_left_for_their_own_steps() -> None:
    found = build(
        {
            "rayquaza": [
                area("hoenn-route-101-area", "emerald", [slot("static", 70, 70, 100)]),
            ],
            "beldum": [
                area("hoenn-route-101-area", "emerald", [slot("gift", 5, 5, 100)]),
            ],
        },
        ROUTE_101,
    )

    assert found == []


def test_two_source_rows_that_produce_the_same_record_are_one_record() -> None:
    # A roamer is listed once for grass and once for water; both come out as "another way" in
    # the same place, at the same level, with the same chance.
    found = build(
        {
            "latias": [
                area(
                    "hoenn-route-101-area",
                    "emerald",
                    [
                        slot("roaming-grass", 40, 40, 25),
                        slot("roaming-water", 40, 40, 25),
                    ],
                )
            ]
        },
        ROUTE_101,
    )

    assert len(found) == 1
    # Not added together: these are two ways of meeting one Pokemon, not two slots in a table.
    assert found[0].rate_percent == 25


def test_a_sub_area_is_what_is_left_of_the_slug() -> None:
    found = build(
        {"zubat": [area("meteor-falls-b1f", "emerald", [slot("walk", 30, 35, 100)])]},
        {"meteor-falls-b1f": ("meteor-falls", "Meteor Falls")},
    )

    assert found[0].location == "Meteor Falls"
    # Floor names keep their shape rather than being title-cased into "B1f".
    assert found[0].sub_area == "B1F"


def test_a_time_of_day_condition_is_carried_into_its_own_field() -> None:
    found = build(
        {
            "hoothoot": [
                area(
                    "hoenn-route-101-area",
                    "emerald",
                    [slot("walk", 2, 4, 30, conditions=["time-night"])],
                )
            ]
        },
        ROUTE_101,
    )

    assert found[0].time_of_day == "night"
    assert found[0].season is None


def test_the_same_place_is_looked_up_once_however_many_pokemon_live_there() -> None:
    api = FakeApi(
        {
            "poochyena": [area("hoenn-route-101-area", "emerald", [slot("walk", 2, 2, 20)])],
            "zigzagoon": [area("hoenn-route-101-area", "emerald", [slot("walk", 2, 2, 20)])],
        },
        ROUTE_101,
    )

    wild_encounters(
        api,
        game_id="emerald",
        version="emerald",
        species=["poochyena", "zigzagoon"],
        retrieved_on=TODAY,
    )

    # Two requests for the first Pokemon, none for the second.
    assert api.asked == ["location-area/hoenn-route-101-area", "location/hoenn-route-101"]


def test_every_record_says_where_it_came_from() -> None:
    found = build(
        {"poochyena": [area("hoenn-route-101-area", "emerald", [slot("walk", 2, 2, 20)])]},
        ROUTE_101,
    )

    assert found[0].source.source == "pokeapi"
    assert found[0].source.retrieved_on == TODAY
    assert str(found[0].source.url).endswith("/pokemon/poochyena/encounters")
