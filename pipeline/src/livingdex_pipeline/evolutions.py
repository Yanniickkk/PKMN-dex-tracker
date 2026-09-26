"""Evolution rules, and which of them a game can actually use.

Two halves of step 5. The rules themselves are shared: "Kadabra becomes Alakazam when traded"
is true of every game that has both, so it is written once into ``evolution-rules.json`` and
every game points at it. What is per-game is *whether* a rule applies, and that is what an
:class:`~.models.EvolutionAcquisition` in a game file says.

PokeAPI answers both. Its evolution chains carry a ``version_group`` on each detail, naming
where that way of evolving started rather than which games have it - so Feebas is listed twice,
once as Ruby and Sapphire's Beauty and once as Black and White's Prism Scale, and Kirlia's
Gallade branch is stamped Diamond and Pearl. Picking the newest variant at or before the game
being built is therefore the whole of "which evolution triggers are actually possible here":
Emerald gets Beauty and no Gallade, without anyone writing either fact down by hand.

A rule with no variant old enough simply produces nothing, which is the right answer: an
Emerald player cannot evolve Roselia, and a dex that claimed otherwise would send them looking
for a Shiny Stone that is four years away.
"""

from __future__ import annotations

import logging
from collections.abc import Container, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date

import httpx

from .models import (
    DexTarget,
    EvolutionAcquisition,
    EvolutionCondition,
    EvolutionRule,
    EvolutionTrigger,
    Form,
    FriendshipCondition,
    GenderCondition,
    HeldItemCondition,
    KnownMoveCondition,
    LocationCondition,
    MinimumLevelCondition,
    OtherCondition,
    SourceCitation,
    TimeOfDayCondition,
    TradePartnerCondition,
    UsedItemCondition,
)
from .places import english, pretty
from .pokeapi import BASE_URL, PokeApiClient
from .sources import bulbapedia

log = logging.getLogger(__name__)

#: PokeAPI's triggers that this project has a name for. Anything else is ``other`` and says
#: what it was in a condition, so a rule stays readable without the enum growing a case per
#: gimmick generation.
TRIGGERS: dict[str, EvolutionTrigger] = {
    "level-up": EvolutionTrigger.LEVEL_UP,
    "use-item": EvolutionTrigger.USE_ITEM,
    "trade": EvolutionTrigger.TRADE,
}

#: How the triggers without a name of their own read on screen, as the sentence that follows
#: "Some other way". Written out rather than derived from the slug: "shed" on its own tells a
#: player nothing about the party slot and the spare ball that Shedinja actually needs.
OTHER_TRIGGERS: dict[str, str] = {
    "shed": "with a free slot in the party and a spare Poke Ball",
    "spin": "by spinning around holding the sweet",
    "tower-of-darkness": "after training in the Tower of Darkness",
    "tower-of-waters": "after training in the Tower of Waters",
    "three-critical-hits": "after three critical hits in one battle",
    "take-damage": "after taking enough damage without fainting",
    "recoil-damage": "after taking enough recoil damage",
    "agile-style-move": "after using an agile style move enough times",
    "strong-style-move": "after using a strong style move enough times",
    # Generation 9's four, and every one of them was already in the dataset reading as its own
    # slug before Scarlet and Violet were written: Legends: Z-A lists Primeape and Gimmighoul,
    # so "use move" and "gimmighoul coins" have been on two tiles since that game was built.
    # Writing these down fixes those as well, which is what a shared table is for.
    "in-battle-level-up": "by levelling up during a battle",
    "use-move": "after using one of its own moves",
    "three-defeated-bisharp": "after defeating three Bisharp that lead a pack",
    "gimmighoul-coins": "by collecting enough Gimmighoul Coins",
    "other": "in a way the source does not spell out",
}

#: Details that are a plain yes-or-no, and the words they turn into.
FLAG_CONDITIONS: dict[str, str] = {
    "near_special_rock": "beside the mossy or icy rock",
    "needs_overworld_rain": "while it is raining outside",
    "turn_upside_down": "with the console turned upside down",
    "needs_multiplayer": "with another player",
}

#: Which stat has to be the higher one, as PokeAPI numbers it.
PHYSICAL_STATS: dict[int, str] = {
    1: "with Attack higher than Defense",
    0: "with Attack and Defense equal",
    -1: "with Defense higher than Attack",
}

#: PokeAPI's gender numbers.
GENDERS: dict[int, str] = {1: "female", 2: "male"}

#: Internals a player has no way to act on. Skipped without a word.
#:
#: The two form fields used to be here, with a note that the forms table did not carry them
#: yet. It does now, and they turned out to be carrying most of Generation 7: it is
#: ``evolved_pokemon_form`` that says a Thunder Stone in Alola makes an *Alolan* Raichu, and
#: ``required_pokemon_form`` that says only an Alolan Vulpix takes the Ice Stone.
IGNORED_DETAILS = frozenset(
    {
        "trigger",
        "version_group",
        "is_default",
        "required_pokemon_form",
        "evolved_pokemon_form",
    }
)


