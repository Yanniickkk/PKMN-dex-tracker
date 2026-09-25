"""Pokemon Legends: Z-A: what it is, and the one route it brings.

Phase 2 step 1 for this game, and nothing after it yet. The third and last Generation IX core
series game and the second "Pokemon Legends" game, and like the first of those it is not half
of a pair - so there is no shared module beside this one and no partner to name.

**It does read from one region module, and that was arranged three generations early.**
:mod:`kalos` was written for X and Y with a paragraph at the top saying that Legends: Z-A is
Lumiose City on the Switch and will read from this file too, and that nothing in it should have
to be edited to let that happen. Step 1 asks it for exactly one thing - the region's name - and
it was there. Whether the rest of that promise holds is steps 2 to 5's to find out, and the
answer will be interesting either way: a fact that has to be moved out of :mod:`kalos` to be
used here is a fact about Generation 6 that was written down as a fact about Kalos.

**Two modules it deliberately does not read from**, each for a reason worth writing down rather
than discovering later:

* A generation module. There is no ``gen9.py`` and on the evidence of Generation 8 there will
  not be one: that generation ended with three modules and nothing left for a fourth to say.
  Scarlet and Violet will want a ``paldea.py`` between them; this game is somewhere else
  entirely, and what it has in common with them is Pokemon HOME, which :mod:`home` has held
  since before any of the three existed.
* A ``legends.py`` shared with Legends: Arceus. :mod:`legends_arceus` refused this in the other
  direction and it is still right. The two games share a **table reader** - which lives in
  :mod:`encountertables` beside the others, because it is about a shape on a wiki page and not
  about a game - and beyond that they share a word in a title. Different generation, different
  region, different dex shape, different Pokeballs, and one of them has alphas as a column where
  the other has them as a heading.

**And it brings one route where every Switch game before it brought two.** Step 0 read the
service's own sentence: Pokemon transferred into this game cannot be transferred back to
previous games, nor can Pokemon obtained in it. :func:`edges` is where that is drawn, and it is
the first game in this dataset with a way in and no way out.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from ..archives import HOME_SET
from ..encountertables import legends_encounters
from ..evolutions import evolution_encounters
from ..formchanges import FormChange
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
    PresentInTargetDexFilter,
    TransferDirection,
    TransferEdge,
    TransferMechanism,
)
from ..sources import ReadByHand
from ..trades import InGameTrade, trade_encounters
from . import home, kalos

GAME_ID = "legends-z-a"

#: Generation 9, and the last of it.
GENERATION = 9

#: Kalos, which is where Lumiose City has always been.
#:
#: **Not the shape Hisui got, and the difference is the whole point of the field.**
#: :mod:`legends_arceus` writes Hisui rather than Sinnoh because a player of that game never
#: hears the word Sinnoh: it is the same ground at a time when nobody had named it that. Here
#: the name has not changed, the era has not changed, and X and Y are set in the same region
#: with the same city in them - so the region is Kalos, taken from :mod:`kalos` rather than
#: spelled again here, and the picker will show two entries under one region three generations
#: apart the way it already does for Kanto and Johto.
#:
#: The city is not the region. This game is played entirely inside Lumiose City, which makes it
#: the smallest place any game here is set in, and that is a fact about its map rather than
#: about where it is.
REGION = kalos.REGION

#: One day, everywhere: Japan, North America, Europe, Australia, South Korea, Hong Kong and
#: Taiwan all on 16 October 2025. The same shape Legends: Arceus had, and by now the norm.
#:
#: There is a Nintendo Switch 2 Edition with its own cover, and it is not a second entity here
#: any more than a console revision ever is: one game, sold twice.
RELEASED = date(2025, 10, 16)

#: What PokeAPI calls this game, and what it calls the group that holds it.
#:
#: **Both are** ``legends-za``, **with no hyphen before the A**, where this dataset's own id for
#: the game is ``legends-z-a``. Step 0 found that by asking for ``version-group/legends-z-a`` and
#: getting a 404, which is the cheapest possible way to find it and the reason that step exists.
#: The id stays as the TODO wrote it - it is this dataset's word, and it matches the title - and
#: only the source's spelling lives here.
POKEAPI_VERSION = "legends-za"
VERSION_GROUP = "legends-za"

#: The expansion, which is folded into this game rather than held beside it.
#:
#: **Sword and Shield already answered this.** The source models Mega Dimension as a version
#: group of its own, ``mega-dimension``, exactly as it models the Isle of Armor and the Crown
#: Tundra - and :mod:`galar` reads all three as one game with three Pokedexes, because a player
#: who owns the expansion is playing one game. Here it is one game with two: the 232 of Lumiose
#: and the 132 of Hyperspace.
#:
#: Which of the two dexes the base game shows on its own is not a question this dataset asks.
#: A collection names a game, and the tiles it draws are what that game can hold.
EXPANSION = "mega-dimension"


#: The two Pokedexes this game shows, in the order a player meets them.
#:
#: **Galar's shape, and the trap Galar's step 2 warned about turns out not to be here.** Sword
#: and Shield show three lists whose 821 entries are 584 species, because a Magikarp is numbered
#: once in Galar and again on the Isle of Armor - so :data:`galar.DEX_TOTAL` is entries and not
#: species, and reading it as species would overcount the game by 237. **These two share
#: nothing at all**: 232 and 132 are 364 entries and 364 species, checked rather than assumed.
#: It is the first game in the dataset with more than one list where the lists do not overlap.
#:
#: The second is the expansion's, which is why it is second. A player without Mega Dimension
#: sees one list of 232; the dataset holds the game a player who owns it plays, which is the
#: call :mod:`galar` made for the Isle of Armor and the Crown Tundra.
DEXES: tuple[tuple[str, str], ...] = (
    ("lumiose-city", "Lumiose"),
    ("hyperspace", "Hyperspace"),
)

#: How many entries the two hold between them, which here is also how many species.
#:
#: **The arithmetic that is worth having in one place, because no other game's works out this
#: way.** 232 + 132 = 364 entries, 364 species, 0 in both.
DEX_TOTAL = 364

#: What each list is made of, which the two of them being disjoint makes worth writing down.
#:
#: **The base game is Kalos and the expansion is everything else.** Of the 232, seventy are
#: Generation VI species - and there are seventy-two of those in the series, the missing pair
#: being Hoopa and Volcanion, which are in the Hyperspace list instead. So the wiki's own line
#: that all of Generation VI is in the base game is off by exactly its two Mythicals.
#:
#: **And exactly two of the 232 are newer than Kalos**: Drampa from Alola and Falinks from
#: Galar. Both of them are in the 35 files step 0 read off the Archives, so both are here
#: because this game gives them a Mega. Nothing from Generation IX is in the base game's list at
#: all - the wiki says so and the count agrees - and thirty-two of the expansion's 132 are.
#:
#: Written down and used nowhere: it is a description of the lists rather than a rule about
#: them, and the lists themselves come from the source.
DEX_SHAPE = "232 Lumiose, 70 of them Kalos; 132 Hyperspace, 32 of them Generation IX"

#: There is no National Pokedex here, and the boxes hold a list rather than everything up to a
#: number.
#:
#: The third game running to leave this empty, and the first to do it with two lists. What
#: :mod:`galar` had to write down as :data:`galar.FOREIGN_TO_EVERY_DEX` - eighty species those
#: games hold without listing - and :mod:`legends_arceus` as two, this game so far needs none
#: of: the sentence in the source is that **only Pokemon in the Lumiose Pokedex and the
#: Hyperspace Pokedex can be transferred into Pokemon Legends: Z-A**, with no exception named
#: beside it.
#:
#: **Step 2 checked that by contrast rather than by not finding anything**, which is the only
#: way a missing sentence can be checked at all. :mod:`legends_arceus` has the same rule and a
#: clause after it - non-Hisuian regional forms of a listed species cannot be transferred in
#: either, "with the exception of Alolan Vulpix and Alolan Ninetales" - and that clause is what
#: :data:`legends_arceus.HELD_WITHOUT_BEING_LISTED` is. The article for this game has the rule
#: and stops. So there is no leftover here: Galar's is eighty, Hisui's is two, and this one's
#: is nothing, which makes it the first game with no National Dex whose Pokedexes really are
#: the whole of what its boxes hold.
NATIONAL_DEX_THROUGH = None


#: Which district each of the twenty wild zones is in, read off the overview table.
#:
#: **The whole game is one city**, which makes it the smallest place any game in this dataset is
#: set in, so the thing that plays the part Hisui's five areas play is Lumiose's six districts.
#: Wild Zone 11 straddles two of them and the page says so; it is written here as the one a
#: player enters it from. Wild Zone 20 is not in a district at all - it is Centrico Plaza, the
#: roundabout at the centre that the whole city is built around, and it is the last to open.
DISTRICTS: dict[int, str] = {
    1: "Vert District",
    2: "Vert District",
    3: "Rouge District",
    4: "Rouge District",
    5: "Bleu District",
    6: "Jaune District",
    7: "Magenta District",
    8: "Jaune District",
    9: "Magenta District",
    10: "Bleu District",
    11: "Jaune District",
    12: "Bleu District",
    13: "Rouge District",
    14: "Magenta District",
    15: "Jaune District",
    16: "Bleu District",
    17: "Vert District",
    18: "Magenta District",
    19: "Jaune District",
    20: "Centrico Plaza",
}

#: The eighteen types the expansion cuts its distortions by.
#:
#: Every one of them has a page and every page has the same shape, which was checked rather than
#: assumed: eighteen pages, none missing, none empty.
HYPERSPACE_TYPES: tuple[str, ...] = (
    "Bug",
    "Dark",
    "Dragon",
    "Electric",
    "Fairy",
    "Fighting",
    "Fire",
    "Flying",
    "Ghost",
    "Grass",
    "Ground",
    "Ice",
    "Normal",
    "Poison",
    "Psychic",
    "Rock",
    "Steel",
    "Water",
)

#: Every page whose tables this game reads, and what a record made from it calls the place.
#:
#: **Thirty-eight pages against Hisui's eighty-one, and they are two different shapes.** The
#: base game writes one page per wild zone, which is the shape Hisui's sublocations have. The
#: expansion writes one page per *type* and cuts each of them into sections by star rating,
#: with the zones numbered from one again inside every section - so the page is a third of the
#: name and :data:`PLACES` and the section supply the rest.
PAGES: dict[str, str] = {
    **{
        f"Wild_Zone_{number}": f"{district}, Wild Zone {number}"
        for number, district in DISTRICTS.items()
    },
    **{
        f"List_of_{one}-type_hyperspace_wild_zones": f"Hyperspace Lumiose, {one}-type"
        for one in HYPERSPACE_TYPES
    },
}

#: The headings on the expansion's pages that name a place rather than a way of being met.
#:
#: **Step 0 found this and it is the one thing about this game the reader did not already do.**
#: On every other Legends page a one-cell row inside a table says how the rows under it are met
#: - "Mass outbreak", "Fixed alpha Pokemon spawns". On these eighteen it says *where* they are,
#: and the same ten numbers come round again in each star rating's section. So the heading is
#: read as a place, the section is put in front of it, and a heading that is not here is passed
#: over with a warning the way an unknown method is - which is what keeps the footnote at the
#: foot of each table from being read as an eleventh zone.
#: The value is what a record says rather than what the heading says, which is why this is a
#: table and not a set: the page writes "Hyperspace Wild Zone 1" inside an article already
#: called Hyperspace Lumiose, and a record that said both would say hyperspace twice.
PLACES: dict[str, str] = {f"Hyperspace Wild Zone {n}": f"Wild Zone {n}" for n in range(1, 11)}

#: What each one-cell heading inside a table means, for the pages whose headings are methods.
#:
#: **Four headings for two hundred and sixty rows**, where Hisui needed thirteen. There is no
#: fishing here, nothing is shaken out of a tree, and there are no space-time distortions: a
#: Pokemon in this game is standing in the street, and the only question is which street.
METHODS: dict[str, EncounterMethod] = {
    "": EncounterMethod.OVERWORLD,
    "Fixed alpha Pokémon spawns": EncounterMethod.OVERWORLD,
    "Only during Main Mission 40": EncounterMethod.OVERWORLD,
    "Only during Side Mission 017": EncounterMethod.OVERWORLD,
}

#: What a heading says that the method it maps to cannot.
METHOD_REQUIREMENTS: dict[str, str] = {
    "Fixed alpha Pokémon spawns": (
        "One particular alpha, which stands in one spot and is there every time - unlike the "
        "rest, which have a small chance of being alpha wherever they spawn"
    ),
    "Only during Main Mission 40": "Only while Main Mission 40 is running",
    "Only during Side Mission 017": "Only while Side Mission 017 is running",
}

#: What the species cell writes after the name, and the suffix this dataset spells it with.
#:
#: **Forty-eight phrases, where Hisui had sixteen, and they are a different kind of phrase.**
#: These pages sometimes write a suffix - "Red Flower", "Amped Form" - and sometimes the whole
#: name over again: "Alolan Marowak", "Galarian Mr. Mime", "Heat Rotom". Both are here, because
#: what the table maps is what the cell says rather than a rule about how it says it.
#:
#: **Most of them map to nothing, and that is the point.** A phrase that names a *default* - a
#: Red Flower Flabebe, a Meadow Pattern Vivillon, a Male Meowstic, an Amped Toxtricity, a Curly
#: Tatsugiri - leaves the record about the species, because that is what those species already
#: are. What is left is the twenty-odd that name a real second form, and nineteen of those are
#: another region's: this game introduces no regional form of its own and holds more of other
#: people's than any game since Sword and Shield.
#:
#: **And Rotom's five appliances are here**, which :mod:`legends_arceus` had to leave out for
#: want of a mechanism. In Hisui the models existed and nothing said how a player changed one;
#: here they are in the grass, one heading at a time.
FORM_PHRASES: dict[str, str] = {
    # The ones that name a second form.
    "Blue Flower": "Blue",
    "Orange Flower": "Orange",
    "White Flower": "White",
    "Yellow Flower": "Yellow",
    "Garden Pattern": "Garden",
    "Female Meowstic": "Female",
    "Female Indeedee": "Female",
    "Female": "Female",
    "Low Key Form": "Low Key",
    "Droopy Form": "Droopy",
    "Stretchy Form": "Stretchy",
    "Blue Plumage": "Blue Plumage",
    "Yellow Plumage": "Yellow Plumage",
    "White Plumage": "White Plumage",
    "Alolan Meowth": "Alola",
    "Alolan Persian": "Alola",
    "Alolan Raichu": "Alola",
    "Alolan Marowak": "Alola",
    "Galarian Meowth": "Galar",
    "Galarian Mr. Mime": "Galar",
    "Galarian Slowpoke": "Galar",
    "Galarian Slowbro": "Galar",
    "Galarian Slowking": "Galar",
    "Galarian Yamask": "Galar",
    "Galarian Stunfisk": "Galar",
    "Galarian Farfetch'd": "Galar",
    "Hisuian Qwilfish": "Hisui",
    "Hisuian Sliggoo": "Hisui",
    "Hisuian Goodra": "Hisui",
    "Hisuian Avalugg": "Hisui",
    "Heat Rotom": "Heat",
    "Wash Rotom": "Wash",
    "Fan Rotom": "Fan",
    "Frost Rotom": "Frost",
    "Mow Rotom": "Mow",
    # And the ones that name what a species already is.
    "Red Flower": "",
    "Meadow Pattern": "",
    "Male Meowstic": "",
    "Male Indeedee": "",
    "Male": "",
    "Medium Variety": "",
    "Amped Form": "",
    "Curly Form": "",
    "Green Plumage": "",
    "Disguised Form": "",
    "Chest Form": "",
    # **The two this dataset cannot say**, and they are worth a line rather than a quiet zero.
    # A cell reading "all forms" or "All Flowers" means every one of them is here, and a record
    # names one target. So these leave the record about the species, which is true and less than
    # the page says - a Vivillon is in that zone, and which Vivillon is not written down.
    # Twenty-one rows, all of them Flabebe's line, Vivillon and Furfrou, and step 8 is where it
    # matters: those forms will have a tile and nothing here fills it.
    "all forms": "",
    "All Flowers": "",
}


#: The two pages step 4 was read from, and the day a person read each.
#:
#: **Two kinds, the way Hisui's were, and this time both are lists.** The event page is one
#: article carrying every Pokemon this game hands over or leaves standing, with the level and
#: the place for each; the gift page is where the *condition* is written - which mission, which
#: NPC, what has to be done first - and it covers only the gifts. So a gift cites the gift page
#: and a static cites the event list, and neither is cited for something it does not say.
GIFTS_PAGE = "Gift_Pok%C3%A9mon"
EVENTS_PAGE = "List_of_in-game_event_Pok%C3%A9mon_in_Pok%C3%A9mon_Legends:_Z-A"

READ_ON = ReadByHand(dict.fromkeys((GIFTS_PAGE, EVENTS_PAGE, "In-game_trade"), date(2026, 9, 25)))


def _static(
    species: str,
    location: str,
    requirement: str,
    level: int | None = None,
    form: str | None = None,
) -> RecordedGift:
    """One Pokemon standing in one place, cited to the list that says where it stands."""
    return RecordedGift(
        species=species,
        location=location,
        form=form,
        level=level,
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement=requirement,
        source=READ_ON(EVENTS_PAGE),
    )


def _gift(
    species: str,
    location: str,
    npc: str,
    requirement: str,
    level: int | None = None,
    kind: GiftKind = GiftKind.NPC_GIFT,
    form: str | None = None,
) -> RecordedGift:
    """One Pokemon somebody hands over, cited to the page that says on what condition."""
    return RecordedGift(
        species=species,
        location=location,
        form=form,
        level=level,
        kind=kind,
        npc=npc,
        requirement=requirement,
        source=READ_ON(GIFTS_PAGE),
    )


#: Everything this game hands over or leaves standing in one spot, written down by hand.
#:
#: **Sixty-eight entries over sixty-seven species**, which is more than any game in this dataset
#: has ever needed, and the reason is the one that gave it 520 places: PokeAPI carries no
#: encounter of any kind for this game, and a gift is an encounter to that source. Every line
#: here was read off a page. The species with two is Absol, which is beaten as a Rogue Mega in
#: the expansion and handed over by one in the base game.
#:
#: **Three things about this table are worth knowing before reading it.**
#:
#: * **There is no egg in it and there never will be.** The article says so in one line -
#:   abilities, breeding and Eggs are not featured in this game - which makes it the third here
#:   with no day care after the Let's Go pair and Legends: Arceus, and the second in a row.
#: * **Ten of them are the ten species nothing else could produce.** Step 3 left fourteen
#:   uncovered; these close ten of them, and the other four are evolutions.
#: * **A static outnumbers a gift two to one.** Twenty-one handed over - three starters, three
#:   fossils and fifteen others - against forty-seven standing in a spot, which is this game
#:   being what it is: a city where things wait on a street corner rather than a region where
#:   somebody meets you at a gate.
GIFTS: tuple[RecordedGift, ...] = (
    # --- the three this game starts a player with --------------------------------------------
    *(
        _gift(
            one,
            "Lumiose City",
            "Urbain / Taunie",
            "Pick one of the three offered on the player's first night in the city",
            level=5,
            kind=GiftKind.STARTER,
        )
        for one in ("chikorita", "tepig", "totodile")
    ),
    # --- and the two other regions' first partners, which are missions rather than a choice ---
    _gift(
        "chespin",
        "Academie Etoile",
        "Chespin",
        "Reward for Side Mission #007: A Feisty Chespin",
        level=14,
    ),
    _gift(
        "fennekin",
        "Magenta Sector 2",
        "Fennekin",
        "Reward for Side Mission #008: Get Well, Fennekin",
        level=14,
    ),
    _gift(
        "froakie",
        "North Boulevard",
        "Froakie",
        "Reward for Side Mission #009: A Challenge from Froakie",
        level=14,
    ),
    *(
        _gift(
            one,
            "Pokemon Research Lab 3F",
            "Mable",
            "Choose one of the three as the reward for Side Mission #022: A Call from Mable",
            level=5,
        )
        for one in ("bulbasaur", "charmander", "squirtle")
    ),
    # --- the fossils, which are bought rather than dug up -------------------------------------
    *(
        _gift(
            species,
            "Pokemon Research Lab 2F",
            "Reg",
            (
                f"Have Reg revive the {fossil}, which is bought at the Stone Emporium on Vernal "
                "Avenue. The first revival is what clears Side Mission #027: Restored from a "
                "Fossil"
            ),
            level=20,
            kind=GiftKind.FOSSIL,
        )
        for species, fossil in (("tyrunt", "Jaw Fossil"), ("amaura", "Sail Fossil"))
    ),
    _gift(
        "aerodactyl",
        "Pokemon Research Lab 2F",
        "Reg",
        (
            "Have Reg revive the Old Amber, which the Stone Emporium only sells once Side "
            "Mission #027: Restored from a Fossil is cleared"
        ),
        level=20,
        kind=GiftKind.FOSSIL,
    ),
    # --- and the rest of what somebody hands over ----------------------------------------------
    _gift(
        "spewpa",
        "Lumiose Museum",
        "Spewpa",
        (
            "Reward for Side Mission #021: Spewpa in the Museum. It evolves into the Marine "
            "Pattern Vivillon, which nothing else here produces"
        ),
        level=9,
    ),
    _gift(
        "absol",
        "Lumiose City",
        "Absol",
        "After defeating the Rogue Mega Absol",
        level=30,
    ),
    _gift(
        "stunfisk",
        "Wild Zone 11",
        "Terri",
        "Reward for Side Mission #072: Find My Galarian Stunfisk!",
        level=38,
        form="stunfisk-galar",
    ),
    _gift(
        "lucario",
        "Hotel Z",
        "AZ",
        "Waiting in the player's room after the credits, with Korrina's name on it",
        level=50,
    ),
    _gift(
        "floette",
        "Lumiose City",
        "Urbain / Taunie",
        (
            "Beat them in the 15th reward match of the Infinite Z-A Royale. It is the Eternal "
            "Flower Floette, with AZ's name on it, and it is the only one there is"
        ),
        level=72,
        form="floette-eternal",
    ),
    _gift(
        "gimmighoul",
        "Rouge Sector 1",
        "Thelo",
        'Handed over on starting Side Mission #122: Let\'s Golden Goooooo, nicknamed "Chestly"',
        level=5,
    ),
    _gift(
        "melmetal",
        "Hyperspace Lumiose",
        "Thelo",
        (
            "Handed over during Side Mission #193: Dreams of Meltan. This is the only game in "
            "the dataset that produces one without Pokemon GO"
        ),
        level=80,
    ),
    _gift(
        "magearna",
        "Quasartico Inc.",
        "Jett",
        "Reward for Side Mission #195: Restarting Magearna",
        level=80,
    ),
    _gift(
        "hoopa",
        "Hyperspace Lumiose",
        "Hoopa",
        "After defeating Hoopa Unbound during Side Mission #196: The Djinn Unbound",
        level=80,
    ),
    # --- the ones standing in a spot: the base game --------------------------------------------
    _static("sableye", "Wild Zone 4", "Standing in one spot rather than rolled with the area", 10),
    _static("mareep", "Wild Zone 1", "Standing in one spot rather than rolled with the area", 11),
    _static("diggersby", "Vernal Avenue", "Standing in one spot on the avenue", 28),
    _static("klefki", "The Sewers", "Standing in one spot in the sewers", 40),
    _static("gastly", "Old Building", "Standing in one spot in the old building", 40),
    _static("gengar", "Old Building", "Standing in one spot in the old building", 42),
    _static("garbodor", "Vert Sector 8", "Standing in one spot in the sector", 50),
    _static("mawile", "Magenta Sector 6", "Standing in one spot in the sector", 52),
    _static("emolga", "Jaune Sector 7", "Standing in one spot in the sector", 53),
    _static("carbink", "Magenta Sector 8", "Standing in one spot in the sector", 66),
    # The six alphas that are an event rather than a roll of the dice.
    *(
        _static(
            species,
            where,
            "One particular alpha, standing in one spot and there every time",
            level,
        )
        for species, where, level in (
            ("bunnelby", "Rouge Sector 8", 10),
            ("weedle", "Magenta Sector 3", 45),
            ("watchog", "Autumnal Avenue", 50),
            ("steelix", "Wild Zone 3", 70),
            ("gallade", "Wild Zone 5", 70),
            ("pangoro", "Wild Zone 9", 70),
        )
    ),
    # Kalos's own three, and the two the city was built over.
    _static("xerneas", "Wild Zone 11", "Waiting at the end of the story", 75),
    _static("yveltal", "Rouge Sector 2", "Waiting at the end of the story", 75),
    _static("zygarde", "Wild Zone 20", "Waiting at the end of the story", 84),
    _static("diancie", "Magenta Sector 8", "Waiting at the end of the story", 70),
    _static("mewtwo", "Lysandre Labs", "Waiting in the laboratory under the city", 70),
    # --- and the expansion's ------------------------------------------------------------------
    *(
        _static(
            species,
            where,
            (
                "Catch it after beating it as a Rogue Mega Evolution, which is the only way any "
                "of these ten is obtained"
            ),
            level,
        )
        for species, where, level in (
            ("absol", "Hyperspace Disaster Arena", 75),
            ("staraptor", "Hyperspace Hunting Grounds", 75),
            ("tatsugiri", "Hyperspace Sushi Paradise", 75),
            ("meowstic", "Hyperspace Second-Sight Arena", 75),
            ("heatran", "Hyperspace Infernal Arena", 80),
            ("kyogre", "Hyperspace Primordial Sea", 80),
            ("groudon", "Hyperspace Desolate Land", 80),
            ("rayquaza", "Hyperspace Sky Pillar", 85),
            ("darkrai", "Hyperspace Newmoon Nightmare", 85),
            ("zeraora", "Hyperspace Lumiose", 85),
        )
    ),
    _static("sandile", "Jaune Sector 6", "Standing in one spot in the sector", 38),
    _static("krokorok", "Jaune Sector 6", "Standing in one spot in the sector", 50),
    _static("nacli", "Vert Sector 8", "Standing in one spot in the sector", 40),
    _static(
        "sandygast", "Wild Zone 8", "Standing in one spot rather than rolled with the area", 40
    ),
    _static("nickit", "Bleu Sector 6", "Standing in one spot in the sector", 15),
    _static("volcanion", "Pokemon Research Lab", "Waiting in the laboratory", 80),
    _static("genesect", "Hyperspace Lumiose", "Waiting in hyperspace", 60),
    _static("marshadow", "Rouge Sector 1", "Waiting in the sector", 80),
    _static("meltan", "Rouge Sector 1", "Waiting in the sector", 70),
    # The seven a Special Scan turns up, all at the same level in the same place.
    *(
        _static(
            species,
            "Hyperspace Lumiose",
            "Turned up by a Special Scan, which is the only way any of these seven is obtained",
            60,
        )
        for species in (
            "latias",
            "latios",
            "cobalion",
            "terrakion",
            "virizion",
            "keldeo",
            "meloetta",
        )
    ),
)


#: The page the five trades were read from.
TRADES_PAGE = "In-game_trade"

#: Every NPC in this game who will swap one Pokemon for another.
#:
#: **Five, where the other Legends game has none**, and that is the more interesting half of
#: this step. :mod:`legends_arceus` had to write down that not one NPC in Hisui will swap
#: anything and that the only trading is with another player over the internet. This game puts
#: four traders on the street and a fifth in the expansion, and one of them is not optional:
#: the Pikachu for Heracross is part of Side Mission 002, which is part of Main Mission 5.
#:
#: **Two of the five hand back the species they were given**, which nothing else in this dataset
#: does: a Slowpoke for a Slowpoke and a Raichu for a Raichu. They are a nickname and another
#: trainer's name rather than a way of obtaining anything, so they fill no tile the player did
#: not already have - and they are here because leaving them out would make this table a list of
#: useful trades rather than a list of trades.
TRADES: tuple[InGameTrade, ...] = (
    InGameTrade(
        gets="heracross",
        wants="pikachu",
        location="Passage du Palais",
        npc="Tracie",
        requirement=(
            "Side Mission 002: A Use for an Evolution Stone!, which is part of Main Mission 5 - "
            "so this is the one trade in the dataset a player cannot decline and finish the story"
        ),
    ),
    InGameTrade(
        gets="riolu",
        wants="abra",
        location="Academie Etoile",
        npc="Bond",
    ),
    InGameTrade(
        gets="slowpoke",
        wants="slowpoke",
        location="South Boulevard",
        npc="Quille",
    ),
    InGameTrade(
        gets="raichu",
        wants="raichu",
        location="Quasartico Inc.",
        npc="Griddella",
    ),
    InGameTrade(
        gets="porygon2",
        wants="porygon",
        location="Bleu Sector 6",
        npc="Trian",
        requirement=(
            "The Porygon handed back is holding an Up-Grade, so it evolves the moment it "
            "arrives. It is the one trade evolution in this game a player can do alone"
        ),
    ),
)

#: What PokeAPI calls the groups whose evolution rules this game plays by.
#:
#: Its own and its expansion's, which is :data:`galar.EVOLUTION_GROUPS` in miniature and for the
#: same reason: a rule stamped with the expansion's name is still this game's.
EVOLUTION_GROUPS = (VERSION_GROUP, EXPANSION)


#: Why step 7 wrote nothing, which is worth a paragraph rather than an empty table.
#:
#: **Every one of this game's 364 entries is produced by this game**, checked rather than
#: assumed: not one is covered only by another game in the dataset, and not one carries an
#: unobtainable reason. So there is nothing for step 7 to turn from "nothing can produce this"
#: into "nothing you can play can produce this, and here is what once did", and no species' *In
#: events* section had to be read at all.
#:
#: It is the second game in the dataset of which that is true, after :mod:`legends_arceus` - and
#: this one gets there more comfortably. **Hisui's two caveats are both absent here.** Nothing
#: in this game waits on save data from another: Shaymin's request needs Sword or Shield on the
#: console and Darkrai's needs Brilliant Diamond or Shining Pearl, and searching every
#: requirement in this game for another game's name, for a date or for the word distribution
#: turns up nothing at all. Every legendary and Mythical here - all twenty-four of them, Mewtwo
#: to Zeraora - is standing in a spot or handed over by somebody in the game.
#:
#: **What is not settled is the order this was run in**, and that is worth saying plainly. The
#: checklist has step 7 after step 6, because its input is the list of entries nothing produces
#: and that is not known before. Step 6 cannot change that list - a picture is not a way of
#: obtaining anything - so running it here costs nothing. **Step 8 can**: seven of the 364 are
#: reachable only by evolving, and two of those seven start from a form rather than a species.
#: :data:`STANDS_ON_A_FORM` is those two, and if step 8 takes either form away from this game
#: they stop being produced and this constant stops being true.
NOTHING_IS_UNOBTAINABLE = True

#: The two entries step 8 could take away, which is the one thing step 7 leaves open.
#:
#: Runerigus is evolved from a Galarian Yamask and Sirfetch'd from a Galarian Farfetch'd, and
#: nothing else in this game produces either - no wild slot, no gift, no trade. Both of those
#: forms are in the wild tables, so both chains stand today; step 8 has to keep them.
STANDS_ON_A_FORM: dict[str, str] = {
    "runerigus": "yamask-galar",
    "sirfetchd": "farfetchd-galar",
}


#: How a form that is not simply met is come by. A sex needs no line: :mod:`formchanges` answers
#: it once for every region.
#:
#: **Empty, and that is the finding rather than an omission.** Legends: Arceus needed twelve
#: sentences for 117 forms, eight of them an item used out of the satchel. Every one of this
#: game's ninety is **caught, handed over, or evolved into** - there is nothing here a player
#: changes a Pokemon they already have into:
#:
#: * Rotom's five appliances are standing in the Electric-type distortions, which is the whole
#:   difference between this table and :data:`legends_arceus.FORM_CHANGES`. That game had the
#:   models and no mechanism; this one skips the mechanism and puts them in the grass.
#: * The Flabebe line's colours, the Squawkabilly plumages, the Tatsugiri, the Low Key
#:   Toxtricity, Pumpkaboo's and Gourgeist's sizes and every regional form are wild slots.
#: * The Eternal Flower Floette and the Galarian Stunfisk are handed over, and the Marine
#:   Pattern Vivillon is what the museum's Spewpa evolves into.
#: * The Roaming Gimmighoul is the one that is neither: it arrives from Pokemon HOME and nothing
#:   in this game makes one, which the species' own Game locations row says in as many words.
#:   That is a fact about a route rather than about a change, and :func:`edges` already draws it.
#:
#: Kept as an empty table rather than deleted, because "nothing here is changed into" is a claim
#: about the game worth being able to point at - and because the four forms step 8 left out are
#: exactly the four that would need a line here the day somebody reads how they are got.
FORM_CHANGES: dict[str, FormChange] = {}

#: Where this game gets its pictures.
#:
#: **HOME's renders, with a layer of its own over them**, which is Ultra Sun's shape rather than
#: Legends: Arceus's. Step 0 read the Archives' own category: 35 files under ``Legends:_Z-A
#: _models``, every one of them a Mega - ``Spr_9z_0121M.png`` - and **not one plain number**. So
#: there is nothing here to draw an ordinary Chikorita with, and the set underneath is the one
#: Brilliant Diamond and Shining Pearl already draw from.
#:
#: The layer itself is step 6's and step 8's, and it needs a table the way :data:`archives.
#: USUM_FORMS` is one. It also needs :func:`archives.form_names` to stop returning nothing for
#: the HOME set, which the comment there has been waiting for since Brilliant Diamond.
SPRITE_SET = HOME_SET


def entity() -> Game:
    """The game as the dataset holds it."""
    return Game(
        id=GAME_ID,
        title="Pokémon Legends: Z-A",
        version="Legends: Z-A",
        generation=GENERATION,
        region=REGION,
        release=GameRelease.CARTRIDGE,
        released=RELEASED,
        national_dex_through=NATIONAL_DEX_THROUGH,
        dex_source=DexSource.GAME_DEX,
        pair_partner=None,
        sprite_set=SPRITE_SET,
    )


def build(context: BuildContext) -> GameData:
    """The game entity, the 364 it shows, and every wild slot that fills one."""
    entries = dex_entries(context)

    return GameData(
        game=entity(),
        dex_entries=entries,
        acquisition_methods=[
            *acquisition_methods(context, entries=entries),
            *handed_over(context, entries=entries),
            *swapped(),
            *evolves(context, entries=entries),
        ],
    )


def dex_entries(
    context: BuildContext,
    *,
    unobtainable: Mapping[str, str] | None = None,
) -> list[DexEntry]:
    """Both Pokedexes, each entry saying which of the two it is numbered in.

    The same shape :func:`galar.dex_entries` has, for the same reason: two lists that each start
    at #001 would arrive as one list with two species numbered #001 unless each entry names
    the list it belongs to. What is different is that these two hold no species in common, so
    the entries and the species are the same number - which is not true of any other game here
    that shows more than one list.

    **Checked against the wiki row by row rather than trusted, and the two agree exactly.** All
    364 numbers line up and all 364 names do: PokeAPI's ``lumiose-city`` and ``hyperspace``
    against Bulbapedia's two list pages, with nothing to reconcile. That is a better result than
    Hisui's, where the wiki wrote a form where the source wrote a species on 32 rows - and the
    26 rows here whose text is longer than a species name are all the wiki naming a *default*:
    an Icy Snow Vivillon, a Male Meowstic, a Shield Forme Aegislash, an Ordinary Keldeo. The one
    row that looked like an exception was Zygarde, and it is the list showing all three formes
    under one number rather than choosing one.

    **Nothing here carries a form**, which is the rule every game's dex list follows: these
    lists number species, and which Vivillon and which Tatsugiri is the shared forms table's to
    say at step 8. This game leans on that answer far less than Hisui did - it introduces no
    regional form of its own, which the wiki states and step 8 will check - and far more than
    it looks, because what it does introduce is Megas.
    """
    reasons = unobtainable or {}
    api = context.require_api()

    return [
        DexEntry(
            game=GAME_ID,
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
    entries: Sequence[DexEntry],
) -> list[AcquisitionMethod]:
    """Every wild slot this game has, which for now is every way to get anything in it.

    Step 3 only. There is no ``wild_encounters`` call beside this one and there will not be:
    step 0 asked the source for six species spread over the Lumiose list and got eleven to
    thirty-three versions of encounter data each, with **not one row for any Generation IX
    version**. The hole the reading before these six games predicted is total.

    The species asked about are the game's own 364 rather than a National Dex slice, which is
    what :meth:`BuildContext.living_dex` does for a game with no National Dex.
    """
    species = context.living_dex(through=NATIONAL_DEX_THROUGH, entries=entries)

    return list(
        legends_encounters(
            context.require_wiki(),
            game_id=GAME_ID,
            pages=PAGES,
            methods=METHODS,
            requirements=METHOD_REQUIREMENTS,
            places=PLACES,
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

    All of it written down by hand, which every game since Brilliant Diamond has had to do:
    PokeAPI carries no encounter of any kind for these games, and a gift is an encounter to that
    source.

    **There is no** ``breeding_encounters`` **call here and there will not be one.** The
    article says in a single line that abilities, breeding and Eggs are not featured in this
    game - so it is the third in the dataset with no day care, after the Let's Go pair and
    Legends: Arceus, and the second Legends game running. An absence worth stating rather than
    a line quietly not written.
    """
    species = context.living_dex(through=NATIONAL_DEX_THROUGH, entries=entries)

    return list(
        recorded_gifts(
            game_id=GAME_ID,
            gifts=GIFTS,
            species=species,
            citation=READ_ON(EVENTS_PAGE),
        )
    )


