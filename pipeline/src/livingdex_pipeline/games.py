"""Where per-game builders plug in.

Phase 2 adds one entry here per game, which is the whole point of the phase: a game is an
entry in this registry plus the scraping behind it, and adding Emerald never means touching
Platinum. Until then the registry is empty and ``build --game`` says so plainly rather than
writing an empty file that looks like a finished game.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .models import GameData


@dataclass(frozen=True)
class BuildContext:
    """What a game builder is handed."""

    game_id: str
    refresh: bool


GameBuilder = Callable[[BuildContext], GameData]


class GameRegistry:
    def __init__(self) -> None:
        self._builders: dict[str, GameBuilder] = {}

    def register(self, game_id: str, builder: GameBuilder) -> None:
        if game_id in self._builders:
            raise ValueError(f"{game_id} is already registered")

        self._builders[game_id] = builder

    def __contains__(self, game_id: object) -> bool:
        return game_id in self._builders

    @property
    def game_ids(self) -> list[str]:
        return sorted(self._builders)

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
