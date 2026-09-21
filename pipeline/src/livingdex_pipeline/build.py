"""The build itself: fetch, normalise, merge, validate, write.

Split from the CLI so a build can be run and tested without going through argument parsing.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import httpx

from .boxart import ARCHIVES_MIN_INTERVAL, BoxArtError, fetch_box_art
from .emit import DatasetWriter, read_dataset, stamp_for
from .games import BuildContext, GameRegistry, UnknownGameError
from .http import PoliteClient, RobotsDisallowed
from .icons import fetch_icons
from .merge import MergeResult
from .models import EvolutionRule, Form, Species, TransferEdge
from .pokeapi import PokeApiClient
from .validate import ValidationReport, validate

log = logging.getLogger(__name__)

#: PokeAPI is a public API built to be used, but it still asks callers to cache and be
#: reasonable. Five a second with everything cached on disk is well inside that.
POKEAPI_MIN_INTERVAL = 0.2

CONFLICT_LOG = "conflicts.json"
VALIDATION_REPORT = "validation.json"


def default_registry() -> GameRegistry:
    """Every game the pipeline knows how to build."""
    from .gamedefs import register_all

    registry = GameRegistry()
    register_all(registry)
    return registry


@dataclass
class BuildResult:
    dataset_root: Path
    written: list[Path] = field(default_factory=list)
    validation: ValidationReport | None = None
    merge: MergeResult | None = None
    #: Edges a game declared whose other end is not in the dataset yet, as (declared by, edge).
    held_back_edges: list[tuple[str, TransferEdge]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.validation is None or self.validation.ok

    def summary(self) -> str:
        lines = [f"wrote {len(self.written)} file(s) to {self.dataset_root}"]

        if self.held_back_edges:
            # Named rather than counted: a game id that will never exist because it is misspelt
            # reads exactly like one that has not been written yet, and the names are what tell
            # the two apart.
            waiting = ", ".join(f"{edge.from_} -> {edge.to}" for _, edge in self.held_back_edges)
            lines.append(
                f"{len(self.held_back_edges)} edge(s) waiting for a game that is not in the "
                f"dataset yet: {waiting}"
            )

        if self.merge is not None and self.merge.conflicts:
            lines.append(f"{len(self.merge.conflicts)} source conflict(s); see {CONFLICT_LOG}")

        if self.validation is not None:
            lines.append(self.validation.summary())

        return "\n".join(lines)


@dataclass
class Build:
    """One run of the pipeline."""

    dataset_root: Path
    cache_root: Path
    version: str = "0.1.0"
    built_on: date | None = None
    species_limit: int | None = None
    refresh: bool = False
    sprites: bool = True
    box_art: bool = True
    icons: bool = True
    registry: GameRegistry = field(default_factory=default_registry)

    def run(self, game_id: str | None = None) -> BuildResult:
        """Build everything, or one game.

        A single-game build rewrites that game's file and the index, and reads the shared
        tables rather than rebuilding them — which is what makes adding Emerald cost nothing
        for Platinum.
        """
        writer = DatasetWriter(self.dataset_root)
        result = BuildResult(dataset_root=self.dataset_root)

        # One client for the whole run rather than one per step: it rate limits per host and
        # keys its cache by full URL, and the game builders need it as much as the shared
        # tables do.
        client = PoliteClient(self.cache_root / "http", min_interval_seconds=POKEAPI_MIN_INTERVAL)
        api = PokeApiClient(client)

        try:
            return self._run(game_id, writer, result, client, api)
        finally:
            client.close()

    def _run(
        self,
        game_id: str | None,
        writer: DatasetWriter,
        result: BuildResult,
        client: PoliteClient,
        api: PokeApiClient,
    ) -> BuildResult:
        if game_id is None:
            result.written.extend(self._build_shared(writer, client, api))
        elif not (self.dataset_root / "species.json").exists():
            raise BuildError(
                f"cannot build {game_id} on its own: the shared tables are missing. "
                "Run a full build first."
            )

        # A full build builds every registered game. Writing the transfer graph without them
        # would leave edges pointing at games that are not in the dataset, which the validator
        # rightly refuses.
        wanted = self.registry.game_ids if game_id is None else [game_id]

        for wanted_id in wanted:
            try:
                data = self.registry.build(
                    BuildContext(game_id=wanted_id, refresh=self.refresh, api=api)
                )
            except UnknownGameError as error:
                raise BuildError(str(error)) from error

            result.written.append(writer.write_game(data))

        if self.box_art:
            result.written.extend(self._fetch_box_art(wanted, writer))

        built_games = writer.known_games()

        stamp = stamp_for(self.version, self.built_on)
        result.written.append(writer.write_index(stamp, built_games))

        result.held_back_edges = self.registry.held_back_edges
        result.validation = self._validate()
        result.validation.write(self.dataset_root / VALIDATION_REPORT)
        result.written.append(self.dataset_root / VALIDATION_REPORT)

        return result

    def _build_shared(
        self,
        writer: DatasetWriter,
        client: PoliteClient,
        api: PokeApiClient,
    ) -> list[Path]:
        """The tables every game shares: species, forms, evolution rules, the transfer graph."""
        species = self._fetch_species(api)
        sprite_paths = self._fetch_sprites(api, client, species, writer) if self.sprites else []
        icon_paths = self._fetch_icons(client, writer) if self.icons else []

        # Forms and evolution rules are still Phase 2 work; the files are written empty so the
        # dataset is always a complete set rather than a partial one. The transfer graph is
        # whatever the registered games brought with them.
        forms: list[Form] = []
        rules: list[EvolutionRule] = []
        edges: list[TransferEdge] = self.registry.edges

        for game_id, held in self.registry.held_back_edges:
            log.info(
                "%s declares %s -> %s, which is not in the dataset yet; the edge is held back",
                game_id,
                held.from_,
                held.to,
            )

        return [
            *icon_paths,
            *sprite_paths,
            writer.write_species(species),
            writer.write_forms(forms),
            writer.write_evolution_rules(rules),
            writer.write_transfers(edges),
        ]

    def _fetch_species(self, api: PokeApiClient) -> list[Species]:
        listing = api.species_list(refresh=self.refresh)
        if self.species_limit is not None:
            listing = listing[: self.species_limit]

        species: list[Species] = []
        for index, entry in enumerate(listing, start=1):
            log.info("species %s/%s: %s", index, len(listing), entry["name"])
            species.append(api.species(entry["name"], refresh=self.refresh))

        return species

    def _fetch_sprites(
        self,
        api: PokeApiClient,
        client: PoliteClient,
        species: list[Species],
        writer: DatasetWriter,
    ) -> list[Path]:
        """One battle sprite per species, so the app never touches the network."""
        written: list[Path] = []

        for one in species:
            url = api.sprite_url(one.national_dex_number)
            try:
                body = client.fetch(url, refresh=self.refresh).body
            except (httpx.HTTPError, RobotsDisallowed) as error:
                # A missing sprite is a hole in the grid, not a reason to throw away a build.
                log.warning("no sprite for %s: %s", one.id, error)
                continue

            written.append(writer.write_sprite(f"{one.id}.png", body))

        return written

    def _fetch_icons(self, client: PoliteClient, writer: DatasetWriter) -> list[Path]:
        """One icon per way of getting a Pokemon. Shared by every game, so built with the tables."""
        return [
            writer.write_icon(icon.file_name, icon.body)
            for icon in fetch_icons(client, refresh=self.refresh)
        ]

    def _fetch_box_art(self, game_ids: list[str], writer: DatasetWriter) -> list[Path]:
        """One cover per game, so the picker can show a game by its box rather than its name."""
        wanted = [
            (game_id, title)
            for game_id in game_ids
            if (title := self.registry.box_art_of(game_id)) is not None
        ]

        if not wanted:
            return []

        written: list[Path] = []

        # Its own client: the Archives ask for five seconds between requests in their
        # robots.txt, and that is not a pace to hold the PokeAPI fetches to.
        with PoliteClient(
            self.cache_root / "http",
            min_interval_seconds=ARCHIVES_MIN_INTERVAL,
        ) as client:
            for game_id, title in wanted:
                try:
                    art = fetch_box_art(client, game_id, title, refresh=self.refresh)
                except (BoxArtError, httpx.HTTPError, OSError) as error:
                    # A missing cover falls back to a drawn one in the app, which is a worse
                    # picker but not a broken build.
                    log.warning("no box art for %s: %s", game_id, error)
                    continue

                written.append(writer.write_box_art(art.file_name, art.body))

        return written

    def _validate(self) -> ValidationReport:
        # Read back from disk rather than validating the objects still in memory: that way a
        # serialisation bug fails the run that caused it.
        return validate(read_dataset(self.dataset_root))


class BuildError(Exception):
    """A build could not start or could not finish. The message is meant for a human."""
