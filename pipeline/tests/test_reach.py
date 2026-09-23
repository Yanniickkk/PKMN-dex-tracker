"""What a game can reach on its own, and the reason an entry it cannot is owed."""

from __future__ import annotations

from datetime import date

from livingdex_pipeline.models import (
    BreedingAcquisition,
    DexEntry,
    DexSource,
    DexTarget,
    EvolutionAcquisition,
    EvolutionRule,
    EvolutionTrigger,
    Game,
    GameData,
    GameRelease,
    LevelRange,
    SourceCitation,
    WildAcquisition,
)
from livingdex_pipeline.reach import reachable_in, spread_unobtainable

CITATION = SourceCitation(source="test", retrieved_on=date(2026, 9, 23))

RULES = [
    EvolutionRule(
        id="lotad-to-lombre",
        **{"from": DexTarget(species="lotad")},
        to=DexTarget(species="lombre"),
        trigger=EvolutionTrigger.LEVEL_UP,
    ),
    EvolutionRule(
        id="lombre-to-ludicolo",
        **{"from": DexTarget(species="lombre")},
        to=DexTarget(species="ludicolo"),
        trigger=EvolutionTrigger.USE_ITEM,
    ),
]

BY_ID = {rule.id: rule for rule in RULES}


def entry(species: str, number: int, reason: str | None = None) -> DexEntry:
    return DexEntry(
        game="omega-ruby",
        target=DexTarget(species=species),
        number=number,
        unobtainable_reason=reason,
    )


def caught(species: str, *, counts: bool = True) -> WildAcquisition:
    return WildAcquisition(
        game="omega-ruby",
        target=DexTarget(species=species),
        location="Route 102",
        method="walk",
        levels=LevelRange(minimum=5, maximum=5),
        does_not_count=None if counts else "A Friend Safari holds what somebody else decided",
        source=CITATION,
    )


def evolves(rule: str, species: str) -> EvolutionAcquisition:
    return EvolutionAcquisition(
        game="omega-ruby", target=DexTarget(species=species), rule=rule, source=CITATION
    )


def hatches(species: str, *parents: str) -> BreedingAcquisition:
    return BreedingAcquisition(
        game="omega-ruby",
        target=DexTarget(species=species),
        parents=[DexTarget(species=one) for one in parents],
        location="Route 117, Pokemon Day Care",
        source=CITATION,
    )


def game(entries: list[DexEntry], methods: list) -> GameData:
    return GameData(
        game=Game(
            id="omega-ruby",
            title="Pokémon Omega Ruby",
            version="Omega Ruby",
            generation=6,
            region="Hoenn",
            release=GameRelease.CARTRIDGE,
            released=date(2014, 11, 21),
            dex_source=DexSource.NATIONAL_DEX,
        ),
        dex_entries=entries,
        acquisition_methods=methods,
    )


def test_a_line_is_reached_from_its_root_however_the_records_are_ordered() -> None:
    # A Ludicolo needs a Lombre, which needs a Lotad, and the order the records happen to be in
    # says nothing about the order they depend on each other.
    data = game(
        [entry("lotad", 1), entry("lombre", 2), entry("ludicolo", 3)],
        [evolves("lombre-to-ludicolo", "ludicolo"), evolves("lotad-to-lombre", "lombre"),
         caught("lotad")],
    )

    assert reachable_in(data, rules=BY_ID) == {"lotad", "lombre", "ludicolo"}


def test_an_evolution_whose_start_is_not_here_reaches_nothing() -> None:
    data = game(
        [entry("lotad", 1, "Alpha Sapphire only"), entry("lombre", 2), entry("ludicolo", 3)],
        [evolves("lotad-to-lombre", "lombre"), evolves("lombre-to-ludicolo", "ludicolo")],
    )

    assert reachable_in(data, rules=BY_ID) == set()


def test_a_slot_that_does_not_count_does_not_start_a_line() -> None:
    # The Friend Safari is real and a player cannot be sent to use it, so it answers no here
    # for the same reason it answers no to "can I get one in X".
    data = game(
        [entry("lotad", 1), entry("lombre", 2)],
        [caught("lotad", counts=False), evolves("lotad-to-lombre", "lombre")],
    )

    assert reachable_in(data, rules=BY_ID) == set()


def test_a_baby_is_reached_through_a_parent_that_can_be_had() -> None:
    data = game(
        [entry("lotad", 1), entry("lombre", 2)],
        [caught("lombre"), hatches("lotad", "lombre", "ludicolo")],
    )

    assert reachable_in(data, rules=BY_ID) == {"lombre", "lotad"}


def test_the_reason_a_base_carries_is_given_to_the_rest_of_its_line() -> None:
    # The gap this module was written for: the evolution record is true, and no Omega Ruby will
    # ever produce a Lotad, so the Ludicolo entry is as unfillable as the Lotad's.
    data = game(
        [
            entry("lotad", 1, "Alpha Sapphire only in Generation 6; trade one in"),
            entry("lombre", 2),
            entry("ludicolo", 3),
        ],
        [evolves("lotad-to-lombre", "lombre"), evolves("lombre-to-ludicolo", "ludicolo")],
    )

    spread = {one.target.species: one.unobtainable_reason for one in
              spread_unobtainable(data, rules=RULES).dex_entries}

    assert spread == {
        "lotad": "Alpha Sapphire only in Generation 6; trade one in",
        "lombre": "Alpha Sapphire only in Generation 6; trade one in",
        "ludicolo": "Alpha Sapphire only in Generation 6; trade one in",
    }


def test_nothing_is_invented_where_the_line_says_nothing() -> None:
    # An entry whose whole line is unexplained is a game that has not been finished, and
    # `every-entry-has-a-method` says so about all of it rather than about the last stage.
    data = game([entry("lotad", 1), entry("lombre", 2)], [evolves("lotad-to-lombre", "lombre")])

    spread = spread_unobtainable(data, rules=RULES)

    assert all(one.unobtainable_reason is None for one in spread.dex_entries)


def test_an_entry_that_can_be_reached_keeps_its_silence() -> None:
    data = game([entry("lotad", 1), entry("lombre", 2)],
                [caught("lotad"), evolves("lotad-to-lombre", "lombre")])

    spread = spread_unobtainable(data, rules=RULES)

    assert [one.unobtainable_reason for one in spread.dex_entries] == [None, None]
