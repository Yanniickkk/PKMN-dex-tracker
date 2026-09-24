"""What the games set in Hoenn have in common, whichever generation they are from.

Two sets of games are set here, as in :mod:`kanto`, :mod:`johto` and :mod:`kalos`. Ruby and
Sapphire are Generation 3 and a version pair, with Emerald as their third version; Omega Ruby
and Alpha Sapphire are the same region on the 3DS twelve years later. So this module is about
the place and not about the hardware that happened to be in a player's hands, and the split is
drawn twice over:

* What is true of Hoenn - where the day care is, who trades what in which town, what walks in
  its grass - lives here, and a table that belongs to one set of cartridges rather than to the
  region says so in its name.
* What is true of the hardware and the generation - which games trade with which, how far the
  National Dex reaches, whether the way out is a Pal Park or Pokemon Bank - lives with the
  generation: :mod:`gba` for the three cartridges and :mod:`gen6` for the two remakes.

The factories are named for the generation for that reason: ``gba_cartridge`` beside
``gen6_cartridge``, ``gba_edges`` beside ``gen6_edges``. A remake shares a region with the game
it remakes and almost nothing else, and the one thing they certainly do not share is a route
between them: no cable reaches a Game Boy Advance cartridge from a 3DS, and what a Ruby has to
travel to reach an Omega Ruby is Pal Park, the Poke Transfer, Poke Transporter and Bank - five
games and two services, every step of it already in this dataset.

Even the Pokedex is different. The three cartridges show 202 entries and these two show 211, so
unlike :mod:`kanto` - where Red and FireRed really do show one list - the dex here belongs to a
generation rather than to the region, and says so in its name.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from ..breeding import CAUGHT, EggFrom, breeding_encounters, day_care_eggs
from ..encountertables import table_encounters
from ..evolutions import evolution_encounters
from ..formchanges import FormChange, form_change_encounters, spread
from ..games import BuildContext
from ..gifts import GiftDetail, GiftDetails, RecordedGift, gift_encounters, recorded_gifts
from ..models import (
    AcquisitionMethod,
    DexEntry,
    DexTarget,
    EncounterMethod,
    Form,
    Game,
    GiftKind,
    SourceCitation,
    TransferEdge,
)
from ..places import LocationNames
from ..pokeapi import BASE_URL
from ..sources import bulbapedia
from ..trades import InGameTrade, trade_encounters
from ..wild import wild_encounters
from . import exclusives, gba, gen6

REGION = "Hoenn"

#: The National Dex opens after the Elite Four in all three, and stops at Deoxys.
GBA_NATIONAL_DEX_THROUGH = gba.NATIONAL_DEX_THROUGH

#: PokeAPI's name for the Generation 3 Hoenn dex, the 202-entry one all three share. Not
#: "updated-hoenn", which is the 211-entry dex of Omega Ruby and Alpha Sapphire.
GBA_DEX = "hoenn"

#: What PokeAPI calls the pair when it says which version group an evolution started in. Ruby
#: and Sapphire are one group; Emerald is its own, and reads that name from its own file.
GBA_PAIR_VERSION_GROUP = "ruby-sapphire"

#: Where the pair's own battle sprites live in the sprite repository. One sheet for the two of
#: them: Ruby and Sapphire were drawn from the same set, and Emerald redrew it later, which is
#: why the third version names a directory of its own.
GBA_PAIR_SPRITE_SET = "generation-iii/ruby-sapphire"

#: PokeAPI's name for the Hoenn dex of the remakes, and the games' own name for it is the same
#: one the Generation 3 list has: both are "the Hoenn Pokedex", in different games.
#:
#: Pokemon Bank had to tell them apart and did it by naming the older one **Good Old Hoenn**,
#: which is the games themselves admitting that a regional dex is not one list for all time.
ORAS_DEX = "updated-hoenn"

#: How many entries it shows: 211, of which the game asks for 208.
#:
#: Rayquaza, Jirachi and Deoxys sit at the end and are not counted towards completing it - the
#: second dex in this dataset to excuse a player from anything, after Central Kalos. It is not
#: the same kind of excusing: Kalos let three Mythicals off because nothing in the region could
#: produce one, and two of these three are caught in these games, in the story after the story.
ORAS_DEX_TOTAL = 211

#: Where the remakes' own pictures live in the sprite repository.
#:
#: One sheet for the two of them, as every pair in this dataset has had, and the second set of
#: Generation 6 pictures that is not a sprite sheet at all: these games are in 3D like X and Y,
#: so what stands in for a sheet is a shot of each model, cropped to whatever the Pokemon is.
#:
#: Named for the pair rather than for the region, like every other set here. A Hoenn game of
#: another generation draws from its own.
ORAS_SPRITE_SET = "generation-vi/omegaruby-alphasapphire"

#: Where an egg is left and collected. Route 117 in all five games set here: the remakes put
#: the building back on the same route, between Mauville and Verdanturf, as they put back
#: everything else.
DAY_CARE = "Route 117, Pokemon Day Care"


def gba_cartridge(
    *,
    game_id: str,
    title: str,
    version: str,
    released: date,
    sprite_set: str | None = None,
    pair_partner: str | None = None,
) -> Game:
    """One Hoenn cartridge: a Generation 3 cartridge that happens to be set here."""
    return gba.cartridge(
        game_id=game_id,
        title=title,
        version=version,
        region=REGION,
        released=released,
        sprite_set=sprite_set,
        pair_partner=pair_partner,
    )


def gba_edges(game_id: str) -> list[TransferEdge]:
    """What this cartridge can send and receive over a link cable.

    The cable does not care about the region, so the answer is :mod:`gba`'s. Kept here as well
    because a game file reads one module and should not have to know which of the two facts
    about it is regional.
    """
    return gba.link_trade_edges(game_id)


def gen6_cartridge(
    *,
    game_id: str,
    title: str,
    version: str,
    released: date,
    pair_partner: str,
    sprite_set: str | None = None,
) -> Game:
    """One Hoenn cartridge of Generation 6: a Generation 6 cartridge that happens to be set here.

    Named for the generation rather than sharing :func:`gba_cartridge`, which is the whole point
    of the split - the two of them agree about the region and about nothing else. A Generation 3
    Hoenn cartridge reaches 386 species over a cable; these reach 721 and talk to a service.

    ``pair_partner`` is required. Hoenn has a third version in Generation 3 and none here: the
    remakes are two halves and that is all.
    """
    return gen6.cartridge(
        game_id=game_id,
        title=title,
        version=version,
        region=REGION,
        released=released,
        sprite_set=sprite_set,
        pair_partner=pair_partner,
    )


def gen6_edges(game_id: str) -> list[TransferEdge]:
    """Every route one of the remakes brings: its own generation's trades, and Bank both ways.

    Not one of them reaches the game it remakes, or any other cartridge older than itself. The
    route from a Generation 3 Hoenn to this one exists and is five games long, and every game
    on it declares its own step; nothing about that is a fact about Hoenn, which is why this
    asks :mod:`gen6` and writes nothing down of its own.
    """
    return gen6.edges(game_id)


def gen6_dex_entries(
    context: BuildContext,
    *,
    game_id: str,
    unobtainable: Mapping[str, str] | None = None,
) -> list[DexEntry]:
    """The Hoenn dex as the remakes number it: Treecko #001 to Deoxys #211.

    The same list as :func:`gba_dex_entries` with nine Pokemon slotted into it, and it is the
    nine that make this a different Pokedex rather than a longer one. Gallade, Probopass,
    Magnezone, Budew, Roserade, Dusknoir, Chingling, Rhyperior and Froslass are all Generation 4
    relatives of families Hoenn already had, and each one goes in beside its family rather than
    at the end - so from #032 on, almost everything moves. A hundred and seventy-one of the 202
    entries have a number here that means a different species in Ruby: #032 is Surskit there and
    Gallade here.

    That is the whole reason a dex entry in this dataset carries the game it belongs to. A
    number is never a fact on its own, and two games set in the same region, sharing a name for
    the list, disagree about 171 of them.

    Both halves show it identically, as every pair in this dataset does. What they disagree
    about is which entries a player can fill, and that is the ``unobtainable`` table each game
    brings.
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
        for number, species in api.pokedex(ORAS_DEX, refresh=context.refresh)
    ]


