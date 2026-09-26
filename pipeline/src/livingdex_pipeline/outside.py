"""Sources that are not games: what they send in, and why it never counts.

Two things in the series put Pokemon into a cartridge without being cartridges themselves.

* The **Pokemon Dream Radar**, a Nintendo 3DS download from 2012 that sends what it catches
  down into Black 2 and White 2 and into nothing else.
* **Pokemon GO**, which reaches Let's Go, Pikachu! and Let's Go, Eevee! through the GO Park.

Neither is a game in the sense this dataset means - no Pokedex to fill, and nothing caught in
either the way this tracker counts catching - so neither can be an entity, and a transfer edge
would have needed one at each end. What is left is a row on the entry itself, which is
:class:`models.OutsideAcquisition`, and this module is what builds those rows.

**Scope, decided by Yannick on 26 September 2026: only where nothing in the game produces one
anyway.** The Radar also hands out fifteen Dream World Pokemon with Hidden Abilities, and Black
2 can catch every one of them; the GO Park will send any of the first 150 across, and Kanto is
full of them. Writing those down would add hundreds of rows that change no answer.

**And none of them ever counts.** :attr:`models.OutsideAcquisition.does_not_count` is required
rather than optional, which is the decision written into the model: a way that leaves this
dataset is a way this dataset cannot promise. The row is shown, the tile stays out of reach, and
the line says why - the same treatment Kalos's Friend Safari has had since Generation 6.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import DexTarget, OutsideAcquisition, SourceCitation


@dataclass(frozen=True)
class SentIn:
    """One thing an outside source can send into one game."""

    #: The species, as the dataset spells it.
    species: str
    #: What the player does at the source, in words they can act on.
    how: str
    #: The form it arrives as, when it is not the species' default. The Radar's forces of
    #: nature arrive in Therian Forme, which is the whole of why this field is here.
    form: str | None = None
    #: What else has to be true first: a cartridge in the same console, another catch before it.
    requirement: str | None = None


def sent_in(
    *,
    game_id: str,
    sent_from: str,
    rows: list[SentIn],
    does_not_count: str,
    citation: SourceCitation,
) -> list[OutsideAcquisition]:
    """The rows one outside source contributes to one game.

    :param game_id: The game the Pokemon arrives in.
    :param sent_from: What to call the source on screen, as a player would name it.
    :param rows: What it sends.
    :param does_not_count: Why none of this counts towards being able to get one here.
    :param citation: The page the table was read from.
    """
    return [
        OutsideAcquisition(
            game=game_id,
            target=DexTarget(species=row.species, form=row.form),
            sent_from=sent_from,
            how=row.how,
            requirement=row.requirement,
            does_not_count=does_not_count,
            source=citation,
        )
        for row in rows
    ]
