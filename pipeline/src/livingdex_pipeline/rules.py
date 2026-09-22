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

from .models import DexTarget
from .validate import Dataset, Finding, GameCoverage, Severity


def _target_key(target: DexTarget) -> tuple[str, str | None]:
    return (target.species, target.form)


def _obtainable_anywhere(dataset: Dataset) -> set[tuple[str, str | None]]:
    """Every target some game in the dataset can produce."""
    return {
        _target_key(method.target) for game in dataset.games for method in game.acquisition_methods
    }


def _obtainable_in(dataset: Dataset, game_id: str) -> set[tuple[str, str | None]]:
    game = dataset.game(game_id)
    return {_target_key(method.target) for method in game.acquisition_methods} if game else set()


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

    A game nothing at all can be obtained in is reported once rather than once per entry: that
    is a game whose encounters have not been gathered yet, and two hundred identical errors say
    the same thing as one while burying everything else in the report. The build fails either
    way, because the game is not finished either way.
    """

    name = "every-entry-has-a-method"

    def check(self, dataset: Dataset) -> Iterator[Finding]:
        obtainable = _obtainable_anywhere(dataset)

        for game in dataset.games:
            needed = [entry for entry in game.dex_entries if entry.unobtainable_reason is None]
            missing = [entry for entry in needed if _target_key(entry.target) not in obtainable]

            if not missing:
                continue

            # Nothing in this game's dex can be explained, and the game brought no methods of
            # its own: it has not been worked on yet rather than having gaps.
            if len(missing) == len(needed) and not game.acquisition_methods:
                yield Finding(
                    rule=self.name,
                    severity=Severity.ERROR,
                    game=game.game.id,
                    message=(
                        f"none of its {len(needed)} dex entries has a way to be obtained; this "
                        "game's encounters have not been gathered yet"
                    ),
                )
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

        for game in dataset.games:
            explained = _explained_in(game)

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
                if previous not in obtainable and previous not in explained:
                    yield Finding(
                        rule=self.name,
                        severity=Severity.ERROR,
                        game=game.game.id,
                        message=(
                            f"{method.target} is only obtainable by evolving {rule.from_}, "
                            "which nothing can produce and nothing explains"
                        ),
                    )


class NoBreedingDeadEnds:
    """Breeding is only an answer if one of the parents can be had.

    The same lie as an evolution dead end, in a different shape: "hatch a Pichu" means nothing
    to someone with no way to get a Pikachu. Any one parent is enough, because any one of them
    left at the day care produces the egg.
    """

    name = "no-breeding-dead-ends"

    def check(self, dataset: Dataset) -> Iterator[Finding]:
        obtainable = _obtainable_anywhere(dataset)

        for game in dataset.games:
            explained = _explained_in(game)

            for method in game.acquisition_methods:
                if method.kind != "breeding":
                    continue

                if any(
                    _target_key(parent) in obtainable or _target_key(parent) in explained
                    for parent in method.parents
                ):
                    continue

                parents = " or ".join(str(parent) for parent in method.parents)
                yield Finding(
                    rule=self.name,
                    severity=Severity.ERROR,
                    game=game.game.id,
                    message=(
                        f"{method.target} is only obtainable by breeding {parents}, "
                        "which nothing can produce and nothing explains"
                    ),
                )


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
            if method.kind in {"wild", "gift", "trade"}
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
    """How much of each game's dex the dataset can account for, and from where.

    The three words the spec asks for, given a meaning here because it does not define them:

    * ``full`` — obtainable in this very game.
    * ``partial`` — not here, but obtainable in another game, so it is a transfer away.
    * ``missing`` — nothing can produce it anywhere. A hole.

    ``unobtainable`` is counted separately rather than folded into one of the three: an entry
    someone has checked and marked is not the same as one nobody has looked at.
    """
    obtainable_anywhere = _obtainable_anywhere(dataset)
    coverage: list[GameCoverage] = []

    for game in dataset.games:
        here = _obtainable_in(dataset, game.game.id)
        full = partial = missing = unobtainable = 0

        for entry in game.dex_entries:
            key = _target_key(entry.target)

            if entry.unobtainable_reason is not None:
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

    Three are not in that list. ``no-breeding-dead-ends`` arrived with the breeding kind and
    guards the same lie its evolution twin does. ``version-pairs-name-each-other`` arrived with
    Ruby and Sapphire, the first pair the dataset has ever held, and checks a field that had
    been carried since Phase 0 without anything ever reading it.
    ``unobtainable-entries-really-are`` arrived with the same pair, after two entries were
    written off as version exclusives and then reached by an evolution a step later.
    """
    return [
        EveryEntryHasAMethod(),
        NoEvolutionDeadEnds(),
        NoBreedingDeadEnds(),
        UnobtainableEntriesReallyAre(),
        FormsReferencedExist(),
        VersionPairsNameEachOther(),
        TransferEdgesConnectKnownGames(),
        EverySpeciesHasASprite(),
        EveryGameHasBoxArt(),
    ]


def rule_names(rules: Iterable[object]) -> list[str]:
    return [getattr(rule, "name", type(rule).__name__) for rule in rules]
