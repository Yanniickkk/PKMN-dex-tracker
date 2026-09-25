"""What Pokemon Sword and Shield share: Galar, and the first Pokedex that leaves things out.

Generation 8's first pair, and the first core games built for the Nintendo Switch rather than
brought to it - Let's Go reached the console a year earlier and is Generation 7 remaking Yellow.
These are a new region, a new starting three, and a list that for the first time in the series
does not have room for everything.

**Named for the region, and here the region is this pair and nothing else.** Generation 8 is
these two in Galar, Brilliant Diamond and Shining Pearl in Sinnoh, and Legends: Arceus in Hisui;
they share no Pokedex, no grass and no cable, and what they do share is Pokemon HOME, which
:mod:`home` has held since before any of them existed. So there is nothing left for a ``gen8``
module to say. This is the :mod:`kalos` shape rather than the :mod:`alola` one - one region, one
pair - and the two islands the Expansion Pass adds are Galar's as much as the Wild Area is.

**Dexit, which is what this file is arranged around.** Every game in this dataset before these
two can hold any species old enough for it: the National Dex number is the whole question, and
:class:`NationalDexRangeFilter` is the shape of the answer. Bulbapedia puts the change plainly -
the choice not to make every existing Pokemon available here is the thing fans named after a
referendum - and it is the reason :class:`PresentInTargetDexFilter` was written. :mod:`home`
wrote the sentence down before this module existed - Sword has no entry for this species, and
HOME will not put one there - and this is where it stops being a prediction. Its example had to
change: it named Decidueye, which turns out to be one of the eighty in
:data:`FOREIGN_TO_EVERY_DEX` that these games hold without listing. Chikorita is the one that is
true both ways round.

**The cable reaches the other half and nothing else.** Bulbapedia says it in one line - as with
other games on the Switch, these are not compatible with other games in the same generation
outside of their pairing - so the graph around them is three routes, the count Let's Go has, and
for once with an ordinary way back: a deposit into HOME, and a withdrawal that hands over
whatever this game's own list names.

**And these are the games that changed after they shipped**, which nothing in the series had
done: Bulbapedia counts adding completely new Pokemon through an update among their firsts. The
Galar Pokedex was 400 entries on 15 November 2019; version 1.2.0 on 16 June 2020 brought the
Isle of Armor's 211 and version 1.3.0 on 22 October 2020 the Crown Tundra's 210, and both times
the Pokemon arrived for every player rather than only for the ones who bought the pass - the
pass buys the islands, and the species turn up in the base game and may be traded in without it.
So what this dataset holds is the game as it can be bought and played today, which is version
1.3.x, while :data:`RELEASED` stays the day it first went on sale. That is the decision the
Virtual Console releases got, arriving in a different shape: a game is the thing a player can
sit down with now.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from ..archives import GALAR_SET
from ..breeding import CAUGHT, breeding_encounters, day_care_eggs
from ..evolutions import evolution_encounters
from ..formchanges import FormChange, form_change_encounters, spread
from ..games import BuildContext
from ..gifts import GiftDetail, GiftDetails, gift_encounters
from ..models import (
    AcquisitionMethod,
    AllSpeciesFilter,
    DexEntry,
    DexSource,
    DexTarget,
    Game,
    GameRelease,
    GiftKind,
    SourceCitation,
    TransferDirection,
    TransferEdge,
    TransferMechanism,
)
from ..places import LocationNames
from ..pokeapi import BASE_URL
from ..sources import bulbapedia
from ..trades import InGameTrade, trade_encounters
from ..wild import wild_encounters
from . import exclusives, home

#: The region itself, and the first in the series drawn from the United Kingdom.
REGION = "Galar"

#: Generation 8, which for once nobody has to argue about.
#:
#: Let's Go made that worth saying: two Switch games that are Generation 7 because the species
#: they know are Generation 1's. These two are the console's generation and the series' both -
#: a new region, and the eighty-nine National Dex numbers from Grookey at #810 to Calyrex at
#: #898, which are the first since Melmetal closed Generation 7 at #809.
GENERATION = 8

#: One day, everywhere, in nine languages.
#:
#: The third release in this dataset with no Japanese date to prefer, after Ultra Sun and Ultra
#: Moon and the Let's Go pair: Japan, North America, Australia, Europe, South Korea, Hong Kong
#: and Taiwan all on 15 November 2019, on a game card and as a download.
#:
#: The day it went on sale is not the day it held what it holds now - this module's own
#: docstring says what happened in between - and this field is the first of those two, because
#: it is what orders a picker.
RELEASED = date(2019, 11, 15)

#: The two halves, which are the whole of what these games reach by cable.
#:
#: Named here rather than worked out from each game's ``pair_partner`` for the same reason
#: :data:`lets_go.PAIR` is: the trade between them needs the pair as a set rather than as two
#: games each knowing the other.
PAIR = ("sword", "shield")

#: PokeAPI's name for the version group the two halves share, which their evolution rules hang
#: off. One for the pair: nothing about evolving differs between Sword and Shield.
VERSION_GROUP = "sword-shield"

#: What PokeAPI calls each half when it says which version an encounter belongs to.
#:
#: **Three names per half, which no game in this dataset has needed before.** The source files
#: the two expansions as version groups of their own - ``the-isle-of-armor`` and
#: ``the-crown-tundra`` - each with a version per half, so a Sword player's grass is spread over
#: ``sword``, ``the-isle-of-armor-sword`` and ``the-crown-tundra-sword``. Reading only the first
#: would lose two thirds of the encounters and nothing in the data would say so.
#:
#: That is the source's shape rather than the game's: a player buys an Expansion Pass and walks
#: onto an island, not into another version. So the three are read together and the records they
#: produce are one game's, told apart by where they are.
VERSIONS: dict[str, tuple[str, ...]] = {
    "sword": ("sword", "the-isle-of-armor-sword", "the-crown-tundra-sword"),
    "shield": ("shield", "the-isle-of-armor-shield", "the-crown-tundra-shield"),
}

#: The three lists these games show, and the name each entry is filed under.
#:
#: Three rather than one, which has happened in this dataset once before: X and Y hand a player
#: Central, Coastal and Mountain Kalos, and :attr:`DexEntry.dex` exists because of it. These are
#: that shape again and not quite. Kalos' three are one region cut in thirds and share nothing,
#: so 153 and 153 and 151 add up to the 457 the games ask for. **These three overlap heavily:**
#: 400 and 211 and 210 are 821 entries and 584 species, and Magikarp is #144 in Galar, #42 on
#: the Isle of Armor and #62 in the Crown Tundra - one Pokemon wearing three numbers in one save
#: file, which no game before this pair has done.
#:
#: They are kept apart anyway, which is X and Y's decision applied to a harder case and is what
#: ``every-dex-number-means-one-thing`` has been guarding since: a number that spans the three
#: is a number no player has ever been shown, and the only one available - the National Dex
#: number - would make the grid say #129 where the game says #144. So the app's dex switch
#: offers the three and shows one at a time, the way it does for Kalos.
#:
#: **What that costs is worth saying plainly rather than discovering at step 9.** A collection
#: built on Sword opens on the Galar list, which is 400 tiles of the 584 these games hold; the
#: other 184 are behind the switch, and the eighty in :data:`FOREIGN_TO_EVERY_DEX` are behind
#: nothing. Seeing everything one of these games can hold in one grid is not something this
#: dataset can express, and it is not a gap in Galar - it is the first time a game's Pokedex and
#: a game's boxes have been different lists.
#:
#: Eighty-nine of the 584 are these games' own, Grookey to Calyrex.
DEXES: tuple[tuple[str, str], ...] = (
    ("galar", "Galar"),
    ("isle-of-armor", "Isle of Armor"),
    ("crown-tundra", "Crown Tundra"),
)

#: How many entries the three hold between them, which is not how many species they hold.
#:
#: 821 against 584. The difference is 237 entries that are a species' second or third listing:
#: 101 species are in both the Galar and the Isle of Armor lists, 135 in Galar's and the Crown
#: Tundra's, 13 on both islands, and 12 are in all three.
DEX_TOTAL = 821

#: Species these games can hold that no list of theirs names, and that get no entry here.
#:
#: Bulbapedia counts eighty - Mewtwo, Mew, Celebi, Jirachi, Reshiram, Zekrom and Kyurem among
#: them - and says each can be moved in from HOME although it is in neither the Galar Pokedex
#: nor either island's. Twenty-six of the eighty do have a Sword and Shield Pokedex entry, and
#: it can only be read in HOME and never in the game that holds it.
#:
#: The arithmetic is worth having in one place: 584 species across :data:`DEXES` and eighty that
#: no list names is 664, which is what these two can hold out of the 898 that existed when the
#: Crown Tundra shipped. Dexit is that subtraction.
#:
#: **Step 2 decided against them, and the reason is the same one that keeps the three apart.**
#: A dex entry is a number in a list, and these eighty have no number in any list this game
#: shows - the twenty-six that have a Pokedex entry have one that can only be read in HOME. An
#: entry invented for them would have to be numbered by something no game ever showed, which is
#: the objection X and Y's step 2 raised against running three lists into one.
#:
#: So the dataset says these games hold 584 species, and that is 80 short of the truth. The
#: direction of the error is the safe one - a tile the grid does not draw asks nothing of a
#: player, while a tile it invents asks for something they may not be able to get - and the one
#: place it shows is the withdrawal out of HOME, which reads the target game's list and so
#: refuses eighty species the real service would hand over. No tile turns on that refusal, and
#: it is written down here rather than left for somebody to find in the graph.
#:
#: :mod:`home` used to name Decidueye as the Pokemon Sword has no entry for and HOME will not
#: put there. Decidueye is one of the eighty: the example was true about this dataset and false
#: about the game, and it has been changed to Chikorita, which is in neither list.
FOREIGN_TO_EVERY_DEX = 80




#: What each half calls itself in the other half's reason.
TITLE = {"sword": "Sword", "shield": "Shield"}

#: The one entry neither half produces, and the six distributions that did.
#:
#: Zarude is the Isle of Armor's Mythical Pokemon and nothing in either cartridge makes one: it
#: is not in the grass, not in a den, not in the Max Lair and not handed over. It was given away
#: six times between August 2020 and March 2022 - twice over in three regions, once as itself
#: and once as Dada Zarude, which the film it came with is about.
ZARUDE = exclusives.with_event(
    "Nothing in either half produces one: it is not in the grass, not in a den, not in the Max "
    "Lair and not handed over",
    exclusives.handed_out(
        "the Jungle Zarude of August 2020",
        "the Jungle Dada Zarude of December 2020",
        "four more distributions of those two through to March 2022",
    ),
)

#: What a Wild Area News raid was, said once because ten entries want it.
#:
#: **The strangest thing step 7 found, and it is a way of distributing a Pokemon that only these
#: games have.** Wild Area News pushes a den table to a Switch over the internet for a few days
#: and takes it away again; what is in the den while it lasts is not in the game before or
#: after. The source marks the leftovers of it in the encounter tables - the
#: ``max-den-rarity-special`` condition step 3 found on a handful of Rolling Fields spawns - and
#: Bulbapedia files the rest under each species' own events, which is where these were read.
#:
#: It matters here because four of the raids were run in the half that cannot catch the Pokemon
#: at all: a Shield player could raid a Galarian Farfetch'd and a Galarian Darumaka for one week
#: in March 2020, and a Sword player a Galarian Ponyta and a Rapidash in the same week. Those
#: four are exactly the four forms Regina's trades are split by, covered once each and never
#: again.
def raid(*periods: str) -> str:
    """One sentence for however many of these a species got, which is one or two."""
    if len(periods) == 1:
        return f"a Wild Area News raid of {periods[0]}"

    return "Wild Area News raids of " + " and of ".join(periods)


#: The nineteen species each half can produce and the other cannot, and what once covered them.
#:
#: Worked out at step 5, dated at step 7. ``None`` means what it says in every game file in this
#: dataset: the question was asked and the answer was nothing - no distribution has ever put one
#: of these in the half that lacks it, so a player without a trading partner has no way at all.
#:
#: **Nine of the thirty-eight were covered and twenty-nine were not**, which is the sparsest
#: showing of any pair since Ultra Sun and Ultra Moon. Six of the nine are a Wild Area News raid
#: that lasted a week or a month; the other three are Mystery Gift - Lancer's Shiny Zacian and
#: Arthur's Shiny Zamazenta, which each ran in *both* halves so that neither box legendary is
#: strictly one cartridge's, and Ash's Sirfetch'd from the year the animated series ended.
ONLY_ON: dict[str, dict[str, str | None]] = {
    # Sword's, which is what a Shield player is told they cannot have.
    "sword": {
        "darumaka": exclusives.handed_out(raid("19 to 25 March 2020")),
        "deino": exclusives.handed_out(raid("October 2020")),
        "farfetchd": exclusives.handed_out(raid("19 to 25 March 2020")),
        "pinsir": exclusives.handed_out(raid("6 to 8 August 2021")),
        "sirfetchd": exclusives.handed_out("Ash's Sirfetch'd of September 2022"),
        "zacian": exclusives.handed_out("Lancer's Shiny Zacian of October 2021"),
        # And the twelve nothing ever covered.
        "bagon": None,
        "clauncher": None,
        "gothita": None,
        "jangmo-o": None,
        "mawile": None,
        "omanyte": None,
        "rufflet": None,
        "scraggy": None,
        "seedot": None,
        "solrock": None,
        "stonjourner": None,
        "swirlix": None,
        "turtonator": None,
    },
    # Shield's, which is what a Sword player is told they cannot have.
    "shield": {
        "corsola": exclusives.handed_out(
            "the Hidden Ability Galarian Corsola of June 2020"
        ),
        "larvitar": exclusives.handed_out(raid("28 April to 11 May 2020")),
        "ponyta": exclusives.handed_out(
            "the Hidden Ability Galarian Ponyta of May 2020", raid("19 to 25 March 2020")
        ),
        "sableye": exclusives.handed_out("Kohei Fujida's Sableye of June 2022"),
        "zamazenta": exclusives.handed_out("Arthur's Shiny Zamazenta of October 2021"),
        # And the fourteen nothing ever covered.
        "croagunk": None,
        "cursola": None,
        "drampa": None,
        "eiscue": None,
        "gible": None,
        "goomy": None,
        "heracross": None,
        "kabuto": None,
        "lotad": None,
        "lunatone": None,
        "skrelp": None,
        "solosis": None,
        "spritzee": None,
        "vullaby": None,
    },
}

#: What a line's later stages were covered by, where they had a raid of their own.
#:
#: :func:`reach.spread_unobtainable` gives an entry the reason its own line already carries, so a
#: Zweilous would otherwise inherit Deino's date. These four had raids of their own and the dates
#: differ, so they are written out rather than inherited.
ALSO_RAIDED: dict[str, dict[str, str]] = {
    "sword": {
        "zweilous": exclusives.handed_out(raid("October 2020")),
        "hydreigon": exclusives.handed_out(raid("October 2020")),
    },
    "shield": {
        "pupitar": exclusives.handed_out(raid("28 April to 11 May 2020")),
        "tyranitar": exclusives.handed_out(raid("28 April to 11 May 2020")),
        "rapidash": exclusives.handed_out(raid("December 2020", "19 to 25 March 2020")),
    },
}


def only_on(partner: str, event: str | None = None) -> str:
    """Why an entry in this dex is not in this cartridge, with Generation 8 filled in."""
    return exclusives.only_on(partner, generation=GENERATION, event=event)


def unobtainable_in(game_id: str) -> dict[str, str]:
    """Everything one half cannot produce: the other half's nineteen, and the one neither can.

    Each reason is two sentences where step 7 found something and one where it did not, which is
    the shape every game in this dataset uses: the first says why the cartridge cannot make one,
    the second says what once could. An event does not make an entry obtainable - a raid that ran
    for a week in 2020 is not a way to fill a dex today - it answers the next question.
    """
    other = next(one for one in PAIR if one != game_id)

    return {
        **{species: only_on(TITLE[other], event) for species, event in ONLY_ON[other].items()},
        **{
            species: only_on(TITLE[other], event)
            for species, event in ALSO_RAIDED[other].items()
        },
        "zarude": ZARUDE,
    }


#: The folder both halves draw their pictures from, which is theirs alone.
#:
#: **These games draw no battle sprite, and neither did the two before them.** PokeAPI's sprite
#: repository stops having a battle sprite folder after Generation 6, and what it holds for
#: Generation 8 is a set of box icons and an empty entry for Brilliant Diamond. The Archives
#: have the models, filed under "Sword and Shield models" and named ``8s`` - the same shape
#: Let's Go's ``7p`` turned out to be, and checked the same way rather than guessed at from the
#: number: the description page says "Game model of #810 Grookey from Pokemon Sword and Shield".
#:
#: Not Pokemon HOME's artwork, which the same wiki also keeps and which is a render of the same
#: model. HOME is a service and these are the games; a picture filed under the games is the one
#: a Galar tile should show, and :mod:`archives` says the same thing about Let's Go.
SPRITE_SET = GALAR_SET

#: Three evolutions the source offers and Galar does not have, named because nothing can say it.
#:
#: The same three Let's Go had to name, for the same reason, and finding them twice is what makes
#: them a shape rather than an accident. A Pikachu, a Cubone and an Exeggcute are one Pokemon
#: each; what a Thunder Stone, a level and a Leaf Stone make of them depends on where the player
#: is standing, and the source writes the Alolan outcome as the newer way without naming an
#: Alolan form to start from. Every other Alolan line names its own form on both ends and is left
#: alone: an Alolan Meowth becomes an Alolan Persian here, because the Diglett Trainer hands one
#: over and the detail says ``meowth-alola``.
#:
#: **Measured before it was written.** Handing the evolution reader Galar's regional forms gains
#: seven records and loses three, and the three are exactly these - a Kantonian Raichu, Marowak
#: and Exeggutor, which are what these games actually make.
NOT_AN_EVOLUTION_HERE: dict[str, str] = {
    "raichu-alola": (
        "A Thunder Stone in Galar makes the Kantonian Raichu; the Alolan one is what the Diglett "
        "Trainer hands over for forty of his hidden Diglett"
    ),
    "marowak-alola": (
        "A Cubone levelling up in Galar becomes the Kantonian Marowak; the Alolan one is the "
        "Diglett Trainer's reward for fifty"
    ),
    "exeggutor-alola": (
        "A Leaf Stone in Galar makes the Kantonian Exeggutor; the Alolan one is the Diglett "
        "Trainer's reward for seventy-five"
    ),
}

#: Where the sentences below were read, which is one page for all of them.
FORMS_PAGE = "List_of_Pok%C3%A9mon_with_form_differences"

#: How a form that is not met is come by. A sex needs no line: :mod:`formchanges` answers it.
#:
#: Only what nothing else in this game already records. Galar's regional forms are caught, so
#: the grass and the dens explain them; what is left is the things a player does to a Pokemon
#: they already have.
FORM_CHANGES: dict[str, FormChange] = {
    "slowbro-galar": FormChange(
        requirement=(
            "Use a Galarica Cuff on a Galarian Slowpoke, which a woman on the Isle of Armor "
            "makes from thirty-five Galarica Twigs"
        ),
        where="Isle of Armor, Master Dojo",
    ),
    "slowking-galar": FormChange(
        requirement=(
            "Use a Galarica Wreath on a Galarian Slowpoke, which a woman in the Crown Tundra "
            "makes from fifteen Galarica Twigs"
        ),
        where="Crown Tundra, Freezington",
    ),
    "urshifu-rapid-strike": FormChange(
        requirement=(
            "Train the Kubfu at the Tower of Waters rather than the Tower of Darkness; the "
            "choice is made once and cannot be taken back"
        ),
        where="Isle of Armor",
    ),
    "toxtricity-low-key": FormChange(
        requirement=(
            "Evolve a Toxel whose nature is one of the quiet half - Lonely, Bold, Calm and their "
            "like. The loud half makes the Amped one, and the nature is fixed when it hatches"
        )
    ),
    # Galar's own two, which are one mark under a teacup's base. The Antique Sinistea is the rare
    # one and the pot decides what it becomes: a Cracked Pot on an Antique, a Chipped Pot on a
    # Phony, and using the wrong one makes the wrong Polteageist.
    "sinistea-antique": FormChange(
        requirement=(
            "Catch the rare one. A Phony and an Antique Sinistea are told apart by the mark "
            "stamped under the base, and nothing else about them differs"
        )
    ),
    "polteageist-antique": FormChange(
        requirement=(
            "Use a Cracked Pot on an Antique Sinistea; a Chipped Pot on a Phony one makes the "
            "ordinary Polteageist instead"
        )
    ),
    "calyrex-ice": FormChange(
        requirement=(
            "Put Calyrex and Glastrier together with the Reins of Unity, which is how the two "
            "are caught in the first place and how they come apart again"
        ),
        where="Crown Tundra, Freezington",
    ),
    "calyrex-shadow": FormChange(
        requirement=(
            "Put Calyrex and Spectrier together with the Reins of Unity, which is how the two "
            "are caught in the first place and how they come apart again"
        ),
        where="Crown Tundra, Freezington",
    ),
    **spread(
        FormChange(
            requirement=(
                "Give Silvally the memory of that type, which come with the Type: Null the "
                "League Staff member hands over"
            ),
            where="Wyndon, Battle Tower",
        ),
        "silvally-bug",
        "silvally-dark",
        "silvally-dragon",
        "silvally-electric",
        "silvally-fairy",
        "silvally-fighting",
        "silvally-fire",
        "silvally-flying",
        "silvally-ghost",
        "silvally-grass",
        "silvally-ground",
        "silvally-ice",
        "silvally-poison",
        "silvally-psychic",
        "silvally-rock",
        "silvally-steel",
        "silvally-water",
    ),
    **spread(
        FormChange(
            requirement=(
                "Order the appliance from the Rotom Catalog, which a League Staff member in a "
                "Wyndon house hands over once he has been beaten"
            ),
            where="Wyndon",
        ),
        "rotom-heat",
        "rotom-wash",
        "rotom-frost",
        "rotom-fan",
        "rotom-mow",
    ),
    **spread(
        FormChange(
            requirement=(
                "Spin with a sweet in hand and a Milcery in the party. The cream is decided by "
                "how long and which way the spin went and by the time of day, and the sweet is "
                "whichever one was being held"
            )
        ),
        "alcremie-caramel-swirl-berry-sweet",
        "alcremie-caramel-swirl-clover-sweet",
        "alcremie-caramel-swirl-flower-sweet",
        "alcremie-caramel-swirl-love-sweet",
        "alcremie-caramel-swirl-ribbon-sweet",
        "alcremie-caramel-swirl-star-sweet",
        "alcremie-caramel-swirl-strawberry-sweet",
        "alcremie-lemon-cream-berry-sweet",
        "alcremie-lemon-cream-clover-sweet",
        "alcremie-lemon-cream-flower-sweet",
        "alcremie-lemon-cream-love-sweet",
        "alcremie-lemon-cream-ribbon-sweet",
        "alcremie-lemon-cream-star-sweet",
        "alcremie-lemon-cream-strawberry-sweet",
        "alcremie-matcha-cream-berry-sweet",
        "alcremie-matcha-cream-clover-sweet",
        "alcremie-matcha-cream-flower-sweet",
        "alcremie-matcha-cream-love-sweet",
        "alcremie-matcha-cream-ribbon-sweet",
        "alcremie-matcha-cream-star-sweet",
        "alcremie-matcha-cream-strawberry-sweet",
        "alcremie-mint-cream-berry-sweet",
        "alcremie-mint-cream-clover-sweet",
        "alcremie-mint-cream-flower-sweet",
        "alcremie-mint-cream-love-sweet",
        "alcremie-mint-cream-ribbon-sweet",
        "alcremie-mint-cream-star-sweet",
        "alcremie-mint-cream-strawberry-sweet",
        "alcremie-rainbow-swirl-berry-sweet",
        "alcremie-rainbow-swirl-clover-sweet",
        "alcremie-rainbow-swirl-flower-sweet",
        "alcremie-rainbow-swirl-love-sweet",
        "alcremie-rainbow-swirl-ribbon-sweet",
        "alcremie-rainbow-swirl-star-sweet",
        "alcremie-rainbow-swirl-strawberry-sweet",
        "alcremie-ruby-cream-berry-sweet",
        "alcremie-ruby-cream-clover-sweet",
        "alcremie-ruby-cream-flower-sweet",
        "alcremie-ruby-cream-love-sweet",
        "alcremie-ruby-cream-ribbon-sweet",
        "alcremie-ruby-cream-star-sweet",
        "alcremie-ruby-cream-strawberry-sweet",
        "alcremie-ruby-swirl-berry-sweet",
        "alcremie-ruby-swirl-clover-sweet",
        "alcremie-ruby-swirl-flower-sweet",
        "alcremie-ruby-swirl-love-sweet",
        "alcremie-ruby-swirl-ribbon-sweet",
        "alcremie-ruby-swirl-star-sweet",
        "alcremie-ruby-swirl-strawberry-sweet",
        "alcremie-salted-cream-berry-sweet",
        "alcremie-salted-cream-clover-sweet",
        "alcremie-salted-cream-flower-sweet",
        "alcremie-salted-cream-love-sweet",
        "alcremie-salted-cream-ribbon-sweet",
        "alcremie-salted-cream-star-sweet",
        "alcremie-salted-cream-strawberry-sweet",
        "alcremie-vanilla-cream-berry-sweet",
        "alcremie-vanilla-cream-clover-sweet",
        "alcremie-vanilla-cream-flower-sweet",
        "alcremie-vanilla-cream-love-sweet",
        "alcremie-vanilla-cream-ribbon-sweet",
        "alcremie-vanilla-cream-star-sweet",
        "alcremie-vanilla-cream-strawberry-sweet",
    ),
}

#: The three version groups these two span, which is what their evolutions hang off.
#:
#: One group is what every game before them needed. The source files each expansion as a group
#: of its own and puts real rules in them: **Kubfu becomes an Urshifu in a tower on the Isle of
#: Armor, and that detail is stamped** ``the-isle-of-armor``. Asking only about ``sword-shield``
#: leaves the one Pokemon the whole island is built around with no way to exist.
EVOLUTION_GROUPS = ("sword-shield", "the-isle-of-armor", "the-crown-tundra")

#: Where an egg is left and collected. Two buildings, and the pair is the first to have them in
#: two different kinds of place: one beside a route, one out in the Wild Area.
NURSERY = "Pokemon Nursery, Route 5 or Bridge Field"

#: Bulbapedia's in-game trade tables, which are where all twenty of these were read.
TRADES_PAGE = "In-game_trade"

#: Why eleven of the twenty are one idea, and it is an idea only Galar could have had.
#:
#: Regina stands in the caves of the Isle of Armor and swaps a regional form for the original.
#: Hand her the Galarian Meowth that Galar's own grass is full of and she gives back the
#: Kantonian one; the same for Ponyta, Farfetch'd, Corsola, Zigzagoon, Darumaka, Stunfisk,
#: Weezing, Mr. Mime and Yamask, and for Exeggutor and Marowak it is the Alolan form that goes
#: the other way. **She is the only way any of those originals exists in these games**, which
#: makes eleven trades that each fill a tile nothing else can.
#:
#: Four of the eleven are one half's only, and the reason is the form being handed over rather
#: than the one being handed back: Galarian Ponyta and Galarian Corsola are Shield's, Galarian
#: Farfetch'd and Galarian Darumaka are Sword's, so those four trades cannot be made in the
#: other half at all. That is a version exclusive arriving through a trade counter, which
#: nothing before this pair has done.
REGINA = "Regina"
CAVES = "Random caves across the Isle of Armor"

def wants_the(form: str, species: str) -> str:
    """Why a trade that looks like a species for itself is not.

    :class:`InGameTrade` carries what is wanted as a species, which is what every trade before
    this pair asked for. Eleven of these want a particular face of one and the difference is the
    whole trade - a Galarian Meowth in, a Kantonian Meowth out - so it is said in the
    requirement instead. That is the same place Unova's Basculin would have been answered if
    anybody had ever written down which stripe Kyle hands over.
    """
    return (
        f"The {species} handed over has to be the {form} one, which is the form these games "
        "have; what comes back is the original, and this trade is the only place it exists here"
    )


#: Every in-game trade in Galar, in the order a player meets them.
#:
#: Nine in the base game, two of which hand over a different Pokemon depending on the cartridge,
#: and eleven from Regina in the caves of the Isle of Armor. Twenty, which is more than any game
#: in this dataset before them.
BASE_TRADES: tuple[InGameTrade, ...] = (
    InGameTrade(
        gets="skwovet", wants="bunnelby", location="Motostoke", npc="Haley"
    ),
    InGameTrade(
        gets="meowth",
        wants="meowth",
        location="Turffield Stadium",
        npc="Mattia",
        requirement=wants_the("Galarian", "Meowth"),
    ),
    InGameTrade(gets="cottonee", wants="minccino", location="Hulbury", npc="Grazia"),
    InGameTrade(gets="togepi", wants="toxel", location="Hammerlocke", npc="Holly"),
    InGameTrade(
        gets="yamask",
        wants="yamask",
        location="Ballonlea Stadium",
        npc="Eve",
        requirement=wants_the("Galarian", "Yamask"),
    ),
    InGameTrade(gets="mr-mime", wants="obstagoon", location="Spikemuth", npc="Edmund"),
    InGameTrade(gets="duraludon", wants="frosmoth", location="Wyndon", npc="Kapoor"),
)

#: The two base-game traders who hand over a different Pokemon in each half.
TRADES_BY_HALF: dict[str, tuple[InGameTrade, ...]] = {
    "sword": (
        InGameTrade(gets="hatenna", wants="maractus", location="Stow-on-Side", npc="Romeo"),
        InGameTrade(gets="throh", wants="vanillish", location="Circhester", npc="Grimm"),
    ),
    "shield": (
        InGameTrade(gets="impidimp", wants="maractus", location="Stow-on-Side", npc="Romeo"),
        InGameTrade(gets="sawk", wants="vanillish", location="Circhester", npc="Grimm"),
    ),
}

#: Regina's eleven, and which half each of them can be made in.
#:
#: The seven both halves have, then the two Sword's Galarian forms open and the two Shield's do.
REGINA_TRADES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("meowth", "Galarian", PAIR),
    ("exeggutor", "Alolan", PAIR),
    ("marowak", "Alolan", PAIR),
    ("weezing", "Galarian", PAIR),
    ("mr-mime", "Galarian", PAIR),
    ("zigzagoon", "Galarian", PAIR),
    ("stunfisk", "Galarian", PAIR),
    ("farfetchd", "Galarian", ("sword",)),
    ("darumaka", "Galarian", ("sword",)),
    ("ponyta", "Galarian", ("shield",)),
    ("corsola", "Galarian", ("shield",)),
)


def traders(game_id: str) -> list[InGameTrade]:
    """Every trade one half can make: the seven both have, its own two, and Regina's."""
    return [
        *BASE_TRADES,
        *TRADES_BY_HALF[game_id],
        *(
            InGameTrade(
                gets=species,
                wants=species,
                location=CAVES,
                npc=REGINA,
                requirement=wants_the(form, PRETTY.get(species, species.title())),
            )
            for species, form, halves in REGINA_TRADES
            if game_id in halves
        ),
    ]


