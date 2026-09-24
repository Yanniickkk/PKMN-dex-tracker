"""The checks a build has to pass.

A note on what "has a method" means, because it decides most of this file. Acquisition methods
are recorded per game, but a living dex is filled by transferring as much as by catching: most
of Platinum's National Dex has no Sinnoh encounter at all. So an entry counts as accounted for
when *some* game in the dataset can produce it. Whether that is the game you are playing is the
difference between ``full`` and ``partial`` in the coverage report, not the difference between
valid and invalid.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from .models import DexTarget, GameRelease
from .reach import parents_in, reachable_in
from .validate import Dataset, Finding, GameCoverage, Severity


def _target_key(target: DexTarget) -> tuple[str, str | None]:
    return (target.species, target.form)


def _is_node(game) -> bool:
    """Whether this entry in the dataset is a transfer node rather than a game.

    Pokemon Bank and HOME are in the dataset because a route has to point at something, and
    almost nothing below has a question to ask about them: there is no dex to fill, no cover to
    put in a picker, and nothing was ever caught there. The checks that would otherwise report
    an empty game every time ask this first.
    """
    return game.game.release is GameRelease.SERVICE


def _counts(method) -> bool:
    """Whether a recorded way is one a player can be told to go and use.

    A record can be true and still not answer "can I get one here". Kalos's Friend Safari is
    eighteen areas of ordinary encounter tables that want another person's 3DS friend code, and
    a third of what they hold is behind a network switched off in April 2024. The rows are kept,
    because they are real and a player with the right friend can use them; what they are kept
    out of is every count and every question below. The record says why in its own words.
    """
    return getattr(method, "does_not_count", None) is None


def _obtainable_anywhere(dataset: Dataset) -> set[tuple[str, str | None]]:
    """Every target some game in the dataset can produce."""
    return {
        _target_key(method.target)
        for game in dataset.games
        for method in game.acquisition_methods
        if _counts(method)
    }


def _obtainable_in(dataset: Dataset, game_id: str) -> set[tuple[str, str | None]]:
    game = dataset.game(game_id)
    if game is None:
        return set()

    return {_target_key(method.target) for method in game.acquisition_methods if _counts(method)}


def _living_dex(dataset: Dataset, game) -> list[str]:
    """Every species this game asks a player to fill, in National Dex order.

    The same list :meth:`~.games.BuildContext.living_dex` hands the builders, worked out here
    from what was written rather than passed along: a rule reads the dataset and nothing else.
    """
    reach = game.game.national_dex_through
    if reach is None:
        return [entry.target.species for entry in game.dex_entries]

    return [
        one.id
        for one in sorted(dataset.species, key=lambda one: one.national_dex_number)
        if one.national_dex_number <= reach
    ]


def _reasons_in(game) -> set[str]:
    """The species this game's own dex says cannot be filled here, by name."""
    return {
        entry.target.species for entry in game.dex_entries if entry.unobtainable_reason is not None
    }


def _listed_in_any_dex(dataset: Dataset) -> set[tuple[str, str | None]]:
    """Every target some game's own Pokedex asks for.

    The line between "this dataset has a hole" and "this dataset does not cover that yet". Ruby
    can evolve a Chikorita into a Bayleef and nothing here produces a Chikorita - because Gold
    and Silver are not built. No game's dex lists one either, and that is the difference between
    a fault and a generation nobody has got to.
    """
    return {_target_key(entry.target) for game in dataset.games for entry in game.dex_entries}


def _not_covered_yet(rule_name: str, game_id: str, kind: str, species: list[str]) -> Finding:
    """One warning for every dead end that leads out of what the dataset covers.

    Aggregated the way a game with no encounters is: seventeen findings that all say "Generation
    2 is not built yet" say it once between them, and burying the real faults under them is how
    a report stops being read.
    """
    named = ", ".join(sorted(species)[:5])
    more = f" and {len(species) - 5} more" if len(species) > 5 else ""

    return Finding(
        rule=rule_name,
        severity=Severity.WARNING,
        game=game_id,
        message=(
            f"{len(species)} thing(s) here are only obtainable by {kind} something no game in "
            f"the dataset lists yet, so the generation they come from has not been built: "
            f"{named}{more}"
        ),
    )


