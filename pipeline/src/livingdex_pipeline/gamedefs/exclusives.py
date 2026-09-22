"""Why an entry is in a cartridge's dex and never in the cartridge.

A version exclusive is the commonest reason, and it is the same fact in every generation: the
other half of the pair has it, this one does not, and the link between them is how the entry
gets filled. The sentence a player reads should not depend on which cartridge they happened to
buy, and it should not be written out once per generation either - which is how it ends up
saying "Generation 3" in a Generation 4 game.

Each hardware module wraps this with its own generation filled in, so a game file says
``only_on("Pearl")`` and nothing else.
"""

from __future__ import annotations


def only_on(partner: str, *, generation: int, event: str | None = None) -> str:
    """Why an entry in this dex is not in this cartridge, when the other half has it.

    A version exclusive is still an entry you have to fill, and the transfer graph is how -
    which is the whole reason the two halves declare a route to each other.

    ``event`` is what step 7 found. It does not change that the cartridge cannot produce one; it
    answers the next question, which is where one could ever have come from.
    """
    return with_event(f"{partner} only in Generation {generation}; trade one in", event)


def with_event(reason: str, event: str | None) -> str:
    """One reason, with what step 7 found about it added as a second sentence."""
    return f"{reason}. {event[0].upper()}{event[1:]}" if event else reason
