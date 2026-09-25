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

#: Galar's, and the first use of a field that has been on the record since it was written.
#:
#: Every game before Sword and Shield has weather and none of them lets it change what is
#: standing there. The Wild Area has nine states - clear, overcast, raining, a thunderstorm,
#: intense sun, a sandstorm, snow, a snowstorm and fog - and each one is its own table.
#:
#: PokeAPI files these under its ``max-den-rating`` condition rather than a weather one, which
#: is a mistake in the source and not one worth working around: the values are named
#: ``weather-*`` and that is what is read here.
WEATHER = "weather-"

#: What the nine states of Galar's sky are called on a record.
#:
#: The field is free text and the fields beside it carry one word - "night", "spring" - so these
#: are the names Bulbapedia prints, lowered to match. "Normal" is the source's word for a sky
#: with nothing happening in it, and a player looking at it would say clear.
WEATHER_NAMES: dict[str, str] = {
    "normal": "clear skies",
    "overcast": "overcast",
    "raining": "raining",
    "thunderstorm": "thunderstorm",
    "intense-sun": "intense sun",
    "sandstorm": "sandstorm",
    "snowing": "snowing",
    "snowstorm": "snowstorm",
    "fog": "fog",
}

#: Galar's Max Raid difficulty, which is a number and is read as one.
#:
#: One to five stars, and a row carries exactly one of them - so a species in a den at three,
#: four and five stars arrives as three rows that differ in nothing else. :mod:`wild` folds
#: them back into a range rather than writing a record per star.
RATING = "max-den-rating-"

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
        # Johto's Safari Zone before anything has been put in it. Baoba only offers the blocks
        # once the National Dex has been received, so an empty area is where every player of
        # these games starts.
        "johto-safari-blocks-inactive",
        # The first two slots of a Friend Safari, which is every Safari a player can reach:
        # both are there from the moment the friend is registered. What that takes is a fact
        # about the place rather than about these two rows, and `kalos` says it once for all of
        # them. The third slot is not ordinary and has a sentence of its own below.
        "friend-safari-slot-1",
        "friend-safari-slot-2",
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
    # Let's Go, and the only place in this dataset where catching a Legendary Pokemon is what
    # puts it back in the wild. Each of the three birds has one static encounter - the source
    # puts Articuno on Seafoam Islands B4F, Zapdos in the Power Plant and Moltres on Victory
    # Road 2F, which is not where FireRed kept them - and once that one has been caught the
    # same bird starts flying over Kanto as a rare spawn, twenty-four routes' worth of it. That
    # is how a player gets a second one; every other game in the series has exactly one.
    "other-caught-articuno": "Only once the Articuno in the Seafoam Islands has been caught",
    "other-caught-zapdos": "Only once the Zapdos in the Power Plant has been caught",
    "other-caught-moltres": "Only once the Moltres in Victory Road has been caught",
    "swarm-yes": "Only while it is swarming",
    # The Pokegear radio in Johto does what the Game Boy Advance slot does in Sinnoh: it puts
    # Pokemon from another region into grass that otherwise has none of them. Two cards rather
    # than a cartridge, so this one asks for nothing a player does not already own.
    "radio-hoenn": "With the Pokegear radio tuned to the Hoenn sound",
    "radio-sinnoh": "With the Pokegear radio tuned to the Sinnoh sound",
    "bug-catching-contest-yes": "Only during the Bug-Catching Contest",
    # Johto's headbutt trees come in three groups, and which tree is in which is fixed per save
    # by the trainer id. So it is not "find the right tree" but "find out which of yours it is",
    # and a player who has the wrong trees near them has a walk ahead.
    "headbutt-tree-common": "On one of the common headbutt trees",
    "headbutt-tree-rare": "On one of the rare headbutt trees",
    "headbutt-tree-secret": "On one of the two special headbutt trees",
    # The three tables the honey trees are drawn from. Which tree belongs to which group is the
    # game's business; what a player needs to know is that not every tree will do.
    "honey-tree-group-a": "On a honey tree of the first group",
    "honey-tree-group-b": "On a honey tree of the second group",
    "honey-tree-group-c": "On a honey tree of the third group",
    "backlot-mentioned": "Only on days Mr. Backlot mentions it in the Trophy Garden",
    # Galar's dens. The beam of light over a Max Raid den says how good the raid is before a
    # player commits to it: an ordinary red pillar, or a purple one that holds the rarer table.
    # The third is the source's own wording and it is about a distribution rather than a den -
    # see `galar` for where it turns up and why it costs nothing.
    "max-den-rarity-common": "In a den under an ordinary red beam of light",
    "max-den-rarity-rare": "In a den under a strong purple beam of light",
    "max-den-rarity-special": "Only while the Wild Area News has put it there",
    # The Crown Tundra's three birds, which have to be seen leaving before they can be met.
    "other-witness-galarian-bird-fight": (
        "After watching the three fight over the Dyna Tree, which is what scatters them "
        "across Galar in the first place"
    ),
    # Generation 3 has exactly three conditioned wild slots, and all three are the roaming eon
    # duo: neither one is loose in Hoenn until the Elite Four are beaten, and in Emerald which
    # of the two it is depends on the colour picked when the television asks.
    "story-progress-hall-of-fame": "After entering the Hall of Fame",
    "story-progress-before-hall-of-fame": "Before entering the Hall of Fame",
    # The Isle of Armor's three trials, which are the spine of that island's story and gate
    # four of the things handed over on it.
    "story-progress-master-dojo-complete-first-trial": (
        "After Mustard's first trial at the Master Dojo"
    ),
    "story-progress-master-dojo-complete-third-trial": (
        "After all three of Mustard's trials at the Master Dojo"
    ),
    "tv-option-red": "Only if the red Pokemon was picked in the television broadcast",
    "tv-option-blue": "Only if the blue Pokemon was picked in the television broadcast",
    "story-progress-before-national-dex": "Before the National Dex opens",
    "story-progress-national-dex": "After the National Dex opens",
    "story-progress-beat-galactic-coronet": "After Team Galactic is beaten at Mt. Coronet",
    # Johto's postgame, which is most of Kanto. Every one of these is a gate a player has to
    # have walked through before the Pokemon on the other side exists at all.
    "story-progress-beat-red": "After Red is beaten at the top of Mt. Silver",
    "other-received-kanto-starter": "After a Kanto first partner has been taken in Pallet Town",
    "story-progress-zephyr-badge": "After the Zephyr Badge",
    "story-progress-receive-tm-from-claire": ("After Clair hands over her TM at the Dragon's Den"),
    "story-progress-returned-machine-part": (
        "After the stolen machine part is returned to the Power Plant"
    ),
    # Primo stands in a Pokemon Center and asks the player's opinion of him. Answer with the
    # right set of phrases and he hands over an egg; the codes were printed in magazines, and
    # nothing about it needs a cartridge or an event.
    "other-correct-password": "Only if Primo is given the right set of phrases",
    # PokeAPI's own marker for something the 3DS release turns on and the cartridge did not.
    # Every Generation 1 and 2 game in this dataset *is* the Virtual Console release, so this
    # is always true where it appears - and it is worth printing anyway, because a player who
    # knows the cartridge will not believe the entry otherwise.
    "other-virtual-console": "On the Virtual Console release, which the cartridge did not allow",
    "other-event-arceus-in-party": "With an event Arceus in the party",
    # PokeAPI's own label, in words: the second Snorlax only turns up once the first is dealt
    # with and the League is behind you.
    "other-snorlax-11-beat-league": (
        "Only once the Route 11 Snorlax is gone and the League has been beaten"
    ),
    # Johto's two roamers, and each one starts moving at a moment a player would remember.
    "story-progress-awakened-beasts": "After the beasts are disturbed in the Burned Tower",
    "story-progress-vermilion-copycat": (
        "After leaving the Vermilion City Pokemon Fan Club with the Copycat's doll"
    ),
    "story-progress-defeat-mars": "After Mars is beaten at the Valley Windworks",
    "story-progress-beat-team-galactic-iron-island": "After Team Galactic is beaten on Iron Island",
    "other-talked-to-32-people-underground": "After talking to 32 people in the Underground",
    # Alola's, and both halves of the same errand: Looker and Anabel hire the player to round up
    # the Ultra Beasts that came through with Lusamine, and what is waiting at the end of it is
    # the one that came through after them.
    "other-captured-all-ultra-beasts": "After every Ultra Beast has been caught",
    "story-progress-finished-looker-sidequest": (
        "After the errand Looker and Anabel hire the player for is finished"
    ),
    # The roaming legendaries of two generations, and the hoops each one waits behind. All of
    # these turned up the day the games started asking about their whole living dex instead of
    # their own Pokedex: every one of them is a National Dex entry that no regional list has.
    "story-progress-beat-elite-four-round-two": "After the Elite Four are beaten a second time",
    "story-progress-oak-eterna-city": "After meeting Professor Oak in Eterna City",
    "story-progress-cure-eldritch-nightmares": (
        "After the sailor's nightmares in Canalave City are cured"
    ),
    "other-regirock-regice-registeel-in-party": (
        "With Regirock, Regice and Registeel in the party"
    ),
    "first-party-pokemon-high-friendship": (
        "With a Pokemon at the front of the party that likes you well enough"
    ),
    # Only ever used where there is no column for them: a gift or a static has no time field,
    # and the Rotom in the Old Chateau is only there after dark.
    "time-morning": "In the morning",
    "time-day": "During the day",
    "time-night": "At night",
    "other-talk-to-cynthias-grandmother": "After talking to Cynthia's grandmother in Celestic Town",
    "other-giratina-not-caught-in-distortion-world": (
        "Only if it was not caught in the Distortion World"
    ),
    # The same fact in Unova, and PokeAPI words it generally because it happens twice there:
    # the cover legendary waits at Dragonspiral Tower if it got away at N's Castle, and Landorus
    # comes back to the Abundant Shrine.
    "special-encounter-couldnt-capture-before": "Only if it got away the first time",
    # Unova's postgame gate. Ghetsis is the last thing in the story, so this is Generation 5's
    # way of saying what other games say with a Hall of Fame.
    "defeated-ghetsis": "After Ghetsis is beaten",
    # And the sequels' three. The first is an ordinary badge gate, the shape Johto's already
    # has above; the other two are one Pokemon standing behind another.
    "story-progress-quake-badge": "After the Quake Badge",
    "story-progress-juniper-cave-of-being": (
        "After Professor Juniper is spoken to in the Cave of Being, which she waits in once the "
        "Champion has been beaten"
    ),
    "other-captured-reshiram-or-zekrom": (
        "Only once the cover legendary has been caught at Dragonspiral Tower"
    ),
    # The Hoenn remakes, where the legendaries of five generations are waiting in places that
    # appear for a day. Which one is standing in a place is decided by the clock or the
    # calendar, and PokeAPI carries that better than a person would write it out: the three
    # beasts take twenty minutes of the hour each, and the lake trio take a stretch of the day.
    "time-minute-00-to-19": "In the first twenty minutes of the hour",
    "time-minute-20-to-39": "In the middle twenty minutes of the hour",
    "time-minute-40-to-59": "In the last twenty minutes of the hour",
    "time-04-00-to-19-59": "Between 4am and 8pm",
    "time-20-00-to-21-59": "Between 8pm and 10pm",
    "time-21-00-to-03-59": "Between 9pm and 4am",
    # And which are a party a player has to have built first. Every one of these is a legendary
    # standing behind another legendary, which is what makes these two games a living dex in a
    # way no game before them was.
    "other-uxie-mesprit-azelf-in-party": "With Uxie, Mesprit and Azelf in the party",
    "other-dialga-or-palkia-in-party": "With Dialga and Palkia in the party",
    "other-castform-in-party": "With a Castform in the party",
    "other-tornadus-thundurus-in-party": "With Tornadus and Thundurus in the party",
    "other-reshiram-zekrom-in-party": "With Reshiram and Zekrom in the party",
    # And Ultra Space asks the same three times over. Two of a trio have to be caught and in the
    # party before the third will appear at the end of a wormhole, which is the oldest habit in
    # the series - the Regis did it in Hoenn - made into the shape of a whole postgame.
    "other-raikou-entei-in-party": "With Raikou and Entei in the party",
    "other-groudon-kyogre-in-party": "With Groudon and Kyogre in the party",
    "other-dialga-palkia-in-party": "With Dialga and Palkia in the party",
    # The Magearna a QR Code unlocks, which Sun and Moon needed written by hand because the
    # source had no row for it at all. It has one for these two, with the condition attached.
    # Worded as a state rather than an instruction, because it is never the only condition on
    # the row: "After entering the Hall of Fame and scan the QR Code" is two sentences that
    # collided, which is the thing :func:`requirement` lowers the second phrase to avoid.
    "other-scan-qr-code": (
        "once this cartridge's region's Magearna QR Code has been scanned with the QR Scanner, "
        "which is region-locked and never Shiny"
    ),
    "story-progress-beat-olivias-trial": "After Olivia's grand trial",
    "other-level-100-pokemon-in-party": "With a Pokemon at level 100 in the party",
    # PokeAPI's slug for this one is mangled, and what it means is the three Regis together.
    "other-nicknamed-cold-item-regice-regirock-registeel3": (
        "With Regirock, Regice and Registeel in the party"
    ),
    "story-progress-defeated-groudon-or-kyogre": (
        "After Groudon or Kyogre has been dealt with at the Cave of Origin"
    ),
    "weekday-sunday": "On a Sunday",
    "weekday-monday": "On a Monday",
    "weekday-tuesday": "On a Tuesday",
    "weekday-wednesday": "On a Wednesday",
    "weekday-thursday": "On a Thursday",
    "weekday-friday": "On a Friday",
    "weekday-saturday": "On a Saturday",
    # Kalos. A Friend Safari's third slot is the one thing in this dataset that got harder to
    # reach after the games came out: it used to open when the friend turned up in the Player
    # Search System, and the network that did that is switched off.
    "friend-safari-slot-3": (
        "Only from the third slot, which opens once that friend has entered their own Hall of "
        "Fame and is playing at the same time as you - since the 3DS network closed in April "
        "2024, that means sitting side by side"
    ),
    # The bins in the Lost Hotel and the Pokemon Village, which hold different things on
    # different days.
    "trash-can-type-daily": "In a bin that is worth checking any day",
    "trash-can-type-tuesday": "In a bin, on a Tuesday",
    "trash-can-type-thursday": "In a bin, on a Thursday",
    # Which of the three a save started with, which in Kalos decides more than the first battle:
    # the legendary bird that roams the region afterwards is chosen by it.
    "starter-chespin": "Only in a save that started with Chespin",
    "starter-fennekin": "Only in a save that started with Fennekin",
    "starter-froakie": "Only in a save that started with Froakie",
    "other-found-11-times-roaming": (
        "Only once it has been met eleven times while roaming, which is when it stops fleeing "
        "and waits here"
    ),
    # The Berry Fields, where each tree keeps its own resident and the colour says which.
    "berry-tree-type-red": "In a red berry tree",
    "berry-tree-type-blue": "In a blue berry tree",
    "berry-tree-type-purple": "In a purple berry tree",
    "berry-tree-type-green": "In a green berry tree",
    "berry-tree-type-yellow": "In a yellow berry tree",
    "berry-tree-type-pink": "In a pink berry tree",
}