def _no_way_to_the_form(rule_name: str, game_id: str, kind: str, forms: list[str]) -> Finding:
    """One warning for a dead end that is a form rather than a generation nobody has built.

    Split off because the sentence above was telling a lie about these. A form is never a dex
    entry - dex entries are species - so a form's earlier stage is never "listed in a dex", and
    it fell into the bucket meant for a species from a generation that has not been written.
    Ultra Sun said "the generation they come from has not been built" about its own generation.

    What is actually true is narrower and worth saying: a Dusk Lycanroc comes from a Rockruff
    with Own Tempo, that Rockruff was a serial code handed to buyers over the winter of 2017,
    and **a form has nowhere to say so**. An ``unobtainable_reason`` lives on a dex entry, and
    the form table has no field for one. Until it does, this is the report.
    """
    named = ", ".join(sorted(forms))

    return Finding(
        rule=rule_name,
        severity=Severity.WARNING,
        game=game_id,
        message=(
            f"{len(forms)} thing(s) here are only obtainable by {kind} a form nothing in the "
            f"dataset produces, and a form has no dex entry to carry a reason on: {named}"
        ),
    )


def _explained_in(game) -> set[tuple[str, str | None]]:
    """Every entry this game's dex says cannot be filled here, and why.

    Not the same as "no data". Someone looked at Meditite, found that Emerald does not have it,
    and wrote down that it comes from a Ruby or Sapphire cartridge. That is an answer, and the
    rules below treat it as one.
    """
    return {
        _target_key(entry.target)
        for entry in game.dex_entries
        if entry.unobtainable_reason is not None
    }


class EveryEntryHasAMethod:
    """A dex entry nothing can produce is either a hole in the data or a stated fact.

    A game that brought no methods of its own is reported once rather than once per entry: that
    is a game whose encounters have not been gathered yet, and two hundred identical errors say
    the same thing as one while burying everything else in the report. The build fails either
    way, because the game is not finished either way.

    "No methods of its own" is the whole test. It used to also ask that not one entry was
    explained anywhere, which held for Emerald - the first game this met - because nothing else
    in the dataset produced a Hoenn species. The Kanto dex broke it: a third of those 151 are
    caught in Hoenn too, so the pair fell past the guard and reported a hundred and change
    separate faults for the one fact that their encounters were not gathered yet.

    Red broke the other half of it. Every one of its 151 entries is caught in some later game,
    so nothing was missing from the *dataset* and the rule had nothing to say - about a game
    that brought no encounters at all. A game with a dex and no way to fill any of it is
    unfinished whatever else covers its species, and step 8 reads "validation green" as proof
    that it is finished, so the check comes before the one about what is missing.
    """

    name = "every-entry-has-a-method"

    def check(self, dataset: Dataset) -> Iterator[Finding]:
        obtainable = _obtainable_anywhere(dataset)

        for game in dataset.games:
            needed = [entry for entry in game.dex_entries if entry.unobtainable_reason is None]
            missing = [entry for entry in needed if _target_key(entry.target) not in obtainable]

            # The game brought no methods of its own: it has not been worked on yet rather than
            # having gaps. What other games happen to cover does not change that.
            if game.dex_entries and not game.acquisition_methods:
                elsewhere = len(needed) - len(missing)
                yield Finding(
                    rule=self.name,
                    severity=Severity.ERROR,
                    game=game.game.id,
                    message=(
                        "this game's encounters have not been gathered yet: it brings no way to "
                        f"obtain anything at all. {len(missing)} of its {len(needed)} dex "
                        f"entries have no source anywhere in the dataset, and the other "
                        f"{elsewhere} are only covered by other games"
                    ),
                )
                continue

            if not missing:
                continue

            for entry in missing:
                yield Finding(
                    rule=self.name,
                    severity=Severity.ERROR,
                    game=game.game.id,
                    message=(
                        f"{entry.target} is in the dex at #{entry.number} but no game in the "
                        "dataset can produce it, and it is not marked unobtainable"
                    ),
                )


