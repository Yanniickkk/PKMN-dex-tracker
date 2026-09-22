"""What has to be true before an encounter slot holds anything.

PokeAPI marks the rows of an encounter table with the state of the world each row is filled in:
the time of day, the day of the week, what is in the Game Boy Advance slot underneath, how far
the story has got, which item is in the bag. Generation 3 has three such rows in total.
Generation 4 has thousands, and some of them carry the whole answer - Gengar is in Sinnoh's
grass only while a Generation 3 cartridge is in the slot.

Wild slots and gifts read the same tables, so they read them the same way, from here. A game
that knows better says so in its own table: what is written here is the fallback, and its job
is to make sure nothing is dropped without anybody noticing.
"""

from __future__ import annotations

import logging

from .places import pretty

log = logging.getLogger(__name__)

#: Prefixes of conditions that have a field of their own rather than a sentence.
TIME = "time-"
SEASON = "season-"

#: Conditions that restrict nothing: the ordinary state of the world.
#:
#: Generation 4 marks every row with the state it is filled in, so the slots a player walks into
#: on an ordinary afternoon carry "no swarm", "no Poke Radar" and "no Game Boy Advance cartridge
#: in the slot underneath". Those are three ways of writing "this is simply what is there", and
#: a Bidoof met in four of them is one Bidoof: their chances add up into the plain total rather
#: than becoming four rows, each telling a player to make sure nothing unusual is happening.
ORDINARY = frozenset(
    {
        "swarm-no",
        "radar-off",
        "slot2-none",
        "radio-off",
        "item-none",
        "other-none",
        "story-progress-none",
        "bug-catching-contest-no",
        # The Great Marsh keeps six residents and rotates two more in each day; the residents
        # are marked as belonging to no daily slot. Marill is there whatever the day says.
        "great-marsh-daily-slot-none",
        # And the Trophy Garden the same way: Pichu and Pikachu live there, and the two Mr.
        # Backlot talks about are the ones that change.
        "backlot-not-mentioned",
    }
)

#: What a condition that does restrict something means, in words a player would recognise.
#:
#: Only the ones the games in the dataset actually use are written out. Anything else is still
#: carried - as its slug, tidied up - and logged at warning level, so the next generation's
#: conditions announce themselves instead of disappearing.
REQUIREMENTS: dict[str, str] = {
    # Dual-slot mode: a Generation 3 cartridge in the Game Boy Advance slot of a DS opens extra
    # slots in Sinnoh's grass. This is the one condition that asks for hardware a player may not
    # own, which is exactly why it cannot be left unsaid.
    "slot2-ruby": "Dual-slot mode, with a Pokemon Ruby cartridge in the Game Boy Advance slot",
    "slot2-sapphire": (
        "Dual-slot mode, with a Pokemon Sapphire cartridge in the Game Boy Advance slot"
    ),
    "slot2-emerald": (
        "Dual-slot mode, with a Pokemon Emerald cartridge in the Game Boy Advance slot"
    ),
    "slot2-firered": (
        "Dual-slot mode, with a Pokemon FireRed cartridge in the Game Boy Advance slot"
    ),
    "slot2-leafgreen": (
        "Dual-slot mode, with a Pokemon LeafGreen cartridge in the Game Boy Advance slot"
    ),
    "radar-on": "With the Poke Radar running",
    "swarm-yes": "Only while it is swarming",
    # The three tables the honey trees are drawn from. Which tree belongs to which group is the
    # game's business; what a player needs to know is that not every tree will do.
    "honey-tree-group-a": "On a honey tree of the first group",
    "honey-tree-group-b": "On a honey tree of the second group",
    "honey-tree-group-c": "On a honey tree of the third group",
    "backlot-mentioned": "Only on days Mr. Backlot mentions it in the Trophy Garden",
    # Generation 3 has exactly three conditioned wild slots, and all three are the roaming eon
    # duo: neither one is loose in Hoenn until the Elite Four are beaten, and in Emerald which
    # of the two it is depends on the colour picked when the television asks.
    "story-progress-hall-of-fame": "After entering the Hall of Fame",
    "tv-option-red": "Only if the red Pokemon was picked in the television broadcast",
    "tv-option-blue": "Only if the blue Pokemon was picked in the television broadcast",
    "story-progress-before-national-dex": "Before the National Dex opens",
    "story-progress-national-dex": "After the National Dex opens",
    "story-progress-beat-galactic-coronet": "After Team Galactic is beaten at Mt. Coronet",
    "story-progress-defeat-mars": "After Mars is beaten at the Valley Windworks",
    "story-progress-beat-team-galactic-iron-island": "After Team Galactic is beaten on Iron Island",
    "other-talked-to-32-people-underground": "After talking to 32 people in the Underground",
    "weekday-sunday": "On a Sunday",
    "weekday-monday": "On a Monday",
    "weekday-tuesday": "On a Tuesday",
    "weekday-wednesday": "On a Wednesday",
    "weekday-thursday": "On a Thursday",
    "weekday-friday": "On a Friday",
    "weekday-saturday": "On a Saturday",
}

#: The Great Marsh rotates two of thirty-two species in each day, and PokeAPI says which of the
#: two slots a species is drawn for. The number is the slot, not the odds.
_GREAT_MARSH = "great-marsh-daily-slot-"

#: An item in the bag, named as the game names it: a fossil to revive, a keystone to place.
_ITEM = "item-"

#: What a Game Corner window charges. The games that have one price their prizes themselves,
#: so this is only what a game that has not bothered would say.
_COINS = "coins-"


def requirement(values: list[str], *, subject: str) -> str | None:
    """Every condition on one row that is not the time or the season, as one sentence.

    Each phrase is written to stand on its own, so the ones after the first are lowered into
    the sentence they are joined onto: "... and After the National Dex opens" reads like two
    sentences that collided.
    """
    phrases = [
        phrase(value, subject=subject)
        for value in values
        if value not in ORDINARY and not value.startswith((TIME, SEASON))
    ]

    if not phrases:
        return None

    first, *rest = phrases

    return " and ".join([first, *(one[:1].lower() + one[1:] for one in rest)])


def phrase(value: str, *, subject: str) -> str:
    """One condition as a sentence a player can act on."""
    if value in REQUIREMENTS:
        return REQUIREMENTS[value]

    if value.startswith(_GREAT_MARSH):
        slot = value.removeprefix(_GREAT_MARSH).replace("-of-", " of ")
        return f"Only on days the Great Marsh rotates it in (daily slot {slot})"

    if value.startswith(_ITEM):
        return pretty(value.removeprefix(_ITEM))

    if value.startswith(_COINS):
        return f"Game Corner prize, {value.removeprefix(_COINS)} coins"

    # A real restriction with no wording yet: carried through as its slug rather than dropped,
    # and said out loud, because a condition nobody has read is a sentence nobody has checked.
    log.warning("%s has a condition with no wording yet: %s", subject, value)

    return value.replace("-", " ").capitalize()


def of(values: list[str], prefix: str) -> str | None:
    """The one condition with this prefix, without it: ``time-night`` is "night"."""
    found = next((one for one in values if one.startswith(prefix)), None)

    return found[len(prefix) :] if found else None