@dataclass
class VersionGroups:
    """Version group -> where it sits in the series, remembering what it has been asked.

    An evolution detail names the version group it started in, and a game is only allowed the
    ones at or before its own. That is an ordering question rather than a generation one:
    Emerald and FireRed are both Generation III, and PokeAPI's ``order`` is what puts them in
    sequence.
    """

    api: PokeApiClient
    refresh: bool = False
    _cache: dict[str, int] = field(default_factory=dict)

    def order_of(self, name: str) -> int:
        if name not in self._cache:
            group = self.api.resource(f"version-group/{name}", refresh=self.refresh)
            self._cache[name] = int(group["order"])

        return self._cache[name]


@dataclass
class Varieties:
    """Species -> the Pokemon of it that are not the default, remembering what it has been asked.

    The whole of telling PokeAPI's two kinds of form name apart. ``evolved_pokemon_form`` points
    at a *form* resource, and the source has a form for the default as readily as for anything
    else: the ordinary Lycanroc is ``lycanroc-midday``, the ordinary Gastrodon is
    ``gastrodon-west``, the ordinary Burmy is ``burmy-plant``. None of those is a second
    Pokemon, and none of them is a form this project records.

    A name that is also one of the species' non-default Pokemon is the other kind, and that one
    is a real fork in the chain: ``lycanroc-midnight``, ``gastrodon-east``, ``raichu-alola``.
    The distinction cannot be made by looking at the name - ``lycanroc-midday`` and
    ``lycanroc-midnight`` are spelled the same way - which is why this asks the source.
    """

    api: PokeApiClient
    refresh: bool = False
    _cache: dict[str, frozenset[str]] = field(default_factory=dict)

    def has(self, species: str, name: str | None) -> bool:
        """Whether this name is one of the species' other Pokemon rather than a form of its one."""
        return name is not None and name in self.of(species)

    def of(self, species: str) -> frozenset[str]:
        if species not in self._cache:
            self._cache[species] = frozenset(
                name
                for name, is_default in self.api.varieties(species, refresh=self.refresh)
                if not is_default
            )

        return self._cache[species]


@dataclass
class EnglishNames:
    """Slug -> the name a player would read, for whatever resource it belongs to."""

    api: PokeApiClient
    refresh: bool = False
    _cache: dict[tuple[str, str], str] = field(default_factory=dict)

    def of(self, resource: str, slug: str) -> str:
        key = (resource, slug)
        if key not in self._cache:
            raw = self.api.resource(f"{resource}/{slug}", refresh=self.refresh)
            self._cache[key] = english(raw.get("names", []), fallback=pretty(slug))

        return self._cache[key]


@dataclass(frozen=True)
class MissingVariant:
    """One way of evolving that PokeAPI does not carry, and the page it was read from.

    **A fact about one game, not about the series, and that is the correction Legends: Z-A
    forced.** This used to say the opposite - that the Linking Cord evolves a Kadabra for
    whoever is holding one, and that which games may use it follows from its version group
    exactly as it does for a way the source carried. The first half is true and the second is
    not: the item's own page lists Legends: Arceus as the only game it can be obtained in, and
    Kadabra's evolution chart marks it "LA only". Carried forward, it told a player of the next
    Legends game to use an item that game does not have.

    So a hand-written way stays in the version group it was read from. A way the source carries
    still moves forward, because there the source is saying "this is how it works from here";
    here a person read one item's page in one game.
    """

    from_species: str
    to_species: str
    version_group: str
    trigger: EvolutionTrigger
    conditions: tuple[EvolutionCondition, ...]
    #: The Bulbapedia page this was read from, which the records made from it cite instead of a
    #: chain url. Citing the chain would point at a document that does not say this.
    page: str


#: The day a person read the item pages the table below was typed from.
NOT_IN_THE_SOURCE_READ_ON = date(2026, 9, 25)

