"""Reading a location page's encounter tables, which is where Hoenn's remakes get their wild."""

from __future__ import annotations

from datetime import date

from livingdex_pipeline.encountertables import (
    legends_encounters,
    paldea_encounters,
    paldea_fixed,
    table_encounters,
)
from livingdex_pipeline.models import EncounterMethod, Form, FormKind, GiftKind

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



# ---------------------------------------------------------------------------
# The Legends tables, which are the same wiki and a different table.
# ---------------------------------------------------------------------------

TIMES = ("Morning", "Day", "Evening", "Night")
WEATHERS = ("Clear", "Harsh sunlight", "Cloudy", "Rain", "Thunderstorm", "Fog")

def icon(name: str) -> str:
    """A column of a Legends table, which is named by a picture and by nothing else."""
    return f'<th><a href="/wiki/{name}"><img alt="{name}" src="/x.png"/></a></th>'


LEGENDS_HEADER = (
    "<tr>"
    "<th rowspan=2>Pokémon</th><th rowspan=2>Levels</th><th rowspan=2>Alpha Levels</th>"
    f"<th colspan={len(TIMES)}>Time of day</th>"
    f"<th colspan={len(WEATHERS)}>Weather</th>"
    "</tr>"
    "<tr>"
    + "".join(icon(one) for one in TIMES)
    + "".join(icon(one) for one in WEATHERS)
    + "</tr>"
)


def ticks(names, listed, over: int) -> str:
    """One block of tick columns, or one cell spanning the block when every column is ticked.

    ``over`` is what the page writes as the colspan in that case, which is four for the times
    and nine for the six weathers - nine being a number somebody typed, and the weather block
    being the last on the row, so a browser stops at the edge of the table.
    """
    if set(listed) == set(names):
        return f'<td colspan="{over}">✔</td>'

    return "".join(f"<td>{'✔' if one in listed else ''}</td>" for one in names)


def legends_row(
    species: str,
    *,
    levels: str = "3-6",
    alpha: str = "18-21",
    times=TIMES,
    weathers=WEATHERS,
    shown: str | None = None,
) -> str:
    """One row of a Legends table, with the decorations the real ones carry."""
    return (
        "<tr>"
        f'<td><img src="/menu.png"/><a href="/wiki/{species}_(Pok%C3%A9mon)" '
        f'title="{species} (Pokémon)">{shown or species}</a></td>'
        f"<td>{levels}</td><td>{alpha}</td>"
        f"{ticks(TIMES, times, len(TIMES))}{ticks(WEATHERS, weathers, 9)}"
        "</tr>"
    )


def legends_table(*rows: str) -> str:
    return f"<table><tbody>{LEGENDS_HEADER}{''.join(rows)}</tbody></table>"


LEGENDS_METHODS = {
    "": EncounterMethod.OVERWORLD,
    "In the air": EncounterMethod.OVERWORLD_FLYING,
    "Mass outbreak": EncounterMethod.SWARM,
}


def read_legends(
    body: str,
    *,
    species: set[str],
    methods=None,
    requirements=None,
    forms=(),
    form_names=None,
    places=None,
):
    wiki = FakeWiki({"Horseshoe_Plains": page(body)})

    return legends_encounters(
        wiki,
        game_id="legends-arceus",
        pages={"Horseshoe_Plains": "Obsidian Fieldlands, Horseshoe Plains"},
        methods=methods or LEGENDS_METHODS,
        requirements=requirements,
        species=species,
        forms=forms,
        form_names=form_names,
        places=places,
    )


def test_a_legends_row_has_no_rate_and_no_games_column() -> None:
    [one] = read_legends(legends_table(legends_row("Ponyta")), species={"ponyta"})

    assert one.target.species == "ponyta"
    assert one.location == "Obsidian Fieldlands, Horseshoe Plains"
    assert (one.levels.minimum, one.levels.maximum) == (3, 6)

    # There is no rate on these pages at all, and none is invented. A species is standing in a
    # place or it is not.
    assert one.rate_percent is None

    # Ticked in every column of both blocks, which is the page saying "whenever, whatever" -
    # not a condition, and so not words on a record.
    assert (one.time_of_day, one.weather) == (None, None)


