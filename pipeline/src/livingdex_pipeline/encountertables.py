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
    GiftAcquisition,
    GiftKind,
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


# ---------------------------------------------------------------------------
# Scarlet and Violet's tables, which are a third table on the same wiki.
# ---------------------------------------------------------------------------

#: The block that says a table belongs to Scarlet and Violet, and the whole reason for a third
#: reader.
#:
#: **These games do not roll a rate, and they do not merely stand something in the world
#: either**, which is what makes them their own shape. A Pokemon spawns at a point with a
#: *weight* against the others that can spawn there - 60, or 80, or 1 - and the page says in its
#: own legend that a higher weight generally means more likely, and then stops.
#: :attr:`WildAcquisition.probability_weight` is where it goes, because turning it into a
#: percentage here would be inventing a denominator nobody was ever shown.
WEIGHT_BLOCK = "Probability Weight"

#: The other block, which is five places to be rather than five ways of looking.
#:
#: Land, water, under the water, hovering over the ground and high in the sky - and a row is
#: ticked in every one it is found in, so a Wingull on a beach is three ticks and three records.
#: ``terrains`` maps each column onto a way of meeting something.
TERRAIN_BLOCK = "Terrain"

#: The Games block, which these tables put *after* the species rather than before it.
GAMES_BLOCK = "Games"

#: The two columns about group spawns, which are read and deliberately not recorded as a rate.
#:
#: A row that leads a group carries a percentage and the name of what the group is made of, and
#: the two are about a cluster arriving rather than about this Pokemon being here. The species
#: it names is the interesting half: a Pawmo in Area Zero leads a group of **Pawmi**, which is a
#: different Pokemon from the one the row is about.
GROUP_RATE = "Group Rate"
GROUP_SPECIES = "Group Pokémon"

#: The one plain column these tables share with every other table on the wiki.
LEVELS = "Levels"


@dataclass(frozen=True)
class PaldeaSlot:
    """One row of one Scarlet and Violet table, before it is matched against a species id."""

    species: str
    #: What the cell wrote after the species name: "Paldean Form", "Pom-Pom Style", "Male".
    form: str
    #: The one-cell heading above this row, which on these pages is the biome: Prairie, Forest,
    #: Cave, Lake, Ocean, Ruins. Never a method and never a condition - it is where in this
    #: place the Pokemon is.
    biome: str
    #: The halves whose letter is filled in rather than left white.
    games: frozenset[str]
    #: The terrain columns this row is ticked in, in the order the header writes them.
    terrains: tuple[str, ...]
    #: Every level band the cell names. Two where an area has a low half and a high half, which
    #: is Kitakami's shape: "30-39, 50-53" is two bands and not a range with a hole in it.
    levels: tuple[tuple[int, int], ...]
    #: The weight at each time column, in the header's order, with that column's own name.
    weights: tuple[tuple[str, int], ...]
    #: What the group columns say, unparsed. Kept because the species named is sometimes not
    #: the species the row is about.
    group_rate: str
    group_species: str
    #: The article heading this row's table sits under, or "" when it sits under none.
    section: str = ""


