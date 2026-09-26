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

#: Legends: Arceus, which has a sheet of its own where the other four modern games have none.
#:
#: **And it only draws its own 242.** ``Spr_8a_001.png`` is a 404 because Bulbasaur is not in
#: Hisui, which is the first sheet here that is not a whole National Dex - the Generation 7 ones
#: draw everything up to their own number whether the game holds it or not.
HISUI = "8a"

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

#: Hisui's own folder, which is the second Generation 8 set and the only one of the last five
#: games in the series with a sheet behind it.
HISUI_SET = "generation-viii/legends-arceus"

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
    HISUI_SET: HISUI,
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
    # And Hisui's, which is the same letter a third time: ``Spr_8a_058H.png`` is the Hisuian
    # Growlithe. Unlike the other two it is not only step 8's, because of what
    # :func:`species_names` has to do with it.
    "Hisui": "H",
    # Basculin's third stripe, which is a form of the same shape and not a regional one: the
    # White-Striped Basculin is the only one in Hisui and the only one that becomes a
    # Basculegion. ``Spr_8a_550W.png``, and there is no plain 550 on that sheet at all.
    "White-Striped": "W",
    # And six more that the Legends: Arceus category turned out to spell as rules rather than as
    # a list. They were guessed at by nobody: the whole of that category is 367 file names, and
    # every code in it belongs to exactly one kind of form.
    "Origin": "O",
    "Therian": "T",
    "Sky": "S",
    "Sandy": "S",
    "Trash": "G",
    "East Sea": "E",
}

#: Unown's letters, which are a rule after all.
#:
#: This module said for three generations that they are "a hundred and thirty separate codes
#: that would have to be read one at a time", and put them in the same bucket as Vivillon's
#: patterns and Arceus's types. Reading a whole category rather than probing showed the rule:
#: the code is the letter, with ``EX`` for the exclamation mark and ``QU`` for the question
#: mark. ``Spr_8a_201B.png`` is the B.
UNOWN_CODES: dict[str, str] = {"!": "EX", "?": "QU"}

#: The codes a species on Hisui's sheet may be drawn under when it has no plain name.
#:
#: Sixteen species are in Legends: Arceus as one form and no other, so the sheet draws that form
#: and nothing else: fifteen Hisuian ones and the White-Striped Basculin. Both are read in
#: :func:`species_names` rather than left to the form table, because a tile showing the species
#: has to show the one the game has.
HISUI_ONLY: tuple[str, ...] = ("H", "W")

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



