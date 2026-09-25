"""What Brilliant Diamond and Shining Pearl share: Sinnoh on a console that has no cable.

The third pair of Generation 8 and the first remakes in this dataset that are not of a game the
dataset also holds as a cartridge - Diamond and Pearl are here, built from :mod:`sinnoh`, and
these two are those games again fifteen years later on different hardware, by a different studio,
with a National Pokedex that stops where the original's did.

**Why this file and not** :mod:`sinnoh`. That module holds what is true of the place across the
generations that have visited it, and it is written for Generation 4: its ``cartridge`` and its
``edges`` both hand the question straight to :mod:`ds`, which answers with a link cable to four
other games and Pal Park from the generation before. Neither sentence is true here. These two
have one cable and it runs to each other; the way in and out is HOME; and the generation is 8.
The overlap that *is* real is step 2's and step 3's to find - the same 151 in the same order,
the same towns, the same routes, mostly the same grass - and this is the same arrangement
:mod:`lets_go` made with :mod:`kanto`: whatever turns out to be about Sinnoh rather than about
this pair moves there and is named for its hardware, the way ``gb_`` and ``gba_`` already are.

**Why this file and not a Switch module.** :mod:`gb`, :mod:`gbc`, :mod:`gba`, :mod:`ds` and
:mod:`gen6` each hold what one generation's cartridges share, and the Switch equivalent keeps
not existing for the same reason each time. Six games sit on that console across two generations
and no two of them share a way out: Let's Go takes back only what it made itself, these take
back only what their engine can hold, Legends: Z-A gives nothing back at all. What they have in
common is HOME, and HOME has had a module since before any of them was written.

**What these two cannot do is the shape of the graph around them**, and Bulbapedia says it in
the same sentence it says it about Sword and Shield: as with other games on the Nintendo Switch,
they are not compatible with other games in the same generation outside of their pairing. So
there is no route to Sword, none to Legends: Arceus, none to the two Let's Go games. Three
routes, not thirty: the cable between the halves and HOME in each direction.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from ..archives import HOME_SET
from ..breeding import CAUGHT, breeding_encounters, day_care_eggs
from ..encountertables import table_encounters
from ..evolutions import evolution_encounters
from ..formchanges import FormChange, form_change_encounters, spread
from ..games import BuildContext
from ..gifts import RecordedGift, recorded_gifts
from ..models import (
    AcquisitionMethod,
    AllSpeciesFilter,
    DexEntry,
    DexSource,
    EncounterMethod,
    Game,
    GameRelease,
    GiftKind,
    SourceCitation,
    TransferDirection,
    TransferEdge,
    TransferMechanism,
)
from ..pokeapi import BASE_URL
from ..sources import ReadByHand
from ..trades import trade_encounters
from . import exclusives, home, sinnoh

#: Generation 8, which is the console and the year rather than the game being remade.
#:
#: The same number Sword and Shield carry, and the games could hardly be less alike: those two
#: hold a list and no National Dex, these hold a National Dex of 493 and nothing above it. A
#: generation is when a game came out, not what it is about.
GENERATION = 8

REGION = "Sinnoh"

#: One day, everywhere. Japan, North America, Europe, Australia, South Korea, Hong Kong and
#: Taiwan all on 19 November 2021 - which the Generation 4 originals emphatically were not.
RELEASED = date(2021, 11, 19)

#: The two halves, spelled here so anything below can say "the other one" in one word.
PAIR = ("brilliant-diamond", "shining-pearl")

#: What PokeAPI calls the two of them together when it says which group something belongs to.
VERSION_GROUP = "brilliant-diamond-shining-pearl"

#: The National Dex opens after the Elite Four here as it did in 2007, and stops at Arceus.
#:
#: **This is the decision Galar did not have**, and it goes the other way. Sword and Shield were
#: the first games in the series whose boxes hold a list rather than everything up to a number,
#: so their entity says ``national_dex_through=None`` and leaves the answer to a dex list. These
#: are a remake of the generation that invented the National Dex, they kept it, and the number
#: is the one Diamond and Pearl had. What a living dex here is aiming at is 493.
NATIONAL_DEX_THROUGH = 493

#: Where these two get their pictures, which is not a sheet of their own because there is none.
#:
#: **The Archives have nothing for this pair**: the only category carrying their name holds
#: trainer select-screen models, and the two files under Scarlet and Violet's are not a sheet
#: either. What the wiki draws the modern games with is Pokemon HOME's renders, and that is the
#: honest answer as well as the available one - these games have no battle sprite to photograph,
#: so a HOME render is the picture a player sees when they open a box.
SPRITE_SET = HOME_SET


#: Every place in these two whose encounter tables are read off Bulbapedia.
#:
#: Fifty-six pages, and the source is the wiki rather than PokeAPI because **PokeAPI has no
#: encounter at all for these games** - not a thin table, none. `bidoof` answers with seven
#: versions and not one of them is this pair. That is the reading done before Generation 8's
#: remaining games, and it holds for all six of them.
#:
#: The wiki's title and this dataset's name disagree in one way only, and it is the Hoenn one:
#: "Sinnoh Route 201" tells it from Kanto's and Johto's, where everything else here says
#: "Route 201". Written as a rule rather than thirty names typed twice.
PAGE_TITLES: tuple[str, ...] = (
    *(f"Sinnoh_Route_{number}" for number in range(201, 231)),
    "Twinleaf_Town",
    "Oreburgh_City",
    "Floaroma_Town",
    "Eterna_City",
    "Hearthome_City",
    "Pastoria_City",
    "Celestic_Town",
    "Canalave_City",
    "Snowpoint_City",
    "Sunyshore_City",
    "Resort_Area",
    "Lake_Verity",
    "Lake_Valor",
    "Lake_Acuity",
    "Acuity_Lakefront",
    "Valor_Lakefront",
    "Eterna_Forest",
    "Oreburgh_Gate",
    "Oreburgh_Mine",
    "Ravaged_Path",
    "Valley_Windworks",
    "Fuego_Ironworks",
    "Wayward_Cave",
    "Mt._Coronet",
    "Solaceon_Ruins",
    "Lost_Tower",
    "Maniac_Tunnel",
    "Ruin_Maniac_Cave",
    "Trophy_Garden",
    "Great_Marsh",
    "Iron_Island",
    "Old_Chateau",
    "Victory_Road_(Sinnoh)",
    "Sendoff_Spring",
    "Turnback_Cave",
    "Stark_Mountain",
    "Snowpoint_Temple",
    "Pok%C3%A9mon_League_(Sinnoh)",
    # Not a place, and the only page here that is not one. A honey tree is twenty-one trees
    # scattered over Sinnoh and the wiki keeps one table for all of them, so this dataset can
    # say what a slathered tree gives and not which tree - where Diamond, whose slots came from
    # PokeAPI one location at a time, names Valley Windworks and the rest.
    "Honey_tree",
)

#: The eighteen caves under Sinnoh, which are this pair's own and have a page each.
#:
#: The Grand Underground is Diamond and Pearl's Underground rebuilt: the digging and the Secret
#: Bases are still there, and what is new is that Pokemon walk around in it. Eleven caves are
#: reached from the tunnels and seven more open after the National Pokedex does, and between
#: them they hold species Sinnoh above ground has none of - which is why a remake's encounter
#: list is not its original's.
#:
#: Named as one place with the cave after it, because that is what a player would say. The cave
#: pages themselves split into "Visible Encounters" and "Rare Spawns", and that split arrives
#: as the sub-area without anything here naming it.
HIDEAWAYS: dict[str, str] = {
    "Dazzling_Cave": "Dazzling Cave",
    "Fountainspring_Cave": "Fountainspring Cave",
    "Grassland_Cave": "Grassland Cave",
    "Icy_Cave": "Icy Cave",
    "Riverbank_Cave": "Riverbank Cave",
    "Rocky_Cave": "Rocky Cave",
    "Sandsear_Cave": "Sandsear Cave",
    "Spacious_Cave": "Spacious Cave",
    "Swampy_Cave": "Swampy Cave",
    "Volcanic_Cave": "Volcanic Cave",
    "Whiteout_Cave": "Whiteout Cave",
    "Big_Bluff_Cavern": "Big Bluff Cavern",
    "Bogsunk_Cavern": "Bogsunk Cavern",
    "Glacial_Cavern": "Glacial Cavern",
    "Stargleam_Cavern": "Stargleam Cavern",
    "Still-Water_Cavern": "Still-Water Cavern",
    "Sunlit_Cavern": "Sunlit Cavern",
    "Typhlo_Cavern": "Typhlo Cavern",
}

PAGES: dict[str, str] = {
    **{
        title: title.replace("_", " ").removeprefix("Sinnoh ").removesuffix(" (Sinnoh)")
        for title in PAGE_TITLES
    },
    **{title: f"Grand Underground, {name}" for title, name in HIDEAWAYS.items()},
}

#: What the Location column on those pages means, in this project's words.
#:
#: A word that is not here is skipped, and the skipped ones are the point as much as the kept
#: ones: "Gift", "Egg" and the three "Trade ..." rows are steps 4 and 5 and have records of
#: their own, so reading them here would put a starter in the grass.
#:
#: The floors are a page's own habit rather than a way of meeting anything - Iron Island and
#: Victory Road write which floor a table covers in the column where every other page writes
#: the method, and a floor is still walking.
METHODS: dict[str, EncounterMethod] = {
    "Grass": EncounterMethod.WALK,
    "Cave": EncounterMethod.WALK,
    "Walking": EncounterMethod.WALK,
    "Swarm": EncounterMethod.WALK,
    "Poké Radar": EncounterMethod.WALK,
    "Backlot": EncounterMethod.WALK,
    "1F": EncounterMethod.WALK,
    "2F": EncounterMethod.WALK,
    "3F": EncounterMethod.WALK,
    "4F": EncounterMethod.WALK,
    "5F": EncounterMethod.WALK,
    "Honey Tree": EncounterMethod.HONEY_TREE,
    "Surfing": EncounterMethod.SURF,
    "Fishing Old Rod": EncounterMethod.OLD_ROD,
    "Fishing Good Rod": EncounterMethod.GOOD_ROD,
    "Fishing Super Rod": EncounterMethod.SUPER_ROD,
}

#: What a page's word says that :class:`EncounterMethod` cannot hold.
#:
#: All three are walking and none of them is the grass a player is already standing in. The
#: swarm and the Poke Radar are worded the way Diamond words them, because they are the same
#: two things fifteen years later and a player reading both games should read one sentence.
METHOD_REQUIREMENTS: dict[str, str] = {
    "Swarm": "Only while it is swarming",
    "Poké Radar": "With the Poke Radar running",
    "Backlot": (
        "Only on days Mr. Backlot's story rotates it into the garden, and after the National "
        "Pokedex opens"
    ),
}

#: A heading the wiki writes for its own readers, reworded for a player - or dropped.
#:
#: Dropped where it says only what the row already says: "Base Encounters" is a Grand
#: Underground page distinguishing the ordinary pool from the rare one, which the sub-area
#: already carries, and "Special Pokemon" sits over rows whose Location column says Poke Radar.
#: A heading that is not here is passed through as it stands, which is right for the ones that
#: say where in a place to stand.
CONDITIONS: dict[str, str] = {
    "Base Encounters": "",
    "Special Pokémon": "",
    "Gift Pokémon": "",
    "First partner Pokémon": "",
    "Added after obtaining the National Pokédex": "After the National Pokedex opens",
    # The dash in these two is an en dash on the page, and a key has to be what is written
    # rather than what it ought to be. It is the only one in the dataset.
    "Post–National Pokédex": "After the National Pokedex opens",  # noqa: RUF001
    "Pre–National Pokédex only": "Only before the National Pokedex opens",  # noqa: RUF001
    "Added after obtaining TM96 ( Strength )": (
        "Once Strength has been taught, which is TM96 here"
    ),
    "Added after obtaining TM97 ( Defog )": "Once Defog has been taught, which is TM97 here",
    "Added after obtaining TM99 ( Waterfall )": (
        "Once Waterfall has been taught, which is TM99 here"
    ),
    "Added after earning the Icicle Badge": "After earning the Icicle Badge",
    "Fewer than 10 Unown": "While fewer than ten kinds of Unown have been caught",
    "10-25 Unown": "Once ten kinds of Unown have been caught",
    "26 or more Unown": "Once twenty-six kinds of Unown have been caught",
    "Four random squares": "On four squares the game picks each day",
    "Dead-end rooms": "In the rooms the tunnels dead-end at",
    "Normal tree": "",
    "Munchlax tree": (
        "Only on the four trees each save file picks, which are the only ones a Munchlax uses"
    ),
    "Room through Maniac Tunnel": "In the room the Maniac Tunnel opens into",
}

#: Names the wiki spells one way and PokeAPI another.
#:
#: Both seas of one Shellos and both of one Gastrodon are one entry here until the form table
#: says otherwise, which is the same answer Hoenn gives.
SPECIES_ALIASES: dict[str, str] = {
    "shellos-west-sea": "shellos",
    "shellos-east-sea": "shellos",
    "gastrodon-west-sea": "gastrodon",
    "gastrodon-east-sea": "gastrodon",
}

#: The two letters these games fill their Games column with.
COLUMNS: dict[str, str] = {"brilliant-diamond": "BD", "shining-pearl": "SP"}


def cartridge(
    *,
    game_id: str,
    title: str,
    version: str,
    pair_partner: str,
    sprite_set: str | None = SPRITE_SET,
) -> Game:
    """One half of the pair, with everything the two of them agree about filled in.

    ``sprite_set`` is :data:`SPRITE_SET`, which step 6 filled in: these games have no sheet of
    their own anywhere, so what a tile shows is a Pokemon HOME render - the first set in this
    dataset that is not a generation's, and one four games in two generations will share.
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
        dex_source=DexSource.NATIONAL_DEX,
        pair_partner=pair_partner,
        sprite_set=sprite_set,
    )