#: Ways of evolving that PokeAPI has no detail for, filled in by hand.
#:
#: The same last resort, and the same warning, as the hand-written wild slots in :mod:`wild` and
#: the hand-written gifts in :mod:`gifts` - and it took until the twenty-ninth game for one to
#: be needed, because until Hisui the source had every way a Pokemon could change.
#:
#: **Legends: Arceus has no held items and no in-game trade**, and between them those two facts
#: break every trade evolution in the series. The game's answer is that the item is simply used:
#: a Linking Cord on the four that needed nothing but a cable, and the item itself on the eight
#: that were held during one. PokeAPI carries none of this - ``kadabra`` still has exactly one
#: detail, ``red-blue`` and ``trade`` - so a build that trusted the source told a player of the
#: one core series game without in-game trades to go and trade a Kadabra.
#:
#: Read off each item's own article rather than generalised from one: the Linking Cord's page
#: names its four, and each of the other eight says the same sentence in its own words - "due to
#: the absence of held items, the Metal Coat simply needs to be used on Onix or Scyther".
#:
#: What is deliberately *not* here is anything that only changes how hard something is. These
#: twelve are the pairs where the way the source gives cannot be done in this game at all.
NOT_IN_THE_SOURCE: tuple[MissingVariant, ...] = (
    # The four that needed a cable and nothing else. One page names all four.
    *(
        MissingVariant(
            from_species=before,
            to_species=after,
            version_group="legends-arceus",
            trigger=EvolutionTrigger.USE_ITEM,
            conditions=(UsedItemCondition(item="Linking Cord"),),
            page="Linking_Cord",
        )
        for before, after in (
            ("kadabra", "alakazam"),
            ("machoke", "machamp"),
            ("graveler", "golem"),
            ("haunter", "gengar"),
        )
    ),
    # And the eight that were traded holding something, which is now used instead.
    *(
        MissingVariant(
            from_species=before,
            to_species=after,
            version_group="legends-arceus",
            trigger=EvolutionTrigger.USE_ITEM,
            conditions=(UsedItemCondition(item=item),),
            page=page,
        )
        for before, after, item, page in (
            ("onix", "steelix", "Metal Coat", "Metal_Coat"),
            ("scyther", "scizor", "Metal Coat", "Metal_Coat"),
            ("rhydon", "rhyperior", "Protector", "Protector"),
            ("electabuzz", "electivire", "Electirizer", "Electirizer"),
            ("magmar", "magmortar", "Magmarizer", "Magmarizer"),
            ("porygon", "porygon2", "Upgrade", "Up-Grade"),
            ("porygon2", "porygon-z", "Dubious Disc", "Dubious_Disc"),
            ("dusclops", "dusknoir", "Reaper Cloth", "Reaper_Cloth"),
        )
    ),
)


@dataclass(frozen=True)
class _Variant:
    """One way of evolving, and the version group it started in.

    ``from_form`` and ``to_form`` are what PokeAPI's two form fields said, raw: a *form* name,
    which is not the same thing as a Pokemon name. ``from_fork`` and ``to_fork`` say whether
    that name is also one of the species' other Pokemon, which is the source's own line between
    two quite different things wearing the same spelling.

    Both are needed, and one without the other gets it wrong. ``gastrodon-east`` is a form of
    the only Gastrodon there is, so the fork flag is false and it is still a form worth naming.
    ``lycanroc-midday`` is a form of the only default Lycanroc, the flag is false too, and it is
    *not* worth naming - it is the species. What separates them is whether anything in this
    project records the form. And ``lycanroc-dusk`` is a second Pokemon that this project may
    record nowhere at all, which is neither of the first two cases and must not quietly become
    the plain Lycanroc.
    """

    from_species: str
    to_species: str
    version_group: str
    order: int
    trigger: EvolutionTrigger
    conditions: tuple[EvolutionCondition, ...]
    #: Whether this way of evolving is that one game's and stops there, rather than the series'
    #: from then on.
    #:
    #: **False for everything PokeAPI carries and true for everything in**
    #: :data:`NOT_IN_THE_SOURCE`. A rule read off a chain is the source saying "this is how it
    #: works from here", and the picker is right to carry it forward. A rule typed in by hand
    #: was read off *one item's page in one game*, and carrying it forward is how Legends: Z-A
    #: came to tell a player to use a Linking Cord - an item whose own page lists Legends:
    #: Arceus as the only game it can be obtained in, and whose entry on Kadabra's evolution
    #: chart is marked "LA only".
    only_in_its_own_game: bool = False
    from_form: str | None = None
    to_form: str | None = None
    from_fork: bool = False
    to_fork: bool = False
    #: Set only on the ways :data:`NOT_IN_THE_SOURCE` supplies. A string rather than a citation
    #: so that a variant stays hashable, which it has to be: it is a dict key twice over.
    page: str | None = None

    @property
    def pair(self) -> tuple[str, str]:
        return (self.from_species, self.to_species)


def evolution_rules(
    api: PokeApiClient,
    *,
    chains: Sequence[str],
    forms: Sequence[Form] = (),
    refresh: bool = False,
) -> list[EvolutionRule]:
    """Every rule in the chains given, across every generation.

    The table is shared, so it holds each variant rather than only the current one: a game file
    points at the variant it can use, and the two Feebas rules sitting side by side are what
    makes "trade holding a Prism Scale" visible as something later games do rather than as
    something Emerald forgot.

    ``forms`` is the whole form table, not one game's. A rule is a fact about the series - the
    Ice Stone turns an Alolan Vulpix into an Alolan Ninetales whoever is asking - so what is
    filtered here is only PokeAPI's habit of naming a default form, and never which game has it.
    """
    known = {one.id for one in forms}
    variants = _all_variants(api, chains=chains, refresh=refresh)
    names = _name_of(variants, known)

    return [
        EvolutionRule(
            id=names[variant],
            **{
                "from": _target(
                    variant.from_species, variant.from_form, variant.from_fork, known
                )
            },
            to=_target(variant.to_species, variant.to_form, variant.to_fork, known),
            trigger=variant.trigger,
            conditions=list(variant.conditions),
        )
        for variant in variants
    ]