#: The Great Marsh rotates two of thirty-two species in each day, and PokeAPI says which of the
#: two slots a species is drawn for. The number is the slot, not the odds.
_GREAT_MARSH = "great-marsh-daily-slot-"

#: The Isle of Armor's Diglett hunt, which is a threshold rather than a yes-or-no.
#:
#: The Diglett Trainer hands over a regional form of something Galar never had at five, ten,
#: twenty, thirty, forty, fifty, seventy-five, a hundred and all hundred and fifty-one, so
#: the number is the condition and writing nine of them out would be writing one sentence
#: nine times.
_DIGLETT = "alolan-diglett-found-"

#: Johto's Safari Zone, where what lives in an area depends on what has been put in it.
#:
#: The number is not a count of objects, quite. An area holds thirty at a time, and each one
#: counts for more once the area has been active long enough - two block points after the first
#: upgrade, three after the second - so what the condition asks for is points. A player reading
#: "at least 35" and counting to thirty would otherwise conclude it cannot be done.
_SAFARI = "johto-safari-blocks-"
_SAFARI_MINIMUM = "-min-"

#: An item in the bag, named as the game names it: a fossil to revive, a keystone to place.
_ITEM = "item-"

#: What a Game Corner window charges. The games that have one price their prizes themselves,
#: so this is only what a game that has not bothered would say.
_COINS = "coins-"

