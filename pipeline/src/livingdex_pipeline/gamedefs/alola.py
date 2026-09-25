"""What the Alola games share, which is nearly but not quite what Generation 7 shares.

Sun and Moon are a version pair. Ultra Sun and Ultra Moon are a second pair a year later, in the
same region, with the same story told differently and a Pokedex a hundred and one entries
longer. That is the Unova shape rather than the Hoenn one - two pairs, not a pair and a third
version - and this module keeps them apart wherever they disagree, which turns out to be
wherever a number is involved.

**Named for the region and not for the generation**, unlike :mod:`gen6` beside it, and the reason
is Let's Go. Generation 7 is four cartridges set in Alola on a 3DS and two games set in Kanto on
a Switch, and they share no trade set, no Pokedex, no hardware and no way out: these four talk to
Pokemon Bank, those two talk to HOME. A file called ``gen7`` would have to say "except in Let's
Go" about nearly every line in it. What Let's Go shares with the rest of Kanto belongs in
:mod:`kanto`, which has served two generations there already. :mod:`gen6` predicted this in so
many words: the pattern of naming a generation after its console stops when the console outlives
the generation, and here the generation outlives the console instead.

**The first games since Generation 2 with no National Pokedex**, and Bulbapedia counts it as the
first since the National Dex was introduced at all. The Rotom Dex shows the Alola list and
nothing else. What a player used to read in the game is in Pokemon Bank now - Bank's own National
Pokedex gathers what has been registered in any Generation 6 or 7 game - which is one more reason
Bank is a node in this dataset rather than a footnote.

That left a decision, and it was taken deliberately: :data:`SM_NATIONAL_DEX_THROUGH` is filled in
anyway. The field answers "how far does a living dex here reach", and the answer for these games
is every species they can hold, which is 802 and not the 302 the dex app lists. The boxes take
anything Bank will hand over; only the Pokedex stops early. The Alola list is still written down,
as the game's own dex, and the grid can be switched to it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from .. import conditions
from ..alolatables import SUN_AND_MOON, TERRAIN, ULTRA_SUN_AND_MOON, Reading, read_times
from ..breeding import CAUGHT, breeding_encounters, day_care_eggs
from ..evolutions import evolution_encounters
from ..formchanges import FormChange, form_change_encounters, spread
from ..games import BuildContext
from ..gifts import (
    Exclusion,
    GiftDetail,
    GiftDetails,
    RecordedGift,
    gift_encounters,
    recorded_gifts,
)
from ..models import (
    AcquisitionMethod,
    AllSpeciesFilter,
    DexEntry,
    DexSource,
    DexTarget,
    Form,
    Game,
    GameRelease,
    GiftKind,
    NationalDexRangeFilter,
    SourceCitation,
    SpeciesFilter,
    TransferDirection,
    TransferEdge,
    TransferMechanism,
    WildAcquisition,
)
from ..normalise import Normaliser
from ..places import LocationNames
from ..pokeapi import BASE_URL
from ..sources import bulbapedia
from ..trades import InGameTrade, trade_encounters
from ..wild import wild_encounters
from . import bank, exclusives

GENERATION = 7

REGION = "Alola"

#: How far a living dex in Sun and Moon reaches: 802, Marshadow.
#:
#: Eighty-one more than Generation 6, and the last number in the series that a single pair
#: settles - Ultra Sun and Ultra Moon move it five further, which no third version or pair of
#: sequels has ever done before. Black 2 added none; Platinum added none; Emerald added none.
SM_NATIONAL_DEX_THROUGH = 802

#: And in Ultra Sun and Ultra Moon: 807, Zeraora.
#:
#: Five species, and they are the reason this region needs two of nearly every number. Poipole
#: and Naganadel, Stakataka and Blacephalon, and Zeraora, which was never in either game and is
#: counted here because the dex has a slot for it.
USUM_NATIONAL_DEX_THROUGH = 807

#: Every Generation 7 cartridge that trades with every other. All four share one GTS and one
#: Festival Plaza, and the second pair trades with the first as freely as with itself - as
#: freely as the five species between them allow, which is what :func:`trade_edges` is about.
#:
#: A game declares the whole set whether or not the others are built yet: the registry holds an
#: edge back until both ends exist, so adding Ultra Sun later lights its routes up without
#: anyone editing Sun.
CARTRIDGES = ("sun", "moon", "ultra-sun", "ultra-moon")

#: The second pair, named because half of what this module does is tell the two pairs apart.
ULTRA = ("ultra-sun", "ultra-moon")

#: PokeAPI's name for the 302-entry Alola dex, the one Sun and Moon show.
#:
#: Named for the pair rather than for the region, for the reason :mod:`unova` gives about its
#: own two: a region with two dexes and one constant for both of them is a mistake this dataset
#: has made before. The source spells it ``original-``, as it does Unova's and Sinnoh's.
SM_DEX = "original-alola"

#: PokeAPI's name for the 403-entry Alola dex, the one Ultra Sun and Ultra Moon show.
#:
#: **The hundred and one it adds are scattered through the list rather than added to the end**,
#: which is the thing to know about these two dexes and the reason they cannot share a constant.
#: Platinum's Sinnoh dex was Diamond's with more after it, and every number in it meant the same
#: thing; here the numbering parts company at #024 - Pichu in one list, Buneary in the other -
#: and most of what follows disagrees. It is what Omega Ruby did to Ruby's list with nine
#: entries, on a larger scale.
USUM_DEX = "updated-alola"

#: How long each of the two lists is. 300 and 400 of them are asked for: Magearna and Marshadow
#: are in both dexes and required by neither, and Zeraora is the third the sequels excuse.
SM_DEX_TOTAL = 302
USUM_DEX_TOTAL = 403

#: The four island dexes, which this dataset deliberately does not write.
#:
#: Alola splits its list four ways - Melemele, Akala, Ula'ula, Poni - and the source has all
#: eight of them, numbered 1 to 120 and so on. Those numbers are the official guidebooks': in
#: the game a Pokemon keeps its overall Alola number wherever it is listed, so Pikipek is #010
#: in all four islands even though it is first in three of them. Writing them as dexes would
#: print a player numbers no game ever showed, which is the opposite of what the three Kalos
#: lists are - those really do renumber, and each really is what the game displays.
#:
#: Thirty-nine entries are in the overall list and on no island at all, so the four are not even
#: a partition of it. Named here so the next person to see them in the source knows they were
#: looked at and left.
ISLAND_DEXES = (
    "original-melemele",
    "original-akala",
    "original-ulaula",
    "original-poni",
)


#: What these games call a place the source files under another name.
#:
#: Empty so far. Alola's places came through the source's own English names without a quarrel,
#: which Unova and Kalos both needed a table for.
RENAMED_PLACES: dict[str, str] = {}

#: And the same below a location, where a sub-area's English is generated from its slug and so
#: was never read by anybody.
RENAMED_SUB_AREAS: dict[str, str] = {}

#: The one sheet in this dataset that does not come from PokeAPI.
#:
#: Every generation from the first to the sixth has a folder of battle sprites in the sprite
#: repository and Generation 7 has none - not for Sun and Moon and not for Ultra Sun and Ultra
#: Moon either. PokeAPI publishes a url for the second of those, ``versions/generation-vii/
#: ultra-sun-ultra-moon/25.png``, and the repository does not have the file; there is no
#: ``sun-moon`` folder to 404 on at all. What it does have is a folder of box icons, which is a
#: different kind of picture from the battle sprites every other game here shows.
#:
#: So these four drew the shared set until the Bulbagarden Archives were read instead, which is
#: what :mod:`~livingdex_pipeline.archives` is. Two things that source settled and this one
#: could not:
#:
#: * **Ultra Sun and Ultra Moon have no sheet of their own.** Their category on the Archives
#:   holds 409 files against Sun and Moon's 1949, and what is in it is what those two *added* -
#:   Dusk Mane, Dawn Wings and Ultra Necrozma, Dusk Form Lycanroc, the Partner Cap Pikachu.
#:   Everything else in Ultra Sun is the picture Sun already had. Hence one folder for four
#:   games rather than a pair each, and hence the name: the region rather than a version group.
#: * **The 800-pixel pictures that look like theirs are Let's Go's.** The wiki prefixes a sprite
#:   with the games it came from, and ``7p`` is Let's Go while ``7u`` is Ultra Sun and Ultra
#:   Moon. A reader who matched on the number alone would have given Alola a sheet ten times the
#:   size, drawn from the wrong games.
SPRITE_SET = "generation-vii/alola"

#: PokeAPI's name for the version group each pair shares, which its evolution rules hang off.
#:
#: Two of them, because the second pair changed how things evolve: Alolan Marowak wants a level
#: at night in both, but the source stamps a rule with the group it started in and a game is
#: only allowed the groups at or before its own. Handing these two Sun and Moon's group would
#: quietly refuse them every rule that arrived with their own.
ALOLA_VERSION_GROUP = "sun-moon"
USUM_VERSION_GROUP = "ultra-sun-ultra-moon"

#: Where an Egg is left and collected.
#:
#: Alola calls it a Nursery rather than a Day Care and there are two of them, at Paniola Ranch
#: and on Route 5. Both do the same thing and the nearer one is the one on the ranch, which is
#: also where the nursery helpers hand over the Eevee Egg.
DAY_CARE = "Paniola Ranch, Pokemon Nursery"

#: The six traders, each standing in one place and wanting one thing.
#:
#: Read off Bulbapedia's in-game trade table. The name is the original trainer stamped on what
#: they hand over, which is the name a player sees in the summary screen forever after - not the
#: nickname, which these six all come with and which a player can change.
#:
#: The one in Tapu Village is the first trade in this dataset that hands over a form: an Alolan
#: Graveler, which turns into an Alolan Golem the moment it arrives. The record is of what is
#: handed over, as Sinnoh's Haunter-into-Gengar already is.
ALOLA_TRADES: tuple[InGameTrade, ...] = (
    InGameTrade(gets="machop", wants="spearow", location="Route 2", npc="Hila"),
    InGameTrade(gets="bounsweet", wants="lillipup", location="Route 5", npc="Kihei"),
    InGameTrade(gets="happiny", wants="pancham", location="Malie City", npc="Momoe"),
    InGameTrade(
        gets="graveler",
        form="graveler-alola",
        wants="haunter",
        location="Tapu Village",
        npc="Sill",
    ),
    InGameTrade(gets="steenee", wants="granbull", location="Seafolk Village", npc="Kumu"),
    InGameTrade(gets="talonflame", wants="bewear", location="Poni Gauntlet", npc="Anga"),
)

#: What step 7 found about the two entries neither half of the second pair can produce.
#:
#: Both were given away for *these two specifically*, which is the thing to notice: Sun and
#: Moon's Marshadow distributions ran out in February 2018 and these two got their own, starting
#: on the day they came out. Zeraora was never offered to any other game at all until Pokemon
#: HOME handed out a Shiny one for a million victories two generations later.
USUM_UNOBTAINABLE: dict[str, str] = {
    "marshadow": exclusives.with_event(
        "Nothing in Alola produces one; it was only ever given away",
        exclusives.handed_out(
            "the Mount Tensei Marshadow by serial code, from the day these two came out until "
            "February 2018",
            "a second run of those codes that spring",
        ),
    ),
    "zeraora": exclusives.with_event(
        "Nothing in Alola produces one; it was only ever given away - and these two are the "
        "only games it was ever given away to",
        exclusives.handed_out(
            "the Fula City Zeraora at a Japanese cinema in July 2018",
            "serial codes in every region from that October until March 2019",
        ),
    ),
}

#: The seven the second pair stands in the same places for, wanting different things.
#:
#: Not one of the six is the same trade. Hila still stands on Route 2 and still wants a Spearow,
#: and what she hands over is a Hawlucha where it was a Machop; Kihei still wants a Lillipup on
#: Route 5 and gives a Noibat rather than a Bounsweet. Two of the first pair's places are gone
#: and three new ones have traders - Royal Avenue, Route 8 and a seventh trade in all - which is
#: why the four cartridges cannot share one table however alike the traders' names look.
#:
#: Two are worth reading twice:
#:
#: - **Sill's Phantump turns into a Trevenant the moment it arrives**, which is what a traded
#:   Phantump does. What is recorded is what is handed over, as Sinnoh's Haunter-into-Gengar and
#:   this pair's own Alolan Graveler-into-Golem already were.
#: - **Kumu's Shellos is the West Sea one**, and Alola's own Shellos is the East Sea. So this
#:   trade is not a shortcut to something in the grass, it is the only West Sea Shellos these
#:   games have - which is the other side of a finding step 8 made about Sun and Moon and could
#:   not act on.
USUM_TRADES: tuple[InGameTrade, ...] = (
    InGameTrade(gets="hawlucha", wants="spearow", location="Route 2", npc="Hila"),
    InGameTrade(gets="noibat", wants="lillipup", location="Route 5", npc="Kihei"),
    InGameTrade(gets="barboach", wants="tentacool", location="Royal Avenue", npc="Yuichi"),
    InGameTrade(gets="arbok", wants="trumbeak", location="Route 8", npc="Miyo"),
    InGameTrade(gets="phantump", wants="phantump", location="Tapu Village", npc="Sill"),
    InGameTrade(gets="shellos", wants="granbull", location="Seafolk Village", npc="Kumu"),
    InGameTrade(gets="tauros", wants="bewear", location="Poni Gauntlet", npc="Anga"),
)

#: Where the wiki keeps a place's encounter table when its own title is not the place's name.
#:
#: Two in fifty-seven, which is what :func:`page_of` handles the rest of with one rule and a
#: substitution.
PAGE_TITLES: dict[str, str] = {
    # The wiki's article is the Berry fields, with no region in front of it.
    "Alola Berry Fields": "Berry_fields",
    # Every wild slot the source files under Royal Avenue is in the abandoned Thrifty Megamart,
    # which has a page of its own - and, as it happens, stands on another island.
    "Royal Avenue": "Thrifty_Megamart",
}


def page_of(location: str) -> str:
    """The wiki page one of this region's encounter tables is on.

    A rule rather than a table of fifty-seven, because Alola's names carry across almost
    unchanged. Two things have to be done to them: a route is disambiguated by its region, since
    six generations have had a Route 2, and the source writes some of the Hawaiian names with a
    curly apostrophe and some with a straight one - Hau'oli City one way and Hau'oli Cemetery the
    other, in the same game.
    """
    name = location.replace("\u2019", "'")
    if name.startswith("Route "):
        name = f"Alola {name}"

    return PAGE_TITLES.get(name, name.replace(" ", "_"))


#: Who hands each of these over, and what has to be true first.
#:
#: PokeAPI has the place and the level of every one of them and the word "gift" for all three
#: kinds at once, so what is here is the half it cannot carry: the name of the person holding it
#: out, whether the thing is a starter, a fossil or a present, and what the game wants doing
#: before any of it happens. Read off Bulbapedia's own gift table for these two games.
ALOLA_GIFTS: dict[str, GiftDetails] = {
    # Hala holds all three out at the festival in Iki Town, after Tapu Koko has handed the player
    # a stone and flown off again. The other two are a trade away, as always.
    **{
        species: GiftDetail(
            kind=GiftKind.STARTER,
            npc="Hala",
            requirement="Pick one of the three at the festival; the other two take a trade",
        )
        for species in ("rowlet", "litten", "popplio")
    },
    # The one gift in these games that is not a Pokemon when it is handed over. The nursery
    # helpers at Paniola Ranch give an Egg, so the level is 1 and the record says hatching.
    "eevee": GiftDetail(
        kind=GiftKind.EGG,
        npc="The nursery helpers",
        requirement="Hatch the Egg they hand over",
    ),
    # Four fossils and two of them per game, which the source does not know - see
    # :func:`alola_excluded`. Olivia sells each once, and the Restoration Center revives it.
    **{
        species: GiftDetail(
            kind=GiftKind.FOSSIL,
            npc="A Pokemon Breeder at the Fossil Restoration Center",
            requirement=(
                f"Revive the {fossil} Fossil, which Olivia's shop in Konikoni City sells once"
            ),
        )
        for species, fossil in (
            ("cranidos", "Skull"),
            ("shieldon", "Armor"),
            ("tirtouga", "Cover"),
            ("archen", "Plume"),
        )
    },
    "aerodactyl": GiftDetail(npc="An Ace Trainer on one of the boats"),
    "porygon": GiftDetail(
        npc="An Aether Foundation employee",
        requirement="After entering the Hall of Fame",
    ),
    # Gladion hands over the beast his family made, with the seventeen discs that turn it into
    # the thing it was meant to be. Silvally is step 5's: a memory is not a stone but the
    # evolution is an evolution.
    "type-null": GiftDetail(
        npc="Gladion",
        requirement=(
            "After entering the Hall of Fame, along with all seventeen of Silvally's memories"
        ),
    ),
    # Both Zygarde formes, at two levels: thirty before the Hall of Fame and fifty after. What
    # the record cannot say is that the two are the same Pokemon taken apart and put together
    # again, which is why neither is a form change.
    **{
        species: GiftDetail(
            npc="The Reassembly Unit",
            requirement=(
                "Built from the Zygarde Cells and Cores collected around Alola - ten of them "
                "for the 10% Forme and fifty for the 50%"
            ),
        )
        for species in ("zygarde",)
    },
    # The four guardians, each asleep in the ruins its island is named for, and each one only
    # ever there once.
    **{
        species: GiftDetail(
            kind=GiftKind.STATIC_ENCOUNTER,
            requirement="Waiting in the ruins after the Hall of Fame; there is only one",
        )
        for species in ("tapu-koko", "tapu-lele", "tapu-bulu", "tapu-fini")
    },
    # The one Ultra Beast the source files as a static rather than as grass, and the only entry
    # here a player may have four of.
    **{
        species: GiftDetail(
            kind=GiftKind.STATIC_ENCOUNTER,
            requirement=(
                "On the Ultra Beast hunt, at Route 17 or in Malie Garden; four at either"
            ),
        )
        for species in ("kartana", "celesteela")
    },
    # Standing on the island that is named after it, and the only Exeggutor in these two games
    # that is not traded in.
    "exeggutor": GiftDetail(
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement="The one standing on the island named after it",
    ),
    # And the one that will not stand still. Wimpod bolts the moment it is looked at, and
    # catching it is a chase down the beach rather than a battle walked into.
    "wimpod": GiftDetail(
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement="It bolts the moment it sees you; run it down",
    ),
}

#: The legendary each half of the pair ends its story with, and the Cosmog it hands over after.
#:
#: Two entries rather than one shared: the giver is the legendary itself, which is Solgaleo in
#: one game and Lunala in the other, and a player who has one has the other's name in front of
#: them on the box.
ALOLA_BY_HALF: dict[str, dict[str, GiftDetails]] = {
    "sun": {
        "solgaleo": GiftDetail(
            kind=GiftKind.STATIC_ENCOUNTER,
            requirement="Caught at the Altar of the Sunne during the story; there is only one",
        ),
        "cosmog": GiftDetail(
            npc="Solgaleo",
            requirement=(
                "At the Lake of the Sunne after the Hall of Fame, with Solgaleo in the party"
            ),
        ),
    },
    "moon": {
        "lunala": GiftDetail(
            kind=GiftKind.STATIC_ENCOUNTER,
            requirement="Caught at the Altar of the Moone during the story; there is only one",
        ),
        "cosmog": GiftDetail(
            npc="Lunala",
            requirement=(
                "At the Lake of the Moone after the Hall of Fame, with Lunala in the party"
            ),
        ),
    },
}

#: How a player reaches the Ultra Space Wilds, which is the whole of what these two added.
#:
#: Ride Solgaleo or Lunala through Ultra Space, steering with the 3DS's own tilt, and dive into
#: a warp hole. There are four tiers of them and the farthest flights find the rarest: **a hole
#: with a flower-shaped aura is guaranteed to hold a legendary**, and the rates stop improving
#: at five thousand light-years. A legendary that is not caught comes back, so a lost battle
#: costs a flight rather than the entry.
#:
#: This is the single largest thing any game in this dataset does for a living dex. Nearly every
#: legendary of the six generations before Alola is at the end of one of these wormholes, and
#: most of them had been reachable only by carrying one across five transfers from the cartridge
#: it was caught on.
ULTRA_WARP_RIDE = (
    "Through a warp hole on the Ultra Warp Ride; the farther the flight the rarer the hole, and "
    "one with a flower-shaped aura always holds a legendary"
)

#: The legendaries and Ultra Beasts waiting at the end of a wormhole.
#:
#: Written as one sentence over a list rather than fifty copies of it, the way :func:`spread`
#: does for forms. Which of them a cartridge meets is the source's to say and it says it
#: properly: Ho-Oh, Dialga, Groudon, Reshiram, Xerneas, Raikou, Latios, Tornadus and Heatran are
#: Ultra Sun's, and Lugia, Palkia, Kyogre, Zekrom, Yveltal, Entei, Latias, Thundurus and
#: Regigigas are Ultra Moon's - the two halves of nine pairs, which is a version exclusive on a
#: scale nothing before this has tried.
ULTRA_SPACE: tuple[str, ...] = (
    "articuno",
    "azelf",
    "cobalion",
    "cresselia",
    "dialga",
    "entei",
    "groudon",
    "heatran",
    "ho-oh",
    "kyogre",
    "latias",
    "latios",
    "lugia",
    "mesprit",
    "mewtwo",
    "moltres",
    "palkia",
    "raikou",
    "regice",
    "regirock",
    "registeel",
    "reshiram",
    "terrakion",
    "thundurus",
    "tornadus",
    "uxie",
    "virizion",
    "xerneas",
    "yveltal",
    "zapdos",
    "zekrom",
)

#: The five that want two of their own trio caught first.
#:
#: The source knows these and files them on the copy of the place this module refuses - see
#: :func:`usum_excluded` - so they are written here instead. It is the oldest habit in the
#: series, the one the Regis had in Hoenn, turned into the shape of a whole postgame: catch two
#: and the third will show itself.
IN_PARTY: dict[str, str] = {
    "giratina": "With Dialga and Palkia in the party",
    "rayquaza": "With Groudon and Kyogre in the party",
    "suicune": "With Raikou and Entei in the party",
    "kyurem": "With Reshiram and Zekrom in the party",
    "landorus": "With Tornadus and Thundurus in the party",
    "regigigas": "With Regirock, Regice and Registeel in the party",
}

#: What the second pair hands over, and where it differs from the first.
#:
#: Nearly every line here is somewhere else than it was: Kukui hands the starters over on Route
#: 1 rather than Hala at the festival in Iki Town, Wicke hands over the Type: Null at Ancient
#: Poni Path because Gladion has left Alola, the fossils are revived at a Restoration Center on
#: Route 8 instead of bought from Olivia's shop, and Necrozma waits in Mount Lanakila's crater
#: rather than in Ten Carat Hill. Which is the reason the four cartridges share no gift table.
USUM_GIFTS: dict[str, GiftDetails] = {
    **dict.fromkeys(
        ("rowlet", "litten", "popplio"),
        GiftDetail(
            kind=GiftKind.STARTER,
            npc="Professor Kukui",
            requirement="Pick one of the three on Route 1; the other two take a trade",
        ),
    ),
    "eevee": GiftDetail(
        kind=GiftKind.EGG,
        npc="The nursery helpers",
        requirement="Hatch the Egg they hand over",
    ),
    # All four fossils in both halves, which is the one place these two are kinder than Sun and
    # Moon: there, Olivia stocked two of the four and the other two took a trade.
    **dict.fromkeys(
        ("cranidos", "shieldon", "tirtouga", "archen", "omanyte", "kabuto", "lileep",
         "anorith", "tyrunt", "amaura"),
        GiftDetail(
            kind=GiftKind.FOSSIL,
            npc="A Pokemon Breeder at the Fossil Restoration Center",
            requirement="Revive the fossil, which this half sells as readily as the other",
        ),
    ),
    "aerodactyl": GiftDetail(npc="An Ace Trainer on one of the boats"),
    "porygon": GiftDetail(
        npc="An Aether Foundation employee",
        requirement="After entering the Hall of Fame",
    ),
    # Gladion is out of Alola for the whole of this story, so the beast his family made is
    # handed over by the one who looked after it instead.
    "type-null": GiftDetail(
        npc="Wicke",
        requirement=(
            "After entering the Hall of Fame, along with all seventeen of Silvally's memories"
        ),
    ),
    "zygarde": GiftDetail(
        npc="The Reassembly Unit",
        requirement=(
            "Built from the Zygarde Cells and Cores collected around Alola - ten of them for "
            "the 10% Forme and fifty for the 50%"
        ),
    ),
    **dict.fromkeys(
        ("tapu-koko", "tapu-lele", "tapu-bulu", "tapu-fini"),
        GiftDetail(
            kind=GiftKind.STATIC_ENCOUNTER,
            requirement="Waiting in the ruins after the Hall of Fame; there is only one",
        ),
    ),
    "necrozma": GiftDetail(
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement="Waiting in the crater at the top of Mount Lanakila; there is only one",
    ),
    "wimpod": GiftDetail(
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement="It bolts the moment it sees you; run it down",
    ),
    # The wormhole crowd, and the five that want company first.
    **{
        species: GiftDetail(kind=GiftKind.STATIC_ENCOUNTER, requirement=ULTRA_WARP_RIDE)
        for species in ULTRA_SPACE
    },
    **{
        species: GiftDetail(
            kind=GiftKind.STATIC_ENCOUNTER,
            requirement=f"{ULTRA_WARP_RIDE}. {wanted}",
        )
        for species, wanted in IN_PARTY.items()
    },
    # The Ultra Beasts, each in the world it came from rather than on Looker's errand.
    **dict.fromkeys(
        ("nihilego", "buzzwole", "pheromosa", "xurkitree", "celesteela", "kartana",
         "guzzlord", "blacephalon", "stakataka"),
        GiftDetail(
            kind=GiftKind.STATIC_ENCOUNTER,
            requirement=(
                "In its own world at the end of a warp hole, which it keeps coming back to "
                "however many are caught"
            ),
        ),
    ),
}

#: What Samson Oak hands over at Heahea Beach for Totem Stickers.
#:
#: **These are the reason a gift can name a form now.** A Totem-sized Gumshoos is not a
#: Gumshoos with a note on it, it is `gumshoos-totem` - three feet taller, with its own entry in
#: the form table - and the source files every one of them under the ordinary species, which is
#: the one thing it is not. A plain Gumshoos is caught in the grass on Route 1.
#:
#: They are also the only way anybody gets one. Sun and Moon have Totem Pokemon at their trial
#: sites and a Totem is a battle rather than a catch; step 8 for that pair had to leave all
#: seven of its Totem forms with no way at all, and said so. This is where they come from, and
#: the first pair can only be handed one over the link.
#:
#: Which six a cartridge keeps is a version exclusive, and Mimikyu is in both - the sole
#: exception, and the wiki says so in as many words.
TOTEM_STICKERS = (
    "From Samson Oak on Heahea Beach, for Totem Stickers collected around Alola"
)


def totem(species: str) -> GiftDetail:
    """One of Samson Oak's, named as the form it really is."""
    return GiftDetail(
        form=f"{species}-totem",
        npc="Samson Oak",
        requirement=TOTEM_STICKERS,
    )


