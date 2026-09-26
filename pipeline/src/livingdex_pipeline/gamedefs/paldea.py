"""What Pokemon Scarlet and Violet share: Paldea, and a game that is set in three places.

Generation 9's first pair, and the last pair in this dataset - Legends: Z-A closes the
generation alone, and it was written first because it came out last. These two are a new
region, a new starting three, and the second pair in the series whose boxes hold a list rather
than everything up to a number.

**Galar's shape, three years on, and almost detail for detail.** Three Pokedexes kept apart,
two of them brought by an expansion the source files as version groups of its own, no National
Pokedex, a handful of species the games hold without listing anywhere, and HOME as the only
door. :mod:`galar` answered every one of those questions once already; this module's job is to
say where the answer is the same and where it is not, rather than to answer them again.

**Where it is not the same is the map.** The Isle of Armor and the Crown Tundra are Galar -
islands off a region the base game is already set in. Kitakami is a land of its own in the east,
and Blueberry Academy is in **Unova**, which is the region :mod:`unova` holds for Black and
White. Bulbapedia counts it among this pair's firsts: they take place in three separate
territories, and they are the first core series games since HeartGold and SoulSilver to feature
more than one playable region. :mod:`johto` settled what to do with that in one line - Kanto is
a second half of the map rather than a second region for these entities, and a HeartGold
cartridge is a Johto game - so these are Paldea games, and :data:`REGION` says so once.

**And the pair is softer than any pair before it**, which is step 4's problem and is written
down here because it is a fact about what these two are. Most of their version exclusives can be
caught by a player of the other half who joins a Union Circle or a Tera Raid Battle; only
Koraidon and Miraidon really have to be traded for. Every pair since Red and Blue has meant "one
half catches these and the other catches those", and this one means it less than the words
suggest.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from ..archives import HOME_SET
from ..breeding import CAUGHT, breeding_encounters, day_care_eggs
from ..encountertables import paldea_encounters, paldea_fixed
from ..evolutions import evolution_encounters
from ..formchanges import FormChange, form_change_encounters, spread
from ..games import BuildContext
from ..gifts import RecordedGift, recorded_gifts
from ..models import (
    AcquisitionMethod,
    AllSpeciesFilter,
    DexEntry,
    DexSource,
    DexTarget,
    EncounterMethod,
    Game,
    GameRelease,
    GiftKind,
    TransferDirection,
    TransferEdge,
    TransferMechanism,
)
from ..sources import ReadByHand
from ..trades import InGameTrade, trade_encounters
from . import exclusives, home

#: The region itself, and the first in the series drawn from the Iberian Peninsula.
#:
#: One name for a game played in three places. Kitakami is its own land and Blueberry Academy is
#: in Unova, and the source agrees with the choice made here rather than forcing it: all three
#: of this game's version groups carry ``paldea`` as their only region, the expansions included.
#: :mod:`johto` wrote the rule this follows - Kanto is playable in every game set there and a
#: HeartGold cartridge is still a Johto game - and this is the first pair since those two that
#: the rule has had to be applied to.
REGION = "Paldea"

#: Generation 9, which these two open and Legends: Z-A closes.
#:
#: The National Dex numbers from Sprigatito at #906 onwards are these two games' own, and they
#: are the last the series has added here: Legends: Z-A closes the generation without adding a
#: species of its own.
GENERATION = 9

#: One day, everywhere, in nine languages.
#:
#: Japan, North America, Australia, Europe, South Korea, Hong Kong and Taiwan all on 18 November
#: 2022. By this point in the series it is the norm rather than the exception, and the field is
#: the day it first went on sale rather than the day it held what it holds now - which is
#: :mod:`galar`'s decision, taken for the same reason and with the same two expansions behind
#: it.
#:
#: There is a Nintendo Switch 2 edition by way of a version update, and it is not a second
#: entity here any more than a console revision ever is.
RELEASED = date(2022, 11, 18)

#: The two halves, which are the whole of what these games reach by cable.
#:
#: Named here rather than worked out from each game's ``pair_partner``, for the reason
#: :data:`galar.PAIR` and :data:`lets_go.PAIR` are: the trade between them needs the pair as a
#: set rather than as two games each knowing the other.
PAIR = ("scarlet", "violet")

#: The letter each half fills the Games column with on a location page.
#:
#: Read rather than assumed, which is Hoenn's lesson on a third table: both letters are written
#: on every row and the answer is whether the cell behind them is coloured in. 120 rows on
#: these pages are Scarlet's alone and 151 are Violet's.
LETTERS = {"scarlet": "S", "violet": "V"}

#: PokeAPI's name for the version group the two halves share, which their evolution rules hang
#: off. One for the pair: nothing about evolving differs between Scarlet and Violet.
VERSION_GROUP = "scarlet-violet"

#: What PokeAPI calls each half when it says which version an encounter belongs to.
#:
#: **Three names per half, exactly as Sword and Shield have.** The source files the two halves
#: of The Hidden Treasure of Area Zero as version groups of their own - ``the-teal-mask`` at
#: order 28 and ``the-indigo-disk`` at order 29, each with a version per half - so a Scarlet
#: player's grass is spread over ``scarlet``, ``the-teal-mask-scarlet`` and
#: ``the-indigo-disk-scarlet``. Reading only the first would lose Kitakami and the Terarium and
#: nothing in the data would say so.
#:
#: That is the source's shape rather than the game's: a player buys a DLC and takes a school
#: trip, not another version. So the three are read together and the records they produce are
#: one game's, told apart by where they are.
VERSIONS: dict[str, tuple[str, ...]] = {
    "scarlet": ("scarlet", "the-teal-mask-scarlet", "the-indigo-disk-scarlet"),
    "violet": ("violet", "the-teal-mask-violet", "the-indigo-disk-violet"),
}

#: The three lists these games show, and the name each entry is filed under.
#:
#: **Galar's count and Galar's trap, and step 2 is where it gets checked rather than assumed.**
#: Three lists that each start at #001, so an entry that does not name its list is not a fact
#: about anything - which is why :attr:`DexEntry.dex` exists and why
#: ``every-dex-number-means-one-thing`` has been guarding it since X and Y.
#:
#: Whether the three overlap is the open question. Sword and Shield's three do, heavily: 821
#: entries and 584 species. Legends: Z-A's two do not overlap at all. 400 + 200 + 243 is 843
#: entries, and how many species that is, is step 2's to count rather than this file's to guess.
#:
#: The order is the order a player meets them - Paldea, then Kitakami, then Blueberry - which is
#: release order and also the order the Pokedex app shows its tabs in.
DEXES: tuple[tuple[str, str], ...] = (
    ("paldea", "Paldea"),
    ("kitakami", "Kitakami"),
    ("blueberry", "Blueberry"),
)

#: How many entries the three hold between them, which is not how many species they hold.
#:
#: 400 + 200 + 243 = 843 entries and **664 species**, read off the source's own three Pokedexes
#: and counted rather than guessed. The difference is 179 entries that are a species' second or
#: third listing: 101 species are in both the Paldea and Kitakami lists, 69 in Paldea's and
#: Blueberry's, 13 in the two expansions', and 4 in all three.
#:
#: Galar's shape, and almost Galar's arithmetic - 821 entries and 584 species there, against 843
#: and 664 here. Legends: Z-A, in between the two, is the one game with several lists where
#: there is nothing to subtract at all.
DEX_TOTAL = 843

#: How many species the three lists name between them, which is what a collection asks for.
#:
#: The number the three-list shape makes worth stating separately, for the reason
#: ``every-dex-number-means-one-thing`` exists: 843 tiles would be 179 of them drawn twice.
DEX_SPECIES = 664

#: Species these games can hold that no list of theirs names, and that get no entry here.
#:
#: **Galar's shape again, and its own number.** The article says only Pokemon in the three
#: Pokedexes and "a select few" foreign ones may be transferred in, and those two words link to
#: a section of the Paldea list - *Compatible Pokemon not in any Scarlet and Violet Pokedex* -
#: which is kept as three tables by the version each became compatible in: 60 since 1.0.0, 6
#: since 2.0.1 and 24 since 3.0.0. **Ninety rows, and sixty-nine of them are a species no list
#: names**; the other twenty-one are a form of a species a list does name, an Alolan Raichu
#: beside a listed Raichu.
#:
#: So the arithmetic is 664 listed species and 69 unlisted, which is **733 these two can hold**
#: against Galar's 664. The leftover is smaller than Galar's eighty and the games are much
#: larger, which is the whole story of the two DLC packs.
#:
#: **Step 2 decided against them, the way Galar's step 2 did, and for its reason rather than by
#: following it.** A dex entry is a number in a list, and these sixty-nine have no number in any
#: list these games show; an entry invented for them would have to be numbered by something no
#: player was ever shown. The direction of the error is the safe one - a tile the grid does not
#: draw asks nothing of a player, while a tile it invents asks for something they may not be
#: able to get - and the one place it shows is the withdrawal out of HOME, which reads the
#: target game's list and so refuses sixty-nine species the real service would hand over.
#:
#: **And the page checks itself, which is why the count can be trusted.** It keeps a fourth
#: table of Pokemon *formerly* not in any of these Pokedexes - 64 rows, the ones a DLC list
#: later took in - and every one of those 64 is in one of the three lists today. A page that
#: records its own corrections is a page whose current section is worth counting.
FOREIGN_TO_EVERY_DEX = 69

#: There is no National Pokedex here, and the boxes hold a list rather than everything up to a
#: number.
#:
#: The fourth game running to leave this empty, and the second pair. What a box can hold is the
#: three lists in :data:`DEXES` and the leftover in :data:`FOREIGN_TO_EVERY_DEX`.
NATIONAL_DEX_THROUGH = None

#: What the three lists are made of, written down because it is the one thing step 2 found that
#: no arithmetic would have shown.
#:
#: **Twenty of the 843 rows name a form rather than a species, and not the species' default
#: one.** Fifteen of the twenty are Blueberry's, which is the Terarium doing what it was built
#: to do: the Indigo Disk's biomes are stocked with Alolan Sandshrew, Galarian Slowpoke and
#: Hisuian Qwilfish, and the list numbers those rather than the originals. Kitakami numbers a
#: White-Striped Basculin and a **Bloodmoon Ursaluna**, and Paldea a Paldean Wooper, a Combat
#: Breed Paldean Tauros and a Family of Three Maushold.
#:
#: A further 29 rows name a form and it *is* the species' default - an Icy Snow Vivillon, a
#: Midday Lycanroc, a Baile Oricorio - which costs nothing, and is the same harmless pattern
#: Legends: Z-A's step 2 found 26 of.
#:
#: **The twenty are not harmless, and Ursaluna is the sharpest of them.** These lists number
#: species in this dataset, so the entry says ``ursaluna`` while Kitakami's #196 is the Bloodmoon
#: one - and the ordinary Ursaluna is in the leftover, unlisted. The species-level entry is the
#: exact inverse of the game's own row. The same inversion runs the other way in the leftover,
#: where an Alolan Raichu is a stranger beside a listed Raichu.
#:
#: That is the known cost of a species-level dex, paid here more than anywhere before, and it is
#: **step 8's to settle** rather than this step's: a form is not a dex entry, and which of these
#: forms these games really have is the question that step asks.
LISTS_THAT_NAME_A_FORM = 20

#: The folder both halves draw their pictures from, which is not theirs alone.
#:
#: **These games have no sheet of their own worth the name.** The Archives' category for their
#: models holds two files, where Sword and Shield's holds one per species: the Generation 9
#: numbering runs to four digits - ``Spr_9s_0726.png`` answers where ``Spr_9s_001.png`` does not
#: - and almost nothing under it was ever uploaded. So what draws a Paldea tile is Pokemon
#: HOME's artwork, the set :mod:`bdsp` and :mod:`legends_z_a` already draw from.
#:
#: Written here at step 1 because it decides nothing until step 6, which is where it is proved
#: by fetching rather than by reading a category. :mod:`archives` learned at Let's Go that a
#: category is a good index, and at Legends: Z-A that it is not a complete one.
SPRITE_SET = HOME_SET


#: Every page that carries a Scarlet and Violet wild table, and the place this dataset calls it.
#:
#: **Fifty, found by reading rather than by listing.** The Archives lesson applies to article
#: categories too - a category is a good index and not a complete one - so every one of the 125
#: pages in *Category:Scarlet and Violet locations* was fetched and asked whether it holds a
#: table with a Probability Weight header. Fifty do; the other 75 are shops, restaurants,
#: plazas, gyms and the towns, which is what a category of locations is mostly made of.
#:
#: **One page is a genuine hole and it is the wiki's rather than this reader's.** Timeless Woods
#: in Kitakami has a Pokemon section with no table under it at all. It is left out here rather
#: than guessed at, and step 9 is where its absence gets checked against the dex.
#:
#: The four ``Biome`` pages are the Terarium's, which is Blueberry Academy's dome in Unova, and
#: they are the only pages here that are not a place a player walks to from a road.
PAGES: dict[str, str] = {
    "Alfornada_Cavern": "Alfornada Cavern",
    "Apple_Hills": "Apple Hills",
    "Area_Zero": "Area Zero",
    "Asado_Desert": "Asado Desert",
    "Canyon_Biome": "Canyon Biome",
    "Casseroya_Lake": "Casseroya Lake",
    "Chargestone_Cavern": "Chargestone Cavern",
    "Chilling_Waterhead": "Chilling Waterhead",
    "Coastal_Biome": "Coastal Biome",
    "Colonnade_Hollow": "Colonnade Hollow",
    "Crystal_Pool": "Crystal Pool",
    "Dalizapa_Passage": "Dalizapa Passage",
    "East_Paldean_Sea": "East Paldean Sea",
    "East_Province_(Area_One)": "East Province (Area One)",
    "East_Province_(Area_Three)": "East Province (Area Three)",
    "East_Province_(Area_Two)": "East Province (Area Two)",
    "Fellhorn_Gorge": "Fellhorn Gorge",
    "Glaseado_Mountain": "Glaseado Mountain",
    "Infernal_Pass": "Infernal Pass",
    "Inlet_Grotto": "Inlet Grotto",
    "Kitakami_Road": "Kitakami Road",
    "Kitakami_Wilds": "Kitakami Wilds",
    "Mossfell_Confluence": "Mossfell Confluence",
    "North_Paldean_Sea": "North Paldean Sea",
    "North_Province_(Area_One)": "North Province (Area One)",
    "North_Province_(Area_Three)": "North Province (Area Three)",
    "North_Province_(Area_Two)": "North Province (Area Two)",
    "Oni_Mountain": "Oni Mountain",
    "Oni's_Maw": "Oni's Maw",
    "Paradise_Barrens": "Paradise Barrens",
    "Poco_Path": "Poco Path",
    "Pokémon_League_(Paldea)": "Pokémon League",
    "Polar_Biome": "Polar Biome",
    "Reveler's_Road": "Reveler's Road",
    "Savanna_Biome": "Savanna Biome",
    "Socarrat_Trail": "Socarrat Trail",
    "South_Paldean_Sea": "South Paldean Sea",
    "South_Province_(Area_Five)": "South Province (Area Five)",
    "South_Province_(Area_Four)": "South Province (Area Four)",
    "South_Province_(Area_One)": "South Province (Area One)",
    "South_Province_(Area_Six)": "South Province (Area Six)",
    "South_Province_(Area_Three)": "South Province (Area Three)",
    "South_Province_(Area_Two)": "South Province (Area Two)",
    "Tagtree_Thicket": "Tagtree Thicket",
    "Torchlit_Labyrinth": "Torchlit Labyrinth",
    "West_Paldean_Sea": "West Paldean Sea",
    "West_Province_(Area_One)": "West Province (Area One)",
    "West_Province_(Area_Three)": "West Province (Area Three)",
    "West_Province_(Area_Two)": "West Province (Area Two)",
    "Wistful_Fields": "Wistful Fields",
}

#: The five terrain columns, and the four ways of meeting something they come to.
#:
#: **Four and not five, and which two share a name was measured rather than argued.** Of the
#: 3,409 rows these fifty pages hold, 393 tick Underwater and **197 tick it and nothing else** -
#: an Arrokuda is never on the surface, so folding it into the water above it would tell a
#: player to swim past one. It gets a name of its own, which is
#: :attr:`EncounterMethod.OVERWORLD_UNDERWATER`.
#:
#: The Sky column did not earn one. It has 246 ticks and **four** rows where it is the only
#: tick, all four a Braviary in Area Zero that walks on the ground elsewhere in the same game -
#: so a Pikipek circling high and a Gastly hovering at head height are one event with different
#: scenery, which is the call :data:`kalos` made about five ambushes.
#:
#: A row ticked in both of those is one record and not two: :func:`paldea_encounters`
#: deduplicates what the five columns come to.
TERRAINS: dict[str, EncounterMethod] = {
    "Land": EncounterMethod.OVERWORLD,
    "Water surface": EncounterMethod.OVERWORLD_WATER,
    "Underwater": EncounterMethod.OVERWORLD_UNDERWATER,
    "Overland": EncounterMethod.OVERWORLD_FLYING,
    "Sky": EncounterMethod.OVERWORLD_FLYING,
}

#: What the species cell writes after the species name, and which form this dataset spells it.
#:
#: Hisui's shape and Lumiose's: the text of the cell reads "WooperPaldean Form", and the link
#: beside it says only which species it is. Fifty-three phrases over these fifty pages, every
#: one of them belonging to a single species or a single family, so nothing here is ambiguous.
#:
#: **A phrase mapped to nothing is the source naming a default**, and there are fifteen of
#: those: a Spring Deerling, a Red Flower Flabebe, a Midday Lycanroc, a Male Meowstic, a Baile
#: Oricorio, a Phony Sinistea. Those rows are about the species and the record says so; the
#: other thirty-nine name a choice, and the record names it too.
#:
#: **Most of them resolve to a species today and to a form at step 8**, which is deliberate.
#: :data:`forms.FORMS_NAMED_BY_THE_GAME` holds both halves of this pair, so the form table has
#: nothing of theirs in it yet, and :meth:`Normaliser.target` drops an unknown form back to its
#: species rather than inventing an id. So this table is written once, here, and starts
#: answering in full the day step 8 fills the form table in.
FORM_PHRASES: dict[str, str] = {
    # Regional forms, which are the phrases that matter most and the ones the Terarium is
    # stocked with: seven Alolan species in the biomes, Slowpoke's Galarian line, a Hisuian
    # Qwilfish, and Paldea's own Wooper.
    "Alolan Form": "alola",
    "Galarian Form": "galar",
    "Hisuian Form": "hisui",
    "Paldean Form": "paldea",
    # Paldean Tauros, whose three breeds the cell writes without repeating the region.
    "Combat Breed": "paldea-combat-breed",
    "Blaze Breed": "paldea-blaze-breed",
    "Aqua Breed": "paldea-aqua-breed",
    # The sexes the source models as forms rather than as a flag. The male is the default for
    # all four species that appear here.
    "Male": "",
    "Female": "female",
    # Deerling and Sawsbuck, whose spring is the default.
    "Spring Form": "",
    "Summer Form": "summer",
    "Autumn Form": "autumn",
    "Winter Form": "winter",
    # The Flabebe family's five flowers, of which red is the default.
    "Red Flower": "",
    "Blue Flower": "blue",
    "Orange Flower": "orange",
    "White Flower": "white",
    "Yellow Flower": "yellow",
    # Basculin's stripes, of which red is the default.
    "Red-Striped": "",
    "Blue-Striped": "blue-striped",
    # Rockruff, whose ordinary self the page calls Standard.
    "Standard": "",
    "Own Tempo": "own-tempo",
    # Lycanroc's three, of which midday is the default.
    "Midday Form": "",
    "Midnight Form": "midnight",
    "Dusk Form": "dusk",
    # Minior's seven cores, and all seven name a form rather than six naming one and a default
    # saying nothing. The source's default is the plain meteor, so *every* core is a choice -
    # and step 6 is what settled it: Pokemon HOME draws one plain Minior and seven cores and no
    # coloured meteor at all, so the core is both the thing that differs and the thing there is
    # a picture of.
    "Red Core": "red",
    "Orange Core": "orange",
    "Yellow Core": "yellow",
    "Green Core": "green",
    "Blue Core": "blue",
    "Indigo Core": "indigo",
    "Violet Core": "violet",
    # Oricorio's four styles, of which Baile is the default. The wiki writes Pom-Pom with a
    # non-breaking hyphen and the key has to be the string the page actually holds, so the
    # escape is deliberate: an ordinary hyphen here would match nothing and lose the style.
    "Baile Style": "",
    "Pom‑Pom Style": "pom-pom",  # noqa: RUF001
    "Pa'u Style": "pau",
    "Sensu Style": "sensu",
    # The two tea families, whose counterfeits are the defaults.
    "Phony Form": "",
    "Antique Form": "antique",
    "Counterfeit Form": "",
    # And the Artisan one says nothing either, which is the source's doing rather than a
    # judgement: it models Poltchageist's two as one Pokemon wearing two `pokemon-form`
    # entries, so there is no second Pokemon for this dataset to give an id to.
    "Artisan Form": "",
    # Squawkabilly's four plumages, of which green is the default.
    "Green Plumage": "",
    "Blue Plumage": "blue-plumage",
    "White Plumage": "white-plumage",
    "Yellow Plumage": "yellow-plumage",
    # Toxtricity's two, Dudunsparce's two, Shellos' two seas and Tatsugiri's three, each with
    # its default written as nothing.
    "Amped Form": "",
    "Low Key Form": "low-key",
    "Two-Segment Form": "",
    "West Sea": "",
    "East Sea": "east",
    "Curly Form": "",
    "Droopy Form": "droopy",
    "Stretchy Form": "stretchy",
    # And one Vivillon, which is the pattern a player of these games is given rather than the
    # one their console's region decides.
    "Fancy Pattern": "fancy",
    # The one phrase the wild tables never write and the fixed-encounter tables write eleven
    # times: a Gimmighoul on a watchtower is the Chest Form, which is its default - the
    # Roaming Form is the one that walks around and cannot be caught at all.
    "Chest Form": "",
}


def acquisition_methods(
    context: BuildContext,
    *,
    game_id: str,
    entries: Sequence[DexEntry],
) -> list[AcquisitionMethod]:
    """Every wild slot one of these two has. Step 3, and nothing after it yet.

    **There is no** ``wild_encounters`` **call beside this and there will not be one.** The
    source carries no Generation IX encounter at all: asking it for Sprigatito, Lechonk and
    Ursaluna returns no location areas whatever, and asking for Pikachu, Magikarp and Wooper -
    which have between 40 and 287 - returns not one row for ``scarlet``, ``violet`` or any of
    the four version names the two expansions add. The hole the reading before these six games
    predicted is total here too, exactly as it was for Legends: Z-A.

    So the whole of it is the wiki, through :func:`paldea_encounters`, and the species asked
    about are the game's own 664 rather than a National Dex slice - which is what
    :meth:`BuildContext.living_dex` does when a game has no National Dex to slice.

    Fixed and special encounters are deliberately not read here. They sit on the same fifty
    pages in a table of the familiar shape - a Games column, a Location and a Rate that says
    "Respawns" - and what they hold is one Pokemon standing in one named spot, which is step
    4's question rather than this one's.
    """
    species = context.living_dex(through=NATIONAL_DEX_THROUGH, entries=entries)

    return [
        *paldea_encounters(
            context.require_wiki(),
            game_id=game_id,
            version=LETTERS[game_id],
            pages=PAGES,
            terrains=TERRAINS,
            species=set(species),
            forms=context.forms_here(),
            form_names=FORM_PHRASES,
            refresh=context.refresh,
        ),
    ]

#: The page each hand-written record below was read from, and the day a person read it.
#:
#: A fetched citation takes its date from the cache entry the answer came out of. These have no
#: fetch to take one from, so the day is written down beside the table that was read.
#:
#: **Every one of these came off the species' own article rather than off a location page**,
#: which is the shape Hisui's statics have and for the same reason: the fifty location pages
#: carry the ordinary fixed encounters and not one of the nineteen below. Koraidon is not in
#: Poco Path's tables; Koraidon's own *Game locations* row says "Poco Path (only one)".
STATICS_PAGE = "Pok%C3%A9mon_Scarlet_and_Violet"

READ_ON = ReadByHand(
    dict.fromkeys(
        (STATICS_PAGE, "In-game_trade", "List_of_Pok%C3%A9mon_with_form_differences"),
        date(2026, 9, 26),
    )
)


def _partner(species: str) -> RecordedGift:
    """One of the three a player picks from in Cabo Poco.

    The article words it the same for all three - "First partner Pokemon from Clavell in Cabo
    Poco" - and a player takes one of them, which is the same thing every starter record in
    this dataset says and none of them tries to say twice.
    """
    return RecordedGift(
        species=species,
        location="Cabo Poco",
        level=5,
        kind=GiftKind.STARTER,
        npc="Clavell",
        requirement="One of the three, and the other two are somebody else's",
        source=READ_ON(STATICS_PAGE),
    )


def _legendary(
    species: str,
    location: str,
    requirement: str,
    *,
    level: int | None = None,
    form: str | None = None,
) -> RecordedGift:
    """One Pokemon standing in one place, cited to the article that says where it stands.

    ``form`` is for the one of these that is not the ordinary Pokemon: what stands in Timeless
    Woods is the **Bloodmoon** Ursaluna, and the ordinary one is not in these games at all.
    """
    return RecordedGift(
        species=species,
        location=location,
        form=form,
        level=level,
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement=requirement,
        source=READ_ON(STATICS_PAGE),
    )


#: What these games hand over or stand in one spot that no location page lists.
#:
#: **Nineteen, and every one read off its own article's Game locations row.** The fifty pages
#: step 3 read carry 302 fixed encounters between them and not one of these: a Titan is on its
#: province's page and Koraidon is not on Poco Path's, because the story hands it over rather
#: than standing it in the grass.
#:
#: Keyed by the half that has it, because five of the nineteen are a version exclusive and the
#: other fourteen are in both. The box legendary is the sharpest: Scarlet's article says
#: "Poco Path (only one) (Limited Build)" and then "Area Zero (after credits; only one) (Apex
#: Build)", and Violet's says "Trade, Event" - so a Koraidon in Violet comes over the cable
#: from the other half, which the pair's own trade edge already says.
STATICS: dict[str, tuple[RecordedGift, ...]] = {
    "scarlet": (
        _legendary(
            "koraidon",
            "Poco Path",
            "The one the story gives, in its Limited Build; the Apex Build stands in Area "
            "Zero after the credits",
        ),
        _legendary(
            "gouging-fire",
            "Area Zero",
            "Only one, after Perrin's questline in The Indigo Disk has been started",
        ),
        _legendary(
            "raging-bolt",
            "Area Zero",
            "Only one, after Perrin's questline in The Indigo Disk has been started",
        ),
    ),
    "violet": (
        _legendary(
            "miraidon",
            "Poco Path",
            "The one the story gives, in its Low-Power Mode; the Ultimate Mode stands in Area "
            "Zero after the credits",
        ),
        _legendary(
            "iron-crown",
            "Area Zero",
            "Only one, after Perrin's questline in The Indigo Disk has been started",
        ),
        _legendary(
            "iron-boulder",
            "Area Zero",
            "Only one, after Perrin's questline in The Indigo Disk has been started",
        ),
    ),
}

#: The thirteen both halves stand in the same place, which is everything but the box pair and
#: the Indigo Disk's four Paradox Pokemon.
SHARED_STATICS: tuple[RecordedGift, ...] = (
    # The three a player picks between, and the two they do not get are the pair's oldest
    # promise: a starter is one of three and a trade is how the other two arrive.
    _partner("sprigatito"),
    _partner("fuecoco"),
    _partner("quaxly"),
    # The Treasures of Ruin, each behind eight stakes pulled out of the ground somewhere else.
    _legendary("wo-chien", "South Province (Area One)", "Only one, at the Grasswither Shrine"),
    _legendary("chien-pao", "West Province (Area One)", "Only one, at the Icerend Shrine"),
    _legendary("ting-lu", "Socarrat Trail", "Only one, at the Groundblight Shrine"),
    _legendary("chi-yu", "North Province (Area Two)", "Only one, at the Firescourge Shrine"),
    # The Teal Mask's four, three of which have to be beaten before they stand anywhere.
    _legendary(
        "okidogi",
        "Paradise Barrens",
        "Only one, after the main story of The Teal Mask",
    ),
    _legendary(
        "munkidori",
        "Wistful Fields",
        "Only one, after the main story of The Teal Mask",
    ),
    _legendary(
        "fezandipiti",
        "Oni Mountain",
        "Only one, after the main story of The Teal Mask",
    ),
    _legendary("ogerpon", "Dreaded Den", "Only one, in The Teal Mask"),
    # And the two the last two updates added, one at the bottom of the crater and one that
    # wants a berry.
    _legendary("terapagos", "Area Zero Underdepths", "Only one, in The Indigo Disk"),
    _legendary(
        "pecharunt",
        "Loyalty Plaza",
        "Only one, and it wants the Mythical Pecha Berry",
    ),
    # And the two step 9 caught, standing in the one place step 3 could not read.
    #
    # **Timeless Woods is the wiki's own hole and it turned out to hold both of them.** Step 3
    # found a page with a Pokemon section and no table under it, left it out rather than
    # guessing, and said step 9 would check what that cost. It cost two, and neither article
    # states a level - which is why both are here rather than in a wild table: a static carries
    # a level that may be left out, and a wild slot must have one. Writing 1-100 to satisfy a
    # field would be telling a player something no page says.
    #
    # **Timeless Woods is the page with a Pokemon section and no table under it**, which step 3
    # left out rather than guessed at and called the wiki's own hole. This is what was in it: a
    # Bloodmoon Ursaluna, only one, and the ordinary Ursaluna is in neither half at all. The
    # dex entry is the species, because Kitakami numbers #196 as the Bloodmoon one - so without
    # this the entry had a number, a picture and no way to fill it, and the smoke test is what
    # said so.
    _legendary(
        "basculin",
        "Timeless Woods",
        "The White-Striped form, which is in this one place; everywhere else in these games a "
        "Basculin is Red-Striped or Blue-Striped",
        form="basculin-white-striped",
    ),
    _legendary(
        "ursaluna",
        "Timeless Woods",
        "Only one, after the main story of The Teal Mask; the ordinary Ursaluna is in neither "
        "half",
        form="ursaluna-bloodmoon",
    ),
)


def statics(game_id: str) -> tuple[RecordedGift, ...]:
    """What this half stands in one spot, which is the fourteen shared and its own three."""
    return (*SHARED_STATICS, *STATICS[game_id])


def handed_over(
    context: BuildContext,
    *,
    game_id: str,
    entries: Sequence[DexEntry],
) -> list[AcquisitionMethod]:
    """Everything these games hand over or leave standing in one spot. Step 4.

    Two halves, and the split is between what a location page knows and what it does not.

    **The fifty pages know 302 of them**, in a *Fixed encounters* table shaped the way every
    location page in this dataset has been shaped since Hoenn, and :func:`paldea_fixed` reads
    it. 295 respawn and seven do not; ten of their species are in no wild table at all, which
    is the Titans, Gimmighoul on its watchtowers, and the high-level spawns Area Zero stands
    rather than rolls.

    **The nineteen that matter most are on none of them**, and are written out by hand in
    :data:`SHARED_STATICS` and :data:`STATICS` from each species' own article: the three a
    player picks between in Cabo Poco, the box legendary, the four Treasures of Ruin, the Teal
    Mask's four, Terapagos, Pecharunt, and the four Paradox Pokemon the Indigo Disk splits
    between the halves.

    **And two are deliberately absent.** Walking Wake and Iron Leaves say "Poke Portal News"
    where the others name a place - they were handed out in a seven-star raid and in nothing
    else - so they are not step 4's and their reason is step 7's to write.
    """
    species = context.living_dex(through=NATIONAL_DEX_THROUGH, entries=entries)

    return [
        *paldea_fixed(
            context.require_wiki(),
            game_id=game_id,
            version=LETTERS[game_id],
            pages=PAGES,
            species=set(species),
            forms=context.forms_here(),
            form_names=FORM_PHRASES,
            refresh=context.refresh,
        ),
        *recorded_gifts(
            game_id=game_id,
            gifts=statics(game_id),
            species=species,
            citation=READ_ON(STATICS_PAGE),
        ),
    ]

#: The three version groups these two span, which is what their evolutions hang off.
#:
#: **Galar's answer, and for Galar's reason**: the source files each expansion as a group of
#: its own and puts real rules in them. Asking only about ``scarlet-violet`` would lose five
#: evolutions that only the DLC has - an Applin becoming a Dipplin with a Syrupy Apple and a
#: Dipplin becoming a Hydrapple knowing Dragon Cheer are stamped ``the-teal-mask`` and
#: ``the-indigo-disk`` - and with them Archaludon and both Sinistcha.
EVOLUTION_GROUPS = ("scarlet-violet", "the-teal-mask", "the-indigo-disk")

#: Where an egg is left and collected, which in these games is not a building at all.
#:
#: **The first game in the dataset with no day care and no nursery.** A player sets out a
#: picnic anywhere in the world, leaves two compatible Pokemon in the party, and comes back to
#: a basket. So the field says where a player actually goes, which is nowhere in particular.
NURSERY = "a picnic, anywhere in the world"

#: Bulbapedia's in-game trade tables, which are where all twenty-one of these were read.
TRADES_PAGE = "In-game_trade"

#: The three trades these games have in the old sense: an NPC who wants one thing in exchange.
#:
#: Three, where Galar has twenty. The two things worth saying about them are both about what
#: is handed over rather than what is wanted: the Cascarrafa trader takes a **Paldean** Wooper
#: and gives back the ordinary one, which is the only place in these games that direction of
#: swap happens, and the Haunter from Levincia **becomes a Gengar on the way**, which is the
#: series' oldest joke and the only Gengar this pair produces without a second console.
NPC_TRADES: tuple[InGameTrade, ...] = (
    InGameTrade(
        gets="snom",
        wants="flabebe",
        location="Cortondo",
        npc="Glen",
        requirement="Any Flabebe, whichever flower it is holding",
    ),
    InGameTrade(
        gets="wooper",
        wants="wooper",
        location="Cascarrafa",
        npc="Sue",
        requirement="A Paldean Wooper, and what comes back is the ordinary one",
    ),
    InGameTrade(
        gets="gengar",
        wants="pincurchin",
        location="Levincia",
        npc="Chimi",
        requirement="A Haunter is handed over and evolves into a Gengar on the way across",
    ),
)

#: The room where eighteen more trades happen, and the one thing they all ask for.
#:
#: **A different kind of trade, and the first of its kind in the dataset.** Invite a Gym
#: Leader, an Elite Four member, a staff member, Geeta or Cyrano to the League Club Room three
#: times and they offer to swap one of theirs for **any Pokemon of the player's** - any at all,
#: as long as the player is its original trainer and it is neither Shiny nor a Special Pokemon.
#:
#: So :attr:`InGameTrade.wants` is left empty, which is what that field's own docstring says it
#: means: the trader who will take whatever is in the party. Eighteen of them, and every one of
#: the eighteen is a species the grass already produces - so what this adds is a second way and
#: not a second species, which is worth writing down because it was worth checking.
CLUB_ROOM = "League Club Room"
CLUB_ROOM_CONDITION = (
    "Invite them to the League Club Room three times; they will take any Pokemon the player "
    "raised themselves, as long as it is not Shiny"
)

CLUB_ROOM_TRADES: tuple[tuple[str, str], ...] = (
    ("magby", "Crispin"),
    ("dudunsparce", "Larry"),
    ("wooper", "Rika"),
    ("pawmo", "Clavell"),
    ("cetoddle", "Grusha"),
    ("veluza", "Kofu"),
    ("arctibax", "Hassel"),
    ("combee", "Katy"),
    ("duraludon", "Drayton"),
    ("meditite", "Dendra"),
    ("sunflora", "Brassius"),
    ("mareanie", "Miriam"),
    ("magnemite", "Iono"),
    ("skarmory", "Amarys"),
    ("glimmet", "Geeta"),
    ("tinkatuff", "Poppy"),
    ("greavard", "Ryme"),
    ("gimmighoul", "Raifort"),
)


def traders() -> list[InGameTrade]:
    """Every trade either half can make, which is the same list for both.

    Twenty-one, and no version exclusive among them: a pair usually splits its traders the way
    it splits its grass, and this one does not.
    """
    return [
        *NPC_TRADES,
        *(
            InGameTrade(
                gets=species,
                location=CLUB_ROOM,
                npc=npc,
                requirement=CLUB_ROOM_CONDITION,
            )
            for species, npc in CLUB_ROOM_TRADES
        ),
    ]


#: Three the source says can be evolved into here and which cannot be, with the reason.
#:
#: **The Linking Cord problem in a new dress, and step 9's smoke test is what found it.** A
#: source rule carries forward to every later game, which is right almost always and is the
#: whole reason :class:`evolutions.MissingVariant` distinguishes a rule the source carries from
#: one a person read on an item's page. What carries forward with it is the *item*, and an item
#: can stop existing: the Peat Block and the Black Augurite are Hisui's and are in no shop,
#: cave or tree in Paldea.
#:
#: So a tile for the ordinary Ursaluna said "use a Peat Block on an Ursaring, during the
#: full-moon" to a player of Scarlet, who has no Peat Block and no way to get one. Each of the
#: three was checked against its own article's Game locations row, which says in every case
#: that the evolution happens *in Legends: Arceus* and arrives here through Pokemon HOME.
#:
#: Two of the three are still obtainable and it is worth saying how: **Kleavor is caught in the
#: Terarium's Canyon Biome**, so only its evolution is refused, and **Ursaluna's Bloodmoon form
#: stands in Timeless Woods** while the ordinary one is a stranger to all three lists. Only
#: Hisuian Lilligant has nothing left but the transfer.
NOT_AN_EVOLUTION_HERE: dict[str, str] = {
    "ursaluna": (
        "The Peat Block is Hisui's and is in no shop or cave in Paldea; an Ursaring becomes an "
        "Ursaluna in Legends: Arceus and comes here through Pokemon HOME. The Bloodmoon one "
        "stands in Timeless Woods and is a different Pokemon"
    ),
    "kleavor": (
        "The Black Augurite is Hisui's; a Scyther becomes a Kleavor in Legends: Arceus. In "
        "these games a Kleavor is caught in the Terarium rather than made"
    ),
    "lilligant-hisui": (
        "A Petilil becomes a Hisuian Lilligant in Hisui, which the rule says in as many words; "
        "here the Sun Stone makes the Unovan one and the Hisuian arrives through Pokemon HOME"
    ),
}

#: The page the sentences below were read from, which is the list of form differences.
FORMS_PAGE = "List_of_Pok%C3%A9mon_with_form_differences"

#: How a form that is not caught is come by. A sex needs no line: :mod:`formchanges` answers it.
#:
#: **Only eight, and that is the whole shape of this pair's forms.** Of the 171 these two hold,
#: 82 are caught or handed over, 51 are a sex, thirty are a regional form that arrives through
#: HOME rather than being made here - and eight are something a player does to a Pokemon they
#: already have. Galar needed eighty-odd lines for the same job because it had Alcremie.
#:
#: Rotom's five are the Catalog, which these games give whole: unlike Brilliant Diamond, where
#: a form has to have been worn once before the Catalog will offer it, every appliance is
#: unlocked the moment the item is in the bag.
#:
#: Ogerpon's three are the masks it is carrying when it is found, and a player swaps between
#: them by handing it a different one. The fourth, the Teal Mask, is the one it wears already.
FORM_CHANGES: dict[str, FormChange] = {
    **spread(
        FormChange(
            requirement=(
                "Use the Rotom Catalog, which unlocks every appliance at once in these games "
                "rather than only the ones a Rotom has already worn"
            ),
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
                "Give Ogerpon the mask, which is found in Kitakami; it wears the Teal Mask "
                "when it is caught and changes between the four freely"
            ),
            where="Kitakami",
        ),
        "ogerpon-wellspring-mask",
        "ogerpon-hearthflame-mask",
        "ogerpon-cornerstone-mask",
    ),
}


def swapped_and_evolved(
    context: BuildContext,
    *,
    game_id: str,
    entries: Sequence[DexEntry],
    found: Sequence[AcquisitionMethod],
) -> list[AcquisitionMethod]:
    """The trades, the evolutions and the eggs. Step 5.

    **The evolutions needed three groups and four new words.** The groups are Galar's answer
    again; the words are Generation IX's own, and every one of them was already wrong in the
    dataset before this pair was written. ``evolutions.OTHER_TRIGGERS`` had no wording for
    ``in-battle-level-up``, ``use-move``, ``three-defeated-bisharp`` or ``gimmighoul-coins``,
    so a Primeape's tile in Legends: Z-A said "use move" and a Gimmighoul's said "gimmighoul
    coins" - two tiles that have read like that since that game was built. Pawmo was worse:
    its only requirement is a thousand steps walked beside the player, the source carries that
    as ``min_steps`` and nothing read it, so the rule came out with **no conditions at all**
    and told a player that a Pawmo simply levels up.

    **The eggs are last and are worked out rather than listed**, which is the shape every game
    since Diamond has used: a nursery can only be asked for what nothing else here produces.
    What is different is where a player goes, and it is nowhere - these are the first games in
    the dataset with no day care building at all, only a picnic basket.
    """
    api = context.require_api()
    species = context.living_dex(through=NATIONAL_DEX_THROUGH, entries=entries)
    evolved = [
        *trade_encounters(
            game_id=game_id,
            trades=traders(),
            citation=READ_ON(TRADES_PAGE),
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
    ]

    return [
        *evolved,
        *form_change_encounters(
            game_id=game_id,
            forms=context.forms_here(),
            changes=FORM_CHANGES,
            citation=READ_ON(FORMS_PAGE),
        ),
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
                caught={
                    one.target.species
                    for one in (*found, *evolved)
                    if one.kind in CAUGHT
                },
                evolved={
                    one.target.species
                    for one in (*found, *evolved)
                    if one.kind == "evolution"
                },
                refresh=context.refresh,
            ),
            citation=READ_ON(TRADES_PAGE),
        ),
    ]

#: What each half calls itself in the other half's reason.
TITLE = {"scarlet": "Scarlet", "violet": "Violet"}

#: The second way across, which no pair before this one had.
#:
#: **This is the softest version pair in the series and step 7 is where that becomes a
#: sentence.** The article says most version exclusives can be encountered and caught by a
#: player of the opposite version who joins a Union Circle or a Tera Raid Battle - so for
#: thirty of the forty, "trade one in" is true and is not the whole truth.
#:
#: Three groups, and the article draws the lines itself. Paradox Pokemon can be met in somebody
#: else's Union Circle but **not** in a raid, not counting the limited-time event ones; the
#: ordinary exclusives can be met in either; and Koraidon and Miraidon, it says in as many
#: words, require trading.
IN_SOMEBODY_ELSES = "catch one in somebody else's Union Circle or Tera Raid Battle"
IN_A_UNION_CIRCLE = "catch one in somebody else's Union Circle"

#: The six that really do need the cable, which are the story's own.
#:
#: The box legendary and the four Paradox Pokemon the Indigo Disk stands in Area Zero: each is
#: one Pokemon in one place in one half, so there is no wild table for the other half to join
#: and no raid it turns up in.
TRADE_ONLY = frozenset(
    {"koraidon", "miraidon", "gouging-fire", "raging-bolt", "iron-crown", "iron-boulder"}
)

#: The fourteen the article keeps out of raids, seven each way.
#:
#: Paldea's own Paradox Pokemon, ancient in one half and future in the other. They can be
#: caught in a Union Circle and not in a raid, which is the exact opposite of the rule for
#: Armarouge and Ceruledge - and neither of those is an exclusive, so only this half of the
#: sentence has anywhere to live.
PARADOX = frozenset(
    {
        "brute-bonnet",
        "flutter-mane",
        "great-tusk",
        "roaring-moon",
        "sandy-shocks",
        "scream-tail",
        "slither-wing",
        "iron-bundle",
        "iron-hands",
        "iron-jugulis",
        "iron-moth",
        "iron-thorns",
        "iron-treads",
        "iron-valiant",
    }
)

#: What each half has that the other does not, and what once handed one over anyway.
#:
#: **Twenty each way, which is a large pair by any measure** - Sword and Shield have nineteen -
#: and the twenty are three kinds: three statics, seven Paradox Pokemon and ten ordinary
#: exclusives, the same shape on both sides.
#:
#: The value is what step 7 found, or ``None`` where it found nothing. **Ten of the forty had a
#: distribution**, and the two that matter most are the pair's own: *Paldea's Shiny Koraidon*
#: went to **Violet** players and *Paldea's Shiny Miraidon* to **Scarlet** ones, both online in
#: the autumn of 2025. That is Galar's sharpest step-7 finding repeated exactly - Lancer's
#: Shiny Zacian ran in Shield and Arthur's Shiny Zamazenta in Sword - and it is worth knowing
#: that the series has now done it twice.
#:
#: The other eight are CoroCoro's, and they were **SV** distributions rather than one half's,
#: so a Scarlet player really was handed an Iron Hands and a Violet player a Brute Bonnet.
ONLY_ON: dict[str, dict[str, str | None]] = {
    "scarlet": {
        "brute-bonnet": exclusives.handed_out(
            "the CoroCoro Brute Bonnet of 15 January to 14 March 2024"
        ),
        "cramorant": None,
        "cranidos": None,
        "deino": None,
        "drifloon": None,
        "flutter-mane": exclusives.handed_out(
            "the CoroCoro Flutter Mane of 15 January to 14 March 2024",
            "Shin Yeo-myeong's Flutter Mane of May 2024",
        ),
        "gligar": None,
        "gouging-fire": None,
        "great-tusk": None,
        "koraidon": exclusives.handed_out(
            "Paldea's Shiny Koraidon, given to Violet players from 26 September to 23 October 2025"
        ),
        "larvitar": None,
        "oranguru": None,
        "raging-bolt": None,
        "roaring-moon": exclusives.handed_out(
            "the CoroCoro Roaring Moon of 15 December 2023 to 14 February 2024"
        ),
        "sandy-shocks": None,
        "scream-tail": exclusives.handed_out(
            "the CoroCoro Scream Tail of 15 January to 14 March 2024"
        ),
        "skrelp": None,
        "slither-wing": None,
        "stonjourner": None,
        "stunky": None,
    },
    "violet": {
        "aipom": None,
        "bagon": None,
        "clauncher": None,
        "dreepy": None,
        "eiscue": None,
        "gulpin": None,
        "iron-boulder": None,
        "iron-bundle": None,
        "iron-crown": None,
        "iron-hands": exclusives.handed_out(
            "the CoroCoro Iron Hands of 15 January to 14 March 2024",
            "Marco Silva's Iron Hands of April 2024",
        ),
        "iron-jugulis": exclusives.handed_out(
            "the CoroCoro Iron Jugulis of 15 January to 14 March 2024"
        ),
        "iron-moth": None,
        "iron-thorns": exclusives.handed_out(
            "the CoroCoro Iron Thorns of 15 January to 14 March 2024"
        ),
        "iron-treads": None,
        "iron-valiant": exclusives.handed_out(
            "the CoroCoro Iron Valiant of 15 December 2023 to 14 February 2024"
        ),
        "miraidon": exclusives.handed_out(
            "Paldea's Shiny Miraidon, given to Scarlet players from 26 September to 24 October 2025"
        ),
        "misdreavus": None,
        "morpeko": None,
        "passimian": None,
        "shieldon": None,
    },
}

#: The two entries neither half produces, and the raid that has handed them out six times.
#:
#: **The first step-7 finding in this dataset that is not over.** Every distribution named in
#: any other game's reasons ran once or twice and stopped; the *Walking Wake and Iron Leaves
#: Showcase* is a seven-star Tera Raid that has come back **six times in three years** - 27
#: February 2023, 1 May 2023, 25 December 2023, 26 April 2024, 21 February 2025 and 19
#: December 2025 - and the last of those ended on 4 January 2026.
#:
#: So the sentence a player gets is different in kind from Galar's. A raid that ran for a week
#: in 2020 is not a way to fill a dex today; a raid that has returned every year since 2023 is
#: a reason to watch the news rather than to give up. The entry is still unobtainable, because
#: nothing a player can do today produces one, and that is what the field means.
#:
#: Walking Wake is Scarlet's and Iron Leaves is Violet's, at level 75 with a Water and a
#: Psychic Tera Type - which is the one place these two split something that neither of them
#: can catch.
SHOWCASE = exclusives.with_event(
    "Nothing in either half produces one: it is not in the grass, not standing anywhere and "
    "not handed over",
    exclusives.handed_out(
        "the Walking Wake and Iron Leaves Showcase of February 2023",
        "five repeats of it through to 4 January 2026",
    ),
)


def only_on(partner: str, species: str, event: str | None = None) -> str:
    """Why an entry in this dex is not in this cartridge, with the way across it really has."""
    if species in TRADE_ONLY:
        also = None
    elif species in PARADOX:
        also = IN_A_UNION_CIRCLE
    else:
        also = IN_SOMEBODY_ELSES

    return exclusives.only_on(partner, generation=GENERATION, event=event, also=also)


def unobtainable_in(game_id: str) -> dict[str, str]:
    """Everything one half cannot produce: the other half's twenty, and the two neither can.

    Each reason is two sentences where step 7 found something and one where it did not, which
    is the shape every game in this dataset uses: the first says why the cartridge cannot make
    one, the second says what once could.

    **Not Basculegion and not Overqwil**, which were the other two entries no method here
    filled and which were step 8's rather than this step's. Both hung on a form the form table
    did not hold yet - a White-Striped Basculin and a Hisuian Qwilfish - and both came back the
    moment step 8 added them: Overqwil off a rule the source stamps ``scarlet-violet``, and
    Basculegion off one it stamps ``legends-arceus``, which carries forward the way every rule
    the source carries does. Marking either unobtainable would have been writing down a gap
    that the next step closed.
    """
    other = next(one for one in PAIR if one != game_id)

    return {
        **{
            species: only_on(TITLE[other], species, event)
            for species, event in ONLY_ON[other].items()
        },
        # Both halves, because neither of them produces either: the raid handed Scarlet the one
        # and Violet the other, and a raid that is over hands nobody anything.
        "walking-wake": SHOWCASE,
        "iron-leaves": SHOWCASE,
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

    No ``national_dex_through``, for the reason :func:`galar.cartridge` gives: the field says how
    far a living dex in this game reaches, and these hold a list instead.
    :class:`DexSource.GAME_DEX` is the answer, and step 2 fills the lists in.
    """
    return Game(
        id=game_id,
        title=title,
        version=version,
        generation=GENERATION,
        region=REGION,
        release=GameRelease.CARTRIDGE,
        released=RELEASED,
        national_dex_through=NATIONAL_DEX_THROUGH,
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
    """All three Paldea Pokedexes, each entry saying which of them it is numbered in.

    One function for the two halves, because the two halves show the same three lists in the
    same order with the same numbers. A version pair splits what can be *caught*, not what is
    listed, and that has been true since Red and Blue; what differs between Scarlet and Violet
    is steps 3 to 5, and the ``unobtainable`` table each game brings once step 7 knows what to
    put in it.

    The order is the order a player meets them - Paldea, then Kitakami, then Blueberry - which
    is release order and also the order the Pokedex app shows its tabs in.

    **Checked against the wiki row by row rather than trusted, and it is the cleanest result of
    any game with more than one list.** Kitakami's 200 and Blueberry's 243 match the source
    number for number and name for name with nothing to reconcile at all; Paldea's 400 have one
    row where the two texts differ, and it is #145 Flabebe, where the wiki names the Red Flower
    it always shows first. Hisui's step 2 had 32 rows to argue about.

    **Nothing here carries a form**, which is the rule every game's dex list follows - and these
    lists lean on it harder than any before them. :data:`LISTS_THAT_NAME_A_FORM` says how hard:
    twenty rows name a form that is not the species' default, fifteen of them Blueberry's, and
    one of them is a Bloodmoon Ursaluna whose ordinary self is not in any list. Step 8 is where
    that is settled.
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


def trade_edges(game_id: str) -> list[TransferEdge]:
    """The one cable these games have, which runs to the other half of the pair.

    The same limit every Switch pair has had: no route to Legends: Z-A, none to the Generation 8
    games that share the console, and none to Pokemon GO, which connects to these two over
    Bluetooth and sends postcards and Gimmighoul Coins rather than Pokemon. Everything else goes
    by way of HOME.

    Local wireless, the internet, Surprise Trade and a Link Code are four ways of doing one
    thing and the graph holds it once. What this edge does not say is that HOME will move a
    Pokemon between two Scarlet and Violet save files on the same console, profiles included -
    the article says so in as many words - because that is a route from a game to itself, and a
    graph of games has nowhere to draw it.
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

    Three, which is Galar's count and Galar's pair of HOME edges - the deposit that takes
    anything and the withdrawal that reads the target's own list - because HOME connects to
    these games in both directions, from its version 3.0.0 of 30 May 2023.

    **The way out is real and it has an end, which is the finding.** The article says a Pokemon
    may still be transferred to any Generation VIII game, and that one which has been
    transferred to any later game *starting with Legends: Z-A* becomes incompatible. That is the
    deposit :mod:`legends_z_a` declined to draw, seen from the other side: the graph already
    says a Pokemon caught here can reach Sword, and already says that one which has gone on to
    Legends: Z-A can reach nothing. Neither sentence needed an edge added or removed - the game
    written after this generation's last one turns out to have got it right.

    **Registering these two lights nothing that was waiting**, for the seventh Switch game
    running and for the same reason: HOME is the only door, and every older game that can reach
    these was already reaching HOME.
    """
    return [*trade_edges(game_id), *home.home_edges(game_id)]
