"""Gifts and statics: what PokeAPI says, and what only the game itself can say.

The split is the point of this step. PokeAPI knows where a Pokemon is handed over and at what
level; it calls a starter, a fossil and a present from a stranger all "gift". Which of the
three it is, who gives it, and what you had to do first come from the game's own table.
"""

from __future__ import annotations

import logging
from datetime import date

from livingdex_pipeline.gifts import GiftDetail, gift_encounters
from livingdex_pipeline.models import Form, FormKind, GiftKind

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
        #: species -> extra (pokemon, is_default=False) pairs, for the tests that need one.
        self.extra_varieties: dict[str, list[tuple[str, bool]]] = {}

    def retrieved_on(self, url: str) -> date:
        """The day the cache says this url was fetched, which a citation carries."""
        return TODAY

    def default_pokemon(self, species: str, *, refresh: bool = False) -> str:
        return f"{species}-normal" if species == "deoxys" else species

    def varieties(self, species: str, *, refresh: bool = False) -> list[tuple[str, bool]]:
        """Every Pokemon of a species. The fakes hold one each unless a test says otherwise."""
        return [(self.default_pokemon(species), True), *self.extra_varieties.get(species, [])]

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
    details: dict[str, GiftDetail | tuple[GiftDetail, ...]] | None = None,
    version: str = "emerald",
    excluded: dict[str, str] | None = None,
):
    return gift_encounters(
        FakeApi(encounters, locations),
        game_id="emerald",
        version=version,
        species=[name.removesuffix("-normal") for name in encounters],
        details=details,
        excluded=excluded,
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


def test_a_game_that_knows_the_level_better_than_the_source_says_so() -> None:
    # The last thing a game was given the right to correct, and the Let's Go pair is why: two
    # other sources agree with each other against PokeAPI about four of that pair's gifts, and
    # one of the four is an Electrode at exactly the level the Electrode in the same room was
    # in Red and Blue. Every other game leaves this out and keeps what the row says.
    kept = build(
        {"electrode": [area("hoenn-route-101-area", "emerald", [row("static", 43)])]},
        ROUTE_101,
    )
    corrected = build(
        {"electrode": [area("hoenn-route-101-area", "emerald", [row("static", 43)])]},
        ROUTE_101,
        {"electrode": GiftDetail(level=42)},
    )

    assert kept[0].level == 43
    assert corrected[0].level == 42


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


def test_a_gift_another_game_sends_over_is_not_this_game_handing_it_over(caplog) -> None:
    # Manaphy hatches in Sinnoh from an egg a Pokemon Ranger cartridge sends across. That is a
    # fact about two games and a wireless link, not about anything standing in the grass.
    caplog.set_level(logging.INFO)
    found = build(
        {"manaphy": [area("hoenn-route-101-area", "emerald", [row("pokemon-ranger", 1)])]},
        ROUTE_101,
    )

    assert found == []
    assert "another game" in caplog.text


def test_a_source_that_is_wrong_about_a_version_can_be_told_so(caplog) -> None:
    # PokeAPI files both Sinnoh fossils under both halves of the pair. Only Diamond's
    # Underground holds a Skull Fossil, so the row Pearl was given is not Pearl's.
    caplog.set_level(logging.INFO)
    found = build(
        {
            "cranidos": [
                area("hoenn-route-101-area", "emerald", [row("gift", 20, ["item-skull-fossil"])])
            ]
        },
        ROUTE_101,
        excluded={"cranidos": "the Skull Fossil is only in the other half's Underground"},
    )

    assert found == []
    assert "other half" in caplog.text


def test_a_condition_that_is_not_an_item_is_still_carried() -> None:
    # Two bare facts where a player wants one sentence - but dropping them is worse, and that
    # is what used to happen to everything that was not an item.
    found = build(
        {
            "drifloon": [
                area(
                    "hoenn-route-101-area",
                    "emerald",
                    [row("static", 22, ["weekday-friday", "story-progress-defeat-mars"])],
                )
            ]
        },
        ROUTE_101,
    )

    assert found[0].requirement == ("On a Friday and after Mars is beaten at the Valley Windworks")


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


def test_one_species_handed_over_in_two_places_can_be_described_once_per_place() -> None:
    # Johto is where this became necessary: Bill hands over an Eevee in Goldenrod and the
    # Celadon Game Corner sells one for coins. A table keyed by species alone would have put
    # "From: Bill" on a slot machine prize.
    found = build(
        {
            "eevee": [
                area("goldenrod-city-bills-house", "heartgold", [row("gift", 5)]),
                area("celadon-city-prize-corner", "heartgold", [row("gift", 15, ["coins-6666"])]),
            ]
        },
        {
            "goldenrod-city-bills-house": ("goldenrod-city", "Goldenrod City"),
            "celadon-city-prize-corner": ("celadon-city", "Celadon City"),
        },
        {
            "eevee": (
                GiftDetail(npc="Bill", where="Goldenrod City, Bills House"),
                GiftDetail(),
            )
        },
        version="heartgold",
    )

    by_place = {one.location: one for one in found}

    assert by_place["Goldenrod City, Bills House"].npc == "Bill"
    assert by_place["Celadon City, Prize Corner"].npc is None
    # And the one with nothing of its own still reads what the conditions say.
    assert by_place["Celadon City, Prize Corner"].requirement == "Game Corner prize, 6666 coins"


def test_a_description_that_fits_nowhere_is_said_out_loud(caplog) -> None:
    # A place renamed or a gift moved leaves a table describing somewhere that no longer exists,
    # and a silent miss is a sentence nobody notices has stopped being printed.
    found = build(
        {"eevee": [area("goldenrod-city-bills-house", "heartgold", [row("gift", 5)])]},
        {"goldenrod-city-bills-house": ("goldenrod-city", "Goldenrod City")},
        {"eevee": (GiftDetail(npc="Bill", where="Somewhere Else"),)},
        version="heartgold",
    )

    assert found[0].npc is None
    assert "which its gift table does not describe" in caplog.text


def test_a_gift_can_belong_to_a_form_rather_than_to_the_species() -> None:
    # What stands on Exeggutor Island is the Alolan Exeggutor, and the Kantonian one is trade-only
    # in these games. A record saying "Exeggutor" would name the wrong tree.
    api = FakeApi(
        {
            "exeggutor-alola": [
                area("exeggutor-island-area", "sun", [row("static", 40)]),
            ]
        },
        {"exeggutor-island-area": ("exeggutor-island", "Exeggutor Island")},
    )
    api.extra_varieties["exeggutor"] = [("exeggutor-alola", False)]

    found = gift_encounters(
        api,
        game_id="sun",
        version="sun",
        species=["exeggutor"],
        forms=[
            Form(
                id="exeggutor-alola",
                species="exeggutor",
                name="Alola",
                kind=FormKind.REGIONAL,
                games=["sun"],
            )
        ],
    )

    assert len(found) == 1
    assert found[0].target.species == "exeggutor"
    assert found[0].target.form == "exeggutor-alola"


def test_a_game_that_passes_no_forms_is_handed_only_the_default() -> None:
    # Which is every game written before Alola, and none of them loses a record by it.
    api = FakeApi(
        {"exeggutor-alola": [area("exeggutor-island-area", "sun", [row("static", 40)])]},
        {"exeggutor-island-area": ("exeggutor-island", "Exeggutor Island")},
    )
    api.extra_varieties["exeggutor"] = [("exeggutor-alola", False)]

    assert gift_encounters(api, game_id="sun", version="sun", species=["exeggutor"]) == []
