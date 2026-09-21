"""Each rule, shown firing on the thing it exists to catch."""

from __future__ import annotations

from datetime import date

from livingdex_pipeline.models import (
    AllSpeciesFilter,
    DatasetIndex,
    DatasetStamp,
    DexEntry,
    DexSource,
    DexTarget,
    EvolutionAcquisition,
    EvolutionRule,
    EvolutionTrigger,
    Form,
    FormKind,
    Game,
    GameData,
    GameRelease,
    GiftAcquisition,
    GiftKind,
    PokemonType,
    SourceCitation,
    Species,
    TransferDirection,
    TransferEdge,
    TransferMechanism,
)
from livingdex_pipeline.rules import coverage_for
from livingdex_pipeline.validate import Dataset, Severity, validate

CITATION = SourceCitation(source="test", retrieved_on=date(2026, 9, 21))


def game(game_id: str, entries=(), methods=()) -> GameData:
    return GameData(
        game=Game(
            id=game_id,
            title=game_id,
            version=game_id,
            generation=4,
            region="Sinnoh",
            release=GameRelease.CARTRIDGE,
            national_dex_through=493,
            dex_source=DexSource.NATIONAL_DEX,
        ),
        dex_entries=list(entries),
        acquisition_methods=list(methods),
    )


def entry(
    game_id: str, species: str, number: int, form: str | None = None, reason: str | None = None
):
    return DexEntry(
        game=game_id,
        target=DexTarget(species=species, form=form),
        number=number,
        unobtainable_reason=reason,
    )


def gift(game_id: str, species: str, form: str | None = None) -> GiftAcquisition:
    return GiftAcquisition(
        game=game_id,
        target=DexTarget(species=species, form=form),
        gift_kind=GiftKind.NPC_GIFT,
        location="somewhere",
        source=CITATION,
    )


def dataset(games=(), forms=(), rules=(), transfers=(), species=(), sprites=()) -> Dataset:
    return Dataset(
        index=DatasetIndex(
            stamp=DatasetStamp(version="0", built_on=date(2026, 9, 21)),
            games=[one.game.id for one in games],
        ),
        species=list(species),
        forms=list(forms),
        evolution_rules=list(rules),
        transfers=list(transfers),
        games=list(games),
        sprites=frozenset(sprites),
    )


def messages(report, rule: str) -> list[str]:
    return [one.message for one in report.findings if one.rule == rule]


# --- every dex entry has a method -------------------------------------------------------------


def test_an_entry_nothing_can_produce_is_an_error() -> None:
    report = validate(dataset(games=[game("platinum", entries=[entry("platinum", "chimchar", 4)])]))

    assert not report.ok
    assert "chimchar" in messages(report, "every-entry-has-a-method")[0]


def test_an_entry_with_a_method_here_is_fine() -> None:
    data = dataset(
        games=[
            game(
                "platinum",
                entries=[entry("platinum", "chimchar", 4)],
                methods=[gift("platinum", "chimchar")],
            )
        ]
    )

    assert validate(data).ok


def test_an_entry_only_obtainable_in_another_game_is_still_accounted_for() -> None:
    # Most of a National Dex is like this: you transfer it in, you do not catch it here.
    data = dataset(
        games=[
            game("platinum", entries=[entry("platinum", "bulbasaur", 1)]),
            game("emerald", methods=[gift("emerald", "bulbasaur")]),
        ]
    )

    assert validate(data).ok


def test_an_entry_marked_unobtainable_is_accepted_without_a_method() -> None:
    data = dataset(
        games=[
            game(
                "platinum",
                entries=[entry("platinum", "darkrai", 491, reason="event distribution only")],
            )
        ]
    )

    assert validate(data).ok


# --- no evolution dead ends -------------------------------------------------------------------


