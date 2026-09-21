"""Deciding what to believe when two sources disagree.

Sources are ranked once, in the scraper registry, and that ranking settles every disagreement.
The point of doing it here rather than by overwriting as records arrive is that the losing value
is written down: a conflict log is how a wrong encounter rate gets found later, and how anyone
can tell a genuine disagreement from a scraper bug.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .scrape import ScrapedRecord

#: What identifies "the same fact from two sources". Not the whole record: the fields that
#: differ are exactly what we want to compare rather than treat as separate records.
RecordKey = tuple[str, ...]


def default_key(record: ScrapedRecord) -> RecordKey:
    """Same kind, same game, same subject, same place."""
    names = tuple(f"{key}={value}" for key, value in sorted(record.names.items()))
    where = str(record.fields.get("location", ""))
    method = str(record.fields.get("method", ""))

    return (record.kind, record.game, *names, where, method)


@dataclass(frozen=True)
class Conflict:
    """Two sources said different things about the same field of the same fact."""

    key: RecordKey
    field_name: str
    winner: str
    winning_value: Any
    loser: str
    losing_value: Any

    def describe(self) -> str:
        return (
            f"{'/'.join(self.key)}: {self.field_name} = {self.winning_value!r} ({self.winner}) "
            f"over {self.losing_value!r} ({self.loser})"
        )


@dataclass
class MergeResult:
    records: list[ScrapedRecord] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.conflicts

    def write_conflict_log(self, path: Path) -> None:
        """Conflicts as JSON beside the dataset, so a build leaves its reasoning behind."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                [
                    {
                        "key": list(conflict.key),
                        "field": conflict.field_name,
                        "winner": conflict.winner,
                        "winningValue": conflict.winning_value,
                        "loser": conflict.loser,
                        "losingValue": conflict.losing_value,
                    }
                    for conflict in self.conflicts
                ],
                indent=2,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )


class Merger:
    """Folds records from several sources into one, most trusted source winning."""

    def __init__(self, precedence: Iterable[str]) -> None:
        self._rank = {name: index for index, name in enumerate(precedence)}

    def rank_of(self, source: str) -> int:
        """Lower is more trusted. An unregistered source ranks below every registered one."""
        return self._rank.get(source, len(self._rank))

    def merge(
        self,
        records: Iterable[ScrapedRecord],
        key: Callable[[ScrapedRecord], RecordKey] = default_key,
    ) -> MergeResult:
        result = MergeResult()
        best: dict[RecordKey, ScrapedRecord] = {}

        # Sorting by rank first means the winner is already in place when a rival turns up, so
        # the comparison below is always "the challenger lost", which keeps the log readable.
        ordered = sorted(records, key=lambda record: self.rank_of(record.source))

        for record in ordered:
            record_key = key(record)
            incumbent = best.get(record_key)

            if incumbent is None:
                best[record_key] = record
                continue

            result.conflicts.extend(self._compare(record_key, incumbent, record))

        result.records = list(best.values())
        return result

    @staticmethod
    def _compare(
        record_key: RecordKey,
        winner: ScrapedRecord,
        loser: ScrapedRecord,
    ) -> list[Conflict]:
        conflicts: list[Conflict] = []

        for field_name in sorted(set(winner.fields) | set(loser.fields)):
            winning_value = winner.fields.get(field_name)
            losing_value = loser.fields.get(field_name)

            # A source that simply has nothing to say about a field is not disagreeing.
            if losing_value is None or winning_value == losing_value:
                continue

            conflicts.append(
                Conflict(
                    key=record_key,
                    field_name=field_name,
                    winner=winner.source,
                    winning_value=winning_value,
                    loser=loser.source,
                    losing_value=losing_value,
                )
            )

        return conflicts
