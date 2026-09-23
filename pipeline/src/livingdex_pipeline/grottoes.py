"""Unova's Hidden Grottoes, read off Bulbapedia because PokeAPI has never heard of them.

Twenty patches of long grass hidden around the sequels' Unova, each holding a few species with
their Hidden Ability. They are wild encounters in every way a player would recognise - walk in,
meet something, catch it - and they are missing from PokeAPI's encounter tables completely, so
a dataset built from that source alone says a dozen species are nowhere in these games.

This is the first source in the dataset that is read rather than typed. Everything else a game
file knows from Bulbapedia was put there by a person and cited by hand; here the page is
fetched, parsed, and cited to the day the cache says it was fetched. Two things make that worth
doing here and not before: the tables are uniform and there is one page, so the parser is
shorter than the table it replaces; and seventy rows typed out by hand are seventy chances to
mistype a percentage nobody would ever check.

What is deliberately not read is the Funfest Missions table at the foot of the same page. Those
grottoes were opened by a mission handed out over Nintendo Wi-Fi in 2012 and 2013, the service
closed in 2014, and nobody can open one now - so Glameow, Stunky and the Eevee line are not
grotto Pokemon in any sense that fills a dex today. They belong to step 7, which is about
exactly that kind of shut door.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from selectolax.parser import HTMLParser, Node

from .http import PoliteClient
from .models import DexTarget, EncounterMethod, LevelRange, SourceCitation, WildAcquisition
from .normalise import Normaliser
from .sources import BULBAPEDIA, bulbapedia

log = logging.getLogger(__name__)

PAGE = "Hidden_Grotto"
URL = f"{BULBAPEDIA}/{PAGE}"

#: Bulbapedia states no crawl delay, so this is our own floor, borrowed from what the Archives
#: ask for. One page per game and cached after the first, so nothing here is in a hurry.
MIN_INTERVAL = 5.0

#: The heading after the last real grotto. Everything below it was a distribution.
FUNFEST = "Funfest Missions"

#: How a grotto table starts, which is how one is told from the item tables and the language
#: table on the same page.
HEADER = "Pokémon Games Location Levels Rate"

#: The colour Bulbapedia fills a game's cell with when the Pokemon is *not* in that game. The
#: page says so itself: "A colored background means that the Pokemon can be found in this
#: location in the specified game. A white background with a colored letter means that the
#: Pokemon cannot be found here."
ABSENT = "#fff"

_LEVELS = re.compile(r"(\d+)\s*-\s*(\d+)")
_RATE = re.compile(r"([\d.]+)\s*%")


class GrottoError(Exception):
    """The page could not be read the way this parser expects. The message is for a human."""


@dataclass(frozen=True)
class GrottoSlot:
    """One row of one grotto's table, before it is matched against a species id."""

    species: str
    area: str
    grotto: str | None
    lowest: int
    highest: int
    rate_percent: float
    games: frozenset[str]


def grotto_encounters(
    client: PoliteClient,
    *,
    game_id: str,
    column: str,
    species: set[str],
    refresh: bool = False,
) -> list[WildAcquisition]:
    """Every Hidden Grotto slot one of the sequels has, for the species given.

    ``column`` is how the page's Games column spells this game - "B2" or "W2". The two halves
    disagree about four of the rows, and they disagree by rate rather than by species: Lostlorn
    Forest holds a Pinsir three times as often in Black 2 as in White 2, and a Heracross the
    other way round. A parser that read the species column and ignored the colours would have
    both games right about what is there and both wrong about how long it takes.
    """
    page = HTMLParser(client.get_text(URL, refresh=refresh))
    citation = bulbapedia(PAGE, retrieved_on=client.retrieved_on(URL))
    names = Normaliser(species_ids=species)

    found: list[WildAcquisition] = []

    for slot in _slots(page):
        if column not in slot.games:
            continue

        target = names.target(slot.species)
        if target is None:
            # Loud rather than silent: a species this cannot place is a hole in a game's dex,
            # and the page naming something the dataset has never heard of is exactly the case
            # worth being told about.
            log.warning("%s: no species matches %r on %s", game_id, slot.species, URL)
            continue

        found.append(_record(slot, game_id=game_id, target=target, citation=citation))

    if not found:
        raise GrottoError(
            f"{URL} yielded no Hidden Grotto slots for {game_id}; has the page been rewritten?"
        )

    return found


def _record(
    slot: GrottoSlot,
    *,
    game_id: str,
    target: DexTarget,
    citation: SourceCitation,
) -> WildAcquisition:
    return WildAcquisition(
        game=game_id,
        target=target,
        location=slot.area,
        sub_area=slot.grotto,
        method=EncounterMethod.HIDDEN_GROTTO,
        levels=LevelRange(minimum=slot.lowest, maximum=slot.highest),
        rate_percent=slot.rate_percent,
        source=citation,
    )


def _slots(page: HTMLParser) -> list[GrottoSlot]:
    """Every row of every grotto table, in the order the page lists them."""
    body = page.css_first("#mw-content-text")
    if body is None:
        raise GrottoError(f"{URL} has no article body")

    found: list[GrottoSlot] = []
    area: str | None = None

    for node in body.traverse(include_text=False):
        if node.tag == "h3":
            area = _text(node)
            if area == FUNFEST:
                break
        elif node.tag == "table" and area is not None and _text(node).startswith(HEADER):
            found.extend(_rows(node, area=area))

    return found


def _rows(table: Node, *, area: str) -> list[GrottoSlot]:
    """One table's rows, carrying whichever grotto's heading they sit under.

    An area with two grottoes writes a heading row between them - "Dark grass" and "Pond" on
    Route 3 - and an area with one writes none. The heading becomes the sub-area, because
    "Route 3" alone would make two grottoes look like one place with six species in it.
    """
    body = table.css_first("tbody") or table
    found: list[GrottoSlot] = []
    grotto: str | None = None

    for row in body.iter():
        if row.tag != "tr":
            continue

        cells = [cell for cell in row.iter() if cell.tag in ("td", "th")]

        # A row of one cell is either a grotto's heading or the legend at the foot of the
        # table. The legend explains the colours; a heading is a place.
        if len(cells) == 1:
            heading = _text(cells[0])
            grotto = heading if "colored background" not in heading else grotto
            continue

        if len(cells) != 6:
            continue

        slot = _slot(cells, area=area, grotto=grotto)
        if slot is not None:
            found.append(slot)

    return found


def _slot(cells: list[Node], *, area: str, grotto: str | None) -> GrottoSlot | None:
    species, black, white, _where, levels, rate = cells

    levels_match = _LEVELS.search(_text(levels))
    rate_match = _RATE.search(_text(rate))
    if levels_match is None or rate_match is None:
        # The header row, and anything else shaped like a row and not filled in like one.
        return None

    return GrottoSlot(
        species=_text(species),
        area=area,
        grotto=grotto,
        lowest=int(levels_match.group(1)),
        highest=int(levels_match.group(2)),
        rate_percent=float(rate_match.group(1)),
        games=frozenset(_text(cell) for cell in (black, white) if _present(cell)),
    )


def _present(cell: Node) -> bool:
    """Whether this game's letter is filled in rather than left white."""
    return ABSENT not in cell.attributes.get("style", "").lower()


def _text(node: Node) -> str:
    return " ".join(node.text(separator=" ").split())
