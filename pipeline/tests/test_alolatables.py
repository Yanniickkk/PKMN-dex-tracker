"""Reading the one thing PokeAPI does not say about an Alola slot: when it is there."""

from __future__ import annotations

import httpx

from livingdex_pipeline.alolatables import Reading, read_times
from livingdex_pipeline.models import EncounterMethod
from livingdex_pipeline.normalise import Normaliser

SPECIES = {"rattata", "yungoos", "tapu-koko", "magikarp", "machop", "gastrodon"}
FORMS = {"rattata-alola", "gastrodon-east"}


def matcher() -> Normaliser:
    return Normaliser(SPECIES, FORMS)


def row(name: str, games: tuple[str, str], label: str, levels: str, *rates: str) -> str:
    """One entry's first table row, which is the one carrying everything."""
    rate = (
        f'<td colspan="2">{rates[0]}</td>'
        if len(rates) == 1
        else f"<td>{rates[0]}</td><td>{rates[1]}</td>"
    )

    return (
        f"<tr><th></th><th colspan=3>{games[0]}</th><th colspan=3>{games[1]}</th>"
        f"<td>{name}</td><td>{name}</td><td>{name}</td>"
        f"<td>{label}</td><td></td><td>{label}</td><td>{levels}</td>{rate}</tr>"
    )


def page(*rows: str, heading: str = "") -> str:
    head = f'<tr><th colspan="15">{heading}</th></tr>' if heading else ""

    return (
        '<div id="mw-content-text"><table><tr><th>Pokemon</th><th>Allies</th>'
        "<th>Games</th><th>Location</th><th>Levels</th><th>Rate</th></tr>"
        f"{head}{''.join(rows)}</table></div>"
    )


class FakeWiki:
    """A client that hands back the pages a test wrote, and records what was asked for."""

    def __init__(self, pages: dict[str, str]) -> None:
        self._pages = pages
        self.asked: list[str] = []

    def get_text(self, url: str, *, refresh: bool = False) -> str:
        title = url.rsplit("/", 1)[-1]
        self.asked.append(title)
        return self._pages[title]


def read(html: str) -> list[Reading]:
    return read_times(
        FakeWiki({"Alola_Route_2": html}),
        pages={"Route 2": "Alola_Route_2"},
        normaliser=matcher(),
    )


def test_a_dash_in_one_of_the_two_rate_columns_is_the_whole_fact() -> None:
    # Which is what this module exists for. Yungoos stands in Route 2's grass by day and Alolan
    # Rattata by night, in both halves of the pair, and the source says neither.
    found = read(
        page(
            row("Rattata Alolan Form", ("S", "M"), "Grass", "7-10", "-", "10%"),
            row("Yungoos", ("S", "M"), "Grass", "7-10", "10%", "-"),
        )
    )

    assert [(one.target.form or one.target.species, one.time_of_day) for one in found] == [
        ("rattata-alola", "night"),
        ("yungoos", "day"),
    ]


def test_one_cell_across_both_hours_is_no_condition_at_all() -> None:
    # The wiki writes a single cell spanning Day and Night where the two agree, so "any hour" is
    # read off the shape of the table rather than by comparing two numbers.
    [found] = read(page(row("Magikarp", ("S", "M"), "Fishing", "10-15", "55%")))

    assert found.time_of_day is None
    assert found.method is EncounterMethod.SUPER_ROD


def test_the_other_pairs_rows_are_left_alone() -> None:
    # Every Alola location page carries two tables, and Ultra Sun and Ultra Moon renumbered and
    # restocked nearly all of them.
    found = read(
        page(
            row("Yungoos", ("S", "M"), "Grass", "7-10", "10%", "-"),
            row("Yungoos", ("US", "UM"), "Grass", "6-9", "-", "20%"),
        )
    )

    assert [one.time_of_day for one in found] == ["day"]


def test_a_form_is_read_as_a_form_and_a_two_word_species_as_a_species() -> None:
    # The wiki writes the species and its form as one string, so the split is guessed at from
    # the right: "Tapu Koko" is two words and no form, "Rattata Alolan Form" is one and two.
    found = read(
        page(
            row("Tapu Koko", ("S", "M"), "Grass", "60", "One", "One"),
            row("Gastrodon East Sea", ("S", "M"), "Surfing", "20-25", "30%"),
        )
    )

    assert [(one.target.species, one.target.form) for one in found] == [
        ("tapu-koko", None),
        ("gastrodon", "gastrodon-east"),
    ]


def test_a_bubbling_spot_is_named_by_its_heading_rather_than_its_column() -> None:
    # A bubbling spot is fished in, so its rows say "Fishing" like any other water and the
    # heading above them is what tells them apart. It is also the one of Alola's seven ambushes
    # the source does name, which is how it came to name the whole family.
    [found] = read(
        page(
            row("Magikarp", ("S", "M"), "Fishing", "10-18", "20%"),
            heading="Fishing at a bubbling spot",
        )
    )

    assert found.method is EncounterMethod.MOVING_SPOT
    assert found.label == "Bubbling spot"


def test_a_row_that_is_not_a_wild_slot_is_left_for_the_step_it_belongs_to() -> None:
    # The same tables hold the gifts, the in-game trades and the fossils, each of which has a
    # step of its own and a record shape of its own.
    found = read(page(row("Machop", ("S", "M"), "Trade Spearow", "9", "One")))

    assert found == []


def test_a_page_that_cannot_be_read_costs_a_condition_and_no_record() -> None:
    # This layers a second opinion on records that already stand on their own, so a hole in it
    # must not be able to take one away.
    class Broken:
        def get_text(self, url: str, *, refresh: bool = False) -> str:
            raise httpx.HTTPError("404")

    assert read_times(Broken(), pages={"Route 2": "x"}, normaliser=matcher()) == []