def test_a_block_of_ticks_becomes_a_phrase_only_when_it_leaves_something_out() -> None:
    body = legends_table(
        legends_row("Cascoon", times=("Night",)),
        legends_row("Starly", times=("Morning", "Day", "Evening")),
        legends_row("Ponyta", weathers=("Clear", "Harsh sunlight", "Cloudy")),
    )
    cascoon, starly, ponyta = read_legends(body, species={"cascoon", "starly", "ponyta"})

    assert cascoon.time_of_day == "night"
    assert starly.time_of_day == "morning, day and evening"
    assert ponyta.weather == "clear, harsh sunlight and cloudy"

    # And the block that is not restricted says nothing, on the same rows.
    assert (cascoon.weather, starly.weather, ponyta.time_of_day) == (None, None, None)


def test_a_cell_spans_whatever_somebody_typed() -> None:
    # A row that is there in any weather writes colspan="9" over six columns. Nine is a number
    # somebody typed; a browser stops at the edge of the table, and so does this.
    assert 'colspan="9"' in legends_row("Eevee")

    [one] = read_legends(legends_table(legends_row("Eevee")), species={"eevee"})

    assert one.weather is None


def test_the_heading_above_a_group_is_what_the_location_column_is_elsewhere() -> None:
    body = legends_table(
        legends_row("Starly"),
        heading("In the air"),
        legends_row("Drifloon", times=("Night",)),
        heading("Mass outbreak"),
        legends_row("Ponyta", levels="15-17"),
        heading("Space-time distortions"),
        legends_row("Gengar", levels="25-60"),
    )
    found = read_legends(body, species={"starly", "drifloon", "ponyta", "gengar"})

    assert [(one.target.species, one.method) for one in found] == [
        ("starly", EncounterMethod.OVERWORLD),
        ("drifloon", EncounterMethod.OVERWORLD_FLYING),
        ("ponyta", EncounterMethod.SWARM),
    ]

    # A heading nobody has mapped is skipped rather than guessed at, which is the same guard
    # that keeps gifts and trades out of the older reader.
    assert "gengar" not in {one.target.species for one in found}


def test_a_row_with_only_alpha_levels_says_so() -> None:
    body = legends_table(legends_row("Silcoon", levels="", alpha="22-24"))
    [one] = read_legends(body, species={"silcoon"})

    # The levels are the alpha ones, because they are the only ones there are, and the record
    # says why rather than looking like an ordinary spawn that starts at 22.
    assert (one.levels.minimum, one.levels.maximum) == (22, 24)
    assert one.requirement == "Only as an alpha"


def test_a_group_can_say_more_than_the_method_it_maps_to() -> None:
    body = legends_table(heading("Mass outbreak"), legends_row("Ponyta"))
    [one] = read_legends(
        body,
        species={"ponyta"},
        requirements={"Mass outbreak": "Only while an outbreak is running"},
    )

    assert one.requirement == "Only while an outbreak is running"


def test_the_species_comes_from_the_link_rather_than_the_text() -> None:
    # The cell reads "SneaselHisuian Form" - a form name run straight onto the species name -
    # and on other rows it carries a dagger, the word Shiny, or an alpha badge. The link says
    # the same thing every time.
    body = legends_table(legends_row("Sneasel", shown="Sneasel‡ Hisuian Form Shiny"))
    [one] = read_legends(body, species={"sneasel"})

    assert one.target.species == "sneasel"

    # And which Sneasel goes deliberately unread here: these records name species, the way every
    # other game's do, and step 8 is where a form is answered.
    assert one.target.form is None


