"""Command line entry point for the dataset pipeline."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .build import Build, BuildError

# src/livingdex_pipeline/cli.py -> src/livingdex_pipeline -> src -> pipeline -> repo root.
# Only correct for an editable install from a source checkout, which is how the pipeline is
# meant to be run. --out overrides it.
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET_DIR = REPO_ROOT / "dataset"
DEFAULT_CACHE_DIR = REPO_ROOT / "pipeline" / ".cache"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="livingdex-pipeline")
    parser.add_argument("-v", "--verbose", action="store_true", help="log every fetch")
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
    build.add_argument(
        "--cache",
        type=Path,
        default=DEFAULT_CACHE_DIR,
        help="where downloaded pages and API responses are kept",
    )
    build.add_argument(
        "--dataset-version",
        default="0.1.0",
        help="version to stamp the dataset with",
    )
    build.add_argument(
        "--limit",
        type=int,
        help="only fetch this many species; for a quick smoke build",
    )
    build.add_argument(
        "--refresh",
        action="store_true",
        help="ignore the cache and fetch everything again",
    )
    build.add_argument(
        "--no-sprites",
        action="store_true",
        help="skip the sprite download; the grid will have holes but the build is quick",
    )
    build.add_argument(
        "--no-box-art",
        action="store_true",
        help="skip the box art download; the game picker draws plain covers instead",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(message)s",
    )

    if args.command != "build":
        return 1

    build = Build(
        dataset_root=args.out,
        cache_root=args.cache,
        version=args.dataset_version,
        species_limit=args.limit,
        refresh=args.refresh,
        sprites=not args.no_sprites,
        box_art=not args.no_box_art,
    )

    try:
        result = build.run(args.game)
    except BuildError as error:
        print(f"build failed: {error}", file=sys.stderr)
        return 2

    print(result.summary())

    if not result.ok:
        for finding in result.validation.errors if result.validation else []:
            print(finding.describe(), file=sys.stderr)

        return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
