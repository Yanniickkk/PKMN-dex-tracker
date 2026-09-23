"""Which forms of a species get an entry of their own, and in which games.

The app has had four switches for this since Phase 1 - regional, functional, cosmetic, gender -
and nothing to switch on: ``forms.json`` has been written empty ever since, and every game's
step 2 has been deferring to it. This is that table.

PokeAPI keeps the answer in three places and each needs its own reading:

* **Varieties** on the species are separate Pokemon with their own stats: Rotom's appliances,
  Wormadam's cloaks, the Therian trio, Kyurem's fusions.
* **Forms** under a Pokemon are one Pokemon wearing several faces: Unown's letters, Deerling's
  seasons, Shellos's two seas. Walking the varieties and then each variety's forms covers both
  shapes without having to know which one a species uses.
* **A flag and nothing else**: ``has_gender_differences``. Ninety-odd species in the first five
  generations have one and none of them has an entry anywhere - there are two sprites and a
  boolean.

Two questions the source cannot answer, and this module has to:

**Which kind it is.** There is no field for it, and the four switches are the whole point of
the table. It is worked out rather than listed: a form whose typing, base stats or abilities
differ from the species' own is functional, and one that differs in none of them is cosmetic.
That is why Unown's letters come out cosmetic and Wormadam's cloaks functional without anybody
deciding it twice - the letters are one Pokemon with 28 faces and the cloaks are three Pokemon.

**Which games it is in.** A form carries the version group it arrived in, which is most of the
answer: Rotom's appliances say ``platinum``, Therian Landorus says ``black-2-white-2``, and
everything from Generation 6 onward falls outside this dataset and drops out by itself. What
the version group cannot say is a form that arrived and then went no further, which is what
:data:`ONLY_IN` is for.

Two kinds of form are left out on purpose, because neither is a second Pokemon to catch:

* **Battle-only**, which the source does flag: Castform's weather, Cherrim's sunshine,
  Darmanitan's Zen Mode, Meloetta's Pirouette. They last until the battle ends.
* **Held-item**, which it does not: Arceus's seventeen plates and Genesect's four drives. Take
  the item off and the Pokemon is the same Pokemon again, so counting them would ask a player
  to catch one Arceus eighteen times.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field

from .models import Form, FormKind, PokemonType, Species
from .pokeapi import PokeApiClient

log = logging.getLogger(__name__)

#: Form names that mean a regional variant rather than anything else.
#:
#: None of them is in the first five generations - the earliest is Alola - and they are named
#: here anyway, because the day one arrives it should land in the right switch rather than be
#: measured by its stats like an ordinary form.
REGIONAL = frozenset({"alola", "galar", "hisui", "paldea"})

#: Form names that are the gender difference PokeAPI models as a form rather than as a flag.
#:
#: Only Frillish and Jellicent do this. Every other species with visible sexes carries a
#: boolean and no form at all, which :func:`gender_forms` answers instead.
GENDERED = frozenset({"male", "female"})

#: The version group from which a gender difference is worth an entry.
#:
#: Generation 4 is where the games started drawing the sexes differently. A female Venusaur has
#: had a narrower stripe since Diamond and Pearl and looks exactly like a male one in Red, so
#: an entry for it in a Kanto collection would be an entry for something nobody can see.
GENDER_FROM = "diamond-pearl"

#: Forms that exist only while an item is held, which is not a second Pokemon to catch.
#:
#: Two species, twenty-one forms, and both of them are Mythical Pokemon that no game in this
#: dataset produces anyway. Written by species rather than by form because that is the shape of
#: the fact: it is Arceus's plates and Genesect's drives, not a list of twenty-one accidents.
HELD_ITEM_FORMS = frozenset({"arceus", "genesect"})

#: Where a form is, when the version group it arrived in says more than the truth.
#:
#: The default is that a form reaches every game from its own version group onward, which is
#: right for almost all of them: Rotom's appliances arrived in Platinum and every later game
#: still has them.
#:
#: These are the ones where it is not. Deoxys is the awkward case of the series - each of the
#: three Generation 3 cartridges changes it into a different form, and PokeAPI can only say
#: which version *group* each form belongs to, so FireRed and LeafGreen come out sharing two
#: forms that neither of them shares. The spiky-eared Pichu is the other kind: it is in
#: HeartGold and SoulSilver, it cannot be traded or transferred, and so it goes no further.
#: Every game in this dataset that has a meteorite to change a Deoxys with.
#:
#: Generation 3 decides the forme by the cartridge and there is nothing a player can do about
#: it: a Deoxys is Normal in Ruby and Sapphire, Attack in FireRed, Defense in LeafGreen and
#: Speed in Emerald, and trading it is the only way to see another. From Generation 4 on a
#: meteorite cycles it through all four - outside in Veilstone City, on Route 3 in Johto, in the
#: Nacrene Museum, in Ambrette Town's Fossil Lab, in Professor Cozmo's house in Fallarbor.
#:
#: Written out because the version group a form arrived in cannot say it. All three formes
#: arrived with Generation 3 and were pinned to the one cartridge each of them came from, which
#: was right while this dataset held nothing later and wrong from Diamond on.
METEORITE: tuple[str, ...] = (
    "diamond",
    "pearl",
    "platinum",
    "heartgold",
    "soulsilver",
    "black",
    "white",
    "black-2",
    "white-2",
    "x",
    "y",
    "omega-ruby",
    "alpha-sapphire",
)

ONLY_IN: Mapping[str, tuple[str, ...]] = {
    "deoxys-attack": ("firered", *METEORITE),
    "deoxys-defense": ("leafgreen", *METEORITE),
    "deoxys-speed": ("emerald", *METEORITE),
    "pichu-spiky-eared": ("heartgold", "soulsilver"),
}

#: What to call a form on screen, where the slug does not say it well.
#:
#: The app prints "Shellos (West Sea)", so this is the part in brackets rather than the whole
#: name. Everything not named here is its form name with the words capitalised, which is right
#: for Heat, Therian, Summer and eighty others.
LABELS: Mapping[str, str] = {
    "exclamation": "!",
    "question": "?",
    "east": "East Sea",
    "west": "West Sea",
    "spiky-eared": "Spiky-eared",
}


@dataclass
class VersionGroupGames:
    """Which games are in each version group, and where each group sits in the series.

    A game id and PokeAPI's version name are the same string for every game in this dataset,
    which is checked rather than assumed: a game the registry knows and the source does not
    would otherwise quietly lose all of its forms.
    """

    api: PokeApiClient
    game_ids: frozenset[str]
    refresh: bool = False
    _order: dict[str, int] = field(default_factory=dict)
    _games: dict[str, tuple[str, ...]] = field(default_factory=dict)
    _generation: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        listing = self.api.resource("version-group?limit=100", refresh=self.refresh)

        for entry in listing["results"]:
            group = self.api.resource(f"version-group/{entry['name']}", refresh=self.refresh)
            self._order[entry["name"]] = int(group["order"])
            self._games[entry["name"]] = tuple(
                version["name"] for version in group["versions"] if version["name"] in self.game_ids
            )
            for game in self._games[entry["name"]]:
                self._generation[game] = generation_of(group["generation"]["url"])

        missing = self.game_ids - set(self._generation)
        if missing:
            raise FormsError(
                "these games are not any version group's: " + ", ".join(sorted(missing))
            )

    @property
    def newest_generation(self) -> int:
        """The latest generation any game here belongs to."""
        return max(self._generation.values())

    def knows(self, group: str) -> bool:
        return group in self._order

    def order_of(self, group: str) -> int:
        return self._order[group]

    def from_group_on(self, group: str, *, generation: int) -> list[str]:
        """Every game in that version group or a later one that can hold the species at all.

        Two filters rather than one, and the second is easy to forget. A gender difference
        arrived in Generation 4 and every game from Diamond onward draws it - but only for a
        species those games have. Pyroar's sexes look nothing alike and Pyroar is two
        generations away from the newest game here, so the answer for it is no games at all
        rather than nine.
        """
        here = self.order_of(group)

        return sorted(
            game
            for name, games in self._games.items()
            if self._order[name] >= here
            for game in games
            if self._generation[game] >= generation
        )


def generation_of(url: str) -> int:
    """The number in a generation's address, which is the only place the source writes it.

    The name is a roman numeral - ``generation-v`` - and the url ends in ``/generation/5/``.
    Reading the number is less work than agreeing with the wiki about numerals.
    """
    return int(url.rstrip("/").rsplit("/", 1)[-1])


class FormsError(Exception):
    """The form table could not be built. The message is meant for a human."""


@dataclass(frozen=True)
class FormTable:
    """The table the dataset carries, and where each entry's picture might be.

    The pictures are not part of the table: a form's record says what it is and which games
    have it, and which file a sprite sheet keeps it in is the sprite step's business. They come
    back together because working them out twice would mean walking every species twice.
    """

    forms: list[Form]
    #: Form id -> the names to try under a sprite set's folder, best first.
    pictures: Mapping[str, tuple[str, ...]]


def form_table(
    api: PokeApiClient,
    *,
    species: Sequence[Species],
    game_ids: Iterable[str],
    refresh: bool = False,
) -> FormTable:
    """Every form of every species given, in the games that have it.

    By form id, which is the order :meth:`~.emit.DatasetWriter.write_forms` writes them in and
    therefore the order :func:`~.emit.read_forms` hands them back. Sorted here so that the table
    a full build holds in memory and the table a single-game build reads off disk are the same
    list: a game writes its form records in the order it is given them, and for a while the same
    game built two ways produced the same records twice over in two different orders.
    """
    groups = VersionGroupGames(api, frozenset(game_ids), refresh=refresh)
    found: list[Form] = []
    pictures: dict[str, tuple[str, ...]] = {}

    for one in species:
        found.extend(_forms_of(api, one, groups, pictures, refresh=refresh))

    return FormTable(forms=sorted(found, key=lambda one: one.id), pictures=pictures)


def form_pictures(
    api: PokeApiClient,
    forms: Sequence[Form],
    *,
    refresh: bool = False,
) -> dict[str, tuple[str, ...]]:
    """Where each of these forms' pictures might be, worked out from the source again.

    For a build that did not make the table itself. The table is on disk with everything the
    dataset needs; which file a sprite sheet would keep each picture in is not part of it, and
    this is cheaper than rebuilding the table to find out - only the species that have a form
    are asked about, and every answer is already in the cache.
    """
    wanted = {one.species for one in forms}
    numbers = {one.species: one for one in forms}
    pictures: dict[str, tuple[str, ...]] = {}

    for species in sorted(wanted):
        raw = api.resource(f"pokemon-species/{species}", refresh=refresh)
        default = _default_pokemon(api, raw, refresh=refresh)

        for pokemon, slug, face in _faces(api, raw, refresh=refresh):
            pictures[slug] = _pictures(face, pokemon, default=default)

        # The gender flag has no form anywhere in the source, so nothing above named it.
        pictures.setdefault(f"{species}-female", (f"female/{int(raw['id'])}.png",))

    # Only the forms actually asked about, so a species' unused faces do not leak in.
    return {one.id: pictures[one.id] for one in forms if one.id in pictures and numbers}


def _faces(api: PokeApiClient, raw: dict, *, refresh: bool):
    """Every face of a species, as (its Pokemon, the face's slug, the face).

    The walk both readings of the source need: varieties first, then the forms under each one,
    which is how a Wash Rotom and an Unown letter come out of the same loop.
    """
    for variety in raw["varieties"]:
        pokemon = api.resource(f"pokemon/{variety['pokemon']['name']}", refresh=refresh)

        for entry in pokemon["forms"]:
            yield (
                pokemon,
                entry["name"],
                api.resource(f"pokemon-form/{entry['name']}", refresh=refresh),
            )


def _forms_of(
    api: PokeApiClient,
    species: Species,
    groups: VersionGroupGames,
    pictures: dict[str, tuple[str, ...]],
    *,
    refresh: bool,
) -> list[Form]:
    raw = api.resource(f"pokemon-species/{species.id}", refresh=refresh)
    generation = generation_of(raw["generation"]["url"])

    # Asked before its varieties are, which saves the build a thousand requests: the species
    # table reaches every generation and this dataset stops at Generation 5, so most of what
    # would be fetched here is a Mega or a regional form of something no game has.
    if generation > groups.newest_generation:
        return []

    default = _default_pokemon(api, raw, refresh=refresh)

    found: list[Form] = []
    for pokemon, slug, face in _faces(api, raw, refresh=refresh):
        form = _form(
            species=species,
            pokemon=pokemon,
            default=default,
            slug=slug,
            face=face,
            groups=groups,
            generation=generation,
            pictures=pictures,
        )
        if form is not None:
            found.append(form)

    if raw.get("has_gender_differences") and not any(one.kind is FormKind.GENDER for one in found):
        gendered = _gender_form(species, groups, generation=generation)
        # Empty for a species from a generation this dataset does not reach yet, which is most
        # of them: Pyroar's sexes look nothing alike and no game here has a Pyroar.
        if gendered.games:
            found.append(gendered)
            # The one sprite layout that is a folder rather than a file name: a sheet keeps its
            # female sprites under `female/`, by the species' own number.
            pictures[gendered.id] = (f"female/{species.national_dex_number}.png",)

    return found


def _form(
    *,
    species: Species,
    pokemon: dict,
    default: dict,
    slug: str,
    face: dict,
    groups: VersionGroupGames,
    generation: int,
    pictures: dict[str, tuple[str, ...]],
) -> Form | None:
    raw = face

    # The species' own face, which is the line the form sits under rather than a form of it.
    if raw["is_default"] and pokemon["name"] == default["name"]:
        return None

    if raw["is_battle_only"] or raw["is_mega"] or species.id in HELD_ITEM_FORMS:
        return None

    group = raw["version_group"]["name"]
    if not groups.knows(group):
        raise FormsError(f"{slug} names a version group nothing knows: {group}")

    games = ONLY_IN.get(slug) or groups.from_group_on(group, generation=generation)
    if not games:
        # Introduced after the last game this dataset holds, which every Mega, Gmax and
        # regional form of these species is. Expected rather than exceptional.
        return None

    pictures[slug] = _pictures(raw, pokemon, default=default)
    types = _types(raw, pokemon)

    return Form(
        id=slug,
        species=species.id,
        name=_label(raw["form_name"]),
        kind=_kind(raw["form_name"], pokemon=pokemon, default=default, types=types),
        games=sorted(games),
        types=types if types != species.types else None,
    )


def _pictures(raw: dict, pokemon: dict, *, default: dict) -> tuple[str, ...]:
    """Which file a sprite sheet would keep this form's picture in, best guess first.

    Two layouts, because a form is one of two things. A variety is its own Pokemon with its own
    number - Wash Rotom is 10009 - and a sheet files it under that. A face of one Pokemon has
    no number of its own and is filed under the species' number and the face's name, which is
    what the source's own address for it already says: ``585-summer.png``.

    Both are offered for a variety, because the sheets are not consistent about it: the
    spiky-eared Pichu is a variety and the Generation 4 sheet has it as ``172-spiky-eared.png``.
    The sprite step tries them in order and shrugs when a sheet has neither, which is the usual
    case - most sheets only drew what their own games showed.
    """
    named = _named_picture(raw)

    if pokemon["name"] != default["name"]:
        numbered = f"{pokemon['id']}.png"
        return (numbered, named) if named else (numbered,)

    return (named,) if named else ()


def _named_picture(raw: dict) -> str | None:
    """The file name the source's own address for this form ends in."""
    address = (raw.get("sprites") or {}).get("front_default")

    return address.rsplit("/", 1)[-1] if address else None


def _gender_form(species: Species, groups: VersionGroupGames, *, generation: int) -> Form:
    """The entry for a species whose sexes are drawn differently and have no form of their own.

    One line rather than two: the species' own line is the male, as the games' own sprite sets
    have it, and this is the other half.
    """
    return Form(
        id=f"{species.id}-female",
        species=species.id,
        name="Female",
        kind=FormKind.GENDER,
        games=sorted(groups.from_group_on(GENDER_FROM, generation=generation)),
    )


def _kind(
    form_name: str,
    *,
    pokemon: dict,
    default: dict,
    types: list[PokemonType],
) -> FormKind:
    """Which switch decides whether this form is an entry.

    Measured rather than listed, and the measurement is the same question a player asks: is
    this a different Pokemon to raise, or the same one in different colours? Typing, base stats
    and abilities are what "different" means there, and a form that matches the species in all
    three is a repaint.
    """
    if form_name in REGIONAL:
        return FormKind.REGIONAL

    if form_name in GENDERED:
        return FormKind.GENDER

    if types != _types_of(default) or _stats(pokemon) != _stats(default):
        return FormKind.FUNCTIONAL

    if _abilities(pokemon) != _abilities(default):
        return FormKind.FUNCTIONAL

    return FormKind.COSMETIC


def _default_pokemon(api: PokeApiClient, raw: dict, *, refresh: bool) -> dict:
    name = next(variety["pokemon"]["name"] for variety in raw["varieties"] if variety["is_default"])

    return api.resource(f"pokemon/{name}", refresh=refresh)


def _types(raw: dict, pokemon: dict) -> list[PokemonType]:
    """The form's own typing when it carries one, the Pokemon's otherwise.

    The form carries it for every form that has one of its own, which is how Arceus's plates
    are told apart while sharing a single Pokemon between them.
    """
    if raw.get("types"):
        return _typed(raw["types"])

    return _types_of(pokemon)


def _types_of(pokemon: dict) -> list[PokemonType]:
    return _typed(pokemon["types"])


def _typed(entries: list[dict]) -> list[PokemonType]:
    return [PokemonType(one["type"]["name"]) for one in sorted(entries, key=_slot)]


def _slot(entry: dict) -> int:
    return int(entry["slot"])


def _stats(pokemon: dict) -> tuple[tuple[str, int], ...]:
    return tuple(
        (one["stat"]["name"], int(one["base_stat"]))
        for one in sorted(pokemon["stats"], key=lambda one: one["stat"]["name"])
    )


def _abilities(pokemon: dict) -> tuple[str, ...]:
    return tuple(sorted(one["ability"]["name"] for one in pokemon["abilities"]))


def _label(form_name: str) -> str:
    if form_name in LABELS:
        return LABELS[form_name]

    return "-".join(word.capitalize() for word in form_name.split("-"))
