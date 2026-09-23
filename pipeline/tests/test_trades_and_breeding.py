"""The two step-5 tables no API answers: who trades, and what the day care lays."""

from __future__ import annotations

from datetime import date

from livingdex_pipeline.breeding import EggFrom, breeding_encounters, day_care_eggs
from livingdex_pipeline.sources import bulbapedia
from livingdex_pipeline.trades import InGameTrade, trade_encounters

RETRIEVED_ON = date(2026, 9, 21)
CITATION = bulbapedia("In-game_trade", retrieved_on=RETRIEVED_ON)


def test_a_trade_records_both_sides_of_it() -> None:
    methods = trade_encounters(
        game_id="emerald",
        trades=[
            InGameTrade(gets="seedot", wants="ralts", location="Rustboro City", npc="Kobe"),
        ],
        citation=CITATION,
    )

    trade = methods[0]
    assert trade.kind == "trade"
    assert trade.target.species == "seedot"
    assert trade.wants.species == "ralts"
    assert trade.location == "Rustboro City"
    assert trade.npc == "Kobe"
    assert trade.requirement is None


def test_trades_keep_the_order_the_game_lists_them_in() -> None:
    methods = trade_encounters(
        game_id="emerald",
        trades=[
            InGameTrade(gets="seedot", wants="ralts", location="Rustboro City"),
            InGameTrade(gets="plusle", wants="volbeat", location="Fortree City"),
        ],
        citation=CITATION,
    )

    assert [one.target.species for one in methods] == ["seedot", "plusle"]


def test_a_citation_points_at_the_article_it_was_read_from() -> None:
    assert CITATION.source == "bulbapedia"
    assert CITATION.url == "https://bulbapedia.bulbagarden.net/wiki/In-game_trade"
    assert CITATION.retrieved_on == RETRIEVED_ON


def test_a_baby_carries_every_parent_that_works() -> None:
    methods = breeding_encounters(
        game_id="emerald",
        day_care="Route 117, Pokemon Day Care",
        eggs={"pichu": EggFrom(parents=("pikachu", "raichu"))},
        citation=CITATION,
    )

    egg = methods[0]
    assert egg.kind == "breeding"
    assert egg.target.species == "pichu"
    assert [parent.species for parent in egg.parents] == ["pikachu", "raichu"]
    assert egg.location == "Route 117, Pokemon Day Care"
    assert egg.requirement is None


def test_a_generation_that_asks_for_an_incense_says_so() -> None:
    methods = breeding_encounters(
        game_id="platinum",
        day_care="Solaceon Town",
        eggs={
            "azurill": EggFrom(
                parents=("marill",),
                requirement="The parent has to be holding a Sea Incense",
            )
        },
        citation=CITATION,
    )

    assert methods[0].requirement == "The parent has to be holding a Sea Incense"


def test_a_trader_who_names_no_price_asks_for_nothing() -> None:
    # Jasmine hands over a Steelix for whatever is in the party. Filling `wants` in with a
    # species would invent a price she never asked for.
    methods = trade_encounters(
        game_id="heartgold",
        trades=[
            InGameTrade(gets="steelix", location="Olivine City, Gym", npc="Jasmine"),
        ],
        citation=CITATION,
    )

    assert methods[0].target.species == "steelix"
    assert methods[0].wants is None


class FakeChains:
    """PokeAPI with the two resources the day care needs: a chain, and a species' sexes."""

    def __init__(self, chains: dict[str, dict], genderless: set[str] | None = None) -> None:
        self._chains = chains
        self._genderless = genderless or set()

    def resource(self, path: str, *, refresh: bool = False) -> dict:
        if path.startswith("evolution-chain/"):
            return self._chains[path.removeprefix("evolution-chain/")]

        name = path.removeprefix("pokemon-species/")
        return {"gender_rate": -1 if name in self._genderless else 4}


def chain(name: str, *into: dict, baby_item: str | None = None) -> dict:
    return {
        "baby_trigger_item": {"name": baby_item} if baby_item else None,
        "chain": _stage(name, *into),
    }


def _stage(name: str, *into: dict) -> dict:
    return {"species": {"name": name}, "evolves_to": list(into)}


def test_the_day_care_is_asked_only_for_what_nothing_else_here_produces() -> None:
    # Vulpix is not in this game and its Ninetales is, so the day care answers for it. Ninetales
    # itself is not asked about: the game already has one.
    api = FakeChains({"vulpix": chain("vulpix", _stage("ninetales"))})

    eggs = day_care_eggs(
        api,
        chains={"vulpix": "vulpix", "ninetales": "vulpix"},
        caught={"ninetales"},
        evolved=set(),
    )

    assert list(eggs) == ["vulpix"]
    assert eggs["vulpix"].parents == ("ninetales",)


def test_an_egg_hatches_into_the_bottom_of_the_chain_and_nothing_higher() -> None:
    # Breeding a Beautifly gives a Wurmple. A Silcoon the game happens not to produce is not
    # something the day care can be asked for, however missing it is.
    api = FakeChains({"wurmple": chain("wurmple", _stage("silcoon", _stage("beautifly")))})
    chains = dict.fromkeys(("wurmple", "silcoon", "beautifly"), "wurmple")

    eggs = day_care_eggs(api, chains=chains, caught={"beautifly"}, evolved=set())

    assert list(eggs) == ["wurmple"]
    assert eggs["wurmple"].parents == ("beautifly",)


def test_a_parent_the_game_cannot_actually_get_is_not_offered_as_one() -> None:
    # The mistake this guards against, and X makes it fifty-six times over: the game knows that
    # a Bayleef becomes a Meganium and has no Chikorita anywhere, so neither of the two is a
    # parent anybody can put in the day care.
    api = FakeChains({"chikorita": chain("chikorita", _stage("bayleef", _stage("meganium")))})
    chains = dict.fromkeys(("chikorita", "bayleef", "meganium"), "chikorita")

    eggs = day_care_eggs(api, chains=chains, caught=set(), evolved={"bayleef", "meganium"})

    assert eggs == {}


def test_a_stage_the_game_evolves_from_something_it_has_counts_as_a_parent() -> None:
    api = FakeChains({"chikorita": chain("chikorita", _stage("bayleef", _stage("meganium")))})
    chains = dict.fromkeys(("chikorita", "bayleef", "meganium"), "chikorita")

    eggs = day_care_eggs(api, chains=chains, caught={"bayleef"}, evolved={"meganium"})

    # Bayleef is caught and Meganium is what it becomes here, so both can be left at the door.
    assert eggs["chikorita"].parents == ("bayleef", "meganium")


def test_the_two_things_a_pair_can_need_are_read_off_the_source() -> None:
    # Neither is a fact somebody keeps a list of: the incense is on the chain, and a species
    # with no sex at all has a gender rate of -1.
    api = FakeChains(
        {
            "bonsly": chain("bonsly", _stage("sudowoodo"), baby_item="rock-incense"),
            "beldum": chain("beldum", _stage("metang")),
        },
        genderless={"beldum"},
    )
    chains = {"bonsly": "bonsly", "sudowoodo": "bonsly", "beldum": "beldum", "metang": "beldum"}

    eggs = day_care_eggs(api, chains=chains, caught={"sudowoodo", "metang"}, evolved=set())

    assert eggs["bonsly"].requirement == "A parent has to hold a Rock Incense"
    assert "Ditto" in eggs["beldum"].requirement
