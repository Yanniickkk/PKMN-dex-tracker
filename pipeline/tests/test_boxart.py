"""Finding and downloading a game's cover, without touching the network."""

from __future__ import annotations

import re
from pathlib import Path

import httpx
import pytest

from livingdex_pipeline.boxart import BoxArtError, fetch_box_art
from livingdex_pipeline.http import PoliteClient

FILE_PAGE = """
<html><body>
  <div class="fullImageLink" id="file">
    <a href="/media/upload/6/65/Emerald_EN_boxart.jpg">
      <img src="/media/upload/thumb/6/65/Emerald_EN_boxart.jpg/599px-Emerald_EN_boxart.jpg?2010" />
    </a>
  </div>
</body></html>
"""

ROBOTS = "User-agent: *\nAllow: /wiki/\nDisallow: /w/\nCrawl-delay: 5\n"


def client_for(tmp_path: Path, handler) -> PoliteClient:
    return PoliteClient(
        tmp_path / "cache",
        min_interval_seconds=0.0,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=lambda _: None,
    )


def responder(pages: dict[str, tuple[int, bytes, str]]):
    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text=ROBOTS)

        if str(request.url) in pages:
            status, body, content_type = pages[str(request.url)]
            return httpx.Response(status, content=body, headers={"content-type": content_type})

        return httpx.Response(404, text="not found")

    return handle


def test_the_cover_is_taken_from_the_address_the_page_gives(tmp_path: Path) -> None:
    page = "https://archives.bulbagarden.net/wiki/File:Emerald_EN_boxart.jpg"
    image = (
        "https://archives.bulbagarden.net/media/upload/thumb/6/65/"
        "Emerald_EN_boxart.jpg/599px-Emerald_EN_boxart.jpg?2010"
    )

    client = client_for(
        tmp_path,
        responder(
            {
                page: (200, FILE_PAGE.encode(), "text/html"),
                image: (200, b"jpeg-bytes", "image/jpeg"),
            }
        ),
    )

    art = fetch_box_art(client, "emerald", "Emerald EN boxart.jpg")

    assert art.body == b"jpeg-bytes"
    # The game's id names the file, and the image keeps its own kind.
    assert art.file_name == "emerald.jpg"
    assert art.page_url == page


def test_a_file_that_is_not_there_says_so_rather_than_writing_a_broken_image(
    tmp_path: Path,
) -> None:
    page = "https://archives.bulbagarden.net/wiki/File:Nothing_here.png"
    empty = "<html><body>No file by this name exists.</body></html>"

    client = client_for(tmp_path, responder({page: (200, empty.encode(), "text/html")}))

    with pytest.raises(BoxArtError, match=re.escape("Nothing here.png")):
        fetch_box_art(client, "platinum", "Nothing here.png")


def test_a_declared_crawl_delay_is_honoured_when_it_is_the_slower_of_the_two(
    tmp_path: Path,
) -> None:
    slept: list[float] = []
    pages = {
        "https://archives.bulbagarden.net/wiki/A": (200, b"a", "text/html"),
        "https://archives.bulbagarden.net/wiki/B": (200, b"b", "text/html"),
    }
    client = PoliteClient(
        tmp_path / "cache",
        min_interval_seconds=0.0,
        client=httpx.Client(transport=httpx.MockTransport(responder(pages))),
        sleep=slept.append,
    )

    # Two requests to one host: the second waits out the site's own five seconds.
    client.fetch("https://archives.bulbagarden.net/wiki/A", refresh=True)
    client.fetch("https://archives.bulbagarden.net/wiki/B", refresh=True)

    assert slept, "the second request did not wait at all"
    assert max(slept) > 4.0
