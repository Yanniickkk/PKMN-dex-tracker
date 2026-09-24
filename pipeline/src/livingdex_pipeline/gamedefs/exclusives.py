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


def fossil_only_on(partner: str, fossil: str, *, generation: int, event: str | None = None) -> str:
    """Why the fossil Pokemon of the other half is not in this one.

    Not quite a plain exclusive, and the difference is that a fossil is an item. One half stocks
    or buries the Skull Fossil and the other the Armor Fossil, but either can come across the
    link held by a traded Pokemon and be revived here - so there are two ways over rather than
    one, and a player who cannot find anyone with a spare Cranidos still has the other.

    Sinnoh wrote this first, about two fossils in the Underground. Alola needed the same
    sentence about four in a shop ten years later, which is why it is here and not there.
    """
    return with_event(
        f"{partner} only in Generation {generation}; trade one in, or trade for a Pokemon "
        f"holding the {fossil} and revive that",
        event,
    )


def with_event(reason: str, event: str | None) -> str:
    """One reason, with what step 7 found about it added as a second sentence."""
    return f"{reason}. {event[0].upper()}{event[1:]}" if event else reason


def handed_out(*events: str) -> str:
    """One sentence naming every distribution that ever handed this species out.

    Written as a list of events rather than one sentence per event because most of these were
    covered twice, and "an event existed" is the answer a player is after - which one is detail
    they can read once and forget.

    Here rather than in a region, because step 7 asks the same question of every game and the
    answer is the same shape in all of them. Kanto wrote it first and Unova needed it next.
    """
    named = (
        " and ".join(events) if len(events) < 3 else f"{', '.join(events[:-1])} and {events[-1]}"
    )

    return f"{named} handed one out"