class NoEvolutionDeadEnds:
    """Evolving into something is only an answer if the thing you evolve is itself gettable.

    "Gettable" is the same word ``every-entry-has-a-method`` uses, and it means the same thing
    here: obtainable in some game, *or* marked unobtainable with a reason. Emerald can evolve a
    Meditite into a Medicham and cannot catch a Meditite, and its dex says so in as many words -
    "Ruby and Sapphire only in Generation 3; trade one in". Calling that a dead end would report
    a fact someone checked as though nobody had looked, which is the one distinction this file
    exists to keep.
    """

    name = "no-evolution-dead-ends"

    def check(self, dataset: Dataset) -> Iterator[Finding]:
        rules_by_id = {rule.id: rule for rule in dataset.evolution_rules}
        obtainable = _obtainable_anywhere(dataset)
        listed = _listed_in_any_dex(dataset)

        for game in dataset.games:
            explained = _explained_in(game)
            outside: list[str] = []
            formless: list[str] = []

            for method in game.acquisition_methods:
                if method.kind != "evolution":
                    continue

                rule = rules_by_id.get(method.rule)
                if rule is None:
                    yield Finding(
                        rule=self.name,
                        severity=Severity.ERROR,
                        game=game.game.id,
                        message=(
                            f"{method.target} evolves by rule {method.rule}, which does not exist"
                        ),
                    )
                    continue

                previous = _target_key(rule.from_)
                if previous in obtainable or previous in explained:
                    continue

                # A game asks about every species its living dex reaches, so it records
                # evolutions whose earlier stage belongs to a generation that is not built yet.
                # That is the dataset being unfinished rather than this game being wrong.
                if previous not in listed:
                    # Unless it is a form, which is never in any dex and so can never be
                    # "listed" - a different thing that needs a different sentence.
                    if rule.from_.form is not None:
                        formless.append(str(rule.from_))
                    else:
                        outside.append(str(rule.from_))
                    continue

                yield Finding(
                    rule=self.name,
                    severity=Severity.ERROR,
                    game=game.game.id,
                    message=(
                        f"{method.target} is only obtainable by evolving {rule.from_}, "
                        "which nothing can produce and nothing explains"
                    ),
                )

            if outside:
                yield _not_covered_yet(self.name, game.game.id, "evolving", outside)

            if formless:
                yield _no_way_to_the_form(self.name, game.game.id, "evolving", formless)


class UnreachableEntriesSaySo:
    """An entry a game can only reach by evolving something it has never seen is not fillable.

    The subtler half of ``no-evolution-dead-ends``, which asks whether the earlier stage is
    obtainable *anywhere*. That is the right question for the dataset and the wrong one for a
    player holding one cartridge: Omega Ruby records "evolve a Lombre" for its Ludicolo, the
    record is true, and no Omega Ruby will ever produce a Lotad.

    It was true of sixteen games when this was written, because every version exclusive in the
    dataset had been worked out from encounter tables and nobody had walked the evolutions
    afterwards. :func:`reach.spread_unobtainable` now gives each of those entries the reason its
    own line already carries, and this rule is what notices when a new one arrives without it.

    An entry with nothing explained anywhere in its line is left to ``every-entry-has-a-method``,
    which says the same thing about the whole of it rather than about its last stage.
    """

    name = "unreachable-entries-say-so"

    def check(self, dataset: Dataset) -> Iterator[Finding]:
        by_id = {rule.id: rule for rule in dataset.evolution_rules}

        for game in dataset.games:
            # A game with no methods of its own has not been gathered yet, which is one finding
            # in `every-entry-has-a-method` and would be two hundred here.
            if not game.acquisition_methods:
                continue

            reached = reachable_in(game, rules=by_id)
            explained = {
                entry.target.species
                for entry in game.dex_entries
                if entry.unobtainable_reason is not None
            }
            parents = parents_in(game.acquisition_methods, rules=by_id)

            for entry in game.dex_entries:
                species = entry.target.species
                if species in reached or species in explained:
                    continue

                if not _ancestors(species, parents) & explained:
                    continue

                yield Finding(
                    rule=self.name,
                    severity=Severity.ERROR,
                    game=game.game.id,
                    message=(
                        f"{entry.target} is in the dex at #{entry.number} and nothing in this "
                        "game can reach it: what it comes from cannot be had here, and the "
                        "entry says nothing about that"
                    ),
                )


