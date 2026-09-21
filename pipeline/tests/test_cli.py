import pytest

from livingdex_pipeline.cli import build_parser


def test_build_accepts_a_single_game():
    args = build_parser().parse_args(["build", "--game", "platinum"])
    assert args.command == "build"
    assert args.game == "platinum"


def test_build_without_a_game_means_all_games():
    args = build_parser().parse_args(["build"])
    assert args.game is None


def test_a_command_is_required():
    with pytest.raises(SystemExit):
        build_parser().parse_args([])
