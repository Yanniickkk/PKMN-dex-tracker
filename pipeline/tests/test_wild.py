"""Turning PokeAPI's encounter tables into wild slots.

PokeAPI lists one row per level, so the arithmetic here - adding chances up, keeping the widest
level range, leaving gifts and statics alone - is the whole of step 3 for every game.
"""

from __future__ import annotations

from datetime import date

from livingdex_pipeline.models import EncounterMethod, SourceCitation
from livingdex_pipeline.places import LocationNames
from livingdex_pipeline.wild import RecordedSlot, recorded_encounters, wild_encounters

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

    def retrieved_on(self, url: str) -> date:
        """The day the cache says this url was fetched, which a citation carries."""
        return TODAY

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


def build(
    encounters: dict[str, list],
    locations: dict[str, tuple[str, str]],
    version="emerald",
    gates: dict[str, str] | None = None,
):
    return wild_encounters(
        FakeApi(encounters, locations),
        game_id="emerald",
        version=version,
        species=list(encounters),
        gates=gates,
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


def test_a_sub_area_shouts_the_acronyms_a_slug_writes_in_lower_case() -> None:
    # The Pokemon World Tournament, which Unova's Relic Passage has an entrance to. "Pwt
    # Entrance" is not a place; it is a title-caser that did not know what it was reading.
    found = build(
        {"woobat": [area("relic-passage-pwt-entrance", "black-2", [slot("walk", 30, 35, 100)])]},
        {"relic-passage-pwt-entrance": ("relic-passage", "Relic Passage")},
        version="black-2",
    )

    assert found[0].sub_area == "PWT Entrance"


def test_a_sub_area_can_be_renamed_where_the_generated_name_belongs_elsewhere() -> None:
    # A location's English name was written by a person; a sub-area's comes out of the slug and
    # nobody read it. Unova's Season Research Lab is filed as `weather-institute`, and the
    # Weather Institute is a building in Hoenn - so the generated name is not a worse name, it
    # is another region's.
    api = FakeApi(
        {},
        {
            "unova-route-6-weather-institute": ("unova-route-6", "Route 6"),
            "meteor-falls-b1f": ("meteor-falls", "Meteor Falls"),
        },
    )
    places = LocationNames(api, renamed_sub_areas={"Weather Institute": "Season Research Lab"})

    assert places.of("unova-route-6-weather-institute") == ("Route 6", "Season Research Lab")
    # And a sub-area nobody renamed comes through as it was.
    assert places.of("meteor-falls-b1f") == ("Meteor Falls", "B1F")


def test_a_gated_place_puts_the_way_in_in_front_of_every_slot() -> None:
    # A condition in the source hangs on a row of a table, so it cannot say that the whole
    # place is locked from the outside. The caller knows, and every slot in that place carries
    # it.
    found = build(
        {"kecleon": [area("nature-sanctuary-area", "black-2", [slot("dark-grass", 65, 65, 10)])]},
        {"nature-sanctuary-area": ("nature-sanctuary", "Nature Preserve")},
        version="black-2",
        gates={"Nature Preserve": "Only by plane from Mistralton City"},
    )

    assert found[0].requirement == "Only by plane from Mistralton City"


def test_a_gate_is_matched_against_the_name_a_player_reads() -> None:
    # Keyed by the location's name rather than its slug, so a place the caller has renamed is
    # gated under the name it renamed it to. Keying on the slug would mean writing the source's
    # mistake down twice.
    found = build(
        {"kecleon": [area("somewhere-area", "black-2", [slot("dark-grass", 65, 65, 10)])]},
        {"somewhere-area": ("somewhere", "Nature Sanctuary")},
        version="black-2",
        gates={"Nature Sanctuary": "Only by plane"},
    )

    assert found[0].requirement == "Only by plane"


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


def test_a_game_can_call_a_place_what_its_own_players_call_it() -> None:
    # PokeAPI keeps one name per location and it is the newest game's, which is right nearly
    # everywhere and wrong where a place was renamed. Ho-Oh waits on the Bell Tower in HeartGold
    # and on the Tin Tower in Gold, and a Gold player should read the name their game prints.
    api = FakeApi(
        {"ho-oh": [area("bell-tower-roof", "gold", [slot("walk", 40, 40, 100)])]},
        {"bell-tower-roof": ("bell-tower", "Bell Tower")},
    )
    places = LocationNames(api, renamed={"Bell Tower": "Tin Tower"})

    found = wild_encounters(
        api,
        game_id="gold",
        version="gold",
        species=["ho-oh"],
        places=places,
    )

    assert found[0].location == "Tin Tower"
    # Only the location is renamed; what the area adds to it is untouched.
    assert found[0].sub_area == "Roof"
    assert places.of("bell-tower-roof") == ("Tin Tower", "Roof")


def test_a_place_nobody_renamed_comes_through_as_it_is() -> None:
    api = FakeApi(
        {"poochyena": [area("hoenn-route-101-area", "emerald", [slot("walk", 2, 2, 20)])]},
        ROUTE_101,
    )
    places = LocationNames(api, renamed={"Bell Tower": "Tin Tower"})

    assert places.of("hoenn-route-101-area") == ("Route 101", None)


def test_a_hand_written_slot_is_kept_only_if_the_dex_asks_for_it() -> None:
    # A table written by hand can list more than one game wants - the Bug-Catching Contest holds
    # ten species and a dex may ask for eight of them - and the extras are not records.
    slots = (
        RecordedSlot(species="scyther", location="National Park", lowest=13, highest=14),
        RecordedSlot(species="pinsir", location="National Park", lowest=13, highest=14),
    )
    citation = SourceCitation(
        source="bulbapedia",
        url="https://bulbapedia.bulbagarden.net/wiki/Bug-Catching_Contest",
        retrieved_on=TODAY,
    )

    found = recorded_encounters(game_id="gold", slots=slots, species=["scyther"], citation=citation)

    assert [one.target.species for one in found] == ["scyther"]
    assert found[0].levels.minimum == 13
    # And it says where it came from, which is the whole point of writing it down by hand.
    assert found[0].source.source == "bulbapedia"