#: The two the story gives one of, and the six Samson Oak keeps for whoever collected stickers.
USUM_BY_HALF: dict[str, dict[str, GiftDetails]] = {
    "ultra-sun": {
        "solgaleo": GiftDetail(
            kind=GiftKind.STATIC_ENCOUNTER,
            requirement="Waiting on the Mahalo Trail after the story; there is only one",
        ),
        "cosmog": GiftDetail(
            npc="A woman at the Lake of the Sunne",
            requirement="After the Hall of Fame; there is only one",
        ),
        "poipole": GiftDetail(
            npc="Soliera",
            requirement="Handed over in the Ultra Megalopolis, after the story there",
        ),
        "gumshoos": totem("gumshoos"),
        "vikavolt": totem("vikavolt"),
        "lurantis": totem("lurantis"),
        "marowak": GiftDetail(
            form="marowak-totem", npc="Samson Oak", requirement=TOTEM_STICKERS
        ),
        "ribombee": totem("ribombee"),
        "mimikyu": GiftDetail(
            form="mimikyu-totem-disguised", npc="Samson Oak", requirement=TOTEM_STICKERS
        ),
    },
    "ultra-moon": {
        "lunala": GiftDetail(
            kind=GiftKind.STATIC_ENCOUNTER,
            requirement="Waiting on the Mahalo Trail after the story; there is only one",
        ),
        "cosmog": GiftDetail(
            npc="A woman at the Lake of the Moone",
            requirement="After the Hall of Fame; there is only one",
        ),
        "poipole": GiftDetail(
            npc="Dulse",
            requirement="Handed over in the Ultra Megalopolis, after the story there",
        ),
        "raticate": GiftDetail(
            form="raticate-totem-alola", npc="Samson Oak", requirement=TOTEM_STICKERS
        ),
        "araquanid": totem("araquanid"),
        "salazzle": totem("salazzle"),
        "togedemaru": totem("togedemaru"),
        "kommo-o": totem("kommo-o"),
        "mimikyu": GiftDetail(
            form="mimikyu-totem-disguised", npc="Samson Oak", requirement=TOTEM_STICKERS
        ),
    },
}

