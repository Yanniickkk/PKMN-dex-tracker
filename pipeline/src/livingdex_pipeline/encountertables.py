"""Wild encounter tables read off Bulbapedia's location pages.

The second source in this dataset that is read rather than typed, after :mod:`grottoes`, and the
first that had to be. PokeAPI carries no ordinary encounter table for Omega Ruby and Alpha
Sapphire at all: its rows for those two versions are hordes, the Mirage spots, a little Rock
Smash and the statics, and the grass, the water and the three fishing rods are simply absent.
Built from that source alone, the games say a Tentacool cannot be caught in Hoenn.

So the tables come from the wiki instead, page by page. Bulbapedia keeps one section per
generation on each location's page and one row per species: the games it is in - as colour, not
as text - what it is met by, the levels and the rate. That shape is uniform enough to parse and
wide enough to carry everything a slot needs, and it is the same shape :mod:`grottoes` reads.

What is deliberately not read here is anything the Location column calls a gift, an egg or a
trade. Those are steps 4 and 5, they have their own records and their own sources, and turning
them into wild slots would put a starter in the grass.

A row's games are a colour. Bulbapedia fills a game's letter in when the Pokemon is there and
leaves it white when it is not, which is the only place a version exclusive is written down: the
text of both cells says "OR AS" either way. A parser that read the letters would give both
halves of the pair every species in Hoenn.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from selectolax.parser import HTMLParser, Node

from .conditions import REQUIREMENTS
from .http import PoliteClient
from .models import (
    DexTarget,
    EncounterMethod,
    Form,
    LevelRange,
    SourceCitation,
    WildAcquisition,
)
from .normalise import Normaliser
from .sources import BULBAPEDIA, bulbapedia

log = logging.getLogger(__name__)

#: Bulbapedia states no crawl delay, so this is our own floor, borrowed from what the Archives
#: ask for. One page per location and cached after the first.
MIN_INTERVAL = 5.0

#: The colour a games cell is left when the Pokemon is *not* in that game. The page says so at
#: the foot of every table: "A colored background means that the Pokemon can be found in this
#: location in the specified game. A white background with a colored letter means that the
#: Pokemon cannot be found here."
ABSENT = "#fff"

#: The legend at the foot of a table, which is a one-cell row like a heading and is not one.
LEGEND = "colored background"

_NUMBER = re.compile(r"\d+")
_RATE = re.compile(r"([\d.]+)\s*%")

#: The two letters Omega Ruby and Alpha Sapphire fill their Games column with.
#:
#: A default rather than a constant now that a second pair reads these tables. Brilliant Diamond
#: and Shining Pearl write "BD" and "SP" in the same column on the same kind of page, and a row
#: is told from another generation's by exactly this.
ORAS = ("OR", "AS")

#: What the three rate columns on a Generation 8 grass table mean, left to right.
#:
#: The wiki writes them as icons with no text, so they are read from the header's own links -
#: Morning, Day, Night. Nothing before Generation 8 splits the column this way: Diamond varied
#: by time too and PokeAPI carried it as a condition on one slot, where these pages carry it as
#: three numbers on one row.
TIMES = ("time-morning", "time-day", "time-night")


class EncounterTableError(Exception):
    """A page could not be read the way this parser expects. The message is for a human."""


@dataclass(frozen=True)
class TableSlot:
    """One row of one table, before it is matched against a species id."""

    species: str
    #: What the page's Location column says: "Grass", "Surfing", "Old Rod", "Horde Encounter".
    method: str
    #: The headings this row sits under, in the order they are written. A condition lives
    #: here, and sometimes the method does too.
    headings: tuple[str, ...]
    #: Which part of the location, when a page splits one: "Low tide", "Area 1", "B1F".
    sub_area: str | None
    lowest: int
    highest: int
    rate_percent: float | None
    games: frozenset[str]
    #: Which of :data:`TIMES` this row's rate belongs to, when the page splits it three ways.
    when: str | None = None


def table_encounters(
    client: PoliteClient,
    *,
    game_id: str,
    column: str,
    pages: Mapping[str, str],
    methods: Mapping[str, EncounterMethod],
    species: set[str],
    requirements: Mapping[str, str] | None = None,
    conditions: Mapping[str, str] | None = None,
    aliases: Mapping[str, str] | None = None,
    pair: tuple[str, str] = ORAS,
    refresh: bool = False,
) -> list[WildAcquisition]:
    """Every wild slot these pages give one game, for the species given.

    ``pages`` maps a Bulbapedia page title to the name this dataset gives the place, because
    the two disagree often enough to matter: the wiki writes "Hoenn Route 101" to tell it from
    Kanto's, and everything else in this dataset - including the gifts and statics of the same
    game, which still come from PokeAPI - calls it "Route 101".

    ``column`` is how the Games column spells this game: "OR" or "AS", "BD" or "SP".

    ``pair`` is both of those letters, and it is what tells one generation's rows from another's
    on a page that keeps a section for each. It is the one thing in here that was a constant
    until a second pair of games turned out to keep its tables in the same shape.

    ``methods`` maps the page's word for a way of meeting something onto this project's, and a
    word that is not in it is skipped rather than guessed at. That is how gifts and trades stay
    out, and it is also the guard for the day the wiki grows a word nobody here has seen.

    ``requirements`` is what a page's word says that this project's method cannot hold. Long
    grass and deep sand are both walking, and a player standing in the ordinary grass beside
    them will wait forever.

    ``conditions`` rewords a heading the wiki writes for its own readers into a sentence for a
    player: "Exclusively as hidden Pokemon" means nothing to somebody who has not read the rest
    of the page. A heading that is not in it is passed through as it stands.

    ``aliases`` is for the names the wiki writes that this dataset spells another way, and is
    handed over rather than guessed at: a name nobody can place is reported, because it is a
    species missing from a game rather than a tidy shorter list.
    """
    names = Normaliser(species_ids=species, aliases=dict(aliases or {}))
    said = requirements or {}
    reworded = conditions or {}
    found: list[WildAcquisition] = []

    for title, location in pages.items():
        url = f"{BULBAPEDIA}/{title}"
        page = HTMLParser(client.get_text(url, refresh=refresh))
        citation = bulbapedia(title, retrieved_on=client.retrieved_on(url))
        slots = _slots(page, title=title, pair=pair)

        if not slots:
            # Loud rather than silent. A page with no rows for either half is either a place
            # these games do not have or a page that has been rewritten, and both are worth a
            # human's attention rather than a quietly shorter dataset.
            log.warning("%s: no %s or %s rows on %s", game_id, *pair, url)
            continue

        for slot in slots:
            if column not in slot.games:
                continue

            # A group's heading outranks the Location column about what a row is. Routes 118
            # and 121 write "Horde Encounter" over rows that say "Grass" and "Long grass", and
            # those twelve rows are hordes standing in grass rather than grass.
            word = next((one for one in slot.headings if one in methods), slot.method)
            method = methods.get(word)
            if method is None:
                continue

            target = names.target(slot.species)
            if target is None:
                log.warning("%s: no species matches %r on %s", game_id, slot.species, url)
                continue

            found.append(
                _record(
                    slot,
                    game_id=game_id,
                    target=target,
                    location=location,
                    method=method,
                    requirement=_requirement(slot, word=word, said=said, conditions=reworded),
                    citation=citation,
                )
            )

    return found


def _requirement(
    slot: TableSlot,
    *,
    word: str,
    said: Mapping[str, str],
    conditions: Mapping[str, str],
) -> str | None:
    """Everything this row asks of a player that its method and place do not already say.

    Three kinds, in the order a player would want them: where to be standing, which is what the
    Location column says beyond the method it maps to, then which hours it is there, and then
    what has to be true first, which is what the headings say. A heading that only repeats
    either word is dropped, and one reworded as nothing is dropped too - "Underwater" above rows
    that are already dives.
    """
    return (
        "; ".join(
            one
            for one in (
                said.get(slot.method),
                REQUIREMENTS[slot.when] if slot.when else None,
                *(
                    conditions.get(heading, heading)
                    for heading in slot.headings
                    if not _repeats(heading, word) and not _repeats(heading, slot.method)
                ),
            )
            if one
        )
        or None
    )


def _record(
    slot: TableSlot,
    *,
    game_id: str,
    target: DexTarget,
    location: str,
    method: EncounterMethod,
    requirement: str | None,
    citation: SourceCitation,
) -> WildAcquisition:
    return WildAcquisition(
        game=game_id,
        target=target,
        location=location,
        sub_area=slot.sub_area,
        method=method,
        levels=LevelRange(minimum=slot.lowest, maximum=slot.highest),
        rate_percent=slot.rate_percent,
        requirement=requirement,
        source=citation,
    )


def _slots(page: HTMLParser, *, title: str, pair: tuple[str, str]) -> list[TableSlot]:
    """Every row on one page that is about this pair, whichever section it sits in.

    A row is recognised by its Games column rather than by the heading above it, which is what
    makes this work on pages shaped three different ways: most locations keep a section per
    generation, some split a generation into sub-areas below that, and a place these games
    invented - Sea Mauville, the Mirage spots, Soaring in the sky - has no generation heading at
    all because there is only one.
    """
    body = page.css_first("#mw-content-text")
    if body is None:
        raise EncounterTableError(f"{title} has no article body")

    found: list[TableSlot] = []
    sub_area: str | None = None

    for node in body.traverse(include_text=False):
        if node.tag in ("h2", "h3", "h4"):
            sub_area = _sub_area(_text(node))
        elif node.tag == "table":
            found.extend(_rows(node, sub_area=sub_area, pair=pair))

    return found


def _sub_area(heading: str) -> str | None:
    """A heading that names part of a place, or nothing when it names something else.

    "Low tide" and "Ice room" on Shoal Cave are sub-areas; "Generation VI" and "Pokemon" are
    the scaffolding of the page, and "Items" and "Trivia" are other sections entirely - which
    do not matter, because a table is only read for its rows and a section with no rows
    contributes none.
    """
    if heading.startswith("Generation ") or heading in ("Pokémon", "Pokemon", "Contents"):
        return None

    return heading


def _rows(table: Node, *, sub_area: str | None, pair: tuple[str, str]) -> list[TableSlot]:
    """One table's rows, each carrying the headings written above it.

    A one-cell row is a heading inside the table, and it is where the wiki writes a condition:
    "Exclusively as hidden Pokemon After defeating or capturing Groudon / Kyogre" above the
    species the DexNav and the post-game add. Several stack, and they are kept in the order they
    are written.

    A heading opens a group and the first heading after a row closes it. Without that, what is
    written at the foot of a table would be read as true of the top of it, and a Tentacool in
    the sea off Route 103 would need the DexNav and a defeated Groudon.

    A heading that only repeats the Location column - "Horde Encounter" above the horde rows,
    "Fishing" above the three rods - says nothing a row does not, and is dropped.
    """
    found: list[TableSlot] = []
    headings: list[str] = []
    in_group = False

    for row in table.css("tr"):
        cells = [cell for cell in row.iter() if cell.tag in ("td", "th")]

        if len(cells) == 1:
            if in_group:
                headings = []
                in_group = False

            heading = _text(cells[0])
            if heading and LEGEND not in heading:
                headings.append(heading)

            continue

        if len(cells) not in (6, 8):
            continue

        made = _slot(cells, headings=headings, sub_area=sub_area, pair=pair)
        if made:
            found.extend(made)
            in_group = True

    return found


def _slot(
    cells: list[Node],
    *,
    headings: Sequence[str],
    sub_area: str | None,
    pair: tuple[str, str],
) -> list[TableSlot]:
    """One row, which is one slot on most pages and up to three on a Generation 8 grass table.

    **The rate column is split by time of day there**, morning, day and night, and the three
    numbers are nearly always different - on Sinnoh's thirty route pages, all ninety-two rows
    that carry three rates carry three different ones. So a row is three slots, and a rate of
    **0%** is the page saying the species is not there at that hour rather than that it is
    there and rare: those become no slot at all, which is the difference between a tile a
    player can fill after dark and one they can never fill.

    Where the three numbers agree, the time says nothing and is dropped, the same way a heading
    that only repeats the method column is.
    """
    species, first, second, where, levels, *rates = cells

    if (_text(first), _text(second)) != pair:
        # Another generation's rows, or the header row of this one.
        return []

    games = frozenset(_text(cell) for cell in (first, second) if _present(cell))
    if not games:
        return []

    numbers = [int(one) for one in _NUMBER.findall(_text(levels))]
    if not numbers:
        return []

    def made(rate: Node, when: str | None) -> TableSlot | None:
        match = _RATE.search(_text(rate))
        if match is not None and float(match.group(1)) == 0:
            return None

        return TableSlot(
            species=_text(species),
            method=_text(where),
            headings=tuple(headings),
            sub_area=sub_area,
            lowest=min(numbers),
            highest=max(numbers),
            # "??%" is the wiki saying nobody has measured it, "Varies" is a Grand Underground
            # table saying it depends how far the player has got, and Soaring's flocks are
            # graded in words. All three become no rate rather than a made-up one.
            rate_percent=float(match.group(1)) if match else None,
            games=games,
            when=when,
        )

    if len(rates) == 1 or len({_text(one) for one in rates}) == 1:
        return [one for one in (made(rates[0], None),) if one is not None]

    return [one for one in (made(*pair_) for pair_ in zip(rates, TIMES, strict=True)) if one]


def _repeats(heading: str, method: str) -> bool:
    """Whether a heading says only what the row's own method column says.

    Either way round: "Horde Encounter" is the whole of it, and "Fishing" is the front of
    "Fishing Old Rod".
    """
    one, other = heading.lower(), method.lower()

    return one.startswith(other) or other.startswith(one)


def _present(cell: Node) -> bool:
    """Whether this game's letter is filled in rather than left white."""
    return ABSENT not in cell.attributes.get("style", "").lower()