#: How a form that is not met is come by. A sex needs no line: :mod:`formchanges` answers it.
#:
#: **Diamond and Pearl's table plus the three Platinum added**, which is the same shape the form
#: list itself came out in - and the two places these games differ from Platinum are worth the
#: separate sentences.
#:
#: The meteorites are unchanged and were checked rather than carried over: the wiki has a
#: "Meteorites in Pokemon Brilliant Diamond and Shining Pearl" section saying four of them stand
#: on the east side of Veilstone City and a Deoxys in the party changes form when they are
#: inspected. Deoxys itself can only arrive through HOME, which is a different question.
FORM_CHANGES: dict[str, FormChange] = {
    **sinnoh.PAIR_FORM_CHANGES,
    **spread(
        FormChange(
            requirement=(
                "Let it possess one of the appliances in Rotom's Room. The Secret Key that opens "
                "the room arrives on its own here, the moment the Rotom in the Old Chateau is "
                "caught - where in Platinum it was the first of four items handed out at events"
            ),
            where="Eterna City, Team Galactic Eterna Building",
        ),
        "rotom-heat",
        "rotom-wash",
        "rotom-frost",
        "rotom-fan",
        "rotom-mow",
    ),
    "giratina-origin": FormChange(
        requirement=(
            "While it holds the Griseous Orb. There is no Distortion World here, so unlike "
            "Platinum that is the only way it takes this shape"
        )
    ),
    "shaymin-sky": FormChange(
        requirement=(
            "Use the Gracidea on it in daylight; it goes back to Land Forme at night and while "
            "it is frozen"
        )
    ),
}


