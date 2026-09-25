"""Citations for what a person read rather than what the pipeline fetched.

A fetched citation takes its date from the cache entry the answer came out of. A hand-written
table has no fetch to take one from, and it used to take the build day - which said a reader had
been on Bulbapedia this morning, and said something else tomorrow about the same table.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from livingdex_pipeline import gamedefs
from livingdex_pipeline.sources import BULBAPEDIA, ReadByHand


def test_a_page_is_cited_with_the_day_it_was_read() -> None:
    read_on = ReadByHand({"In-game_trade": date(2026, 9, 22)})

    citation = read_on("In-game_trade")

    assert citation.source == "bulbapedia"
    assert citation.url == f"{BULBAPEDIA}/In-game_trade"
    assert citation.retrieved_on == date(2026, 9, 22)


def test_a_page_with_no_date_raises_rather_than_guessing_one() -> None:
    # The whole point. A table this one does not name has a date nobody wrote down, and the only
    # honest answers are to write it down or to fail - not to quietly say today.
    read_on = ReadByHand({"In-game_trade": date(2026, 9, 22)})

    with pytest.raises(KeyError, match="no read date for 'Fossil'"):
        read_on("Fossil")

    assert "In-game_trade" in read_on
    assert "Fossil" not in read_on


def test_no_game_module_dates_a_citation_with_the_day_the_build_ran() -> None:
    # A guard rather than a check: the habit is one line long and comes back easily, and the
    # cost of it coming back is a few thousand records re-dated by every build that crosses
    # midnight. Six games are still to be written, and each will bring tables of its own.
    here = Path(gamedefs.__file__).parent

    guilty = [
        one.name
        for one in sorted(here.glob("*.py"))
        if "date.today()" in one.read_text(encoding="utf-8")
    ]

    assert guilty == []
