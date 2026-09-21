"""Matching what a source calls something onto the id the dataset uses.

Sources write "Nidoran&#9792;", "Farfetch'd", "Mr. Mime" and "Alolan Vulpix"; the dataset says
``nidoran-f``, ``farfetchd``, ``mr-mime`` and ``vulpix`` plus the form ``vulpix-alola``. This
module does that mapping and, just as importantly, reports what it could not map instead of
guessing. An unmatched name is a gap somebody has to look at, not something to paper over.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from .models import DexTarget

#: Names no amount of slugifying will get right, so they are stated outright.
DEFAULT_ALIASES: dict[str, str] = {
    "nidoran-female": "nidoran-f",
    "nidoran-male": "nidoran-m",
    "nidoran-f": "nidoran-f",
    "nidoran-m": "nidoran-m",
    "mr-mime": "mr-mime",
    "mime-jr": "mime-jr",
    "farfetchd": "farfetchd",
    "sirfetchd": "sirfetchd",
    "ho-oh": "ho-oh",
    "porygon-z": "porygon-z",
    "type-null": "type-null",
    "jangmo-o": "jangmo-o",
    "hakamo-o": "hakamo-o",
    "kommo-o": "kommo-o",
    "flabebe": "flabebe",
}

_NON_ALPHANUMERIC = re.compile(r"[^a-z0-9]+")

#: Dropped rather than turned into a separator: PokeAPI spells Farfetch'd as
#: "farfetchd" and Type: Null as "type-null", so the punctuation disappears while the
#: space stays a word break.
_CURLY_APOSTROPHE = chr(0x2019)
_DROPPED = str.maketrans("", "", "'.:%" + _CURLY_APOSTROPHE)


def slugify(name: str) -> str:
    """A source's spelling reduced to the shape the dataset uses for ids."""
    # The gender symbols have to be spelled out before the ASCII pass, or that pass throws
    # them away and Nidoran-female and Nidoran-male collapse into one name.
    spelled = name.replace("♀", "-female").replace("♂", "-male")

    # Strips accents: Flabebe, Pokemon.
    decomposed = unicodedata.normalize("NFKD", spelled)
    ascii_only = decomposed.encode("ascii", "ignore").decode("ascii")

    return _NON_ALPHANUMERIC.sub("-", ascii_only.translate(_DROPPED).lower()).strip("-")


@dataclass
class NormalisationReport:
    """What matched and what did not, so a build can say why it is incomplete."""

    matched: dict[str, DexTarget] = field(default_factory=dict)
    unmatched: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.unmatched

    def summary(self) -> str:
        return f"{len(self.matched)} matched, {len(self.unmatched)} unmatched"


class Normaliser:
    """Maps source spellings onto species and form ids."""

    def __init__(
        self,
        species_ids: set[str],
        form_ids: set[str] | None = None,
        aliases: dict[str, str] | None = None,
    ) -> None:
        self._species = set(species_ids)
        self._forms = set(form_ids or ())
        self._aliases = {**DEFAULT_ALIASES, **(aliases or {})}

    def species_id(self, name: str) -> str | None:
        """The species id for a source's spelling, or None when nothing fits."""
        slug = slugify(name)
        candidate = self._aliases.get(slug, slug)
        return candidate if candidate in self._species else None

    def target(self, species_name: str, form_name: str | None = None) -> DexTarget | None:
        """A dex target, resolving the form against the species when one is named."""
        species = self.species_id(species_name)
        if species is None:
            return None

        if not form_name:
            return DexTarget(species=species)

        form = f"{species}-{slugify(form_name)}"
        # A form the dataset does not know is dropped back to the base species rather than
        # inventing an id: the species fact is still true and usable.
        if form in self._forms:
            return DexTarget(species=species, form=form)

        return DexTarget(species=species)

    def normalise_all(self, names: list[str]) -> NormalisationReport:
        report = NormalisationReport()

        for name in names:
            target = self.target(name)
            if target is None:
                report.unmatched.append(name)
            else:
                report.matched[name] = target

        return report
