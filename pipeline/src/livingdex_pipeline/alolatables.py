"""The one thing the source does not say about an Alola slot: when it is there.

PokeAPI carries these games' encounter tables in full - place, method, levels, slot chance - and
carries no time of day for a single one of them. That is not a detail in Alola. Yungoos stands in
Route 2's grass by day and Alolan Rattata by night, in both halves of the pair, and a record that
says "Route 2, grass, 10%" sends half of its readers out at the wrong hour.

Bulbapedia has it, in a shape worth describing because it is not the shape :mod:`encountertables`
reads. Each location's encounter table has one **Rate** column split into two, **Day** and
**Night**, and a dash in one of them is the whole fact: a species with ``- / 10%`` is nocturnal
there. Where the two hours agree the wiki writes one cell spanning both, which is how this module
tells "the same at any hour" from "only at one of them" without comparing strings.

What is read here is only that. The places, the levels and the odds stay the source's: this asks
one question of a second source and layers the answer on top, which is the least it can do and
still be worth the fetching.

Two things fall out of the same rows and are taken while they are there. The **Location** column
names the terrain a moving spot is - rustling grass, a sand cloud, a dirt cloud, a shadow on the
water - which PokeAPI flattens into one method whose English names only the wet one. And the
games column tells the Sun and Moon tables from the Ultra ones, so this reads the right pair.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator, Mapping
from dataclasses import dataclass

import httpx
from selectolax.parser import HTMLParser, Node

from .http import PoliteClient, RobotsDisallowed
from .models import DexTarget, EncounterMethod
from .normalise import Normaliser
from .sources import BULBAPEDIA

log = logging.getLogger(__name__)

#: Bulbapedia asks for five seconds between requests, the same as the Archives.
MIN_INTERVAL = 5.0

#: Which games a row belongs to, as the table's own column spells it.
#:
#: Both pairs are on the same page and the column is the only thing that tells them apart, so
#: which one is wanted has to be asked for. They are not the same tables with a few rows added:
#: Route 2 alone has eighteen Sun and Moon rows and thirty-one Ultra ones.
SUN_AND_MOON = ("S", "M")
ULTRA_SUN_AND_MOON = ("US", "UM")

#: What the Location column calls a table, and which of this project's methods it is.
#:
#: Seven of the sixteen are one method here. PokeAPI gives Alola's ambushes as a single method
#: and calls it after the only one that happens in water; the wiki names each terrain, so the
#: record can say which without the schema growing a method per kind of ground.
METHODS: dict[str, EncounterMethod] = {
    "Grass": EncounterMethod.WALK,
    "Long grass": EncounterMethod.WALK,
    "Deep sand": EncounterMethod.WALK,
    "Cave": EncounterMethod.WALK,
    "Yellow flowers": EncounterMethod.WALK,
    "Red flowers": EncounterMethod.WALK,
    "Surfing": EncounterMethod.SURF,
    "Fishing": EncounterMethod.SUPER_ROD,
    "Berry pile": EncounterMethod.BERRY_TREE,
    "Rustling grass": EncounterMethod.MOVING_SPOT,
    "Rustling bush": EncounterMethod.MOVING_SPOT,
    "Rustling tree": EncounterMethod.MOVING_SPOT,
    "Sand cloud": EncounterMethod.MOVING_SPOT,
    "Dirt cloud": EncounterMethod.MOVING_SPOT,
    "Shadow": EncounterMethod.MOVING_SPOT,
    "Water splashes": EncounterMethod.MOVING_SPOT,
}

#: What a moving spot looks like where it is, in words a record can carry.
#:
#: Only for the ambushes: saying "in the grass" beside a grass slot would be saying the method
#: twice. A player standing on Route 2 is looking for grass that shakes; one in Haina Desert is
#: looking for a cloud of sand, and the source calls both the same thing.
TERRAIN: dict[str, str] = {
    "Rustling grass": "In grass that rustles",
    "Rustling bush": "In a bush that rustles",
    "Rustling tree": "In a tree that rustles",
    "Sand cloud": "In a cloud of sand",
    "Dirt cloud": "In a cloud of dirt",
    "Shadow": "In a shadow crossing the water",
    "Water splashes": "Where the water splashes",
    "Bubbling spot": "In a patch of bubbles on the water",
}

#: The one terrain the Location column does not name, and where it says so instead.
#:
#: A bubbling spot is fished in, so its rows are labelled "Fishing" like any other water, and
#: what tells them apart is the heading above them - "Fishing at a bubbling spot". It is the one
#: of the seven the source does name, which is how it came to name the whole family after it.
BUBBLING = "bubbling"

#: How the wiki writes a form, against the suffix the dataset's id uses.
#:
#: The two spell the same thing differently and neither is wrong: the wiki writes what a player
#: reads on the summary screen, the dataset writes what the source called the Pokemon. A name
#: that is not in here is tried as it stands, and a form that still does not resolve falls back
#: to the plain species rather than being invented - which is what :mod:`normalise` does anyway.
FORM_WORDS: dict[str, str] = {
    "Alolan Form": "alola",
    "East Sea": "east",
    "West Sea": "",
    "Pom-Pom Style": "pom-pom",
    "Pa'u Style": "pau",
    "Sensu Style": "sensu",
    "Baile Style": "",
    "Midday Form": "",
    "Midnight Form": "midnight",
    "Dusk Form": "dusk",
    "50% Forme": "",
    "10% Forme": "10",
    "Solo Form": "",
    "School Form": "school",
}


@dataclass(frozen=True)
class Reading:
    """One row of one location's table, reduced to what this module is for."""

    location: str
    target: DexTarget
    method: EncounterMethod
    #: What the Location column called it, for the terrain of an ambush.
    label: str
    #: ``"day"``, ``"night"``, or None when the row holds at any hour.
    time_of_day: str | None


