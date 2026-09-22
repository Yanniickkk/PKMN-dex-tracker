"""Every game the pipeline knows how to build.

Phase 2 adds one module here per game and one line to :func:`register_all`. Registration is
explicit rather than a side effect of importing, so the set of games a build covers is readable
in one place.
"""

from __future__ import annotations

from ..games import GameRegistry
from . import emerald, firered, leafgreen, platinum, ruby, sapphire

# In the order a person would list them: the Hoenn pair, then its third version, then the Kanto
# pair, then Sinnoh.
MODULES = [ruby, sapphire, emerald, firered, leafgreen, platinum]


def register_all(registry: GameRegistry) -> None:
    for module in MODULES:
        module.register(registry)