#: Places the source files twice, and which copy is refused.
#:
#: Two kinds, and the second is the one that matters. The Ultra Space Wilds are under two
#: parents in the source - once as their own place and once under Ultra Space - and the copies
#: are not equal: the Ultra Space one holds only the legendaries and carries the conditions,
#: the other holds those *and* the twenty ordinary species that live there and carries none. So
#: the fuller place is kept and the conditions are written into :data:`IN_PARTY` by hand, which
#: is the only way to end up with both.
#:
#: The Trainers' School and Hau'oli City's Shopping District are the plain kind: the same two
#: statics filed under a place and under its parent. Unova's Friday Musharna, in the Dreamyard
#: and in the Dreamyard basement, is where this shape was first met.
USUM_DUPLICATE_PLACES: dict[str, str] = {
    "Ultra Space, Ultra Space Wilds Cliff": "Ultra Space Wilds, Cliff",
    "Ultra Space, Ultra Space Wilds Rocky": "Ultra Space Wilds, Crag",
    "Ultra Space, Ultra Space Wilds Cave": "Ultra Space Wilds, Cave",
    "Ultra Space, Ultra Space Wilds Water": "Ultra Space Wilds, Waterfall",
    "Trainers' School": "Route 1, Trainers School",
    "Hau'oli City, Shopping District": "Hau'oli City, Main",
}