def _text(node: Node) -> str:
    return " ".join(node.text(separator=" ").split())


# ---------------------------------------------------------------------------
# The Legends games' tables, which are a different table on the same wiki.
# ---------------------------------------------------------------------------

#: The tick a Legends table puts in a column when the species is there under that condition.
TICK = "✔"

#: What the first column of a Legends table is called, which is how one is told from the others.
#:
#: **A page can hold both kinds.** Lake Verity is a sublocation of the Obsidian Fieldlands and a
#: Sinnoh lake, so its article carries forty-one tables: Diamond's, Platinum's, HeartGold's,
#: Brilliant Diamond's - and one of these. Neither reader may read the other's rows, and neither
#: does: this one insists on a header of its own shape, and the older one insists on a Games
#: column holding two particular letters.
LEGENDS_FIRST_COLUMN = ("Pokémon", "Pokemon")

#: The header cell that says a table belongs to a game with alphas in it.
ALPHA_LEVELS = "Alpha Levels"

#: What a species cell carries besides a name and a form, and what a footnote marker looks like.
DECORATIONS = ("\u2021", "\u2020", "*", "Shiny", "Alpha")
_NOTE = re.compile(r"\[[^\]]*\]")

#: The block every Legends table has, and the one no older table has.
#:
#: **Being wide is not enough to be one of these.** Wayward Cave carries two Generation 4 tables
#: whose Games column spans six letters and whose Rate column spans three - morning, day and
#: night - so "a header with a block in it" would have read them as Legends rows and named their
#: six games as six weathers. The hours are what only these games put in a header.
TIME_BLOCK = "Time of day"


