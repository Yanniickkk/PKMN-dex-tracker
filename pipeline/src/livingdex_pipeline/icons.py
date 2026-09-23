"""An icon per way of getting a Pokemon, taken from the games' own item sprites.

Drawing these by hand was tried first and read badly at the size they are shown: a tuft of grass
came out as a letter Y. The games already have a picture for most of these - the three rods are
three different rods, Surf and Rock Smash are their HM discs - and those sit beside the battle
sprites in the grid as if they belong there, because they do.

The mapping is data, not code: an item name per method key, so a game that needs a different
picture later changes one line. Where the games have no item for something - walking through
grass, an in-game trade - it is said so here rather than a stand-in being invented.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from .http import PoliteClient

log = logging.getLogger(__name__)

SPRITES = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items"

#: How a Pokemon was obtained, and the item whose sprite says it best.
#:
#: The keys are this project's own: the acquisition kinds, the encounter methods within wild,
#: and the kinds of gift. The app asks for them by name.
METHOD_ICONS: dict[str, str] = {
    # Wild. Walking has no item of its own, so the ball you throw stands for a plain encounter.
    "walk": "poke-ball",
    "surf": "hm03",
    "old-rod": "old-rod",
    "good-rod": "good-rod",
    "super-rod": "super-rod",
    "rock-smash": "hm06",
    # Headbutt is a TM in Generation 2 and a tutor move afterwards; neither has a sprite here.
    "headbutt": "poke-ball",
    "honey-tree": "honey",
    "swarm": "poke-radar",
    # Generation 5's own. Only the dust cloud has an item that looks like the thing itself; the
    # other three borrow the picture of what a player is doing when they walk into one, which is
    # walking, surfing and walking again. Better a true picture of half of it than a stand-in
    # invented for the other half.
    "dark-grass": "poke-ball",
    "rustling-grass": "poke-ball",
    "dust-cloud": "smoke-ball",
    "rippling-water": "hm03",
    "bridge-shadow": "poke-ball",
    # And the sequels' grottoes, which are the one place in Unova a player is looking for
    # something rather than walking into it. A Dowsing Machine is the picture of looking.
    "hidden-grotto": "dowsing-machine",
    # Generation 6's. Honey is what a player throws to call a horde, so the jar is the picture
    # of one; the Gracidea is the only flower in the item set; a berry tree is drawn as a berry.
    # Nothing in the games is a picture of being jumped, so an ambush keeps the ball.
    "horde": "honey",
    "flower-patch": "gracidea",
    "berry-tree": "oran-berry",
    "ambush": "poke-ball",
    # The Hoenn remakes'. Dive is HM07 in these games, picked up in Mossdeep City, and the Eon
    # Flute is the whole of Soaring: play it and a Latios or Latias comes for you.
    "dive": "hm07",
    "soaring": "eon-flute",
    "other": "poke-ball",
    # Gifts and statics.
    "starter": "poke-ball",
    "fossil": "helix-fossil",
    "egg": "lucky-egg",
    "npc-gift": "premier-ball",
    "static": "ultra-ball",
    # Evolution. A Moon Stone is the oldest picture of one thing becoming another.
    "evolution": "moon-stone",
    # Changing a form, which is a different thing from evolving: it is the same Pokemon after.
    # The Reveal Glass is the item that does it most plainly - point it at a Tornadus and it is
    # still a Tornadus.
    "form-change": "reveal-glass",
    # Breeding. The same egg as the gift kind above, on purpose: what the day care hands over
    # is an egg, and drawing it as something else to keep the two apart would be a worse
    # picture for the sake of a distinction the section headings already make.
    "breeding": "lucky-egg",
    # There is no trading item with a sprite: Link Cable and Linking Cord are not in the set.
    # The app draws that one itself rather than borrowing a picture that means something else.
}


@dataclass(frozen=True)
class Icon:
    """One downloaded icon, named after the method rather than the item."""

    file_name: str
    body: bytes
    url: str


def fetch_icons(client: PoliteClient, *, refresh: bool = False) -> list[Icon]:
    """Every method icon. A miss is logged and skipped: the app draws its own if one is absent."""
    found: list[Icon] = []

    for method, item in METHOD_ICONS.items():
        url = f"{SPRITES}/{item}.png"

        try:
            body = client.fetch(url, refresh=refresh).body
        except (httpx.HTTPError, OSError) as error:
            log.warning("no icon for %s (%s): %s", method, item, error)
            continue

        found.append(Icon(file_name=f"{method}.png", body=body, url=url))

    return found