def usum_gifts(game_id: str) -> dict[str, GiftDetails]:
    """Everything handed over in one half of the second pair."""
    return {**USUM_GIFTS, **USUM_BY_HALF[game_id]}


def usum_excluded(game_id: str) -> dict[str, Exclusion]:
    """The copy of each doubly-filed place that is not kept, per species.

    Keyed by species and then by place, which is what :data:`~.gifts.Exclusion` is for: the
    species is not wrong, one of its two places is.
    """
    duplicated: dict[str, dict[str, str]] = {}

    for species in (*ULTRA_SPACE, *IN_PARTY, "drifloon", "gastly", "bewear", "hypno"):
        for place, kept in USUM_DUPLICATE_PLACES.items():
            duplicated.setdefault(species, {})[place] = (
                f"the source files this place twice; the copy under {kept} is the one kept"
            )

    return duplicated


#: Fossils the source files under both halves that only one half sells.
#:
#: Olivia's shop stocks two of the four and which two is the cartridge's: the Skull and Cover
#: Fossils in Sun, the Armor and Plume in Moon. PokeAPI lists all four under both, which is the
#: same fault it has about Sinnoh's two - a source that is wrong about a version is a
#: disagreement to record rather than a row to quietly keep.
ALOLA_FOSSILS: dict[str, tuple[str, ...]] = {
    "sun": ("shieldon", "archen"),
    "moon": ("cranidos", "tirtouga"),
}