#: Every place in these two games whose encounter tables are read off Bulbapedia.
#:
#: Sixty-nine pages, and they are a list rather than a rule because a place either has a table
#: for this pair or it does not: Littleroot Town has none, the Mirage spots keep theirs on pages
#: that were never written as tables, and Mt. Chimney had its Pokemon taken away when the remakes
#: rebuilt it. A page here that yields nothing says so in the build log.
#:
#: The wiki's title and this dataset's name for the place are both needed because they disagree:
#: the wiki writes "Hoenn Route 101" to tell it from Kanto's and hangs "(Hoenn)" off the Victory
#: Road, where everything else here - including these games' own gifts and statics, which still
#: come from PokeAPI - says "Route 101" and "Victory Road". The rule is written once rather than
#: sixty-nine names being typed twice.
ORAS_PAGE_TITLES: tuple[str, ...] = (
    *(f"Hoenn_Route_{number}" for number in range(101, 135)),
    "Petalburg_City",
    "Rustboro_City",
    "Dewford_Town",
    "Slateport_City",
    "Verdanturf_Town",
    "Lavaridge_Town",
    "Fallarbor_Town",
    "Fortree_City",
    "Lilycove_City",
    "Mossdeep_City",
    "Sootopolis_City",
    "Pacifidlog_Town",
    "Ever_Grande_City",
    "Petalburg_Woods",
    "Rusturf_Tunnel",
    "Granite_Cave",
    "Fiery_Path",
    "Jagged_Pass",
    "Meteor_Falls",
    "Hoenn_Safari_Zone",
    "Mt._Pyre",
    "Shoal_Cave",
    "Seafloor_Cavern",
    "Cave_of_Origin",
    "Sky_Pillar",
    "Victory_Road_(Hoenn)",
    "New_Mauville",
    "Sea_Mauville",
    "Scorched_Slab",
    "Sealed_Chamber",
    "Team_Magma_Hideout",
    "Team_Aqua_Hideout",
    "Southern_Island",
    "Battle_Resort",
    "Soaring_in_the_sky",
)

ORAS_PAGES: dict[str, str] = {
    title: title.replace("_", " ").removeprefix("Hoenn ").removesuffix(" (Hoenn)")
    for title in ORAS_PAGE_TITLES
}

#: What the Location column on those pages means, in this project's words.
#:
#: The wiki writes what a player does rather than what the game calls it, which is mostly the
#: same thing and sometimes better: "Fishing Old Rod" is one phrase where PokeAPI has a method
#: and a rod. A word that is not here is skipped, and three kinds are skipped on purpose -
#: "Gift", "Egg" and the three "Trade ..." rows are steps 4 and 5, with records of their own.
#:
#: Two entries are a page's own habit rather than a way of meeting anything. Mt. Pyre and the
#: Sky Pillar write which floors a table covers in the column where every other page writes the
#: method, and a floor is still walking.
ORAS_METHODS: dict[str, EncounterMethod] = {
    "Grass": EncounterMethod.WALK,
    "Long grass": EncounterMethod.WALK,
    "Deep sand": EncounterMethod.WALK,
    "Cave": EncounterMethod.WALK,
    "1F-4F": EncounterMethod.WALK,
    "1F-5F": EncounterMethod.WALK,
    "Only one": EncounterMethod.WALK,
    "Surfing": EncounterMethod.SURF,
    "Fishing Old Rod": EncounterMethod.OLD_ROD,
    "Fishing Good Rod": EncounterMethod.GOOD_ROD,
    "Fishing Super Rod": EncounterMethod.SUPER_ROD,
    "Rock Smash": EncounterMethod.ROCK_SMASH,
    "Horde Encounter": EncounterMethod.HORDE,
    # Both of these are the water a player has dived under. The wiki says "Dive" where the
    # table is the open sea floor and "Seaweed" where it is the weed growing on it, and a
    # player does the same thing to reach either.
    "Dive": EncounterMethod.DIVE,
    "Seaweed": EncounterMethod.DIVE,
    "Flocks": EncounterMethod.SOARING,
}

#: What a page's word says that :class:`EncounterMethod` cannot hold.
#:
#: Both are walking, and both are somewhere a player has to be standing that is not the grass
#: they are already in. Route 111's deep sand is the one that matters most: it is the only
#: place in Hoenn a Trapinch turns up.
ORAS_METHOD_REQUIREMENTS: dict[str, str] = {
    "Long grass": "In the long grass",
    "Deep sand": "In the deep sand, in the desert",
}

#: What these games call a place PokeAPI spells wrong.
#:
#: One, and it is a typo in the slug rather than two games disagreeing: the Mirage Cave off the
#: coast west of Rustboro City is filed under ``west-of-rustburo``, and a sub-area has no name
#: of its own in PokeAPI - it is made out of the slug. The town has been Rustboro since 2002.
ORAS_RENAMED_SUB_AREAS: dict[str, str] = {"West of Rustburo": "West of Rustboro"}