def test_neither_reader_touches_the_others_rows() -> None:
    # Lake Verity is a sublocation of the Obsidian Fieldlands and a Sinnoh lake, so one article
    # carries both kinds of table. Each reader insists on its own header.
    body = page(
        table(switch_row("Starly"), row("Starly"))
        + legends_table(legends_row("Ponyta"))
    )
    wiki = FakeWiki({"Lake_Verity": body})

    legends = legends_encounters(
        wiki,
        game_id="legends-arceus",
        pages={"Lake_Verity": "Obsidian Fieldlands, Lake Verity"},
        methods=LEGENDS_METHODS,
        species={"starly", "ponyta"},
    )
    remakes = table_encounters(
        wiki,
        game_id="brilliant-diamond",
        column="BD",
        pair=("BD", "SP"),
        pages={"Lake_Verity": "Lake Verity"},
        methods=METHODS,
        species={"starly", "ponyta"},
    )

    assert [one.target.species for one in legends] == ["ponyta"]
    assert [one.target.species for one in remakes] == ["starly"]



def test_a_legends_row_can_be_about_a_form() -> None:
    # Sixteen species are in Hisui as one form and no other, and the cell writes the form's name
    # straight onto the species name: "GrowlitheHisuian Form". Without reading it, the Hisuian
    # evolutions start from a form nothing in the dataset produces.
    body = legends_table(legends_row("Growlithe", shown="GrowlitheHisuian Form"))
    [one] = read_legends(
        body,
        species={"growlithe"},
        forms=[
            Form(
                id="growlithe-hisui",
                species="growlithe",
                name="Hisuian",
                kind=FormKind.REGIONAL,
                games=["legends-arceus"],
            )
        ],
        form_names={"Hisuian Form": "Hisui"},
    )

    assert one.target.form == "growlithe-hisui"


def test_a_phrase_that_names_a_default_leaves_the_record_about_the_species() -> None:
    # "Plant Cloak" and "West Sea" are the source naming what a species already is rather than a
    # choice, and a phrase nobody has mapped is passed over with a warning rather than guessed.
    body = legends_table(
        legends_row("Burmy", shown="BurmyPlant Cloak"),
        legends_row("Shellos", shown="ShellosNorth Sea"),
    )
    burmy, shellos = read_legends(
        body,
        species={"burmy", "shellos"},
        form_names={"Plant Cloak": ""},
    )

    assert burmy.target.form is None
    assert shellos.target.form is None



def test_a_heading_can_name_a_place_instead_of_a_way_of_being_met() -> None:
    # Z-A's expansion writes its encounters on eighteen pages by type, and the one-cell heading
    # inside each table is the zone rather than the method - which is the opposite of what the
    # same heading means on every other Legends page.
    body = legends_table(
        heading("Hyperspace Wild Zone 1"),
        legends_row("Charmander"),
    )
    [one] = read_legends(
        body,
        species={"charmander"},
        places={"Hyperspace Wild Zone 1": "Wild Zone 1"},
    )

    assert one.location == "Obsidian Fieldlands, Horseshoe Plains, Wild Zone 1"
    assert one.method is EncounterMethod.OVERWORLD


def test_a_heading_that_names_no_place_is_still_read_as_a_method() -> None:
    # Both kinds on one page, because nothing says a page cannot have both.
    body = legends_table(
        heading("Mass outbreak"),
        legends_row("Charmander"),
    )
    [one] = read_legends(
        body,
        species={"charmander"},
        places={"Hyperspace Wild Zone 1": "Wild Zone 1"},
    )

    assert one.location == "Obsidian Fieldlands, Horseshoe Plains"
    assert one.method is EncounterMethod.SWARM


def test_an_unmapped_heading_is_passed_over_rather_than_read_as_a_place() -> None:
    # Which is what keeps the footnote at the foot of each of those eighteen pages - a sentence
    # about alphas having a 5% chance - from being recorded as an eleventh zone.
    body = legends_table(
        heading("Non-fixed wild alpha Pokemon always have a 5% chance"),
        legends_row("Charmander"),
    )

    assert not read_legends(
        body,
        species={"charmander"},
        places={"Hyperspace Wild Zone 1": "Wild Zone 1"},
    )


def test_the_section_a_table_sits_under_is_part_of_where_its_rows_are() -> None:
    # The expansion numbers its zones from one again in every star rating's section, so the
    # heading above the table is the only thing telling two Wild Zone 1s apart.
    body = (
        "<h3>3★</h3>"
        + legends_table(heading("Hyperspace Wild Zone 1"), legends_row("Charmander"))
        + "<h3>5★</h3>"
        + legends_table(heading("Hyperspace Wild Zone 1"), legends_row("Charizard"))
    )
    three, five = read_legends(
        body,
        species={"charmander", "charizard"},
        places={"Hyperspace Wild Zone 1": "Wild Zone 1"},
    )

    assert three.location.endswith("3★ Wild Zone 1")
    assert five.location.endswith("5★ Wild Zone 1")
    assert three.location != five.location


