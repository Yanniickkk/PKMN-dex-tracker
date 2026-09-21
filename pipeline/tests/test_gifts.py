"""Gifts and statics: what PokeAPI says, and what only the game itself can say.

The split is the point of this step. PokeAPI knows where a Pokemon is handed over and at what
level; it calls a starter, a fossil and a present from a stranger all "gift". Which of the
three it is, who gives it, and what you had to do first come from the game's own table.
"""

from __future__ import annotations

from datetime import date

from livingdex_pipeline.gifts import GiftDetail, gift_encounters
from livingdex_pipeline.models import GiftKind

TODAY = date(2026, 9, 21)


def row(method: str, level: int, conditions: list[str] | None = None) -> dict:
    return {
        "min_level": level,
        "max_level": level,
        "chance": 100,
        "method": {"name": method},
        "condition_values": [{"name": one} for one in (conditions or [])],
    }


def area(name: str, version: str, details: list[dict]) -> dict:
    return {
        "location_area": {"name": name},
        "version_details": [{"version": {"name": version}, "encounter_details": details}],
    }


class FakeApi:
    def __init__(self, encounters: dict[str, list], locations: dict[str, tuple[str, str]]) -> None:
        self._encounters = encounters
        self._locations = locations

    def default_pokemon(self, species: str, *, refresh: bool = False) -> str:
        return f"{species}-normal" if species == "deoxys" else species

    def encounters(self, pokemon: str, *, refresh: bool = False) -> list:
        return self._encounters.get(pokemon, [])

    def resource(self, path: str, *, refresh: bool = False) -> dict:
        if path.startswith("location-area/"):
            area_slug = path.removeprefix("location-area/")
            return {"location": {"name": self._locations[area_slug][0]}}

        location_slug = path.removeprefix("location/")
        name = next(one for one in self._locations.values() if one[0] == location_slug)[1]

        return {"names": [{"language": {"name": "en"}, "name": name}]}


ROUTE_101 = {"hoenn-route-101-area": ("hoenn-route-101", "Route 101")}


def build(
    encounters: dict[str, list],
    locations: dict[str, tuple[str, str]],
    details: dict[str, GiftDetail] | None = None,
    version: str = "emerald",
):
    return gift_encounters(
        FakeApi(encounters, locations),
        game_id="emerald",
        version=version,
        species=[name.removesuffix("-normal") for name in encounters],
        retrieved_on=TODAY,
        details=details,
    )


def test_a_gift_carries_its_place_and_the_one_level_it_comes_at() -> None:
    found = build(
        {"treecko": [area("hoenn-route-101-area", "emerald", [row("gift", 5)])]},
        ROUTE_101,
    )

    assert len(found) == 1
    assert found[0].location == "Route 101"
    assert found[0].level == 5
    assert found[0].target.species == "treecko"


def test_a_gift_is_a_present_from_a_stranger_until_the_game_says_otherwise() -> None:
    # PokeAPI has one word for three things, so the general one is the default.
    plain = build(
        {"castform": [area("hoenn-route-101-area", "emerald", [row("gift", 25)])]},
        ROUTE_101,
    )
    named = build(
        {"treecko": [area("hoenn-route-101-area", "emerald", [row("gift", 5)])]},
        ROUTE_101,
        {"treecko": GiftDetail(kind=GiftKind.STARTER, npc="Professor Birch")},
    )

    assert plain[0].gift_kind is GiftKind.NPC_GIFT
    assert named[0].gift_kind is GiftKind.STARTER
    assert named[0].npc == "Professor Birch"


def test_an_egg_and_a_static_are_told_apart_by_the_method_alone() -> None:
    found = build(
        {
            "wynaut": [area("hoenn-route-101-area", "emerald", [row("gift-egg", 5)])],
            "rayquaza": [area("hoenn-route-101-area", "emerald", [row("static", 70)])],
        },
        ROUTE_101,
    )

    assert {one.target.species: one.gift_kind for one in found} == {
        "wynaut": GiftKind.EGG,
        "rayquaza": GiftKind.STATIC_ENCOUNTER,
    }