@dataclass(frozen=True)
class LegendsSlot:
    """One row of one Legends table, before it is matched against a species id."""

    species: str
    #: What the cell wrote after the species name: "Hisuian Form", "White-Striped Form", "Male".
    #: Empty where the row is about the species itself.
    form: str
    #: The one-cell heading above this row, or "" for the rows that sit under none. It is what
    #: the Location column is on an older page: the way a player meets this one.
    group: str
    #: What the page writes in each of the two level columns, either of which can be empty.
    levels: tuple[int, int] | None
    alpha_levels: tuple[int, int] | None
    #: The names of the columns this row is ticked in, in the order the header writes them.
    times: tuple[str, ...]
    weathers: tuple[str, ...]
    #: How wide each block of ticks is, so "ticked in all of them" - which is no condition at
    #: all - can be told from "ticked in several".
    time_columns: int = 0
    weather_columns: int = 0
    #: The article heading this row's table sits under, or "" when it sits under none.
    #:
    #: **Hisui's pages need this and never use it**: one page is one place, and the only heading
    #: over its table is the word "Pokemon". Z-A's expansion writes its encounters on eighteen
    #: pages by type, cuts each into sections by star rating, and repeats the same ten zone
    #: numbers in every section - so the heading is the only thing telling Fire-type 2* Wild
    #: Zone 1 from Fire-type 3* Wild Zone 1, which are different places with different Pokemon.
    section: str = ""