#: How HOME spells a form, which is the same idea as :data:`FORM_CODES` and not the same table.
#:
#: **It had to be read rather than assumed, and the reading was the whole of step 6.** HOME's
#: artwork category is 3,126 files and every code in it belongs to one kind of form, which is
#: what made it readable at all - the same trick that settled Hisui's list, on a category nine
#: times the size.
#:
#: Three of the codes are the sheets' own letters a fourth time: ``A`` for Alola, ``G`` for
#: Galar, ``H`` for Hisui. The rest are HOME's, and two of them are two letters where a sheet
#: uses one - ``La``, ``Sm``, ``Su`` for a Gourgeist's size - which is why this is a second
#: table rather than a few more rows in the first.
#:
#: **Every entry here was checked against the file's own description page**, which is the
#: Generation 7 lesson applied before it could cost anything: ``Spr_7p`` was read as Ultra Sun's
#: sheet for months because the number looked right. Rotom is where it would have hurt - its
#: five appliances are ``F``, ``L``, ``O``, ``R`` and ``W``, and only the page says that ``O``
#: is the oven and ``L`` is the lawnmower. Guessing alphabetically would have put a washing
#: machine on the microwave's tile.
HOME_FORM_CODES: dict[str, str] = {
    # The three regional letters, which every sheet since Alola has spelled the same way.
    "Alola": "A",
    "Galar": "G",
    "Hisui": "H",
    # Rotom's five appliances, read off five description pages rather than guessed at.
    "Fan": "F",
    "Mow": "L",
    "Heat": "O",
    "Frost": "R",
    "Wash": "W",
    # The Flabebe line's four other flowers, and the Eternal Flower that is only Floette's.
    "Blue": "B",
    "Orange": "O",
    "White": "W",
    "Yellow": "Y",
    "Eternal": "E",
    # Squawkabilly's three other plumages, which are the same letters with the word attached.
    "Blue-Plumage": "B",
    "White-Plumage": "W",
    "Yellow-Plumage": "Y",
    # The two-letter ones: Pumpkaboo's and Gourgeist's sizes.
    "Large": "La",
    "Small": "Sm",
    "Super": "Su",
    # And the four that are one form each.
    "Low-Key": "L",
    "Droopy": "D",
    "Stretchy": "S",
    "Roaming": "R",
    # Vivillon's patterns are three letters of the pattern's own name. Two of the nineteen are
    # in this dataset's Lumiose list, one is in Paldea's, and the rule would spell all of them.
    "Garden": "Gar",
    "Marine": "Mar",
    "Fancy": "Fan",
    # --- and Paldea's, which is the second game to need this table and added twenty to it ---
    #
    # **Paldean Tauros is where guessing would have cost most, and it is the Rotom lesson a
    # second time.** The three breeds are PA, PB and PC, and they are *alphabetical by the
    # breed's name* rather than in the order the game lists them - so PA is the Aqua Breed and
    # PC the Combat one, where reading the game's own order would have put the Combat bull on
    # the Aqua tile and back again. Every code below was read off the file's own description
    # page, which is the only reason that was caught.
    "Paldea": "P",
    "Paldea-Aqua-Breed": "PA",
    "Paldea-Blaze-Breed": "PB",
    "Paldea-Combat-Breed": "PC",
    # Basculin's stripes, the four seasons, and the two sea slugs.
    "Blue-Striped": "B",
    "White-Striped": "W",
    "Autumn": "A",
    "Summer": "S",
    "Winter": "W",
    "East Sea": "E",
    # Lycanroc's two, of which the midnight one needs two letters because D is already dusk.
    "Dusk": "D",
    "Midnight": "Mn",
    # Oricorio's three styles, all two letters.
    "Pau": "Pa",
    "Pom-Pom": "Po",
    "Sensu": "Se",
    # Minior's cores. Blue, Orange and Yellow are already above as the Flabebe line's flowers
    # and are the same letter, which is why this table is keyed by a form's name and not by a
    # species: a colour is a colour whoever is wearing it.
    "Red": "R",
    "Green": "G",
    "Indigo": "I",
    "Violet": "V",
    # Ogerpon's three masks, and Generation 9's own three.
    "Cornerstone-Mask": "C",
    "Hearthflame-Mask": "H",
    "Wellspring-Mask": "W",
    "Bloodmoon": "B",
    "Family-Of-Three": "T",
    "Three-Segment": "Th",
}

