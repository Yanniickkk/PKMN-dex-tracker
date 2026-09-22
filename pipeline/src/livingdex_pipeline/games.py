"""Where per-game builders plug in.

Phase 2 adds one entry here per game, which is the whole point of the phase: a game is an
entry in this registry plus the scraping behind it, and adding Emerald never means touching
Platinum. The games themselves live in :mod:`gamedefs`. A game nothing has registered makes
``build --game`` say so plainly rather than write an empty file that looks finished.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .models import DexEntry, GameData, Species, TransferDirection, TransferEdge
from .pokeapi import PokeApiClient


@dataclass(frozen=True)
class BuildContext:
    """What a game builder is handed.

    The API client is here because step 2 of a game is a dex list and that is PokeAPI's to
    answer. Sources a game scrapes for its encounters bring their own client, because they are
    the ones that have to keep to another site's pace.

    The species table is here because a game has to ask about more species than its own Pokedex
    lists - see :meth:`living_dex`.
    """

    game_id: str
    refresh: bool
    api: PokeApiClient | None = None
    #: Every species the dataset knows, in National Dex order. The shared tables are built
    #: before any game is, so this is always filled in by the time a builder runs.
    species: Sequence[Species] = ()

    def require_api(self) -> PokeApiClient:
        """The API client, or a clear failure rather than an AttributeError three frames down."""
        if self.api is None:
            raise RuntimeError(
                f"building {self.game_id} needs the PokeAPI client, and the build did not pass one"
            )

        return self.api

    def living_dex(
        self,
        *,
        through: int | None,
        entries: Sequence[DexEntry] = (),
    ) -> list[str]:
        """Every species this game asks a player to fill, in National Dex order.

        Not the game's own Pokedex, and that distinction is the whole reason this exists. A
        living dex in Diamond is 493 entries; the Sinnoh dex is 151 of them. Asking only about
        the regional list is what left Bebe's Eevee, the Rotom in the Old Chateau and a hundred
        and sixty-seven others with nothing recorded against them - not marked unobtainable,
        not marked missing, simply never asked about, in a game that hands them over.

        ``through`` is how far the game's National Dex reaches. A game without one - none yet -
        asks a player for its own dex and nothing else, so ``entries`` answers instead.
        """
        if through is None:
            return [entry.target.species for entry in entries]

        if not self.species:
            raise RuntimeError(
                f"building {self.game_id} needs the species table to know what its living dex "
                "asks for, and the build did not pass one"
            )

        return [
            one.id
            for one in sorted(self.species, key=lambda one: one.national_dex_number)
            if one.national_dex_number <= through
        ]


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
        """The edges both of whose ends are registered, deduplicated and in a fixed order.

        A game declares the whole truth about itself, including routes to games that are not in
        the dataset yet: Emerald trades with Ruby whether or not Ruby has been written. Those
        edges are held back until the other end exists, so the dataset never contains a route
        the app cannot explain, and adding Ruby later lights the route up without anyone going
        back to edit Emerald.

        Both ends may declare the same edge, from either side. They collapse into one, so
        neither game has to know whether the other got there first.
        """
        known = set(self._builders)
        seen: dict[tuple, TransferEdge] = {}

        for game_id in sorted(self._edges):
            for edge in self._edges[game_id]:
                if edge.from_ not in known or edge.to not in known:
                    continue

                seen.setdefault(self._edge_key(edge), edge)

        return sorted(seen.values(), key=lambda one: (one.from_, one.to, one.mechanism.value))

    @property
    def held_back_edges(self) -> list[tuple[str, TransferEdge]]:
        """Declared edges waiting for their other end, with the game that declared them.

        Reported rather than dropped in silence: a typo in a game id looks exactly like a game
        that has not been written yet, and only one of those is worth a build saying nothing
        about.
        """
        known = set(self._builders)

        return [
            (game_id, edge)
            for game_id in sorted(self._edges)
            for edge in self._edges[game_id]
            if edge.from_ not in known or edge.to not in known
        ]

    @staticmethod
    def _edge_key(edge: TransferEdge) -> tuple:
        """What makes two declarations the same route.

        A both-ways route is one route however many of its ends declare it, and which end wrote
        it down is not part of what it is: Ruby names Emerald as a trading partner and Emerald
        names Ruby, and the graph should hold that once. A one-way route is not the same route
        backwards - Pal Park carries Emerald into Platinum and never the other way - so its ends
        keep their order.
        """
        ends = (edge.from_, edge.to)
        if edge.direction is TransferDirection.BOTH_WAYS:
            ends = tuple(sorted(ends))

        return (*ends, edge.mechanism.value, edge.direction.value)

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
