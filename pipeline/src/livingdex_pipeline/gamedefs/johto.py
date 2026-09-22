"""What the Johto cartridges have in common, whichever generation they are from.

Two sets of games are set here. HeartGold and SoulSilver are Generation 4 and a version pair,
the way Diamond and Pearl are; Gold, Silver and Crystal are the same region two generations
earlier, and they will read from this file too. That is the difference between this module and
:mod:`kanto`, which says "the Generation 3 Kanto cartridges" in its first line: this one is
about the place, not about the hardware that happened to be in a player's hands.

So the split is drawn twice over:

* What is true of Johto - its Pokedex, where the day care is, what walks in its grass - lives
  here, and a table that belongs to one pair rather than to the region says so in its name.
* What is true of the hardware and the generation - which cartridges trade with which, how far
  the National Dex reaches, whether there is a Pal Park at all - lives with the generation:
  :mod:`ds` for HeartGold and SoulSilver, :mod:`gbc` for Gold, Silver and Crystal.

The factories are named for the hardware for that reason. Nothing here should have to be edited
to add Crystal; something that does have to be edited is a fact about one pair that has been
written down as a fact about Johto.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from ..breeding import EggFrom, breeding_encounters
from ..evolutions import evolution_encounters
from ..games import BuildContext
from ..gifts import GiftDetail, GiftDetails, gift_encounters
from ..models import AcquisitionMethod, DexEntry, DexTarget, Game, GiftKind, TransferEdge
from ..places import LocationNames
from ..sources import bulbapedia
from ..trades import InGameTrade, trade_encounters
from ..wild import RecordedSlot, recorded_encounters, wild_encounters
from . import ds, exclusives, gbc

#: The region itself. Kanto is playable in every game set here, but it is a second half of the
#: map rather than a second region for these entities: a HeartGold cartridge is a Johto game.
REGION = "Johto"

#: Where an egg is left and collected. The same building in every game set here: Gold and Silver
#: put the day care on Route 34 and HeartGold did not move it.
DAY_CARE = "Route 34, Pokemon Day Care"

#: PokeAPI's name for the 251-entry Johto dex, the order Gold, Silver and Crystal list in.
#:
#: Named here and deliberately not used, which is the opposite of what step 2 expected. These
#: games do open their Pokedex in this order - the Johto first partners first - but they print
#: the old numbers beside it, so a Gold player reads Chikorita as #152. The entries those games
#: carry are numbered nationally for that reason; :mod:`gbc` has the whole of it.
#:
#: Kept because it is a true fact about the region and because the next reader will look for it.
ORIGINAL_DEX = "original-johto"

#: PokeAPI's name for the 256-entry Johto dex, the one HeartGold and SoulSilver show.
#:
#: The five extra entries are the Generation 4 evolutions of Pokemon that were already in it -
#: Yanmega, Ambipom, Lickilicky, Tangrowth, Mamoswine - and each one is filed directly behind
#: what it evolves from rather than added at the end. So this is not the original with five more
#: at the back: everything from Yanmega on is renumbered, 150 entries of it, and Celebi is #256
#: where it used to be #251.
#:
#: Which is the opposite of what Sinnoh does. Platinum's 210 keep Diamond's 151 numbers exactly
#: and append the rest, so a player moving between them recognises every number. A Gold player
#: coming to HeartGold does not, and the two dexes need separate names for that reason.
UPDATED_DEX = "updated-johto"


#: The same sentence for each of a set of three: one is taken and the others are somebody
#: else's problem. Three sets of them in these games, which is what makes them unusual.
STARTER_ELM = "Pick one of the three in his lab; the other two take a trade"
STARTER_OAK = "Pick one of the three, after Red is beaten; the other two take a trade"
STARTER_STEVEN = "Pick one of the three, once a Kanto first partner has been taken"

#: Who revives a fossil in these games, wherever it was dug up.
MUSEUM = "A scientist in the Pewter Museum"


#: One battle per tile on the booby-trapped floor of the Rocket hideout, each met once and
#: impossible to run from.
ROCKET_TRAP_FLOOR = "On the trap floor of the hideout, met once and impossible to run from"

#: The wing this half is handed in the middle of its own story.
RADIO_TOWER_WING = "{wing}, from the Radio Tower Director once Team Rocket is beaten"

#: And the one it has to wait for, which is in Kanto and therefore after the Elite Four.
PEWTER_WING = "{wing}, from an old man in Pewter City, which is a Kanto errand and comes later"


#: What only the game knows about each thing HeartGold and SoulSilver hand over or leave
#: standing in one spot.
#:
#: Named for the pair rather than for the region, as the module docstring asks: Gold, Silver and
#: Crystal hand over their own things in their own places, and the two tables will sit side by
#: side without either being mistaken for "Johto's".
#:
#: One table for both halves. What they disagree about - which of two the Game Corner sells,
#: which legendary sleeps in the Embedded Tower, what level the cover legendary is caught at -
#: PokeAPI already files per version, so none of it needs a switch here.
DS_PAIR_GIFTS: dict[str, GiftDetails] = {
    # Johto's own three, from the lab next door to the house you start in.
    "chikorita": GiftDetail(kind=GiftKind.STARTER, npc="Professor Elm", requirement=STARTER_ELM),
    "cyndaquil": GiftDetail(kind=GiftKind.STARTER, npc="Professor Elm", requirement=STARTER_ELM),
    "totodile": GiftDetail(kind=GiftKind.STARTER, npc="Professor Elm", requirement=STARTER_ELM),
    # And two more sets afterwards, which is what makes these games unusual: a player who
    # finishes one has had three first partners handed over rather than one.
    "bulbasaur": GiftDetail(kind=GiftKind.STARTER, npc="Professor Oak", requirement=STARTER_OAK),
    "charmander": GiftDetail(kind=GiftKind.STARTER, npc="Professor Oak", requirement=STARTER_OAK),
    "squirtle": GiftDetail(kind=GiftKind.STARTER, npc="Professor Oak", requirement=STARTER_OAK),
    "treecko": GiftDetail(kind=GiftKind.STARTER, npc="Steven", requirement=STARTER_STEVEN),
    "torchic": GiftDetail(kind=GiftKind.STARTER, npc="Steven", requirement=STARTER_STEVEN),
    "mudkip": GiftDetail(kind=GiftKind.STARTER, npc="Steven", requirement=STARTER_STEVEN),
    # Every fossil of three generations is revived in one museum, and which of them a player
    # holds is the fossil itself, which the encounter's own conditions name. Where each one is
    # dug up is not in PokeAPI and is not guessed at here.
    "omanyte": GiftDetail(kind=GiftKind.FOSSIL, npc=MUSEUM),
    "kabuto": GiftDetail(kind=GiftKind.FOSSIL, npc=MUSEUM),
    "aerodactyl": GiftDetail(kind=GiftKind.FOSSIL, npc=MUSEUM),
    "lileep": GiftDetail(kind=GiftKind.FOSSIL, npc=MUSEUM),
    "anorith": GiftDetail(kind=GiftKind.FOSSIL, npc=MUSEUM),
    "cranidos": GiftDetail(kind=GiftKind.FOSSIL, npc=MUSEUM),
    "shieldon": GiftDetail(kind=GiftKind.FOSSIL, npc=MUSEUM),
    "togepi": GiftDetail(kind=GiftKind.EGG, npc="Professor Elm's assistant"),
    # Primo's three, one egg per save. The password is a set of phrases picked in conversation,
    # printed in magazines at the time and freely known now; nothing about it needs an event.
    "mareep": GiftDetail(kind=GiftKind.EGG, npc="Primo"),
    "wooper": GiftDetail(kind=GiftKind.EGG, npc="Primo"),
    "slugma": GiftDetail(kind=GiftKind.EGG, npc="Primo"),
    "tyrogue": GiftDetail(npc="The Karate King in Mt. Mortar"),
    "sudowoodo": GiftDetail(requirement="Water it with the SquirtBottle"),
    "gyarados": GiftDetail(requirement="The red one, in the middle of the lake"),
    # Three species that are handed over twice in two different places, which is what `where`
    # is for. A table keyed by species alone would have told a player that a slot machine prize
    # came from Bill.
    "eevee": (
        GiftDetail(npc="Bill", where="Goldenrod City, Bills House"),
        GiftDetail(),
    ),
    "dratini": (
        GiftDetail(
            npc="The Master of the Dragon Shrine",
            requirement=(
                "Answer his quiz; all of it right the first time and it knows ExtremeSpeed"
            ),
            where="Dragon's Den",
        ),
        GiftDetail(),
    ),
    "snorlax": (
        GiftDetail(requirement="Wake it with the Poke Flute, on the Kanto radio", where="Route 11"),
        GiftDetail(),
    ),
    # The Embedded Tower, the one place in these games where a legendary waits behind an item
    # rather than behind a story. The orbs are in-game: Mr. Pokemon hands one over once Red is
    # beaten and a Kanto first partner has been taken.
    "kyogre": GiftDetail(requirement="The Blue Orb, from Mr. Pokemon"),
    "groudon": GiftDetail(requirement="The Red Orb, from Mr. Pokemon"),
    "rayquaza": GiftDetail(
        requirement=(
            "The Jade Orb, which Professor Oak gives for being shown a Kyogre and a Groudon "
            "both caught in this tower - so one of the two has to come from the other version"
        ),
    ),
}


#: What only the game knows about each thing Gold and Silver hand over or leave standing in one
#: spot.
#:
#: Named for the pair, as its DS counterpart above is. Crystal moves one of these and adds
#: several of its own, and it will bring its own table beside this one.
#:
#: The Goldenrod Game Corner needs no rows here and neither does Celadon's: PokeAPI carries what
#: each window charges as a condition on the encounter, so "Game Corner prize, 2100 coins" is
#: already written. Ekans at 700 coins is Gold's window and Sandshrew at 700 is Silver's, which
#: is the pair switch reaching a place no grass ever does.
GBC_PAIR_GIFTS: dict[str, GiftDetails] = {
    # Johto's own three, from the lab next door to the house you start in. The same sentence the
    # remake uses, because the remake changed nothing about it.
    "chikorita": GiftDetail(kind=GiftKind.STARTER, npc="Professor Elm", requirement=STARTER_ELM),
    "cyndaquil": GiftDetail(kind=GiftKind.STARTER, npc="Professor Elm", requirement=STARTER_ELM),
    "totodile": GiftDetail(kind=GiftKind.STARTER, npc="Professor Elm", requirement=STARTER_ELM),
    # And no second or third set: Oak hands nothing over in these games and Steven is two
    # generations away. A player of Gold gets one first partner, where a player of HeartGold
    # gets three.
    "togepi": GiftDetail(
        kind=GiftKind.EGG,
        npc="Professor Elm's assistant",
        requirement=(
            "Hatched from the Egg he brings to Violet City, once Mr. Pokemon's errand is done"
        ),
    ),
    "eevee": (
        # Two places, and the table says which is which. This is what `where` is for.
        GiftDetail(
            where="Goldenrod City, Bills House",
            npc="Bill",
            requirement="Meet him in the Ecruteak City Pokemon Center first",
        ),
        # The other is Celadon's window, whose price the encounter already carries.
        GiftDetail(),
    ),
    # Kenya, handed over with Mail attached for a man by the pond on Route 31. What happens to it
    # after the delivery is not something this dataset has to settle: Spearow is in the grass and
    # in the headbutt trees on half of Johto's routes, so no dex entry hangs on the answer.
    "spearow": GiftDetail(
        npc="A guard in the gate north of Goldenrod City",
        requirement="Kenya, handed over holding Mail for a man on Route 31",
    ),
    "shuckle": GiftDetail(
        npc="Mania, in Cianwood City",
        requirement=(
            "Lent for safekeeping; he asks for it back on another day and lets it stay at 150 "
            "friendship, or if you refuse him"
        ),
    ),
    "tyrogue": GiftDetail(npc="The Karate King", requirement="Beat him in Mt. Mortar"),
    "sudowoodo": GiftDetail(requirement="SquirtBottle, on the tree blocking Route 36"),
    "gyarados": GiftDetail(
        requirement="The red one in the Lake of Rage, at the end of the Rocket story"
    ),
    "snorlax": GiftDetail(
        requirement=(
            "The Expn Card's Poke Flute channel on the Pokegear, to wake the one asleep outside "
            "Vermilion City"
        )
    ),
    # The hideout under Mahogany Town, and the two kinds of fixed encounter in it. Three Electrode
    # are wired to the generator on B2F; the trap floor above holds the rest, one battle per tile.
    "electrode": GiftDetail(requirement="One of the three wired to the generator in the hideout"),
    "geodude": GiftDetail(requirement=ROCKET_TRAP_FLOOR),
    "voltorb": GiftDetail(requirement=ROCKET_TRAP_FLOOR),
    "koffing": GiftDetail(requirement=ROCKET_TRAP_FLOOR),
}

#: Which wing each half is handed during its own story, and which it waits for.
#:
#: The neatest version switch in these two games, and it is not a species at all. Gold's Director
#: hands over the Rainbow Wing once Team Rocket is beaten and Silver's hands over the Silver Wing,
#: so Gold meets Ho-Oh at level 40 in the middle of its story and Silver meets Lugia there. The
#: other wing is an old man's in Pewter City, which is Kanto, which is after the Elite Four - and
#: the level the other bird waits at is 70.
GBC_PAIR_WINGS: dict[str, dict[str, str]] = {
    "gold": {
        "ho-oh": RADIO_TOWER_WING.format(wing="Rainbow Wing"),
        "lugia": PEWTER_WING.format(wing="Silver Wing"),
    },
    "silver": {
        "lugia": RADIO_TOWER_WING.format(wing="Silver Wing"),
        "ho-oh": PEWTER_WING.format(wing="Rainbow Wing"),
    },
}


def gbc_gifts(version: str) -> dict[str, GiftDetails]:
    """The gift table as one half of the pair sees it, with the right wing in the right place."""
    wings = {
        species: GiftDetail(requirement=requirement)
        for species, requirement in GBC_PAIR_WINGS[version].items()
    }

    return {**GBC_PAIR_GIFTS, **wings}


#: Why no Generation 2 game hands over a Kanto first partner.
#:
#: Professor Oak is in these games and gives nothing away: his three are the remake's idea. So
#: the only Bulbasaur in a Gold save came out of a Game Boy, through the Time Capsule.
GBC_KANTO_STARTERS = (
    "Nobody hands one over in Generation 2: Oak's lab is a visit rather than a choice. The Time "
    "Capsule is the way in, from Red, Blue or Yellow"
)

#: And why no fossil is revived in them.
#:
#: The Pewter Museum revives fossils in HeartGold and in no game before it. In Generation 2 the
#: Old Amber and the two fossils are not items a player ever holds, so an Omanyte here was an
#: Omanyte somewhere else first.
GBC_NO_FOSSILS = (
    "No fossil is revived in Generation 2: the scientist in the Pewter Museum starts doing that "
    "in the remake. The Time Capsule is the way in, from Red, Blue or Yellow"
)

#: And why Kanto's four legendaries are not in Kanto here.
#:
#: Half the map of these games is Kanto and none of the four is standing in it: the Seafoam
#: Islands, the Power Plant, Mt. Silver and the Cerulean Cave hold nothing. Their own pages say
#: "Time Capsule, Event" for the whole of Generation 2, which is the rare case of a source
#: saying out loud that a game has nothing.
GBC_KANTO_LEGENDS = (
    "Not standing anywhere in these games, Kanto included. The Time Capsule is the way in, from "
    "Red, Blue or Yellow"
)

#: Why nothing in Gold or Silver produces a Mew.
#:
#: The same reasoning as Red's, one generation on: what was handed out went onto cartridges, and
#: a 3DS download is not one of those. What these two have that the cartridges did not is the
#: other end of the Time Capsule - and Red, Blue and Yellow did get two Virtual Console Mews.
GBC_MEW_REASON = (
    "Distribution event only, and none of them reached these releases: the Mews of 1996 to 2000 "
    "went onto cartridges. The Time Capsule is the way in, from a Red, Blue or Yellow that was "
    "given one of the two 2016 Virtual Console Mews"
)

#: And why nothing in them produces a Celebi, which is the entry this generation is named for.
#:
#: Ten distributions between 2000 and 2003, every one of them onto a cartridge. What makes this
#: worth writing down rather than repeating is the exception one game later: Crystal's Virtual
#: Console release turns the GS Ball event on in every language, where the original had it in
#: Japan alone. So a Celebi caught in Ilex Forest in Crystal can be traded to these two, and
#: until Crystal is in the dataset nothing in it produces a Celebi at all.
GBC_CELEBI_REASON = (
    "Distribution event only, and none of them reached these releases: the Celebis handed out "
    "between 2000 and 2003 went onto cartridges. Crystal is the exception in this generation - "
    "its Virtual Console release turns on the GS Ball event that was Japan's alone - so one "
    "caught in Ilex Forest there can be traded across"
)

#: Dex entries no Generation 2 game fills, whichever half of the pair a player owns.
#:
#: Eleven of the seventeen each half cannot produce, and the other six are the version
#: exclusives, which each game names for itself.
GBC_PAIR_UNOBTAINABLE: dict[str, str] = {
    "bulbasaur": GBC_KANTO_STARTERS,
    "charmander": GBC_KANTO_STARTERS,
    "squirtle": GBC_KANTO_STARTERS,
    "omanyte": GBC_NO_FOSSILS,
    "kabuto": GBC_NO_FOSSILS,
    "articuno": GBC_KANTO_LEGENDS,
    "zapdos": GBC_KANTO_LEGENDS,
    "moltres": GBC_KANTO_LEGENDS,
    "mewtwo": GBC_KANTO_LEGENDS,
    "mew": GBC_MEW_REASON,
    "celebi": GBC_CELEBI_REASON,
}


#: What the Bug-Catching Contest holds, which is the one thing in these games PokeAPI has
#: nothing at all for.
#:
#: Every other slot in this dataset comes from PokeAPI's own encounter tables. This one is read
#: off Bulbapedia and written down, because the alternative is a dataset that says a Scyther
#: cannot be caught in Gold - and it can, in the National Park, on a Tuesday.
#:
#: Four of the ten are only ever caught here. Scyther and Pinsir are in no grass in either game;
#: Weedle is Silver's in the wild and Gold's only at the contest, and Caterpie is the other way
#: round. Their evolutions follow from them, which is why Kakuna and Metapod are in the list but
#: not the point of it.
#:
#: The same table for all three releases: Bulbapedia lists the contest identically for Crystal,
#: so it will read this too.
CONTEST = (
    "In the Bug-Catching Contest, held in the National Park on Tuesdays, Thursdays and Saturdays"
)

GBC_CONTEST: tuple[RecordedSlot, ...] = tuple(
    RecordedSlot(
        species=species,
        location="National Park",
        lowest=lowest,
        highest=highest,
        rate_percent=rate,
        requirement=CONTEST,
    )
    for species, lowest, highest, rate in (
        ("caterpie", 7, 18, 20.0),
        ("metapod", 9, 18, 10.0),
        ("butterfree", 12, 15, 5.0),
        ("weedle", 7, 18, 20.0),
        ("kakuna", 9, 18, 10.0),
        ("beedrill", 12, 15, 5.0),
        ("paras", 10, 17, 10.0),
        ("venonat", 10, 16, 10.0),
        ("scyther", 13, 14, 5.0),
        ("pinsir", 13, 14, 5.0),
    )
)


#: What PokeAPI calls Gold and Silver when it says which version group an evolution started in.
#:
#: One group for the two of them, as the remake has one for its two. Crystal is its own, which
#: is worth knowing before its step 5: nothing it evolves differently, but a game that asked for
#: this group would be asking about another game.
GBC_PAIR_VERSION_GROUP = "gold-silver"

#: The seven trades Gold and Silver share, and what each one wants.
#:
#: Generation 2 is the first in the dataset to record who you traded with: a Pokemon that comes
#: over one of these carries an original trainer, where a Generation 1 trade carries the word
#: TRAINER and nothing else. The games store those names in capitals - as they store every name,
#: including the species - so they are written here the way the rest of this dataset writes text.
#:
#: The nicknames are ROCKY, MUSCLE, VOLTY, DON, AEROY, RUNNY and MAGGIE, in the order below.
#: There is no field for them, so they are kept here rather than lost.
#:
#: Crystal adds an eighth - a Xatu called PAUL for a Haunter, in the same house in Pewter City
#: that trades the Rapidash - and changes none of these. The remake is the one that rearranged
#: them: HeartGold hands over a Dodrio where these hand over a Rhydon, and renames every trainer.
GBC_PAIR_TRADES = (
    InGameTrade(gets="onix", wants="bellsprout", location="Violet City", npc="Kyle"),
    InGameTrade(
        gets="machop",
        wants="drowzee",
        location="Goldenrod City, Department Store",
        npc="Mike",
    ),
    InGameTrade(gets="voltorb", wants="krabby", location="Olivine City", npc="Tim"),
    InGameTrade(gets="rhydon", wants="dragonair", location="Blackthorn City", npc="Emy"),
    InGameTrade(gets="aerodactyl", wants="chansey", location="Route 14", npc="Kim"),
    InGameTrade(gets="rapidash", wants="gloom", location="Pewter City", npc="Chris"),
    InGameTrade(gets="magneton", wants="dugtrio", location="Power Plant", npc="Forest"),
)

#: Which babies the day care on Route 34 is the only way to, and what has to be left there.
#:
#: The first eggs in the dataset that are not a remake's. Generation 2 invented breeding and
#: invented the babies that need it, and these six are in no grass in either game: a Pichu is
#: #172 in a dex that also holds the Pikachu it hatches from.
#:
#: Shorter than the remake's list by half, and every difference is a later generation reaching
#: back. HeartGold hatches Wynaut, Happiny, Mantyke, Mime Jr., Munchlax and Bonsly, each behind
#: an incense that does not exist here; and its Elekid may hatch from an Electivire, which these
#: games have never heard of. Tyrogue and Togepi are left out of both tables for the same
#: reason: the Karate King hands one over and Elm's assistant brings the other.
GBC_PAIR_EGGS: dict[str, EggFrom] = {
    "pichu": EggFrom(parents=("pikachu", "raichu")),
    "cleffa": EggFrom(parents=("clefairy", "clefable")),
    "igglybuff": EggFrom(parents=("jigglypuff", "wigglytuff")),
    "smoochum": EggFrom(parents=("jynx",)),
    "elekid": EggFrom(parents=("electabuzz",)),
    "magby": EggFrom(parents=("magmar",)),
}


#: Where the pair's own battle sprites live in the sprite repository.
#:
#: One sheet for the two of them, as every pair in this dataset has. HeartGold and SoulSilver
#: redrew Generation 4's sprites rather than reusing Diamond and Pearl's or Platinum's, so a
#: player of these games saw these pictures and no others - which is the whole point of the
#: step. The set reaches 493, the same as their National Dex.
DS_PAIR_SPRITE_SET = "generation-iv/heartgold-soulsilver"

#: What PokeAPI calls the pair when it says which version group an evolution started in.
#:
#: The two halves are one group, as every pair in this dataset is. It is also the group that
#: brought the last of Generation 4's own evolution methods, so nothing in the series so far is
#: too new for these games.
DS_PAIR_VERSION_GROUP = "heartgold-soulsilver"

#: The ten NPCs who will swap something, and what each one wants.
#:
#: No API carries these. The names are the original trainers the games record on what they hand
#: over, which is how a player can tell a traded Pokemon from a caught one - and four of them
#: are characters a player already knows, because HeartGold gave its new trades to Brock,
#: Jasmine, Lt. Surge and Steven rather than to invented strangers.
#:
#: Named for the pair: Gold and Silver have their own six, in some of the same towns.
DS_PAIR_TRADES = (
    InGameTrade(gets="onix", wants="bellsprout", location="Violet City", npc="Rudy"),
    InGameTrade(
        gets="machop",
        wants="drowzee",
        location="Goldenrod City, Department Store",
        npc="Jose",
    ),
    InGameTrade(gets="voltorb", wants="krabby", location="Olivine City", npc="Richard"),
    InGameTrade(gets="dodrio", wants="dragonair", location="Blackthorn City", npc="Ayana"),
    InGameTrade(gets="magneton", wants="dugtrio", location="Power Plant", npc="Lorenzo"),
    InGameTrade(gets="xatu", wants="haunter", location="Pewter City", npc="Mondo"),
    # A Pikachu for a Pikachu, and the one handed over is foreign - which is worth having for
    # reasons the games never explain and every breeder knows.
    InGameTrade(
        gets="pikachu",
        wants="pikachu",
        location="Saffron City, Magnet Train Station",
        npc="Lt. Surge",
    ),
    InGameTrade(
        gets="beldum",
        wants="forretress",
        location="Saffron City, Silph Co",
        npc="Steven",
    ),
    InGameTrade(
        gets="rhyhorn",
        wants="bonsly",
        location="Diglett's Cave",
        npc="Brock",
        requirement="Saturdays between 5 and 8 in the evening, after he is beaten at Pewter Gym",
    ),
    # The one trader in the dataset who names no price. `wants` is left out rather than filled
    # in with something she never asked for.
    InGameTrade(
        gets="steelix",
        location="Olivine City, Gym",
        npc="Jasmine",
        requirement=(
            "Between 1 and 2 in the afternoon, after she is beaten in a rematch; "
            "she offers it on the second time she is spoken to"
        ),
    ),
)

#: The babies these games ask for that only the day care produces.
#:
#: Johto is where breeding was invented, and the list is still shorter than it looks: Azurill,
#: Budew and Chingling are in its own grass, so an egg is not the only way to one and they are
#: not here. What is left is the six babies of this region that hatch and nothing else, and the
#: six the generation after it added.
#:
#: The incense is Generation 4's doing, and only for the babies it invented: a Marill left in
#: the day care lays another Marill unless a parent holds a Sea Incense, while a Pikachu has
#: always simply laid a Pichu. Getting that backwards would send a player shopping for an item
#: they do not need, or leave them waiting for an egg that will not come.
DS_PAIR_EGGS: dict[str, EggFrom] = {
    # Generation 2's own, which need nothing but two parents.
    "pichu": EggFrom(parents=("pikachu", "raichu")),
    "cleffa": EggFrom(parents=("clefairy", "clefable")),
    "igglybuff": EggFrom(parents=("jigglypuff", "wigglytuff")),
    "smoochum": EggFrom(parents=("jynx",)),
    "elekid": EggFrom(parents=("electabuzz", "electivire")),
    "magby": EggFrom(parents=("magmar", "magmortar")),
    # And Generation 4's, each behind an incense.
    "wynaut": EggFrom(
        parents=("wobbuffet",),
        requirement="A parent has to hold a Lax Incense",
    ),
    "happiny": EggFrom(
        parents=("chansey", "blissey"),
        requirement="A parent has to hold a Luck Incense",
    ),
    "mantyke": EggFrom(
        parents=("mantine",),
        requirement="A parent has to hold a Wave Incense",
    ),
    "mime-jr": EggFrom(
        parents=("mr-mime",),
        requirement="A parent has to hold an Odd Incense",
    ),
    "munchlax": EggFrom(
        parents=("snorlax",),
        requirement="A parent has to hold a Full Incense",
    ),
    # Which is the only way to the Bonsly that Brock wants for his Rhyhorn: the trade asks for
    # one and nothing in these games hands one over.
    "bonsly": EggFrom(
        parents=("sudowoodo",),
        requirement="A parent has to hold a Rock Incense",
    ),
}


#: Never in any game set here, in either generation: the two the series has always handed out
#: rather than hidden. Both are in the Johto dex all the same, which is why they need a reason
#: rather than being quietly absent.
#:
#: What reached one generation is not what reached the other, so the sentence is here and the
#: distributions are named beside the games they were for.
MEW_REASON = "Distribution event only"
CELEBI_REASON = "Distribution event only"

#: What step 7 found for the DS pair, read off each species' *In events* table.
#:
#: Mew came over Wi-Fi rather than over a counter, which is what the generation changed: no
#: queue, no shop, a download. Three of them reached these games.
DS_PAIR_MEW_EVENT = (
    "the Susumu Mew over Japanese Wi-Fi in November 2009 and again in early 2010, and the Fall "
    "2010 Mew over Wi-Fi in English, French, German, Italian and Spanish"
)

#: And Celebi, which is more than a dex entry here: the event one is what puts the GS Ball in
#: the player's hands and Giovanni in Ilex Forest, so the distribution carried a piece of the
#: game with it.
DS_PAIR_CELEBI_EVENT = (
    "the Cinema Celebi in Japan in 2010 and the Winter 2011 Celebi across Europe and the "
    "Americas - the one that puts the GS Ball in Ilex Forest"
)

#: The one version exclusive of the eleven that any event ever covered, and it was not a
#: Pokemon that was handed out but a place to walk: the Sightseeing route for the Pokewalker,
#: which was itself an event download.
DS_PAIR_SIGHTSEEING = (
    "the Sightseeing route for the Pokewalker holds one, and that route was an event download"
)


def only_on(partner: str, event: str | None = None) -> str:
    """Why an entry in this dex is not in this cartridge, when the other half has it."""
    return ds.only_on(partner, event)


def mew_reason(event: str | None) -> str:
    """Why nothing in this game produces a Mew, and which distributions ever reached it."""
    return exclusives.with_event(MEW_REASON, event)


def celebi_reason(event: str | None) -> str:
    """Why nothing in this game produces a Celebi, and which distributions ever reached it."""
    return exclusives.with_event(CELEBI_REASON, event)


def ds_cartridge(
    *,
    game_id: str,
    title: str,
    version: str,
    released: date,
    pair_partner: str,
    sprite_set: str | None = None,
) -> Game:
    """One Johto cartridge on the DS: a Generation 4 cartridge that happens to be set here.

    Named for the hardware rather than called ``cartridge`` outright, because Gold and Silver
    are Johto cartridges too and none of what :mod:`ds` fills in is true of them. They get a
    factory of their own beside this one, reading their own generation's module. The region is
    the one argument both will pass.

    ``pair_partner`` is required: HeartGold and SoulSilver have no third version, so a cartridge
    here always has another half.
    """
    return ds.cartridge(
        game_id=game_id,
        title=title,
        version=version,
        region=REGION,
        released=released,
        sprite_set=sprite_set,
        pair_partner=pair_partner,
    )


def ds_edges(game_id: str) -> list[TransferEdge]:
    """Every route one of the DS pair brings: its own generation's trades, and Pal Park.

    Also named for the hardware. Gold and Silver's routes are nothing like these - a Time
    Capsule back to Generation 1 and Poke Transporter forward into Bank - and none of that is a
    fact about Johto.
    """
    return ds.edges(game_id)


def gbc_release(
    *,
    game_id: str,
    title: str,
    version: str,
    released: date,
    pair_partner: str | None = None,
    sprite_set: str | None = None,
) -> Game:
    """One Johto game on the Game Boy Color: a Generation 2 release that happens to be set here.

    The other half of the split the DS factory above describes, and the two of them are why
    this module is about the place. Almost nothing either generation fills in is true of the
    other: one is a cartridge with a Pal Park and a National Dex of 493, the other is a 3DS
    download with 251 entries and nowhere else to go but Bank. The region is the one argument
    both pass.

    ``pair_partner`` is optional here and required of the DS factory, which is the difference
    between the two sets: Gold and Silver have Crystal beside them, and HeartGold and SoulSilver
    never had a third version.
    """
    return gbc.release(
        game_id=game_id,
        title=title,
        version=version,
        region=REGION,
        released=released,
        sprite_set=sprite_set,
        pair_partner=pair_partner,
    )


def gbc_edges(game_id: str) -> list[TransferEdge]:
    """Every route a Generation 2 release brings: its own trades, and Bank.

    The Time Capsule is not among them, and that is :mod:`gbc`'s doing rather than an omission
    here: Generation 1 declares it, because the limit on it is a fact about that side.
    """
    return gbc.edges(game_id)


def gbc_acquisition_methods(
    context: BuildContext,
    *,
    game_id: str,
    version: str,
    entries: Sequence[DexEntry],
    gifts: Mapping[str, GiftDetails] | None = None,
    version_group: str | None = None,
    trades: Sequence[InGameTrade] = (),
    eggs: Mapping[str, EggFrom] | None = None,
) -> list[AcquisitionMethod]:
    """Every way to get something in one Generation 2 release, whichever of the three it is.

    ``through`` is None rather than 251, and that is the generation rather than the game: a
    release with no National Dex asks for its own dex, which for these is the same 251 either
    way. It is written as None so that the entity stays the thing that decides.

    The tables are arguments rather than constants because the three releases do not agree about
    them, as Generation 1's three did not. Gold and Silver share theirs; Crystal moves a starter
    and adds the Battle Tower's own, and it will bring its own table when it arrives.

    Eggs are a real argument here for the first time in these two generations. Generation 2 is
    where breeding starts, and it is also where the babies that need it arrive - a Pichu is in
    this dex and nothing in the grass holds one.

    The renamed places are not an argument either: all three of these games call the Tin Tower
    the Tin Tower, so :mod:`gbc` holds the table and every release set here reads it. The
    Bug-Catching Contest is the same - one contest, three games - and it is the one part of
    these games PokeAPI has nothing for.
    """
    return acquisition_methods(
        context,
        game_id=game_id,
        version=version,
        entries=entries,
        through=None,
        gifts=gifts,
        version_group=version_group,
        trades=trades,
        eggs=eggs,
        renamed=gbc.RENAMED_PLACES,
        recorded=GBC_CONTEST,
        recorded_from="Bug-Catching_Contest",
    )


def gbc_dex_entries(
    context: BuildContext,
    *,
    game_id: str,
    unobtainable: Mapping[str, str] | None = None,
) -> list[DexEntry]:
    """The 251 a Generation 2 game asks for, Bulbasaur #001 to Celebi #251.

    The National Dex cut off at Celebi rather than Johto's own list, and the reason is in
    :mod:`gbc`: these games list in the Johto order and number in the national one, and a dex
    entry carries the number a player reads off the screen.

    So this is the only dex in the dataset built by cutting the national list short. Every other
    game either has a regional dex whose numbers it shows - Kanto's 151, Hoenn's 202, the
    updated Johto's 256 - or a National Dex behind that regional one. These have a National Dex
    and nothing in front of it.

    Which of the 251 the game cannot produce is the ``unobtainable`` table each game brings,
    and it arrives with step 7.
    """
    reasons = unobtainable or {}
    api = context.require_api()

    return [
        DexEntry(
            game=game_id,
            target=DexTarget(species=species),
            number=number,
            unobtainable_reason=reasons.get(species),
        )
        for number, species in api.pokedex(gbc.DEX, refresh=context.refresh)
        if number <= gbc.DEX_THROUGH
    ]


def gbc_only_on(partner: str, event: str | None = None) -> str:
    """Why an entry in this dex is not in this Generation 2 release, when the other half has it."""
    return gbc.only_on(partner, event)


def updated_dex_entries(
    context: BuildContext,
    *,
    game_id: str,
    unobtainable: Mapping[str, str] | None = None,
) -> list[DexEntry]:
    """The Johto dex as HeartGold and SoulSilver number it: Chikorita #001 to Celebi #256.

    This is the game's own Pokedex, not the list a living dex in it is aiming at. That list is
    the National Dex, which the entity already says it reaches 493 of; this one is what the
    game's own Pokedex shows.

    Both halves show the same 256 entries in the same order, the way Diamond and Pearl share
    their 151: a version pair is one dataset with a switch in it, and the switch is not here.

    Johto's own form questions wait for the shared forms table, which is still empty. Unown has
    twenty-eight shapes in the Ruins of Alph and they change nothing but the look of it; the
    Rotom appliances and the Giratina forme that Platinum brought are in the National Dex these
    games reach but not in this list.
    """
    return _dex_entries(context, game_id=game_id, dex=UPDATED_DEX, unobtainable=unobtainable)


def _dex_entries(
    context: BuildContext,
    *,
    game_id: str,
    dex: str,
    unobtainable: Mapping[str, str] | None,
) -> list[DexEntry]:
    """One of the region's two Pokedexes, as one game shows it."""
    reasons = unobtainable or {}
    api = context.require_api()

    return [
        DexEntry(
            game=game_id,
            target=DexTarget(species=species),
            number=number,
            unobtainable_reason=reasons.get(species),
        )
        for number, species in api.pokedex(dex, refresh=context.refresh)
    ]


