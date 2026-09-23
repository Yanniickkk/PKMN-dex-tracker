"""The build itself: fetch, normalise, merge, validate, write.

Split from the CLI so a build can be run and tested without going through argument parsing.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import httpx

from .boxart import ARCHIVES_MIN_INTERVAL, BoxArtError, fetch_box_art
from .emit import DatasetWriter, read_dataset, read_forms, read_species, stamp_for
from .evolutions import evolution_rules
from .forms import form_pictures, form_table
from .games import BuildContext, GameRegistry, UnknownGameError
from .grottoes import MIN_INTERVAL as GROTTO_MIN_INTERVAL
from .http import PoliteClient, RobotsDisallowed
from .icons import fetch_icons
from .merge import MergeResult
from .models import EvolutionRule, Form, GameData, Species, TransferEdge
from .pokeapi import PokeApiClient
from .validate import ValidationReport, validate

log = logging.getLogger(__name__)

#: PokeAPI is a public API built to be used, but it still asks callers to cache and be
#: reasonable. Five a second with everything cached on disk is well inside that.
POKEAPI_MIN_INTERVAL = 0.2

#: Where the sprite repository keeps a Pokemon's pictures. The species sprites are asked for
#: through :meth:`PokeApiClient.sprite_url`; a form's file name is not a National Dex number, so
#: its address is built here.
SPRITES = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon"

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
    #: Filled by the shared step, or read back off disk when that step does not run.
    _forms: list[Form] = field(default_factory=list, repr=False)
    _form_pictures: Mapping[str, tuple[str, ...]] = field(default_factory=dict, repr=False)

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

        # Read back rather than kept from _build_shared: a single-game build never runs that
        # step, and both paths need the same table. A game asks about every species its living
        # dex reaches, which is most of this list rather than the handful its own Pokedex lists.
        species = read_species(self.dataset_root)
        # Same reason as the species table: a single-game build never ran the shared step, and
        # a game has to know which forms are its own to say how they are come by.
        forms = self._forms or read_forms(self.dataset_root)
        self._forms = forms

        built: list[GameData] = []

        # A second client for the games that read a wiki page. Its own, because Bulbapedia is
        # not a site to visit at the pace PokeAPI is fetched at, and the floor belongs to the
        # slower host rather than to whichever step happens to be running.
        with PoliteClient(
            self.cache_root / "http",
            min_interval_seconds=GROTTO_MIN_INTERVAL,
        ) as wiki:
            for wanted_id in wanted:
                try:
                    data = self.registry.build(
                        BuildContext(
                            game_id=wanted_id,
                            refresh=self.refresh,
                            api=api,
                            wiki=wiki,
                            species=species,
                            forms=forms,
                        )
                    )
                except UnknownGameError as error:
                    raise BuildError(str(error)) from error

                built.append(data)
                result.written.append(writer.write_game(data))

        if self.sprites:
            result.written.extend(self._fetch_game_sprites(api, client, built, writer))

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

        # The transfer graph is whatever the registered games brought with them, and the form
        # table is read for every species the dataset holds - both are about the whole set
        # rather than about any one game, which is why they are built here.
        table = form_table(
            api,
            species=species,
            game_ids=self.registry.game_ids,
            refresh=self.refresh,
        )
        forms: list[Form] = table.forms
        # Kept for the sprite step, which runs after every game is built and needs to know
        # which file each form's picture would be in.
        self._forms = forms
        self._form_pictures = table.pictures
        rules: list[EvolutionRule] = self._fetch_evolution_rules(api, species)
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

    def _fetch_evolution_rules(
        self,
        api: PokeApiClient,
        species: list[Species],
    ) -> list[EvolutionRule]:
        """Every rule in the chains the species table reaches.

        Chains rather than species: everything in one chain shares it, so the 1025 species of a
        full build are a few hundred fetches. A ``--limit`` build asks for fewer species and so
        for fewer chains, which is what keeps a smoke build quick.
        """
        chains = sorted({one.evolution_chain for one in species})
        log.info("evolution rules from %s chain(s)", len(chains))

        return evolution_rules(api, chains=chains, refresh=self.refresh)

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

    def _fetch_game_sprites(
        self,
        api: PokeApiClient,
        client: PoliteClient,
        built: list[GameData],
        writer: DatasetWriter,
    ) -> list[Path]:
        """The battle sprites of each game that has a set of its own.

        A set is fetched once however many games share it: Ruby and Sapphire were drawn from the
        same sheet, and writing their sprites twice would double a directory for nothing. Which
        games share it still matters for the forms, though - all four Generation 5 games are
        drawn from one sheet and only two of them have a Therian Landorus in it.

        How far a set reaches is the game's own reach. Emerald's National Dex stops at 386 and so
        does its sprite sheet; a game with no National Dex is asked only for what its own dex
        lists. A species the set has no picture of is logged and left out, and the app falls back
        to the shared set for it - which is the "documented fallback" the checklist asks for.
        """
        species = read_species(self.dataset_root)
        if not species:
            return []

        if not self._forms:
            # A single-game build never ran the shared step, so the table is read back off disk.
            # Where each picture lives is worked out later and only for the forms a sheet is
            # actually being fetched for.
            self._forms = read_forms(self.dataset_root)

        written: list[Path] = []
        done: set[str] = set()

        for data in built:
            sprite_set = data.game.sprite_set
            if sprite_set is None or sprite_set in done:
                continue

            done.add(sprite_set)
            sharing = [one for one in built if one.game.sprite_set == sprite_set]
            written.extend(
                self._fetch_sprite_set(api, client, sprite_set, data, sharing, species, writer)
            )

        return written

    def _fetch_sprite_set(
        self,
        api: PokeApiClient,
        client: PoliteClient,
        sprite_set: str,
        data: GameData,
        sharing: list[GameData],
        species: list[Species],
        writer: DatasetWriter,
    ) -> list[Path]:
        wanted = self._species_of(data, species)
        log.info("%s sprites: %s species from %s", data.game.id, len(wanted), sprite_set)

        written: list[Path] = []
        missing = 0

        for one in wanted:
            url = api.sprite_url(one.national_dex_number, sprite_set)
            try:
                body = client.fetch(url, refresh=self.refresh).body
            except (httpx.HTTPError, RobotsDisallowed) as error:
                # Expected rather than exceptional: a set only covers what its generation drew.
                log.debug("%s has no sprite in %s: %s", one.id, sprite_set, error)
                missing += 1
                continue

            written.append(writer.write_sprite(f"{sprite_set}/{one.id}.png", body))

        if missing:
            log.info(
                "%s of them are not in %s; those fall back to the shared set", missing, sprite_set
            )

        return written + self._fetch_form_sprites(api, client, sprite_set, sharing, writer)

    def _fetch_form_sprites(
        self,
        api: PokeApiClient,
        client: PoliteClient,
        sprite_set: str,
        sharing: list[GameData],
        writer: DatasetWriter,
    ) -> list[Path]:
        """The pictures of this game's forms, where the sheet has one.

        Most sheets have few: the Generation 5 sheet draws Deerling's four seasons and Unown's
        letters and has nothing for Wash Rotom, which the games themselves did draw. A form
        with no picture here falls back to its species' one in the app, which is the same
        fallback a species with no picture in its set already uses.
        """
        games = {one.game.id for one in sharing}
        forms = [one for one in self._forms if games & set(one.games)]
        if not forms:
            return []

        # Asked for here rather than when the table was built, and only about these: a build
        # that fetches no sprites should ask the source nothing, and a single-game build should
        # ask about one game's forms instead of every species in the dataset.
        pictures = self._form_pictures or form_pictures(api, forms, refresh=self.refresh)
        written: list[Path] = []

        for form in (one.id for one in forms if one.id in pictures):
            body = self._first_picture(client, sprite_set, pictures[form])
            if body is not None:
                written.append(writer.write_sprite(f"{sprite_set}/{form}.png", body))

        log.info("form sprites: %s of %s in %s", len(written), len(forms), sprite_set)

        return written

    def _first_picture(
        self,
        client: PoliteClient,
        sprite_set: str,
        candidates: tuple[str, ...],
    ) -> bytes | None:
        for name in candidates:
            url = f"{SPRITES}/versions/{sprite_set}/{name}"
            try:
                return client.fetch(url, refresh=self.refresh).body
            except (httpx.HTTPError, RobotsDisallowed):
                continue

        return None

    @staticmethod
    def _species_of(data: GameData, species: list[Species]) -> list[Species]:
        """Every species this game's grid can draw."""
        reach = data.game.national_dex_through
        if reach is not None:
            return [one for one in species if one.national_dex_number <= reach]

        # No National Dex, so the grid is the game's own dex and nothing else.
        listed = {entry.target.species for entry in data.dex_entries}
        return [one for one in species if one.id in listed]

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