#: Names the wiki writes in full that this dataset lets a species stand for.
#:
#: All three are a form, written out in full where a wild record names the species.
#:
#: The Shellos pair is a version exclusive nobody would guess at: **Omega Ruby's Route 103 and
#: Route 110 hold the West Sea Shellos and Alpha Sapphire's hold the East Sea one**, which is
#: the only thing in Hoenn that differs between the halves by form rather than by species. A
#: wild slot here says a Shellos is in that grass, and which sea it belongs to is step 8's
#: answer - the same place Deerling's spring coat is explained.
ORAS_SPECIES_ALIASES: dict[str, str] = {
    "shellos-west-sea": "shellos",
    "shellos-east-sea": "shellos",
    "deerling-spring-form": "deerling",
}

#: What PokeAPI calls the pair when it says which version group an evolution started in.
#:
#: One group for the two of them, like every pair. Its number in the ordering is what decides
#: whether an evolution that arrived later exists here: a Sylveon is in this group and a
#: Perrserker is not.
ORAS_VERSION_GROUP = "omega-ruby-alpha-sapphire"

#: The three NPCs who will trade in these two games, and what each one wants for it.
#:
#: The same three towns and the same three Pokemon Ruby and Sapphire had, and not the same
#: trades. Fortree wants a **Spinda** where it wanted a Pikachu, which is the remakes putting a
#: Hoenn Pokemon where a Kanto one had been; and the two trainers whose names the game records
#: swapped towns - Darrell is in Rustboro here and was in Fortree, Elyssa the other way round.
#: Nothing is shared with :data:`GBA_PAIR_TRADES` for that reason: they read alike and are not
#: the same table.
ORAS_TRADES = (
    InGameTrade(gets="makuhita", wants="slakoth", location="Rustboro City", npc="Darrell"),
    InGameTrade(
        gets="skitty",
        wants="spinda",
        location="Fortree City",
        npc="Elyssa",
        requirement="A Spinda, which is on Route 113 and nowhere else in Hoenn",
    ),
    InGameTrade(
        gets="corsola",
        wants="bellossom",
        location="Pacifidlog Town",
        npc="Lane",
        requirement="A Bellossom, which takes a Sun Stone on a Gloom",
    ),
)

#: The wiki's own headings, said the way a player would need them said.
#:
#: The heading inside a table is where Bulbapedia writes what a group of rows asks of a player,
#: and it is written for somebody who has read the rest of the page. "Exclusively as hidden
#: Pokemon" is the **DexNav**, which is this pair's own invention and the answer to where a
#: third of what they hold is: a patch of grass shakes, the touch screen names what is in it,
#: and a player creeps up on it. A hundred and sixty-five rows of these two games depend on it
#: and those four words explain none of it.
#:
#: The wiki says the same thing four ways - the sea gets its own wording, and half the pages
#: say "capturing" where the other half say "catching" - and all four mean one sentence here.
#:
#: A heading rewritten as nothing is one that adds nothing: "Underwater" above rows that are
#: already dives.
ORAS_CONDITIONS: dict[str, str] = {
    "Exclusively as hidden Pokémon After defeating or capturing Groudon / Kyogre": (
    "Only as a hidden Pokemon - a patch that rustles, named on the touch screen by the "
    "DexNav and crept up on rather than walked into - and only once Groudon or Kyogre has been "
    "caught or beaten"
    ),
    "Exclusively as hidden Pokémon After defeating or catching Groudon / Kyogre": (
    "Only as a hidden Pokemon - a patch that rustles, named on the touch screen by the "
    "DexNav and crept up on rather than walked into - and only once Groudon or Kyogre has been "
    "caught or beaten"
    ),
    "Surfing (exclusively as hidden Pokémon ) After defeating or capturing Groudon / Kyogre": (
    "Only as a hidden Pokemon - a patch that rustles, named on the touch screen by the "
    "DexNav and crept up on rather than walked into - and only once Groudon or Kyogre has been "
    "caught or beaten"
    ),
    "Surfing (exclusively as hidden Pokémon ) After defeating or catching Groudon / Kyogre": (
    "Only as a hidden Pokemon - a patch that rustles, named on the touch screen by the "
    "DexNav and crept up on rather than walked into - and only once Groudon or Kyogre has been "
    "caught or beaten"
    ),
    "Special hidden Pokémon": (
        "Only as a hidden Pokemon the DexNav finds, and only the once"
    ),
    # Bulbapedia writes this above four different things, and three of them - two in-game
    # trades and the pair on Southern Island - are gifts and trades that this step does not
    # read. What is left is Feebas, whose answer is the same on all three rods.
    "Special Pokémon": (
        "Fished out of the water under the bridge by the Weather Institute, in the daytime, "
        "where it bites every time; anywhere else on the route it is rare"
    ),
    "Underwater": "",
}


#: What a whole Mirage spot asks of a player before the legendary in it can be met.
#:
#: The one gate this pair has that PokeAPI cannot know: an island that only rises when the
#: party is built a certain way. Three Pokemon with every effort value they can hold, which is
#: the deepest thing any game in this dataset asks for.
PATHLESS_PLAIN = (
    "The Pathless Plain appears south of Route 131 only while three Pokemon in the party have "
    "maxed EVs"
)

