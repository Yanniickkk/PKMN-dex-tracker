"""Each rule, shown firing on the thing it exists to catch."""

from __future__ import annotations

from datetime import date

from livingdex_pipeline.models import (
    AllSpeciesFilter,
    BreedingAcquisition,
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
            released=date(2000, 1, 1),
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
    # One gap in a game that has other methods: the entry is named, because that is what a gap
    # needs to be findable.
    data = dataset(
        games=[
            game(
                "platinum",
                entries=[entry("platinum", "chimchar", 4), entry("platinum", "starly", 16)],
                methods=[gift("platinum", "starly")],
            )
        ]
    )

    report = validate(data)

    assert not report.ok
    assert "chimchar" in messages(report, "every-entry-has-a-method")[0]


def test_a_game_nothing_can_be_obtained_in_is_reported_once() -> None:
    # A dex list written before its encounters - which is how Phase 2 goes - should read as one
    # unfinished game rather than as two hundred separate faults.
    data = dataset(
        games=[
            game(
                "platinum",
                entries=[entry("platinum", "chimchar", 4), entry("platinum", "starly", 16)],
            )
        ]
    )

    report = validate(data)
    found = messages(report, "every-entry-has-a-method")

    assert not report.ok
    assert len(found) == 1
    assert "have not been gathered yet" in found[0]
    assert "2 of its 2 dex entries" in found[0]


def test_a_game_without_encounters_is_still_reported_once_when_another_game_covers_some() -> None:
    # The Kanto dex is the case: a third of its 151 are caught in Hoenn as well, so a FireRed
    # with no encounters yet is not a game where *nothing* can be explained. It is still one
    # unfinished game, and it should read as one.
    data = dataset(
        games=[
            game(
                "emerald",
                entries=[entry("emerald", "pikachu", 1)],
                methods=[gift("emerald", "pikachu")],
            ),
            game(
                "firered",
                entries=[entry("firered", "pikachu", 25), entry("firered", "mew", 151)],
            ),
        ]
    )

    report = validate(data)
    found = messages(report, "every-entry-has-a-method")

    assert not report.ok
    assert len(found) == 1
    # One entry of the two has a source elsewhere; the sentence says so rather than claiming
    # nothing does.
    assert "1 of its 2 dex entries" in found[0]


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
    #
    # Platinum hands over a Turtwig of its own as well, and that is not decoration: a game with
    # a dex and no way to fill any of it is unfinished whatever else covers its species, and
    # the rule says so separately.
    data = dataset(
        games=[
            game(
                "platinum",
                entries=[entry("platinum", "bulbasaur", 1), entry("platinum", "turtwig", 387)],
                methods=[gift("platinum", "turtwig")],
            ),
            game("emerald", methods=[gift("emerald", "bulbasaur")]),
        ]
    )

    assert validate(data).ok


def test_an_entry_marked_unobtainable_is_accepted_without_a_method() -> None:
    data = dataset(
        games=[
            game(
                "platinum",
                entries=[
                    entry("platinum", "darkrai", 491, reason="event distribution only"),
                    entry("platinum", "turtwig", 387),
                ],
                methods=[gift("platinum", "turtwig")],
            )
        ]
    )

    assert validate(data).ok


def test_a_game_with_a_dex_and_nothing_to_fill_it_with_is_not_finished() -> None:
    # Red found this. Every one of its 151 entries is caught in some later game, so nothing was
    # missing from the dataset and the rule had nothing to say - about a game that brought no
    # encounters at all. "Validation green" is what step 8 reads as proof a game is done.
    data = dataset(
        games=[
            game("red", entries=[entry("red", "bulbasaur", 1)]),
            game("emerald", methods=[gift("emerald", "bulbasaur")]),
        ]
    )

    report = validate(data)

    assert not report.ok
    said = messages(report, "every-entry-has-a-method")[0]
    assert "no way to obtain anything at all" in said
    # And it says which of the two kinds of gap this is: nothing missing, everything borrowed.
    assert "0 of its 1 dex entries have no source" in said
    assert "other 1 are only covered by other games" in said


# --- no evolution dead ends -------------------------------------------------------------------


def test_evolving_from_something_nothing_can_produce_is_a_dead_end() -> None:
    data = dataset(
        games=[
            game(
                "platinum",
                # Chimchar is in the dex and nothing produces one, so the dataset should have
                # had an answer about it and does not.
                entries=[entry("platinum", "chimchar", 4), entry("platinum", "monferno", 5)],
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


def test_a_stated_reason_is_an_answer_rather_than_a_dead_end() -> None:
    data = dataset(
        games=[
            game(
                "emerald",
                entries=[
                    # Checked, and it is not in this game. The transfer graph is how it arrives.
                    entry(
                        "emerald",
                        "meditite",
                        1,
                        reason="Ruby and Sapphire only in Generation 3; trade one in",
                    ),
                    entry("emerald", "medicham", 2),
                ],
                methods=[
                    EvolutionAcquisition(
                        game="emerald",
                        target=DexTarget(species="medicham"),
                        rule="meditite-to-medicham",
                        source=CITATION,
                    )
                ],
            )
        ],
        rules=[
            EvolutionRule(
                id="meditite-to-medicham",
                **{"from": DexTarget(species="meditite")},
                to=DexTarget(species="medicham"),
                trigger=EvolutionTrigger.LEVEL_UP,
            )
        ],
    )

    assert validate(data).ok


def test_a_previous_stage_the_dex_asks_for_and_nothing_produces_is_a_dead_end() -> None:
    data = dataset(
        games=[
            game(
                "emerald",
                # Meditite is in the dex with nothing said about it, and nothing produces one:
                # somebody has to have looked and did not.
                entries=[entry("emerald", "meditite", 1), entry("emerald", "medicham", 2)],
                methods=[
                    EvolutionAcquisition(
                        game="emerald",
                        target=DexTarget(species="medicham"),
                        rule="meditite-to-medicham",
                        source=CITATION,
                    )
                ],
            )
        ],
        rules=[
            EvolutionRule(
                id="meditite-to-medicham",
                **{"from": DexTarget(species="meditite")},
                to=DexTarget(species="medicham"),
                trigger=EvolutionTrigger.LEVEL_UP,
            )
        ],
    )

    report = validate(data)

    assert not report.ok
    assert "meditite" in messages(report, "no-evolution-dead-ends")[0]


def test_a_previous_stage_no_dex_anywhere_asks_for_is_a_generation_nobody_has_built() -> None:
    # A game records evolutions for every species its living dex reaches, so Ruby knows how to
    # finish a Bayleef long before anything in the dataset can produce a Chikorita. Worth
    # saying, not worth failing a build over, and said once rather than once per chain.
    data = dataset(
        games=[
            game(
                "emerald",
                entries=[entry("emerald", "medicham", 2)],
                methods=[
                    EvolutionAcquisition(
                        game="emerald",
                        target=DexTarget(species="medicham"),
                        rule="meditite-to-medicham",
                        source=CITATION,
                    )
                ],
            )
        ],
        rules=[
            EvolutionRule(
                id="meditite-to-medicham",
                **{"from": DexTarget(species="meditite")},
                to=DexTarget(species="medicham"),
                trigger=EvolutionTrigger.LEVEL_UP,
            )
        ],
    )

    report = validate(data)

    assert report.ok
    assert "has not been built" in messages(report, "no-evolution-dead-ends")[0]


# --- no breeding dead ends --------------------------------------------------------------------


def test_a_baby_whose_parents_cannot_be_had_is_an_error() -> None:
    data = dataset(
        games=[
            game(
                "platinum",
                # Both parents are in the dex and nothing produces either: a hole, not a
                # generation nobody has built.
                entries=[
                    entry("platinum", "pichu", 1),
                    entry("platinum", "pikachu", 2),
                    entry("platinum", "raichu", 3),
                ],
                methods=[
                    BreedingAcquisition(
                        game="platinum",
                        target=DexTarget(species="pichu"),
                        parents=[DexTarget(species="pikachu"), DexTarget(species="raichu")],
                        location="Solaceon Town",
                        source=CITATION,
                    )
                ],
            )
        ]
    )

    report = validate(data)

    assert not report.ok
    assert "pikachu or raichu" in messages(report, "no-breeding-dead-ends")[0]


def test_one_parent_being_obtainable_is_enough() -> None:
    data = dataset(
        games=[
            game(
                "platinum",
                entries=[entry("platinum", "pichu", 1)],
                methods=[
                    # Raichu is not here, and does not have to be: one parent at the day care
                    # lays the egg.
                    gift("platinum", "pikachu"),
                    BreedingAcquisition(
                        game="platinum",
                        target=DexTarget(species="pichu"),
                        parents=[DexTarget(species="pikachu"), DexTarget(species="raichu")],
                        location="Solaceon Town",
                        source=CITATION,
                    ),
                ],
            )
        ]
    )

    assert validate(data).ok


# --- version pairs name each other ------------------------------------------------------------


def paired(game_id: str, partner: str | None):
    data = game(game_id)
    return data.model_copy(update={"game": data.game.model_copy(update={"pair_partner": partner})})


def test_two_halves_that_name_each_other_are_fine() -> None:
    assert validate(dataset(games=[paired("ruby", "sapphire"), paired("sapphire", "ruby")])).ok


def test_a_half_whose_partner_is_not_in_the_dataset_is_an_error() -> None:
    report = validate(dataset(games=[paired("ruby", "sapphire")]))

    assert not report.ok
    assert "not a game in the dataset" in messages(report, "version-pairs-name-each-other")[0]


def test_a_partner_that_names_somebody_else_is_an_error() -> None:
    data = dataset(
        games=[paired("ruby", "sapphire"), paired("sapphire", "emerald"), paired("emerald", None)]
    )

    report = validate(data)

    assert not report.ok
    assert "names emerald" in messages(report, "version-pairs-name-each-other")[0]


def test_a_game_cannot_be_its_own_other_half() -> None:
    report = validate(dataset(games=[paired("ruby", "ruby")]))

    assert "its own pair partner" in messages(report, "version-pairs-name-each-other")[0]


# --- unobtainable entries really are ----------------------------------------------------------


def test_an_entry_the_game_can_evolve_into_must_not_claim_it_cannot() -> None:
    data = dataset(
        games=[
            game(
                "ruby",
                entries=[
                    entry("ruby", "shuppet", 1),
                    # Wrong: this game catches Shuppet and evolves one.
                    entry("ruby", "banette", 2, reason="Sapphire only in Generation 3"),
                ],
                methods=[
                    gift("ruby", "shuppet"),
                    EvolutionAcquisition(
                        game="ruby",
                        target=DexTarget(species="banette"),
                        rule="shuppet-to-banette",
                        source=CITATION,
                    ),
                ],
            )
        ],
        rules=[
            EvolutionRule(
                id="shuppet-to-banette",
                **{"from": DexTarget(species="shuppet")},
                to=DexTarget(species="banette"),
                trigger=EvolutionTrigger.LEVEL_UP,
            )
        ],
    )

    report = validate(data)

    assert not report.ok
    assert "banette" in messages(report, "unobtainable-entries-really-are")[0]


def test_an_evolution_whose_earlier_stage_is_out_of_reach_is_left_alone() -> None:
    # Emerald evolves a Medicham from a Meditite it cannot catch. Both statements are true and
    # neither is a mistake, so this rule must not fire on them.
    data = dataset(
        games=[
            game(
                "emerald",
                entries=[
                    entry("emerald", "meditite", 1, reason="Ruby and Sapphire only"),
                    entry("emerald", "medicham", 2, reason="Ruby and Sapphire only"),
                ],
                methods=[
                    EvolutionAcquisition(
                        game="emerald",
                        target=DexTarget(species="medicham"),
                        rule="meditite-to-medicham",
                        source=CITATION,
                    )
                ],
            )
        ],
        rules=[
            EvolutionRule(
                id="meditite-to-medicham",
                **{"from": DexTarget(species="meditite")},
                to=DexTarget(species="medicham"),
                trigger=EvolutionTrigger.LEVEL_UP,
            )
        ],
    )

    assert validate(data).ok


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


def national_dex(*entries: tuple[int, str]) -> list[Species]:
    return [
        Species(
            id=name,
            national_dex_number=number,
            name=name.title(),
            types=[PokemonType.FIRE],
            evolution_chain=name,
        )
        for number, name in entries
    ]


def test_coverage_separates_caught_here_from_a_transfer_away_from_a_hole() -> None:
    data = dataset(
        games=[
            game(
                "platinum",
                entries=[entry("platinum", "darkrai", 491, reason="event distribution only")],
                methods=[gift("platinum", "chimchar")],
            ),
            game("emerald", methods=[gift("emerald", "bulbasaur")]),
        ],
        species=national_dex((1, "bulbasaur"), (151, "mew"), (390, "chimchar"), (491, "darkrai")),
    )

    platinum = next(one for one in coverage_for(data) if one.game == "platinum")

    assert platinum.full == 1  # chimchar, caught in Sinnoh
    assert platinum.partial == 1  # bulbasaur, a transfer away
    assert platinum.missing == 1  # mew, nothing can produce it
    assert platinum.unobtainable == 1  # darkrai, checked and stated
    assert platinum.total == 4


def test_coverage_counts_what_the_player_fills_rather_than_the_games_own_dex() -> None:
    # Bulbasaur is not in Platinum's Pokedex and Platinum hands one over anyway. Counting the
    # Pokedex called that nothing; counting the living dex calls it what it is.
    data = dataset(
        games=[
            game(
                "platinum",
                entries=[entry("platinum", "chimchar", 4)],
                methods=[gift("platinum", "chimchar"), gift("platinum", "bulbasaur")],
            )
        ],
        species=national_dex((1, "bulbasaur"), (390, "chimchar")),
    )

    assert coverage_for(data)[0].full == 2


def test_coverage_is_reported_for_every_game() -> None:
    data = dataset(games=[game("platinum"), game("emerald")])

    assert [one.game for one in coverage_for(data)] == ["platinum", "emerald"]


def test_a_game_with_no_national_dex_is_judged_on_the_dex_it_has() -> None:
    # None yet, but the rule has to answer for one: its grid is its own Pokedex and the species
    # table has nothing to say about how far it reaches.
    data = dataset(
        games=[
            GameData(
                game=Game(
                    id="colosseum",
                    title="colosseum",
                    version="colosseum",
                    released=date(2000, 1, 1),
                    generation=3,
                    region="Orre",
                    release=GameRelease.CARTRIDGE,
                    national_dex_through=None,
                    dex_source=DexSource.GAME_DEX,
                ),
                dex_entries=[entry("colosseum", "chimchar", 1)],
                acquisition_methods=[gift("colosseum", "chimchar")],
            )
        ],
        species=national_dex((1, "bulbasaur"), (390, "chimchar")),
    )

    assert coverage_for(data)[0].total == 1


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