def wiki_games(game_id: str) -> tuple[str, str]:
    """How the wiki's encounter tables spell this cartridge's pair in their games column.

    Both pairs are on one page and that column is all that separates them, so reading the wrong
    one would quietly give a game the other pair's hours. Worked out from the cartridge rather
    than passed in, because it is not a choice: there is exactly one right answer per game and
    nothing upstream knows it better than this module does.
    """
    return ULTRA_SUN_AND_MOON if game_id in ULTRA else SUN_AND_MOON


def alola_gifts(game_id: str) -> dict[str, GiftDetails]:
    """Everything handed over in one half of the pair."""
    return {**ALOLA_GIFTS, **ALOLA_BY_HALF[game_id]}


def alola_excluded(game_id: str) -> dict[str, Exclusion]:
    """What the source says this half hands over and this half does not."""
    other = "Moon" if game_id == "sun" else "Sun"

    return {
        species: (
            f"Olivia's shop sells the other two fossils in this half; this one is {other}'s"
        )
        for species in ALOLA_FOSSILS[game_id]
    }


#: The one thing in these two games that PokeAPI has no row for at all, and it is not an event.
#:
#: Step 7 went looking for the distribution that once handed a Magearna out and found a game
#: location instead. Bulbapedia lists it beside the grass and the fishing spots - "Hau'oli City
#: (QR Scanner)" - and keeps the word *Event* for Marshadow one line below, which is the wiki
#: drawing exactly the line this step draws.
#:
#: The QR Code is a picture. It was published for each region in 2016, it is still published,
#: and scanning it happens on the 3DS's own camera with nothing switched on at the other end.
#: There is no closing date on Bulbapedia's row because there is nothing to close: every other
#: distribution in this dataset needed a shop to stand in or a server to answer, and this one
#: needs neither. So a player who buys a Sun cartridge today can still fill this tile, and
#: saying it was unobtainable would have been wrong.
#:
#: Hand-written because there is nothing to write it from. PokeAPI has no encounter for Magearna
#: in any version - not a gift, not a static, not even the ``event`` method it uses for the
#: distributions it does know about.
QR_MAGEARNA: tuple[RecordedGift, ...] = (
    RecordedGift(
        species="magearna",
        location="Hau'oli City",
        level=50,
        npc="A delivery man at the Shopping Mall",
        requirement=(
            "After entering the Hall of Fame, scan this cartridge's region's Magearna QR Code "
            "with the QR Scanner; the codes are region-locked and it is never Shiny"
        ),
    ),
)


def only_on(partner: str, event: str | None = None) -> str:
    """Why an entry in this dex is not in this cartridge, and which half has it.

    One partner, not the several :mod:`unova` names, and deliberately so while this is the only
    pair built. Ultra Sun and Ultra Moon keep sixteen of these eighteen splits and will belong
    in the sentence when they exist; the two fossils they drop mean that sentence cannot simply
    be written ahead of time. A game this dataset does not have is not a trade to send anyone
    after.
    """
    return exclusives.only_on(partner, generation=GENERATION, event=event)


def fossil_only_on(partner: str, fossil: str, event: str | None = None) -> str:
    """Why the other half's fossil Pokemon is not in this one.

    Olivia's shop in Konikoni City stocks two of the four, and a fossil is an item: it can cross
    the link held by a traded Pokemon and be revived at the Restoration Center here. Sinnoh's
    Underground said this first about two.
    """
    return exclusives.fossil_only_on(partner, fossil, generation=GENERATION, event=event)


def handed_out(*events: str) -> str:
    """One sentence naming every distribution that ever handed this species out."""
    return exclusives.handed_out(*events)


#: The two Egg giveaways that covered all four of the pair's exclusives at once.
#:
#: Six Eggs went out at Pokemon Centers in Japan over Easter 2017 and the same six in South
#: Korea a month later: Goomy, Mareanie, and then Oranguru, Passimian, Turtonator and Drampa -
#: which is every version exclusive these two games have that is not a fossil, a Beast or an
#: Alolan form. One distribution, both halves, all four gaps. Kalos did the same thing with
#: three at a Korean tournament and this is the tidier version of it.
EASTER_EGGS = "the Easter Eggs at Pokemon Centers in Japan over March and April 2017"
KOREAN_EGGS = "the Korean Pokemon Eggs a month after them"

#: And the one Pokemon Bank handed out twice, to both halves, with its Hidden Ability.
BANK_HIDDEN_ABILITY = "the Pokemon Bank Hidden Ability giveaway of 2019"

#: What step 7 found about the one entry neither half of this pair can produce.
#:
#: One, where the first draft of this table had two. Marshadow is the ordinary shape: a film
#: tie-in, a fortnight in Japanese cinemas and then serial codes that ran out in February 2018,
#: and nothing since. Magearna looked identical from the unobtainable list and turned out not to
#: be one of these at all - see :data:`QR_MAGEARNA`.
SM_UNOBTAINABLE: dict[str, str] = {
    "marshadow": exclusives.with_event(
        "Nothing in Alola produces one; it was only ever given away",
        handed_out(
            "the Mount Tensei Marshadow in Japanese cinemas in July 2017",
            "the serial codes that followed in Europe and America until February 2018",
        ),
    ),
}