def swapped() -> list[AcquisitionMethod]:
    """The five NPCs who will trade, which is five more than the other Legends game has."""
    return list(
        trade_encounters(
            game_id=GAME_ID,
            trades=TRADES,
            citation=READ_ON(TRADES_PAGE),
        )
    )


def evolves(
    context: BuildContext,
    *,
    entries: Sequence[DexEntry],
) -> list[AcquisitionMethod]:
    """Every evolution that works in Lumiose City.

    **The source carries exactly one rule stamped with this game's name**, which is Hisuian
    Qwilfish into Overqwil by using Barb Barrage twenty times - and that is a measurement rather
    than an estimate: of the 540 evolution chains PokeAPI holds, one detail names ``legends-za``
    and none names ``mega-dimension``. Everything else here falls back to the newest rule at or
    before this game's order, which is Scarlet and Violet's and its two expansions'.

    **That fallback is right here and was wrong for Hisui**, which is the whole of why this step
    needed no :data:`evolutions.NOT_IN_THE_SOURCE` entries of its own. Legends: Arceus changed
    the *mechanism*: there are no held items and no trading in that game, so a rule saying
    "trade it holding a King's Rock" described something a player could not do, and twelve
    variants had to be written by hand. This game did not change it. The wiki says so plainly -
    all but one of the trade-evolution Pokemon that exist here can also be found fully evolved
    in Hyperspace Lumiose, and there is an in-game trade that evolves a Porygon - so a trade
    rule in this game is a trade rule a player can follow.

    There is no ``breeding_encounters`` call beside this one for the reason :func:`handed_over`
    gives: nothing in this game breeds.
    """
    species = context.living_dex(through=NATIONAL_DEX_THROUGH, entries=entries)

    return list(
        evolution_encounters(
            context.require_api(),
            game_id=GAME_ID,
            version_group=EVOLUTION_GROUPS,
            species=species,
            forms=context.forms_here(),
            all_forms=context.forms,
            refresh=context.refresh,
        )
    )