def legends_encounters(
    client: PoliteClient,
    *,
    game_id: str,
    pages: Mapping[str, str],
    methods: Mapping[str, EncounterMethod],
    species: set[str],
    forms: Sequence[Form] = (),
    form_names: Mapping[str, str] | None = None,
    requirements: Mapping[str, str] | None = None,
    places: Mapping[str, str] | None = None,
    aliases: Mapping[str, str] | None = None,
    refresh: bool = False,
) -> list[WildAcquisition]:
    """Every wild slot the Legends games' pages give, for the species given.

    A second reader beside :func:`table_encounters` rather than more parameters on it, because
    the two tables agree about almost nothing. **There is no Games column**, so nothing here is
    a version exclusive and nothing is told apart by colour; **there is no rate**, because these
    games do not roll one - a species is standing in a place or it is not; and **there is no
    Location column**, so the way a player meets something is written as a heading over a group
    of rows instead of beside every one of them.

    What it has instead is two blocks of ticks, each column named by an icon and nothing else. A
    row is ticked in the ones it is there for, and a cell spanning a whole block is the page
    saying "all of them" - which is not a condition, and becomes no words on the record.

    **How wide the weather block is depends on where you are standing**, which is why the header
    is read rather than assumed: six columns in the Obsidian Fieldlands, seven in the Coronet
    Highlands, five on the Cobalt Coastlands and four in the Alabaster Icelands, where it never
    rains and it can blizzard. A reader that had counted on six would have put every tick in
    three of the five areas in the wrong column and said so about nothing.

    ``pages`` maps a page title to the name this dataset gives the place, as it does for the
    older tables. ``methods`` maps a heading above a group of rows onto a way of meeting
    something, with ``""`` for the rows that sit under no heading at all; a heading that is not
    in it is skipped, which is the same guard the older reader has against gifts and trades.

    **And a row here can be about a form, which no older table's is.** The species cell writes
    the form's name straight onto the species name - the text reads "SneaselHisuian Form" - and
    sixteen species in Hisui are in the game as that form and no other. ``form_names`` maps what
    the cell writes onto the suffix this dataset spells a form with, and a phrase mapped to
    nothing, or missing from the table, leaves the record about the species: "Plant Cloak" and
    "Incarnate Forme" and "West Sea" are the source naming a default, not a choice.

    Without it, ``growlithe-to-arcanine-hisui`` starts from a form nothing in the dataset
    produces, which is what ``no-evolution-dead-ends`` says and what this closes.
    """
    names = Normaliser(
        species_ids=species,
        form_ids={one.id for one in forms},
        aliases=dict(aliases or {}),
    )
    spelled = form_names or {}
    said = requirements or {}
    named = places or {}
    found: list[WildAcquisition] = []

    for title, location in pages.items():
        url = f"{BULBAPEDIA}/{title}"
        page = HTMLParser(client.get_text(url, refresh=refresh))
        citation = bulbapedia(title, retrieved_on=client.retrieved_on(url))
        slots = _legends_slots(page, title=title)

        if not slots:
            # Loud rather than silent, for the reason the older reader gives: a place with no
            # rows is either one this game does not have or a page that has been rewritten.
            log.warning("%s: no Legends rows on %s", game_id, url)
            continue

        for slot in slots:
            here = location
            if (place := named.get(slot.group)) is not None:
                # The heading names where these rows are rather than how they are met, which is
                # what the expansion's pages do. The section is part of the name because the
                # zone numbers start again in each of them.
                here = f"{location}, {slot.section} {place}".replace(",  ", ", ").rstrip()
                method = methods.get("")
            else:
                method = methods.get(slot.group)

            if method is None:
                continue

            if slot.form and slot.form not in spelled:
                # A phrase nobody has read is worth a person's eyes: it is either a form this
                # game has that nothing here names, or a default spelled a new way.
                log.warning(
                    "%s: %s is written %r on %s and nothing says what that is",
                    game_id,
                    slot.species,
                    slot.form,
                    url,
                )

            target = names.target(slot.species, spelled.get(slot.form))
            if target is None:
                log.warning("%s: no species matches %r on %s", game_id, slot.species, url)
                continue

            levels = slot.levels or slot.alpha_levels
            if levels is None:
                # A row with neither level column filled says nothing about levels and
                # everything about the species being here. There is no such row today; if one
                # arrives it is worth a person's eyes rather than a made-up range.
                log.warning("%s: %s has no levels on %s", game_id, slot.species, url)
                continue

            found.append(
                WildAcquisition(
                    game=game_id,
                    target=target,
                    location=here,
                    method=method,
                    levels=LevelRange(minimum=levels[0], maximum=levels[1]),
                    time_of_day=_listed(slot.times, slot.time_columns),
                    weather=_listed(slot.weathers, slot.weather_columns),
                    requirement=_legends_requirement(slot, said=said),
                    source=citation,
                )
            )

    return found


