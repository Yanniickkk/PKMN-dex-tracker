"""Pokemon Legends: Arceus: what it is, and the two routes it brings.

Phase 2 steps 1 to 8 for this game, and nothing after them yet. The fifth and last
Generation VIII core series game, and the only one of the five that is not half of a pair -
so unlike Sword, Shield, Brilliant Diamond and Shining Pearl there is no shared module beside
this one and no partner to name. What the pair modules hold, this file holds itself.

**Three modules it deliberately does not read from**, each for a reason worth writing down
rather than discovering later:

* :mod:`sinnoh`. Hisui is the same landmass, and that is all it is. The region module holds
  Sinnoh's Pokedex, its towns, its routes and its traders across two generations of games set
  there, and not one of those survives the trip back: the dex is 242 entries in its own order,
  the towns do not exist yet, and there are no routes or in-game trades at all. Brilliant
  Diamond could ask :mod:`sinnoh` for its 151 because it shows the same list; this shows a
  different one, of a different place, at a different time, and the only thing the two share is
  ground.
* A generation module. There is no ``gen8.py`` and there is still nothing for one to say: the
  four games written before this one have exactly one thing in common, Pokemon HOME, and
  :mod:`home` has held that since before any of them existed.
* A ``legends.py`` shared with Legends: Z-A. Tempting, and wrong at this stage. Z-A is another
  generation in another region with another dex shape, and the one thing the reading before
  these six games found the two of them sharing is a **table reader** - which belongs in
  :mod:`encountertables` beside the others, not in a module about games.

**What this game cannot do is most of the shape of the graph around it.** Bulbapedia, in the
same sentence it uses for Sword and for Brilliant Diamond: as with other games on the Nintendo
Switch, the game is not compatible with other games of the same generation. It trades with other
copies of itself over the internet and with nothing else, and a route from a game to itself is
one a graph of games has nowhere to draw. So two routes, and both of them are HOME's.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from ..archives import HISUI_SET
from ..encountertables import legends_encounters
from ..evolutions import evolution_encounters
from ..formchanges import FormChange, form_change_encounters, spread
from ..games import BuildContext, GameRegistry
from ..gifts import RecordedGift, recorded_gifts
from ..models import (
    AcquisitionMethod,
    DexEntry,
    DexSource,
    DexTarget,
    EncounterMethod,
    Game,
    GameData,
    GameRelease,
    GiftKind,
    TransferEdge,
)
from ..sources import ReadByHand
from . import home

GAME_ID = "legends-arceus"

#: Generation 8, and the last of it.
#:
#: The same number Sword and Brilliant Diamond carry, which by now says nothing about what a
#: game is: this generation holds a pair with no National Dex, a pair of remakes with one, and
#: an action RPG with no gyms and no wild battle a player is made to stand still for. A
#: generation is when a game came out.
GENERATION = 8

#: Hisui, which is Sinnoh long before anybody called it that.
#:
#: Written as its own region rather than as Sinnoh with a date on it, because what a player
#: reads on the screen is Hisui and this field is what a player would say. The two entries share
#: a landmass and nothing a living dex cares about - no list, no town, no route.
REGION = "Hisui"

#: One day, everywhere: Japan, North America, Europe, Australia, South Korea, Hong Kong and
#: Taiwan all on 28 January 2022.
RELEASED = date(2022, 1, 28)

#: What PokeAPI calls this game, and what it calls the group of one that holds it.
#:
#: Both are the same word, which is what a standalone game looks like in that source: the
#: version group ``legends-arceus`` holds one version, one region and one Pokedex.
POKEAPI_VERSION = "legends-arceus"
VERSION_GROUP = "legends-arceus"

#: There is no National Pokedex here, and the boxes hold a list rather than everything up to a
#: number.
#:
#: **Galar's answer, reached by a different road.** Sword and Shield leave this empty because
#: their boxes hold three lists *and eighty species besides* - :data:`galar.
#: FOREIGN_TO_EVERY_DEX` is that leftover written down, and the reading before these six games
#: says to look at it before assuming a game's own dex is the whole of what it can hold.
#: Bulbapedia says of this one that **only Pokemon in the Hisui Pokedex can be transferred into
#: Legends: Arceus**, which is very nearly the dex being the boxes - and the leftover is
#: :data:`HELD_WITHOUT_BEING_LISTED`, which has two entries where Galar's has eighty.
NATIONAL_DEX_THROUGH = None

#: What this game can hold that its Pokedex does not list. Galar's eighty, in miniature.
#:
#: **Step 2 is what turned this from nothing into two.** The sentence next to the transfer rule
#: reads: non-Hisuian regional forms of a listed species cannot be transferred in either, "with
#: the exception of Alolan Vulpix and Alolan Ninetales". That looked at first like the wiki
#: naming this game's own entries for those two - and it is not. The Hisui Pokedex's #168 and
#: #169 are the **Kantonian** Vulpix and Ninetales, which is the oddity a player meets in the
#: Alabaster Icelands: the snow here is full of the Vulpix that is not the icy one. So the
#: Alolan pair is a genuine exception, and a box in Hisui can hold two kinds of Vulpix while the
#: Pokedex has a page for one.
#:
#: Written down rather than acted on. A form is not a dex entry, so nothing here reaches a tile
#: until step 8 says which forms this game has; what this constant does is stop the next reader
#: concluding from ``national_dex_through is None`` that the list is the whole story.
HELD_WITHOUT_BEING_LISTED = ("vulpix-alola", "ninetales-alola")


#: The five areas of Hisui and the parts of each one that hold wild Pokemon.
#:
#: **The tables are a level below the place a player would name.** Asking Bulbapedia about the
#: Obsidian Fieldlands gets an article with a Pokemon section that is empty and a list of
#: nineteen sublocations underneath; the encounters are on those. So this is eighty-one pages
#: rather than five, and a record says "Obsidian Fieldlands, Horseshoe Plains" the way the Grand
#: Underground's say which cave.
#:
#: Written as areas and their parts rather than as eighty-one pairs, because the page title and
#: the name are the same word with underscores in it, every time - which was checked rather than
#: assumed while this was generated.
SUBLOCATIONS: dict[str, tuple[str, ...]] = {
    "Obsidian Fieldlands": (
        "Aspiration Hill",
        "Floaro Gardens",
        "Horseshoe Plains",
        "Grueling Grove",
        "Worn Bridge",
        "Deertrack Path",
        "Deertrack Heights",
        "Windswept Run",
        "Nature's Pantry",
        "Tidewater Dam",
        "The Heartwood",
        "Grandtree Arena",
        "Oreburrow Tunnel",
        "Obsidian Falls",
        "Ramanas Island",
        "Sandgem Flats",
        "Lake Verity",
    ),
    "Crimson Mirelands": (
        "Golden Lowlands",
        "Gapejaw Bog",
        "Holm of Trials",
        "Ursa's Ring",
        "Sludge Mound",
        "Scarlet Bog",
        "Solaceon Ruins",
        "Cloudpool Ridge",
        "Shrouded Ruins",
        "Diamond Heath",
        "Diamond Settlement",
        "Bolderoll Slope",
        "Cottonsedge Prairie",
        "Droning Meadow",
        "Lake Valor",
    ),
    "Cobalt Coastlands": (
        "Crossing Slope",
        "Ginkgo Landing",
        "Aipom Hill",
        "Bathers' Lagoon",
        "Hideaway Bay",
        "Deadwood Haunt",
        "Tombolo Walk",
        "Sand's Reach",
        "Tranquility Cove",
        "Castaway Shore",
        "Windbreak Stand",
        "Spring Path",
        "Islespy Shore",
        "Veilstone Cape",
        "Lunker's Lair",
        "Seagrass Haven",
        "Seaside Hollow",
        "Firespit Island",
    ),
    "Coronet Highlands": (
        "Heavenward Lookout",
        "Wayward Cave",
        "Wayward Wood",
        "Ancient Quarry",
        "Sonorous Path",
        "Lonely Spring",
        "Clamberclaw Cliffs",
        "Celestica Ruins",
        "Celestica Trail",
        "Primeval Grotto",
        "Sacred Plaza",
        "Stonetooth Rows",
        "Bolderoll Ravine",
        "Fabled Spring",
        "Cloudcap Pass",
    ),
    "Alabaster Icelands": (
        "Whiteout Valley",
        "Crevasse Passage",
        "Bonechill Wastes",
        "Icebound Falls",
        "Avalanche Slopes",
        "Ice Column Chamber",
        "Arena's Approach",
        "Avalugg's Legacy",
        "Icepeak Cavern",
        "Snowfall Hot Spring",
        "Secret Hollow",
        "Glacier Terrace",
        "Heart's Crag",
        "Pearl Settlement",
        "Lake Acuity",
        "Snowpoint Temple",
    ),
}

#: The twenty-two parts of Hisui with no wild table, listed so that none of them is silently
#: missing.
#:
#: Three kinds, and all three are the game rather than a gap in the wiki. **Eleven base camps**,
#: which are the safe places a player sleeps and crafts in and where nothing spawns. **Four
#: arenas** where a noble Pokemon is fought, which is a battle rather than a catch - Grandtree
#: Arena is not among them, because ordinary Pokemon walk around in it as well. And **seven
#: places the story owns**: the Temple of Sinnoh and the Hall of Origin, the Stone Portal, the
#: Lava Dome Sanctum, the Tidal Passage, Turnback Cave and Hibernal Cave. Four of those seven
#: hold a Legendary each, which is step 4's rather than step 3's.
#:
#: Checked one at a time rather than inferred from an empty result: Turnback Cave's article
#: carries a "Pokemon Legends: Arceus" heading with nothing under it, and Hibernal Cave's has no
#: Pokemon section at all.
NO_WILD_TABLE: dict[str, tuple[str, ...]] = {
    "Obsidian Fieldlands": (
        "Fieldlands Camp",
        "Heights Camp",
    ),
    "Crimson Mirelands": (
        "Mirelands Camp",
        "Bogbound Camp",
        "Brava Arena",
    ),
    "Cobalt Coastlands": (
        "Beachside Camp",
        "Coastlands Camp",
        "Tidal Passage",
        "Turnback Cave",
        "Molten Arena",
        "Lava Dome Sanctum",
    ),
    "Coronet Highlands": (
        "Highlands Camp",
        "Mountain Camp",
        "Summit Camp",
        "Moonview Arena",
        "Stone Portal",
        "Temple of Sinnoh",
        "Hall of Origin",
    ),
    "Alabaster Icelands": (
        "Snowfields Camp",
        "Hibernal Cave",
        "Icepeak Camp",
        "Icepeak Arena",
    ),
}

#: Page title to the name this dataset gives the place.
PAGES: dict[str, str] = {
    name.replace(" ", "_"): f"{area}, {name}"
    for area, names in SUBLOCATIONS.items()
    for name in names
}

#: What a heading over a group of rows means, in this project's words.
#:
#: These pages have no Location column: the way a player meets something is written once above a
#: group of rows, and the rows that sit under no heading at all are the ordinary ones. So ``""``
#: is a real key here and it is the commonest.
#:
#: **Three of Let's Go's words do most of the work**, because these two games ask the same thing
#: of a player: there is no grass, no rod and nothing rolled when they walk - what is standing
#: in the world is what is there, and they choose which one to touch. Hisui adds two ways of its
#: own, and both had to be measured before they could be named. A heading that is not here is
#: skipped, which is how the gift, the boxes of a request and the two "Special Pokemon" stay out
#: of the grass and wait for step 4.
#:
#: The wiki spells the outbreak heading three ways on three pages - "Mass outbreak", "Mass
#: Outbreak" and "Mass outbreak s" - and all three are here rather than being tidied into one
#: by lowercasing, because a heading nobody typed would then be silently accepted.
METHODS: dict[str, EncounterMethod] = {
    "": EncounterMethod.OVERWORLD,
    "Fixed Alpha": EncounterMethod.OVERWORLD,
    "Water": EncounterMethod.OVERWORLD_WATER,
    "In the air": EncounterMethod.OVERWORLD_FLYING,
    "Flying": EncounterMethod.OVERWORLD_FLYING,
    "Mass outbreak": EncounterMethod.SWARM,
    "Mass Outbreak": EncounterMethod.SWARM,
    "Mass outbreak s": EncounterMethod.SWARM,
    "Space-time distortions": EncounterMethod.SPACE_TIME_DISTORTION,
    "Shaking trees": EncounterMethod.SHAKEN_LOOSE,
    "Shaking ore deposits": EncounterMethod.SHAKEN_LOOSE,
    "Boxes": EncounterMethod.SHAKEN_LOOSE,
    "Unown Research Notes": EncounterMethod.OVERWORLD,
}

#: What the species cell writes after the name, and the suffix this dataset spells it with.
#:
#: These pages run a form's name straight onto the species name, so the cell reads
#: "SneaselHisuian Form". Most of what turns up there is the source naming a *default* rather
#: than a choice - a Plant Cloak Burmy, an Incarnate Forme Tornadus, a West Sea Shellos - and
#: those map to nothing, which leaves the record about the species.
#:
#: **Thirteen phrases, and they were collected rather than guessed.** The first draft of this
#: table was written from what the dex list page spells and got three of them wrong: the wiki
#: writes "Trash Cloak" where that page writes "Plant Cloak", and it writes White-Striped with a
#: **non-breaking hyphen** and sometimes with the sex in brackets. The reader logs a phrase
#: nothing here names, and that is what found all three.
#: How the wiki spells White-Striped, which is not how anybody types it: the hyphen is
#: U+2011, the non-breaking one. Written as an escape so that it is visible rather than a
#: character that looks exactly like the ordinary one.
STRIPED = "White\u2011Striped"

FORM_PHRASES: dict[str, str] = {
    "Hisuian Form": "Hisui",
    "Alolan Form": "Alola",
    "Sandy Cloak": "Sandy",
    "Trash Cloak": "Trash",
    "East Sea": "East",
    # The wiki writes this one with a non-breaking hyphen, and writes it three ways: on its own
    # and with the sex in brackets. This dataset holds one White-Striped Basculin, so all three
    # land on it. Found by the reader's own warning rather than by reading the page: every
    # spelling here is one the pages actually use.
    **dict.fromkeys(
        (
            STRIPED,
            f"{STRIPED} (Male)",
            f"{STRIPED} (Female)",
        ),
        "White-Striped",
    ),
    "Female": "Female",
    # And the defaults, which are the source naming what a species already is rather than a
    # choice: a Plant Cloak Burmy, a west sea Shellos, the Johtonian Sneasel the distortions
    # hold beside the Hisuian one, and the Kantonian Vulpix the Pokedex lists.
    "Plant Cloak": "",
    "West Sea": "",
    "Johtonian Form": "",
    "Kantonian Form": "",
}


#: What a heading says that the method it maps to cannot.
#:
#: A group that explains itself gets no other sentence: :func:`legends_encounters` writes "Only
#: as an alpha" on a row whose ordinary Levels column is empty, and a fixed alpha's is always
#: empty, so saying both would say alpha twice.
METHOD_REQUIREMENTS: dict[str, str] = {
    "Fixed Alpha": (
        "One particular alpha, which stands in one spot and is there every time - unlike the "
        "rest, which are rolled when the area is entered"
    ),
    "Mass outbreak": "Only while an outbreak of it is running",
    "Mass Outbreak": "Only while an outbreak of it is running",
    "Mass outbreak s": "Only while an outbreak of it is running",
    "Shaking trees": "Knock it out of a shaking tree",
    "Shaking ore deposits": "Knock it out of a shaking ore deposit",
    "Boxes": "Break open one of the boxes",
    "Unown Research Notes": "Hidden in one spot, which the Unown Research Notes describe",
}


#: The page the form-change sentences and the list of what was removed were read from.
FORMS_PAGE = "Pok%C3%A9mon_Legends:_Arceus"

#: The pages each of step 4's claims was read from, and the day a person read it.
#:
#: Two kinds. ``Request`` is the list of every mission and request in the game, and it is what
#: says which of them hands a Pokemon over and what has to be done first; the species' own
#: articles are what say **where each one stands**, which the list does not. So a static cites
#: its own species page and the two outright gifts cite the list.
READ_ON = ReadByHand(
    dict.fromkeys(
        (
            "Request",
            FORMS_PAGE,
            *(
                f"{one}_(Pok%C3%A9mon)"
                for one in (
                    "Arceus",
                    "Azelf",
                    "Cresselia",
                    "Cyndaquil",
                    "Darkrai",
                    "Dialga",
                    "Enamorus",
                    "Giratina",
                    "Heatran",
                    "Landorus",
                    "Manaphy",
                    "Mesprit",
                    "Oshawott",
                    "Palkia",
                    "Phione",
                    "Regigigas",
                    "Rowlet",
                    "Shaymin",
                    "Spiritomb",
                    "Thundurus",
                    "Tornadus",
                    "Uxie",
                    "Vulpix",
                )
            ),
        ),
        date(2026, 9, 25),
    )
)

#: The one page that lists every mission and request, and so every Pokemon one of them hands over.
QUESTS_PAGE = "Request"


def _static(
    species: str,
    location: str,
    requirement: str,
    page: str | None = None,
    form: str | None = None,
) -> RecordedGift:
    """One Pokemon standing in one place, cited to its own article.

    ``page`` is only given when the species this dataset names and the article the wiki keeps
    are spelled differently, which they are not yet - it is here so that the day one is, the
    answer is a word rather than a second table.
    """
    return RecordedGift(
        species=species,
        location=location,
        form=form,
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement=requirement,
        source=READ_ON(page or f"{species.title()}_(Pok%C3%A9mon)"),
    )


#: Everything this game hands over or leaves standing in one spot.
#:
#: **No levels, and that is a gap rather than a decision.** Every other game in this dataset
#: takes its gifts from PokeAPI, which carries the level; there is nothing for this one, and the
#: pages that say where each of these stands do not say what level it is at. A number nobody
#: read is worse than no number.
#:
#: **Nineteen of the twenty-two are a mission or a request**, which is this game's shape: there
#: is no cave you can simply walk into and find a deity in. The list of them is one page and the
#: place each one stands is twenty-one others, which is why each record cites its own.
GIFTS: tuple[RecordedGift, ...] = (
    # The three that start it, and all three are gettable in one save file. Laventon offers a
    # choice of the three he has just chased across Obsidian Fieldlands; after Mission 18 he
    # hands over the two that were not picked. Every other starter in this dataset needs a trade
    # or a second cartridge.
    *(
        RecordedGift(
            species=species,
            location="Jubilife Village",
            kind=GiftKind.STARTER,
            npc="Professor Laventon",
            requirement=(
                "Pick one of the three at the Galaxy Team's entry trial; Professor Laventon "
                "hands over the other two after Mission 18"
            ),
            source=READ_ON(f"{species.title()}_(Pok%C3%A9mon)"),
        )
        for species in ("rowlet", "cyndaquil", "oshawott")
    ),
    # The two the story is about. One is caught at the temple in Mission 17 - which one depends
    # on whether the player went looking for the Red Chain with Adaman or with Irida - and the
    # other is caught in the same place in Mission 18, with a ball made out of the broken chain.
    # So the clan a player sides with changes the order and not the answer.
    _static(
        "dialga",
        "Coronet Highlands, Temple of Sinnoh",
        "Mission 17 if the player sided with Adaman, and Mission 18 with the Origin Ball if not",
    ),
    _static(
        "palkia",
        "Coronet Highlands, Temple of Sinnoh",
        "Mission 17 if the player sided with Irida, and Mission 18 with the Origin Ball if not",
    ),
    _static(
        "giratina",
        "Cobalt Coastlands, Turnback Cave",
        "Request 91, after Mission 26, and it is in its Origin Forme",
    ),
    # The three lake guardians, each in the cavern under its own lake, and each setting a trial
    # of its own before it will be caught.
    _static(
        "mesprit",
        "Obsidian Fieldlands, Verity Cavern",
        "Mission 21, and it sets a trial before it can be caught",
    ),
    _static(
        "azelf",
        "Crimson Mirelands, Valor Cavern",
        "Mission 21, and it sets a trial before it can be caught",
    ),
    _static(
        "uxie",
        "Alabaster Icelands, Acuity Cavern",
        "Mission 21, and it sets a trial before it can be caught",
    ),
    # Cogita's four, which are the plates rather than the story.
    _static("heatran", "Cobalt Coastlands, Lava Dome Sanctum", "Mission 22, after Mission 20"),
    _static("cresselia", "Coronet Highlands, Moonview Arena", "Mission 23, after Mission 20"),
    _static(
        "regigigas",
        "Alabaster Icelands, Snowpoint Temple",
        "Mission 24, and the Stone, Icicle and Iron Plates have to be in the bag",
    ),
    _static(
        "arceus",
        "Coronet Highlands, Hall of Origin",
        (
            "Mission 27: meet every Pokemon there is to meet, then play the flute on the dais in "
            "the Temple of Sinnoh"
        ),
    ),
    # The four Forces of Nature, which Cogita sets loose once the plates are gathered. Two of
    # them only appear in one state of the sky, which is the only place in this game where the
    # weather decides whether something is there at all.
    _static(
        "tornadus",
        "Alabaster Icelands, Bonechill Wastes",
        "Request 94, and only during a blizzard",
    ),
    _static(
        "thundurus",
        "Cobalt Coastlands, between Sand's Reach and Lunker's Lair",
        "Request 94, and only during a thunderstorm",
    ),
    _static("landorus", "Obsidian Fieldlands, Ramanas Island", "Request 94"),
    _static(
        "enamorus",
        "Crimson Mirelands, Scarlet Bog",
        "Request 94, once Tornadus, Thundurus and Landorus are all in the Pokedex",
    ),
    # The two whose requests only exist if another game is on the console, which is the mirror
    # of the Azure Flute: Brilliant Diamond gets its Arceus because this game has been played,
    # and this game gets its Darkrai because Brilliant Diamond has. A save file is not a route
    # between two games and this dataset draws no edge for it - what it is is a condition on one
    # record, and it is the only condition of its kind in the dataset.
    _static(
        "shaymin",
        "Obsidian Fieldlands, Floaro Gardens",
        (
            "Request 92, in the field of Gracidea flowers, and the request only appears if the "
            "console has Sword or Shield save data on it"
        ),
    ),
    _static(
        "darkrai",
        "Coronet Highlands, near Clamberclaw Cliffs",
        (
            "Request 93, at night, and the request only appears if the console has Brilliant "
            "Diamond or Shining Pearl save data on it"
        ),
    ),
    # The two from the sea, and the reason Phione is here as well as in the water tables: the
    # wiki's encounter table for Seaside Hollow says a Phione is there and does not say that it
    # is only there during the request.
    _static(
        "manaphy",
        "Cobalt Coastlands, Seaside Hollow",
        'Request 66, "The Sea\'s Legend", which needs Star Rank 5 and Mission 10 finished',
    ),
    _static(
        "phione",
        "Cobalt Coastlands, Seaside Hollow",
        (
            "Three of them during Request 66, and as many as you like once the Manaphy beside "
            "them has been caught"
        ),
    ),
    # And the Alolan Vulpix, which is the answer to a question step 1 could not settle. The
    # Hisui Pokedex's Vulpix is the Kantonian one; this is a second Vulpix, in the game, that
    # the list has no page for - and it is why HOME lets an Alolan Vulpix in when it refuses
    # every other regional form of a listed species.
    _static(
        "vulpix",
        "Alabaster Icelands, Whiteout Valley",
        (
            "Request 83, and it is the Alolan Vulpix rather than the Kantonian one the Hisui "
            "Pokedex lists"
        ),
        form="vulpix-alola",
    ),
    # The only two that are handed over rather than caught, and both are a villager's thank-you.
    RecordedGift(
        species="spiritomb",
        location="Jubilife Village",
        npc="Vessa",
        requirement=(
            "Request 22: gather the 107 wisps scattered across Hisui and take the last one from "
            "the Shrouded Ruins at night"
        ),
        source=READ_ON(QUESTS_PAGE),
    ),
)


#: Where this game gets its pictures, which step 6 filled in: a sheet of its own.
#:
#: **The only one of the last five games in the series with one.** Sword and Shield have ``8s``,
#: and after them Brilliant Diamond, Shining Pearl, Scarlet and Violet draw Pokemon HOME's
#: renders because the Archives have no sheet for any of them. This game has ``8a``, 367 files,
#: and it draws only its own 242 - ``Spr_8a_001.png`` is a 404 because Bulbasaur is not in Hisui.
SPRITE_SET = HISUI_SET


#: Why step 7 wrote nothing, which is worth a paragraph rather than an empty table.
#:
#: **This game has no unobtainable entry at all**, and it is the only one of the thirty-five in
#: this dataset with a Pokedex of which that is true. Sword leaves 17 of its 821 to another
#: game, Gold leaves 17 of 251, Pearl leaves 4 of 151 - and every one of those is where step 7
#: does its work, turning "nothing can produce this" into "nothing you can play can produce
#: this, and here is what once did". There is nothing here for it to turn.
#:
#: Two things keep that from being a boast:
#:
#: * **Two of the 242 need another game on the console.** Shaymin's request appears only with
#:   Sword or Shield save data and Darkrai's only with Brilliant Diamond or Shining Pearl save
#:   data. Both are recorded as a gift with a requirement rather than as unobtainable, which is
#:   the call Brilliant Diamond's Arceus got for the same reason in reverse - and it is a
#:   condition a player can meet, unlike a distribution that closed in 2006.
#: * **Three of the 242 stand on a chain step 8 has not finished.** Basculegion, Overqwil and
#:   Sneasler are produced by nothing here but an evolution, and each of those evolutions starts
#:   from a form - White-Striped Basculin, Hisuian Qwilfish, Hisuian Sneasel - that no record in
#:   this game yet names, because step 3's records name species. The validator says so itself as
#:   ``no-evolution-dead-ends``, and closing it is step 8's.
NOTHING_IS_UNOBTAINABLE = True


#: How a form that is not simply met is come by. A sex needs no line: :mod:`formchanges` answers
#: it once for every region.
#:
#: **Twelve sentences for 117 forms**, which is what this game being what it is comes to. The
#: sixteen Hisuian forms are not changed into, they are the Growlithe and the Voltorb that live
#: here; the Alolan pair is a request and a stone; Unown's letters are found one at a time; the
#: east sea Shellos swims off a different coast. What is left is the eleven a player does
#: something to a Pokemon they already have to get.
#:
#: **Eight of the twelve are an item used out of the satchel**, because this game has no
#: held items: the Griseous Orb that Giratina carried in Platinum is a Griseous *Core* here and
#: it is used on it. Three for the deities, four for the Forces of Nature and the Gracidea for
#: Shaymin; the other four are Burmy's cloaks, which are decided by where it last fought.
FORM_CHANGES: dict[str, FormChange] = {
    "dialga-origin": FormChange(
        requirement=(
            "Use the Adamant Crystal on it from the satchel. There are no held items here, so "
            "unlike every later game it is used rather than carried"
        )
    ),
    "palkia-origin": FormChange(
        requirement="Use the Lustrous Globe on it from the satchel"
    ),
    "giratina-origin": FormChange(
        requirement=(
            "Use the Griseous Core on it from the satchel. It is the Griseous Orb Platinum had "
            "it hold, and it is used here rather than carried"
        )
    ),
    **spread(
        FormChange(requirement="Use the Reveal Glass on it, which Cogita hands over"),
        "tornadus-therian",
        "thundurus-therian",
        "landorus-therian",
        "enamorus-therian",
    ),
    "shaymin-sky": FormChange(
        requirement=(
            "Use the Gracidea on it. The Gracidea only arrives with the save data bonus from "
            "Sword or Shield, which is the same bonus that makes the Shaymin request appear at "
            "all - so a console without those two has neither"
        )
    ),
    **spread(
        FormChange(
            requirement=(
                "Its cloak is made of whatever it last battled in - sand in caves and on sand, "
                "rubbish indoors, and leaves everywhere else"
            )
        ),
        "burmy-sandy",
        "burmy-trash",
    ),
    **spread(
        FormChange(
            requirement=(
                "The cloak its Burmy was wearing when it evolved, which it keeps for good; "
                "only the Burmy's own cloak can still be changed"
            )
        ),
        "wormadam-sandy",
        "wormadam-trash",
    ),
}


def entity() -> Game:
    """The game as the dataset holds it."""
    return Game(
        id=GAME_ID,
        title="Pokémon Legends: Arceus",
        version="Legends: Arceus",
        generation=GENERATION,
        region=REGION,
        release=GameRelease.CARTRIDGE,
        released=RELEASED,
        national_dex_through=NATIONAL_DEX_THROUGH,
        dex_source=DexSource.GAME_DEX,
        pair_partner=None,
        sprite_set=SPRITE_SET,
    )


#: What PokeAPI calls the one Pokedex this game shows.
DEX = "hisui"

#: How many entries it has, which is also how many tiles a collection of this game draws.
#:
#: 242, and **238 of them are what the game asks for**: Phione, Manaphy, Shaymin and Darkrai sit
#: at the end and are not required to complete the Pokedex. That is a fact about the game's own
#: reward rather than about a living dex, which wants all 242 - so it is written here and used
#: nowhere.
DEX_SIZE = 242


def build(context: BuildContext) -> GameData:
    """The game entity, the 242 it shows, and every wild slot that fills one."""
    entries = dex_entries(context)

    return GameData(
        game=entity(),
        dex_entries=entries,
        acquisition_methods=[
            *acquisition_methods(context, entries=entries),
            *handed_over(context, entries=entries),
            *evolves(context, entries=entries),
            *form_change_encounters(
                game_id=GAME_ID,
                forms=context.forms_here(),
                changes=FORM_CHANGES,
                citation=READ_ON(FORMS_PAGE),
            ),
        ],
    )


def dex_entries(
    context: BuildContext,
    *,
    unobtainable: Mapping[str, str] | None = None,
) -> list[DexEntry]:
    """The Hisui Pokedex: Rowlet #001 to Darkrai #242.

    One list, so no entry names which dex it is numbered in - the same rule every game before X
    and Y followed, and the opposite of Galar's three. And the whole of what a living dex here
    aims at, which is the other half of what ``dexSource`` gameDex means: there is no National
    Dex above this to count towards.

    **Checked against the wiki row by row rather than trusted.** PokeAPI's ``hisui`` and
    Bulbapedia's list agree on all 242 entries, in the same order, with the same numbers. The
    only place the two texts differ is that the wiki names a form where the source names a
    species - 32 rows of it, "DecidueyeHisuian Form" against ``decidueye`` - and that difference
    is the interesting one, because it is most of this game's character.

    **Nothing here carries a form**, for the reason Galar's list gives: these lists number
    species, and which Decidueye, which Growlithe, which Basculin is the shared forms table's to
    say at step 8. What is worth knowing before then is that this game leans on that answer
    harder than any game in the dataset: **sixteen of the 242 species exist here only as their
    Hisuian form**, so a grid drawn with forms switched off will show a Kantonian Growlithe on a
    tile a player of this game can only fill with the Hisuian one. Sinnoh had Burmy's cloaks and
    Shellos's two seas; here it is a quarter of what makes the game itself.

    And two more the list is quiet about, which are a surprise rather than a form question:
    **#168 and #169 are the Kantonian Vulpix and Ninetales** - the snow in the Alabaster Icelands
    is full of the Vulpix that is not the icy one - while the Alolan pair can be carried in
    without being listed at all. :data:`HELD_WITHOUT_BEING_LISTED` is where that is written down.
    """
    reasons = unobtainable or {}
    api = context.require_api()

    return [
        DexEntry(
            game=GAME_ID,
            target=DexTarget(species=species),
            number=number,
            unobtainable_reason=reasons.get(species),
        )
        for number, species in api.pokedex(DEX, refresh=context.refresh)
    ]


def acquisition_methods(
    context: BuildContext,
    *,
    entries: Sequence[DexEntry],
) -> list[AcquisitionMethod]:
    """Every wild slot this game has, which for now is every way to get anything in it.

    Step 3 only. There is no ``wild_encounters`` call beside this one and there will not be:
    PokeAPI carries nothing at all for this game, which is what the reading before Generation
    8's remaining games found and is true of all six of them.

    The species asked about are the game's own 242 rather than a National Dex slice, which is
    what :meth:`BuildContext.living_dex` does for a game with no National Dex - the same answer
    Galar gets, and the opposite of Brilliant Diamond's.
    """
    species = context.living_dex(through=NATIONAL_DEX_THROUGH, entries=entries)

    return list(
        legends_encounters(
            context.require_wiki(),
            game_id=GAME_ID,
            pages=PAGES,
            methods=METHODS,
            requirements=METHOD_REQUIREMENTS,
            species=set(species),
            forms=context.forms_here(),
            form_names=FORM_PHRASES,
            refresh=context.refresh,
        )
    )


def handed_over(
    context: BuildContext,
    *,
    entries: Sequence[DexEntry],
) -> list[AcquisitionMethod]:
    """Everything this game hands over or leaves standing in one spot.

    All of it written down by hand, which no game in this dataset before Brilliant Diamond had
    to do and every game after it will: PokeAPI carries no encounter of any kind for this game,
    and a gift is an encounter to that source.
    """
    species = context.living_dex(through=NATIONAL_DEX_THROUGH, entries=entries)

    return list(
        recorded_gifts(
            game_id=GAME_ID,
            gifts=GIFTS,
            species=species,
            citation=READ_ON(QUESTS_PAGE),
        )
    )


#: What PokeAPI calls the group whose evolution rules this game plays by.
#:
#: Its own, and it is the first game in this dataset whose group is a group of one: Brilliant
#: Diamond reaches back to ``diamond-pearl`` because a remake keeps its original's answers, and
#: this reaches nowhere because nothing else evolves the way it does.
EVOLUTION_GROUP = VERSION_GROUP


def evolves(
    context: BuildContext,
    *,
    entries: Sequence[DexEntry],
) -> list[AcquisitionMethod]:
    """Every evolution that works in Hisui.

    **And nothing else, which is most of what step 5 is here.** There is no in-game trade in
    this game - not one NPC will swap anything, and the only trading is with another player over
    the internet - so there is no ``trade_encounters`` call. There is no day care and no egg
    either: nothing in Hisui breeds, which makes this the second game in the dataset with no
    ``breeding_encounters`` after the Let's Go pair, and for the same kind of reason. Both are
    absences worth stating rather than lines quietly not written.
    """
    species = context.living_dex(through=NATIONAL_DEX_THROUGH, entries=entries)

    return list(
        evolution_encounters(
            context.require_api(),
            game_id=GAME_ID,
            version_group=EVOLUTION_GROUP,
            species=species,
            forms=context.forms_here(),
            all_forms=context.forms,
            refresh=context.refresh,
        )
    )


def edges() -> list[TransferEdge]:
    """HOME in both directions, and that is the whole of it.

    HOME arrived on 18 May 2022 in its version 2.0.0, four months after the game and the same
    day it reached Brilliant Diamond and Shining Pearl - so for a third of a year the three
    newest games in the series had no way out at all. As with that pair, the dataset holds that
    the route exists rather than when it opened: when a service was updated is a fact about the
    service.

    **The withdrawal's** ``PresentInTargetDexFilter`` **is the wiki's own sentence here.** "Only
    Pokemon in the Hisui Pokedex can be transferred into Pokemon Legends: Arceus" is exactly
    what that filter asks - does the game being transferred into list this one - so step 2 is
    what makes this edge honest, and nothing written here has to name a species.

    **Three things the filter does not say, read rather than assumed:**

    * **Regional forms of a listed species cannot come in either**, with Alolan Vulpix and
      Alolan Ninetales excepted - and step 2 found that the exception is a real one rather than
      the wiki naming this game's own entries: the Hisui Pokedex's Vulpix and Ninetales are the
      Kantonian ones. :data:`HELD_WITHOUT_BEING_LISTED` is that pair. The filter as the app
      implements it lets a form through whenever the target lists its species, which happens to
      be right for those two and wrong for every other regional form of a listed species.
      Whether it reaches a tile is step 8's to settle, and it is the same question Brilliant
      Diamond left open.
    * **A Pokemon that has been in Legends: Z-A can never come back**, which is a fact about one
      Pokemon's history rather than about a species. This dataset records where a route goes.
    * **Anything arriving from elsewhere is put in a Strange Ball** and has its moves rewritten
      to its four most recent level-up ones. Neither changes which entry it fills.

    Registering this lights nothing that was waiting, which is the expected answer for the fifth
    Generation VIII game running: HOME is the only door this generation has, and every older
    game that can reach this one was already reaching HOME.
    """
    return home.home_edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Legends Arceus EN boxart.png")