def read_times(
    client: PoliteClient,
    *,
    pages: Mapping[str, str],
    normaliser: Normaliser,
    games: tuple[str, str] = SUN_AND_MOON,
    refresh: bool = False,
) -> list[Reading]:
    """Every row of every page given that belongs to ``games``, as far as it can be read.

    ``pages`` is location name to page title, because only the game's own files know which of
    the source's places the wiki calls what. A page that cannot be fetched is logged and skipped:
    this layers a second opinion on records that already stand on their own, so a hole in it
    costs a condition rather than a record.

    ``games`` is the pair whose rows are wanted, spelled as the table's own column spells it.
    One page holds both pairs' tables and nothing but that column separates them.
    """
    found: list[Reading] = []

    for location, page in sorted(pages.items()):
        try:
            html = client.get_text(f"{BULBAPEDIA}/{page}", refresh=refresh)
        except (httpx.HTTPError, RobotsDisallowed) as error:
            log.warning("no encounter table for %s at %s: %s", location, page, error)
            continue

        body = HTMLParser(html).css_first("#mw-content-text")
        if body is None:
            continue

        found.extend(
            _readings(body, location=location, normaliser=normaliser, games=games)
        )

    return found


def _readings(
    body: Node,
    *,
    location: str,
    normaliser: Normaliser,
    games: tuple[str, str],
) -> Iterator[Reading]:
    for table in body.css("table"):
        rows = table.css("tr")
        if not rows or "Allies" not in _text(rows[0]):
            continue

        heading = ""

        for row in rows:
            cells = row.css("th, td")
            if len(cells) == 1 and cells[0].tag == "th":
                heading = _text(cells[0])
                continue

            reading = _reading(
                row, location=location, heading=heading, normaliser=normaliser, games=games
            )
            if reading is not None:
                yield reading


def _reading(
    row: Node,
    *,
    location: str,
    heading: str,
    normaliser: Normaliser,
    games: tuple[str, str],
) -> Reading | None:
    """One data row, or None when it is another pair's or not a wild slot."""
    cells = row.css("th, td")
    if len(cells) < 9:
        return None

    text = [_text(one) for one in cells]
    if (text[1], text[2]) != games:
        return None

    # The last cell spans both hours when they agree, and is the Night column when they do not.
    both = cells[-1].attributes.get("colspan") == "2"
    label = text[-3] if both else text[-4]
    day, night = (text[-1], text[-1]) if both else (text[-2], text[-1])

    if BUBBLING in heading.lower():
        # The heading is doing the Location column's job, so it is read instead of it.
        method, label = EncounterMethod.MOVING_SPOT, "Bubbling spot"
    elif (found := METHODS.get(label)) is not None:
        method = found
    else:
        # A gift, a trade, a fossil, an Island Scan: every one of those has a step of its own.
        return None

    target = _target(text[3], normaliser)
    if target is None:
        return None

    return Reading(
        location=location,
        target=target,
        method=method,
        label=label,
        time_of_day=_when(day, night),
    )


def _when(day: str, night: str) -> str | None:
    """Which hours a row holds in, or None when it holds in both."""
    by_day, by_night = _present(day), _present(night)

    if by_day and not by_night:
        return "day"
    if by_night and not by_day:
        return "night"

    return None


def _present(rate: str) -> bool:
    """Whether a rate cell says the species is there at all. A dash says it is not."""
    # Hyphen, em dash and en dash: the wiki is not consistent about which it writes.
    dashes = {"-", chr(0x2014), chr(0x2013)}

    return bool(rate) and rate.strip() not in dashes


def _target(name: str, normaliser: Normaliser) -> DexTarget | None:
    """A row's Pokemon, which the wiki writes as the species and its form in one string.

    Split from the right rather than the left: "Tapu Koko" and "Type: Null" are two words and no
    form, and "Rattata Alolan Form" is one word and two. The longest prefix that is a species
    wins, which gets both without a table of exceptions.
    """
    words = name.split()

    for cut in range(len(words), 0, -1):
        species = " ".join(words[:cut])
        rest = " ".join(words[cut:])
        if normaliser.species_id(species) is None:
            continue

        form = FORM_WORDS.get(rest, rest)
        return normaliser.target(species, form or None)

    return None


def _text(node: Node) -> str:
    return " ".join(node.text(separator=" ").split())