def _legends_requirement(slot: LegendsSlot, *, said: Mapping[str, str]) -> str | None:
    """What this row asks that its method, its place, its hours and its sky do not say.

    Two things, and the second is this game's own. A group's heading can mean more than the
    method it maps to, which is what ``requirements`` is for on the older tables as well. And a
    row with an empty Levels column and a filled Alpha Levels one is the page saying the only
    one here is an alpha - a real restriction, because alphas do not appear at all until the
    player has got far enough.
    """
    return (
        "; ".join(
            one
            for one in (
                said.get(slot.group),
                "Only as an alpha" if slot.levels is None and slot.alpha_levels else None,
            )
            if one
        )
        or None
    )


def _listed(ticked: Sequence[str], columns: int) -> str | None:
    """The ticked columns of one block as a phrase, or nothing when they say nothing.

    Every column ticked is the page saying the species is there whatever the sky is doing, which
    is no condition at all; none ticked is a row that says nothing either way. Both become an
    empty field rather than a list of six weathers a reader has to notice adds up to "any".
    """
    if not ticked or len(ticked) >= columns:
        return None

    words = [one.lower() for one in ticked]
    if len(words) == 1:
        return words[0]

    return f"{', '.join(words[:-1])} and {words[-1]}"


def _legends_slots(page: HTMLParser, *, title: str) -> list[LegendsSlot]:
    """Every Legends row on one page, each carrying the heading it sits under.

    Read in document order rather than by pulling the tables out, because the heading above a
    table is part of what the table says. Nothing in Hisui needed that - one of those pages is
    one place, and the heading over its table is the word "Pokemon" - and Z-A's expansion cannot
    do without it: eighteen pages by type, each cut into sections by star rating, each section
    numbering its zones from one again.
    """
    body = page.css_first("#mw-content-text")
    if body is None:
        raise EncounterTableError(f"{title} has no article body")

    found: list[LegendsSlot] = []
    section = ""

    # Walked rather than selected: a css selector for several tags hands back all of one tag
    # and then all of the next, which put every row on a page under that page's last heading.
    for node in body.traverse(include_text=False):
        if node.tag in ("h2", "h3", "h4"):
            section = _text(node)
        elif node.tag == "table":
            found.extend(_legends_rows(node, section=section))

    return found