#: Why nothing in these two produces a Manaphy.
#:
#: Diamond and Pearl hatch it from an egg Pokemon Ranger sends over, and Ranger is a Nintendo DS
#: game with no version of itself on this console. So the remake inherited the hole and not the
#: way out of it - which is the one place where a remake of a linked game is poorer than the
#: game it remakes.
MANAPHY_REASON = (
    "Nothing here produces one. Pokemon Ranger sent the egg to Diamond and Pearl, and there is "
    "no Ranger on this console to send it"
)

#: And what step 7 found, which is one distribution and a generous one.
#:
#: Measured rather than assumed: of the nine entries these two halves cannot fill between them,
#: **Manaphy is the only one any distribution ever covered**, and the wiki's table for it lists
#: exactly one row for these games. It opened on the day the games came out and ran for three
#: months - so a player who bought them at release could fill this entry, and one who bought
#: them in March could not.
MANAPHY_EVENT = (
    "the Manaphy Egg was handed out over the internet from 19 November 2021, the day these "
    "games came out, until 21 February 2022"
)

#: Everything Shining Pearl has that Brilliant Diamond cannot produce, and what step 7 found.
#:
#: Four each, and every value is None: **not one distribution in the series ever handed out a
#: Misdreavus, a Glameow, a Palkia, a Shieldon, a Murkrow, a Stunky, a Cranidos or a Dialga for
#: these games.** Checked species by species against the wiki's own events table rather than
#: assumed, and the emptiness is a finding: a version exclusive is filled by the link to the
#: other half, which is exactly what the transfer graph is for.
#:
#: The evolutions behind them are not listed. Mismagius, Purugly and Bastiodon have evolution
#: records here and no base to use them on, and :func:`reach.spread_unobtainable` pushes the
#: reason down the line rather than each line being typed twice.
ONLY_ON: dict[str, dict[str, str | None]] = {
    "brilliant-diamond": {"misdreavus": None, "glameow": None, "palkia": None},
    "shining-pearl": {"murkrow": None, "stunky": None, "dialga": None},
}