def _target(species: str, form: str | None, fork: bool, known: Container[str]) -> DexTarget:
    """One end of a rule, named as a form only where the form is one this project records.

    A real fork this project has no form for - a Generation 9 one, say, while the table stops
    earlier - leaves the rule about the species. That is the same answer the rule had before
    forms were read at all, which is what makes this safe to add underneath games already
    written. Which games may *use* such a rule is :func:`_target_here`'s stricter question.
    """
    found = _form_in(form, fork, known)

    return DexTarget(species=species, form=found if isinstance(found, str) else None)


def _cited(api: PokeApiClient, url: str) -> SourceCitation:
    """One chain's url, dated by the day the cache last fetched it."""
    return SourceCitation(source="pokeapi", url=url, retrieved_on=api.retrieved_on(url))


def evolution_encounters(
    api: PokeApiClient,
    *,
    game_id: str,
    version_group: str | Sequence[str],
    species: Sequence[str],
    forms: Sequence[Form] = (),
    all_forms: Sequence[Form] = (),
    excluded: Mapping[str, str] | None = None,
    refresh: bool = False,
) -> list[EvolutionAcquisition]:
    """Every evolution the given species can go through in one game.

    One record per evolution that works here, pointing at the rule it uses. A pair with several
    variants contributes the newest ones this game is old enough for, and nothing at all when
    every variant came later.

    **The newest, plural.** A later generation changing how something evolves replaces the older
    way - a Thunder Stone in Alola makes an Alolan Raichu and no longer a Kantonian one - so
    only the newest version group counts. But several ways can start *together*, and then they
    are different evolutions rather than one superseding another: a Rockruff becomes a Midday
    Lycanroc by day and a Midnight one by night, both in Sun and Moon, and Wormadam has worn
    three cloaks since Diamond and Pearl. Taking one of those and dropping the rest is what this
    did until the forms table could tell them apart, and it cost every one of them a record.

    **And "replaces" means what starts from the same form.** Ways are grouped by what is put in
    as well as what comes out, because Generation 7 added a second Rattata rather than changing
    the first: a Kantonian one still becomes a Kantonian Raticate and an Alolan one becomes an
    Alolan Raticate, and the source says so in as many words - the newer detail names
    ``rattata-alola`` as the form it requires. Three of the eighteen name no Alolan form at all,
    and those three really are replacements: a Pikachu, a Cubone and an Exeggcute are one
    Pokemon each and what the stone makes of them depends on where you are standing. Reading
    every Alolan detail as a replacement is what left the Let's Go pair unable to evolve a
    Kantonian Graveler, and Sun unable to evolve the Kantonian Rattata that Bank sends it.

    **The newest way this game actually has**, which is not always the newest way. If every
    variant at the top order is refused because it produces a form this game has not got, the
    order below it is tried, and so on down. The Let's Go pair is why: a Thunder Stone in Alola
    makes an Alolan Raichu, those two games are later than Alola and are Kanto, and taking the
    newest rule and stopping left them unable to evolve a Pikachu at all. Ten of Kanto's lines
    were missing the same way - Raichu, Ninetales, Persian, Sandslash, Dugtrio, Raticate, Golem,
    Muk, Marowak and Exeggutor, which is exactly the list of species Alola drew a second time.
    Nothing else in the dataset changes: a game old enough to be refused a form's rule is
    already too old for it to be usable.

    ``forms`` is this game's own table and ``all_forms`` the whole one, and the difference
    between them is what is refused: a detail naming a form some other game has is a way this
    game does not have, while one naming a form nobody records is PokeAPI spelling out a
    default. Rockruff's Dusk Lycanroc is the first and Gastrodon's West Sea is the second.

    ``version_group`` is usually one name and may be several, which Galar is the first to need.
    The source files Sword and Shield's two expansions as version groups of their own, and it
    puts real rules in them: Kubfu becomes an Urshifu in a tower on the Isle of Armor, and that
    detail is stamped ``the-isle-of-armor`` rather than ``sword-shield``. What counts is the
    newest of the names given, because this reads every way up to it.

    ``species`` is asked of both ends. Every game before the Let's Go pair holds everything up
    to its own National Dex number, so anything a species in the list evolves into is in the
    list too; these two hold a fixed 153 and nothing else, and their Eevee would otherwise have
    been recorded as producing an Espeon their boxes cannot hold.

    ``excluded`` names a species this source says can be evolved into here and which cannot be,
    with the reason - the same shape, and the same argument, as the one in :mod:`gifts`. A
    Melmetal is 400 Meltan Candy in Pokemon GO and the chain does not say where that happens.

    Whether the thing that evolves is itself obtainable is not asked here. That is the
    ``no-evolution-dead-ends`` check's job, and it can see the whole dataset where this can only
    see one game.
    """
    wanted = set(species)
    skip = excluded or {}
    here_forms = {one.id for one in forms}
    every_form = {one.id for one in all_forms} or here_forms
    chain_of = {name: api.evolution_chain(name, refresh=refresh) for name in species}
    variants = _all_variants(api, chains=sorted(set(chain_of.values())), refresh=refresh)
    names = _name_of(variants, every_form)
    groups = VersionGroups(api, refresh=refresh)
    wanted_groups = (version_group,) if isinstance(version_group, str) else tuple(version_group)
    here = max(groups.order_of(one) for one in wanted_groups)

    found: list[EvolutionAcquisition] = []

    for (pair, _source), choices in _by_way(variants, every_form).items():
        if pair[0] not in wanted:
            continue

        # And what it becomes. A game whose boxes hold a list rather than everything up to a
        # number can evolve something into what it cannot hold: the Let's Go pair's Eevee has
        # five stones' worth of evolutions and three of them are in its Pokedex.
        if pair[1] not in wanted:
            log.info(
                "%s does not evolve into %s in %s: that is not one of the species it holds",
                pair[0],
                pair[1],
                game_id,
            )
            continue

        not_here = skip.get(pair[1])
        if not_here is not None:
            log.info(
                "%s does not evolve into %s in %s: %s", pair[0], pair[1], game_id, not_here
            )
            continue

        usable = [
            variant
            for variant in choices
            if variant.order <= here
            and (not variant.only_in_its_own_game or variant.version_group in wanted_groups)
        ]
        if not usable:
            log.info(
                "%s does not evolve into %s in %s: every way of doing it came later",
                pair[0],
                pair[1],
                game_id,
            )
            continue

        # Newest first, and down a step whenever the whole of an order is refused for wanting a
        # form this game has not got. See the docstring: the Let's Go pair is the only game in
        # the dataset this reaches, and without it those two cannot evolve a Pikachu.
        for order in sorted({one.order for one in usable}, reverse=True):
            ways = _ways_at(
                [one for one in usable if one.order == order],
                api,
                game_id=game_id,
                here_forms=here_forms,
                every_form=every_form,
                names=names,
                chain=chain_of[pair[0]],
                skip=skip,
            )

            if ways:
                found.extend(ways)
                break

            log.info(
                "%s does not evolve into %s the newest way in %s; trying an older one",
                pair[0],
                pair[1],
                game_id,
            )

    return found