#: What these two know about the things they hand over that PokeAPI cannot say.
#:
#: Twelve first partners is the first thing to notice, and no game before or since has come
#: close. Professor Birch gives one of Treecko, Torchic and Mudkip on Route 101 the way he
#: always has, and then gives one of Johto's three after the Hall of Fame, one of Unova's after
#: the Delta Episode, and one of Sinnoh's after the Hall of Fame a second time - each time a
#: choice of three, so a save reaches four of the twelve and the other eight are a trade.
#:
#: The rest of the table is mostly this pair's legendaries, and they are the reason these two
#: games matter to a living dex more than any other pair in the series: **the Mirage spots hold
#: the legendaries of five generations**. Not one of them is in the Hoenn dex, and every one of
#: them is standing in a place that appears for a day off a coast a player has to fly over.
ORAS_GIFTS: dict[str, GiftDetails] = {
    # The three Birch has always handed over, and the nine the remakes added.
    **{
        species: GiftDetail(
            kind=GiftKind.STARTER,
            npc="Professor Birch",
            requirement="Pick one of the three; the other two take a trade",
        )
        for species in ("treecko", "torchic", "mudkip")
    },
    **{
        species: GiftDetail(
            kind=GiftKind.STARTER,
            npc="Professor Birch",
            requirement=(
                "Pick one of Johto's three, which he offers after Zinnia has been spoken to "
                "once the Hall of Fame is behind you"
            ),
        )
        for species in ("chikorita", "cyndaquil", "totodile")
    },
    **{
        species: GiftDetail(
            kind=GiftKind.STARTER,
            npc="Professor Birch",
            requirement="Pick one of Unova's three, which he offers after the Delta Episode",
        )
        for species in ("snivy", "tepig", "oshawott")
    },
    **{
        species: GiftDetail(
            kind=GiftKind.STARTER,
            npc="Professor Birch",
            requirement=(
                "Pick one of Sinnoh's three, which he offers after the Hall of Fame a second time"
            ),
        )
        for species in ("turtwig", "chimchar", "piplup")
    },
    "beldum": GiftDetail(
        npc="Steven",
        requirement="In the Poke Ball at his house in Mossdeep City, after the Delta Episode",
    ),
    "castform": GiftDetail(
        npc="Weather Institute scientist",
        requirement="After driving the villains out of the Weather Institute",
    ),
    # One Pikachu, and PokeAPI files it under four buildings because the Contest Hall a player
    # walks into first is the one that hands it over.
    "pikachu": GiftDetail(
        npc="A woman at the Contest Hall",
        requirement=(
            "After your first Contest, at whichever of the four Contest Halls you enter first - "
            "one Pikachu between them, and the only one in the series that can be dressed up"
        ),
    ),
    "sharpedo": GiftDetail(
        npc="Team Aqua Grunt",
        requirement="At the Battle Resort, once the story is over",
    ),
    "camerupt": GiftDetail(
        npc="Team Magma Grunt",
        requirement="At the Battle Resort, once the story is over",
    ),
    "togepi": GiftDetail(
        kind=GiftKind.EGG,
        npc="An old woman in Lavaridge Town",
        requirement="Hatches from the egg she hands over, once the National Dex has opened",
    ),
    "wynaut": GiftDetail(
        kind=GiftKind.EGG,
        npc="An old couple in Lavaridge Town",
        requirement="Hatches from the egg they hand over",
    ),
    "kecleon": GiftDetail(requirement="Devon Scope, to see it at all"),
    # The story's own, and the one the Delta Episode is about.
    "groudon": GiftDetail(requirement="At the bottom of the Cave of Origin, in the story"),
    "kyogre": GiftDetail(requirement="At the bottom of the Cave of Origin, in the story"),
    "rayquaza": GiftDetail(
        requirement="At the top of the Sky Pillar, in the Delta Episode"
    ),
    "deoxys": GiftDetail(
        requirement=(
            "At the top of the Sky Pillar after the Delta Episode, reached by Soaring into the "
            "meteorite it arrives in"
        )
    ),

    # The three golems, unchanged since Generation 3 but for the puzzle, and the fourth that
    # waits on all three of them.
    "regirock": GiftDetail(requirement="Braille puzzle in the Desert Ruins"),
    "regice": GiftDetail(requirement="Braille puzzle in the Island Cave"),
    "registeel": GiftDetail(requirement="Braille puzzle in the Ancient Tomb"),
    # Nothing is added here: the conditions on the row already say the National Dex and the
    # three golems in the party, which is the whole of it.
    "regigigas": GiftDetail(),
    # And the Mirage spots, which is what these two games are to a living dex. Each place is a
    # gate, and what PokeAPI says about which day or hour it is stays beside it.
    # The three swords, and which one is standing there is the day of the week. PokeAPI has
    # two of Cobalion's three days and files the Sunday with no condition at all, so the days
    # are written out here and the three rows collapse into one record.
    **{
        species: GiftDetail(gate=PATHLESS_PLAIN, requirement=days)
        for species, days in (
            ("cobalion", "On a Wednesday, a Friday or a Sunday"),
            ("terrakion", "On a Tuesday or a Saturday"),
            ("virizion", "On a Monday or a Thursday"),
        )
    },
    **{
        species: GiftDetail(
            gate=(
                "The Nameless Cavern appears north-east of Sootopolis City only while three "
                "Pokemon in the party are at maximum friendship"
            ),
        )
        for species in ("uxie", "mesprit", "azelf")
    },
    **{
        species: GiftDetail(
            gate=(
                "The Trackless Forest appears east of Petalburg Woods only with Ho-Oh or Lugia "
                "in the party"
            ),
        )
        for species in ("raikou", "entei", "suicune")
    },
    **{
        species: GiftDetail(
            gate="The Fabled Cave appears on the island north of Route 133",
        )
        for species in ("reshiram", "zekrom")
    },
    "kyurem": GiftDetail(gate="The Gnarled Den appears west of Mt. Chimney"),
    "cresselia": GiftDetail(gate="Crescent Isle is a Mirage spot like any other"),
    "heatran": GiftDetail(
        requirement="In the Scorched Slab, which opens once the story's legendary is dealt with",
    ),
    # The two bells, which are Mirage spot items, and the two that answer to them. One each:
    # the Clear Bell is Omega Ruby's and the Tidal Bell Alpha Sapphire's.
    "ho-oh": GiftDetail(
        gate="Aboard the Sea Mauville",
        requirement=(
            "With the Clear Bell, which Captain Stern swaps for the Scanner found on the same "
            "wreck"
        ),
    ),
    "lugia": GiftDetail(
        gate="Aboard the Sea Mauville",
        requirement=(
            "With the Tidal Bell, which Captain Stern swaps for the Scanner found on the same "
            "wreck"
        ),
    ),
    "spiritomb": GiftDetail(
        requirement=(
            "Aboard the Sea Mauville, in the hold, once the story's legendary is dealt with"
        ),
    ),
    # Three rifts in the sky over Hoenn, each one opened by what is already in the party.
    **{
        species: GiftDetail(gate="A gap in the sky south of Dewford Town, met while Soaring")
        for species in ("dialga", "palkia")
    },
    # The second gap, which opens once the first two are caught. PokeAPI puts a Sunday on this
    # one and nothing else does - not the species page, not the page about the gaps themselves -
    # so the requirement is written out rather than read off, and says only what is checked.
    "giratina": GiftDetail(
        gate="The second gap in the sky south of Dewford Town, met while Soaring",
        requirement="With Dialga and Palkia in the party",
    ),
    **{
        species: GiftDetail(
            gate="A black cloud in the sky over Fortree City, met while Soaring",
        )
        for species in ("tornadus", "thundurus", "landorus")
    },
}