#: The other half's fossil, which takes its own sentence: a fossil can travel held by a traded
#: Pokemon, so there are two ways across the link rather than one.
FOSSIL_ONLY_ON: dict[str, tuple[str, str]] = {
    "brilliant-diamond": ("shieldon", "Armor Fossil"),
    "shining-pearl": ("cranidos", "Skull Fossil"),
}

#: What each half calls the other in a sentence a player reads.
TITLES: dict[str, str] = {
    "brilliant-diamond": "Brilliant Diamond",
    "shining-pearl": "Shining Pearl",
}


def unobtainable_in(game_id: str) -> dict[str, str]:
    """Dex entries no amount of playing this half will fill, and why.

    A reason rather than a gap: the validator can tell "we checked and it cannot be caught" from
    "we have not gathered this yet", and only the second is a fault.
    """
    partner = TITLES[PAIR[0] if game_id == PAIR[1] else PAIR[1]]
    fossil, item = FOSSIL_ONLY_ON[game_id]

    return {
        "manaphy": exclusives.with_event(MANAPHY_REASON, MANAPHY_EVENT),
        fossil: exclusives.fossil_only_on(
            partner, item, generation=GENERATION, event=None
        ),
        **{
            species: exclusives.only_on(partner, generation=GENERATION, event=event)
            for species, event in ONLY_ON[game_id].items()
        },
    }


