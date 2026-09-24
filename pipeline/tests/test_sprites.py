"""Which battle sprites a game gets, and where they land."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import httpx

from livingdex_pipeline.build import Build
from livingdex_pipeline.emit import DatasetWriter, read_species
from livingdex_pipeline.http import PoliteClient
from livingdex_pipeline.models import (
    DexEntry,
    DexSource,
    DexTarget,
    Form,
    FormKind,
    Game,
    GameData,
    GameRelease,
    PokemonType,
    Species,
)
from livingdex_pipeline.pokeapi import PokeApiClient


class Counting:
    """A client that remembers what it was asked for and has nothing to hand back.

    Every miss is logged and skipped by the caller, so a build survives it - which is what
    makes this usable for counting requests rather than serving them.
    """

    def __init__(self) -> None:
        self.asked: list[str] = []

    def fetch(self, url: str, *, refresh: bool = False) -> None:
        self.asked.append(url)
        raise httpx.HTTPError("nothing here")


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
            released=date(2000, 1, 1),
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


# --- what is already in the dataset is not asked for again ------------------------------------


def test_a_sprite_already_in_the_dataset_is_not_fetched(tmp_path: Path) -> None:
    writer = DatasetWriter(tmp_path)
    writer.write_sprite("pikachu.png", b"drawn earlier")
    build = Build(dataset_root=tmp_path, cache_root=tmp_path / "cache")
    client = Counting()

    written = build._fetch_sprites(api(), client, species((25, "pikachu")), writer)

    # The committed dataset is the only cache that travels with the repository, so a clone
    # with a cold HTTP cache must not go back out for eight thousand pictures it already has.
    assert client.asked == []
    assert written == [tmp_path / "sprites" / "pikachu.png"]
    assert writer.kept == written
    # And not counted as unchanged: nothing came back to compare it against.
    assert writer.unchanged == []


def test_refresh_fetches_it_anyway(tmp_path: Path) -> None:
    writer = DatasetWriter(tmp_path)
    writer.write_sprite("pikachu.png", b"drawn earlier")
    build = Build(dataset_root=tmp_path, cache_root=tmp_path / "cache", refresh=True)
    client = Counting()

    # A picture that was wrong when it was written is the one thing having the file cannot
    # notice, and this flag is the only way past it.
    assert build._fetch_sprites(api(), client, species((25, "pikachu")), writer) == []
    assert client.asked == [api().sprite_url(25)]
    assert writer.kept == []


def test_a_sheet_asks_only_for_what_it_is_missing(tmp_path: Path) -> None:
    writer = DatasetWriter(tmp_path)
    writer.write_sprite("generation-iii/emerald/pikachu.png", b"drawn earlier")
    build = Build(dataset_root=tmp_path, cache_root=tmp_path / "cache")
    client = Counting()
    table = species((25, "pikachu"), (26, "raichu"))

    build._fetch_sprite_set(api(), client, "generation-iii/emerald", game(), [], table, writer)

    assert client.asked == [api().sprite_url(26, "generation-iii/emerald")]


def test_a_form_already_drawn_costs_nothing_at_all(tmp_path: Path) -> None:
    writer = DatasetWriter(tmp_path)
    writer.write_sprite("vulpix-alola.png", b"drawn earlier")
    build = Build(dataset_root=tmp_path, cache_root=tmp_path / "cache")
    forms = [
        Form(
            id="vulpix-alola",
            species="vulpix",
            name="Alolan",
            kind=FormKind.REGIONAL,
            games=["emerald"],
        )
    ]

    # Both clients are None: where a form's picture lives costs a request per species to work
    # out, and a build whose forms are all drawn should not even ask that.
    written = build._fetch_form_faces(None, None, forms, writer)

    assert written == [tmp_path / "sprites" / "vulpix-alola.png"]


def test_a_cover_already_in_the_dataset_opens_no_client(tmp_path: Path) -> None:
    writer = DatasetWriter(tmp_path)
    writer.write_box_art("emerald.png", b"drawn earlier")
    build = Build(dataset_root=tmp_path, cache_root=tmp_path / "cache")

    written = build._fetch_box_art(["emerald"], writer)

    assert written == [tmp_path / "boxart" / "emerald.png"]
    # The Archives are the five-second host, and two requests a game is five minutes for the
    # twenty-eight covers. Nothing was opened, so nothing was cached.
    assert not (tmp_path / "cache" / "http").exists()


def test_a_build_with_no_sprite_set_fetches_nothing(tmp_path: Path) -> None:
    DatasetWriter(tmp_path).write_species(species((25, "pikachu")))
    build = Build(dataset_root=tmp_path, cache_root=tmp_path / "cache", built_on=date(2026, 9, 21))

    # A client that would raise if it were used: a game with no set of its own asks for nothing.
    assert (
        build._fetch_game_sprites(api(), None, [game(sprite_set=None)], DatasetWriter(tmp_path))
        == []
    )