def test_a_page_with_one_heading_over_all_of_it_is_unchanged() -> None:
    # Hisui's pages have exactly one heading - the word "Pokemon" - and nothing there uses it.
    # A section is only read into a location where a heading names a place.
    body = "<h2>Pokémon</h2>" + legends_table(legends_row("Charmander"))
    [one] = read_legends(body, species={"charmander"})

    assert one.location == "Obsidian Fieldlands, Horseshoe Plains"


# ---------------------------------------------------------------------------
# Scarlet and Violet's tables, which are the third shape on this wiki.
# ---------------------------------------------------------------------------

PALDEA_TERRAINS = {
    "Land": EncounterMethod.OVERWORLD,
    "Water surface": EncounterMethod.OVERWORLD_WATER,
    "Underwater": EncounterMethod.OVERWORLD_UNDERWATER,
    "Overland": EncounterMethod.OVERWORLD_FLYING,
    "Sky": EncounterMethod.OVERWORLD_FLYING,
}

PALDEA_HEADER = """
<tr>
  <th rowspan="2">Pokémon</th>
  <th rowspan="2" colspan="2">Games</th>
  <th colspan="5">Terrain</th>
  <th rowspan="2">Levels</th>
  <th colspan="4">Probability Weight</th>
  <th rowspan="2">Group Rate</th>
  <th rowspan="2">Group Pokémon</th>
</tr>
<tr>
  <td><img alt="Land"></td>
  <td><img alt="Water surface"></td>
  <td><img alt="Underwater"></td>
  <td><img alt="Overland"></td>
  <td><img alt="Sky"></td>
  <th><img alt="Morning"></th>
  <th><img alt="Day"></th>
  <th><img alt="Evening"></th>
  <th><img alt="Night"></th>
</tr>
"""


def paldea_row(
    species: str,
    *,
    form: str = "",
    terrain: tuple[str, ...] = ("Land",),
    levels: str = "5-8",
    weight: str | tuple[str, str, str, str] = "60",
    scarlet: bool = True,
    violet: bool = True,
    group_rate: str = "✘",
    group_species: str = "✘",
) -> str:
    """One row, shaped the way a Scarlet and Violet location page shapes one."""
    ticks = "".join(
        f"<td>{'✔' if one in terrain else '✘'}</td>"
        for one in ("Land", "Water surface", "Underwater", "Overland", "Sky")
    )
    weights = (
        f'<td colspan="4">{weight}</td>'
        if isinstance(weight, str)
        else "".join(f"<td>{one}</td>" for one in weight)
    )

    return f"""
    <tr>
      <td><a href="/wiki/{species}" title="{species} (Pokémon)">{species}{form}</a></td>
      <td style="{PRESENT if scarlet else ABSENT}">S</td>
      <th style="{PRESENT if violet else ABSENT}">V</th>
      {ticks}
      <td>{levels}</td>
      {weights}
      <td>{group_rate}</td>
      <td>{group_species}</td>
    </tr>
    """


def biome(text: str) -> str:
    """A one-cell row inside a Scarlet and Violet table, which is always the biome."""
    return f'<tr><th colspan="15">{text}</th></tr>'


def paldea_table(*rows: str) -> str:
    return f"<table><tbody>{PALDEA_HEADER}{''.join(rows)}{LEGEND}</tbody></table>"


def read_paldea(
    body: str,
    *,
    species: set[str],
    version: str = "S",
    terrains=None,
    forms=(),
    form_names=None,
    pages=None,
):
    wiki = FakeWiki(
        {title: html if "mw-content-text" in html else page(html) for title, html in
         (pages or {"South_Province_(Area_One)": body}).items()}
    )

    return paldea_encounters(
        wiki,
        game_id="scarlet",
        version=version,
        pages={title: title.replace("_", " ") for title in wiki.pages},
        terrains=terrains or PALDEA_TERRAINS,
        species=species,
        forms=forms,
        form_names=form_names,
    )


