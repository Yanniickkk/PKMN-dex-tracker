"""Every game the pipeline knows how to build.

Phase 2 adds one module here per game and one line to :func:`register_all`. Registration is
explicit rather than a side effect of importing, so the set of games a build covers is readable
in one place.
"""

from __future__ import annotations

from ..games import GameRegistry
from . import diamond, emerald, firered, leafgreen, pearl, platinum, ruby, sapphire

# In the order they came out: the Hoenn pair, the Kanto pair, the third version that followed
# them, then the Sinnoh pair and its own third version.
MODULES = [ruby, sapphire, firered, leafgreen, emerald, diamond, pearl, platinum]


def register_all(registry: GameRegistry) -> None:
    for module in MODULES:
        module.register(registry)