def test_evolving_from_something_nothing_can_produce_is_a_dead_end() -> None:
    data = dataset(
        games=[
            game(
                "platinum",
                entries=[entry("platinum", "monferno", 5)],
                methods=[
                    EvolutionAcquisition(
                        game="platinum",
                        target=DexTarget(species="monferno"),
                        rule="chimchar-to-monferno",
                        source=CITATION,
                    )
                ],
            )
        ],
        rules=[
            EvolutionRule(
                id="chimchar-to-monferno",
                **{"from": DexTarget(species="chimchar")},
                to=DexTarget(species="monferno"),
                trigger=EvolutionTrigger.LEVEL_UP,
            )
        ],
    )

    report = validate(data)

    assert not report.ok
    assert "chimchar" in messages(report, "no-evolution-dead-ends")[0]


def test_a_chain_holds_as_long_as_the_first_stage_can_be_got() -> None:
    data = dataset(
        games=[
            game(
                "platinum",
                entries=[entry("platinum", "chimchar", 4), entry("platinum", "monferno", 5)],
                methods=[
                    gift("platinum", "chimchar"),
                    EvolutionAcquisition(
                        game="platinum",
                        target=DexTarget(species="monferno"),
                        rule="chimchar-to-monferno",
                        source=CITATION,
                    ),
                ],
            )
        ],
        rules=[
            EvolutionRule(
                id="chimchar-to-monferno",
                **{"from": DexTarget(species="chimchar")},
                to=DexTarget(species="monferno"),
                trigger=EvolutionTrigger.LEVEL_UP,
            )
        ],
    )

    assert validate(data).ok


def test_pointing_at_a_rule_that_does_not_exist_is_an_error() -> None:
    data = dataset(
        games=[
            game(
                "platinum",
                entries=[entry("platinum", "monferno", 5)],
                methods=[
                    EvolutionAcquisition(
                        game="platinum",
                        target=DexTarget(species="monferno"),
                        rule="no-such-rule",
                        source=CITATION,
                    )
                ],
            )
        ]
    )

    report = validate(data)

    assert "no-such-rule" in " ".join(messages(report, "no-evolution-dead-ends"))


# --- forms referenced exist -------------------------------------------------------------------


def test_a_dex_that_numbers_an_unknown_form_is_an_error() -> None:
    data = dataset(
        games=[
            game(
                "sword",
                entries=[entry("sword", "vulpix", 101, form="vulpix-alola")],
                methods=[gift("sword", "vulpix", form="vulpix-alola")],
            )
        ]
    )

    report = validate(data)

    assert not report.ok
    assert "vulpix-alola" in messages(report, "forms-referenced-exist")[0]


def test_a_form_filed_under_the_wrong_species_is_an_error() -> None:
    data = dataset(
        games=[
            game(
                "sword",
                entries=[entry("sword", "ninetales", 101, form="vulpix-alola")],
                methods=[gift("sword", "ninetales", form="vulpix-alola")],
            )
        ],
        forms=[
            Form(
                id="vulpix-alola",
                species="vulpix",
                name="Alolan",
                kind=FormKind.REGIONAL,
                games=["sword"],
                types=[PokemonType.ICE],
            )
        ],
    )

    report = validate(data)

    assert not report.ok
    assert "belongs to vulpix" in messages(report, "forms-referenced-exist")[0]


def test_a_form_the_table_does_not_place_in_this_game_is_a_warning_not_an_error() -> None:
    # The dex builder would silently drop it, which shortens a dex without saying so.
    data = dataset(
        games=[
            game(
                "sword",
                entries=[entry("sword", "vulpix", 101, form="vulpix-alola")],
                methods=[gift("sword", "vulpix", form="vulpix-alola")],
            )
        ],
        forms=[
            Form(
                id="vulpix-alola",
                species="vulpix",
                name="Alolan",
                kind=FormKind.REGIONAL,
                games=["sun"],
                types=[PokemonType.ICE],
            )
        ],
    )

    report = validate(data)

    assert report.ok
    assert len(report.warnings) == 1
    assert report.warnings[0].severity is Severity.WARNING