#: What a species is called in a sentence, where the slug is not it.
PRETTY = {"mr-mime": "Mr. Mime", "farfetchd": "Farfetch'd"}


#: The people Galar hands things over through, named once because several rows want them.
LEON = "Leon"
CARA_LISS = "Cara Liss"
MUSTARD = "Mustard"
DIGLETT_TRAINER = "the Diglett Trainer"

#: Why the box legendary is caught rather than fought, which is the same in both halves.
HERO = (
    "During the postgame story about Sordward and Shielbert, where it has to be caught for the "
    "story to go on"
)


def fossil(first: str, second: str) -> str:
    """What Cara Liss has to be handed, which for a Galar fossil is two things and not one."""
    return (
        f"Cara Liss puts the Fossilized {first} and the Fossilized {second} together on Route 6. "
        "Galar's four are the first fossils in the series that each take two halves, out of a "
        "set of four, and which two go in decides which of the four comes out"
    )


def lets_go(partner: str) -> str:
    """Why a save file on the same console is a way of getting a Pokemon."""
    return (
        f"Only with a Let's Go, {partner}! save file on the same console. It is the Gigantamax "
        f"{partner}, which cannot evolve, and the only thing in this dataset that another game "
        "gives without anything being transferred"
    )


def temple(ruins: str, asked: str) -> str:
    """What one of the three older giants wants before its door opens."""
    return (
        f"In the {ruins} in the Crown Tundra, which only open if {asked}. Then step on the dots "
        "on the floor and touch the statue"
    )


