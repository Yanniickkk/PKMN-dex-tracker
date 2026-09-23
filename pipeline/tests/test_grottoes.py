"""Reading the Hidden Grotto page: the one source in this dataset that is parsed, not typed."""

from __future__ import annotations

from datetime import date

import pytest

from livingdex_pipeline.grottoes import URL, GrottoError, grotto_encounters
from livingdex_pipeline.models import EncounterMethod

PRESENT = "background:#303E51;"
ABSENT = "background:#FFF;"


def row(species: str, *, levels: str, rate: str, black: bool = True, white: bool = True) -> str:
    """One table row, shaped the way the page shapes one."""
    return f"""
    <tr>
      <td><a href="/wiki/{species}_(Pok%C3%A9mon)">{species}</a></td>
      <th style="{PRESENT if black else ABSENT}">B2</th>
      <th style="{PRESENT if white else ABSENT}">W2</th>
      <td>Hidden Grotto</td>
      <td>{levels}</td>
      <td>{rate}</td>
    </tr>
    """


LEGEND = (
    "<tr><td>A colored background means that the Pokemon can be found in this location in the "
    "specified game.</td></tr>"
)

HEADER_ROW = "<tr><th>Pokémon</th><th>Games</th><th>Location</th><th>Levels</th><th>Rate</th></tr>"


def table(*rows: str) -> str:
    return f"<table><tbody>{HEADER_ROW}{''.join(rows)}{LEGEND}</tbody></table>"


def page(body: str) -> str:
    return f"<html><body><div id='mw-content-text'>{body}</div></body></html>"


class FakeWiki:
    """Serves one page and remembers the day it says it was fetched."""

    def __init__(self, html: str, retrieved: date = date(2026, 9, 20)) -> None:
        self.html = html
        self.retrieved = retrieved
        self.asked_for: list[str] = []

    def get_text(self, url: str, *, refresh: bool = False) -> str:
        self.asked_for.append(url)
        return self.html

    def retrieved_on(self, url: str) -> date:
        return self.retrieved


ONE_GROTTO = page(
    "<h3>Route 2</h3>"
    + table(
        row("Nidoran♀", levels="55-59", rate="2%"),
        row("Granbull", levels="55-59", rate="1%"),
    )
)


def read(html: str, *, column: str = "B2", species: set[str] | None = None, **kwargs):
    wiki = FakeWiki(html, **kwargs)
    return grotto_encounters(
        wiki,
        game_id="black-2",
        column=column,
        species=species if species is not None else {"nidoran-f", "granbull"},
    )


def test_a_grotto_row_becomes_a_wild_slot_in_the_area_it_sits_under() -> None:
    found = read(ONE_GROTTO)

    assert len(found) == 2
    first = found[0]
    assert str(first.target) == "nidoran-f"
    assert first.location == "Route 2"
    assert first.sub_area is None
    assert first.method is EncounterMethod.HIDDEN_GROTTO
    assert (first.levels.minimum, first.levels.maximum) == (55, 59)
    assert first.rate_percent == 2.0


def test_every_slot_is_cited_to_the_day_the_cache_says_the_page_was_read() -> None:
    # The same rule the PokeAPI records follow: a rebuild from an unchanged page does not
    # re-date the claim to the day of the build.
    [first, _] = read(ONE_GROTTO, retrieved=date(2026, 9, 20))

    assert first.source.source == "bulbapedia"
    assert first.source.url == URL
    assert first.source.retrieved_on == date(2026, 9, 20)


def test_a_white_cell_means_the_other_half_has_it_and_this_one_does_not() -> None:
    # The page's own legend, which is the only thing that distinguishes the two halves here:
    # Lostlorn Forest holds a Pinsir three times as often in one as in the other, and the
    # species column says the same thing on both rows.
    html = page(
        "<h3>Lostlorn Forest</h3>"
        + table(
            row("Pinsir", levels="20-24", rate="0.75%", white=False),
            row("Pinsir", levels="20-24", rate="0.25%", black=False),
        )
    )

    [black] = read(html, column="B2", species={"pinsir"})
    [white] = read(html, column="W2", species={"pinsir"})

    assert black.rate_percent == 0.75
    assert white.rate_percent == 0.25


def test_an_area_with_two_grottoes_keeps_them_apart() -> None:
    html = page(
        "<h3>Route 3</h3>"
        + table(
            "<tr><th>Dark grass</th></tr>",
            row("Zebstrika", levels="55-59", rate="1%"),
            "<tr><th>Pond</th></tr>",
            row("Lombre", levels="55-59", rate="1%"),
        )
    )

    zebstrika, lombre = read(html, species={"zebstrika", "lombre"})

    assert (zebstrika.location, zebstrika.sub_area) == ("Route 3", "Dark grass")
    assert (lombre.location, lombre.sub_area) == ("Route 3", "Pond")


def test_the_legend_at_the_foot_of_a_table_is_not_a_grotto() -> None:
    # It is a row of one cell, exactly like a grotto's heading is, and it says nothing about
    # where anything lives.
    [first, _] = read(ONE_GROTTO)

    assert first.sub_area is None
    assert "colored background" not in str(first.sub_area)


def test_the_funfest_tables_below_the_last_grotto_are_left_alone() -> None:
    # Those grottoes were opened by a mission handed out over Wi-Fi, and the service closed in
    # 2014. Reading them would tell a player to walk into a door that no longer opens.
    html = page(
        "<h3>Route 2</h3>"
        + table(row("Granbull", levels="55-59", rate="1%"))
        + "<h3>Funfest Missions</h3>"
        + table(row("Espeon", levels="55-59", rate="1%"))
    )

    found = read(html, species={"granbull", "espeon"})

    assert [str(one.target) for one in found] == ["granbull"]


def test_a_species_the_dataset_cannot_place_is_reported_rather_than_dropped(caplog) -> None:
    html = page("<h3>Route 2</h3>" + table(row("Granbull", levels="55-59", rate="1%")))

    with caplog.at_level("WARNING"), pytest.raises(GrottoError):
        read(html, species={"something-else"})

    assert "Granbull" in caplog.text


def test_a_page_that_has_been_rewritten_fails_loudly() -> None:
    # A parser that quietly returns nothing when a page changes shape is worse than one that
    # breaks: the build stays green and two games lose a dozen species.
    with pytest.raises(GrottoError, match="rewritten"):
        read(page("<h3>Route 2</h3><p>Nothing here any more.</p>"))