def dex_entries(
    context: BuildContext,
    *,
    game_id: str,
    unobtainable: Mapping[str, str] | None = None,
) -> list[DexEntry]:
    """The Sinnoh dex these two show, which is the one Diamond and Pearl showed: 151 entries.

    Asked of :mod:`sinnoh` rather than held here, and that is the arrangement working rather
    than a shortcut. A Pokedex is a fact about the region and the list is the same list -
    Bulbapedia calls it "the Sinnoh Pokedex's return to the original Diamond and Pearl
    numbering", and PokeAPI files ``original-sinnoh`` under both version groups. Turtwig is
    #001 and Manaphy #151 in four games now.

    **Not Platinum's 210.** The third version of 2008 added 59 species to the regional list and
    these remakes did not take them, which is the only place a remake could have quietly grown
    and did not. What it means for a player is real: Eevee's family, Togepi's, Rotom and Scyther
    are National Dex work here, the way they were in 2007.

    The list is not what a living dex in these games is aiming at. That is the National Dex,
    which the entity says reaches 493 - so the grid is 493 tiles and the Pokedex on screen is
    151 of them, exactly as it is in Diamond.

    No ``unobtainable`` table yet, and the parameter is here because the two halves will each
    bring one: which entries a cartridge can never fill is what steps 3 to 7 find out, and
    guessing now would be claiming to have looked.
    """
    return sinnoh.original_dex_entries(context, game_id=game_id, unobtainable=unobtainable)


#: Where the form table below was read, which is one page for all of it.
FORMS_PAGE = "List_of_Pok%C3%A9mon_with_form_differences"

#: Where every gift and static below was read, which is one page for all of them.
EVENT_PAGE = (
    "List_of_in-game_event_Pok%C3%A9mon_in_Pok%C3%A9mon_Brilliant_Diamond_and_Shining_Pearl"
)

#: The day a person read the page the tables below were typed from.
READ_ON = ReadByHand(
    {
        EVENT_PAGE: date(2026, 9, 25),
        "In-game_trade": date(2026, 9, 25),
        FORMS_PAGE: date(2026, 9, 25),
    }
)

