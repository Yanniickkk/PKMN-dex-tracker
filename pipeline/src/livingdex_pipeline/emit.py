"""Writing the dataset to disk, in the shape the app reads.

Two things matter here beyond getting the JSON right. The dataset is committed, so a rebuild
has to produce a readable diff: two-space indent, LF, sorted where order is not meaningful.
And ``--game`` has to be able to rewrite one game file without disturbing the rest, which is
why the shared tables and the per-game files are written separately.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # circular at runtime: validate imports the models, not the writer.
    from .validate import Dataset

from .models import (
    DatasetIndex,
    DatasetStamp,
    EvolutionRule,
    Form,
    GameData,
    Model,
    Species,
    TransferEdge,
)

INDEX_FILE = "index.json"
SPECIES_FILE = "species.json"
FORMS_FILE = "forms.json"
EVOLUTION_RULES_FILE = "evolution-rules.json"
TRANSFERS_FILE = "transfers.json"
GAMES_DIRECTORY = "games"
SPRITES_DIRECTORY = "sprites"
BOXART_DIRECTORY = "boxart"
ICONS_DIRECTORY = "icons"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def _dump(models: Sequence[Model]) -> list[object]:
    return [json.loads(model.model_dump_json(by_alias=True, exclude_none=True)) for model in models]


@dataclass(frozen=True)
class DatasetWriter:
    """Writes into one dataset directory."""

    root: Path
    #: How many pictures were already exactly right and so were not written again.
    #:
    #: A counter rather than nothing at all, because "wrote 8303 files" when 8211 of them were
    #: untouched is a summary that describes the intent instead of the act.
    unchanged: list[Path] = field(default_factory=list, compare=False, repr=False)
    #: Pictures that were already in the dataset, so the source was never asked about them.
    #:
    #: A different fact from :attr:`unchanged`, and the difference is the whole point of it:
    #: unchanged means the bytes came back and matched, kept means nothing was fetched at all.
    kept: list[Path] = field(default_factory=list, compare=False, repr=False)

    def game_file(self, game_id: str) -> Path:
        return self.root / GAMES_DIRECTORY / f"{game_id}.json"

    def write_index(self, stamp: DatasetStamp, games: Sequence[str]) -> Path:
        index = DatasetIndex(stamp=stamp, games=sorted(games))
        path = self.root / INDEX_FILE
        _write_json(path, json.loads(index.model_dump_json(by_alias=True, exclude_none=True)))
        return path

    def write_species(self, species: Sequence[Species]) -> Path:
        path = self.root / SPECIES_FILE
        _write_json(path, _dump(sorted(species, key=lambda one: one.national_dex_number)))
        return path

    def write_forms(self, forms: Sequence[Form]) -> Path:
        path = self.root / FORMS_FILE
        _write_json(path, _dump(sorted(forms, key=lambda one: one.id)))
        return path

    def write_evolution_rules(self, rules: Sequence[EvolutionRule]) -> Path:
        path = self.root / EVOLUTION_RULES_FILE
        _write_json(path, _dump(sorted(rules, key=lambda one: one.id)))
        return path

    def write_transfers(self, edges: Sequence[TransferEdge]) -> Path:
        path = self.root / TRANSFERS_FILE
        ordered = sorted(edges, key=lambda one: (one.from_, one.to, one.mechanism.value))
        _write_json(path, _dump(ordered))
        return path

    def write_game(self, data: GameData) -> Path:
        """One game file. Touches nothing else, which is what ``--game`` relies on."""
        path = self.game_file(data.game.id)
        _write_json(path, json.loads(data.model_dump_json(by_alias=True, exclude_none=True)))
        return path

    def known_games(self) -> list[str]:
        """The games that already have a file, so a single-game build can keep the index whole."""
        directory = self.root / GAMES_DIRECTORY
        if not directory.exists():
            return []

        return sorted(path.stem for path in directory.glob("*.json"))

    def sprite_path(self, name: str) -> Path:
        return self.root / SPRITES_DIRECTORY / name

    def box_art_path(self, name: str) -> Path:
        return self.root / BOXART_DIRECTORY / name

    def icon_path(self, name: str) -> Path:
        return self.root / ICONS_DIRECTORY / name

    def write_icon(self, name: str, body: bytes) -> Path:
        return self._write_picture(self.icon_path(name), body)

    def write_box_art(self, name: str, body: bytes) -> Path:
        return self._write_picture(self.box_art_path(name), body)

    def write_sprite(self, name: str, body: bytes) -> Path:
        return self._write_picture(self.sprite_path(name), body)

    def _write_picture(self, path: Path, body: bytes) -> Path:
        """One picture into the dataset, written only if it is not already there.

        A full build hands this the same eight thousand pictures it handed it last time, and a
        sprite does not change: the bytes come out of a cache that has no expiry. Writing them
        anyway costs eight thousand file writes and, worse, moves eight thousand timestamps -
        which makes every tool that watches this directory believe the whole dataset is new.
        Comparing first is one read against one write, and the read is the cheaper of the two on
        every machine this has been run on.
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if path.read_bytes() == body:
                self.unchanged.append(path)
                return path
        except OSError:
            pass

        path.write_bytes(body)
        return path

    def kept_sprite(self, name: str) -> Path | None:
        """The picture the dataset already holds, if it holds it.

        ``dataset/sprites`` is committed, which makes it the only cache this project has that
        travels with the repository. The HTTP cache under ``pipeline/.cache`` is gitignored and
        over half a gigabyte, so a fresh clone starts with nothing and would fetch eight
        thousand pictures that are already sitting in its own working tree. Against a host that
        asks five seconds between requests - the Archives, where Generation 7's sprites have to
        come from - that is not a slow build, it is a build nobody will run.

        A sprite does not change, so having the file is the whole answer. What this cannot
        notice is a picture that was wrong when it was written, or a better one appearing
        upstream. Both are what ``--refresh`` is for, and the caller checks that flag before
        asking.
        """
        return self._kept(self.sprite_path(name))

    def kept_box_art(self, game_id: str) -> Path | None:
        """The cover this game already has, whichever extension it was saved under.

        Asked by game rather than by file name because the name is not known until the
        Archives' description page has been read, and reading that page is half of what this
        is here to avoid: two requests a game at five seconds each, thirty times over, for
        covers that are committed.
        """
        directory = self.root / BOXART_DIRECTORY
        if not directory.is_dir():
            return None

        for path in sorted(directory.glob(f"{game_id}.*")):
            return self._kept(path)

        return None

    def _kept(self, path: Path) -> Path | None:
        if not path.is_file():
            return None

        self.kept.append(path)
        return path


