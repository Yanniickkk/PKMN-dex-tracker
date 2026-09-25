"""Reading a location page's encounter tables, which is where Hoenn's remakes get their wild."""

from __future__ import annotations

from datetime import date

from livingdex_pipeline.encountertables import table_encounters
from livingdex_pipeline.models import EncounterMethod

PRESENT = "background:#AB2813;"
ABSENT = "background:#FFF;"

METHODS = {
    "Grass": EncounterMethod.WALK,
    "Long grass": EncounterMethod.WALK,
    "Dive": EncounterMethod.DIVE,
    "Cave": EncounterMethod.WALK,
    "Surfing": EncounterMethod.SURF,
    "Old Rod": EncounterMethod.OLD_ROD,
    "Horde Encounter": EncounterMethod.HORDE,
}


def row(
    species: str,
    *,
    method: str = "Grass",
    levels: str = "5",
    rate: str = "20%",
    omega_ruby: bool = True,
    alpha_sapphire: bool = True,
) -> str:
    """One row, shaped the way a location page shapes one."""
    return f"""
    <tr>
      <td><a href="/wiki/{species}_(Pok%C3%A9mon)">{species}</a></td>
      <th style="{PRESENT if omega_ruby else ABSENT}">OR</th>
      <th style="{PRESENT if alpha_sapphire else ABSENT}">AS</th>
      <td>{method}</td>
      <td>{levels}</td>
      <td>{rate}</td>
    </tr>
    """


def old_row(species: str) -> str:
    """A Generation 3 row on the same page, which has one cell more and is not ours."""
    return f"""
    <tr>
      <td>{species}</td>
      <th style="{PRESENT}">R</th>
      <th style="{PRESENT}">S</th>
      <th style="{PRESENT}">E</th>
      <td>Grass</td>
      <td>5</td>
      <td>20%</td>
    </tr>
    """


def heading(text: str) -> str:
    return f"<tr><td>{text}</td></tr>"


LEGEND = heading(
    "A colored background means that the Pokemon can be found in this location in the "
    "specified game."
)

HEADER_ROW = "<tr><th>Pokémon</th><th>Games</th><th>Location</th><th>Levels</th><th>Rate</th></tr>"


def table(*rows: str) -> str:
    return f"<table><tbody>{HEADER_ROW}{''.join(rows)}{LEGEND}</tbody></table>"


def page(body: str) -> str:
    return f"<html><body><div id='mw-content-text'>{body}</div></body></html>"


class FakeWiki:
    """Serves a page per title and remembers the day it says each was fetched."""

    def __init__(self, pages: dict[str, str], retrieved: date = date(2026, 9, 23)) -> None:
        self.pages = pages
        self.retrieved = retrieved
        self.asked_for: list[str] = []

    def get_text(self, url: str, *, refresh: bool = False) -> str:
        self.asked_for.append(url)
        return self.pages[url.rsplit("/", 1)[-1]]

    def retrieved_on(self, url: str) -> date:
        return self.retrieved


CONDITIONS = {
    "Exclusively as hidden Pokémon": "Only as a hidden Pokemon the DexNav finds",
    "Underwater": "",
}

REQUIREMENTS = {"Long grass": "In the long grass"}


def read(pages: dict[str, str], *, column: str = "OR", species: set[str] | None = None) -> list:
    # A test that only cares about rows hands over a table; one that cares about the headings
    # above it builds the article body itself.
    wiki = FakeWiki(
        {
            title: html if "mw-content-text" in html else page(html)
            for title, html in pages.items()
        }
    )

    return table_encounters(
        wiki,
        game_id="omega-ruby",
        column=column,
        pages={title: title.replace("Hoenn_", "").replace("_", " ") for title in pages},
        methods=METHODS,
        requirements=REQUIREMENTS,
        conditions=CONDITIONS,
        species=species or {"zigzagoon", "tentacool", "seedot", "lotad", "golbat"},
    )


def test_which_half_a_row_belongs_to_is_a_colour_and_not_the_letters() -> None:
    # Both cells say "OR" and "AS" whatever the answer is; the wiki writes the answer as a
    # filled-in background. A parser reading the text would give both halves every exclusive
    # in Hoenn, which is the one thing a version pair exists to get right.
    pages = {
        "Hoenn_Route_102": table(
            row("Seedot", omega_ruby=True, alpha_sapphire=False),
            row("Lotad", omega_ruby=False, alpha_sapphire=True),
        )
    }

    assert [one.target.species for one in read(pages, column="OR")] == ["seedot"]
    assert [one.target.species for one in read(pages, column="AS")] == ["lotad"]


def test_a_heading_inside_the_table_is_what_the_row_asks_of_a_player() -> None:
    # "Exclusively as hidden Pokemon" is how the wiki says a species is only there through the
    # DexNav, and it is written once above the rows it covers rather than on each of them.
    pages = {
        "Hoenn_Route_101": table(
            row("Zigzagoon"),
            heading("Exclusively as hidden Pokémon"),
            heading("After defeating or capturing Groudon/Kyogre"),
            row("Tentacool", rate="??%"),
        )
    }

    ordinary, hidden = read(pages)

    assert ordinary.requirement is None
    assert hidden.requirement == (
        "Only as a hidden Pokemon the DexNav finds; After defeating or capturing Groudon/Kyogre"
    )
    # "??%" is the wiki saying nobody measured it. No rate beats an invented one.
    assert hidden.rate_percent is None
    assert ordinary.rate_percent == 20.0