#: The eon duo, one of which is a ticket that was only ever handed out at an event.
#:
#: Each half meets one of them on Southern Island in its own story - Latios in Omega Ruby,
#: Latias in Alpha Sapphire - and the other waits on the same island for anybody holding an Eon
#: Ticket, which came by StreetPass from somebody who already had one and, before that, from a
#: code printed in a magazine. Step 7 is where that door gets looked at properly.
#:
#: Both are written as a static rather than as a gift, which is also what folds PokeAPI's two
#: rows for the same island into the one encounter they describe.
ORAS_EON_DUO: dict[str, dict[str, GiftDetails]] = {
    "omega-ruby": {
        "latios": GiftDetail(
            kind=GiftKind.STATIC_ENCOUNTER,
            requirement="Waiting on Southern Island, in the story",
        ),
        "latias": GiftDetail(
            kind=GiftKind.STATIC_ENCOUNTER,
            requirement="Waiting on Southern Island, which takes an Eon Ticket to reach",
        ),
    },
    "alpha-sapphire": {
        "latias": GiftDetail(
            kind=GiftKind.STATIC_ENCOUNTER,
            requirement="Waiting on Southern Island, in the story",
        ),
        "latios": GiftDetail(
            kind=GiftKind.STATIC_ENCOUNTER,
            requirement="Waiting on Southern Island, which takes an Eon Ticket to reach",
        ),
    },
}


def oras_gifts(game_id: str) -> dict[str, GiftDetails]:
    """What one of the remakes hands over, the eon duo said its own way round."""
    return {**ORAS_GIFTS, **ORAS_EON_DUO[game_id]}


#: The fossils, which PokeAPI has no encounter for and which no wild table lists.
#:
#: Nine species between the two games, and every one of them is an item carried to the Devon
#: Corporation rather than a Pokemon met anywhere. Two are the choice Hoenn has always asked
#: for - the Root Fossil or the Claw Fossil on Route 111, and the one left behind is left for
#: good - and the other seven are what the remakes added: rocks at the Mirage spots, smashed
#: after the story's legendary is dealt with, holding the fossils of three generations.
#:
#: Which fossils those rocks hold is a version exclusive, and a quiet one: Omega Ruby's rocks
#: hold the Dome, Armor and Plume Fossils, Alpha Sapphire's the Helix, Skull and Cover. The Old
#: Amber is in both. The Jaw and Sail Fossils of Kalos are in neither, which is the only reason
#: Tyrunt and Amaura are not on this list.
ORAS_MIRAGE_FOSSILS = (
    "Smashing rocks at the Mirage spots, once the story's legendary is dealt with, and revived "
    "at the Devon Corporation in Rustboro City"
)

ORAS_HANDED_OVER: dict[str, tuple[RecordedGift, ...]] = {
    "omega-ruby": (
        RecordedGift(
            species="kabuto",
            kind=GiftKind.FOSSIL,
            location="Rustboro City, Devon Corporation",
            requirement=f"Dome Fossil. {ORAS_MIRAGE_FOSSILS}",
        ),
        RecordedGift(
            species="shieldon",
            kind=GiftKind.FOSSIL,
            location="Rustboro City, Devon Corporation",
            requirement=f"Armor Fossil. {ORAS_MIRAGE_FOSSILS}",
        ),
        RecordedGift(
            species="archen",
            kind=GiftKind.FOSSIL,
            location="Rustboro City, Devon Corporation",
            requirement=f"Plume Fossil. {ORAS_MIRAGE_FOSSILS}",
        ),
    ),
    "alpha-sapphire": (
        RecordedGift(
            species="omanyte",
            kind=GiftKind.FOSSIL,
            location="Rustboro City, Devon Corporation",
            requirement=f"Helix Fossil. {ORAS_MIRAGE_FOSSILS}",
        ),
        RecordedGift(
            species="cranidos",
            kind=GiftKind.FOSSIL,
            location="Rustboro City, Devon Corporation",
            requirement=f"Skull Fossil. {ORAS_MIRAGE_FOSSILS}",
        ),
        RecordedGift(
            species="tirtouga",
            kind=GiftKind.FOSSIL,
            location="Rustboro City, Devon Corporation",
            requirement=f"Cover Fossil. {ORAS_MIRAGE_FOSSILS}",
        ),
    ),
}

#: The three both halves revive, written once.
ORAS_FOSSILS_BOTH = (
    RecordedGift(
        species="lileep",
        kind=GiftKind.FOSSIL,
        location="Rustboro City, Devon Corporation",
        requirement=(
            "Root Fossil, taken on Route 111 instead of the Claw Fossil; the other is lost for "
            "good, as it has been in that desert since Ruby and Sapphire"
        ),
    ),
    RecordedGift(
        species="anorith",
        kind=GiftKind.FOSSIL,
        location="Rustboro City, Devon Corporation",
        requirement=(
            "Claw Fossil, taken on Route 111 instead of the Root Fossil; the other is lost for "
            "good, as it has been in that desert since Ruby and Sapphire"
        ),
    ),
    RecordedGift(
        species="aerodactyl",
        kind=GiftKind.FOSSIL,
        location="Rustboro City, Devon Corporation",
        requirement=f"Old Amber. {ORAS_MIRAGE_FOSSILS}",
    ),
)


def oras_handed_over(game_id: str) -> tuple[RecordedGift, ...]:
    """The fossils one of the remakes revives: the three both have, and the three it keeps."""
    return (*ORAS_FOSSILS_BOTH, *ORAS_HANDED_OVER[game_id])


