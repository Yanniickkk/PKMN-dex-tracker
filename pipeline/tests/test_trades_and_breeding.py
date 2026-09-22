"""The two step-5 tables no API answers: who trades, and what the day care lays."""

from __future__ import annotations

from datetime import date

from livingdex_pipeline.breeding import EggFrom, breeding_encounters
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
