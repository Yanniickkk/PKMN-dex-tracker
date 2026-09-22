"""The build as a whole: what it writes, what it refuses, and what it validates."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from livingdex_pipeline.build import Build, BuildError
from livingdex_pipeline.cli import build_parser, main
from livingdex_pipeline.emit import read_dataset
from livingdex_pipeline.games import BuildContext, GameRegistry
from livingdex_pipeline.models import DatasetIndex, DatasetStamp
from livingdex_pipeline.validate import Dataset, Finding, Severity, validate
from sample_dataset import platinum, sword, write_sample_dataset


def registry_with_platinum() -> GameRegistry:
    registry = GameRegistry()
    registry.register("platinum", lambda _: platinum())
    return registry


def build_for(tmp_path: Path, registry: GameRegistry | None = None) -> Build:
    return Build(
        dataset_root=tmp_path / "dataset",
        cache_root=tmp_path / "cache",
        built_on=date(2026, 9, 21),
        registry=registry or registry_with_platinum(),
    )


def test_building_one_game_needs_the_shared_tables_to_exist_already(tmp_path: Path) -> None:
    with pytest.raises(BuildError) as error:
        build_for(tmp_path).run("platinum")

    assert "shared tables are missing" in str(error.value)


def test_a_game_nothing_knows_how_to_build_is_named(tmp_path: Path) -> None:
    write_sample_dataset(tmp_path / "dataset")

    with pytest.raises(BuildError) as error:
        build_for(tmp_path).run("legends-z-a")

    assert "legends-z-a" in str(error.value)
    assert "platinum" in str(error.value)


def test_building_one_game_leaves_the_other_game_files_untouched(tmp_path: Path) -> None:
    root = tmp_path / "dataset"
    write_sample_dataset(root)
    before = (root / "games" / "sword.json").read_bytes()

    result = build_for(tmp_path).run("platinum")

    assert (root / "games" / "sword.json").read_bytes() == before
    assert (root / "games" / "platinum.json") in result.written


def test_a_single_game_build_keeps_the_index_whole(tmp_path: Path) -> None:
    root = tmp_path / "dataset"
    write_sample_dataset(root)

    build_for(tmp_path).run("platinum")

    index = json.loads((root / "index.json").read_text(encoding="utf-8"))
    assert index["games"] == ["diamond", "emerald", "home", "pearl", "platinum", "shield", "sword"]
    assert index["stamp"]["builtOn"] == "2026-09-21"


def test_a_build_leaves_a_validation_report_behind(tmp_path: Path) -> None:
    root = tmp_path / "dataset"
    write_sample_dataset(root)

    result = build_for(tmp_path).run("platinum")

    report = json.loads((root / "validation.json").read_text(encoding="utf-8"))
    assert report["rulesRun"] == [
        "every-entry-has-a-method",
        "no-evolution-dead-ends",
        "no-breeding-dead-ends",
        "unobtainable-entries-really-are",
        "forms-referenced-exist",
        "version-pairs-name-each-other",
        "transfer-edges-connect-known-games",
        "every-species-has-a-sprite",
        "every-game-has-box-art",
    ]
    assert report["findings"] == []
    assert result.ok


def test_the_committed_sample_passes_its_own_validator(tmp_path: Path) -> None:
    root = tmp_path / "dataset"
    write_sample_dataset(root)

    report = validate(read_dataset(root))

    assert report.ok, [one.describe() for one in report.findings]
    assert "0 error(s)" in report.summary()


def test_a_report_with_no_rules_says_so_rather_than_looking_clean() -> None:
    dataset = Dataset(
        index=DatasetIndex(stamp=DatasetStamp(version="0", built_on=date(2026, 9, 21)), games=[]),
        species=[],
        forms=[],
        evolution_rules=[],
        transfers=[],
        games=[],
    )

    assert "no rules ran" in validate(dataset, []).summary()


def test_the_coverage_report_is_written_beside_the_dataset(tmp_path: Path) -> None:
    root = tmp_path / "dataset"
    write_sample_dataset(root)

    build_for(tmp_path).run("platinum")

    report = json.loads((root / "validation.json").read_text(encoding="utf-8"))
    platinum_coverage = next(one for one in report["coverage"] if one["game"] == "platinum")

    # Four species in the table, and Platinum's living dex reaches all four: Chimchar and
    # Monferno it produces, Vulpix only Sword does, Darkrai nothing does and its dex says why.
    # Counted over the living dex rather than Platinum's own three-entry Pokedex.
    assert platinum_coverage == {
        "game": "platinum",
        "full": 2,
        "partial": 1,
        "missing": 0,
        "unobtainable": 1,
    }


def test_the_validator_reads_what_was_written_not_what_was_in_memory(tmp_path: Path) -> None:
    root = tmp_path / "dataset"
    write_sample_dataset(root)

    seen: list[Dataset] = []

    class Spy:
        name = "spy"

        def check(self, dataset: Dataset):
            seen.append(dataset)
            return []

    build = build_for(tmp_path)
    build.run("platinum")

    report = validate(read_dataset(root), [Spy()])

    assert report.ok
    assert [one.game.id for one in seen[0].games] == [
        "diamond",
        "emerald",
        "home",
        "pearl",
        "platinum",
        "shield",
        "sword",
    ]


def test_an_error_finding_fails_the_report_and_a_warning_does_not() -> None:
    dataset = Dataset(
        index=DatasetIndex(stamp=DatasetStamp(version="0", built_on=date(2026, 9, 21)), games=[]),
        species=[],
        forms=[],
        evolution_rules=[],
        transfers=[],
        games=[],
    )

    class Noisy:
        name = "noisy"

        def check(self, _: Dataset):
            return [
                Finding(rule="noisy", severity=Severity.WARNING, message="hmm"),
                Finding(rule="noisy", severity=Severity.ERROR, message="no", game="platinum"),
            ]

    report = validate(dataset, [Noisy()])

    assert not report.ok
    assert len(report.warnings) == 1
    assert "[platinum]" in report.errors[0].describe()


def test_a_game_can_only_be_registered_once() -> None:
    registry = registry_with_platinum()

    with pytest.raises(ValueError):
        registry.register("platinum", lambda _: platinum())


def test_a_builder_is_told_which_game_and_whether_to_refresh() -> None:
    seen: list[BuildContext] = []
    registry = GameRegistry()

    def builder(context: BuildContext):
        seen.append(context)
        return sword()

    registry.register("sword", builder)
    registry.build(BuildContext(game_id="sword", refresh=True))

    assert seen[0].game_id == "sword"
    assert seen[0].refresh is True


def test_the_cli_parses_a_single_game_build() -> None:
    args = build_parser().parse_args(["build", "--game", "platinum"])

    assert args.command == "build"
    assert args.game == "platinum"
    assert args.refresh is False


def test_the_cli_defaults_to_building_everything() -> None:
    assert build_parser().parse_args(["build"]).game is None


def test_the_cli_requires_a_command() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args([])


def test_the_cli_reports_a_build_failure_without_a_traceback(tmp_path: Path, capsys) -> None:
    exit_code = main(
        [
            "build",
            "--game",
            "platinum",
            "--out",
            str(tmp_path / "dataset"),
            "--cache",
            str(tmp_path),
        ]
    )

    assert exit_code == 2
    assert "build failed" in capsys.readouterr().err