def _legends_rows(table: Node, *, section: str = "") -> list[LegendsSlot]:
    """One table's rows, when it is a Legends table, and nothing at all when it is not."""
    rows = table.css("tr")
    if len(rows) < 3:
        return []

    columns = _legends_columns(rows[0], rows[1])
    if columns is None:
        return []

    names, width = columns
    times = sum(1 for _, kind in names if kind == "time")
    weathers = sum(1 for _, kind in names if kind == "weather")

    found: list[LegendsSlot] = []
    group = ""

    for row in rows[2:]:
        cells = [cell for cell in row.iter() if cell.tag in ("td", "th")]

        if len(cells) == 1:
            # A heading inside the table, which is where these pages write the method.
            group = _text(cells[0])
            continue

        made = _legends_slot(cells, group=group, names=names, width=width)
        if made is not None:
            found.append(
                replace(made, section=section, time_columns=times, weather_columns=weathers)
            )

    return found


def _legends_columns(header: Node, icons: Node) -> tuple[list[tuple[str, str]], int] | None:
    """What each column of this table is, read off its two header rows.

    **The header is what says a table is one of these**, which is the lesson the Generation 8
    grass tables taught: the pair of letters and the split rate column were both written into a
    reader as constants, and both turned out to be the header's business. So this reads the
    header first and gives up on anything not shaped like a Legends table, rather than reading
    rows and hoping.

    The first row names the blocks and says how wide each one is; the second names each column
    of each block, and only of the blocks - the first three cells of the first row span both
    rows, so the second holds nothing for them. A column's name is its icon's alt text, because
    the wiki writes these as pictures with no words at all.
    """
    top = [cell for cell in header.iter() if cell.tag in ("td", "th")]
    if not top or _text(top[0]) not in LEGENDS_FIRST_COLUMN:
        return None

    blocks = [(_text(cell), int(cell.attributes.get("colspan", "1"))) for cell in top]
    if not any(label == TIME_BLOCK and span > 1 for label, span in blocks):
        return None

    named = iter(
        img.attributes.get("alt", "")
        for cell in icons.iter()
        if cell.tag in ("td", "th")
        for img in cell.css("img")
    )

    columns: list[tuple[str, str]] = []
    for label, span in blocks:
        if span == 1:
            columns.append((label, "column"))
            continue

        kind = "time" if label == TIME_BLOCK else "weather"
        columns.extend((next(named, label), kind) for _ in range(span))

    return columns, len(columns)


