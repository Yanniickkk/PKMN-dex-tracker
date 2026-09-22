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
    _cache: dict[str, tuple[str, str | None]] = field(default_factory=dict)

    def of(self, area_slug: str) -> tuple[str, str | None]:
        if area_slug in self._cache:
            return self._cache[area_slug]

        area = self.api.resource(f"location-area/{area_slug}", refresh=self.refresh)
        location_slug = area["location"]["name"]
        location = self.api.resource(f"location/{location_slug}", refresh=self.refresh)

        name = english(location.get("names", []), fallback=pretty(location_slug))
        self._cache[area_slug] = (
            self.renamed.get(name, name),
            sub_area(area_slug, location_slug),
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
    """
    tail = area_slug.removesuffix("-area")
    if tail == location_slug:
        return None

    return pretty(tail.removeprefix(f"{location_slug}-")) or None


def pretty(slug: str) -> str:
    """A slug as words. Floor names keep their shape: ``b1f`` is B1F, not "B1f"."""
    words = [
        word.upper() if _is_floor(word) else word.capitalize() for word in slug.split("-") if word
    ]

    return " ".join(words)


def _is_floor(word: str) -> bool:
    body = word.removeprefix("b")
    return bool(body) and body.endswith("f") and body[:-1].isdigit()