def _ways_at(
    variants: Sequence[_Variant],
    api: PokeApiClient,
    *,
    game_id: str,
    here_forms: Container[str],
    every_form: Container[str],
    names: Mapping[_Variant, str],
    chain: str,
    skip: Mapping[str, str],
) -> list[EvolutionAcquisition]:
    """Every way this game has at one version group's worth of rules, which is often none."""
    told_apart: set[str | None] = set()
    found: list[EvolutionAcquisition] = []

    for variant in variants:
        target = _target_here(variant, here_forms, every_form, game_id=game_id)
        if target is None:
            continue

        # A form the game says it cannot make this way. Refusing it here rather than before the
        # loop is what lets the order below be tried: a Thunder Stone in Kanto still makes a
        # Raichu, and what it makes is the one the Kanto games have always made.
        not_here = skip.get(target.form) if target.form else None
        if not_here is not None:
            log.info(
                "%s does not evolve into %s in %s: %s",
                variant.from_species,
                target.form,
                game_id,
                not_here,
            )
            continue

        # Two ways this game cannot tell apart are one way. It happens where a fork is real
        # and nothing in this dataset records it yet: Rockruff becomes a Dusk Lycanroc only
        # in Ultra Sun and Ultra Moon, and until those are built there is no
        # ``lycanroc-dusk`` to refuse it by - so it lands on the plain Lycanroc that Sun's
        # daytime evolution already produces. Keeping both would tell a Sun player to find
        # a Rockruff with Own Tempo and wait for dusk, which Sun cannot do at all.
        if target.form in told_apart:
            log.info(
                "%s evolves into %s in %s more than one way, and this game cannot tell them "
                "apart",
                variant.from_species,
                target.species,
                game_id,
            )
            continue

        told_apart.add(target.form)

        found.append(
            EvolutionAcquisition(
                game=game_id,
                target=target,
                rule=names[variant],
                source=(
                    bulbapedia(variant.page, retrieved_on=NOT_IN_THE_SOURCE_READ_ON)
                    if variant.page
                    else _cited(api, f"{BASE_URL}/evolution-chain/{chain}")
                ),
            )
        )

    return found