def split(other: str) -> str:
    """Why only one of the Split-Decision Ruins' two can ever be caught in one save."""
    return (
        "In the Split-Decision Ruins, which need Regirock, Regice and Registeel in the party. "
        "The pattern of dots lit on the floor decides which of the two appears: light its eyes "
        f"rather than {other}'s, because {other} cannot be caught in the same save"
    )


def footprints(colour: str, where: str) -> str:
    """What the Swords of Justice ask, which is fifty of something on the ground."""
    return (
        f"After the base game is finished, collect all 50 of its {colour} footprints for Sonia. "
        f"It then stands at {where}"
    )


def steed(carrot: str, called: str, other: str) -> str:
    """Why Calyrex's two steeds are one choice rather than two Pokemon."""
    return (
        f"Grow an {carrot} Carrot from Carrot Seeds in Freezington and it calls {called}, which "
        f"Calyrex is riding when it challenges the player. {other} cannot be had in the same "
        "save; the Reins of Unity separate the steed from Calyrex afterwards"
    )


#: Bulbapedia's list of these games' event Pokemon, which is where the names of the people come
#: from. PokeAPI carries the method, the place and the level and never who is holding it.
EVENTS_PAGE = "List_of_in-game_event_Pokémon_in_Generation_VIII"

#: What only the game knows about each thing these two hand over or leave standing in one spot.
#:
#: The same shape every game since Ruby has had, and the longest of them: Galar hands over
#: eighteen Pokemon and leaves twenty standing somewhere, and PokeAPI has one word - ``gift`` -
#: for a first partner, a revived fossil and a present from a stranger alike.
#:
#: **The fossils are the sharpest thing in the table, and they are new to the series.** Every
#: fossil from the Helix to the Sail is one item, revived into one Pokemon. Galar's four are
#: made of *two* apiece, from a set of four halves - a bird, a fish, a drake and a dino - and
#: which two go in decides which of the four comes out. Cara Liss puts them together on Route 6
#: and does not care that a Dracovish is a fish's head on a drake's legs. The source says it
#: plainly, two ``item-fossilized-`` conditions on one row, and it is the one place in this
#: table where a sentence had to be written rather than borrowed.
#:
#: **Three ways of being handed a Pokemon that only exist because of another game.** A Let's Go
#: save on the same console is worth a Pikachu or an Eevee at the Meetup Spot - which half
#: depends on which Let's Go - and both are the Gigantamax ones that cannot evolve. That is the
#: only thing in this dataset where one game's save file is a way to get a Pokemon in another,
#: and it is not a transfer: nothing moves, somebody just looks and hands one over.
#:
#: **And the Crown Tundra's legendaries are a quiz.** Three of the five giants want something of
#: the player before the door opens - an Everstone in the party, a Cryogonal walking behind
#: them, a whistle - and PokeAPI knows none of it, so those three sentences are read off the
#: wiki. The two behind them are a choice: the dots on the floor of the Split-Decision Ruins
#: make either Regieleki or Regidrago and never both, the same way the carrot grown in
#: Freezington makes either Glastrier or Spectrier.
GIFTS: dict[str, GiftDetails] = {
    # Galar's three, which Leon presents in Postwick once he has been walked home.
    **{
        species: GiftDetail(
            kind=GiftKind.STARTER,
            npc=LEON,
            requirement="Pick one of the three in Postwick; the other two take a trade",
        )
        for species in ("grookey", "scorbunny", "sobble")
    },
    # And the fourth, which is the same man once he has stopped being Champion: a Charmander in
    # a Poke Ball in his room, with the Gigantamax Factor on it.
    "charmander": GiftDetail(kind=GiftKind.NPC_GIFT, npc=f"{LEON}, in his room"),
    # The Isle of Armor's pair, which is a choice of two rather than of three.
    **{
        species: GiftDetail(
            kind=GiftKind.NPC_GIFT,
            npc="Honey",
            requirement=(
                "After Mustard's first trial at the Master Dojo, pick Bulbasaur or Squirtle; "
                "the other takes a trade"
            ),
        )
        for species in ("bulbasaur", "squirtle")
    },
    # Cara Liss on Route 6, and the two halves each of her four needs.
    **{
        species: GiftDetail(
            kind=GiftKind.FOSSIL, npc=CARA_LISS, requirement=fossil(*halves)
        )
        for species, halves in (
            ("dracovish", ("Drake", "Fish")),
            ("dracozolt", ("Drake", "Bird")),
            ("arctovish", ("Dino", "Fish")),
            ("arctozolt", ("Dino", "Bird")),
        )
    },
    "kubfu": GiftDetail(kind=GiftKind.NPC_GIFT, npc=MUSTARD),
    "porygon": GiftDetail(
        kind=GiftKind.NPC_GIFT,
        npc="Hyde",
        requirement="After Mustard is beaten at the Battle Court on the Isle of Armor",
    ),
    "toxel": GiftDetail(kind=GiftKind.NPC_GIFT, npc="a Breeder in the Route 5 Nursery"),
    "type-null": GiftDetail(kind=GiftKind.NPC_GIFT, npc="a League Staff member"),
    # The Diglett Trainer's other six, which are regional forms of things Galar never had. How
    # many Diglett each one costs is the condition's to say, and :mod:`conditions` says it once.
    **{
        species: GiftDetail(kind=GiftKind.NPC_GIFT, npc=DIGLETT_TRAINER)
        for species in (
            "meowth", "vulpix", "sandshrew", "raichu", "marowak", "exeggutor", "diglett",
        )
    },
    "slowpoke": GiftDetail(
        kind=GiftKind.NPC_GIFT,
        npc=DIGLETT_TRAINER,
        requirement=(
            "After ten of the Isle of Armor's 151 hidden Alolan Diglett have been found. This is "
            "the Kantonian Slowpoke, which is not the one Galar's own grass holds"
        ),
    ),
    "pikachu": GiftDetail(
        kind=GiftKind.NPC_GIFT,
        npc="a man at the Wild Area Station",
        requirement=lets_go("Pikachu"),
    ),
    "eevee": GiftDetail(
        kind=GiftKind.NPC_GIFT,
        npc="a woman at the Wild Area Station",
        requirement=lets_go("Eevee"),
    ),
    # --- and the ones standing somewhere -------------------------------------------------------
    "eternatus": GiftDetail(
        requirement=(
            "At the climax of the story, in a Max Raid Battle alongside Hop and the hero of the "
            "other half's box. The throw afterwards cannot miss"
        )
    ),
    "zacian": GiftDetail(requirement=HERO),
    "zamazenta": GiftDetail(requirement=HERO),
    "regirock": GiftDetail(
        requirement=temple("Rock Peak Ruins", "a party Pokemon holds an Everstone")
    ),
    "regice": GiftDetail(
        requirement=temple(
            "Iceberg Ruins", "the Pokemon walking behind the player is a Cryogonal"
        )
    ),
    "registeel": GiftDetail(
        requirement=temple("Iron Ruins", "the player whistles at the door")
    ),
    "regieleki": GiftDetail(requirement=split("Regidrago")),
    "regidrago": GiftDetail(requirement=split("Regieleki")),
    "cobalion": GiftDetail(
        requirement=footprints("dark blue", "an island in the Frigid Sea")
    ),
    "terrakion": GiftDetail(requirement=footprints("grey", "Lakeside Cave")),
    "virizion": GiftDetail(requirement=footprints("green", "Giant's Bed")),
    "spiritomb": GiftDetail(
        requirement=(
            "Talk to the tombstone at Ballimere Lake, then to 32 different players, then to the "
            "tombstone again"
        )
    ),
    "glastrier": GiftDetail(requirement=steed("Iceroot", "Glastrier", "Spectrier")),
    "spectrier": GiftDetail(requirement=steed("Shaderoot", "Spectrier", "Glastrier")),
    "calyrex": GiftDetail(
        requirement=(
            "At the end of the Crown Tundra's story, riding whichever steed the carrot grown in "
            "Freezington called. The two are caught in one ball and the Reins of Unity separate "
            "them afterwards"
        )
    ),
}