#: How each of this pair's forms is come by, keyed by form.
#:
#: Nearly all of it is the same table X and Y keep, with every item in a different place -
#: which is the reason a form's answer belongs to a region rather than to a generation. The
#: Reveal Glass is a woman selling mirrors in Mauville City here and a Scientist in Kalos; the
#: DNA Splicers are hidden in the Gnarled Den, which is the Mirage spot Kyurem itself waits in;
#: the Griseous Orb is underwater off Route 130, and the Gracidea is handed over on Route 123
#: for showing somebody a Shaymin.
ORAS_FORM_CHANGES: dict[str, FormChange] = {
    **spread(
        FormChange(
            requirement=(
                "Use the Reveal Glass on it, which the woman selling mirrors on the first floor "
                "hands over for being shown Tornadus, Thundurus or Landorus"
            ),
            where="Mauville City",
        ),
        "tornadus-therian",
        "thundurus-therian",
        "landorus-therian",
    ),
    "kyurem-black": FormChange(
        requirement=(
            "Fuse it with Zekrom using the DNA Splicers, which are hidden in the Gnarled Den - "
            "the Mirage spot Kyurem itself waits in; the fusion can be undone again"
        ),
    ),
    "kyurem-white": FormChange(
        requirement=(
            "Fuse it with Reshiram using the DNA Splicers, which are hidden in the Gnarled Den - "
            "the Mirage spot Kyurem itself waits in; the fusion can be undone again"
        ),
    ),
    "giratina-origin": FormChange(
        requirement="While it holds the Griseous Orb, which lies underwater off Route 130",
    ),
    "shaymin-sky": FormChange(
        requirement=(
            "Use the Gracidea, which is handed over for being shown a Shaymin; it turns back at "
            "night and in a box"
        ),
        where="Route 123",
    ),
    "keldeo-resolute": FormChange(
        requirement=(
            "While it knows Secret Sword, which the Swords of Justice teach it at the Pledge "
            "Grove in Unova and which it keeps wherever it goes afterwards"
        ),
    ),
    # The one form these two games invented, and the second in the dataset that a living dex
    # cannot hold: three days, and back in the bottle the moment it is put in a box.
    "hoopa-unbound": FormChange(
        requirement=(
            "Use the Prison Bottle, which a clerk in any Poke Mart hands over while a Hoopa is "
            "in the party; it folds back up after three days, or the moment it goes in a box"
        ),
    ),
    # The Cosplay Pikachu, which is these games' own and unlike anything else in the dataset.
    # Written out as six rather than keyed by species on purpose: a female Pikachu is a form
    # too, and it is not in a costume.
    **spread(
        FormChange(
            requirement=(
                "The Cosplay Pikachu, handed over after your first Contest Spectacular - as the "
                "Rock Star for a boy and the Pop Star for a girl - and dressed again by the "
                "Breeder in the green room. It cannot evolve, cannot breed, and cannot be "
                "traded or put into Bank: it stays on the cartridge it was given on"
            ),
            where="Any Contest Hall",
        ),
        "pikachu-cosplay",
        "pikachu-rock-star",
        "pikachu-belle",
        "pikachu-pop-star",
        "pikachu-phd",
        "pikachu-libre",
    ),
    # Burmy's cloak is the terrain of its last battle, which a player can do here even though no
    # Burmy is caught in Hoenn. Wormadam's is fixed at the moment it evolves.
    "burmy-sandy": FormChange(
        requirement="Let it battle in a cave or on sand; its cloak is wherever it last fought",
    ),
    "burmy-trash": FormChange(
        requirement="Let it battle indoors; its cloak is wherever it last fought",
    ),
    "wormadam-sandy": FormChange(
        requirement="Evolve a female Burmy wearing the Sandy Cloak; a Wormadam keeps that cloak",
    ),
    "wormadam-trash": FormChange(
        requirement="Evolve a female Burmy wearing the Trash Cloak; a Wormadam keeps that cloak",
    ),
}

#: The families where one sentence answers for every form of a species.
ORAS_FORM_CHANGES_BY_SPECIES: dict[str, FormChange] = {
    "rotom": FormChange(
        requirement="Let it possess one of the appliances in the boxes there",
        where="Littleroot Town, Professor Birch's lab",
    ),
    # Deoxys is the reason this step found something the shared table had wrong. Its formes were
    # pinned to the three Generation 3 cartridges that decide one each, and from Generation 4 on
    # a meteorite changes them at will - in these two it is the one in Professor Cozmo's house,
    # the same meteorite Ruby and Sapphire have a fetch quest about.
    "deoxys": FormChange(
        requirement="Touch the meteorite there; it cycles through all four formes",
        where="Fallarbor Town, Professor Cozmo's house",
    ),
    # Seasons ended with Generation 5, so Hoenn has one coat in its grass and three that can
    # only be bred or brought over - the same sentence Kalos needed for the same reason.
    **spread(
        FormChange(
            requirement=(
                "Hoenn has no seasons: every wild one wears the spring coat, and the other three "
                "only hatch from a mother wearing one or come over from Generation 5"
            ),
        ),
        "deerling",
        "sawsbuck",
    ),
}

#: The one family whose answer is the version's, which no other form in the dataset has been.
#:
#: Omega Ruby's Shellos are the West Sea kind and Alpha Sapphire's the East Sea kind, in the
#: same two places on Routes 103 and 110. The West Sea one is the plain species and needs no
#: record; the East Sea one is a form, and it is a form one half simply has and the other half
#: has not.
ORAS_EAST_SEA = FormChange(
    requirement=(
        "Caught as it is: every Shellos in Alpha Sapphire is the East Sea kind, where every one "
        "in Omega Ruby is the West Sea kind"
    ),
)

#: Species whose forms these two games have no way of producing, left without a record on
#: purpose.
#:
#: Seventy-five forms over nine species, and every one of them for the same reason: the species
#: is not in Hoenn at all. Unown's letters want ruins that are in Johto, and Vivillon's patterns,
#: Furfrou's trims, Flabebe's colours and Pumpkaboo's sizes all want Kalos - which is the other
#: half of this generation and a different set of games. A form with no sentence gets no record
#: rather than a guessed one.
ORAS_NOTHING_HERE = frozenset(
    {
        "unown",
        "vivillon",
        "furfrou",
        "flabebe",
        "floette",
        "florges",
        "pumpkaboo",
        "gourgeist",
        "basculin",
    }
)


def oras_form_changes(forms: Sequence[Form], *, game_id: str) -> dict[str, FormChange]:
    """One sentence for every form given that has one, and nothing for the rest.

    Built from the forms rather than handed back whole, for the reason :mod:`kalos` gives: what
    comes out should be about the game that asked. The id wins over the species where both have
    something to say, and one pair of forms is the version's own answer.
    """
    east_sea = {"shellos-east": ORAS_EAST_SEA, "gastrodon-east": ORAS_EAST_SEA}
    by_id = {**ORAS_FORM_CHANGES, **(east_sea if game_id == "alpha-sapphire" else {})}

    changes: dict[str, FormChange] = {}
    for form in forms:
        if form.species in ORAS_NOTHING_HERE:
            continue

        change = by_id.get(form.id) or ORAS_FORM_CHANGES_BY_SPECIES.get(form.species)
        if change is not None:
            changes[form.id] = change

    return changes