def _target_here(
    variant: _Variant,
    here: Container[str],
    every: Container[str],
    *,
    game_id: str,
) -> DexTarget | None:
    """What this evolution produces in this game, or nothing when it does not happen here.

    Both ends are asked. What it turns into has to be something this game holds, and so does
    what it turns *from*: only an Alolan Vulpix takes the Ice Stone, and a game with no Alolan
    Vulpix has no use for the rule however much it may like the stone.
    """
    ends = (
        (variant.from_form, variant.from_fork, "from"),
        (variant.to_form, variant.to_fork, "into"),
    )

    for name, fork, which in ends:
        found = _form_in(name, fork, every)

        if found is None:
            # The species, under whatever name the source spells it. Nothing to refuse.
            continue

        if found is _UNRECORDED or name not in here:
            log.info(
                "%s does not evolve %s %s in %s: that form is not in this game",
                variant.from_species,
                which,
                name,
                game_id,
            )
            return None

    produced = _form_in(variant.to_form, variant.to_fork, here)

    return DexTarget(
        species=variant.to_species,
        form=produced if isinstance(produced, str) else None,
    )


def _all_variants(
    api: PokeApiClient,
    *,
    chains: Sequence[str],
    refresh: bool,
) -> list[_Variant]:
    """Every variant in every chain given, in a fixed order so ids do not move between builds."""
    groups = VersionGroups(api, refresh=refresh)
    names = EnglishNames(api, refresh=refresh)
    varieties = Varieties(api, refresh=refresh)
    variants: list[_Variant] = []

    for chain_id in sorted(set(chains)):
        try:
            chain = api.resource(f"evolution-chain/{chain_id}", refresh=refresh)
        except httpx.HTTPError as error:
            # A species whose chain cannot be read loses its evolutions, which the dead-end
            # check will notice. Throwing away a whole build over one of them would not.
            log.warning("no evolution chain %s: %s", chain_id, error)
            continue

        _walk(
            chain.get("chain"),
            groups=groups,
            names=names,
            varieties=varieties,
            into=variants,
        )

    variants.extend(
        _Variant(
            from_species=one.from_species,
            to_species=one.to_species,
            version_group=one.version_group,
            order=groups.order_of(one.version_group),
            trigger=one.trigger,
            conditions=one.conditions,
            page=one.page,
            only_in_its_own_game=True,
        )
        for one in NOT_IN_THE_SOURCE
        if one.from_species in _species_in(variants)
    )

    # Two details a player could not tell apart are one way of evolving, however many times the
    # source lists them. Left in, they would each want the same id.
    seen: dict[_Variant, None] = dict.fromkeys(variants)

    return sorted(seen, key=lambda one: (one.from_species, one.to_species, one.order))


def _walk(
    node: dict | None,
    *,
    groups: VersionGroups,
    names: EnglishNames,
    varieties: Varieties,
    into: list,
) -> None:
    if not node:
        return

    parent = node["species"]["name"]

    for child in node.get("evolves_to", []):
        for detail in child.get("evolution_details", []):
            into.append(
                _variant(
                    from_species=parent,
                    to_species=child["species"]["name"],
                    detail=detail,
                    groups=groups,
                    names=names,
                    varieties=varieties,
                )
            )

        _walk(child, groups=groups, names=names, varieties=varieties, into=into)


def _named(field_value: dict | None) -> str | None:
    """What one of PokeAPI's two form fields said, if it said anything."""
    return (field_value or {}).get("name")


#: A real fork in the chain that nothing in this project records, which is not a way to get
#: anything here and is not the species either.
_UNRECORDED = object()


def _species_in(variants: Sequence[_Variant]) -> set[str]:
    """Every species the chains just read mention, so a hand-written way is only added beside
    the chain it belongs to. Without it, asking about one game's species would pull in ways
    about Pokemon that game has never heard of."""
    return {one.from_species for one in variants} | {one.to_species for one in variants}


def _form_in(name: str | None, fork: bool, known: Container[str]) -> str | object | None:
    """Which form a detail names, as far as ``known`` is concerned. Three answers.

    ``None`` is the species: either the detail said nothing, or it named what PokeAPI calls the
    default form of the only Pokemon there is - ``gastrodon-west``, ``lycanroc-midday``,
    ``burmy-plant``, ``flabebe-red``. Those are spellings, not choices.

    A form id is one this project records, whether it is a second Pokemon (``lycanroc-midnight``)
    or a form of the one (``gastrodon-east``). PokeAPI keeps those two in different places and
    the difference does not matter here.

    :data:`_UNRECORDED` is the third, and it only happens to a real second Pokemon: a fork this
    project has no form for. Rockruff becomes a Dusk Lycanroc off a Rockruff with Own Tempo,
    both of which belong to games this dataset has not built - and neither one may be silently
    read as "a Rockruff becomes a Lycanroc", which is a thing Sun can do and this is not.
    """
    if name is None:
        return None

    if name in known:
        return name

    return _UNRECORDED if fork else None


