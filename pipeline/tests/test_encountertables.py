"""Reading a location page's encounter tables, which is where Hoenn's remakes get their wild."""

from __future__ import annotations

from datetime import date

from livingdex_pipeline.encountertables import legends_encounters, table_encounters
from livingdex_pipeline.models import EncounterMethod, Form, FormKind

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