#: Where the islands keep the items that change something brought in from elsewhere.
#:
#: Alola does this differently from every region before it, and the difference is worth naming.
#: In Kalos each of these items was a favour done for showing the legendary itself - a Scientist
#: near Shalour City wanted to see all three forces of nature before parting with the Reveal
#: Glass - and in Hoenn's remakes a woman in Mauville wanted to see one. Here two of them are
#: simply for sale in a shopping mall, two more are handed over by the same Aether Foundation
#: employee in the same back room, and the Reveal Glass is a reward for a grand trial. Nobody is
#: asked to show anything.
MALL = "Hau'oli City, Shopping Mall"
SECRET_LAB = "Aether Paradise, Secret Lab A"

#: And where the island challenge keeps the two that change something caught here.
OBSERVATORY = "Mount Hokulani, Hokulani Observatory"
KUKUIS_LAB = "Hau'oli Outskirts, Professor Kukui's lab"

#: How each of this pair's forms is come by, keyed by form.
#:
#: Smaller than Kalos's, and for a reason that is itself the finding: most of what makes Alola's
#: form table the biggest in the dataset is not changed into anything. The Alolan forms are
#: caught and evolved, which is step 3's work and step 5's and which really is recorded as such
#: now; the Totem ones cannot be got here at all; the Ultra Beasts have no forms. What is left
#: is the old legendaries' items, Rotom's appliances, Silvally's memories, and two families
#: whose answer is where to look.
ALOLA_FORM_CHANGES: dict[str, FormChange] = {
    **spread(
        FormChange(
            requirement="Touch the meteorite standing beside Sophocles; it cycles through all four",
            where=OBSERVATORY,
        ),
        "deoxys-attack",
        "deoxys-defense",
        "deoxys-speed",
    ),
    # The forces of nature. Burnet hands the glass over for beating Olivia rather than for being
    # shown the three, which is the one place Alola makes this easier than Kalos did.
    **spread(
        FormChange(
            requirement=(
                "Use the Reveal Glass on it, which Professor Burnet hands over at the "
                "Dimensional Research Lab once Olivia's grand trial is done"
            ),
        ),
        "tornadus-therian",
        "thundurus-therian",
        "landorus-therian",
    ),
    "kyurem-black": FormChange(
        requirement=(
            "Fuse it with Zekrom using the DNA Splicers, which an Aether Foundation employee "
            "hands over; the fusion can be undone again"
        ),
        where=SECRET_LAB,
    ),
    "kyurem-white": FormChange(
        requirement=(
            "Fuse it with Reshiram using the DNA Splicers, which an Aether Foundation employee "
            "hands over; the fusion can be undone again"
        ),
        where=SECRET_LAB,
    ),
    # The same employee, in the same back room, holds the other one out.
    "hoopa-unbound": FormChange(
        requirement=(
            "Use the Prison Bottle on it, which an Aether Foundation employee hands over; it "
            "goes back in the bottle after three days"
        ),
        where=SECRET_LAB,
    ),
    "giratina-origin": FormChange(
        requirement="While it holds the Griseous Orb, which Antiquities of the Ages sells",
        where=MALL,
    ),
    "shaymin-sky": FormChange(
        requirement=(
            "Use the Gracidea on it, which the mall's Gracidea shop sells; it turns back at "
            "night and in a box"
        ),
        where=MALL,
    ),
    "keldeo-resolute": FormChange(
        requirement=(
            "While it knows Secret Sword, which the Swords of Justice teach it at the Pledge "
            "Grove in Unova and which it keeps wherever it goes afterwards"
        ),
    ),
    # Burmy's cloak is the terrain of its last battle, which a player can do here even though no
    # Burmy is caught in Alola. Wormadam is not in this table at all any more: which cloak a
    # Wormadam wears is settled by the Burmy it evolved from, and that is an evolution rather
    # than a change - which the evolution step now says in records of its own.
    "burmy-sandy": FormChange(
        requirement="Let it battle in a cave or on sand; its cloak is wherever it last fought",
    ),
    "burmy-trash": FormChange(
        requirement="Let it battle indoors; its cloak is wherever it last fought",
    ),
}

#: The families where one sentence answers for every form of a species.
ALOLA_FORM_CHANGES_BY_SPECIES: dict[str, FormChange] = {
    # Seventeen discs and one beast, handed over together: Gladion gives the memories with the
    # Type: Null itself, so a player who has the one has all of the other.
    "silvally": FormChange(
        requirement=(
            "Let it hold the memory of that type, which Gladion hands over with the Type: Null "
            "itself - all seventeen at once, after the Hall of Fame"
        ),
        where="Aether Paradise",
    ),
    "rotom": FormChange(
        requirement="Let it possess one of the appliances in the boxes down there",
        where=KUKUIS_LAB,
    ),
    # The one family here whose answer is patience rather than an item. Which of the seven cores
    # a Minior has is settled when it appears and cannot be changed, so seven of them is seven
    # shooting stars. The shells are those same seven seen from outside: a Minior is in its
    # Meteor Form until its health drops by half, and a player filling a dex never sees a core.
    "minior": FormChange(
        requirement=(
            "Catch one with that core, which is settled when it appears and cannot be changed; "
            "the matching shell is the same Minior outside battle"
        ),
        where="Mount Hokulani",
    ),
}

#: Forms this pair holds and has no way of producing, left without a record on purpose.
#:
#: Six reasons, and only the last of them is the ordinary one:
#:
#: - **The Totem ones are Ultra Sun and Ultra Moon's.** A Totem Pokemon at a trial site is a
#:   battle, not a catch. What can be kept is a Totem-*like* one, and Samson Oak hands those out
#:   at Heahea Beach for Totem Stickers in the second pair only. They trade back to these two,
#:   which is why the form is theirs to hold and not theirs to produce.
#: - **The caps were given away.** Seven Pikachu in seven of Ash's hats, every one a serial code
#:   or a local wireless event in 2017, and every one of them over.
#: - **Cosplay Pikachu never arrives at all**, which is why none of the six is in this list:
#:   Bank refuses them and so does a trade, so they are not in this game's form table either.
#:   :data:`~.forms.COSPLAY_PIKACHU` is where that is written down.
#: - **Ash-Greninja came out of the demo.** The Special Demo Version handed one over to be moved
#:   across, and the eShop that handed out the demo closed in March 2023.
#: - **The Original Color Magearna is Pokemon HOME's**, for finishing its National Dex, which is
#:   two generations further on than anything these two can reach.
#: - And the families that are simply not caught in Alola: Unown's letters, Vivillon's patterns,
#:   Furfrou's trims, Flabebe's colours, Pumpkaboo's sizes, Deerling's coats and Basculin's
#:   stripe are each settled where the Pokemon is caught or bred, and none of them is caught or
#:   bred here. What a player brings in is what they keep, and there is nothing to tell them to
#:   do. The Eternal Flower Floette is AZ's, and no game has ever handed one over.
#:
#: Only four are named. The rest need no naming because no table above reaches them: a form is
#: only explained when something says so, and silence is already the right answer. These four
#: would otherwise be caught by a sentence meant for their family.
ALOLA_NO_WAY_HERE = frozenset(
    {
        "basculin-blue-striped",
        "floette-eternal",
        "greninja-battle-bond",
        "magearna-original",
    }
)