def _ancestors(species: str, parents: Iterable) -> set[str]:
    """Everything this species comes from in one game, however far back."""
    found: set[str] = set()
    edge = set(parents.get(species, ()))

    while edge:
        found |= edge
        edge = {older for one in edge for older in parents.get(one, ()) if older not in found}

    return found


class NoBreedingDeadEnds:
    """Breeding is only an answer if one of the parents can be had.

    The same lie as an evolution dead end, in a different shape: "hatch a Pichu" means nothing
    to someone with no way to get a Pikachu. Any one parent is enough, because any one of them
    left at the day care produces the egg.
    """

    name = "no-breeding-dead-ends"

    def check(self, dataset: Dataset) -> Iterator[Finding]:
        obtainable = _obtainable_anywhere(dataset)
        listed = _listed_in_any_dex(dataset)

        for game in dataset.games:
            explained = _explained_in(game)
            outside: list[str] = []

            for method in game.acquisition_methods:
                if method.kind != "breeding":
                    continue

                if any(
                    _target_key(parent) in obtainable or _target_key(parent) in explained
                    for parent in method.parents
                ):
                    continue

                parents = " or ".join(str(parent) for parent in method.parents)

                # The same distinction the evolution rule makes: no parent obtainable because
                # nobody has built the generation they come from is not this game's fault.
                if all(_target_key(parent) not in listed for parent in method.parents):
                    outside.append(parents)
                    continue

                yield Finding(
                    rule=self.name,
                    severity=Severity.ERROR,
                    game=game.game.id,
                    message=(
                        f"{method.target} is only obtainable by breeding {parents}, "
                        "which nothing can produce and nothing explains"
                    ),
                )

            if outside:
                yield _not_covered_yet(self.name, game.game.id, "breeding", outside)


class UnobtainableEntriesReallyAre:
    """An entry a game can actually produce must not also claim it cannot.

    The two are easy to get out of step, because they are established at different times. A
    version exclusive is worked out from encounter tables, before evolutions exist; the
    evolutions arrive a step later and can quietly reach the very thing that was written off.
    Ruby has no wild Banette and was marked accordingly - and it has wild Shuppet, which
    evolves into one.

    "Can produce" here means the game can get there on its own: something it catches or is
    handed, and then anything those evolve or hatch into, and so on. A stated reason whose
    subject is genuinely out of reach - Emerald evolving a Medicham from a Meditite it cannot
    catch - is not caught by this, which is the point.
    """

    name = "unobtainable-entries-really-are"

    def check(self, dataset: Dataset) -> Iterator[Finding]:
        rules_by_id = {rule.id: rule for rule in dataset.evolution_rules}

        for game in dataset.games:
            reachable = self._reachable_in(game, rules_by_id)

            for entry in game.dex_entries:
                if entry.unobtainable_reason is None:
                    continue

                if _target_key(entry.target) in reachable:
                    yield Finding(
                        rule=self.name,
                        severity=Severity.ERROR,
                        game=game.game.id,
                        message=(
                            f"{entry.target} is marked unobtainable, but this game can produce "
                            "it without help from anywhere else"
                        ),
                    )

    @staticmethod
    def _reachable_in(game, rules_by_id) -> set[tuple[str, str | None]]:
        """What this game can get to on its own, following evolutions and eggs as far as they go."""
        # Caught, handed over or traded for: no prerequisite this game has to satisfy first.
        reachable = {
            _target_key(method.target)
            for method in game.acquisition_methods
            if method.kind in {"wild", "gift", "trade"} and _counts(method)
        }

        # Then anything those turn into, and anything those turn into, until nothing new appears.
        growing = True
        while growing:
            growing = False

            for method in game.acquisition_methods:
                key = _target_key(method.target)
                if key in reachable:
                    continue

                if method.kind == "evolution":
                    rule = rules_by_id.get(method.rule)
                    reached = rule is not None and _target_key(rule.from_) in reachable
                elif method.kind == "breeding":
                    reached = any(_target_key(parent) in reachable for parent in method.parents)
                else:
                    continue

                if reached:
                    reachable.add(key)
                    growing = True

        return reachable


