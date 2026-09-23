"""What one game can actually reach, and what that means for the entries it cannot.

Every other question in this pipeline is asked of a record: is there a way to get this, and does
it have a place, a level, a source. This one is asked of a chain of them. A game records "evolve
a Lombre" for its Ludicolo whether or not it has ever seen a Lotad, and the record is true - the
evolution does work, on a Lombre somebody brings in - while the entry is as unfillable as the
Lotad's is.

That gap was in sixteen games at once, because a version exclusive is worked out from encounter
tables and nobody walked the evolutions afterwards. Red says Sandshrew is Blue's and says nothing
about Sandslash; Ruby says Lotad is Sapphire's and says nothing about Ludicolo; Gold and Silver
leave twelve entries each unexplained. The answer is the same in every case and it is the base's
own: trade one in.

So a species is *reachable* in a game when the game puts one in a player's hands - caught,
handed over, traded for - or when something reachable evolves or hatches into it. Anything the
dex lists that is not reachable is an entry this game cannot fill, and it is owed a reason.

:mod:`rules` asks the same question the other way round, as ``unreachable-entries-say-so``, so
that a game which grows a new exclusive and forgets its evolutions is told about it.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

from .models import AcquisitionMethod, DexEntry, EvolutionRule, GameData

#: The record kinds that put a Pokemon in a player's hands with nothing to have first.
#:
#: The same three :mod:`breeding` counts, and for the same reason. A wild slot that does not
#: count - the Friend Safari - is not one of them, which is checked on the record rather than
#: here.
CAUGHT = frozenset({"wild", "gift", "trade"})


def reachable_in(data: GameData, *, rules: Mapping[str, EvolutionRule]) -> set[str]:
    """Every species this game can end up with, starting from what it hands over itself.

    A fixed point rather than one pass: a Ludicolo needs a Lombre, which needs a Lotad, and the
    order the records happen to be in says nothing about the order they depend on each other.
    """
    reached = {
        method.target.species
        for method in data.acquisition_methods
        if method.kind in CAUGHT and getattr(method, "does_not_count", None) is None
    }
    steps = list(_steps(data.acquisition_methods, rules=rules))

    growing = True
    while growing:
        growing = False
        for parents, child in steps:
            if child not in reached and any(one in reached for one in parents):
                reached.add(child)
                growing = True

    return reached


def spread_unobtainable(data: GameData, *, rules: Sequence[EvolutionRule]) -> GameData:
    """Give an entry the reason its own line already carries, where it has none of its own.

    Only downhill from something that was written down: if nothing in an entry's ancestry is
    explained, nothing is invented here and ``every-entry-has-a-method`` is left to say so.
    """
    by_id = {rule.id: rule for rule in rules}
    reached = reachable_in(data, rules=by_id)
    explained = {
        entry.target.species: entry.unobtainable_reason
        for entry in data.dex_entries
        if entry.unobtainable_reason
    }
    parents = parents_in(data.acquisition_methods, rules=by_id)

    entries = [
        _with_reason(entry, _inherited(entry.target.species, explained, parents))
        if entry.target.species not in reached and not entry.unobtainable_reason
        else entry
        for entry in data.dex_entries
    ]

    return data.model_copy(update={"dex_entries": entries})


def _with_reason(entry: DexEntry, reason: str | None) -> DexEntry:
    return entry if reason is None else entry.model_copy(update={"unobtainable_reason": reason})


def _inherited(
    species: str,
    explained: Mapping[str, str],
    parents: Mapping[str, set[str]],
) -> str | None:
    """The nearest reason above this species in this game's own evolution records."""
    seen = {species}
    edge = set(parents.get(species, ()))

    while edge:
        for one in sorted(edge):
            if one in explained:
                return explained[one]

        seen |= edge
        edge = {
            older for one in edge for older in parents.get(one, ()) if older not in seen
        }

    return None


def _steps(
    methods: Iterable[AcquisitionMethod],
    *,
    rules: Mapping[str, EvolutionRule],
) -> Iterable[tuple[set[str], str]]:
    """What each record needs first, and what it produces: (any of these, this)."""
    for method in methods:
        if method.kind == "evolution":
            rule = rules.get(method.rule)
            if rule is not None:
                yield {rule.from_.species}, method.target.species
        elif method.kind == "breeding":
            yield {parent.species for parent in method.parents}, method.target.species


def parents_in(
    methods: Iterable[AcquisitionMethod],
    *,
    rules: Mapping[str, EvolutionRule],
) -> dict[str, set[str]]:
    """What this game says each species comes from, for walking back up a line.

    Public because :mod:`rules` asks the same question when it checks that an entry nothing here
    can reach says so.
    """
    found: dict[str, set[str]] = {}

    for older, child in _steps(methods, rules=rules):
        found.setdefault(child, set()).update(older)

    return found