def test_a_heading_that_only_repeats_the_method_says_nothing() -> None:
    pages = {
        "Hoenn_Route_101": table(
            heading("Horde Encounter"),
            row("Zigzagoon", method="Horde Encounter", rate="95%"),
        )
    }

    [horde] = read(pages)

    assert horde.method is EncounterMethod.HORDE
    assert horde.requirement is None


def test_a_heading_above_the_table_is_which_part_of_the_place_it_is() -> None:
    # Shoal Cave is one location and four tables: high tide, low tide, the ice room. A record
    # that said only "Shoal Cave" would send a player in at the wrong hour.
    pages = {
        "Shoal_Cave": page(
            "<h3>Generation VI</h3>"
            "<h4>Low tide</h4>" + table(row("Golbat", method="Cave"))
        )
    }

    [slot] = read(pages, species={"golbat"})

    assert slot.location == "Shoal Cave"
    assert slot.sub_area == "Low tide"


def test_another_generations_rows_on_the_same_page_are_not_read() -> None:
    # Every location page carries its Generation 3 tables too, and those have a cell more.
    pages = {"Hoenn_Route_102": table(old_row("Zigzagoon"), row("Seedot"))}

    assert [one.target.species for one in read(pages)] == ["seedot"]


def test_a_word_for_something_that_is_not_a_wild_slot_is_left_to_its_own_step() -> None:
    # The same table lists the starters as gifts. They are step 4's, with their own record and
    # their own NPC, and a starter in the grass would be a lie about both.
    pages = {
        "Hoenn_Route_101": table(
            row("Zigzagoon"),
            heading("First partner Pokémon"),
            row("Treecko", method="Gift", levels="5", rate="One"),
        )
    }

    assert [one.target.species for one in read(pages, species={"zigzagoon", "treecko"})] == [
        "zigzagoon"
    ]


def test_a_level_column_can_be_a_list_a_range_or_one_number() -> None:
    pages = {
        "Shoal_Cave": table(
            row("Golbat", method="Cave", levels="26, 28, 30, 32"),
            row("Zigzagoon", levels="31-34"),
            row("Tentacool", method="Surfing", levels="5"),
        )
    }

    listed, ranged, single = read(pages)

    assert (listed.levels.minimum, listed.levels.maximum) == (26, 32)
    assert (ranged.levels.minimum, ranged.levels.maximum) == (31, 34)
    assert (single.levels.minimum, single.levels.maximum) == (5, 5)


def test_the_place_is_named_the_way_the_rest_of_the_dataset_names_it() -> None:
    # The wiki writes "Hoenn Route 101" to tell it from Kanto's; everything else in this game -
    # its gifts, its statics, all still from PokeAPI - calls it "Route 101".
    pages = {"Hoenn_Route_101": table(row("Zigzagoon"))}

    [slot] = read(pages)

    assert slot.location == "Route 101"
    assert slot.source.source == "bulbapedia"
    assert slot.source.url.endswith("Hoenn_Route_101")


def test_a_name_the_dataset_has_never_heard_of_is_reported_rather_than_guessed() -> None:
    pages = {"Hoenn_Route_101": table(row("Zigzagoon"), row("Nosepassa"))}

    assert [one.target.species for one in read(pages)] == ["zigzagoon"]


def test_a_page_with_nothing_for_this_pair_is_a_warning_and_not_a_failure() -> None:
    # Half of Hoenn's places are Generation 3's only - the Mirage Tower crumbled and was never
    # rebuilt. A page with no rows for these two is worth saying out loud and is not a reason to
    # throw away the other eighty.
    pages = {"Mirage_Tower": table(old_row("Anorith")), "Hoenn_Route_101": table(row("Zigzagoon"))}

    assert [one.target.species for one in read(pages)] == ["zigzagoon"]


def test_a_heading_closes_when_the_next_one_opens() -> None:
    # The bug this guards was in the data before it was in a test: with the headings piling up,
    # a Tentacool surfacing at the top of Route 103 needed the DexNav and a defeated Groudon,
    # because that is what the foot of the same table says about three other species.
    pages = {
        "Hoenn_Route_103": table(
            row("Tentacool", method="Surfing"),
            heading("Horde Encounter"),
            row("Zigzagoon", method="Horde Encounter"),
            heading("Exclusively as hidden Pokémon"),
            row("Seedot", rate="??%"),
        )
    }

    surfing, horde, hidden = read(pages)

    assert surfing.requirement is None
    assert horde.requirement is None
    assert hidden.requirement == "Only as a hidden Pokemon the DexNav finds"