def paldea_encounters(
    client: PoliteClient,
    *,
    game_id: str,
    version: str,
    pages: Mapping[str, str],
    terrains: Mapping[str, EncounterMethod],
    species: set[str],
    forms: Sequence[Form] = (),
    form_names: Mapping[str, str] | None = None,
    aliases: Mapping[str, str] | None = None,
    refresh: bool = False,
) -> list[WildAcquisition]:
    """Every wild slot Scarlet and Violet's pages give, for the species given.

    A third reader beside :func:`table_encounters` and :func:`legends_encounters`, and it is
    closer to the second than the first: there is no rate, nothing is met by pushing into grass,
    and what a row carries is ticks. What it has that neither of the others has is a **weight**
    and a **terrain block**, and those are the two reasons it cannot be either of them.

    **The weight is not a rate and is not made into one.** The page's own legend says a higher
    probability weight generally means a Pokemon is more likely to spawn "relative to others
    that can spawn there", and stops there. Making that a percentage would need a denominator
    that depends on the biome, the terrain and the hour at once, and would hand a player a
    number no game ever showed them. So ``rate_percent`` stays empty, and the weight is
    recorded as itself.

    **The terrain block is five places, and a row ticked in three of them is three records.**
    Land, water surface, underwater, overland and sky: a Wingull on a beach walks on the sand,
    hovers over it and circles above it, and an Arrokuda is only ever under the water. Mapping
    those onto one method would lose the one thing a player needs, which is where to look.
    ``terrains`` maps each column name onto a way of meeting something, and a column missing
    from it is skipped, which is the guard the other two readers have against a heading nobody
    has read.

    **The weight block is the hours**, in the shape Brilliant Diamond's reader learned to read
    off the header instead of assuming: one cell spanning all four is a Pokemon that is there
    whatever the time, and four numbers is one that is not. A zero is an hour it is absent for,
    and two different non-zero numbers are two records - a Hoothoot in the Kitakami Wilds is
    weight 70 in the morning and the day and 400 in the evening and at night, which is one
    Pokemon said twice rather than one record that has to average them.

    ``version`` is the letter this half fills its Games column with - ``S`` or ``V`` - and a row
    whose letter is left white is not on this cartridge at all.
    """
    names = Normaliser(
        species_ids=species,
        form_ids={one.id for one in forms},
        aliases=dict(aliases or {}),
    )
    spelled = form_names or {}
    found: list[WildAcquisition] = []

    for title, location in pages.items():
        url = f"{BULBAPEDIA}/{title}"
        page = HTMLParser(client.get_text(url, refresh=refresh))
        citation = bulbapedia(title, retrieved_on=client.retrieved_on(url))
        slots = _paldea_slots(page, title=title)

        if not slots:
            log.warning("%s: no Scarlet and Violet rows on %s", game_id, url)
            continue

        for slot in slots:
            if version not in slot.games:
                continue

            if slot.form and slot.form not in spelled:
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

            if not slot.levels:
                log.warning("%s: %s has no levels on %s", game_id, slot.species, url)
                continue

            # Deduplicated rather than one per tick, because two of the five columns are one
            # place: a row ticked in Overland and Sky is a Pikipek that circles at two heights
            # and is caught the same way at both, and two identical records would say so twice.
            here = dict.fromkeys(
                method
                for terrain in slot.terrains
                if (method := terrains.get(terrain)) is not None
            )

            for method in here:
                for when, weight in _hours(slot.weights):
                    for lowest, highest in slot.levels:
                        found.append(
                            WildAcquisition(
                                game=game_id,
                                target=target,
                                location=location,
                                sub_area=_paldea_sub_area(slot),
                                method=method,
                                levels=LevelRange(minimum=lowest, maximum=highest),
                                probability_weight=weight,
                                time_of_day=when,
                                source=citation,
                            )
                        )

    return found


def _paldea_sub_area(slot: PaldeaSlot) -> str | None:
    """Where in this place the row is, which these pages say in two halves.

    The biome is a one-cell heading inside the table - Prairie, Forest, Cave, Lake - and the
    part of the place is an article heading above it, where a page has parts at all. The
    Terarium's Canyon Biome has five of them and South Province (Area One) has none.
    """
    return ", ".join(one for one in (slot.section, slot.biome) if one) or None


def _hours(weights: Sequence[tuple[str, int]]) -> list[tuple[str | None, int]]:
    """The hours this row is there for, grouped by the weight it has in them.

    One cell spanning the whole block is a Pokemon that is there at every hour with one weight,
    and becomes one record with nothing said about the time - and four numbers that happen to
    be equal say the same thing and are read the same way. A zero is an hour it is not there
    for, and is dropped rather than recorded as a slot with no chance in it.
    """
    here = [(name, weight) for name, weight in weights if weight > 0]
    if not here:
        return []

    if len({weight for _, weight in here}) == 1 and len(here) == len(weights):
        return [(None, here[0][1])]

    grouped: dict[int, list[str]] = {}
    for name, weight in here:
        grouped.setdefault(weight, []).append(name)

    return [(_listed(tuple(when), len(weights)), weight) for weight, when in grouped.items()]


