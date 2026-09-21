"""Writing the dataset to disk, in the shape the app reads.

Two things matter here beyond getting the JSON right. The dataset is committed, so a rebuild
has to produce a readable diff: two-space indent, LF, sorted where order is not meaningful.
And ``--game`` has to be able to rewrite one game file without disturbing the rest, which is
why the shared tables and the per-game files are written separately.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
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
        path = self.icon_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        return path

    def write_box_art(self, name: str, body: bytes) -> Path:
        path = self.box_art_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        return path

    def write_sprite(self, name: str, body: bytes) -> Path:
        path = self.sprite_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        return path


def stamp_for(version: str, built_on: date | None = None) -> DatasetStamp:
    """What the app shows when someone asks which data they are looking at."""
    return DatasetStamp(version=version, built_on=built_on or date.today())


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