def edges() -> list[TransferEdge]:
    """HOME, one way in, and nothing at all coming back out.

    **Every Switch game in this dataset calls** :func:`home.home_edges` **and gets two edges;
    this one does not, and the missing half is the whole finding of step 1.** That function
    draws a deposit and a withdrawal because the service moves Pokemon both ways with every core
    series game on the Switch. Here it does not, and both the game's article and HOME's own say
    so in the same words: Pokemon transferred into Legends: Z-A cannot be transferred back to
    previous games, nor can Pokemon obtained in Legends: Z-A. HOME gained the compatibility on
    2 April 2026 in its version 4.0.0, nearly six months after the game - so for half a year the
    newest game in the series had no route of any kind.

    **The deposit is not simply absent from the service, which is the part worth being careful
    about.** A player really can put a Pokemon from this game into HOME, and take it out again
    into this game - that is how two save files on one console swap anything. What they cannot
    do is take it out anywhere else. So the deposit exists and every path it opens leads back
    here, and :mod:`legends_arceus` already wrote the rule for that case in another context: a
    route from a game to itself is one a graph of games has nowhere to draw.

    Drawing it anyway would not be a harmless extra: this graph is read to answer which other
    games can supply an entry, and a ``legends-z-a -> home`` edge would tell a player of Red or
    of Sword that a Pokemon caught here can fill a tile there. It cannot.

    **This is a statement about the games this dataset holds, not a prophecy.** The sentence
    says *previous* games, and this is the last one there is. The day a game after it is added,
    the deposit is the edge that connects them, and this docstring is where whoever adds it
    should start.

    **The withdrawal's** ``PresentInTargetDexFilter`` **is the source's own sentence**, as it
    was for Legends: Arceus: only Pokemon in the Lumiose Pokedex and the Hyperspace Pokedex can
    be transferred in, so the filter asks the one question it knows how to ask - does the game
    being transferred into list this species - and step 2 is what makes the answer honest.

    Registering this lights nothing that was waiting. Every older game that can reach this one
    was already reaching HOME, which has been true since the fifth Generation VIII game.
    """
    return [
        TransferEdge(
            **{"from": home.NODE},
            to=GAME_ID,
            mechanism=TransferMechanism.HOME,
            direction=TransferDirection.ONE_WAY,
            filter=PresentInTargetDexFilter(),
        ),
    ]


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Legends Z-A EN boxart.png")