#: Which first partner the save was started with. FireRed and LeafGreen decide which of the
#: three legendary beasts roams Kanto by this and nothing else, so a player who picked
#: Bulbasaur will never meet the other two however long they walk.
_STARTER = "starter-"


def requirement(
    values: list[str],
    *,
    subject: str,
    skip: tuple[str, ...] = (TIME, SEASON),
) -> str | None:
    """Every condition on one row that has no field of its own, as one sentence.

    ``skip`` is which prefixes the caller has somewhere better to put. A wild slot has columns
    for the time and the season, so it takes them out; a gift has neither, and Rotom sits in
    front of its television in the Old Chateau only at night. Dropping that because some other
    record type has a column for it is how a condition disappears.

    Each phrase is written to stand on its own, so the ones after the first are lowered into
    the sentence they are joined onto: "... and After the National Dex opens" reads like two
    sentences that collided.
    """
    phrases = [
        phrase(value, subject=subject)
        for value in values
        if value not in ORDINARY and not (skip and value.startswith(skip))
    ]

    return joined(*phrases)


def joined(*phrases: str | None) -> str | None:
    """Several stand-alone phrases as one sentence, in the order they were given.

    Each phrase is written to stand on its own, so the ones after the first are lowered into
    the sentence they are joined onto: "... and After the National Dex opens" reads like two
    sentences that collided. Empty phrases are left out, and nothing at all is ``None`` rather
    than an empty string, because that is what a record with no requirement carries.
    """
    kept = [one for one in phrases if one]
    if not kept:
        return None

    first, *rest = kept

    return " and ".join([first, *(one[:1].lower() + one[1:] for one in rest)])


