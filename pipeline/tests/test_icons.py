"""The icons the app shows beside each way of getting a Pokemon."""

from __future__ import annotations

from pathlib import Path

import httpx

from livingdex_pipeline.http import PoliteClient
from livingdex_pipeline.icons import METHOD_ICONS, fetch_icons


def client_for(tmp_path: Path, missing: set[str] | None = None) -> PoliteClient:
    absent = missing or set()

    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)

        name = request.url.path.rsplit("/", 1)[-1].removesuffix(".png")

        return (
            httpx.Response(404)
            if name in absent
            else httpx.Response(200, content=f"png for {name}".encode())
        )

    return PoliteClient(
        tmp_path / "cache",
        min_interval_seconds=0.0,
        client=httpx.Client(transport=httpx.MockTransport(handle)),
        sleep=lambda _: None,
    )


def test_each_icon_is_filed_under_the_method_rather_than_the_item(tmp_path: Path) -> None:
    icons = fetch_icons(client_for(tmp_path))

    by_name = {icon.file_name: icon for icon in icons}

    # The app asks for icons/good-rod.png, not icons/good-rod-the-item.png.
    assert "good-rod.png" in by_name
    assert "surf.png" in by_name
    # Surf's picture is its HM disc, which is what the mapping says.
    assert by_name["surf.png"].body == b"png for hm03"


def test_every_method_the_app_can_show_has_an_icon(tmp_path: Path) -> None:
    icons = fetch_icons(client_for(tmp_path))

    assert {icon.file_name.removesuffix(".png") for icon in icons} == set(METHOD_ICONS)
    # Everything except an in-game trade, which has no item and is drawn by the app.
    assert "trade" not in METHOD_ICONS


def test_an_icon_that_cannot_be_fetched_is_skipped_rather_than_failing_the_build(
    tmp_path: Path,
) -> None:
    # The app falls back to drawing nothing for a missing key, which is worth less than an icon
    # but much less bad than a build that stops.
    icons = fetch_icons(client_for(tmp_path, missing={"honey"}))

    names = {icon.file_name for icon in icons}

    assert "honey-tree.png" not in names
    assert "walk.png" in names
