"""Citations for facts that did not come from an API.

Most of the dataset can point at the PokeAPI URL it was read from. What a game's own file
carries - who trades what, which parent lays which egg, where a swarm turns up - was read off a
wiki by a person, and it still has to say where. A citation is a note about where a fact came
from, not a record of a request this pipeline made.
"""

from __future__ import annotations

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