def _paldea_slots(page: HTMLParser, *, title: str) -> list[PaldeaSlot]:
    """Every Scarlet and Violet row on one page, each carrying the heading it sits under.

    Walked in document order for the reason :func:`_legends_slots` gives, and it matters more
    here: the Terarium's biome pages carry five tables under five headings, and a selector that
    handed back all the headings and then all the tables would put every row in the last one.
    """
    body = page.css_first("#mw-content-text")
    if body is None:
        raise EncounterTableError(f"{title} has no article body")

    found: list[PaldeaSlot] = []
    section = ""

    for node in body.traverse(include_text=False):
        if node.tag in ("h2", "h3", "h4"):
            heading = _text(node)
            # "Pokemon" is the heading the tables live under rather than a part of anywhere,
            # and repeating it in every sub-area would be saying nothing twice.
            section = "" if heading in LEGENDS_FIRST_COLUMN else heading
        elif node.tag == "table":
            found.extend(_paldea_rows(node, section=section))

    return found


def _paldea_rows(table: Node, *, section: str = "") -> list[PaldeaSlot]:
    """One table's rows, when it is a Scarlet and Violet table, and nothing when it is not."""
    rows = table.css("tr")
    if len(rows) < 3:
        return []

    columns = _paldea_columns(rows[0], rows[1])
    if columns is None:
        return []

    found: list[PaldeaSlot] = []
    biome = ""

    for row in rows[2:]:
        cells = [cell for cell in row.iter() if cell.tag in ("td", "th")]

        if len(cells) == 1:
            # A one-cell row is the biome - or the legend at the foot of the table, which is a
            # paragraph wearing a heading's clothes.
            heading = _text(cells[0])
            if LEGEND not in heading:
                biome = heading
            continue

        made = _paldea_slot(cells, biome=biome, names=columns)
        if made is not None:
            found.append(replace(made, section=section))

    return found


def _paldea_columns(header: Node, icons: Node) -> list[tuple[str, str]] | None:
    """What each column of this table is, read off its two header rows.

    The header is what says a table is one of these, which is the rule all three readers on
    this wiki now follow. A Scarlet and Violet table is the one with a Probability Weight block
    in it: nothing else on the wiki writes those two words in a header, and the older games
    these pages share space with have neither block.

    Both blocks are named by icons with no words, and the order they are written in is the
    order the columns appear, so they are read rather than counted: the terrain block is five
    wide on every page today and the weight block four, and neither number is written down
    here. That is Brilliant Diamond's lesson, which cost a reader two constants.
    """
    top = [cell for cell in header.iter() if cell.tag in ("td", "th")]
    if not top or _text(top[0]) not in LEGENDS_FIRST_COLUMN:
        return None

    blocks = [(_text(cell), int(cell.attributes.get("colspan", "1"))) for cell in top]
    if not any(label == WEIGHT_BLOCK and span > 1 for label, span in blocks):
        return None

    named = iter(
        img.attributes.get("alt", "")
        for cell in icons.iter()
        if cell.tag in ("td", "th")
        for img in cell.css("img")
    )

    columns: list[tuple[str, str]] = []
    for label, span in blocks:
        if label == GAMES_BLOCK:
            columns.extend(("", "games") for _ in range(span))
        elif label in (TERRAIN_BLOCK, WEIGHT_BLOCK):
            kind = "terrain" if label == TERRAIN_BLOCK else "weight"
            columns.extend((next(named, label), kind) for _ in range(span))
        else:
            columns.extend((label, "column") for _ in range(span))

    return columns