def _legends_slot(
    cells: Sequence[Node],
    *,
    group: str,
    names: Sequence[tuple[str, str]],
    width: int,
) -> LegendsSlot | None:
    """One row, expanded to the table's full width and read against the column names.

    **A cell spans whatever somebody typed.** A row that is there at every hour writes one cell
    over the four time columns; one that is there in any weather writes ``colspan="9"`` over six
    columns, because nine is a number and a browser stops at the edge of the table anyway. So
    the spans are expanded and then cut back to the width the header declared.
    """
    spread: list[Node] = []
    for cell in cells:
        span = int(cell.attributes.get("colspan", "1"))
        spread.extend([cell] * max(span, 1))

    if len(spread) < width:
        return None

    plain = [_text(cell) for cell in spread[:width]]
    species = _species_name(spread[0])
    if not species:
        return None

    levels = {
        label: _range(text)
        for (label, kind), text in zip(names, plain, strict=True)
        if kind == "column"
    }
    ticked = {
        kind: tuple(
            label
            for (label, this), text in zip(names, plain, strict=True)
            if this == kind and TICK in text
        )
        for kind in ("time", "weather")
    }

    return LegendsSlot(
        species=species,
        form=_form_phrase(plain[0], species),
        group=group,
        levels=levels.get("Levels"),
        alpha_levels=levels.get(ALPHA_LEVELS),
        times=ticked["time"],
        weathers=ticked["weather"],
    )


def _form_phrase(text: str, species: str) -> str:
    """What the species cell says after the species name, with its decorations taken off.

    The cell is a menu sprite, the species name, sometimes a form name run straight onto it, and
    then any of a dagger pointing at a footnote, a bracketed note number, the word Shiny and an
    alpha badge. Taking the species name off the front and the decorations off the back leaves
    the form's name or nothing.
    """
    rest = text
    if rest.startswith(species):
        rest = rest[len(species) :]

    for decoration in DECORATIONS:
        rest = rest.replace(decoration, " ")

    rest = _NOTE.sub(" ", rest)

    return " ".join(rest.split())


def _species_name(cell: Node) -> str:
    """The species a row is about, taken from its link rather than from its text.

    The cell holds a menu sprite, sometimes an alpha badge, a dagger pointing at a footnote, the
    word Shiny, and - on sixteen species in Hisui - a form name run straight onto the end of the
    species name, so that the text of the cell reads "SneaselHisuian Form". The link says
    "Sneasel (Pokémon)", and says it the same way every time.

    Which form it is goes deliberately unread. These records name species, the way every other
    game's do; which Sneasel this is belongs to the form table, and step 8 is where it is
    answered.
    """
    for link in cell.css("a"):
        title = link.attributes.get("title", "")
        if title.endswith(("(Pokémon)", "(Pokemon)")):
            return title.rsplit("(", 1)[0].strip()

    return ""


def _range(text: str) -> tuple[int, int] | None:
    """One level column, which is "3-6", or "40", or empty."""
    numbers = [int(one) for one in _NUMBER.findall(text)]

    return (min(numbers), max(numbers)) if numbers else None
