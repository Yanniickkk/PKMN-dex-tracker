"""Babies from the day care.

Pichu, Igglybuff and Azurill are in Emerald's dex and there is no way to meet one: they hatch
from an egg the day care hands over, and nothing else in the game produces them. That is not a
gift, not a wild slot, not an evolution and not a trade, so it is its own kind rather than one
of the four bent to fit.

There are two ways to arrive at such a table, and this module carries both.

A game can write one out, which is what the first twenty did. Which parent lays which baby is a
fact about a generation more than about a game - the incense a Generation IV parent has to hold
is the sort of thing that changes - so the table lives in the game's own file and this module
only turns it into records.

Or it can be worked out, which is what :func:`day_care_eggs` does and what Kalos needed. Unova's
list is twenty-seven names and X's is fifty-four, and every one of them is the same three
questions asked of PokeAPI: what does this grow into, can this game get to any of those, and is
it the bottom of its chain. Typing fifty-four answers to questions a source already answers is
how a list drifts from the game it describes - and the two exceptions a hand-written table
exists for turn out to be in the source as well. The incense is ``baby_trigger_item`` on the
chain; a Beldum needing a Ditto is ``gender_rate`` of -1 on the species.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass

from . import conditions
from .models import BreedingAcquisition, DexTarget, SourceCitation
from .places import pretty
from .pokeapi import PokeApiClient


@dataclass(frozen=True)
class EggFrom:
    """What has to be in the day care for one baby to turn up."""

    #: Any one of these works. A Pichu hatches from a Pikachu or from a Raichu, and naming only
    #: the first would make the other look like a way that does not exist.
    parents: Sequence[str]
    #: What else has to be true - the incense a Generation IV parent has to hold, say.
    requirement: str | None = None


def breeding_encounters(
    *,
    game_id: str,
    day_care: str,
    eggs: Mapping[str, EggFrom],
    citation: SourceCitation,
) -> list[BreedingAcquisition]:
    """One record per baby, in the order the game's table lists them."""
    return [
        BreedingAcquisition(
            game=game_id,
            target=DexTarget(species=baby),
            parents=[DexTarget(species=parent) for parent in egg.parents],
            location=day_care,
            requirement=egg.requirement,
            source=citation,
        )
        for baby, egg in eggs.items()
    ]


#: What a genderless parent needs, which is the only other thing in the day care.
DITTO = "Genderless, so the other half of the pairing has to be a Ditto"


def day_care_eggs(
    api: PokeApiClient,
    *,
    chains: Mapping[str, str],
    caught: Collection[str],
    evolved: Collection[str],
    refresh: bool = False,
) -> dict[str, EggFrom]:
    """Every species a game can only get out of the day care, and what has to be left there.

    ``chains`` is species id -> evolution chain id for the whole living dex, which the shared
    species table already holds. ``caught`` is what the game produces without help - anything
    wild, handed over or traded for - and ``evolved`` is everything it has an evolution record
    for. The two are not one set: a game can know that a Bayleef becomes a Meganium and have no
    Chikorita anywhere, and treating that as "the game has a Bayleef" would offer a player an
    egg from a parent they cannot get. Fifty-six of X's evolution records are exactly that.

    What comes back is only the bottom of a chain. An egg hatches into the first stage, so a
    Silcoon that a game happens not to produce is not something the day care can be asked for -
    breeding its Beautifly gives a Wurmple.
    """
    trees = {
        chain: api.resource(f"evolution-chain/{chain}", refresh=refresh)
        for chain in sorted(set(chains.values()))
    }
    grows_into = {chain: _descendants(tree["chain"]) for chain, tree in trees.items()}
    roots = {chain: tree["chain"]["species"]["name"] for chain, tree in trees.items()}

    reachable = _reachable(caught, evolved, grows_into.values())

    eggs: dict[str, EggFrom] = {}
    for name, chain in chains.items():
        if name in reachable or roots[chain] != name:
            continue

        parents = tuple(one for one in sorted(grows_into[chain].get(name, ())) if one in reachable)
        if not parents:
            continue

        eggs[name] = EggFrom(
            parents=parents,
            requirement=_requirement(api, species=name, chain=trees[chain], refresh=refresh),
        )

    return eggs


def _descendants(node: dict) -> dict[str, set[str]]:
    """Every species each stage of a chain grows into, however many steps down."""
    below: dict[str, set[str]] = {}

    def walk(one: dict) -> set[str]:
        under: set[str] = set()
        for nxt in one.get("evolves_to", []):
            under.add(nxt["species"]["name"])
            under |= walk(nxt)

        below[one["species"]["name"]] = under
        return under

    walk(node)
    return below


def _reachable(
    caught: Collection[str],
    evolved: Collection[str],
    chains: Collection[Mapping[str, set[str]]],
) -> set[str]:
    """What a game can get to on its own: what it catches, and what those grow into here."""
    reached = set(caught)
    growing = True

    while growing:
        growing = False
        for below in chains:
            for name, under in below.items():
                if name not in reached:
                    continue

                for nxt in under:
                    if nxt in evolved and nxt not in reached:
                        reached.add(nxt)
                        growing = True

    return reached


def _requirement(
    api: PokeApiClient, *, species: str, chain: dict, refresh: bool = False
) -> str | None:
    """The two things a pair in the day care can need beyond being a pair.

    Both come from the source rather than from a list somebody keeps: an incense is what the
    chain says has to be held for the baby rather than the adult, and a species with no sex at
    all is one PokeAPI gives a gender rate of -1.
    """
    item = (chain.get("baby_trigger_item") or {}).get("name")
    incense = f"A parent has to hold a {pretty(item)}" if item else None

    raw = api.resource(f"pokemon-species/{species}", refresh=refresh)
    genderless = DITTO if raw.get("gender_rate") == -1 else None

    return conditions.joined(incense, genderless)