def _paldea_slot(
    cells: Sequence[Node],
    *,
    biome: str,
    names: Sequence[tuple[str, str]],
) -> PaldeaSlot | None:
    """One row, expanded to the table's full width and read against the column names.

    The spans are expanded for the reason :func:`_legends_slot` gives, and here one of them
    carries meaning rather than tidiness: a weight cell spanning the whole block is the page
    saying this Pokemon has the same weight at every hour of the day.
    """
    spread: list[Node] = []
    for cell in cells:
        span = int(cell.attributes.get("colspan", "1"))
        spread.extend([cell] * max(span, 1))

    if len(spread) < len(names):
        return None

    spread = spread[: len(names)]
    plain = [_text(cell) for cell in spread]

    species = _species_name(spread[0])
    if not species:
        return None

    labelled = list(zip(names, spread, plain, strict=True))

    def column(wanted: str) -> str:
        return next((text for (label, _), _, text in labelled if label == wanted), "")

    return PaldeaSlot(
        species=species,
        form=_form_phrase(plain[0], species),
        biome=biome,
        games=frozenset(
            text for (_, kind), cell, text in labelled if kind == "games" and _present(cell)
        ),
        terrains=tuple(
            label for (label, kind), _, text in labelled if kind == "terrain" and TICK in text
        ),
        levels=_bands(column(LEVELS)),
        weights=tuple(
            (label, int(text) if text.isdigit() else 0)
            for (label, kind), _, text in labelled
            if kind == "weight"
        ),
        group_rate=column(GROUP_RATE),
        group_species=column(GROUP_SPECIES),
    )


def _bands(text: str) -> tuple[tuple[int, int], ...]:
    """Every level band a cell names, which is one on most pages and two on some.

    "5-8" is one band and "30-39, 50-53" is two: an area with a low half and a high half, which
    Kitakami writes a good deal and Paldea hardly at all. Two records rather than 30-53, which
    would send a player looking for a level 45 one that is not there.
    """
    return tuple(band for part in text.split(",") if (band := _range(part)) is not None)


#: The two sections a Scarlet and Violet page keeps its one-of-a-kind Pokemon in.
#:
#: Read together because they are one table in two places: across all fifty pages there are 29
#: *Fixed encounters* tables and a single *Special encounters* one, and the header is identical.
FIXED_SECTIONS = ("Fixed encounters", "Special encounters")

#: What the Rate column of one of those tables says when the Pokemon comes back.
#:
#: 295 rows of 302 say this and seven say "Only One". That is the whole difference between a
#: Gimmighoul on a watchtower, which a player can farm, and a Titan, which stands where it was
#: beaten and is there once.
RESPAWNS = "respawns"

#: What the Location column says when it has nothing to add, which is most of the time.
#:
#: 278 of the 302 rows. The other 24 are Gimmighoul's watchtowers and the Titans' own sentence,
#: and those are worth carrying; "Fixed" copied into a requirement would be the page's own
#: scaffolding wearing a player's sentence.
NO_LOCATION = "fixed"

#: What a species cell adds on these tables and nowhere else.
#:
#: A Titan's row writes "Great TuskFormer Titan" and "TatsugiriCurly Form Former Titan" - a
#: form's name and then a badge - so the badge comes off before the rest is read as a form,
#: and it is worth a sentence on the record instead of being thrown away.
FORMER_TITAN = "Former Titan"