def cartridge(
    *,
    game_id: str,
    title: str,
    version: str,
    pair_partner: str,
    sprite_set: str | None = SPRITE_SET,
) -> Game:
    """One half of the pair, with everything the two of them agree about filled in.

    No ``national_dex_through``, and here that is the wrong question rather than an unfilled
    answer. The field says how far a living dex in this game reaches, and for every game before
    Let's Go the answer was a number. These hold a list instead: Sword keeps a Bulbasaur and
    cannot keep a Chikorita, and no number separates those two. :class:`DexSource.GAME_DEX` is
    the answer, and step 2 fills it in.

    ``sprite_set`` is :data:`SPRITE_SET`, which step 6 filled in: these games draw no battle
    sprite at all, so what a Galar tile shows is a render of the model, off the Archives.
    """
    return Game(
        id=game_id,
        title=title,
        version=version,
        generation=GENERATION,
        region=REGION,
        release=GameRelease.CARTRIDGE,
        released=RELEASED,
        national_dex_through=None,
        dex_source=DexSource.GAME_DEX,
        pair_partner=pair_partner,
        sprite_set=sprite_set,
    )


def dex_entries(
    context: BuildContext,
    *,
    game_id: str,
    unobtainable: Mapping[str, str] | None = None,
) -> list[DexEntry]:
    """All three Galar Pokedexes, each entry saying which of them it is numbered in.

    One function for the two halves, because the two halves show the same three lists in the
    same order with the same numbers. A version pair splits what can be *caught*, not what is
    listed, and that has been true since Red and Blue; what differs between Sword and Shield is
    steps 3 to 5, and the ``unobtainable`` table each game brings once step 7 knows what to put
    in it.

    The order is the order a player meets them - Galar, then the Isle of Armor, then the Crown
    Tundra - which is release order and also the order the Pokedex app shows its tabs in.

    Nothing here carries a form. These lists number species, and what Galar adds - Gigantamax,
    the Galarian forms, Alcremie's creams and sweets - is the shared forms table's, waiting for
    step 8 to say which of it these games really have.
    """
    reasons = unobtainable or {}
    api = context.require_api()

    return [
        DexEntry(
            game=game_id,
            target=DexTarget(species=species),
            dex=name,
            number=number,
            unobtainable_reason=reasons.get(species),
        )
        for dex, name in DEXES
        for number, species in api.pokedex(dex, refresh=context.refresh)
    ]