def test_a_heading_that_names_a_method_outranks_the_location_column() -> None:
    # Routes 118 and 121 write "Horde Encounter" over rows whose Location column says "Long
    # grass". Five Wingull walking up at once is a horde standing in long grass, and reading
    # the column alone would file it as an ordinary walk.
    pages = {
        "Hoenn_Route_118": table(
            heading("Horde Encounter"),
            row("Zigzagoon", method="Long grass", levels="12", rate="35%"),
        )
    }

    [horde] = read(pages)

    assert horde.method is EncounterMethod.HORDE
    # And the column is still worth saying: the long grass is not the grass beside it.
    assert horde.requirement == "In the long grass"


def test_a_heading_reworded_as_nothing_is_dropped() -> None:
    # "Underwater" above rows that are already dives says nothing twice.
    pages = {
        "Hoenn_Route_107": table(
            heading("Underwater"),
            row("Tentacool", method="Dive", levels="25", rate="50%"),
        )
    }

    [dive] = read(pages)

    assert dive.method is EncounterMethod.DIVE
    assert dive.requirement is None


# --- the second pair to keep its tables this way -------------------------------------------------


def switch_row(
    species: str,
    *,
    method: str = "Grass",
    levels: str = "5",
    rates: tuple[str, ...] = ("20%",),
    brilliant_diamond: bool = True,
    shining_pearl: bool = True,
) -> str:
    """One row the way a Generation 8 remake's page shapes one: the rate may be split by hour."""
    cells = "".join(f"<td>{one}</td>" for one in rates)

    return f"""
    <tr>
      <td><a href="/wiki/{species}_(Pok%C3%A9mon)">{species}</a></td>
      <th style="{PRESENT if brilliant_diamond else ABSENT}">BD</th>
      <th style="{PRESENT if shining_pearl else ABSENT}">SP</th>
      <td>{method}</td>
      <td>{levels}</td>
      {cells}
    </tr>
    """


def test_a_rate_split_by_hour_is_three_slots_with_the_hour_said() -> None:
    # Generation 8 writes the rate three times, under a morning, a day and a night icon. On
    # Sinnoh's thirty route pages every single row that carries three carries three different
    # ones, so folding them into an average would throw away the whole of what they say.
    rows = table(switch_row("Starly", rates=("50%", "50%", "40%")))
    wiki = FakeWiki({"Sinnoh_Route_201": page(rows)})

    found = table_encounters(
        wiki,
        game_id="brilliant-diamond",
        column="BD",
        pair=("BD", "SP"),
        pages={"Sinnoh_Route_201": "Route 201"},
        methods=METHODS,
        species={"starly"},
    )

    assert [one.rate_percent for one in found] == [50.0, 50.0, 40.0]
    assert [one.requirement for one in found] == [
        "In the morning",
        "During the day",
        "At night",
    ]


def test_an_hour_a_species_is_not_there_is_no_slot_rather_than_a_rare_one() -> None:
    # 0% is the page saying it is not out at that hour. Reading it as a rate would offer a
    # player a tile they could stand in the grass all morning for and never fill.
    rows = table(switch_row("Hoothoot", rates=("0%", "0%", "30%")))
    wiki = FakeWiki({"Sinnoh_Route_201": page(rows)})

    found = table_encounters(
        wiki,
        game_id="brilliant-diamond",
        column="BD",
        pair=("BD", "SP"),
        pages={"Sinnoh_Route_201": "Route 201"},
        methods=METHODS,
        species={"hoothoot"},
    )

    assert [(one.rate_percent, one.requirement) for one in found] == [(30.0, "At night")]


def test_an_hour_that_changes_nothing_is_not_said_at_all() -> None:
    # Three of the same number is the page saying the hour does not matter, and a requirement
    # that is true all day is noise on a tile.
    wiki = FakeWiki({"Sinnoh_Route_201": page(table(switch_row("Bidoof", rates=("25%",) * 3)))})

    found = table_encounters(
        wiki,
        game_id="brilliant-diamond",
        column="BD",
        pair=("BD", "SP"),
        pages={"Sinnoh_Route_201": "Route 201"},
        methods=METHODS,
        species={"bidoof"},
    )

    assert [(one.rate_percent, one.requirement) for one in found] == [(25.0, None)]


def test_the_pair_of_letters_is_what_tells_one_generation_from_another() -> None:
    # The same page carries Diamond and Pearl's tables and these two's, and the rows are told
    # apart by the letters in the Games column rather than by the heading above them. Until a
    # second pair needed this, those letters were written into the reader.
    body = page(table(switch_row("Starly"), row("Starly"), old_row("Starly")))
    wiki = FakeWiki({"Sinnoh_Route_201": body})

    switch = table_encounters(
        wiki,
        game_id="brilliant-diamond",
        column="BD",
        pair=("BD", "SP"),
        pages={"Sinnoh_Route_201": "Route 201"},
        methods=METHODS,
        species={"starly"},
    )
    remakes = table_encounters(
        wiki,
        game_id="omega-ruby",
        column="OR",
        pages={"Sinnoh_Route_201": "Route 201"},
        methods=METHODS,
        species={"starly"},
    )

    assert len(switch) == 1
    assert len(remakes) == 1
