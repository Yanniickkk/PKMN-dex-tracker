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
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date

import httpx

from .models import (
    DexTarget,
    EvolutionAcquisition,
    EvolutionCondition,
    EvolutionRule,
    EvolutionTrigger,
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

#: Details about forms, which the forms table does not carry yet, and internals a player has no
#: way to act on. Skipped without a word, because logging "eevee must be an eevee" eight times
#: per chain buries the details that do matter.
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
class _Variant:
    """One way of evolving, and the version group it started in."""

    from_species: str
    to_species: str
    version_group: str
    order: int
    trigger: EvolutionTrigger
    conditions: tuple[EvolutionCondition, ...]

    @property
    def pair(self) -> tuple[str, str]:
        return (self.from_species, self.to_species)


def evolution_rules(
    api: PokeApiClient,
    *,
    chains: Sequence[str],
    refresh: bool = False,
) -> list[EvolutionRule]:
    """Every rule in the chains given, across every generation.

    The table is shared, so it holds each variant rather than only the current one: a game file
    points at the variant it can use, and the two Feebas rules sitting side by side are what
    makes "trade holding a Prism Scale" visible as something later games do rather than as
    something Emerald forgot.
    """
    variants = _all_variants(api, chains=chains, refresh=refresh)
    names = _name_of(variants)

    return [
        EvolutionRule(
            id=names[variant],
            **{"from": DexTarget(species=variant.from_species)},
            to=DexTarget(species=variant.to_species),
            trigger=variant.trigger,
            conditions=list(variant.conditions),
        )
        for variant in variants
    ]


def evolution_encounters(
    api: PokeApiClient,
    *,
    game_id: str,
    version_group: str,
    species: Sequence[str],
    retrieved_on: date,
    refresh: bool = False,
) -> list[EvolutionAcquisition]:
    """Every evolution the given species can go through in one game.

    One record per evolution that works here, pointing at the rule it uses. A pair with several
    variants contributes the newest one this game is old enough for, and nothing at all when
    every variant came later.

    Whether the thing that evolves is itself obtainable is not asked here. That is the
    ``no-evolution-dead-ends`` check's job, and it can see the whole dataset where this can only
    see one game.
    """
    wanted = set(species)
    chain_of = {name: api.evolution_chain(name, refresh=refresh) for name in species}
    variants = _all_variants(api, chains=sorted(set(chain_of.values())), refresh=refresh)
    names = _name_of(variants)
    groups = VersionGroups(api, refresh=refresh)
    here = groups.order_of(version_group)

    found: list[EvolutionAcquisition] = []

    for pair, choices in _by_pair(variants).items():
        if pair[0] not in wanted:
            continue

        usable = [variant for variant in choices if variant.order <= here]
        if not usable:
            log.info(
                "%s does not evolve into %s in %s: every way of doing it came later",
                pair[0],
                pair[1],
                game_id,
            )
            continue

        # The newest way that exists yet. A later generation changing how something evolves
        # replaces the older way rather than adding to it.
        variant = max(usable, key=lambda one: one.order)

        found.append(
            EvolutionAcquisition(
                game=game_id,
                target=DexTarget(species=variant.to_species),
                rule=names[variant],
                source=SourceCitation(
                    source="pokeapi",
                    url=f"{BASE_URL}/evolution-chain/{chain_of[pair[0]]}",
                    retrieved_on=retrieved_on,
                ),
            )
        )

    return found


def _all_variants(
    api: PokeApiClient,
    *,
    chains: Sequence[str],
    refresh: bool,
) -> list[_Variant]:
    """Every variant in every chain given, in a fixed order so ids do not move between builds."""
    groups = VersionGroups(api, refresh=refresh)
    names = EnglishNames(api, refresh=refresh)
    variants: list[_Variant] = []

    for chain_id in sorted(set(chains)):
        try:
            chain = api.resource(f"evolution-chain/{chain_id}", refresh=refresh)
        except httpx.HTTPError as error:
            # A species whose chain cannot be read loses its evolutions, which the dead-end
            # check will notice. Throwing away a whole build over one of them would not.
            log.warning("no evolution chain %s: %s", chain_id, error)
            continue

        _walk(chain.get("chain"), groups=groups, names=names, into=variants)

    # Two details a player could not tell apart are one way of evolving, however many times the
    # source lists them. Left in, they would each want the same id.
    seen: dict[_Variant, None] = dict.fromkeys(variants)

    return sorted(seen, key=lambda one: (one.from_species, one.to_species, one.order))


def _walk(node: dict | None, *, groups: VersionGroups, names: EnglishNames, into: list) -> None:
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
                )
            )

        _walk(child, groups=groups, names=names, into=into)


def _variant(
    *,
    from_species: str,
    to_species: str,
    detail: dict,
    groups: VersionGroups,
    names: EnglishNames,
) -> _Variant:
    trigger_slug = detail.get("trigger", {}).get("name", "other")
    group = (detail.get("version_group") or {}).get("name")

    return _Variant(
        from_species=from_species,
        to_species=to_species,
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
    }
)


def _other_trigger(slug: str, what: str) -> str:
    if slug in OTHER_TRIGGERS:
        return OTHER_TRIGGERS[slug]

    log.info("%s evolves by %s, which has no wording of its own yet", what, slug)
    return pretty(slug).lower()


def _by_pair(variants: Sequence[_Variant]) -> dict[tuple[str, str], list[_Variant]]:
    grouped: dict[tuple[str, str], list[_Variant]] = {}
    for variant in variants:
        grouped.setdefault(variant.pair, []).append(variant)

    return grouped


def _name_of(variants: Sequence[_Variant]) -> dict[_Variant, str]:
    """A stable id per variant.

    ``kadabra-to-alakazam`` while there is one way to do it, which is nearly always. A pair with
    several variants names the version group each one started in - ``feebas-to-milotic-ruby-
    sapphire`` beside ``feebas-to-milotic-black-white`` - rather than one of them holding the
    plain id and the rest looking like afterthoughts.

    Two variants that started in the same version group would collide, so the second and any
    after it are numbered. An id has to be unique before it has to be pretty: it is what a game
    file points at.
    """
    grouped = _by_pair(variants)
    names: dict[_Variant, str] = {}
    taken: set[str] = set()

    for (from_species, to_species), choices in grouped.items():
        base = f"{from_species}-to-{to_species}"

        for variant in choices:
            wanted = base if len(choices) == 1 else f"{base}-{variant.version_group}"
            names[variant] = _free(wanted, taken)
            taken.add(names[variant])

    return names


def _free(wanted: str, taken: set[str]) -> str:
    if wanted not in taken:
        return wanted

    return next(f"{wanted}-{index}" for index in range(2, 100) if f"{wanted}-{index}" not in taken)