class FormsReferencedExist:
    """A dex that numbers a form the form table has never heard of would build a broken grid."""

    name = "forms-referenced-exist"

    def check(self, dataset: Dataset) -> Iterator[Finding]:
        forms_by_id = {form.id: form for form in dataset.forms}

        for game in dataset.games:
            for entry in game.dex_entries:
                if entry.target.form is None:
                    continue

                form = forms_by_id.get(entry.target.form)
                if form is None:
                    yield Finding(
                        rule=self.name,
                        severity=Severity.ERROR,
                        game=game.game.id,
                        message=(
                            f"the dex lists form {entry.target.form}, "
                            "which is not in the form table"
                        ),
                    )
                    continue

                if form.species != entry.target.species:
                    yield Finding(
                        rule=self.name,
                        severity=Severity.ERROR,
                        game=game.game.id,
                        message=(
                            f"the dex lists {entry.target.form} under {entry.target.species}, "
                            f"but the form table says it belongs to {form.species}"
                        ),
                    )
                    continue

                # Not in the spec's list, but the dex builder drops forms whose games do not
                # include the game being built, so this disagreement silently shortens a dex.
                if game.game.id not in form.games:
                    yield Finding(
                        rule=self.name,
                        severity=Severity.WARNING,
                        game=game.game.id,
                        message=(
                            f"the dex numbers {entry.target.form}, but the form table does not "
                            "list this game among the ones it exists in, so the dex builder will "
                            "leave it out"
                        ),
                    )


class EveryDexNumberMeansOneThing:
    """A number in a game's dex points at one Pokemon, and a game with several says which list.

    Twenty games were written before a dex entry could name the list it belongs to, because
    twenty games had one list each and a number could not be ambiguous. X and Y have three -
    Central, Coastal and Mountain Kalos - which share no species and each start at #001, so
    three entries are numbered #001 in the same game and all three are right.

    That makes two things worth checking, and neither could go wrong before now. A game that
    names the list on some entries and not others has three lists that will be read as one and
    a half; and two different species numbered the same within one list is the collision the
    naming exists to prevent, arriving anyway. A species numbered twice is not that: a dex may
    list a species and its forms separately, and the app already shows such a species under its
    lowest number.
    """

    name = "every-dex-number-means-one-thing"

    def check(self, dataset: Dataset) -> Iterator[Finding]:
        for game in dataset.games:
            named = [entry for entry in game.dex_entries if entry.dex is not None]

            if named and len(named) != len(game.dex_entries):
                yield Finding(
                    rule=self.name,
                    severity=Severity.ERROR,
                    game=game.game.id,
                    message=(
                        f"{len(named)} of its {len(game.dex_entries)} dex entries say which of "
                        "this game's Pokedexes they are numbered in and the rest do not, so the "
                        "numbering of the ones that do not cannot be read"
                    ),
                )
                continue

            yield from self._collisions(game)

    def _collisions(self, game) -> Iterator[Finding]:
        seen: dict[tuple[str | None, int], str] = {}

        for entry in game.dex_entries:
            key = (entry.dex, entry.number)
            first = seen.setdefault(key, entry.target.species)

            if first == entry.target.species:
                continue

            where = f"the {entry.dex} dex" if entry.dex else "its dex"
            yield Finding(
                rule=self.name,
                severity=Severity.ERROR,
                game=game.game.id,
                message=(
                    f"{where} numbers both {first} and {entry.target.species} #{entry.number}, "
                    "so one of them is unreachable in the grid"
                ),
            )


