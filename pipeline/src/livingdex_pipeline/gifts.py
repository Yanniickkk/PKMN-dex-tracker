"""Gifts and statics for one game, from PokeAPI.

Step 4 is everything handed to you or waiting for you: the starter, the revived fossil, the egg
in someone's arms, the legendary asleep at the end of a cave. PokeAPI files all of it under the
same encounter tables as the wild slots, so the fetching is the same work with different methods
taken out of it.

What PokeAPI knows is the method, the place and the level. What it does not know is *who* hands
it over, what you have to have done first, and whether a "gift" is a starter, a fossil or a
present from a stranger - `gift` is one word for all three. Those are facts about one game, so
they come from that game's own file as a table of :class:`GiftDetail`, and this module only
puts the two halves together.

And sometimes it does not know the gift at all. The Karate King hands over a Tyrogue in all
three Generation 2 games and PokeAPI has the row for two of them, so a game may also bring
gifts written down by hand, cited to whoever was read - the same last resort, and the same
warning, as the hand-written wild slots in :mod:`wild`.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from . import conditions
from .forms import targets_of
from .models import (
    DexTarget,
    Form,
    GiftAcquisition,
    GiftKind,
    SourceCitation,
)
from .places import LocationNames
from .pokeapi import BASE_URL, PokeApiClient

log = logging.getLogger(__name__)

#: PokeAPI's encounter methods that are a gift or a static, and what this project calls them.
#:
#: ``gift`` covers starters, fossils and presents alike, so it lands on the most general of the
#: three; a game that knows better says so in its own table.
GIFT_METHODS: dict[str, GiftKind] = {
    "gift": GiftKind.NPC_GIFT,
    "gift-egg": GiftKind.EGG,
    "static": GiftKind.STATIC_ENCOUNTER,
    # One Pokemon standing in one spot, which is a static encounter however you reveal it. The
    # item it takes to see it comes through as a condition.
    "devon-scope": GiftKind.STATIC_ENCOUNTER,
    "squirt-bottle": GiftKind.STATIC_ENCOUNTER,
    "wailmer-pail": GiftKind.STATIC_ENCOUNTER,
    "pokeflute": GiftKind.STATIC_ENCOUNTER,
}

#: Methods that are a distribution event rather than anything in the game. Skipped with a word,
#: because "you had to be at a shop in Japan in 2003" is not a way to fill a dex today.
EVENT_METHODS = frozenset(
    {
        "colosseum-bonus-disc-jpn",
        "colosseum-bonus-disc-int",
        "event",
    }
)

#: Methods that are another game handing something over rather than this one.
#:
#: Manaphy hatches in Sinnoh from an egg a Pokemon Ranger cartridge sends across, which is a
#: fact about two games and a wireless link, not about anything in the grass. Skipped with a
#: word, the way a distribution event is, and answered where the unobtainable entries are.
OTHER_GAME_METHODS = frozenset({"pokemon-ranger"})


@dataclass(frozen=True)
class GiftDetail:
    """What a game knows about one of its gifts that PokeAPI cannot say.

    Every field is optional: a game that has nothing to add about a static leaves it out of the
    table entirely and the record still carries its place and level.
    """

    #: Overrides what the method alone suggests - a starter and a fossil are both `gift`.
    kind: GiftKind | None = None
    #: Who hands it over, when someone does.
    npc: str | None = None
    #: What has to be true first. Replaces the item read off the encounter's conditions.
    requirement: str | None = None
    #: What level it is handed over at, where the source's own row has it wrong.
    #:
    #: The last field to be needed and the one that says the least, because until the Let's Go
    #: pair the wording was what a game had to correct and never the number. PokeAPI has four of
    #: that pair's rows at a level two other sources agree with each other it is not - and its
    #: Electrode is 43, which is exactly what the Electrode in the same room of the same Power
    #: Plant was in Red and Blue. A number carried down twenty-two years of remakes of that room
    #: is not a number to keep.
    #:
    #: Nothing else in the dataset sets it. A game that leaves it out keeps what the row says,
    #: which is what every game before this pair does.
    level: int | None = None
    #: What the place itself asks before anything in it can be reached.
    #:
    #: Written *beside* what the conditions say rather than instead of them, which is the whole
    #: difference between this and :attr:`requirement`. The Hoenn remakes are why it exists:
    #: the Pathless Plain only appears off Route 131 while three Pokemon in the party have
    #: maxed EVs - which PokeAPI does not know - and which of the three legendaries is standing
    #: in it depends on the day, which PokeAPI does know and says better than a person would.
    gate: str | None = None
    #: What is handed over, where it is a form and the source says only the species.
    #:
    #: The forms step already teaches the wild and gift readers to ask for a species' whole set
    #: of Pokemon, which is how an Alolan Rattata gets a record of its own. It only works where
    #: the source gives the form a Pokemon to hang an encounter on, and sometimes it does not:
    #: Samson Oak hands out Totem-sized Pokemon for Totem Stickers and every one of those is
    #: filed under the ordinary species, which is the one thing it certainly is not. A plain
    #: Gumshoos is caught in the grass on Route 1; what he is holding is three feet taller.
    form: str | None = None
    #: Which of this species' gifts this describes, as the record spells the place: "Goldenrod
    #: City, Bills House". Left out when the species is only handed over once, which is the
    #: usual case.
    #:
    #: Johto is where this became necessary. Bill hands over an Eevee in Goldenrod and the
    #: Celadon Game Corner sells one for 6,666 coins; the Dragon Shrine's Master gives a Dratini
    #: for answering his quiz and the Goldenrod Game Corner sells one for 2,100. A table keyed
    #: by species alone would have put "From: Bill" on a slot machine prize, which is worse than
    #: saying nothing.
    where: str | None = None


#: What a game says about one species' gifts: one description, or one per place.
GiftDetails = GiftDetail | tuple[GiftDetail, ...]

#: Why a row is not kept: one reason for the whole species, or one per place it is filed under.
#:
#: The second shape is for a source that lists one encounter twice. PokeAPI has Unova's Friday
#: Musharna both in the Dreamyard and in the Dreamyard basement, and only the first row carries
#: the conditions that make it true - so the species is not wrong, one of its two places is.
Exclusion = str | Mapping[str, str]


def gift_encounters(
    api: PokeApiClient,
    *,
    game_id: str,
    version: str | Sequence[str],
    species: list[str],
    details: Mapping[str, GiftDetails] | None = None,
    excluded: Mapping[str, Exclusion] | None = None,
    refresh: bool = False,
    forms: Sequence[Form] = (),
    places: LocationNames | None = None,
) -> list[GiftAcquisition]:
    """Every gift and static in one game, as one record per place a Pokemon is given or waits.

    Unlike a wild slot there is nothing to add up: one of these is one Pokemon. Two rows that a
    player could not tell apart are still folded together, because PokeAPI does sometimes list
    the same encounter twice.

    ``excluded`` names species PokeAPI files under this version that the version does not
    actually hand over, and says why. It is not a way of tidying the output: PokeAPI lists both
    Sinnoh fossils under both halves of the pair, and Bulbapedia is clear that the Skull Fossil
    is Diamond's and the Armor Fossil is Pearl's. A source that is wrong about a version is a
    disagreement to record, not a row to keep.

    A reason can also be given per place rather than for the species, for the case where only
    one of its rows is wrong - see :data:`Exclusion`.

    ``version`` is usually one name and may be several, for the reason :func:`wild.wild_encounters`
    gives: the source files Galar's two expansions as versions of their own, so half the gifts in
    Sword are under ``the-isle-of-armor-sword`` and ``the-crown-tundra-sword``.

    ``forms`` is this game's own form table, and it is here for the reason it is in :mod:`wild`:
    what stands on Exeggutor Island is the Alolan Exeggutor and not the Kantonian one, and the
    10% Zygarde comes off the same Reassembly Unit as the 50%.
    """
    known = details or {}
    skip = excluded or {}
    #: Species this game handed over that its own table says nothing about. Reported at the end
    #: rather than per row: a game whose living dex reaches past its own Pokedex meets gifts
    #: nobody has written up yet, and the number is the size of that job.
    undescribed: set[str] = set()
    wanted_versions = (version,) if isinstance(version, str) else tuple(version)
    where = places or LocationNames(api, refresh=refresh)
    known_forms = {one.id for one in forms}
    found: list[GiftAcquisition] = []
    seen: set[tuple] = set()

    for name in species:
        whole_species = skip.get(name)
        if isinstance(whole_species, str):
            log.info("%s is not one of %s's gifts: %s", name, game_id, whole_species)
            continue

        # A gift hangs off a Pokemon rather than a species, and a species can be several.
        for pokemon, target in targets_of(api, name, known_forms, refresh=refresh):
            url = f"{BASE_URL}/pokemon/{pokemon}/encounters"
            citation = SourceCitation(
                source="pokeapi", url=url, retrieved_on=api.retrieved_on(url)
            )

            for area in api.encounters(pokemon, refresh=refresh):
                area_slug = area["location_area"]["name"]

                for version_details in area.get("version_details", []):
                    if version_details["version"]["name"] not in wanted_versions:
                        continue

                    for detail in version_details.get("encounter_details", []):
                        method = detail["method"]["name"]

                        if method in EVENT_METHODS:
                            log.info(
                                "%s in %s comes from a distribution event (%s), not from the game",
                                name,
                                game_id,
                                method,
                            )
                            continue

                        if method in OTHER_GAME_METHODS:
                            log.info(
                                "%s in %s comes across from another game (%s), not from this one",
                                name,
                                game_id,
                                method,
                            )
                            continue

                        if method not in GIFT_METHODS:
                            continue

                        place = where.of(area_slug)
                        not_here = _not_here(skip.get(name), _as_written(place))
                        if not_here is not None:
                            log.info(
                                "%s is not handed over in %s in %s: %s",
                                name,
                                _as_written(place),
                                game_id,
                                not_here,
                            )
                            continue

                        record = _record(
                            game_id=game_id,
                            target=target,
                            species=name,
                            place=place,
                            method=method,
                            detail=detail,
                            known=_detail_for(known.get(name), _as_written(place), species=name),
                            citation=citation,
                        )

                        key = _identity(record)
                        if key in seen:
                            continue

                        if name not in known:
                            undescribed.add(name)

                        seen.add(key)
                        found.append(record)

    if undescribed:
        log.info(
            "%s hands over %s species its gift table does not describe: %s",
            game_id,
            len(undescribed),
            ", ".join(sorted(undescribed)),
        )

    return found


def _record(
    *,
    game_id: str,
    target: DexTarget,
    species: str,
    place: tuple[str, str | None],
    method: str,
    detail: dict,
    known: GiftDetail,
    citation: SourceCitation,
) -> GiftAcquisition:
    values = [one["name"] for one in detail.get("condition_values", [])]

    return GiftAcquisition(
        game=game_id,
        # The game's own table wins here too, and for the same reason it wins about the giver:
        # the source has one row and no way of saying which of a species it is about.
        target=DexTarget(species=target.species, form=known.form) if known.form else target,
        gift_kind=known.kind or GIFT_METHODS[method],
        location=_as_written(place),
        npc=known.npc,
        # A gift comes at one level, so PokeAPI's range is a range of one - and the game's
        # own table wins here too, for the four rows in Let's Go where the range of one is
        # wrong. See :attr:`GiftDetail.level`.
        level=known.level if known.level is not None else detail.get("min_level"),
        # The game's own table wins: it can say "Odd Keystone in the Hallowed Tower, after
        # talking to 32 people in the Underground" where the conditions say two bare facts.
        # What the conditions say is the fallback, so that a game which has not been written
        # out yet loses nothing.
        # ``skip`` is empty because a gift record has no column for any of it: not the time of
        # day, not the season. Whatever the row says has to fit in this one sentence or be lost.
        requirement=conditions.joined(
            known.gate,
            known.requirement or conditions.requirement(values, subject=species, skip=()),
        ),
        source=citation,
    )


def _not_here(exclusion: Exclusion | None, place: str) -> str | None:
    """Why this one place is not kept, when the species itself is."""
    if exclusion is None or isinstance(exclusion, str):
        return None

    return exclusion.get(place)


def _as_written(place: tuple[str, str | None]) -> str:
    """A place as a gift record spells it.

    A gift has one line for where it happens and no room for a sub-area, so the two are read as
    one: "Route 119, Weather Institute".
    """
    location, sub_area = place

    return f"{location}, {sub_area}" if sub_area else location


def _detail_for(known: GiftDetails | None, place: str, *, species: str) -> GiftDetail:
    """What the game's table says about the gift in this place.

    A single description answers for every place the species is handed over. Several answer one
    each, and one of them may leave ``where`` out to cover the rest. A set of descriptions that
    between them say nothing about this place is a table that has drifted from the data - a
    place renamed, a gift moved - so it is said out loud rather than passing silently.
    """
    if known is None:
        return GiftDetail()

    if isinstance(known, GiftDetail):
        return known

    for one in known:
        if one.where == place:
            return one

    for one in known:
        if one.where is None:
            return one

    log.warning("%s is handed over in %s, which its gift table does not describe", species, place)

    return GiftDetail()


def _identity(record: GiftAcquisition) -> tuple:
    """Everything a player would use to tell two of these apart."""
    return (
        record.target.species,
        record.target.form,
        record.gift_kind,
        record.location,
        record.npc,
        record.level,
        record.requirement,
    )


@dataclass(frozen=True)
class RecordedGift:
    """One gift or static a source other than PokeAPI knows about.

    Everything a PokeAPI row and a :class:`GiftDetail` would have carried between them, in one
    place, because there is no row here for a table to describe.
    """

    species: str
    location: str
    #: Which form of it, when the game hands over one in particular.
    #:
    #: Hisui is the first to need it and needs it once: Request 83 hands over an **Alolan**
    #: Vulpix, where the Pokedex's own Vulpix is the Kantonian one. Without it the record says a
    #: Vulpix is handed over and the Alolan Ninetales it evolves into starts from a form nothing
    #: in the game produces.
    form: str | None = None
    level: int | None = None
    kind: GiftKind = GiftKind.NPC_GIFT
    npc: str | None = None
    requirement: str | None = None
    #: The page this one was read from, when it is not the page the rest of the table came from.
    #:
    #: A table read off one page needs no such thing and every table before Hisui's was. That
    #: game's statics are not on one page at all: the list of them is on ``Request``, which says
    #: which mission hands each over, and where each one stands is on the species' own article
    #: and nowhere else. Citing the list for a place it does not mention would be a footnote
    #: pointing at the wrong paragraph.
    source: SourceCitation | None = None


def recorded_gifts(
    *,
    game_id: str,
    gifts: Sequence[RecordedGift],
    species: Sequence[str],
    citation: SourceCitation,
) -> list[GiftAcquisition]:
    """Gifts written down by hand, for what PokeAPI does not carry.

    One record per gift, filtered to what this game's living dex asks for. The citation is the
    game file's to give and it is not a PokeAPI url, which is what makes these records tellable
    from the rest - and a gift that names its own page uses that instead, for the reason
    :attr:`RecordedGift.source` gives.
    """
    wanted = set(species)

    return [
        GiftAcquisition(
            game=game_id,
            target=DexTarget(species=gift.species, form=gift.form),
            gift_kind=gift.kind,
            location=gift.location,
            npc=gift.npc,
            level=gift.level,
            requirement=gift.requirement,
            source=gift.source or citation,
        )
        for gift in gifts
        if gift.species in wanted
    ]
