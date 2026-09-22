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


def test_the_ordinary_state_of_the_world_is_not_a_condition() -> None:
    # Generation 4 marks every row of a table with the state it is filled in, so the slots a
    # player walks into on an ordinary afternoon say "no swarm", "no Poke Radar", "nothing in
    # the Game Boy Advance slot". One Bidoof, one record, and the chances add up.
    found = build(
        {
            "bidoof": [
                area(
                    "hoenn-route-101-area",
                    "diamond",
                    [
                        slot("walk", 2, 2, 20, conditions=["swarm-no"]),
                        slot("walk", 3, 3, 15),
                        slot("walk", 3, 3, 11, conditions=["radar-off"]),
                        slot("walk", 2, 2, 4, conditions=["slot2-none"]),
                    ],
                )
            ]
        },
        ROUTE_101,
        version="diamond",
    )

    assert len(found) == 1
    assert found[0].rate_percent == 50
    assert found[0].levels.minimum == 2
    assert found[0].levels.maximum == 3
    assert found[0].requirement is None


def test_a_condition_a_player_has_to_arrange_is_written_out() -> None:
    found = build(
        {
            "gengar": [
                area(
                    "hoenn-route-101-area",
                    "diamond",
                    [slot("walk", 15, 15, 4, conditions=["slot2-ruby"])],
                )
            ]
        },
        ROUTE_101,
        version="diamond",
    )

    assert found[0].requirement == (
        "Dual-slot mode, with a Pokemon Ruby cartridge in the Game Boy Advance slot"
    )


def test_two_conditions_on_one_row_become_one_sentence() -> None:
    found = build(
        {
            "drapion": [
                area(
                    "hoenn-route-101-area",
                    "diamond",
                    [
                        slot(
                            "walk",
                            26,
                            26,
                            5,
                            conditions=[
                                "great-marsh-daily-slot-1-of-32",
                                "story-progress-national-dex",
                            ],
                        )
                    ],
                )
            ]
        },
        ROUTE_101,
        version="diamond",
    )

    # Each phrase is written to stand on its own, so the second is lowered into the first
    # rather than left reading like two sentences that collided.
    assert found[0].requirement == (
        "Only on days the Great Marsh rotates it in (daily slot 1 of 32) "
        "and after the National Dex opens"
    )


def test_the_fuller_of_two_rows_for_one_encounter_is_the_one_kept() -> None:
    # PokeAPI writes a roamer down twice, once for grass and once for water, and in Generation 3
    # only one of the two rows says Latias is not loose until the Elite Four are beaten. Same
    # place, same level, same chance: one encounter, and the row that read the game wins.
    found = build(
        {
            "latias": [
                area(
                    "hoenn-route-101-area",
                    "emerald",
                    [
                        slot(
                            "roaming-grass", 40, 40, 25, conditions=["story-progress-hall-of-fame"]
                        ),
                        slot("roaming-water", 40, 40, 25),
                    ],
                )
            ]
        },
        ROUTE_101,
    )

    assert len(found) == 1
    assert found[0].requirement == "After entering the Hall of Fame"


def test_a_condition_on_something_the_place_already_gives_is_dropped() -> None:
    # Stunky is in this grass whatever is in the Game Boy Advance slot. "And also with Ruby in
    # the slot" is not a second way of getting one.
    found = build(
        {
            "stunky": [
                area(
                    "hoenn-route-101-area",
                    "diamond",
                    [
                        slot("walk", 14, 14, 20, conditions=["swarm-no"]),
                        slot("walk", 15, 15, 4, conditions=["slot2-ruby"]),
                        slot("walk", 15, 15, 4, conditions=["slot2-sapphire"]),
                    ],
                )
            ]
        },
        ROUTE_101,
        version="diamond",
    )

    assert len(found) == 1
    assert found[0].requirement is None


def test_a_condition_on_something_the_place_gives_no_other_way_stays() -> None:
    # The other case, and the reason the rule is about the place rather than about the species:
    # nothing here is unconditional, so every cartridge that opens the slot is worth naming.
    found = build(
        {
            "gengar": [
                area(
                    "hoenn-route-101-area",
                    "diamond",
                    [
                        slot("walk", 15, 15, 4, conditions=["slot2-ruby"]),
                        slot("walk", 15, 15, 4, conditions=["slot2-sapphire"]),
                    ],
                )
            ]
        },
        ROUTE_101,
        version="diamond",
    )

    assert len(found) == 2
    assert all(one.requirement for one in found)


def test_a_condition_nobody_has_worded_yet_is_carried_and_complained_about(caplog) -> None:
    # The example here used to be one of Johto's Safari Zone blocks, until HeartGold arrived and
    # somebody wrote the sentence. That is the whole point of this path: an unread condition is
    # carried and complained about until a generation gets round to it. This one is Generation
    # 7's, and its turn will come.
    found = build(
        {
            "shellder": [
                area(
                    "hoenn-route-101-area",
                    "diamond",
                    [slot("walk", 20, 20, 5, conditions=["sos-battle-chain"])],
                )
            ]
        },
        ROUTE_101,
        version="diamond",
    )

    # Carried through rather than dropped: a restriction nobody has read is still a restriction.
    assert found[0].requirement == "Sos battle chain"
    assert "no wording yet" in caplog.text


def test_johtos_own_conditions_read_as_sentences(caplog) -> None:
    found = build(
        {
            "buizel": [
                area(
                    "johto-route-30-area",
                    "heartgold",
                    [slot("walk", 5, 5, 10, conditions=["radio-sinnoh"])],
                )
            ],
            "fearow": [
                area(
                    "johto-route-30-area",
                    "heartgold",
                    [slot("walk", 20, 20, 5, conditions=["johto-safari-blocks-forest-min-5"])],
                )
            ],
            "heracross": [
                area(
                    "johto-route-30-area",
                    "heartgold",
                    [slot("headbutt", 10, 10, 5, conditions=["headbutt-tree-rare"])],
                )
            ],
        },
        {"johto-route-30-area": ("johto-route-30", "Route 30")},
        version="heartgold",
    )

    said = {one.target.species: one.requirement for one in found}

    # A Sinnoh Pokemon in Johto's grass, put there by the radio rather than by a cartridge in
    # the slot underneath - which is what Sinnoh needed for the same trick.
    assert said["buizel"] == "With the Pokegear radio tuned to the Sinnoh sound"
    # Points rather than objects: an area holds thirty, and days of use make each count for more.
    assert said["fearow"] == "With at least 5 forest block points in that area of the Safari Zone"
    assert said["heracross"] == "On one of the rare headbutt trees"
    # Every one of them had a sentence waiting; nothing was carried through as a slug.
    assert "no wording yet" not in caplog.text


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
