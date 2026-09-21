"""Base for the per-source scrapers that Phase 2 fills in.

A scraper's job is to turn one source's pages into loose records naming things the way that
source names them. It does not decide what is true and it does not know about PokeAPI ids;
:mod:`normalise` maps the names and :mod:`merge` decides who wins. Keeping those apart is what
makes a disagreement between two sources visible instead of silently resolved by whichever ran
last.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from selectolax.parser import HTMLParser

from .http import PoliteClient
from .models import SourceCitation


@dataclass(frozen=True)
class ScrapedRecord:
    """One fact from one page, before anything has been matched or reconciled.

    ``names`` holds whatever the source called things; the normaliser replaces them with ids.
    ``fields`` is free-form because each record kind needs different columns, and the shape is
    only pinned once it becomes a real model in :mod:`merge`.
    """

    source: str
    kind: str
    game: str
    names: dict[str, str]
    fields: dict[str, Any] = field(default_factory=dict)
    url: str | None = None

    def citation(self, retrieved_on: date) -> SourceCitation:
        return SourceCitation(source=self.source, url=self.url, retrieved_on=retrieved_on)


class Scraper(ABC):
    """One source. Subclasses say where pages live and how to read them."""

    #: Short name used in citations and in the precedence order, for example ``bulbapedia``.
    name: str

    #: Where this source lives, for building page URLs.
    base_url: str

    def __init__(self, client: PoliteClient) -> None:
        self._client = client

    @abstractmethod
    def scrape_game(self, game_id: str, *, refresh: bool = False) -> list[ScrapedRecord]:
        """Every record this source has about one game."""

    def page(self, url: str, *, refresh: bool = False) -> HTMLParser:
        """A parsed page. Cached and rate limited by the client, not by this class."""
        return HTMLParser(self._client.get_text(url, refresh=refresh))

    def url_for(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"


class ScraperRegistry:
    """The scrapers a build should run, in the order their sources are trusted.

    Order matters: it is the precedence :mod:`merge` uses, so registering a source is also
    a statement about how much it is believed relative to the others.
    """

    def __init__(self) -> None:
        self._scrapers: list[Scraper] = []

    def register(self, scraper: Scraper) -> None:
        if any(existing.name == scraper.name for existing in self._scrapers):
            raise ValueError(f"a scraper named {scraper.name} is already registered")

        self._scrapers.append(scraper)

    @property
    def scrapers(self) -> list[Scraper]:
        return list(self._scrapers)

    @property
    def precedence(self) -> list[str]:
        """Source names, most trusted first."""
        return [scraper.name for scraper in self._scrapers]

    def scrape_game(self, game_id: str, *, refresh: bool = False) -> list[ScrapedRecord]:
        records: list[ScrapedRecord] = []
        for scraper in self._scrapers:
            records.extend(scraper.scrape_game(game_id, refresh=refresh))

        return records