def stamp_for(version: str, built_on: date | None = None) -> DatasetStamp:
    """What the app shows when someone asks which data they are looking at."""
    return DatasetStamp(version=version, built_on=built_on or date.today())


def read_species(root: Path) -> list[Species]:
    """The species table as it stands on disk.

    A single-game build does not rebuild the shared tables, and it still has to turn National
    Dex numbers into file names to fetch that game's sprites. Reading the table back is how it
    gets the mapping without re-fetching a thousand species.
    """
    path = root / SPECIES_FILE
    if not path.exists():
        return []

    return [Species.model_validate(one) for one in json.loads(path.read_text(encoding="utf-8"))]


def read_forms(root: Path) -> list[Form]:
    """The form table as it stands on disk, for the same reason :func:`read_species` exists.

    A single-game build has to know which of a game's forms have a picture in its sheet, and
    rebuilding the table to find out would be a thousand requests for a list that is already
    written down.
    """
    path = root / FORMS_FILE
    if not path.exists():
        return []

    return [Form.model_validate(one) for one in json.loads(path.read_text(encoding="utf-8"))]


def read_evolution_rules(root: Path) -> list[EvolutionRule]:
    """The evolution rules as they stand on disk, for the same reason :func:`read_species` does.

    A single-game build never rebuilds the shared tables, and it has to walk this game's own
    evolution records back to what starts them - see :mod:`reach`.
    """
    path = root / EVOLUTION_RULES_FILE
    if not path.exists():
        return []

    return [
        EvolutionRule.model_validate(one)
        for one in json.loads(path.read_text(encoding="utf-8"))
    ]


def read_dataset(root: Path) -> Dataset:
    """Read back what was written.

    The build validates the files on disk rather than the objects in memory, so a serialisation
    bug is caught by the same run that caused it instead of by the app later.
    """
    from .validate import Dataset as ReadDataset

    def load(name: str) -> list[dict]:
        path = root / name
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []

    index_path = root / INDEX_FILE
    index = (
        DatasetIndex.model_validate_json(index_path.read_text(encoding="utf-8"))
        if index_path.exists()
        else DatasetIndex(stamp=DatasetStamp(version="0.0.0", built_on=date.today()), games=[])
    )

    game_paths = [(root / GAMES_DIRECTORY / f"{game_id}.json") for game_id in index.games]
    games = [
        GameData.model_validate_json(path.read_text(encoding="utf-8"))
        for path in game_paths
        if path.exists()
    ]

    sprites = frozenset(path.stem for path in (root / SPRITES_DIRECTORY).glob("*.png"))
    box_art = frozenset(path.stem for path in (root / BOXART_DIRECTORY).glob("*.*"))

    return ReadDataset(
        index=index,
        species=[Species.model_validate(one) for one in load(SPECIES_FILE)],
        forms=[Form.model_validate(one) for one in load(FORMS_FILE)],
        evolution_rules=[EvolutionRule.model_validate(one) for one in load(EVOLUTION_RULES_FILE)],
        transfers=[TransferEdge.model_validate(one) for one in load(TRANSFERS_FILE)],
        games=games,
        sprites=sprites,
        box_art=box_art,
    )
