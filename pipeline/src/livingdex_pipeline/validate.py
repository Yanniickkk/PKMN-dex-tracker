"""The validator the build runs before it writes anything.

This module is the harness: what a rule is, what it reports, and how a failing rule stops a
build. The rules themselves are Phase 0.7; :func:`default_rules` is empty until then, and a
build with no rules says so rather than claiming a clean bill of health.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from .models import DatasetIndex, EvolutionRule, Form, GameData, Species, TransferEdge


class Severity(StrEnum):
    """An error fails the build. A warning is written down and the build continues."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: Severity
    message: str
    game: str | None = None

    def describe(self) -> str:
        where = f" [{self.game}]" if self.game else ""
        return f"{self.severity.value}{where} {self.rule}: {self.message}"


@dataclass(frozen=True)
class GameCoverage:
    """How much of one game's dex the dataset can actually account for."""

    game: str
    full: int = 0
    partial: int = 0
    missing: int = 0
    #: Entries someone has checked and marked as not fillable here. Counted apart from
    #: the other three: a stated fact is not the same as a hole nobody has looked at.
    unobtainable: int = 0

    @property
    def total(self) -> int:
        return self.full + self.partial + self.missing + self.unobtainable


@dataclass(frozen=True)
class Dataset:
    """Everything a rule is allowed to look at, in one place."""

    index: DatasetIndex
    species: Sequence[Species]
    forms: Sequence[Form]
    evolution_rules: Sequence[EvolutionRule]
    transfers: Sequence[TransferEdge]
    games: Sequence[GameData]

    def game(self, game_id: str) -> GameData | None:
        return next((one for one in self.games if one.game.id == game_id), None)


class Rule(Protocol):
    """One check. Reports what it finds; never changes anything."""

    name: str

    def check(self, dataset: Dataset) -> Iterable[Finding]: ...


@dataclass
class ValidationReport:
    findings: list[Finding] = field(default_factory=list)
    coverage: list[GameCoverage] = field(default_factory=list)
    rules_run: list[str] = field(default_factory=list)

    @property
    def errors(self) -> list[Finding]:
        return [one for one in self.findings if one.severity is Severity.ERROR]

    @property
    def warnings(self) -> list[Finding]:
        return [one for one in self.findings if one.severity is Severity.WARNING]

    @property
    def ok(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        if not self.rules_run:
            return "no rules ran, so nothing was checked"

        return (
            f"{len(self.rules_run)} rule(s), {len(self.errors)} error(s), "
            f"{len(self.warnings)} warning(s)"
        )

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "rulesRun": self.rules_run,
                    "findings": [
                        {
                            "rule": one.rule,
                            "severity": one.severity.value,
                            "game": one.game,
                            "message": one.message,
                        }
                        for one in self.findings
                    ],
                    "coverage": [
                        {
                            "game": one.game,
                            "full": one.full,
                            "partial": one.partial,
                            "missing": one.missing,
                            "unobtainable": one.unobtainable,
                        }
                        for one in self.coverage
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )


def default_rules() -> list[Rule]:
    """The rules every build runs. Defined in :mod:`rules`; imported late to keep that module
    free to import this one."""
    from .rules import all_rules

    return all_rules()


def validate(dataset: Dataset, rules: Sequence[Rule] | None = None) -> ValidationReport:
    from .rules import coverage_for

    rules = default_rules() if rules is None else rules
    report = ValidationReport(rules_run=[rule.name for rule in rules])

    for rule in rules:
        report.findings.extend(rule.check(dataset))

    report.coverage = coverage_for(dataset)
    return report