def test_a_paldea_row_has_a_weight_where_every_other_table_has_a_rate() -> None:
    [one] = read_paldea(paldea_table(paldea_row("Lechonk", weight="80")), species={"lechonk"})

    assert one.target.species == "lechonk"
    assert one.location == "South Province (Area One)"
    assert (one.levels.minimum, one.levels.maximum) == (5, 8)

    # The whole reason for a third reader. The page counts in weights against the others that
    # can spawn at the same point and declines to turn that into a percentage, so this dataset
    # declines too: a denominator that depends on the biome, the terrain and the hour at once
    # is not something a player was ever shown.
    assert one.probability_weight == 80
    assert one.rate_percent is None


def test_which_half_a_row_belongs_to_is_a_colour_here_too() -> None:
    # Hoenn's lesson on a new table: both letters are always written, and the answer is whether
    # the cell behind them is filled in.
    body = paldea_table(
        paldea_row("Larvitar", scarlet=True, violet=False),
        paldea_row("Bagon", scarlet=False, violet=True),
    )
    listed = {"larvitar", "bagon"}

    assert [one.target.species for one in read_paldea(body, species=listed)] == ["larvitar"]
    assert [
        one.target.species for one in read_paldea(body, species=listed, version="V")
    ] == ["bagon"]


def test_a_row_ticked_in_several_terrains_is_several_places_to_look() -> None:
    # A Wingull on a beach walks on the sand, hovers over it and circles above it. One record
    # would have to pick one of the three and would be wrong about the other two - and two of
    # the three are one place, because Overland and Sky both map to flying, so this is two
    # records rather than three.
    found = read_paldea(
        paldea_table(paldea_row("Wingull", terrain=("Land", "Overland", "Sky"))),
        species={"wingull"},
    )

    assert [one.method for one in found] == [
        EncounterMethod.OVERWORLD,
        EncounterMethod.OVERWORLD_FLYING,
    ]
    assert {one.probability_weight for one in found} == {60}


def test_underwater_is_its_own_place_and_the_sky_is_not() -> None:
    # Both halves of the same measurement, which is why they are asserted together. Of the
    # 3,409 rows these games' fifty pages hold, 197 are ticked underwater and nothing else, so
    # folding it into the water above it would tell a player to swim past an Arrokuda. The Sky
    # column has four such rows, all of them a Braviary that walks on the ground elsewhere in
    # the same game, so it is the Overland column with different scenery.
    [under] = read_paldea(
        paldea_table(paldea_row("Arrokuda", terrain=("Underwater",))), species={"arrokuda"}
    )
    assert under.method is EncounterMethod.OVERWORLD_UNDERWATER

    [high] = read_paldea(
        paldea_table(paldea_row("Braviary", terrain=("Sky",))), species={"braviary"}
    )
    assert high.method is EncounterMethod.OVERWORLD_FLYING


def test_a_terrain_nothing_maps_is_skipped_rather_than_guessed_at() -> None:
    # The same guard the other two readers have against a heading nobody has read.
    found = read_paldea(
        paldea_table(paldea_row("Arrokuda", terrain=("Underwater",))),
        species={"arrokuda"},
        terrains={"Land": EncounterMethod.OVERWORLD},
    )

    assert found == []


def test_one_weight_across_the_block_says_nothing_about_the_time() -> None:
    [one] = read_paldea(paldea_table(paldea_row("Hoppip")), species={"hoppip"})

    assert one.time_of_day is None
    assert one.probability_weight == 60


def test_four_weights_are_read_as_the_hours_they_belong_to() -> None:
    # A Hoothoot in the Kitakami Wilds is weight 70 in the morning and the day and 400 in the
    # evening and at night. Two records rather than one that has to average them.
    found = read_paldea(
        paldea_table(paldea_row("Hoothoot", weight=("70", "70", "400", "400"))),
        species={"hoothoot"},
    )

    assert [(one.time_of_day, one.probability_weight) for one in found] == [
        ("morning and day", 70),
        ("evening and night", 400),
    ]