class VersionPairsNameEachOther:
    """A pair is two games, and each one says who the other is.

    The field has been in the schema since Phase 0 and nothing ever checked it, because until
    Ruby and Sapphire there was no pair to get wrong. A half that names a game the dataset does
    not have, or one that names a partner which names somebody else, is a claim the app would
    read and act on.
    """

    name = "version-pairs-name-each-other"

    def check(self, dataset: Dataset) -> Iterator[Finding]:
        by_id = {game.game.id: game.game for game in dataset.games}

        for game in dataset.games:
            partner_id = game.game.pair_partner
            if partner_id is None:
                continue

            if partner_id == game.game.id:
                yield Finding(
                    rule=self.name,
                    severity=Severity.ERROR,
                    game=game.game.id,
                    message="names itself as its own pair partner",
                )
                continue

            partner = by_id.get(partner_id)
            if partner is None:
                yield Finding(
                    rule=self.name,
                    severity=Severity.ERROR,
                    game=game.game.id,
                    message=(
                        f"names {partner_id} as the other half of its pair, which is not a game "
                        "in the dataset"
                    ),
                )
                continue

            if partner.pair_partner != game.game.id:
                named = partner.pair_partner or "nobody"
                yield Finding(
                    rule=self.name,
                    severity=Severity.ERROR,
                    game=game.game.id,
                    message=(
                        f"names {partner_id} as the other half of its pair, but {partner_id} "
                        f"names {named}"
                    ),
                )


class TransferEdgesConnectKnownGames:
    """An edge to a game that is not in the dataset is a route the app can never explain."""

    name = "transfer-edges-connect-known-games"

    def check(self, dataset: Dataset) -> Iterator[Finding]:
        known = {game.game.id for game in dataset.games}

        for edge in dataset.transfers:
            for end, role in ((edge.from_, "from"), (edge.to, "to")):
                if end not in known:
                    yield Finding(
                        rule=self.name,
                        severity=Severity.ERROR,
                        message=(
                            f"the {edge.mechanism.value} edge {edge.from_} -> {edge.to} names "
                            f"{end} as its {role}, which is not a game in the dataset"
                        ),
                    )


class EverySpeciesHasASprite:
    """A species with no sprite file is a hole in the grid the moment the app runs offline.

    A warning rather than an error, because the rest of the dataset is still worth shipping and
    the build already logs the fetch that failed. It is here so the hole is counted and written
    down rather than scrolling past in a log.
    """

    name = "every-species-has-a-sprite"

    def check(self, dataset: Dataset) -> Iterator[Finding]:
        # A build run with --no-sprites has none at all; that is a deliberate quick build and
        # saying it 1025 times helps nobody.
        if not dataset.sprites:
            return

        for species in dataset.species:
            if species.id not in dataset.sprites:
                yield Finding(
                    rule=self.name,
                    severity=Severity.WARNING,
                    message=(
                        f"{species.id} has no sprite, so its tile will be blank; the app ships "
                        "its sprites and never fetches one at runtime"
                    ),
                )