#: Where the second pair keeps what the first kept, which is nearly everywhere.
#:
#: Every item that changes an older legendary is in the same place: the Griseous Orb and the
#: Gracidea are still sold in the Hau'oli City mall, the DNA Splicers and the Prison Bottle still
#: come from the same Aether Foundation employee in Secret Lab A, the Reveal Glass is still
#: Professor Burnet's for beating Olivia, Rotom's appliances are still in the boxes in Kukui's
#: basement, and the meteorite is still beside Sophocles. So this table is the first pair's with
#: three changes, and each of the three is worth its own line.
USUM_FORM_CHANGES: dict[str, FormChange] = {
    **ALOLA_FORM_CHANGES,
    # **The thing these two are about.** Colress hands over both fusion items on Mount Lanakila
    # once Necrozma is caught, and which of the two a cartridge can actually use is decided by
    # the box it came in: Dusk Mane needs a Solgaleo and Dawn Wings needs a Lunala, and each
    # half has one of those and trades for the other.
    "necrozma-dusk": FormChange(
        requirement=(
            "Fuse it with Solgaleo using the N-Solarizer, which Colress hands over once Necrozma "
            "is caught; the fusion can be undone again"
        ),
        where="Mount Lanakila",
    ),
    "necrozma-dawn": FormChange(
        requirement=(
            "Fuse it with Lunala using the N-Lunarizer, which Colress hands over once Necrozma "
            "is caught; the fusion can be undone again"
        ),
        where="Mount Lanakila",
    ),
    # The second QR Code these games shipped with, and the same shape as Magearna's: a picture
    # published for each region, scanned on the 3DS's own camera, with nothing at the other end
    # to switch off. It is the only one of Ash's caps anybody can still get.
    "pikachu-partner-cap": FormChange(
        requirement=(
            "Scan this cartridge's region's Partner Cap QR Code with the QR Scanner, once Akala "
            "Island is reached; the codes are region-locked"
        ),
    ),
}


#: And the one family whose whole answer moved with Gladion.
#:
#: He is out of Alola for this story, so the seventeen discs come from the one who looked after
#: the beast instead, and in a different place. Everything else keyed by species - Rotom's
#: appliances, Minior's cores - is where it was, so this table is one entry and a fallback.
USUM_FORM_CHANGES_BY_SPECIES: dict[str, FormChange] = {
    "silvally": FormChange(
        requirement=(
            "Let it hold the memory of that type, which Wicke hands over with the Type: Null "
            "itself - all seventeen at once, after the Hall of Fame"
        ),
        where="Ancient Poni Path",
    ),
}


def usum_form_changes(forms: Sequence[Form]) -> dict[str, FormChange]:
    """One sentence for every form given that has one, and nothing for the rest."""
    changes: dict[str, FormChange] = {}

    for form in forms:
        if form.id in USUM_NO_WAY_HERE:
            continue

        change = (
            USUM_FORM_CHANGES.get(form.id)
            or USUM_FORM_CHANGES_BY_SPECIES.get(form.species)
            or ALOLA_FORM_CHANGES_BY_SPECIES.get(form.species)
        )
        if change is not None:
            changes[form.id] = change

    return changes


#: Forms this pair holds and has no way of producing, left without a record on purpose.
#:
#: Shorter than the first pair's list by everything Samson Oak hands out: the twelve Totem forms
#: that Sun and Moon can only be traded are step 4's gifts here, which is the one place these
#: two answer a question the first pair had to leave open.
#:
#: What is left is four, and the last of them is new:
#:
#: - **Ash-Greninja** came out of the Special Demo Version, as it did for the first pair, and the
#:   eShop that handed out the demo closed in March 2023.
#: - **The Original Color Magearna** is Pokemon HOME's, for finishing its National Dex.
#: - **The Eternal Flower Floette** is AZ's and no game has ever handed one over.
#: - **The Own Tempo Rockruff** was a serial code for buyers between the day these two came out
#:   and 10 January 2018, and a Dusk Lycanroc comes from nothing else. The validator reports
#:   this one rather than going quiet about it, because a form has no dex entry to carry a
#:   reason on - see ``no-evolution-dead-ends``.
USUM_NO_WAY_HERE = frozenset(
    {
        "basculin-blue-striped",
        "floette-eternal",
        "greninja-battle-bond",
        "magearna-original",
        "rockruff-own-tempo",
        "lycanroc-dusk",
    }
)


def alola_form_changes(forms: Sequence[Form]) -> dict[str, FormChange]:
    """One sentence for every form given that has one, and nothing for the rest."""
    changes: dict[str, FormChange] = {}

    for form in forms:
        if form.id in ALOLA_NO_WAY_HERE:
            continue

        change = ALOLA_FORM_CHANGES.get(form.id) or ALOLA_FORM_CHANGES_BY_SPECIES.get(form.species)
        if change is not None:
            changes[form.id] = change

    return changes


def cartridge(
    *,
    game_id: str,
    title: str,
    version: str,
    released: date,
    national_dex_through: int,
    pair_partner: str,
    sprite_set: str | None = SPRITE_SET,
) -> Game:
    """One Alola cartridge, with the facts all four of them share filled in.

    ``national_dex_through`` is a parameter rather than a constant because this is the first
    region whose two pairs do not agree about it. ``pair_partner`` is required: Alola has two
    pairs and no third version, so every one of these four has another half.

    The sheet is filled in rather than asked for, because all four draw from the same folder -
    Ultra Sun and Ultra Moon have no pictures of their own beyond what they added.
    """
    return Game(
        id=game_id,
        title=title,
        version=version,
        generation=GENERATION,
        region=REGION,
        release=GameRelease.CARTRIDGE,
        released=released,
        national_dex_through=national_dex_through,
        dex_source=DexSource.NATIONAL_DEX,
        pair_partner=pair_partner,
        sprite_set=sprite_set,
    )