# --- transfer edges connect known games -------------------------------------------------------


def test_an_edge_to_a_game_that_is_not_in_the_dataset_is_an_error() -> None:
    data = dataset(
        games=[game("platinum")],
        transfers=[
            TransferEdge(
                **{"from": "emerald"},
                to="platinum",
                mechanism=TransferMechanism.PAL_PARK,
                direction=TransferDirection.ONE_WAY,
                filter=AllSpeciesFilter(),
            )
        ],
    )

    report = validate(data)

    assert not report.ok
    assert "emerald" in messages(report, "transfer-edges-connect-known-games")[0]


def test_an_edge_between_two_known_games_is_fine() -> None:
    data = dataset(
        games=[game("platinum"), game("emerald")],
        transfers=[
            TransferEdge(
                **{"from": "emerald"},
                to="platinum",
                mechanism=TransferMechanism.PAL_PARK,
                direction=TransferDirection.ONE_WAY,
                filter=AllSpeciesFilter(),
            )
        ],
    )

    assert validate(data).ok


# --- coverage ---------------------------------------------------------------------------------


def test_coverage_separates_caught_here_from_a_transfer_away_from_a_hole() -> None:
    data = dataset(
        games=[
            game(
                "platinum",
                entries=[
                    entry("platinum", "chimchar", 4),
                    entry("platinum", "bulbasaur", 1),
                    entry("platinum", "mew", 151),
                    entry("platinum", "darkrai", 491, reason="event distribution only"),
                ],
                methods=[gift("platinum", "chimchar")],
            ),
            game("emerald", methods=[gift("emerald", "bulbasaur")]),
        ]
    )

    platinum = next(one for one in coverage_for(data) if one.game == "platinum")

    assert platinum.full == 1  # chimchar, caught in Sinnoh
    assert platinum.partial == 1  # bulbasaur, a transfer away
    assert platinum.missing == 1  # mew, nothing can produce it
    assert platinum.unobtainable == 1  # darkrai, checked and stated
    assert platinum.total == 4


def test_coverage_is_reported_for_every_game() -> None:
    data = dataset(games=[game("platinum"), game("emerald")])

    assert [one.game for one in coverage_for(data)] == ["platinum", "emerald"]


def test_species_are_not_needed_to_judge_coverage() -> None:
    # Coverage is about acquisition data, not about whether the species table is filled in.
    data = dataset(
        games=[
            game(
                "platinum",
                entries=[entry("platinum", "chimchar", 4)],
                methods=[gift("platinum", "chimchar")],
            )
        ],
        species=[
            Species(
                id="chimchar",
                national_dex_number=390,
                name="Chimchar",
                types=[PokemonType.FIRE],
                evolution_chain="chimchar",
            )
        ],
    )

    assert coverage_for(data)[0].full == 1


# --- every species has a sprite ---------------------------------------------------------------


def _chimchar() -> Species:
    return Species(
        id="chimchar",
        national_dex_number=390,
        name="Chimchar",
        types=[PokemonType.FIRE],
        evolution_chain="chimchar",
    )


def test_a_species_without_a_sprite_is_reported() -> None:
    data = dataset(species=[_chimchar()], sprites=["turtwig"])

    found = messages(validate(data), "every-species-has-a-sprite")

    assert len(found) == 1
    assert "chimchar" in found[0]


def test_a_species_with_a_sprite_is_not_reported() -> None:
    data = dataset(species=[_chimchar()], sprites=["chimchar"])

    assert messages(validate(data), "every-species-has-a-sprite") == []


def test_a_build_that_skipped_sprites_is_not_reported_species_by_species() -> None:
    # --no-sprites is a deliberate quick build. Saying it a thousand times helps nobody.
    data = dataset(species=[_chimchar()], sprites=[])

    assert messages(validate(data), "every-species-has-a-sprite") == []