class EveryGameHasBoxArt:
    """A game with no cover is a blank card in the picker.

    A warning, like a missing sprite: the app draws a plain cover in its place and the rest of
    the dataset is fine. It is reported so the gap is counted rather than noticed by a player.
    """

    name = "every-game-has-box-art"

    def check(self, dataset: Dataset) -> Iterator[Finding]:
        # A build run with --no-box-art has none at all, which is a deliberate quick build.
        if not dataset.box_art:
            return

        for game in dataset.games:
            # A node is never in the picker, so it has no cover to be missing.
            if _is_node(game):
                continue

            if game.game.id not in dataset.box_art:
                yield Finding(
                    rule=self.name,
                    severity=Severity.WARNING,
                    game=game.game.id,
                    message=(
                        "no box art, so the game picker will draw a plain cover instead of "
                        "showing the box"
                    ),
                )


def coverage_for(dataset: Dataset) -> list[GameCoverage]:
    """How much of what each game asks a player to fill the dataset can account for, and from
    where.

    The three words the spec asks for, given a meaning here because it does not define them:

    * ``full`` — obtainable in this very game.
    * ``partial`` — not here, but obtainable in another game, so it is a transfer away.
    * ``missing`` — nothing can produce it anywhere. A hole.

    ``unobtainable`` is counted separately rather than folded into one of the three: an entry
    someone has checked and marked is not the same as one nobody has looked at.

    Counted over the living dex rather than the game's own Pokedex, because that is what a
    player is filling and what the grid shows. Diamond used to report 151 entries of which 146
    were full, which was true and answered a question nobody asked: the screen has 493 tiles on
    it. The numbers are larger and worse now, and they are about the right thing.
    """
    obtainable_anywhere = _obtainable_anywhere(dataset)
    coverage: list[GameCoverage] = []

    for game in dataset.games:
        # A transfer node asks a player to fill nothing, and four zeroes in this report read
        # like a game nobody has started rather than like a thing with no dex.
        if _is_node(game):
            continue

        here = _obtainable_in(dataset, game.game.id)
        explained = _reasons_in(game)
        full = partial = missing = unobtainable = 0

        for species in _living_dex(dataset, game):
            key = (species, None)

            if species in explained:
                unobtainable += 1
            elif key in here:
                full += 1
            elif key in obtainable_anywhere:
                partial += 1
            else:
                missing += 1

        coverage.append(
            GameCoverage(
                game=game.game.id,
                full=full,
                partial=partial,
                missing=missing,
                unobtainable=unobtainable,
            )
        )

    return coverage


def all_rules() -> list:
    """Every check, in the order the spec lists them.

    Four are not in that list. ``no-breeding-dead-ends`` arrived with the breeding kind and
    guards the same lie its evolution twin does. ``version-pairs-name-each-other`` arrived with
    Ruby and Sapphire, the first pair the dataset has ever held, and checks a field that had
    been carried since Phase 0 without anything ever reading it.
    ``unobtainable-entries-really-are`` arrived with the same pair, after two entries were
    written off as version exclusives and then reached by an evolution a step later.
    ``every-dex-number-means-one-thing`` arrived with X and Y, the first games to show more than
    one Pokedex, and guards the field that keeps their three lists apart.
    ``unreachable-entries-say-so`` arrived with Omega Ruby, whose Ludicolo has an evolution to
    come from and no Lotad to start it - which turned out to be true of eighty-six entries in
    sixteen games.
    """
    return [
        EveryEntryHasAMethod(),
        NoEvolutionDeadEnds(),
        UnreachableEntriesSaySo(),
        NoBreedingDeadEnds(),
        UnobtainableEntriesReallyAre(),
        FormsReferencedExist(),
        EveryDexNumberMeansOneThing(),
        VersionPairsNameEachOther(),
        TransferEdgesConnectKnownGames(),
        EverySpeciesHasASprite(),
        EveryGameHasBoxArt(),
    ]


def rule_names(rules: Iterable[object]) -> list[str]:
    return [getattr(rule, "name", type(rule).__name__) for rule in rules]