def acquisition_methods(
    context: BuildContext,
    *,
    game_id: str,
    entries: Sequence[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way one of these two hands a player a Pokemon. Step 3, and nothing after it yet.

    The species asked about are the game's own 584 and not a National Dex slice, which is what
    :meth:`BuildContext.living_dex` does when a game has no National Dex to slice. The three
    lists name 821 entries between them and that method deduplicates, so Magikarp is asked about
    once rather than three times.

    **What Galar brings that no grass before it had.** Weather: nine states of the sky, each its
    own table, and the first use of a field that has been on :class:`WildAcquisition` since it
    was written. Two ways of meeting a Pokemon that are not a place at all - a Max Raid den and
    the Crown Tundra's Dynamax Adventures - which between them are the only source in these
    games for most of the legendaries of the six generations before. And four overworld methods
    where Let's Go had three, because the source separates what stands still from what wanders a
    fixed patch, what comes up out of the ground, and what chases a player into the water.

    Gifts, statics and the sixteen in-game trades are skipped here and are steps 4 and 5: the
    fossils, the Master Dojo's two, the Regis' footprints, the carrots Calyrex's steed wants,
    and the Pokemon a Let's Go save on the same console hands over.
    """
    api = context.require_api()
    species = context.living_dex(through=None, entries=entries)
    places = LocationNames(api, refresh=context.refresh)

    found = [
        *wild_encounters(
            api,
            game_id=game_id,
            version=VERSIONS[game_id],
            species=species,
            forms=context.forms_here(),
            refresh=context.refresh,
            places=places,
        ),
        *gift_encounters(
            api,
            game_id=game_id,
            version=VERSIONS[game_id],
            species=species,
            details=GIFTS,
            forms=context.forms_here(),
            refresh=context.refresh,
            places=places,
        ),
        *trade_encounters(
            game_id=game_id,
            trades=traders(game_id),
            citation=bulbapedia(TRADES_PAGE, retrieved_on=date.today()),
        ),
        *evolution_encounters(
            api,
            game_id=game_id,
            version_group=EVOLUTION_GROUPS,
            species=species,
            forms=context.forms_here(),
            all_forms=context.forms,
            excluded=NOT_AN_EVOLUTION_HERE,
            refresh=context.refresh,
        ),
        *form_change_encounters(
            game_id=game_id,
            forms=context.forms_here(),
            changes=FORM_CHANGES,
            citation=bulbapedia(FORMS_PAGE, retrieved_on=date.today()),
        ),
    ]

    # Last, and worked out from what the steps above came to rather than from a table: a nursery
    # can only be asked for what nothing else here produces.
    return [
        *found,
        *breeding_encounters(
            game_id=game_id,
            day_care=NURSERY,
            eggs=day_care_eggs(
                api,
                chains={
                    one.id: one.evolution_chain
                    for one in context.species
                    if one.id in set(species)
                },
                caught={one.target.species for one in found if one.kind in CAUGHT},
                evolved={one.target.species for one in found if one.kind == "evolution"},
                refresh=context.refresh,
            ),
            citation=SourceCitation(
                source="pokeapi",
                url=f"{BASE_URL}/evolution-chain",
                retrieved_on=api.retrieved_on(f"{BASE_URL}/evolution-chain"),
            ),
        ),
    ]


def trade_edges(game_id: str) -> list[TransferEdge]:
    """The one cable these games have, which runs to the other half of the pair.

    Bulbapedia states the limit in a line: as with other games on the Switch, these are not
    compatible with other games in the same generation outside of their pairing. So there is no
    route to Brilliant Diamond, none to Legends: Arceus, and none to the two Let's Go games that
    share the console - everything else goes by way of HOME.

    Local wireless, the internet, Surprise Trade and a Link Code are four ways of doing one
    thing and the graph holds it once. What this edge does not say is that HOME will move a
    Pokemon between two Sword and Shield save files on the same console, profiles included:
    that is a route from a game to itself, and a graph of games has nowhere to draw it.
    """
    return [
        TransferEdge(
            **{"from": game_id},
            to=partner,
            mechanism=TransferMechanism.TRADE,
            direction=TransferDirection.BOTH_WAYS,
            filter=AllSpeciesFilter(),
        )
        for partner in PAIR
        if partner != game_id
    ]


def edges(game_id: str) -> list[TransferEdge]:
    """Every route one of these two brings: the cable to its other half, and HOME both ways.

    Three, which is the count Let's Go has and not the same three. Those two got a withdrawal
    that asks where a Pokemon started, because HOME hands them back only what they made
    themselves. These get :func:`home.home_edges`, the ordinary pair - the deposit that takes
    anything and the withdrawal that reads the target's own list - which is the function that
    was written when Bank and HOME were built and has had nothing to describe until now.

    **Registering these two lights nothing that was waiting**, and for once that is a finding
    rather than an apology. Every game in the dataset that can reach them reaches HOME instead,
    because HOME is the only door Generation 8 has: a Pokemon caught in Red arrives here by
    Poke Transporter, Bank, HOME and then Sword, and not one edge on that route had to be told
    these games exist.

    One route is deliberately not here, and it is the Let's Go one again: a Pokemon sent into
    HOME from Pokemon GO can be withdrawn into these games, and GO is not a game this dataset
    holds. :mod:`home` says why, and nothing about Galar changes it.
    """
    return [*trade_edges(game_id), *home.home_edges(game_id)]