def phrase(value: str, *, subject: str) -> str:
    """One condition as a sentence a player can act on."""
    if value in REQUIREMENTS:
        return REQUIREMENTS[value]

    if value.startswith(_DIGLETT):
        found = value.removeprefix(_DIGLETT)
        return (
            f"After finding {found} of the Isle of Armor's 151 hidden Alolan Diglett, which the "
            "Diglett Trainer asks for"
        )

    if value.startswith(_GREAT_MARSH):
        slot = value.removeprefix(_GREAT_MARSH).replace("-of-", " of ")
        return f"Only on days the Great Marsh rotates it in (daily slot {slot})"

    if value.startswith(_SAFARI) and _SAFARI_MINIMUM in value:
        kind, _, points = value.removeprefix(_SAFARI).partition(_SAFARI_MINIMUM)
        return f"With at least {points} {kind} block points in that area of the Safari Zone"

    if value.startswith(_ITEM):
        return pretty(value.removeprefix(_ITEM))

    if value.startswith(_COINS):
        return f"Game Corner prize, {value.removeprefix(_COINS)} coins"

    if value.startswith(_STARTER):
        return f"Only in a save that started with {pretty(value.removeprefix(_STARTER))}"

    # A real restriction with no wording yet: carried through as its slug rather than dropped,
    # and said out loud, because a condition nobody has read is a sentence nobody has checked.
    log.warning("%s has a condition with no wording yet: %s", subject, value)

    return value.replace("-", " ").capitalize()


def stars(values: list[str]) -> int | None:
    """The Max Raid difficulty on one row, as a number, or None if the row is not a raid."""
    found = next((one for one in values if one.startswith(RATING)), None)
    if found is None:
        return None

    return int(found.removeprefix(RATING).removesuffix("-star").removesuffix("-stars"))


def star_range(lowest: int, highest: int) -> str:
    """What a folded run of star ratings reads as on a record."""
    if lowest == highest:
        return f"At {lowest} star" if lowest == 1 else f"At {lowest} stars"

    return f"At {lowest} to {highest} stars"


def of(values: list[str], prefix: str) -> str | None:
    """The one condition with this prefix, without it: ``time-night`` is "night"."""
    found = next((one for one in values if one.startswith(prefix)), None)

    return found[len(prefix) :] if found else None