#: Everything both halves hand over, hatch or leave standing in one spot.
#:
#: Written out rather than described, because there is nothing to describe it *to*: PokeAPI has
#: no encounter for these games, so unlike every game before Let's Go there is no row here for a
#: :class:`GiftDetail` to add a sentence to. A gift, an egg, a fossil and a legendary standing
#: in a cave are one kind of record and the ``kind`` field is what tells them apart.
#:
#: **The two Mythical Pokemon in Floaroma Town are the strangest thing in this table**, and they
#: are in it because a player can still get them: an old woman hands over a Mew if the console
#: has Let's Go save data and an old man a Jirachi if it has Sword or Shield save data. That is
#: not an event that closed in 2022 - it is a condition on hardware, and a player who owns those
#: games can meet it today. Compare the three below it that are genuinely shut.
GIFTS: tuple[RecordedGift, ...] = (
    # --- the briefcase ------------------------------------------------------------------------
    *(
        RecordedGift(
            species=one,
            location="Lake Verity",
            level=5,
            kind=GiftKind.STARTER,
            npc="Professor Rowan",
            requirement=(
                "Pick one of the three from the suitcase to see off the wild Starly; the other "
                "two take a trade"
            ),
        )
        for one in ("turtwig", "chimchar", "piplup")
    ),
    # --- what the Grand Underground digs up, revived ------------------------------------------
    *(
        RecordedGift(
            species=species,
            location="Oreburgh City, Oreburgh Mining Museum",
            kind=GiftKind.FOSSIL,
            requirement=(
                f"{fossil}, dug up in the Grand Underground once Dialga or Palkia has been "
                "caught or beaten on the Spear Pillar"
            ),
        )
        for species, fossil in (
            ("omanyte", "Helix Fossil"),
            ("kabuto", "Dome Fossil"),
            ("aerodactyl", "Old Amber"),
            ("lileep", "Root Fossil"),
            ("anorith", "Claw Fossil"),
        )
    ),
    # --- handed over --------------------------------------------------------------------------
    RecordedGift(
        species="eevee",
        location="Hearthome City",
        level=5,
        npc="Bebe",
        requirement="After the National Pokedex opens",
    ),
    RecordedGift(
        species="mew",
        location="Floaroma Town",
        level=1,
        npc="An old woman",
        requirement=(
            "With save data from Let's Go, Pikachu! or Let's Go, Eevee! on the same console"
        ),
    ),
    RecordedGift(
        species="jirachi",
        location="Floaroma Town",
        level=5,
        npc="An old man",
        requirement="With save data from Sword or Shield on the same console",
    ),
    # --- hatched ------------------------------------------------------------------------------
    RecordedGift(
        species="happiny",
        location="Hearthome City",
        level=1,
        kind=GiftKind.EGG,
        npc="A Hiker",
    ),
    RecordedGift(
        species="riolu",
        location="Iron Island",
        level=1,
        kind=GiftKind.EGG,
        npc="Riley",
        requirement="After going through Iron Island with him",
    ),
    # --- standing in one spot -----------------------------------------------------------------
    RecordedGift(
        species="drifloon",
        location="Valley Windworks",
        level=22,
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement="On a Friday, once Mars has been beaten at the Valley Windworks",
    ),
    RecordedGift(
        species="spiritomb",
        location="Route 209, Hallowed Tower",
        level=25,
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement=(
            "Put the Odd Keystone in the Hallowed Tower, then talk to people in the Grand "
            "Underground thirty-two times"
        ),
    ),
    RecordedGift(
        species="uxie",
        location="Lake Acuity",
        level=50,
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement="Once Team Galactic is beaten and the cover legendary has been faced",
    ),
    RecordedGift(
        species="mesprit",
        location="Lake Verity",
        level=50,
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement=(
            "Once Team Galactic is beaten and the cover legendary has been faced. Talking to it "
            "sets it roaming Sinnoh"
        ),
    ),
    RecordedGift(
        species="azelf",
        location="Lake Valor",
        level=50,
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement="Once Team Galactic is beaten and the cover legendary has been faced",
    ),
    RecordedGift(
        species="rotom",
        location="Old Chateau",
        level=15,
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement="At night, after the National Pokedex opens",
    ),
    RecordedGift(
        species="heatran",
        location="Stark Mountain",
        level=70,
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement="After Buck has put the Magma Stone back",
    ),
    RecordedGift(
        species="regigigas",
        location="Snowpoint Temple",
        level=70,
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement=(
            "With Regirock, Regice and Registeel in the party. The temple stays shut until the "
            "National Pokedex opens"
        ),
    ),
    RecordedGift(
        species="giratina",
        location="Turnback Cave",
        level=70,
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement="In the last room, after the National Pokedex opens",
    ),
    RecordedGift(
        species="cresselia",
        location="Fullmoon Island",
        level=50,
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement=(
            "After the National Pokedex opens, once the sailor in Canalave City asks for a Lunar "
            "Feather. Talking to it sets it roaming Sinnoh"
        ),
    ),
    # --- and the three a player cannot reach any more ------------------------------------------
    #
    # Left in rather than left out, and marked by their requirement rather than by a flag: the
    # island and the paradise are in the game and the Pokemon is standing on it, and what a
    # player cannot get is the item that opens the way. Step 7 is where an entry nothing can
    # produce gets its sentence, and these three will be its clearest cases - two distributions
    # that closed in 2022, and one that is not a distribution at all.
    RecordedGift(
        species="shaymin",
        location="Flower Paradise",
        level=30,
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement=(
            "With Oak's Letter, which was handed out over the internet between 27 February and "
            "27 March 2022 and has not been since"
        ),
    ),
    RecordedGift(
        species="darkrai",
        location="Newmoon Island",
        level=50,
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement=(
            "With the Member Card, which was handed out over the internet between 1 and 30 "
            "April 2022 and has not been since"
        ),
    ),
    RecordedGift(
        species="arceus",
        location="Hall of Origin",
        level=80,
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement=(
            "With the Azure Flute, which appears in the player's room in Twinleaf Town from "
            "version 1.3.0 if the console has Legends: Arceus save data with every main mission "
            "finished"
        ),
    ),
)

