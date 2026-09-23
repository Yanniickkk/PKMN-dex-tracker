"""The sixth kind of record: how a form is come by, once the Pokemon is already caught."""

from __future__ import annotations

from datetime import date

from livingdex_pipeline.formchanges import (
    GENDER,
    FormChange,
    form_change_encounters,
    spread,
)
from livingdex_pipeline.models import Form, FormKind, SourceCitation

CITATION = SourceCitation(
    source="bulbapedia", url="https://example/forms", retrieved_on=date(2026, 9, 23)
)


def form(name: str, species: str, kind: FormKind = FormKind.FUNCTIONAL) -> Form:
    return Form(id=name, species=species, name=name.title(), kind=kind, games=["platinum"])


def changes(*forms: Form, table=None):
    return form_change_encounters(
        game_id="platinum",
        forms=list(forms),
        changes=table or {},
        citation=CITATION,
    )


def test_a_form_with_a_sentence_becomes_one_record() -> None:
    table = {"rotom-heat": FormChange(requirement="Let it possess the oven", where="Rotom's Room")}

    [record] = changes(form("rotom-heat", "rotom"), table=table)

    assert record.kind == "formChange"
    assert record.game == "platinum"
    assert record.target.species == "rotom"
    assert record.target.form == "rotom-heat"
    assert record.requirement == "Let it possess the oven"
    assert record.location == "Rotom's Room"


def test_a_form_nobody_has_explained_gets_no_record_at_all() -> None:
    # "No recorded way to get this in your games" is an honest answer and an invented sentence
    # is not. An Unown in Ruby is exactly this: the letters are in its dex and its cartridge
    # has no ruins to find one in.
    assert changes(form("unown-b", "unown")) == []


def test_one_sentence_covers_a_family_without_being_written_out_again() -> None:
    table = spread(
        FormChange(requirement="Whichever season it is"),
        "deerling-summer",
        "deerling-winter",
    )

    records = changes(
        form("deerling-summer", "deerling"),
        form("deerling-winter", "deerling"),
        table=table,
    )

    assert [one.requirement for one in records] == ["Whichever season it is"] * 2
    assert {one.target.form for one in records} == {"deerling-summer", "deerling-winter"}


def test_a_sex_answers_itself_wherever_it_is_asked() -> None:
    # The one form that is not something you do to a Pokemon you have: you look for it while
    # catching. Ninety-seven species ask it and the answer is the same every time, so no region
    # writes it down.
    [record] = changes(form("venusaur-female", "venusaur", FormKind.GENDER))

    assert record.requirement == GENDER.requirement
    assert record.location is None


def test_a_region_can_still_answer_for_a_sex_in_its_own_words() -> None:
    # Frillish and Jellicent are the two the source models as forms rather than as a flag, and
    # a game with something to add about one is not overruled by the standard sentence.
    table = {"frillish-female": FormChange(requirement="The pink one")}

    [record] = changes(form("frillish-female", "frillish", FormKind.GENDER), table=table)

    assert record.requirement == "The pink one"
