"""Matching names onto ids, and deciding who wins when sources disagree."""

from __future__ import annotations

import json
from pathlib import Path

from livingdex_pipeline.merge import Merger, default_key
from livingdex_pipeline.normalise import Normaliser, slugify
from livingdex_pipeline.scrape import ScrapedRecord

SPECIES = {"chimchar", "vulpix", "nidoran-f", "nidoran-m", "farfetchd", "mr-mime", "flabebe"}
FORMS = {"vulpix-alola"}


def normaliser() -> Normaliser:
    return Normaliser(SPECIES, FORMS)


def test_slugify_handles_the_spellings_sources_actually_use() -> None:
    assert slugify("Chimchar") == "chimchar"
    assert slugify("Farfetch'd") == "farfetchd"
    assert slugify("Mr. Mime") == "mr-mime"
    assert slugify("Flabébé") == "flabebe"
    assert slugify("Nidoran♀") == "nidoran-female"
    assert slugify("  Ho-Oh  ") == "ho-oh"


def test_the_gender_symbols_land_on_the_right_ids() -> None:
    assert normaliser().species_id("Nidoran♀") == "nidoran-f"
    assert normaliser().species_id("Nidoran♂") == "nidoran-m"


def test_a_name_nothing_matches_is_reported_rather_than_guessed() -> None:
    report = normaliser().normalise_all(["Chimchar", "Missingno.", "Vulpix"])

    assert set(report.matched) == {"Chimchar", "Vulpix"}
    assert report.unmatched == ["Missingno."]
    assert report.ok is False
    assert "1 unmatched" in report.summary()


def test_a_named_form_becomes_a_form_target() -> None:
    target = normaliser().target("Vulpix", "Alola")

    assert target is not None
    assert target.species == "vulpix"
    assert target.form == "vulpix-alola"


def test_an_unknown_form_falls_back_to_the_species_rather_than_inventing_an_id() -> None:
    target = normaliser().target("Vulpix", "Hisui")

    assert target is not None
    assert target.species == "vulpix"
    assert target.form is None


def record(source: str, **fields) -> ScrapedRecord:
    return ScrapedRecord(
        source=source,
        kind="wild",
        game="platinum",
        names={"species": "Starly"},
        fields=fields,
    )


def test_the_more_trusted_source_wins() -> None:
    merger = Merger(["bulbapedia", "serebii"])

    result = merger.merge(
        [
            record("serebii", location="Route 202", rate=40),
            record("bulbapedia", location="Route 202", rate=55),
        ]
    )

    assert len(result.records) == 1
    assert result.records[0].source == "bulbapedia"
    assert result.records[0].fields["rate"] == 55


def test_the_losing_value_is_written_down_rather_than_dropped() -> None:
    merger = Merger(["bulbapedia", "serebii"])

    result = merger.merge(
        [
            record("serebii", location="Route 202", rate=40),
            record("bulbapedia", location="Route 202", rate=55),
        ]
    )

    assert not result.ok
    conflict = result.conflicts[0]
    assert conflict.field_name == "rate"
    assert (conflict.winner, conflict.winning_value) == ("bulbapedia", 55)
    assert (conflict.loser, conflict.losing_value) == ("serebii", 40)
    assert "rate" in conflict.describe()


def test_agreeing_sources_are_not_a_conflict() -> None:
    merger = Merger(["bulbapedia", "serebii"])

    result = merger.merge(
        [
            record("serebii", location="Route 202", rate=55),
            record("bulbapedia", location="Route 202", rate=55),
        ]
    )

    assert result.ok
    assert len(result.records) == 1


def test_a_source_that_is_simply_quiet_about_a_field_is_not_disagreeing() -> None:
    merger = Merger(["bulbapedia", "serebii"])

    result = merger.merge(
        [
            record("serebii", location="Route 202"),
            record("bulbapedia", location="Route 202", rate=55),
        ]
    )

    assert result.ok


def test_records_about_different_things_are_kept_apart() -> None:
    merger = Merger(["bulbapedia"])

    result = merger.merge(
        [
            record("bulbapedia", location="Route 202", rate=55),
            record("bulbapedia", location="Route 203", rate=20),
        ]
    )

    assert len(result.records) == 2
    assert result.ok


def test_an_unregistered_source_ranks_below_every_registered_one() -> None:
    merger = Merger(["bulbapedia", "serebii"])

    assert merger.rank_of("bulbapedia") < merger.rank_of("serebii")
    assert merger.rank_of("serebii") < merger.rank_of("some-blog")


def test_the_conflict_log_lands_beside_the_dataset(tmp_path: Path) -> None:
    merger = Merger(["bulbapedia", "serebii"])
    result = merger.merge(
        [
            record("serebii", location="Route 202", rate=40),
            record("bulbapedia", location="Route 202", rate=55),
        ]
    )

    path = tmp_path / "conflicts.json"
    result.write_conflict_log(path)

    logged = json.loads(path.read_text(encoding="utf-8"))
    assert logged[0]["winner"] == "bulbapedia"
    assert logged[0]["losingValue"] == 40
    assert path.read_bytes().endswith(b"\n")


def test_the_default_key_treats_the_same_slot_from_two_sources_as_one_fact() -> None:
    left = record("bulbapedia", location="Route 202", method="walk", rate=55)
    right = record("serebii", location="Route 202", method="walk", rate=40)

    assert default_key(left) == default_key(right)
