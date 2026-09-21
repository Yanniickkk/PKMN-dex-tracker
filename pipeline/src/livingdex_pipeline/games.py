"""Where per-game builders plug in.

Phase 2 adds one entry here per game, which is the whole point of the phase: a game is an
entry in this registry plus the scraping behind it, and adding Emerald never means touching
Platinum. The games themselves live in :mod:`gamedefs`. A game nothing has registered makes
``build --game`` say so plainly rather than write an empty file that looks finished.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .models import GameData, TransferEdge


@dataclass(frozen=True)
class BuildContext:
    """What a game builder is handed."""

    game_id: str
    refresh: bool


GameBuilder = Callable[[BuildContext], GameData]


class GameRegistry:
    def __init__(self) -> None:
        self._builders: dict[str, GameBuilder] = {}
        self._edges: dict[str, list[TransferEdge]] = {}
        self._box_art: dict[str, str] = {}

    def register(
        self,
        game_id: str,
        builder: GameBuilder,
        edges: Sequence[TransferEdge] = (),
        box_art: str | None = None,
    ) -> None:
        """A game and the transfer edges it brings with it.

        Edges arrive with a game because that is how Phase 2 step 1 is written, but they are
        written to the shared transfer file rather than the game file: a route is about two
        games, so it cannot belong to one of them.
        """
        if game_id in self._builders:
            raise ValueError(f"{game_id} is already registered")

        self._builders[game_id] = builder
        self._edges[game_id] = list(edges)

        # The name of the cover's file on the Archives, spelled by the game that wants it.
        # There is no pattern across the series to derive it from.
        if box_art is not None:
            self._box_art[game_id] = box_art

    def __contains__(self, game_id: object) -> bool:
        return game_id in self._builders

    @property
    def game_ids(self) -> list[str]:
        return sorted(self._builders)

    def box_art_of(self, game_id: str) -> str | None:
        """Which file on the Archives holds this game's cover, if it named one."""
        return self._box_art.get(game_id)

    @property
    def edges(self) -> list[TransferEdge]:
        """Every registered edge, in a fixed order so the file is diffable."""
        return [edge for game_id in sorted(self._edges) for edge in self._edges[game_id]]

    def build(self, context: BuildContext) -> GameData:
        builder = self._builders.get(context.game_id)
        if builder is None:
            raise UnknownGameError(context.game_id, self.game_ids)

        return builder(context)


class UnknownGameError(Exception):
    """Asked to build a game nothing knows how to build."""

    def __init__(self, game_id: str, known: list[str]) -> None:
        known_text = ", ".join(known) if known else "none yet"
        super().__init__(f"no builder registered for {game_id} (registered: {known_text})")
        self.game_id = game_id
        self.known = known


#: The registry a build uses. Phase 2 calls ``register`` on it.
REGISTRY = GameRegistry()
