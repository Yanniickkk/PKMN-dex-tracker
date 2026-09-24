"""Generation 7's pictures, from the Bulbagarden Archives.

PokeAPI's sprite repository has a folder of battle sprites for every generation from the first
to the sixth and none for the seventh, so the four Alola cartridges have been drawing the shared
set since they were written. The Archives have what is missing, under their own names and their
own rules, and this module is those rules.

**Three sheets, not two.** The wiki prefixes a Generation 7 sprite with the games it came from,
and the three are ``7s`` for Sun and Moon, ``7u`` for Ultra Sun and Ultra Moon, and ``7p`` for
Let's Go. That last one matters here only because it is easy to mistake for the second: a search
that trusts the number finds ``Spr_7p_019A.png`` for an Alolan Rattata, which is a Let's Go
picture at 800 pixels square, where the Alola cartridges' own is 240.

**Ultra Sun and Ultra Moon have no sheet of their own**, and that is a finding rather than a
gap. Their category on the Archives holds 409 files against Sun and Moon's 1949, and what is in
it is what those two *added*: Dusk Mane, Dawn Wings and Ultra Necrozma, Dusk Form Lycanroc, the
Partner Cap Pikachu. Everything else in Ultra Sun is the picture Sun already had. So the four
share one folder, ``generation-vii/alola``, and ``7u`` is laid over ``7s`` rather than beside it.

**Where a file lives can be worked out rather than asked for.** MediaWiki keeps an upload at
``/media/upload/<first hex digit>/<first two>/<name>``, where the hex is the MD5 of the file
name. :mod:`boxart` reads a description page for the address because a cover is one request a
game and the name is spelled by a human; here it would double two thousand requests against a
host that asks five seconds between each, so the path is computed and the fetch is the proof.

**What a name is made of**, in the order this module builds them:

* the number, three digits, so Bulbasaur is ``001`` and Necrozma is ``800``;
* a letter code for a form - ``A`` for an Alolan one, ``Mn`` for Midnight Lycanroc, ``DM`` for
  Dusk Mane Necrozma - which is the wiki's own shorthand and follows no rule we could derive;
* ``_m`` or ``_f`` where the two sexes are drawn differently, and *neither* where they are not,
  so Rattata has no ``Spr_7s_019.png`` at all and Bulbasaur has nothing else.

That last one is why a species is asked for under two names. Which of the two comes first is
not a guess: a species drawn differently by sex is exactly a species this dataset holds a
``-female`` form for, so the table it already has says which to try.
"""

from __future__ import annotations

import hashlib
import io
import logging

import httpx
from PIL import Image

from .http import PoliteClient, RobotsDisallowed

log = logging.getLogger(__name__)

#: Where the files are. The same host :mod:`boxart` reads, under the same five-second interval.
ARCHIVES = "https://archives.bulbagarden.net"

#: Sun and Moon. 240 pixels square, about five kilobytes.
SM = "7s"

#: What Ultra Sun and Ultra Moon added to that, and nothing they left alone.
USUM = "7u"

#: Let's Go. 800 pixels square, and not these games' - here so it is not mistaken for ``7u``.
LETS_GO = "7p"

#: The folder under ``dataset/sprites`` that all four Alola cartridges draw from.
ALOLA_SET = "generation-vii/alola"

#: How far Sun and Moon's National Dex goes, and so how far their sheet does.
#:
#: Past this the second sheet is the only one there is: Poipole, Naganadel, Stakataka,
#: Blacephalon and Zeraora are the five Ultra Sun and Ultra Moon added, and Sun and Moon never
#: drew them because those two had never heard of them. Found by asking - all 802 up to here
#: answered to ``7s`` on the first name tried, and these five answered to nothing until they
#: were asked for under ``7u``.
SM_THROUGH = 802

#: The wiki's shorthand for a form, by the name this dataset gives it.
#:
#: Only the ones that are a rule rather than a list. ``Female`` and ``Alola`` each cover dozens
#: of forms and spell the same way every time; the rest - Unown's letters, Vivillon's patterns,
#: Arceus's types - are a hundred and thirty separate codes that would have to be read one at a
#: time, and a form with no code here falls back to the shared set's picture of that form, which
#: is the right picture drawn in another generation's style rather than a hole.
FORM_CODES: dict[str, str] = {
    "Female": "_f",
    "Alola": "A",
}