def test_an_hour_with_a_weight_of_zero_is_an_hour_it_is_not_there() -> None:
    # Sunkern is 60, 60, 60, 0: a slot with no chance in it is not a slot.
    [one] = read_paldea(
        paldea_table(paldea_row("Sunkern", weight=("60", "60", "60", "0"))),
        species={"sunkern"},
    )

    assert one.time_of_day == "morning, day and evening"
    assert one.probability_weight == 60


def test_four_equal_weights_say_the_same_thing_as_one_spanning_cell() -> None:
    [one] = read_paldea(
        paldea_table(paldea_row("Hoppip", weight=("60", "60", "60", "60"))),
        species={"hoppip"},
    )

    assert one.time_of_day is None


def test_the_one_cell_row_inside_the_table_is_the_biome() -> None:
    # Never a method and never a condition, which is what makes these tables different from
    # the Legends ones: it is where in this place the Pokemon is.
    found = read_paldea(
        paldea_table(
            biome("Prairie"),
            paldea_row("Hoppip"),
            biome("Lake"),
            paldea_row("Psyduck", terrain=("Water surface",)),
        ),
        species={"hoppip", "psyduck"},
    )

    assert [one.sub_area for one in found] == ["Prairie", "Lake"]


def test_the_heading_above_the_table_is_the_part_of_the_place() -> None:
    # The Terarium's Canyon Biome carries five tables under five headings, and the biome
    # heading inside each of them starts again. Both halves are the answer to "where".
    body = page(
        "<h2>Pokémon</h2>"
        + paldea_table(biome("Prairie"), paldea_row("Scyther"))
        + "<h3>East Bridge Cave</h3>"
        + paldea_table(biome("Cave"), paldea_row("Geodude"))
    )

    found = read_paldea(body, species={"scyther", "geodude"})

    # "Pokemon" is the heading the tables live under rather than a part of anywhere.
    assert [one.sub_area for one in found] == ["Prairie", "East Bridge Cave, Cave"]


def test_two_level_bands_are_two_records_rather_than_one_with_a_hole_in_it() -> None:
    # "30-39, 50-53" is an area with a low half and a high half, which Kitakami writes a good
    # deal. 30-53 would send a player looking for a level 45 one that is not there.
    found = read_paldea(
        paldea_table(paldea_row("Hoothoot", levels="30-39, 50-53")),
        species={"hoothoot"},
    )

    assert [(one.levels.minimum, one.levels.maximum) for one in found] == [(30, 39), (50, 53)]


def test_a_form_written_onto_the_species_name_is_read_off_the_link() -> None:
    # The same cell shape Hisui has: the text runs the form's name onto the species name, and
    # the link says which species it is.
    found = read_paldea(
        paldea_table(paldea_row("Wooper", form="Paldean Form")),
        species={"wooper"},
        forms=[
            Form(
                id="wooper-paldea",
                species="wooper",
                name="Paldean Wooper",
                kind=FormKind.REGIONAL,
                games=["scarlet"],
            )
        ],
        form_names={"Paldean Form": "paldea"},
    )

    assert [(one.target.species, one.target.form) for one in found] == [
        ("wooper", "wooper-paldea")
    ]


def test_a_table_without_a_weight_block_is_not_one_of_these() -> None:
    # A page can hold both kinds: the older tables share the wiki with these, and the header is
    # what tells them apart rather than a row's width.
    assert read_paldea(table(row("Zigzagoon")), species={"zigzagoon"}) == []
    assert read_paldea(legends_table(legends_row("Ponyta")), species={"ponyta"}) == []


def fixed_row(
    species: str,
    *,
    form: str = "",
    location: str = "Fixed",
    levels: str = "20",
    rate: str = "Respawns",
    scarlet: bool = True,
    violet: bool = True,
) -> str:
    """One row of a Fixed encounters table, which is the familiar five-column shape."""
    return f"""
    <tr>
      <td><a href="/wiki/{species}" title="{species} (Pokémon)">{species}{form}</a></td>
      <td colspan="3" style="{PRESENT if scarlet else ABSENT}">S</td>
      <th colspan="3" style="{PRESENT if violet else ABSENT}">V</th>
      <td>{location}</td>
      <td>{levels}</td>
      <td colspan="3">{rate}</td>
    </tr>
    """