def paldea_fixed(
    client: PoliteClient,
    *,
    game_id: str,
    version: str,
    pages: Mapping[str, str],
    species: set[str],
    forms: Sequence[Form] = (),
    form_names: Mapping[str, str] | None = None,
    aliases: Mapping[str, str] | None = None,
    refresh: bool = False,
) -> list[GiftAcquisition]:
    """Every Pokemon standing in one spot on a Scarlet and Violet page, as a static.

    The other half of these pages, and the half the survey before this generation predicted
    would need nothing new: ``Pokemon | Games | Location | Levels | Rate``, which is the shape
    every location page in the dataset has had since Hoenn. What makes it a reader of its own
    rather than a call to :func:`table_encounters` is the Location column - there it holds a
    *method*, the word "Grass" or "Surfing" that says how a player meets the row, and here it
    holds a place, or the word "Fixed", which is the page saying nothing.

    **What it holds is a guarantee.** A weighted row in the table above says a Pokemon is in
    the pool at a spawn point; one of these says it is standing there. 295 of the 302 rows come
    back when they are caught and seven do not, and both are one Pokemon in one place, so both
    are :attr:`GiftKind.STATIC_ENCOUNTER` and the Rate column becomes a sentence rather than a
    second kind of record.

    Ten species are here and in no wild table at all: the Titans that stay where they were
    beaten, Gimmighoul on its watchtowers, and the handful of high-level spawns that Area Zero
    and the late provinces stand rather than roll.
    """
    names = Normaliser(
        species_ids=species,
        form_ids={one.id for one in forms},
        aliases=dict(aliases or {}),
    )
    spelled = form_names or {}
    found: list[GiftAcquisition] = []

    for title, location in pages.items():
        url = f"{BULBAPEDIA}/{title}"
        page = HTMLParser(client.get_text(url, refresh=refresh))
        citation = bulbapedia(title, retrieved_on=client.retrieved_on(url))

        for cells in _fixed_rows(page, title=title):
            plain = [_text(cell) for cell in cells]
            here, there = cells[1], cells[2]
            letters = {
                text for cell, text in ((here, plain[1]), (there, plain[2])) if _present(cell)
            }
            if version not in letters:
                continue

            species_name = _species_name(cells[0])
            if not species_name:
                continue

            phrase = _form_phrase(plain[0], species_name)
            titan = FORMER_TITAN in phrase
            phrase = " ".join(phrase.replace(FORMER_TITAN, " ").split())

            if phrase and phrase not in spelled:
                log.warning(
                    "%s: %s is written %r on %s and nothing says what that is",
                    game_id,
                    species_name,
                    phrase,
                    url,
                )

            target = names.target(species_name, spelled.get(phrase))
            if target is None:
                log.warning("%s: no species matches %r on %s", game_id, species_name, url)
                continue

            levels = _range(plain[4])

            found.append(
                GiftAcquisition(
                    game=game_id,
                    target=target,
                    gift_kind=GiftKind.STATIC_ENCOUNTER,
                    location=location,
                    level=levels[0] if levels else None,
                    requirement=_fixed_requirement(plain[3], plain[5], titan=titan),
                    source=citation,
                )
            )

    return found


def _fixed_requirement(where: str, rate: str, *, titan: bool) -> str | None:
    """What this row asks or offers that its place and its level do not say.

    Three things, and a row usually has one: where in the place it stands, when the page
    bothers to say; whether it comes back, which 295 of 302 rows do and is the reason a player
    can stop worrying about it; and whether it is a Titan standing where it was beaten, which
    is a badge on the species cell rather than a column.
    """
    said = []
    if where and where.lower() != NO_LOCATION:
        said.append(where)
    if titan and "Titan" not in where:
        # Said once. The Titans' rows write the badge on the species cell *and* spell the same
        # thing out in the Location column, and a record that carries both reads like a stutter.
        said.append("The Titan, once it has been beaten")

    said.append(
        "respawns after it is caught" if rate.lower() == RESPAWNS else "there is only one"
    )

    return "; ".join(said) or None


def _fixed_rows(page: HTMLParser, *, title: str) -> list[list[Node]]:
    """Every row of every fixed-encounter table on one page, expanded to six cells.

    The Games block spans six columns and the Rate block three, which is the wiki writing a
    table wide enough to sit beside the one above it; the cells themselves are one per column,
    so nothing has to be expanded and a row is six cells or it is not one of these.
    """
    body = page.css_first("#mw-content-text")
    if body is None:
        raise EncounterTableError(f"{title} has no article body")

    found: list[list[Node]] = []
    inside = False

    for node in body.traverse(include_text=False):
        if node.tag == "h2":
            inside = _text(node) in FIXED_SECTIONS
        elif node.tag == "table" and inside:
            for row in node.css("tr")[1:]:
                cells = [cell for cell in row.iter() if cell.tag in ("td", "th")]
                if len(cells) == 6:
                    found.append(cells)

    return found