#: Everything Ultra Sun and Ultra Moon drew that Sun and Moon did not.
#:
#: This is the whole of the second sheet: four pictures, against Sun and Moon's eleven hundred.
#: Their category on the Archives holds a little over four hundred files and nearly all of them
#: are Pokedex artwork rather than battle sprites; what those two games actually redrew is
#: Necrozma twice over, Lycanroc's third form, and a Pikachu wearing the cap from the event.
#:
#: Keyed by the form this dataset names rather than by that name alone, because the names
#: collide where the codes do not: Lycanroc's Dusk Form is ``D`` and Necrozma's Dusk Mane is
#: ``DM``, and both are called Dusk here.
#:
#: Ultra Necrozma is the one picture in the category with nothing to hang it on - it is a state
#: a Pokemon is in for the length of a battle and not a form anything can be stored as, so this
#: dataset has no entry for it to fill.
USUM_FORMS: dict[str, str] = {
    "lycanroc-dusk": "D",
    "necrozma-dusk": "DM",
    "necrozma-dawn": "DW",
    "pikachu-partner-cap": "P",
}


def media_url(file_name: str) -> str:
    """Where the Archives keep a file, from its name alone.

    The hash is of the name exactly as the wiki stores it, underscores and all.
    """
    digest = hashlib.md5(file_name.encode("utf-8"), usedforsecurity=False).hexdigest()

    return f"{ARCHIVES}/media/upload/{digest[0]}/{digest[:2]}/{file_name}"


def species_names(number: int, *, sexed: bool = False) -> tuple[str, ...]:
    """What this species' front sprite might be called, likeliest first.

    The sheet follows the number: everything through :data:`SM_THROUGH` is Sun and Moon's, and
    the five past it are on Ultra Sun and Ultra Moon's because they are what those two added.

    ``sexed`` is what the form table already knows: a species drawn differently by sex has a
    ``-female`` form here, and on the wiki it has ``_m`` and ``_f`` and no plain name at all.
    Both spellings are offered either way, because being wrong about that should cost one extra
    request rather than a picture - which is what saved Eevee, whose female PokeAPI records and
    whose Generation 7 sheet draws only once.
    """
    sheet = SM if number <= SM_THROUGH else USUM
    plain = f"Spr_{sheet}_{number:03d}.png"
    male = f"Spr_{sheet}_{number:03d}_m.png"

    return (male, plain) if sexed else (plain, male)


def form_names(number: int, *, form_id: str, form_name: str) -> tuple[str, ...]:
    """What this form's front sprite might be called. Empty when there is no picture to ask for.

    Empty covers two different things and neither is a fault. A Totem Pokemon and an Own Tempo
    Rockruff are drawn as the ordinary form and have no file of their own - checked on the wiki
    rather than assumed - and Unown's letters, Vivillon's patterns and Arceus's types have files
    under a hundred and thirty separate codes that would each have to be read one at a time.
    Both fall back to the shared set's picture of that form, which is the right Pokemon in
    another generation's style rather than a hole.
    """
    if (usum := USUM_FORMS.get(form_id)) is not None:
        return (f"Spr_{USUM}_{number:03d}{usum}.png",)

    code = FORM_CODES.get(form_name)
    if code is None:
        return ()

    if code.startswith("_"):
        return (f"Spr_{SM}_{number:03d}{code}.png",)

    # A lettered form can itself be drawn twice - an Alolan Meowth is not, but nothing says a
    # later one could not be - so the plain spelling is tried first and the male second.
    return (
        f"Spr_{SM}_{number:03d}{code}.png",
        f"Spr_{SM}_{number:03d}{code}_m.png",
    )


def cropped(body: bytes) -> bytes:
    """The same picture with the empty air around it taken off.

    These are the only sprites in the dataset that arrive padded. The Archives put every
    Generation 7 Pokemon in the same 240 pixel frame, at its true size relative to the others,
    so a Wailord fills three fifths of it and a Pikachu a quarter - and the drawing inside is
    the same 60 pixels across as the Generation 6 one, which comes with no padding at all.

    In a grid that is one 56 pixel tile per Pokemon, ``object-fit: contain`` then draws that
    Pikachu at fourteen pixels beside a Kalos Pikachu at fifty-six. The relative sizing is real
    information and no other sheet here carries it, so it goes: a checklist is not a size chart,
    and one generation shrinking is a fault a reader sees before they see the cleverness.

    A picture that is empty is handed back untouched rather than cropped to nothing.
    """
    picture = Image.open(io.BytesIO(body))
    box = picture.convert("RGBA").getbbox()
    if box is None:
        return body

    out = io.BytesIO()
    picture.crop(box).save(out, format="PNG", optimize=True)

    return out.getvalue()


def first_picture(
    client: PoliteClient,
    candidates: tuple[str, ...],
    *,
    refresh: bool = False,
) -> bytes | None:
    """The first of these the Archives actually have.

    A miss is ordinary: it is how "this species is drawn once" is told apart from "this species
    is drawn twice", and the client remembers a 404 so the next build does not ask again.
    """
    for name in candidates:
        try:
            return client.fetch(media_url(name), refresh=refresh).body
        except (httpx.HTTPError, RobotsDisallowed) as error:
            log.debug("no %s: %s", name, error)

    return None