#: The room in Ramanas Park each slate opens, and what walks out of it.
#:
#: **The remake's own answer to a question Diamond never asked**: a Generation 4 cartridge got
#: the older legendaries by trading with a Generation 3 cartridge through Pal Park, and a Switch
#: game has no cartridge slot to trade with. So these two grow a building instead, and eighteen
#: legendaries that used to be somebody else's become theirs.
#:
#: Every one of them needs the National Pokedex, and the slates are dug out of the Grand
#: Underground. The versions split the way a version pair always splits: Brilliant Diamond gets
#: Johto's three and Ho-Oh, Shining Pearl gets Kanto's three and Lugia, and the rest are both.
RAMANAS: tuple[tuple[str, str, str | None], ...] = (
    ("articuno", "Kanto Room", "shining-pearl"),
    ("zapdos", "Kanto Room", "shining-pearl"),
    ("moltres", "Kanto Room", "shining-pearl"),
    ("raikou", "Johto Room", "brilliant-diamond"),
    ("entei", "Johto Room", "brilliant-diamond"),
    ("suicune", "Johto Room", "brilliant-diamond"),
    ("lugia", "Squall Room", "shining-pearl"),
    ("ho-oh", "Rainbow Room", "brilliant-diamond"),
    ("mewtwo", "Genome Room", None),
    ("regirock", "Discovery Room", None),
    ("regice", "Discovery Room", None),
    ("registeel", "Discovery Room", None),
    ("latias", "Soul Room", None),
    ("latios", "Soul Room", None),
    ("kyogre", "Oceanic Room", None),
    ("groudon", "Tectonic Room", None),
    ("rayquaza", "Stratospheric Room", None),
)

#: What each half alone hands over or leaves standing.
#:
#: The cover legendary, the fossil its Underground digs up, and its share of Ramanas Park. The
#: Distortion Slate is deliberately not here: it calls up a second Giratina, and Turnback Cave
#: already has the first - a living dex counts what a box can hold, not how many ways there are
#: to fill the same page.
SPLIT_GIFTS: dict[str, tuple[RecordedGift, ...]] = {
    "brilliant-diamond": (
        RecordedGift(
            species="dialga",
            location="Spear Pillar",
            level=47,
            kind=GiftKind.STATIC_ENCOUNTER,
            requirement="Once Cyrus is beaten at the Spear Pillar",
        ),
        RecordedGift(
            species="cranidos",
            location="Oreburgh City, Oreburgh Mining Museum",
            kind=GiftKind.FOSSIL,
            requirement=(
                "Skull Fossil, dug up in the Grand Underground. Shining Pearl digs up the Armor "
                "Fossil instead"
            ),
        ),
    ),
    "shining-pearl": (
        RecordedGift(
            species="palkia",
            location="Spear Pillar",
            level=47,
            kind=GiftKind.STATIC_ENCOUNTER,
            requirement="Once Cyrus is beaten at the Spear Pillar",
        ),
        RecordedGift(
            species="shieldon",
            location="Oreburgh City, Oreburgh Mining Museum",
            kind=GiftKind.FOSSIL,
            requirement=(
                "Armor Fossil, dug up in the Grand Underground. Brilliant Diamond digs up the "
                "Skull Fossil instead"
            ),
        ),
    ),
}


#: Where Sinnoh's day care is, which fifteen years and a console did not move.
DAY_CARE = sinnoh.DAY_CARE

#: The four traders, which are Diamond and Pearl's four traders.
#:
#: Checked rather than assumed: the wiki's in-game trade table for this pair is Hilary's Abra
#: for a Machop, Norton's Chatot for a Buizel, Mindy's Haunter for a Medicham and Meister's
#: foreign Magikarp for a Finneon - the same people in the same rooms wanting the same things.
#: So the table lives in :mod:`sinnoh` and is asked for here.
TRADES = sinnoh.TRADES

#: The version group whose evolution methods these games use, which is **not their own**.
#:
#: The one place where treating a remake as a Generation 8 game gives the wrong answer, and it
#: was measured rather than argued: asked as ``brilliant-diamond-shining-pearl`` the reader
#: returns the same 246 evolutions but seven of them by the wrong route - the newest way wins,
#: so Eevee would take an Ice Stone and a Leaf Stone, Magneton and Nosepass a Thunder Stone,
#: Feebas a Prism Scale. **None of those items is in these games.** Bulbapedia says it plainly:
#: the Ice Stone is not obtainable in Brilliant Diamond and Shining Pearl, so Eevee can only
#: evolve into Glaceon with the Ice Rock.
#:
#: So the remake keeps its original's ways, and the rule ids it produces are Diamond's - which
#: is the honest outcome as well as the convenient one: a Magnezone made at Mt. Coronet in 2007
#: and one made there in 2021 were made the same way.
#:
#: Nothing is lost by looking backwards. Both readings give 246 records with the same targets;
#: no evolution arrived after Diamond and Pearl for a species this dex holds.
EVOLUTION_GROUP = sinnoh.PAIR_VERSION_GROUP


def handed_over(game_id: str) -> tuple[RecordedGift, ...]:
    """Everything one half hands over, hatches or leaves standing, its own share included."""
    return (
        *GIFTS,
        *SPLIT_GIFTS[game_id],
        *(
            RecordedGift(
                species=species,
                location=f"Ramanas Park, {room}",
                level=70,
                kind=GiftKind.STATIC_ENCOUNTER,
                requirement=(
                    f"Put the slate the {room} takes into its pedestal, after the National "
                    "Pokedex opens. The slates are dug out of the Grand Underground"
                ),
            )
            for species, room, only_on in RAMANAS
            if only_on in (None, game_id)
        ),
    )


