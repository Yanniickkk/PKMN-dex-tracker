"""Which battle sprites a game gets, and where they land."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from livingdex_pipeline.build import Build
from livingdex_pipeline.emit import DatasetWriter, read_species
from livingdex_pipeline.http import PoliteClient
from livingdex_pipeline.models import (
    DexEntry,
    DexSource,
    DexTarget,
    Game,
    GameData,
    GameRelease,
    PokemonType,
    Species,
)
from livingdex_pipeline.pokeapi import PokeApiClient


def api() -> PokeApiClient:
    # Never asked for anything: the URL is built from the number, not fetched.
    return PokeApiClient(PoliteClient(Path("unused")))


def species(*entries: tuple[int, str]) -> list[Species]:
    return [
        Species(
            id=name,
            national_dex_number=number,
            name=name.title(),
            types=[PokemonType.NORMAL],
            evolution_chain=name,
        )
        for number, name in entries
    ]


def game(sprite_set: str | None = None, reach: int | None = 386, entries=()) -> GameData:
    return GameData(
        game=Game(
            id="emerald",
            title="Pokemon Emerald Version",
            version="Emerald",
            generation=3,
            region="Hoenn",
            release=GameRelease.CARTRIDGE,
            national_dex_through=reach,
            dex_source=DexSource.NATIONAL_DEX if reach else DexSource.GAME_DEX,
            sprite_set=sprite_set,
        ),
        dex_entries=[
            DexEntry(game="emerald", target=DexTarget(species=name), number=number)
            for number, name in entries
        ],
    )


# --- where a sprite comes from ----------------------------------------------------------------


def test_without_a_set_a_sprite_is_the_current_artwork() -> None:
    assert api().sprite_url(25).endswith("/sprites/pokemon/25.png")


def test_a_set_asks_for_that_generation_s_own_sprite() -> None:
    url = api().sprite_url(25, "generation-iii/emerald")

    assert url.endswith("/sprites/pokemon/versions/generation-iii/emerald/25.png")


# --- how far a set reaches --------------------------------------------------------------------


def test_a_national_dex_reaches_as_far_as_it_says() -> None:
    table = species((1, "bulbasaur"), (386, "deoxys"), (387, "turtwig"))

    # Emerald's National Dex stops at 386, and so does the sheet its sprites were drawn on.
    assert [one.id for one in Build._species_of(game(reach=386), table)] == [
        "bulbasaur",
        "deoxys",
    ]


def test_a_game_without_a_national_dex_gets_only_what_its_own_dex_lists() -> None:
    table = species((1, "bulbasaur"), (25, "pikachu"), (386, "deoxys"))
    data = game(reach=None, entries=((1, "pikachu"),))

    assert [one.id for one in Build._species_of(data, table)] == ["pikachu"]


# --- where it lands ---------------------------------------------------------------------------


def test_a_set_writes_into_a_directory_of_its_own(tmp_path: Path) -> None:
    writer = DatasetWriter(tmp_path)

    shared = writer.write_sprite("pikachu.png", b"shared")
    own = writer.write_sprite("generation-iii/emerald/pikachu.png", b"emerald")

    assert shared.read_bytes() == b"shared"
    assert own.read_bytes() == b"emerald"
    # Side by side rather than one on top of the other: the shared set is the fallback.
    assert own.parent == tmp_path / "sprites" / "generation-iii" / "emerald"


def test_a_missing_species_table_is_not_a_reason_to_fetch_anything(tmp_path: Path) -> None:
    assert read_species(tmp_path) == []


def test_the_species_table_reads_back_from_disk(tmp_path: Path) -> None:
    DatasetWriter(tmp_path).write_species(species((25, "pikachu")))

    assert [one.id for one in read_species(tmp_path)] == ["pikachu"]


def test_a_build_with_no_sprite_set_fetches_nothing(tmp_path: Path) -> None:
    DatasetWriter(tmp_path).write_species(species((25, "pikachu")))
    build = Build(dataset_root=tmp_path, cache_root=tmp_path / "cache", built_on=date(2026, 9, 21))

    # A client that would raise if it were used: a game with no set of its own asks for nothing.
    assert (
        build._fetch_game_sprites(api(), None, [game(sprite_set=None)], DatasetWriter(tmp_path))
        == []
    )
