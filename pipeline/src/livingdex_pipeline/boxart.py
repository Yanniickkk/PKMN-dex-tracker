"""Box art for a game, from the Bulbagarden Archives.

The picker in the app shows a game by its cover, so the cover has to be shipped like the
sprites are. The source is the Archives because that is where Bulbapedia's own game pages take
their images from, and because their ``robots.txt`` allows both the file description page and
the media itself while disallowing the API: the page is read for the image's address rather
than guessed at, and nothing here touches ``/w/``.

A game names its file - ``Emerald EN boxart.jpg`` - and that name lives with the game, in
:mod:`gamedefs`. Names do not follow one pattern across the series (some are ``.png``, some
``.jpg``), so guessing one would break on the first game that spells it differently.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from urllib.parse import quote, urlsplit

from selectolax.parser import HTMLParser

from .http import PoliteClient

log = logging.getLogger(__name__)

ARCHIVES = "https://archives.bulbagarden.net"

#: Their robots.txt asks for five seconds between requests. It is not negotiable from here.
ARCHIVES_MIN_INTERVAL = 5.0


class BoxArtError(Exception):
    """The cover could not be found or read. The message is meant for a human."""


@dataclass(frozen=True)
class BoxArt:
    """One downloaded cover."""

    #: What to save it as, extension included, for example ``platinum.jpg``.
    file_name: str
    body: bytes
    #: The page it was found through, for the citation.
    page_url: str


def fetch_box_art(
    client: PoliteClient,
    game_id: str,
    file_title: str,
    *,
    refresh: bool = False,
) -> BoxArt:
    """The cover for one game.

    Two requests: the file's description page, then the image it points at. The page is asked
    for the address rather than the address being built from the file name, because the path
    carries a hash of the name that is the wiki's business and not ours.
    """
    page_url = f"{ARCHIVES}/wiki/File:{quote(file_title.replace(' ', '_'))}"
    page = HTMLParser(client.get_text(page_url, refresh=refresh))

    address = _image_address(page)
    if address is None:
        raise BoxArtError(f"{page_url} does not show an image; is {file_title} still its name?")

    body = client.fetch(address, refresh=refresh).body
    extension = _extension(address)

    return BoxArt(file_name=f"{game_id}{extension}", body=body, page_url=page_url)


def _image_address(page: HTMLParser) -> str | None:
    """Where the image actually is.

    The preview the page shows is preferred over the original: a cover is drawn at 92 pixels
    in the app, and shipping a 1500 pixel scan of it would put megabytes into the exe for
    nothing.
    """
    preview = page.css_first("#file img")
    if preview is not None and preview.attributes.get("src"):
        return _absolute(preview.attributes["src"])

    full = page.css_first(".fullImageLink a")
    if full is not None and full.attributes.get("href"):
        return _absolute(full.attributes["href"])

    return None


def _absolute(address: str) -> str:
    if address.startswith("//"):
        return f"https:{address}"

    return address if address.startswith("http") else f"{ARCHIVES}{address}"


def _extension(address: str) -> str:
    """The image's own extension, lower case. The app serves whatever it is handed."""
    path = urlsplit(address).path
    _, _, tail = path.rpartition(".")
    return f".{tail.lower()}" if tail and len(tail) <= 4 else ".png"