def _variant(
    *,
    from_species: str,
    to_species: str,
    detail: dict,
    groups: VersionGroups,
    names: EnglishNames,
    varieties: Varieties,
) -> _Variant:
    trigger_slug = detail.get("trigger", {}).get("name", "other")
    group = (detail.get("version_group") or {}).get("name")

    return _Variant(
        from_species=from_species,
        to_species=to_species,
        from_form=_named(detail.get("required_pokemon_form")),
        to_form=_named(detail.get("evolved_pokemon_form")),
        from_fork=varieties.has(from_species, _named(detail.get("required_pokemon_form"))),
        to_fork=varieties.has(to_species, _named(detail.get("evolved_pokemon_form"))),
        # A detail with no version group is one PokeAPI cannot place; treating it as the
        # oldest keeps it usable everywhere rather than nowhere.
        version_group=group or "unknown",
        order=groups.order_of(group) if group else 0,
        trigger=TRIGGERS.get(trigger_slug, EvolutionTrigger.OTHER),
        conditions=tuple(
            _conditions(
                detail,
                trigger_slug=trigger_slug,
                names=names,
                what=f"{from_species} -> {to_species}",
            )
        ),
    )


def _conditions(
    detail: dict,
    *,
    trigger_slug: str,
    names: EnglishNames,
    what: str,
) -> list[EvolutionCondition]:
    """Everything on top of the trigger, in one fixed order so two builds agree."""
    conditions: list[EvolutionCondition] = []

    if trigger_slug not in TRIGGERS:
        conditions.append(OtherCondition(description=_other_trigger(trigger_slug, what)))

    if (level := detail.get("min_level")) is not None:
        conditions.append(MinimumLevelCondition(level=level))

    if (happiness := detail.get("min_happiness")) is not None:
        conditions.append(FriendshipCondition(minimum=happiness))

    if item := detail.get("item"):
        conditions.append(UsedItemCondition(item=names.of("item", item["name"])))

    if held := detail.get("held_item"):
        conditions.append(HeldItemCondition(item=names.of("item", held["name"])))

    if move := detail.get("known_move"):
        conditions.append(KnownMoveCondition(move=names.of("move", move["name"])))

    if place := detail.get("location"):
        conditions.append(LocationCondition(location=names.of("location", place["name"])))

    if (gender := detail.get("gender")) is not None:
        conditions.append(GenderCondition(gender=GENDERS.get(gender, str(gender))))

    if time_of_day := detail.get("time_of_day"):
        conditions.append(TimeOfDayCondition(time_of_day=time_of_day))

    if partner := detail.get("trade_species"):
        conditions.append(TradePartnerCondition(species=partner["name"]))

    conditions.extend(_prose(detail, names=names, what=what))

    return conditions


def _prose(detail: dict, *, names: EnglishNames, what: str) -> list[EvolutionCondition]:
    """The requirements this project has no type for, said in words.

    ``other`` is the schema's escape hatch, and using it is how a game gets finished without
    first growing a condition type for every gimmick. A requirement that turns up in a second
    game is a candidate for promotion to a type of its own.
    """
    said: list[EvolutionCondition] = []

    if (beauty := detail.get("min_beauty")) is not None:
        said.append(OtherCondition(description=f"with Beauty {beauty} or higher"))

    # Generation 9's three, and the first of them is the reason they are here. Pawmo's only
    # requirement is a thousand steps walked beside the player, and the source carries it as
    # `min_steps` and nothing else - so before this the rule came out with an empty condition
    # list and told a player that a Pawmo levels up into a Pawmot, which it does not.
    if (steps := detail.get("min_steps")) is not None:
        said.append(
            OtherCondition(
                description=f"after walking {steps:,} steps with it out of its ball"
            )
        )

    # Said as the move and the count rather than as another sentence starting "after using",
    # because the trigger above has already said that much and a record that says it twice
    # reads like a stutter.
    if used := detail.get("used_move"):
        times = detail.get("min_move_count")
        counted = f", {times} times" if times else ""
        said.append(OtherCondition(description=f"{pretty(used['name'])}{counted}"))

    if (affection := detail.get("min_affection")) is not None:
        said.append(OtherCondition(description=f"with affection {affection} or higher"))

    if move_type := detail.get("known_move_type"):
        said.append(OtherCondition(description=f"knowing a {pretty(move_type['name'])} move"))

    if party := detail.get("party_species"):
        said.append(
            OtherCondition(
                description=f"with {names.of('pokemon-species', party['name'])} in the party"
            )
        )

    if party_type := detail.get("party_type"):
        said.append(
            OtherCondition(description=f"with a {pretty(party_type['name'])} type in the party")
        )

    if (stats := detail.get("relative_physical_stats")) is not None:
        said.append(OtherCondition(description=PHYSICAL_STATS.get(stats, "with the right stats")))

    if region := detail.get("region"):
        said.append(OtherCondition(description=f"in {pretty(region['name'])}"))

    for key, words in FLAG_CONDITIONS.items():
        if detail.get(key):
            said.append(OtherCondition(description=words))

    if expression := detail.get("condition_expression"):
        # The expression itself is machine arithmetic on a hidden value - "PID 16 >> 10 % 4 <="
        # - which no player can act on. The odds are the part that is worth saying.
        if (chance := expression.get("percentage_chance")) is not None:
            said.append(OtherCondition(description=f"a {chance}% chance"))
        else:
            log.info("%s has an unreadable condition: %s", what, expression.get("expression"))

    for key, value in detail.items():
        if key in IGNORED_DETAILS or key in FLAG_CONDITIONS or not value:
            continue

        if key not in _HANDLED:
            log.info("%s has an unmapped evolution detail: %s = %s", what, key, value)

    return said