def dex_entries(
    context: BuildContext,
    *,
    game_id: str,
    dex: str,
    unobtainable: Mapping[str, str] | None = None,
) -> list[DexEntry]:
    """One of the region's two Pokedexes, as one game shows it.

    No ``dex`` name on the entries, unlike X and Y's. Those games show three lists and a player
    picks between them; Alola shows one, and the islands under it are a way of reading it rather
    than another numbering.
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
        for number, species in api.pokedex(dex, refresh=context.refresh)
    ]


def acquisition_methods(
    context: BuildContext,
    *,
    game_id: str,
    version: str,
    entries: Sequence[DexEntry],
    reach: int,
    gifts: Mapping[str, GiftDetails] | None = None,
    excluded: Mapping[str, Exclusion] | None = None,
    recorded: Sequence[RecordedGift] = (),
    version_group: str | None = None,
    trades: Sequence[InGameTrade] = (),
    form_changes: Mapping[str, FormChange] | None = None,
    eggs: bool = False,
) -> list[AcquisitionMethod]:
    """Every way to get something in one Alola cartridge.

    The four share every piece of machinery here and not one of the tables behind it: the second
    pair rewrote the encounter tables, moved the gifts, changed which fossils are sold where and
    stamped its evolutions with its own version group. So a game brings what it knows and this
    puts it together, which is :mod:`sinnoh`'s shape and for :mod:`sinnoh`'s reason.

    **A table left out is a step that has not been gathered yet**, not a game with nothing to
    declare. Ultra Sun and Ultra Moon arrive with their encounters first, as the pair did, and
    pick the rest up as the steps that gather them run. Handing this an empty gift table instead
    would print PokeAPI's bare rows and call it step 4.

    ``reach`` is how far the living dex goes, and it is required because this is the first
    region whose two pairs disagree about it: 802 for Sun and Moon, 807 for these two. The
    species asked about are that whole list rather than the regional dex, for the reason
    :mod:`kalos` gives - plenty of what fills a living dex is caught in Alola without being on
    the Rotom Dex's list.

    The forms are passed too, which no game before this region did and which is the whole of
    what makes its grass different. Most of Alola's Kanto Pokemon are the regional form and
    nothing else: every Rattata on Route 1 is the Alolan one, every Diglett on Route 2, every
    Grimer in Hau'oli City. A record that said "Rattata" would be wrong about the only Rattata
    in the game, and the Kantonian one - which really is not here - would look catchable.
    """
    api = context.require_api()
    species = context.living_dex(through=reach, entries=entries)
    places = LocationNames(api, refresh=context.refresh, renamed_sub_areas=RENAMED_SUB_AREAS)

    wild = wild_encounters(
        api,
        game_id=game_id,
        version=version,
        species=species,
        forms=context.forms_here(),
        refresh=context.refresh,
        places=places,
    )

    found: list[AcquisitionMethod] = [*told_when(context, wild, games=wiki_games(game_id))]

    if gifts is not None:
        found.extend(
            gift_encounters(
                api,
                game_id=game_id,
                version=version,
                species=species,
                details=gifts,
                excluded=excluded,
                forms=context.forms_here(),
                refresh=context.refresh,
                places=places,
            )
        )

    if recorded:
        # What no source this pipeline reads has a row for. Sun and Moon's one is the Magearna
        # a QR Code unlocks, which step 7 turned up in place of a distribution that is over.
        found.extend(
            recorded_gifts(
                game_id=game_id,
                gifts=recorded,
                species=species,
                citation=bulbapedia("QR_Scanner", retrieved_on=date.today()),
            )
        )

    if version_group is not None:
        found.extend(
            evolution_encounters(
                api,
                game_id=game_id,
                version_group=version_group,
                species=species,
                forms=context.forms_here(),
                all_forms=context.forms,
                refresh=context.refresh,
            )
        )

    if trades:
        found.extend(
            trade_encounters(
                game_id=game_id,
                trades=trades,
                citation=bulbapedia("In-game_trade", retrieved_on=date.today()),
            )
        )

    if form_changes is not None:
        found.extend(
            form_change_encounters(
                game_id=game_id,
                forms=context.forms_here(),
                changes=form_changes,
                citation=bulbapedia(
                    "List_of_Pok%C3%A9mon_with_form_differences", retrieved_on=date.today()
                ),
            )
        )

    # Last, and worked out from what the steps above came to rather than from a table: the
    # nursery can only be asked for what nothing else here produces, so it cannot be answered
    # until everything else has been - which is also why it is the one thing here that a game
    # asks for with a flag rather than a table.
    if eggs:
        found.extend(
            breeding_encounters(
                game_id=game_id,
                day_care=DAY_CARE,
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
            )
        )

    return found


def told_when(
    context: BuildContext,
    records: Sequence[WildAcquisition],
    *,
    games: tuple[str, str] = SUN_AND_MOON,
) -> list[WildAcquisition]:
    """The same slots, with the hour the wiki knows and the source does not.

    Every record here stands on its own already - the source gave the place, the levels and the
    odds - so this only ever adds. A page that cannot be read, a row whose Pokemon will not
    resolve, a slot the wiki files somewhere this does not: each of those costs a condition and
    no record, which is why nothing below raises.

    Two conditions, in fact. The hour is the one this was written for. The other is the terrain
    of an ambush, which the source flattens into one method named after the only one of its
    seven kinds that happens in water; the wiki's Location column says whether a player is
    looking at grass that rustles, a cloud of sand or a shadow on the sea.
    """
    readings = _read(context, {one.location for one in records}, games=games)
    if not readings:
        return list(records)

    hours: dict[tuple, set[str | None]] = {}
    terrains: dict[tuple, set[str]] = {}

    for one in readings:
        key = (one.location, one.target.species, one.target.form, one.method)
        hours.setdefault(key, set()).add(one.time_of_day)
        if one.label in TERRAIN:
            terrains.setdefault(key, set()).add(TERRAIN[one.label])

    return [_told(record, hours, terrains) for record in records]


def _told(
    record: WildAcquisition,
    hours: dict[tuple, set[str | None]],
    terrains: dict[tuple, set[str]],
) -> WildAcquisition:
    key = (record.location, record.target.species, record.target.form, record.method)

    # One place can hold the same species in two patches of grass, and only one of them be
    # nocturnal. A player who can meet it at any hour somewhere in the place is not told to wait
    # for dark, so a single unconditioned reading settles the whole place.
    when = hours.get(key, set())
    hour = next(iter(when)) if len(when) == 1 else None

    where = terrains.get(key, set())
    terrain = next(iter(where)) if len(where) == 1 else None

    if hour is None and terrain is None:
        return record

    return record.model_copy(
        update={
            "time_of_day": hour or record.time_of_day,
            "requirement": conditions.joined(terrain, record.requirement),
        }
    )


def _read(
    context: BuildContext,
    locations: set[str],
    *,
    games: tuple[str, str],
) -> list[Reading]:
    """What the wiki says about the hours, for the places these records are in."""
    species = {one.id for one in context.species}
    forms = {one.id for one in context.forms_here()}

    return read_times(
        context.require_wiki(),
        games=games,
        pages={one: page_of(one) for one in locations},
        normaliser=Normaliser(species, forms),
        refresh=context.refresh,
    )


def carried_between(one: str, other: str) -> SpeciesFilter:
    """What a route between two of these four will take.

    Everything, unless it crosses between the pairs. Ultra Sun and Ultra Moon introduced five
    species and Sun and Moon cannot read them, so a cable between an older cartridge and a newer
    one carries National Dex 1 to 802 and no further - in both directions, which costs the older
    side nothing because it holds nothing above 802 anyway.

    The same shape the Time Capsule has: a both-ways route that refuses part of what the newer
    end can offer. It is written here, once, rather than at each end, because a filter is not
    part of what makes two declarations the same edge - two games declaring this route with
    different filters would collapse into whichever was seen first.
    """
    if (one in ULTRA) != (other in ULTRA):
        return NationalDexRangeFilter(**{"from": 1}, to=SM_NATIONAL_DEX_THROUGH)

    return AllSpeciesFilter()


def bank_carries(game_id: str) -> SpeciesFilter:
    """What Bank will hand back to this cartridge.

    The same 802 a cable between the pairs is capped at, and for the same reason: Sun and Moon
    cannot read the five species Ultra Sun and Ultra Moon introduced, and which route they came
    by makes no difference to that.
    """
    return AllSpeciesFilter() if game_id in ULTRA else carried_between("sun", "ultra-sun")


def trade_edges(game_id: str) -> list[TransferEdge]:
    """What this cartridge trades with: the other three, both ways.

    Only its own generation, as Generation 6's were. Backwards there is nothing at all - no
    Generation 6 cartridge trades with one of these, although both sit in the same 3DS - and
    what stands between them is Bank, which is not a game.
    """
    return [
        TransferEdge(
            **{"from": game_id},
            to=partner,
            mechanism=TransferMechanism.TRADE,
            direction=TransferDirection.BOTH_WAYS,
            filter=carried_between(game_id, partner),
        )
        for partner in CARTRIDGES
        if partner != game_id
    ]


def edges(game_id: str) -> list[TransferEdge]:
    """Every route one Alola cartridge brings: its trades, and Bank both ways.

    Two kinds and not three, as Generation 6's are. Nothing carries the generation before this
    one forward into it, because what does that is Bank.

    **And Bank finally hands something to the Virtual Console releases' side of the graph.**
    Bank refuses a Generation 6 game anything that came out of a Virtual Console Red or Gold;
    these four it does not refuse, and that route - Poke Transporter into Bank, Bank into here -
    is the only reason Generations 1 and 2 are in this dataset as their 3DS releases at all. Six
    games that have had a node and nowhere to go since Bank was written now have somewhere.

    The withdrawal into Sun or Moon is capped, though, at the same 802 a cable between the pairs
    is: the five species the second pair introduced cannot be moved into the first by any route,
    and Bank is a route.
    """
    return [
        *trade_edges(game_id),
        *bank.bank_edges(game_id, carries=bank_carries(game_id)),
    ]
