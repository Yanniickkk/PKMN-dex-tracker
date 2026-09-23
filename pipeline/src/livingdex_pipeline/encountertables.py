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
from dataclasses import dataclass

from selectolax.parser import HTMLParser, Node

from .http import PoliteClient
from .models import DexTarget, EncounterMethod, LevelRange, SourceCitation, WildAcquisition
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
    refresh: bool = False,
) -> list[WildAcquisition]:
    """Every wild slot these pages give one game, for the species given.

    ``pages`` maps a Bulbapedia page title to the name this dataset gives the place, because
    the two disagree often enough to matter: the wiki writes "Hoenn Route 101" to tell it from
    Kanto's, and everything else in this dataset - including the gifts and statics of the same
    game, which still come from PokeAPI - calls it "Route 101".

    ``column`` is how the Games column spells this game: "OR" or "AS".

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
        slots = _slots(page, title=title)

        if not slots:
            # Loud rather than silent. A page with no rows for either half is either a place
            # these games do not have or a page that has been rewritten, and both are worth a
            # human's attention rather than a quietly shorter dataset.
            log.warning("%s: no Omega Ruby or Alpha Sapphire rows on %s", game_id, url)
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

    Two kinds, in the order a player would want them: where to be standing, which is what the
    Location column says beyond the method it maps to, and then what has to be true first,
    which is what the headings say. A heading that only repeats either word is dropped, and one
    reworded as nothing is dropped too - "Underwater" above rows that are already dives.
    """
    return (
        "; ".join(
            one
            for one in (
                said.get(slot.method),
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


def _slots(page: HTMLParser, *, title: str) -> list[TableSlot]:
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
            found.extend(_rows(node, sub_area=sub_area))

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


def _rows(table: Node, *, sub_area: str | None) -> list[TableSlot]:
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

        if len(cells) != 6:
            continue

        slot = _slot(cells, headings=headings, sub_area=sub_area)
        if slot is not None:
            found.append(slot)
            in_group = True

    return found


def _slot(
    cells: list[Node],
    *,
    headings: Sequence[str],
    sub_area: str | None,
) -> TableSlot | None:
    species, first, second, where, levels, rate = cells

    if (_text(first), _text(second)) != ("OR", "AS"):
        # Another generation's rows, or the header row of this one.
        return None

    games = frozenset(_text(cell) for cell in (first, second) if _present(cell))
    if not games:
        return None

    numbers = [int(one) for one in _NUMBER.findall(_text(levels))]
    if not numbers:
        return None

    rate_match = _RATE.search(_text(rate))

    return TableSlot(
        species=_text(species),
        method=_text(where),
        headings=tuple(headings),
        sub_area=sub_area,
        lowest=min(numbers),
        highest=max(numbers),
        # "??%" is the wiki saying nobody has measured it, and Soaring's flocks are graded in
        # words rather than numbers. Both become no rate rather than a made-up one.
        rate_percent=float(rate_match.group(1)) if rate_match else None,
        games=games,
    )


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