#: Every detail key the two condition builders above read. Anything else is logged once so a
#: new PokeAPI field is noticed rather than silently dropped.
_HANDLED = frozenset(
    {
        "min_level",
        "min_happiness",
        "item",
        "held_item",
        "known_move",
        "location",
        "gender",
        "time_of_day",
        "trade_species",
        "min_beauty",
        "min_affection",
        "known_move_type",
        "party_species",
        "party_type",
        "relative_physical_stats",
        "region",
        "condition_expression",
        "min_steps",
        "used_move",
        "min_move_count",
    }
)


def _other_trigger(slug: str, what: str) -> str:
    if slug in OTHER_TRIGGERS:
        return OTHER_TRIGGERS[slug]

    log.info("%s evolves by %s, which has no wording of its own yet", what, slug)
    return pretty(slug).lower()


def _by_pair(variants: Sequence[_Variant]) -> dict[tuple[str, str], list[_Variant]]:
    """Every variant of one pair of species together, which is what an id is unique within."""
    grouped: dict[tuple[str, str], list[_Variant]] = {}
    for variant in variants:
        grouped.setdefault(variant.pair, []).append(variant)

    return grouped


def _by_way(
    variants: Sequence[_Variant],
    every_form: Container[str],
) -> dict[tuple[tuple[str, str], str | object | None], list[_Variant]]:
    """The variants grouped by what a way starts from as well as what it ends at.

    The source form is read the way :func:`_target_here` reads it, so that PokeAPI spelling a
    default out - ``pikachu`` as the form a Pikachu must be in - groups with saying nothing.
    What separates a group is a form something records: ``rattata-alola`` is one and the plain
    Rattata is not, which is the whole of the difference between a second Pokemon and a rule
    that changed.
    """
    grouped: dict[tuple[tuple[str, str], str | object | None], list[_Variant]] = {}

    for variant in variants:
        source = _form_in(variant.from_form, variant.from_fork, every_form)
        grouped.setdefault((variant.pair, source), []).append(variant)

    return grouped


def _name_of(variants: Sequence[_Variant], known: Container[str] = frozenset()) -> dict[
    _Variant, str
]:
    """A stable id per variant.

    ``kadabra-to-alakazam`` while there is one way to do it, which is nearly always. A pair with
    several variants names the version group each one started in - ``feebas-to-milotic-ruby-
    sapphire`` beside ``feebas-to-milotic-black-white`` - rather than one of them holding the
    plain id and the rest looking like afterthoughts.

    Where the variants differ by what they produce rather than by when, the form is what tells
    them apart: ``rockruff-to-lycanroc-midnight`` beside ``rockruff-to-lycanroc``. Both started
    in the same version group, so naming them after it would have collided and numbered one of
    them, and a numbered id says nothing about which way of evolving it is.

    Two variants that still collide are numbered. An id has to be unique before it has to be
    pretty: it is what a game file points at.
    """
    grouped = _by_pair(variants)
    names: dict[_Variant, str] = {}
    taken: set[str] = set()

    for (from_species, to_species), choices in grouped.items():
        for variant in choices:
            named = _named_as(variant, known, to_species)
            base = f"{from_species}-to-{named}"
            same = [one for one in choices if _named_as(one, known, to_species) == named]

            wanted = base if len(same) == 1 else f"{base}-{variant.version_group}"
            names[variant] = _free(wanted, taken)
            taken.add(names[variant])

    return names


def _named_as(variant: _Variant, known: Container[str], to_species: str) -> str:
    """What an id calls the thing this variant produces: its form, or else its species."""
    found = _form_in(variant.to_form, variant.to_fork, known)

    return found if isinstance(found, str) else to_species


def _free(wanted: str, taken: set[str]) -> str:
    if wanted not in taken:
        return wanted

    return next(f"{wanted}-{index}" for index in range(2, 100) if f"{wanted}-{index}" not in taken)
