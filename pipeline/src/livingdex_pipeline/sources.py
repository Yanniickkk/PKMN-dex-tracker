"""Citations for facts that did not come from an API.

Most of the dataset can point at the PokeAPI URL it was read from. What a game's own file
carries - who trades what, which parent lays which egg, where a swarm turns up - was read off a
wiki by a person, and it still has to say where. A citation is a note about where a fact came
from, not a record of a request this pipeline made.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date

from .models import SourceCitation

BULBAPEDIA = "https://bulbapedia.bulbagarden.net/wiki"


def bulbapedia(page: str, *, retrieved_on: date) -> SourceCitation:
    """A citation for one Bulbapedia article, named the way its URL spells it."""
    return SourceCitation(
        source="bulbapedia",
        url=f"{BULBAPEDIA}/{page}",
        retrieved_on=retrieved_on,
    )


class ReadByHand:
    """The pages one module's hand-written tables were typed from, and the day each was read.

    A fetched citation takes its date from the cache entry the answer came out of, so a rebuild
    from unchanged pages does not re-date what nobody touched. A hand-written table has no fetch
    to take a date from, and it used to take the build day instead - which said a person had been
    reading Bulbapedia this morning, and said something different tomorrow about the same
    unchanged table.

    So the module that holds the table holds the day it was read, beside it. There is no way to
    work this out after the fact, which is why the guess is not offered: a page this table does
    not name raises rather than falling back to today, so a new table cannot quietly inherit a
    date nobody chose for it.
    """

    def __init__(self, pages: Mapping[str, date]) -> None:
        self._pages = dict(pages)

    def __call__(self, page: str) -> SourceCitation:
        """Cite one of those pages, dated the day it was read."""
        if page not in self._pages:
            known = ", ".join(sorted(self._pages)) or "nothing"
            raise KeyError(f"no read date for {page!r}; this table knows {known}")
        return bulbapedia(page, retrieved_on=self._pages[page])

    def __contains__(self, page: object) -> bool:
        return page in self._pages
