"""Command line entry point for the dataset pipeline.

Phase 0.6 fills in the real steps. For now this only proves the package is
installed and the dataset output directory is where everything agrees it is.
"""

from __future__ import annotations

import argparse
from pathlib import Path

# src/livingdex_pipeline/cli.py -> src/livingdex_pipeline -> src -> pipeline -> repo root.
# Only correct for an editable install from a source checkout, which is how the
# pipeline is meant to be run. --out overrides it.
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET_DIR = REPO_ROOT / "dataset"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="livingdex-pipeline")
    subcommands = parser.add_subparsers(dest="command", required=True)

    build = subcommands.add_parser("build", help="build the dataset")
    build.add_argument(
        "--game",
        help="rebuild a single game by id, leaving the rest of the dataset untouched",
    )
    build.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_DATASET_DIR,
        help="dataset output directory (default: the repo's dataset/)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "build":
        target = args.game or "all games"
        print(f"build: {target} -> {args.out}")
        print("Not implemented yet. See Phase 0.6 in 'TODO dex tracker.md'.")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