def acquisition_methods(
    context: BuildContext,
    *,
    game_id: str,
    version: str,
    entries: Sequence[DexEntry],
    through: int | None,
    gifts: Mapping[str, GiftDetails] | None = None,
    version_group: str | None = None,
    trades: Sequence[InGameTrade] = (),
    eggs: Mapping[str, EggFrom] | None = None,
    renamed: Mapping[str, str] | None = None,
    recorded: Sequence[RecordedSlot] = (),
    recorded_from: str | None = None,
) -> list[AcquisitionMethod]:
    """Every way to get something in one Johto cartridge.

    ``through`` is how far this game's National Dex reaches, and it is an argument rather than a
    constant for the reason the module docstring gives: Gold and Silver reach 251 and HeartGold
    and SoulSilver 493, and neither number is a fact about Johto.

    A table left out is a step nobody has done yet rather than a game with nothing to declare.
    What an NPC will swap for and what evolves into what arrive with the steps that gather them;
    handing this an empty gift table instead would print PokeAPI's bare rows and call it step 4.

    The wild and gift steps read the same encounter tables and walk into the same places, so
    they share one place lookup: Route 34 is named once however many times it comes up. That
    lookup is also where ``renamed`` lands - what these games call a place PokeAPI names after a
    later one - so both steps write the same name down.

    Johto hangs more on its conditions than any region before it. The Pokegear radio changes
    what is in the grass, the Safari Zone changes what is in an area depending on what has been
    put there, the Bug-Catching Contest replaces the National Park for a day, and the headbutt
    trees are three groups a save decides between. All of that is read in :mod:`conditions`,
    which is shared, so Gold and Silver will find most of it already written.
    """
    api = context.require_api()
    # Every species the living dex here asks for, which is not the game's own Pokedex. Kanto is
    # half of these games and none of it is in their 256 entries.
    species = context.living_dex(through=through, entries=entries)
    today = date.today()
    places = LocationNames(api, refresh=context.refresh, renamed=renamed or {})

    found: list[AcquisitionMethod] = [
        *wild_encounters(
            api,
            game_id=game_id,
            version=version,
            species=species,
            retrieved_on=today,
            refresh=context.refresh,
            places=places,
        )
    ]

    if gifts is not None:
        found.extend(
            gift_encounters(
                api,
                game_id=game_id,
                version=version,
                species=species,
                retrieved_on=today,
                details=gifts,
                refresh=context.refresh,
                places=places,
            )
        )

    if version_group is not None:
        found.extend(
            evolution_encounters(
                api,
                game_id=game_id,
                version_group=version_group,
                species=species,
                retrieved_on=today,
                refresh=context.refresh,
            )
        )

    if eggs:
        found.extend(
            breeding_encounters(
                game_id=game_id,
                day_care=DAY_CARE,
                eggs=eggs,
                citation=bulbapedia("Baby_Pok%C3%A9mon", retrieved_on=today),
            )
        )

    if recorded and recorded_from:
        found.extend(
            recorded_encounters(
                game_id=game_id,
                slots=recorded,
                species=species,
                citation=bulbapedia(recorded_from, retrieved_on=today),
            )
        )

    found.extend(
        trade_encounters(
            game_id=game_id,
            trades=trades,
            citation=bulbapedia("In-game_trade", retrieved_on=today),
        )
    )

    return found


def ds_acquisition_methods(
    context: BuildContext,
    *,
    game_id: str,
    version: str,
    entries: Sequence[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something in HeartGold or SoulSilver.

    The two halves differ by one word - which version PokeAPI is asked about - so one function
    answers for both and each game brings its own version name. Two copies of this is how one of
    them gets edited and the other does not.
    """
    return acquisition_methods(
        context,
        game_id=game_id,
        version=version,
        entries=entries,
        through=ds.NATIONAL_DEX_THROUGH,
        gifts=DS_PAIR_GIFTS,
        version_group=DS_PAIR_VERSION_GROUP,
        trades=DS_PAIR_TRADES,
        eggs=DS_PAIR_EGGS,
    )
