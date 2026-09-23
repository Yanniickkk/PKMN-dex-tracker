"""Where an encounter happens, in words a player would recognise.

PokeAPI files encounters under an *area* - ``hoenn-route-101-area``, ``sky-pillar-apex`` - and
generates the area's English name from that slug, which is how Route 101 ends up being called
"Road 101". The parent location's name is written by hand and correct, so the location comes
from there and whatever is left of the slug becomes the sub-area.

Every step that reads encounters needs this, and they share one instance so a place that a
dozen Pokemon live in is looked up once for all of them.

One location has one name in PokeAPI, and it is the newest game's. That is right for most of
the series and wrong wherever a place was renamed: Ho-Oh waits on top of the Bell Tower in
HeartGold and on top of the Tin Tower in Gold, and a Gold player reading "Bell Tower" is being
told the name of a game they are not playing. So a set of games can hand over what it calls the
places it disagrees about, and everything else is left alone.

A sub-area can be renamed the same way and for a worse reason. A sub-area's name is generated
from the slug and nobody wrote it: Unova's Season Research Lab is filed as
``unova-route-6-weather-institute``, and the Weather Institute is a building in Hoenn.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from .pokeapi import PokeApiClient


@dataclass
class LocationNames:
    """Area slug -> (location, sub-area), remembering what it has already been asked.

    ``renamed`` is what these games call a place that PokeAPI names after a later one, keyed by
    the name PokeAPI gives: ``{"Bell Tower": "Tin Tower"}``. It is a fact about a set of games
    rather than about the place, so it arrives from the module that knows which games these are,
    and a lookup that is not in it comes through untouched.

    A renaming applies before anything is written down, so a gift table's ``where`` and a
    validation message both read the name the player would.
    """

    api: PokeApiClient
    refresh: bool = False
    renamed: Mapping[str, str] = field(default_factory=dict)
    #: The same for the part below the location, keyed by what the slug generates.
    renamed_sub_areas: Mapping[str, str] = field(default_factory=dict)
    _cache: dict[str, tuple[str, str | None]] = field(default_factory=dict)

    def of(self, area_slug: str) -> tuple[str, str | None]:
        if area_slug in self._cache:
            return self._cache[area_slug]

        area = self.api.resource(f"location-area/{area_slug}", refresh=self.refresh)
        location_slug = area["location"]["name"]
        location = self.api.resource(f"location/{location_slug}", refresh=self.refresh)

        name = english(location.get("names", []), fallback=pretty(location_slug))
        below = sub_area(area_slug, location_slug)
        self._cache[area_slug] = (
            self.renamed.get(name, name),
            self.renamed_sub_areas.get(below, below) if below else below,
        )

        return self._cache[area_slug]


def english(names: list[dict], *, fallback: str) -> str:
    for entry in names:
        if entry.get("language", {}).get("name") == "en":
            return entry["name"]

    return fallback


def sub_area(area_slug: str, location_slug: str) -> str | None:
    """What is left of the area slug once the location is taken off it.

    ``meteor-falls-b1f`` under ``meteor-falls`` is "B1F"; ``hoenn-route-101-area`` is nothing,
    because the area is the whole location.

    What PokeAPI has no name for is dropped rather than printed. Unova's Victory Road is filed
    as a dozen ``unknown-area-53``, and "Victory Road, Unknown Area 62" tells a player nothing
    they can walk to - it is the source admitting it does not know, written out as if it were a
    place. Whatever else the slug holds is kept: ``1f-unknown-room`` is still 1F.
    """
    tail = area_slug.removesuffix("-area")
    if tail == location_slug:
        return None

    return pretty(_named(tail.removeprefix(f"{location_slug}-"))) or None


#: How PokeAPI spells an area it has not named: ``unknown-area-53``, or ``unknown-room``.
_UNNAMED = ("unknown-area", "unknown-room")


def _named(slug: str) -> str:
    """The slug without the part that says the source has no name for it."""
    words = slug.split("-")
    kept: list[str] = []
    index = 0

    while index < len(words):
        pair = "-".join(words[index : index + 2])

        if pair in _UNNAMED:
            # An unknown area is followed by its number, which goes with it; an unknown room
            # is not numbered.
            numbered = words[index + 2 : index + 3]
            index += 3 if pair == "unknown-area" and numbered and numbered[0].isdigit() else 2
            continue

        kept.append(words[index])
        index += 1

    return "-".join(kept)


#: Words a slug spells in lower case that are shouted in English. Only the ones the dataset has
#: met: Unova files Game Freak's offices as ``game-freak-hq``, and "Game Freak Hq" reads like a
#: typo rather than like a building. The sequels brought the second one - Relic Passage has an
#: entrance at the Pokemon World Tournament, and "Pwt Entrance" reads like nothing at all.
_ACRONYMS = frozenset({"hq", "pwt"})

#: Words English leaves in lower case in the middle of a name.
#:
#: The Hoenn remakes are what asked for this: their Mirage spots are filed as
#: ``mirage-spot-cave-north-of-fallarbor``, and a rule that capitalises every word turns two
#: dozen places into "North Of Fallarbor". Sinnoh had the same thing quietly - Spear Pillar's
#: "Between Pillars 1 And 2" - and nobody had looked.
_JOINING = frozenset({"of", "the", "and", "in", "at", "to", "on", "a"})


def pretty(slug: str) -> str:
    """A slug as words. Floor names keep their shape: ``b1f`` is B1F, not "B1f".

    A joining word keeps its lower case where English keeps it, which is anywhere but the ends
    of the name: "North of Fallarbor", and the room called "A" at the end of ``sealed-chamber-a``
    is still A.
    """
    words = [word for word in slug.split("-") if word]

    return " ".join(
        _word(word, joining=0 < position < len(words) - 1)
        for position, word in enumerate(words)
    )


def _word(word: str, *, joining: bool) -> str:
    if _is_floor(word) or word in _ACRONYMS:
        return word.upper()

    return word if joining and word in _JOINING else word.capitalize()


def _is_floor(word: str) -> bool:
    body = word.removeprefix("b")
    return bool(body) and body.endswith("f") and body[:-1].isdigit()
