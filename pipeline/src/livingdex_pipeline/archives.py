"""The pictures PokeAPI has none of, from the Bulbagarden Archives.

PokeAPI's sprite repository has a folder of battle sprites for every generation from the first
to the sixth and none for the seventh or the eighth, so every game from Sun onwards drew the
shared set until this module was written. The Archives have what is missing, under their own
names and their own rules, and this module is those rules.

**This file was called** ``gen7sprites`` **until Galar arrived**, which was true while Alola and
Let's Go were the only games in it. Sword and Shield are Generation 8 and read exactly the same
rules - the same three-digit number, the same form codes, the same ``_m`` and ``_f`` - so the
name was the only thing that had to change.

**Three sheets, and now two folders.** The wiki prefixes a Generation 7 sprite with the games
it came from, and the three are ``7s`` for Sun and Moon, ``7u`` for Ultra Sun and Ultra Moon,
and ``7p`` for Let's Go. The last one was written down here before it was wanted, because it is
easy to mistake for the second - a search that trusts the number finds ``Spr_7p_019A.png`` for
an Alolan Rattata, which is a Let's Go picture at 800 pixels square where the Alola cartridges'
own is 240. Step 6 of the Let's Go pair is when it stopped being a warning and became
:data:`LETS_GO_SET`.

**PokeAPI does have a Let's Go folder, and it is not usable.** It holds animated GIFs of the
models - 384 pixels square, thirty to seventy-five frames, three quarters of a megabyte to two
megabytes each, and named ``.gif`` where every other set in the repository is ``.png``. A
hundred and fifty-three of those is a quarter of a gigabyte for a picture drawn at 56 pixels in
a grid. Taking the first frame of each would work and would still be a pose out of an idle
animation rather than the front-facing render the wiki keeps, so the Archives win the same
argument twice.

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

#: Sword and Shield, whose models the wiki files under "Sword and Shield models".
#:
#: The frame is 1080 pixels square and the drawing inside it runs from about 240 to 770, which
#: is the largest thing in this dataset and the reason :func:`cropped` matters more here than
#: anywhere. Checked on the description page rather than guessed at, the way ``7p`` was: the
#: file says "Game model of #810 Grookey from Pokemon Sword and Shield" in as many words.
GALAR = "8s"

#: The folder under ``dataset/sprites`` that all four Alola cartridges draw from.
ALOLA_SET = "generation-vii/alola"

#: And the one the two Let's Go games draw from, which shares nothing with it but a generation.
LETS_GO_SET = "generation-vii/lets-go"

#: Sword and Shield's own folder, which is the first Generation 8 set in the dataset.
GALAR_SET = "generation-viii/sword-shield"

#: Pokemon HOME's artwork, which is what the games with no sheet of their own show.
#:
#: **The first set here that is not a generation's**, and it is named for what it is rather than
#: filed under one, because four games in two generations will share it. Brilliant Diamond and
#: Shining Pearl are the first: the Archives have no sheet for them at all - the only category
#: carrying their name holds trainer select-screen models - and the two files in the Scarlet and
#: Violet category are not a sheet either. What the wiki actually draws the modern games with is
#: HOME's own renders, 3,143 of them.
#:
#: That is the honest answer as well as the available one. These games have no battle sprite to
#: photograph: a HOME render is the picture a player of them sees when they open a box.
HOME_SET = "home"

#: And the marker that says a name is built HOME's way rather than a sheet's.
HOME = "home"

#: Which sheet a folder is filled from, for the sets that come off the Archives.
#:
#: ``None`` means "work it out from the number", which is Alola's rule and nobody else's: its
#: four cartridges split across two sheets at :data:`SM_THROUGH`. Let's Go is one sheet from
#: Bulbasaur to Melmetal.
ARCHIVES_SHEETS: dict[str, str | None] = {
    ALOLA_SET: None,
    LETS_GO_SET: LETS_GO,
    GALAR_SET: GALAR,
    HOME_SET: HOME,
}

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
    # The Let's Go partner, which is drawn twice and has no plain name at all: the wiki keeps
    # `Spr_7p_025P_m.png` and `Spr_7p_025P_f.png` and nothing between them. The same letter on
    # the `7u` sheet is the Partner Cap Pikachu, which is a hat rather than a partner and is
    # keyed by form id in :data:`USUM_FORMS` - one sheet apart, and they never meet.
    "Partner": "P",
    # Galar's own, checked the same way: ``Spr_8s_052G.png`` is the Galarian Meowth. Step 8 is
    # what wants it, and it is written here beside the Alolan one because the two sheets spell
    # a regional form the same way and there is nothing to choose between them.
    "Galar": "G",
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


def species_names(number: int, *, sheet: str | None = None, sexed: bool = False) -> tuple[str, ...]:
    """What this species' front sprite might be called, likeliest first.

    Without a ``sheet`` the number picks one, which is Alola's rule: everything through
    :data:`SM_THROUGH` is Sun and Moon's, and the five past it are on Ultra Sun and Ultra Moon's
    because they are what those two added. Let's Go passes its own and the number decides
    nothing - ``7p`` drew all 153 of that Pokedex, Meltan and Melmetal included.

    ``sexed`` is what the form table already knows: a species drawn differently by sex has a
    ``-female`` form here, and on the wiki it has ``_m`` and ``_f`` and no plain name at all.
    Both spellings are offered either way, because being wrong about that should cost one extra
    request rather than a picture - which is what saved Eevee, whose female PokeAPI records and
    whose Generation 7 sheet draws only once.

    HOME spells everything differently and more simply: four digits, no sheet code, no prefix
    but its own, and a plain name for every species - ``HOME0001.png``. Only the female is
    marked, with ``_f``, so unlike a sheet there is no ``_m`` to try and the plain name is
    always right. Shiny renders sit beside them under ``_s`` and this dataset has no use for
    one.
    """
    if sheet == HOME:
        return (f"HOME{number:04d}.png",)

    sheet = sheet or (SM if number <= SM_THROUGH else USUM)
    plain = f"Spr_{sheet}_{number:03d}.png"
    male = f"Spr_{sheet}_{number:03d}_m.png"

    return (male, plain) if sexed else (plain, male)


def form_names(
    number: int,
    *,
    form_id: str,
    form_name: str,
    sheet: str | None = None,
) -> tuple[str, ...]:
    """What this form's front sprite might be called. Empty when there is no picture to ask for.

    A ``sheet`` given is a sheet used, and :data:`USUM_FORMS` is skipped along with it: that
    table is the four pictures Ultra Sun and Ultra Moon added to Sun and Moon's sheet, and it
    has nothing to say about any other. The codes themselves carry over - an Alolan Rattata is
    ``019A`` on the Let's Go sheet as it is on Alola's - which is what makes one namer enough
    for both.

    Empty covers two different things and neither is a fault. A Totem Pokemon and an Own Tempo
    Rockruff are drawn as the ordinary form and have no file of their own - checked on the wiki
    rather than assumed - and Unown's letters, Vivillon's patterns and Arceus's types have files
    under a hundred and thirty separate codes that would each have to be read one at a time.
    Both fall back to the shared set's picture of that form, which is the right Pokemon in
    another generation's style rather than a hole.
    """
    if sheet == HOME:
        # HOME's own way of spelling a form is not read here yet, and nothing wants it: the two
        # games drawing from this set name no forms at all until their step 8. A form with no
        # name falls back to the shared set's picture, which is the right Pokemon in another
        # generation's style rather than a hole.
        return (f"HOME{number:04d}_f.png",) if form_name == "Female" else ()

    if sheet is None and (usum := USUM_FORMS.get(form_id)) is not None:
        return (f"Spr_{USUM}_{number:03d}{usum}.png",)

    code = FORM_CODES.get(form_name)
    if code is None:
        return ()

    on = sheet or SM

    if code.startswith("_"):
        return (f"Spr_{on}_{number:03d}{code}.png",)

    # A lettered form can itself be drawn twice - an Alolan Meowth is not, but nothing says a
    # later one could not be - so the plain spelling is tried first and the male second.
    return (
        f"Spr_{on}_{number:03d}{code}.png",
        f"Spr_{on}_{number:03d}{code}_m.png",
    )


def cropped(body: bytes) -> bytes:
    """The same picture with the empty air around it taken off.

    These are the only sprites in the dataset that arrive padded, and both Generation 7 sheets
    do it. The Archives put every Pokemon on a sheet in the same frame at its true size relative
    to the others - 240 pixels square for Alola, 800 for Let's Go - so a Wailord fills three
    fifths of it and a Pikachu a quarter. Alola's drawing inside is the same 60 pixels across as
    the Generation 6 one, which comes with no padding at all; Let's Go's is a render of a model
    and comes out between 150 and 500 pixels, which is the largest thing in this dataset and
    still a tenth of what the frame claimed.

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