#: The one form of Legends: Z-A's ninety that this set does not draw.
#:
#: **A category is a good index and not a complete one, which is worth knowing before the next
#: game trusts one.** Reading the 3,126 files said ``HOME0710Sm.png`` was missing and that the
#: Small Size Pumpkaboo would have to fall back - and asking for it got a picture. The file is
#: there; the category does not list it. So the list below is what a *build* found rather than
#: what the category said, which is the only kind of answer worth writing down here.
#:
#: What is really absent is Torchic's female, whose ``HOME0255_f.png`` does not answer. It is
#: the wiki being short of an upload rather than the game being short of a Torchic, so that one
#: form falls back to the shared set's picture - the right Pokemon drawn another way.
#:
#: **Paldea added three more and none of them is in this tuple**, because a form with no code
#: in :data:`HOME_FORM_CODES` is never asked for and so can never be remembered as missing.
#: They are here in words because the reason differs each time and each one was read:
#:
#: * An **Own Tempo Rockruff** has no file because HOME draws it as an ordinary Rockruff, which
#:   is what it looks like. Nothing is missing.
#: * An **Antique Sinistea** and an **Antique Polteageist** have a file each - and it is the
#:   *back* of them, and its own description page says the render exists only in the mobile
#:   app. A back view on a tile would be worse than a fallback, so neither gets a code. This is
#:   the sharpest thing reading a description page has caught since Rotom's oven.
#:
#: All four fall back to the shared set, which is the right Pokemon in another style.
HOME_HAS_NO_PICTURE = ("torchic-female",)


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

    **Hisui's sheet needs two more names, and they are a form code where every other sheet's
    species name has none.** Fifteen species are in Legends: Arceus only as their Hisuian form,
    so the sheet draws no plain one at all: ``Spr_8a_058.png`` does not exist and
    ``Spr_8a_058H.png`` is the Growlithe that game has. Falling back to the shared set for those
    fifteen would put a Kantonian Growlithe on a Hisui tile, which is a different Pokemon rather
    than another generation's drawing of the same one.

    They go last, so a species drawn both ways still gets the plain one: Vulpix has
    ``Spr_8a_037.png`` and ``Spr_8a_037A.png``, and the Pokedex entry is the Kantonian one.
    Sneasel is drawn four times - ``215_m``, ``215_f``, ``215H_m`` and ``215H_f`` - which is why
    the sexed spelling of the coded name is here too.

    **And a female last of all, for one species.** Floatzel is drawn on this sheet exactly once,
    as ``Spr_8a_419_f.png``: there is no plain 419 and no ``_m``, which is the wiki being short
    of an upload rather than the game being short of a Floatzel. Asked for last, so it can only
    ever be the picture when nothing else is - and this game's own drawing of the right species
    beats the shared set's, which is what falling back would otherwise give.
    """
    if sheet == HOME:
        return (f"HOME{number:04d}.png",)

    sheet = sheet or (SM if number <= SM_THROUGH else USUM)
    plain = f"Spr_{sheet}_{number:03d}.png"
    male = f"Spr_{sheet}_{number:03d}_m.png"
    first = (male, plain) if sexed else (plain, male)

    if sheet != HISUI:
        return first

    coded: list[str] = []
    for code in HISUI_ONLY:
        one = f"Spr_{HISUI}_{number:03d}{code}.png"
        male_one = f"Spr_{HISUI}_{number:03d}{code}_m.png"
        coded.extend((male_one, one) if sexed else (one, male_one))

    return (*first, *coded, f"Spr_{HISUI}_{number:03d}_f.png")


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
    rather than assumed - and Vivillon's patterns and Arceus's types have files under codes that
    would each have to be read one at a time. Both fall back to the shared set's picture of that
    form, which is the right Pokemon in another generation's style rather than a hole.

    **Unown used to be in that second list and is not any more.** Reading a whole category
    instead of probing one name at a time showed that its letters are a rule: see
    :data:`UNOWN_CODES`.
    """
    if sheet == HOME:
        # **HOME spells a form the way a sheet does, and step 6 of Legends: Z-A is what read
        # it.** The comment that stood here said this was not read yet and that nothing wanted
        # it, which was true for as long as the only games drawing from this set named no forms.
        # That game names ninety.
        if form_name == "Female":
            return (f"HOME{number:04d}_f.png",)

        code = HOME_FORM_CODES.get(form_name)

        return (f"HOME{number:04d}{code}.png",) if code else ()

    if sheet is None and (usum := USUM_FORMS.get(form_id)) is not None:
        return (f"Spr_{USUM}_{number:03d}{usum}.png",)

    if form_id.startswith("unown-"):
        code = UNOWN_CODES.get(form_name, form_name.upper())
        return (f"Spr_{sheet or SM}_{number:03d}{code}.png",)

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
