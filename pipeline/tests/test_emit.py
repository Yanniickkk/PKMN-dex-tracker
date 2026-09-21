"""The dataset as it lands on disk."""

from __future__ import annotations

import filecmp
import json
from pathlib import Path

from livingdex_pipeline.emit import DatasetWriter, read_dataset, stamp_for
from sample_dataset import write_sample_dataset

FIXTURE_DIR = Path(__file__).parent / "expected" / "sample-dataset"


def test_the_committed_sample_is_what_the_writer_produces(tmp_path: Path) -> None:
    """The fixture a C# test reads is regenerated here, so the two cannot drift apart.

    If this fails after a deliberate schema change, regenerate the fixture:
        python -c "import sys; sys.path.insert(0, 'pipeline/tests'); \
from pathlib import Path; from sample_dataset import write_sample_dataset; \
write_sample_dataset(Path('pipeline/tests/expected/sample-dataset'))"
    """
    write_sample_dataset(tmp_path)

    expected = sorted(path.relative_to(FIXTURE_DIR) for path in FIXTURE_DIR.rglob("*.json"))
    produced = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*.json"))
    assert produced == expected

    mismatched = [
        str(name)
        for name in expected
        if not filecmp.cmp(FIXTURE_DIR / name, tmp_path / name, shallow=False)
    ]
    assert not mismatched, f"the committed sample is out of date: {mismatched}"


def test_json_is_diffable(tmp_path: Path) -> None:
    write_sample_dataset(tmp_path)
    raw = (tmp_path / "species.json").read_bytes()

    # Committed output: LF endings, two-space indent, trailing newline.
    assert b"\r\n" not in raw
    assert raw.endswith(b"\n")
    assert b'\n  {\n    "id"' in raw


def test_absent_fields_are_left_out_rather_than_written_as_null(tmp_path: Path) -> None:
    write_sample_dataset(tmp_path)
    forms = json.loads((tmp_path / "forms.json").read_text(encoding="utf-8"))

    alolan = next(one for one in forms if one["id"] == "vulpix-alola")
    female = next(one for one in forms if one["id"] == "pikachu-female")

    assert alolan["types"] == ["ice"]
    assert "types" not in female


def test_a_dex_target_names_its_form_only_when_it_has_one(tmp_path: Path) -> None:
    write_sample_dataset(tmp_path)
    sword = json.loads((tmp_path / "games" / "sword.json").read_text(encoding="utf-8"))

    base, form = sword["dexEntries"]
    assert base["target"] == {"species": "vulpix"}
    assert form["target"] == {"species": "vulpix", "form": "vulpix-alola"}


def test_reserved_words_are_written_the_way_the_schema_spells_them(tmp_path: Path) -> None:
    write_sample_dataset(tmp_path)
    transfers = json.loads((tmp_path / "transfers.json").read_text(encoding="utf-8"))

    pal_park = next(one for one in transfers if one["mechanism"] == "palPark")

    # "from" is a Python keyword; it must still be "from" on disk.
    assert pal_park["from"] == "emerald"
    assert pal_park["filter"] == {"filter": "nationalDexRange", "from": 1, "to": 386}


def test_writing_one_game_leaves_the_others_alone(tmp_path: Path) -> None:
    write_sample_dataset(tmp_path)
    before = (tmp_path / "games" / "sword.json").read_bytes()

    from sample_dataset import platinum

    DatasetWriter(tmp_path).write_game(platinum())

    assert (tmp_path / "games" / "sword.json").read_bytes() == before


def test_the_index_lists_the_games_and_stamps_the_build(tmp_path: Path) -> None:
    write_sample_dataset(tmp_path)
    index = json.loads((tmp_path / "index.json").read_text(encoding="utf-8"))

    assert index["games"] == ["platinum", "sword"]
    assert index["stamp"] == {"version": "0.1.0-sample", "builtOn": "2026-09-21"}


def test_known_games_finds_what_is_already_built(tmp_path: Path) -> None:
    write_sample_dataset(tmp_path)

    assert DatasetWriter(tmp_path).known_games() == ["platinum", "sword"]


def test_what_is_written_can_be_read_back(tmp_path: Path) -> None:
    write_sample_dataset(tmp_path)

    dataset = read_dataset(tmp_path)

    assert [one.id for one in dataset.species] == ["vulpix", "chimchar", "monferno"]
    assert [one.game.id for one in dataset.games] == ["platinum", "sword"]
    assert dataset.games[0].acquisition_methods[0].kind == "gift"
    assert dataset.transfers[2].filter.filter == "presentInTargetDex"


def test_a_stamp_defaults_to_today() -> None:
    from datetime import date

    assert stamp_for("1.0.0").built_on == date.today()


def test_sprites_land_beside_the_dataset(tmp_path: Path) -> None:
    writer = DatasetWriter(tmp_path)

    path = writer.write_sprite("chimchar.png", b"\x89PNG-not-really")

    assert path == tmp_path / "sprites" / "chimchar.png"
    assert path.read_bytes() == b"\x89PNG-not-really"


def test_the_sprite_url_is_keyed_by_national_dex_number() -> None:
    from livingdex_pipeline.pokeapi import PokeApiClient

    url = PokeApiClient.sprite_url(None, 390)  # type: ignore[arg-type]

    assert url.endswith("/390.png")
