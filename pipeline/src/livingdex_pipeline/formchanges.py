"""How a form is come by, for one game.

The sixth kind of record, and the one the other five could not be bent into. Everything else in
this pipeline answers "how do I get one of these": a slot in the grass, somebody handing it
over, an egg, a trade, an evolution. A form asks the question after that one. The Pokemon is
already caught and something changes it - the Reveal Glass, the DNA Splicers, a season turning
over, which sea you are standing on - and none of those is a way of getting a Pokemon.

No API carries it. Which sentence belongs to which form is a fact about one set of games, so it
lives in that region's own file the way its gifts and trades do, and this module only turns the
table into records. A form with no sentence gets no record rather than a guessed one: "no
recorded way" is an honest answer and an invented one is not.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .models import DexTarget, Form, FormChangeAcquisition, FormKind, SourceCitation


@dataclass(frozen=True)
class FormChange:
    """What one game knows about turning something into one of its forms."""

    #: What makes the change, in words a player can act on.
    requirement: str
    #: Where it happens, when it is somewhere rather than something.
    where: str | None = None


#: The answer for a sex, which is the same wherever the question is asked.
#:
#: Every other form in this dataset is a thing you do to a Pokemon you already have; this one is
#: a thing you look for while catching it. It is written here rather than in each region because
#: it is not a fact about a region at all - the games started drawing the sexes apart in
#: Generation 4 and have done it the same way since.
GENDER = FormChange(
    requirement="Catch or hatch a female one; the sexes have been drawn apart since Generation 4"
)


def spread(change: FormChange, *forms: str) -> dict[str, FormChange]:
    """One sentence over a family of forms.

    Unown has twenty-seven letters and one answer; Deerling four coats and one answer. Writing
    the sentence once and naming what it covers is shorter than twenty-seven copies and cannot
    drift apart from itself.
    """
    return dict.fromkeys(forms, change)


def form_change_encounters(
    *,
    game_id: str,
    forms: Sequence[Form],
    changes: Mapping[str, FormChange],
    citation: SourceCitation,
) -> list[FormChangeAcquisition]:
    """One record per form of this game that can be explained.

    ``forms`` is the shared table filtered to this game, which already knows what each form is.
    A sex needs no table: its answer is :data:`GENDER` everywhere, and a region that wrote it
    out again would be writing down the same sentence twenty times.
    """
    return [
        FormChangeAcquisition(
            game=game_id,
            target=DexTarget(species=form.species, form=form.id),
            requirement=change.requirement,
            location=change.where,
            source=citation,
        )
        for form in forms
        for change in (_change_for(form, changes),)
        if change is not None
    ]


def _change_for(form: Form, changes: Mapping[str, FormChange]) -> FormChange | None:
    if form.id in changes:
        return changes[form.id]

    return GENDER if form.kind is FormKind.GENDER else None