FIXED_HEADER = (
    '<tr><th>Pokémon</th><th colspan="6">Games</th><th>Location</th>'
    '<th>Levels</th><th colspan="3">Rate</th></tr>'
)


def fixed_table(*rows: str) -> str:
    return f"<table><tbody>{FIXED_HEADER}{''.join(rows)}</tbody></table>"


def read_fixed(body: str, *, species: set[str], version: str = "S", form_names=None, forms=()):
    wiki = FakeWiki({"Asado_Desert": page(body)})

    return paldea_fixed(
        wiki,
        game_id="scarlet",
        version=version,
        pages={"Asado_Desert": "Asado Desert"},
        species=species,
        forms=forms,
        form_names=form_names,
    )


def test_a_fixed_encounter_is_one_pokemon_standing_in_one_place() -> None:
    body = page("<h2>Fixed encounters</h2>" + fixed_table(fixed_row("Gimmighoul", levels="20")))

    [one] = read_fixed(body, species={"gimmighoul"})

    assert one.target.species == "gimmighoul"
    assert one.gift_kind is GiftKind.STATIC_ENCOUNTER
    assert one.location == "Asado Desert"
    assert one.level == 20

    # A weighted row says a Pokemon is in the pool at a spawn point; one of these says it is
    # standing there, and 295 of the 302 come back when they are caught.
    assert one.requirement == "respawns after it is caught"


def test_the_location_column_here_is_a_place_and_not_a_method() -> None:
    # Which is the whole reason this is not a call to table_encounters: there the column holds
    # the word "Grass" or "Surfing" and says how a player meets the row.
    body = page(
        "<h2>Fixed encounters</h2>"
        + fixed_table(fixed_row("Gimmighoul", location="Asado Desert Watchtower"))
    )

    [one] = read_fixed(body, species={"gimmighoul"})

    assert one.requirement == "Asado Desert Watchtower; respawns after it is caught"


def test_the_page_saying_only_fixed_is_the_page_saying_nothing() -> None:
    # 278 of the 302 rows write it, and copying it into a requirement would be the page's own
    # scaffolding wearing a player's sentence.
    body = page("<h2>Fixed encounters</h2>" + fixed_table(fixed_row("Dragonite")))

    [one] = read_fixed(body, species={"dragonite"})

    assert "Fixed" not in (one.requirement or "")


def test_a_titan_is_said_once_rather_than_twice() -> None:
    # The badge is on the species cell and the same thing is spelled out in the Location
    # column, and a record carrying both reads like a stutter.
    body = page(
        "<h2>Fixed encounters</h2>"
        + fixed_table(
            fixed_row(
                "Great Tusk",
                form="Former Titan",
                location="Appears in the same area where it was fought as a Titan Pokémon",
                rate="Only One",
            )
        )
    )

    [one] = read_fixed(body, species={"great-tusk"})

    assert one.target.species == "great-tusk"
    assert one.requirement is not None
    assert one.requirement.count("Titan") == 1
    assert one.requirement.endswith("there is only one")


def test_a_row_only_one_half_has_stays_out_of_the_other() -> None:
    body = page(
        "<h2>Fixed encounters</h2>"
        + fixed_table(fixed_row("Spiritomb", scarlet=True, violet=False))
    )

    assert len(read_fixed(body, species={"spiritomb"})) == 1
    assert read_fixed(body, species={"spiritomb"}, version="V") == []


def test_only_the_two_sections_that_hold_these_are_read() -> None:
    # The same table shape appears nowhere else on these pages, but the wild tables above do
    # carry six-cell rows, and reading them here would double every one of them.
    body = page(
        "<h2>Items</h2>"
        + fixed_table(fixed_row("Gimmighoul"))
        + "<h2>Fixed encounters</h2>"
        + fixed_table(fixed_row("Dragonite"))
    )

    found = read_fixed(body, species={"gimmighoul", "dragonite"})

    assert [one.target.species for one in found] == ["dragonite"]