def test_the_item_an_encounter_depends_on_becomes_the_requirement() -> None:
    found = build(
        {
            "anorith": [
                area("hoenn-route-101-area", "emerald", [row("gift", 20, ["item-claw-fossil"])])
            ]
        },
        ROUTE_101,
    )

    assert found[0].requirement == "Claw Fossil"


def test_what_the_game_says_first_beats_what_the_conditions_imply() -> None:
    # "Claw Fossil" is true but thin: the game knows where the fossil comes from and that taking
    # one means not taking the other.
    found = build(
        {
            "anorith": [
                area("hoenn-route-101-area", "emerald", [row("gift", 20, ["item-claw-fossil"])])
            ]
        },
        ROUTE_101,
        {"anorith": GiftDetail(requirement="Claw Fossil from the Mirage Tower; only one of two")},
    )

    assert found[0].requirement == "Claw Fossil from the Mirage Tower; only one of two"


def test_a_sub_area_is_read_as_part_of_the_place() -> None:
    # A gift record has one line for where it happens, so the two halves are joined rather than
    # the narrower half being dropped.
    found = build(
        {"beldum": [area("mossdeep-city-stevens-house", "emerald", [row("gift", 5)])]},
        {"mossdeep-city-stevens-house": ("mossdeep-city", "Mossdeep City")},
    )

    assert found[0].location == "Mossdeep City, Stevens House"


def test_a_pokemon_waiting_in_three_places_is_three_records() -> None:
    found = build(
        {
            "electrode": [
                area("new-mauville-area", "emerald", [row("static", 30)]),
                area("team-aqua-hideout-area", "emerald", [row("static", 30)]),
            ]
        },
        {
            "new-mauville-area": ("new-mauville", "New Mauville"),
            "team-aqua-hideout-area": ("team-aqua-hideout", "Aqua Hideout"),
        },
    )

    assert sorted(one.location for one in found) == ["Aqua Hideout", "New Mauville"]


def test_the_same_encounter_listed_twice_is_one_record() -> None:
    found = build(
        {
            "rayquaza": [
                area("hoenn-route-101-area", "emerald", [row("static", 70), row("static", 70)])
            ]
        },
        ROUTE_101,
    )

    assert len(found) == 1


def test_a_distribution_event_is_not_a_way_to_get_one(caplog) -> None:
    # A shop in Japan in 2003 is not somewhere a dex can be filled today.
    found = build(
        {
            "pikachu": [
                area("hoenn-route-101-area", "emerald", [row("colosseum-bonus-disc-jpn", 10)])
            ]
        },
        ROUTE_101,
    )

    assert found == []


def test_wild_slots_are_left_to_their_own_step() -> None:
    found = build(
        {"poochyena": [area("hoenn-route-101-area", "emerald", [row("walk", 2)])]},
        ROUTE_101,
    )

    assert found == []


def test_another_version_is_not_this_game() -> None:
    found = build(
        {"treecko": [area("hoenn-route-101-area", "ruby", [row("gift", 5)])]},
        ROUTE_101,
    )

    assert found == []


def test_a_form_is_asked_for_by_its_species_and_recorded_as_one() -> None:
    # Encounters hang off deoxys-normal; the dex entry is deoxys.
    found = build(
        {"deoxys-normal": [area("hoenn-route-101-area", "emerald", [row("static", 30)])]},
        ROUTE_101,
    )

    assert found[0].target.species == "deoxys"


def test_every_record_says_where_it_came_from() -> None:
    found = build(
        {"treecko": [area("hoenn-route-101-area", "emerald", [row("gift", 5)])]},
        ROUTE_101,
    )

    assert found[0].source.source == "pokeapi"
    assert found[0].source.retrieved_on == TODAY
    assert str(found[0].source.url).endswith("/pokemon/treecko/encounters")