def gen6_acquisition_methods(
    context: BuildContext,
    *,
    game_id: str,
    version: str,
    column: str,
    entries: Sequence[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something in one of the remakes. Wild slots so far.

    Read off Bulbapedia rather than out of PokeAPI, which is the thing that makes these two
    games different from every other in this dataset. PokeAPI has encounter rows for them -
    hordes, the Mirage spots, a little Rock Smash - and no grass, no water and no fishing at
    all, so a build from that source says a Tentacool cannot be caught in Hoenn. The wiki has
    the whole table, one page per place, and :mod:`encountertables` reads it.

    PokeAPI is still read for what the wiki's location pages do not cover, which is the Mirage
    spots: twenty-odd islands, caves, forests and mountains that appear somewhere off the coast
    for a day and hold what Hoenn otherwise does not. Their rows are in the API and their pages
    are not tables, so each source answers where the other is silent and a place that both know
    about is the wiki's - otherwise every horde in Hoenn would be recorded twice.

    ``column`` is how those pages' Games column spells this half: "OR" or "AS". It is the only
    place a version exclusive is written down - as a colour rather than as a word.
    """
    api = context.require_api()
    species = context.living_dex(through=gen6.NATIONAL_DEX_THROUGH, entries=entries)
    # The Mirage spots and the gifts are read out of the same tables and walk into the same
    # places, so they share one lookup - and one correction to a slug that misspells Rustboro.
    places = LocationNames(
        api,
        refresh=context.refresh,
        renamed_sub_areas=ORAS_RENAMED_SUB_AREAS,
    )
    scraped = set(ORAS_PAGES.values())
    elsewhere = [
        one
        for one in wild_encounters(
            api,
            game_id=game_id,
            version=version,
            species=species,
            forms=context.forms_here(),
            refresh=context.refresh,
            places=places,
        )
        if one.location not in scraped
    ]

    found: list[AcquisitionMethod] = [
        *table_encounters(
            context.require_wiki(),
            game_id=game_id,
            column=column,
            pages=ORAS_PAGES,
            methods=ORAS_METHODS,
            requirements=ORAS_METHOD_REQUIREMENTS,
            conditions=ORAS_CONDITIONS,
            aliases=ORAS_SPECIES_ALIASES,
            species=set(species),
            refresh=context.refresh,
        ),
        *elsewhere,
        *gift_encounters(
            api,
            game_id=game_id,
            version=version,
            species=species,
            details=oras_gifts(game_id),
            refresh=context.refresh,
            places=places,
        ),
        *recorded_gifts(
            game_id=game_id,
            gifts=oras_handed_over(game_id),
            species=species,
            citation=bulbapedia("Fossil", retrieved_on=date.today()),
        ),
        *evolution_encounters(
            api,
            game_id=game_id,
            version_group=ORAS_VERSION_GROUP,
            species=species,
            forms=context.forms_here(),
            all_forms=context.forms,
            refresh=context.refresh,
        ),
        *trade_encounters(
            game_id=game_id,
            trades=ORAS_TRADES,
            citation=bulbapedia("In-game_trade", retrieved_on=date.today()),
        ),
    ]

    # Last, and worked out from what the steps above came to rather than from a table: the day
    # care can only be asked for what nothing else here produces, so it cannot be answered until
    # everything else has been.
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

    found.extend(
        form_change_encounters(
            game_id=game_id,
            forms=context.forms_here(),
            changes=oras_form_changes(context.forms_here(), game_id=game_id),
            citation=bulbapedia(
                "List_of_Pok%C3%A9mon_with_form_differences", retrieved_on=date.today()
            ),
        )
    )

    return found


def gba_dex_entries(
    context: BuildContext,
    *,
    game_id: str,
    unobtainable: Mapping[str, str] | None = None,
) -> list[DexEntry]:
    """The Hoenn dex as all three cartridges number it: Treecko #001 to Deoxys #202.

    This is the game's own dex, not the list a living dex in it is aiming at. That list is the
    National Dex, which the entity already says it reaches 386 of; this one is what the game's
    own Pokedex shows and what the coverage report measures encounters against.

    Ruby, Sapphire and Emerald share these entries *and their numbering*, which is why one
    function answers for all three. What differs between them is which entries their own grass
    never holds, and that is the ``unobtainable`` table each game brings.

    Deoxys is the one form question in Hoenn - it takes a different forme in each of the three -
    and it waits for the shared forms table, which is still empty. Nothing else in the region
    has a form.
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
        for number, species in api.pokedex(GBA_DEX, refresh=context.refresh)
    ]


def gba_pair_acquisition_methods(
    context: BuildContext,
    *,
    game_id: str,
    version: str,
    entries: Sequence[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something in one of the pair.

    Steps 3 to 5, and every one of them the same for both halves except for one word - which
    version PokeAPI is asked about. Everything else they share, which is why the tables this
    reads are module-level here rather than passed in: two copies of the same three trades is
    how one of them gets edited and the other does not.

    The wild and gift steps read the same encounter tables and walk into the same places, so
    they share one place lookup: Route 119 is named once however many times it comes up.
    """
    api = context.require_api()
    # Every species the living dex here asks for, which is not the game's own Pokedex. Those
    # are two different lists, and asking only about the second is what left every entry
    # outside the regional dex with nothing recorded against it - in games that produce plenty
    # of them.
    species = context.living_dex(through=GBA_NATIONAL_DEX_THROUGH, entries=entries)
    today = date.today()
    places = LocationNames(api, refresh=context.refresh)

    return [
        *wild_encounters(
            api,
            game_id=game_id,
            version=version,
            species=species,
            forms=context.forms_here(),
            refresh=context.refresh,
            places=places,
        ),
        *gift_encounters(
            api,
            game_id=game_id,
            version=version,
            species=species,
            details=GBA_PAIR_GIFTS,
            refresh=context.refresh,
            places=places,
        ),
        *evolution_encounters(
            api,
            game_id=game_id,
            version_group=GBA_PAIR_VERSION_GROUP,
            species=species,
            forms=context.forms_here(),
            all_forms=context.forms,
            refresh=context.refresh,
        ),
        *breeding_encounters(
            game_id=game_id,
            day_care=DAY_CARE,
            eggs=GBA_PAIR_EGGS,
            citation=bulbapedia("Baby_Pok%C3%A9mon", retrieved_on=today),
        ),
        *trade_encounters(
            game_id=game_id,
            trades=GBA_PAIR_TRADES,
            citation=bulbapedia("In-game_trade", retrieved_on=today),
        ),
    ]


#: The Bonus Disc that came with Pokemon Colosseum in the West, and the Tanabata giveaways in
#: Japan. Nothing in any of the three games produces one, so all three say the same thing.
GBA_JIRACHI_REASON = (
    "Distribution event only: the Pokemon Colosseum Bonus Disc in the West, and the "
    "Tanabata Jirachi giveaways in Japan"
)


#: The one distribution that covers most of what these games cannot produce: a Japanese campaign
#: that ran for three weeks in 2006 and handed out, among others, most of the version exclusives
#: - for Ruby, Sapphire, Emerald, FireRed and LeafGreen alike.
FIFTH_CAMPAIGN = "a 2006 Japanese event (Gather More Pokemon! Fifth Campaign) handed one out"

#: Four of the exclusives were also given away in English, at the Pokemon Center in New York in
#: the summer of 2004, and those carts were Ruby and Sapphire specifically.
FIFTH_CAMPAIGN_AND_NEW_YORK = (
    f"{FIFTH_CAMPAIGN}, and the Pokemon Center in New York gave one out in English in 2004"
)

#: Never caught in any of the three: the two 2006 distributions handed the Pokemon itself over,
#: where Emerald's Aurora Ticket instead opened the island it waits on.
GBA_DEOXYS_REASON = (
    "Distribution event only: the Space Center Deoxys in the United States and the Doel Deoxys "
    "in the Netherlands, both in 2006"
)


def handed_out(*events: str) -> str:
    """One sentence naming every distribution that ever handed this species out."""
    return exclusives.handed_out(*events)


#: What step 7 found about the one entry these two hold and nothing in any game produces.
#:
#: Nine distributions reached these games, which is more than any other entry in the dataset
#: has, and not one of them is a door a player can walk through now. The Pokemon Center Jirachi
#: and both Tanabata giveaways were Japan's; the twentieth anniversary one, in April 2016, is
#: the one most players outside Japan could have had.
#:
#: Jirachi has never been catchable in any game. Generation 3's answer is the Colosseum Bonus
#: Disc and Generation 6's is this, and in between there was nothing at all.
ORAS_JIRACHI_REASON = exclusives.with_event(
    "Nothing in Hoenn produces one, and nothing ever has: it has only been given away",
    exclusives.handed_out(
        "the Pokemon Center Jirachi in Japan over the winter of 2014",
        "the 2015 and 2016 Tanabata Jirachi in Japan",
        "the Nintendo Hong Kong Jirachi",
        "the Pokemon 20th Anniversary Jirachi in America and Europe in April 2016",
    ),
)


def gen6_only_on(partner: str, event: str | None = None) -> str:
    """Why an entry in this dex is not in this remake, when the other half has it.

    The same sentence the rest of the dataset uses, with this generation's number in it - so a
    player reads "Alpha Sapphire only in Generation 6" here and "Sapphire only in Generation 3"
    one shelf down, and the two are not confused for each other.
    """
    return gen6.only_on(partner, event)


def gba_only_on(partner: str, event: str | None = None) -> str:
    """Why an entry in this dex is not in this cartridge, when the other half has it.

    The wording is :mod:`gba`'s: FireRed and LeafGreen split their exclusives exactly the way
    Ruby and Sapphire do, and a player should read the same sentence either way.
    """
    return gba.only_on(partner, event)


#: Who hands a Pokemon over in Ruby and Sapphire, and what has to be true first.
#:
#: One table for the two of them. PokeAPI knows the method, the place and the level; the rest is
#: the cartridge's own business, and on that the pair agree about every species they share. Where
#: they differ they differ by *which* species turns up at all - Groudon in one Cave of Origin and
#: Kyogre in the other - so a key that the other half never sees simply never matches.
#:
#: Emerald keeps a table of its own. It reads the same in places and must not be merged: its
#: legendary hides in a cave that moves, its Rayquaza waits on a fight that only it has, and its
#: Desert Underpass hands over the fossil the other two can never take.
GBA_PAIR_GIFTS: dict[str, GiftDetail] = {
    "treecko": GiftDetail(
        kind=GiftKind.STARTER,
        npc="Professor Birch",
        requirement="Pick one of the three; the other two take a trade",
    ),
    "torchic": GiftDetail(
        kind=GiftKind.STARTER,
        npc="Professor Birch",
        requirement="Pick one of the three; the other two take a trade",
    ),
    "mudkip": GiftDetail(
        kind=GiftKind.STARTER,
        npc="Professor Birch",
        requirement="Pick one of the three; the other two take a trade",
    ),
    # Two fossils lie in the desert on Route 111 and taking one loses the other. The Mirage
    # Tower they are inside in Emerald is Emerald's alone, and so is the Desert Underpass that
    # gives the second one back - in these two the choice really is final. Corrected while the
    # remakes were being written, which ask the same question in the same desert.
    "lileep": GiftDetail(
        kind=GiftKind.FOSSIL,
        npc="Devon Corporation scientist",
        requirement=(
            "Root Fossil, taken on Route 111 instead of the Claw Fossil; the other is lost for "
            "good"
        ),
    ),
    "anorith": GiftDetail(
        kind=GiftKind.FOSSIL,
        npc="Devon Corporation scientist",
        requirement=(
            "Claw Fossil, taken on Route 111 instead of the Root Fossil; the other is lost for "
            "good"
        ),
    ),
    "beldum": GiftDetail(
        npc="Steven",
        requirement="In the Poke Ball in his house, after the Elite Four",
    ),
    "castform": GiftDetail(
        npc="Weather Institute scientist",
        requirement="After driving the villains out of the Weather Institute",
    ),
    "wynaut": GiftDetail(
        npc="Woman in Lavaridge Town",
        requirement="Hatches from the egg she gives you",
    ),
    "kecleon": GiftDetail(requirement="Devon Scope, to see it at all"),
    "regirock": GiftDetail(requirement="Braille puzzle, with Relicanth and Wailord in the party"),
    "regice": GiftDetail(requirement="Braille puzzle, with Relicanth and Wailord in the party"),
    "registeel": GiftDetail(requirement="Braille puzzle, with Relicanth and Wailord in the party"),
    # Southern Island is reached with a ticket that was only ever handed out at events. Which of
    # the two waits there is the version's business: Ruby's island holds Latias and Sapphire's
    # holds Latios, each the opposite of the one roaming its own Hoenn.
    "latias": GiftDetail(requirement="Eon Ticket, a distribution event"),
    "latios": GiftDetail(requirement="Eon Ticket, a distribution event"),
}


#: The three NPCs who will trade in Ruby and Sapphire, and what each one wants for it.
#:
#: One table again: the pair share these three, where Emerald swapped them for four of its own.
#: No API carries them. The names are the original trainers the game records on what it hands
#: over, which is how a player can tell a traded Pokemon from a caught one.
GBA_PAIR_TRADES = (
    InGameTrade(gets="makuhita", wants="slakoth", location="Rustboro City", npc="Elyssa"),
    InGameTrade(gets="skitty", wants="pikachu", location="Fortree City", npc="Darrell"),
    InGameTrade(
        gets="corsola",
        wants="bellossom",
        location="Pacifidlog Town",
        npc="Lane",
        requirement="A Bellossom, which takes a Sun Stone on a Gloom",
    ),
)

#: The babies nothing else in these games produces.
#:
#: Wynaut is not here although it breeds too: both cartridges hand one over in an egg, and a
#: record for the long way round adds nothing. Generation 3 asks for no incense, so no parent
#: here has to be holding anything.
GBA_PAIR_EGGS: dict[str, EggFrom] = {
    "pichu": EggFrom(parents=("pikachu", "raichu")),
    "igglybuff": EggFrom(parents=("jigglypuff", "wigglytuff")),
    "azurill": EggFrom(parents=("marill", "azumarill")),
}