def acquisition_methods(
    context: BuildContext,
    *,
    game_id: str,
    entries: Sequence[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get anything in one of these two: caught, handed over, traded for, evolved.

    Steps 3 to 5. There is no ``wild_encounters`` call beside this one and no ``gift_encounters``
    either: PokeAPI carries nothing at all for these games, so unlike Hoenn - where the wiki
    filled a hole in the source - here the wiki *is* the source, and step 4 is a table written
    out by hand rather than sentences added to rows somebody else supplied.

    The species asked about are the whole living dex rather than the game's own Pokedex: the
    Grand Underground alone holds dozens of species that are nowhere in Sinnoh's 151, and asking
    only about the regional list would leave most of what a player can catch here unrecorded.
    """
    species = context.living_dex(through=NATIONAL_DEX_THROUGH, entries=entries)

    found = [
        *table_encounters(
            context.require_wiki(),
            game_id=game_id,
            column=COLUMNS[game_id],
            pair=("BD", "SP"),
            pages=PAGES,
            methods=METHODS,
            requirements=METHOD_REQUIREMENTS,
            conditions=CONDITIONS,
            aliases=SPECIES_ALIASES,
            species=set(species),
            refresh=context.refresh,
        ),
        *recorded_gifts(
            game_id=game_id,
            gifts=handed_over(game_id),
            species=species,
            citation=READ_ON(EVENT_PAGE),
        ),
        *trade_encounters(
            game_id=game_id,
            trades=TRADES,
            citation=READ_ON("In-game_trade"),
        ),
        *evolution_encounters(
            context.require_api(),
            game_id=game_id,
            version_group=EVOLUTION_GROUP,
            species=species,
            forms=context.forms_here(),
            all_forms=context.forms,
            refresh=context.refresh,
        ),
        *form_change_encounters(
            game_id=game_id,
            forms=context.forms_here(),
            changes=FORM_CHANGES,
            citation=READ_ON(FORMS_PAGE),
        ),
    ]

    # Last, and worked out from what the steps above came to rather than from a table: a day
    # care can only be asked for what nothing else here produces.
    api = context.require_api()

    return [
        *found,
        *breeding_encounters(
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
                retrieved_on=api.newest_read_under(f"{BASE_URL}/evolution-chain"),
            ),
        ),
    ]


def trade_edges(game_id: str) -> list[TransferEdge]:
    """The one cable these games have, which runs to the other half of the pair.

    Local wireless, the internet, the Union Room and a Link Code are four ways of doing one
    thing and the graph holds it once. What this edge does not say is that HOME will move a
    Pokemon between two Brilliant Diamond save files on the same console, profiles included -
    Bulbapedia states that plainly, and it is a route from a game to itself, which a graph of
    games has nowhere to draw.
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

    HOME arrived on 18 May 2022, six months after the games, in its version 2.0.0 - so for half
    a year these were the only core series games on the console with no way out at all. The
    dataset has no field for that and should not grow one: a route that exists now is a route,
    and when it opened is the release date of a service rather than a property of the games.

    :func:`home.home_edges`, the ordinary pair, and the withdrawal's
    :class:`PresentInTargetDexFilter` happens to be exactly right here for a reason worth
    writing down. Bulbapedia: "Only Pokemon that exist in the game data (i.e., those from the
    first four generations of games, excluding regional forms) can be transferred to Pokemon
    Brilliant Diamond and Shining Pearl." That is the filter's own sentence in the wiki's words
    - the target's list decides - and it means step 2 and step 8 are what make this edge honest
    rather than anything written here. An Alolan Vulpix is a Generation 7 form of a Generation 1
    species, and it may not come in.

    **Three limits the filter cannot express, checked rather than assumed**, and none of them
    changes what a living dex here can hold:

    * **Spinda cannot be transferred to or from these games at all**, which is the only species
      in the dataset with that said about it. It is still a Sinnoh-era entry and still catchable
      in the game, so it is an entry a player fills here rather than one they carry in.
    * **A Nincada from another game cannot be deposited into these**, one way only, and the same
      answer applies: what matters to a living dex is whether the game can produce one.
    * **Certain Legendary Pokemon may be moved out of a save file only once per save file.** A
      limit on how often a route may be used is not a limit on where it goes, and this dataset
      records the second.

    Whether those three stay a docstring or become something the graph carries is step 3's to
    say, because step 3 is what finds out if the game produces each of them.
    """
    return [*trade_edges(game_id), *home.home_edges(game_id)]
