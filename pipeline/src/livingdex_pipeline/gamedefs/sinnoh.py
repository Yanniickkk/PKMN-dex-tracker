"""What the Sinnoh cartridges have in common.

Diamond and Pearl are a version pair; Platinum is their third version, the way Emerald is Ruby
and Sapphire's. The shared half lives here and each game brings only what is true about itself.

At step 4 this file holds the region, the pair's Pokedex, every wild slot in it and
everything the games hand over or leave standing in one spot - what their NPCs will swap for
and what evolves into what arrive with the step that gathers them. What these three share with
HeartGold and SoulSilver rather than with each other is in :mod:`ds`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from ..breeding import EggFrom, breeding_encounters
from ..evolutions import evolution_encounters
from ..formchanges import FormChange, form_change_encounters, spread
from ..games import BuildContext
from ..gifts import GiftDetail, gift_encounters
from ..models import AcquisitionMethod, DexEntry, DexTarget, Game, GiftKind, TransferEdge
from ..places import LocationNames
from ..sources import ReadByHand
from ..trades import InGameTrade, trade_encounters
from ..wild import wild_encounters
from . import ds, exclusives

GENERATION = ds.GENERATION

REGION = "Sinnoh"

#: Where an egg is left and collected, in all three.
DAY_CARE = "Solaceon Town, Pokemon Day Care"

#: The National Dex opens after the Elite Four here as well, and stops at Arceus.
NATIONAL_DEX_THROUGH = ds.NATIONAL_DEX_THROUGH

#: PokeAPI's name for the 151-entry Sinnoh dex, the one Diamond and Pearl show.
#:
#: Not :data:`EXTENDED_DEX`, which is the 210-entry dex Platinum shows: the third version added
#: 59 species to the regional list, so unlike the Hoenn three the Sinnoh three do *not* share one
#: dex. Platinum names its own, which is why this one says which of the two lists it is.
#:
#: Named for the list rather than for a pair, because two pairs show it. Brilliant Diamond and
#: Shining Pearl went back to it over Platinum's - Bulbapedia calls that "the Sinnoh Pokedex's
#: return to the original Diamond and Pearl numbering" - so four games in two generations put
#: Turtwig at #001 and Manaphy at #151.
ORIGINAL_DEX = "original-sinnoh"

#: PokeAPI's name for the 210-entry Sinnoh dex, the one Platinum shows.
#:
#: The pair's 151 with 59 appended, and the first 151 keep their numbers exactly - Turtwig is
#: still #001 and Manaphy still #151, with Rotom at #152 and Giratina last at #210. So the two
#: lists are not rivals: a player moving from Diamond to Platinum finds the dex they know with
#: more at the end of it.
#:
#: What the 59 are is mostly what Diamond and Pearl held back until the National Dex opened -
#: Eevee's whole family, Togepi's, Rotom, Scyther, Porygon - and Platinum simply counts them
#: as Sinnoh's.
EXTENDED_DEX = "extended-sinnoh"

#: What PokeAPI calls the pair when it says which version group an evolution started in. The
#: two halves are one group, the way Ruby and Sapphire are - and it is the group that brought
#: most of Sinnoh's own evolutions, from Roserade's Shiny Stone to Magnezone's magnetic field.
PAIR_VERSION_GROUP = "diamond-pearl"

#: Where the pair's own battle sprites live in the sprite repository. One sheet for the two of
#: them, the way FireRed and LeafGreen share one.
#:
#: Named for the pair rather than the region, because Platinum redrew them: the third version
#: has a sheet of its own, and a Sinnoh player sees different sprites depending on which of the
#: three is in the slot. The National Dex reaches 493 here, and anything above what this sheet
#: covers falls back to the shared artwork.
PAIR_SPRITE_SET = "generation-iv/diamond-pearl"


def cartridge(
    *,
    game_id: str,
    title: str,
    version: str,
    released: date,
    sprite_set: str | None = None,
    pair_partner: str | None = None,
) -> Game:
    """One Sinnoh cartridge: a Generation 4 cartridge that happens to be set here."""
    return ds.cartridge(
        game_id=game_id,
        title=title,
        version=version,
        region=REGION,
        released=released,
        sprite_set=sprite_set,
        pair_partner=pair_partner,
    )


def edges(game_id: str) -> list[TransferEdge]:
    """Every route this cartridge brings: trades with its own generation, Pal Park from before."""
    return ds.edges(game_id)


def original_dex_entries(
    context: BuildContext,
    *,
    game_id: str,
    unobtainable: Mapping[str, str] | None = None,
) -> list[DexEntry]:
    """The Sinnoh dex as Diamond and Pearl number it: Turtwig #001 to Manaphy #151.

    Four games rather than two, which is why this is named for the list. The Switch remakes show
    the same 151 in the same order - they went back to this numbering rather than taking
    Platinum's 210 - so :mod:`bdsp` asks for it here instead of holding a copy.

    This is the game's own Pokedex, not the list a living dex in it is aiming at. That list is
    the National Dex, which the entity already says it reaches 493 of.

    Sinnoh is the first region in this dataset with real form questions in its own dex. Burmy
    and Wormadam wear three cloaks, and Wormadam's change its typing, which makes them forms
    that a living dex has to count separately; Shellos and Gastrodon come in two colours that
    change nothing but their looks. Both wait for the shared forms table, which is still empty,
    the way Deoxys does in Hoenn. Rotom's appliances are not a question here at all: those
    arrived with Platinum.
    """
    return _dex_entries(context, game_id=game_id, dex=ORIGINAL_DEX, unobtainable=unobtainable)


def extended_dex_entries(
    context: BuildContext,
    *,
    game_id: str,
    unobtainable: Mapping[str, str] | None = None,
) -> list[DexEntry]:
    """The Sinnoh dex as Platinum numbers it: Turtwig #001 to Giratina #210.

    The pair's list is the first 151 of this one, numbers and all, so a Diamond player coming
    here recognises everything and finds 59 more at the end. Which is why the two have separate
    names rather than one function with a flag: they are two lists a game shows, and the game
    says which of them it is.

    Platinum brings two form questions of its own on top of the pair's. Rotom's five appliances
    are new here, and they change its second type each time - a living dex counts those. So is
    Giratina's Origin Forme, which the Distortion World hands over and the Griseous Orb keeps.
    Both wait for the shared forms table, which is still empty, exactly as Burmy's cloaks and
    Shellos's colours do.
    """
    return _dex_entries(context, game_id=game_id, dex=EXTENDED_DEX, unobtainable=unobtainable)


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


#: What only the game knows about each thing it hands over or leaves standing in one spot.
#:
#: PokeAPI carries the method, the place and the level. It does not carry who hands it over,
#: and it calls a starter, a fossil and an egg from a stranger by the same word - `gift`. The
#: conditions it does carry are two bare facts where a player wants one sentence, so the ones
#: that need a sentence get one here.
#:
#: One table for the pair: both halves hand over the same things in the same places. The two
#: they disagree about are the fossil and the cover legendary, and those are :data:`SPLIT_GIFTS`.
PAIR_GIFTS: dict[str, GiftDetail] = {
    "turtwig": GiftDetail(
        kind=GiftKind.STARTER,
        npc="Professor Rowan",
        requirement="Pick one of the three from the briefcase; the other two take a trade",
    ),
    "chimchar": GiftDetail(
        kind=GiftKind.STARTER,
        npc="Professor Rowan",
        requirement="Pick one of the three from the briefcase; the other two take a trade",
    ),
    "piplup": GiftDetail(
        kind=GiftKind.STARTER,
        npc="Professor Rowan",
        requirement="Pick one of the three from the briefcase; the other two take a trade",
    ),
    "happiny": GiftDetail(kind=GiftKind.EGG, npc="A hiker in the Hearthome City gate"),
    "riolu": GiftDetail(
        kind=GiftKind.EGG,
        npc="Riley",
        requirement="Given on Iron Island, once Team Galactic is beaten there",
    ),
    # A balloon that turns up at one building on one day of the week. PokeAPI carries both
    # halves of that as conditions; a player wants them in one sentence.
    "drifloon": GiftDetail(
        requirement="On a Friday, once Team Galactic is beaten at the Valley Windworks",
    ),
    "spiritomb": GiftDetail(
        requirement=(
            "An Odd Keystone in the Hallowed Tower, after talking to 32 people in the Underground"
        ),
    ),
    # The three that exist once. Worth saying for a living dex: a legendary that faints or is
    # run from does not come back in these games.
    "uxie": GiftDetail(requirement="Only one in the game"),
    "azelf": GiftDetail(requirement="Only one in the game"),
}

#: The two gifts the halves disagree about, by version.
#:
#: The cover legendary is the obvious one. The fossil is the one PokeAPI gets wrong: it files
#: both under both halves, and Bulbapedia is clear that only Diamond's Underground holds a Skull
#: Fossil and only Pearl's an Armor Fossil. :data:`NOT_A_GIFT` takes the other one back out.
SPLIT_GIFTS: dict[str, dict[str, GiftDetail]] = {
    "diamond": {
        "cranidos": GiftDetail(
            kind=GiftKind.FOSSIL,
            npc="A scientist in the Oreburgh Mining Museum",
            requirement="Skull Fossil, dug up in the Underground",
        ),
        "dialga": GiftDetail(requirement="Only one in the game"),
    },
    "pearl": {
        "shieldon": GiftDetail(
            kind=GiftKind.FOSSIL,
            npc="A scientist in the Oreburgh Mining Museum",
            requirement="Armor Fossil, dug up in the Underground",
        ),
        "palkia": GiftDetail(requirement="Only one in the game"),
    },
}

#: The fossil the other half digs up, and why this one does not.
#:
#: Not a tidy-up: PokeAPI says both halves revive both fossils, and that is a disagreement with
#: the wiki rather than noise. Saying so out loud is what keeps the next reader from "fixing"
#: it back.
NOT_A_GIFT: dict[str, dict[str, str]] = {
    "diamond": {
        "shieldon": "the Armor Fossil is only in Pearl's Underground; PokeAPI lists it for both",
    },
    "pearl": {
        "cranidos": "the Skull Fossil is only in Diamond's Underground; PokeAPI lists it for both",
    },
}


def only_on(partner: str, event: str | None = None) -> str:
    """Why an entry in this dex is not in this cartridge, when the other half has it."""
    return ds.only_on(partner, event)


def fossil_only_on(partner: str, fossil: str, event: str | None = None) -> str:
    """Why the fossil Pokemon of the other half is not in this one.

    The sentence is :func:`exclusives.fossil_only_on`'s, with this generation filled in. It was
    written here about the Underground's two and moved out when Alola's shop sold four.
    """
    return exclusives.fossil_only_on(partner, fossil, generation=GENERATION, event=event)


#: What step 7 found about Manaphy for the pair: nine distributions between 2006 and 2011.
#:
#: The only entry of the five they cannot produce that any event ever covered - and it was
#: covered nine times over, on three continents. Named rather than counted for the two a reader
#: is most likely to recognise; the rest were PalCity, the Nintendo World Store, E for All, JB
#: Hi-Fi, Nintendo of Korea and the Summer Nintendo Zone.
PAIR_MANAPHY_EVENT = (
    "nine distributions between 2006 and 2011 handed one out as well, from the World Hobby Fair "
    'in Japan to the Toys "R" Us Manaphy in the United States'
)

#: And what it found for Platinum, which is not the same thing.
#:
#: Seven of those nine had come and gone before Platinum was released, so their Manaphy could
#: never reach it. Only the last two list Pt among their games. Worth splitting rather than
#: sharing the pair's sentence, which told a Platinum player to have been at a Toys "R" Us in
#: 2007 for a game that did not exist until 2008.
THIRD_MANAPHY_EVENT = (
    "two later distributions reached this game as well: the Summer Nintendo Zone Manaphy over "
    "Japanese Wi-Fi in 2010, and the Pokemon Love Manaphy in South Korea in 2011"
)

#: Why nothing in Sinnoh produces a Manaphy.
#:
#: Its egg is a reward in Pokemon Ranger, a different game on the same handheld, and it is sent
#: across rather than found. The events that also handed one out differ per game, so each brings
#: its own.
MANAPHY_REASON = (
    "Pokemon Ranger only: the egg is a reward in that game and is sent across to this one"
)


def manaphy_reason(event: str | None) -> str:
    """Why this cartridge has no Manaphy, and which distributions ever reached it."""
    return exclusives.with_event(MANAPHY_REASON, event)


#: The four NPCs who will swap something, and what each one wants.
#:
#: No API carries these. The names are the original trainers the games record on what they hand
#: over, which is how a player can tell a traded Pokemon from a caught one.
#:
#: The one table all three cartridges share, which is why it is not named for the pair. Platinum
#: moved the starters, swapped where Porygon comes from and changed the terms on both cover
#: legendaries, and then left these four standing exactly where they were - same NPCs, same
#: houses, same asking price. Bulbapedia files them under one heading for that reason.
#:
#: The Haunter is worth knowing about and there is no field that says it: it is handed over
#: holding an Everstone, so the trade that would normally finish a Gengar does not. Gengar is
#: still only in the Old Chateau, and only in dual-slot mode.
TRADES = (
    InGameTrade(gets="abra", wants="machop", location="Oreburgh City", npc="Hilary"),
    InGameTrade(
        gets="chatot",
        wants="buizel",
        location="Eterna City, Eterna Condominiums",
        npc="Norton",
    ),
    InGameTrade(gets="haunter", wants="medicham", location="Snowpoint City", npc="Mindy"),
    InGameTrade(gets="magikarp", wants="finneon", location="Route 226", npc="Meister"),
)


def gifts(version: str) -> dict[str, GiftDetail]:
    """The gift table as one half of the pair sees it."""
    return {**PAIR_GIFTS, **SPLIT_GIFTS[version]}


#: How each of Sinnoh's forms is come by, in the two games that came first.
#:
#: Four families and four different kinds of answer, and only one of them is something a player
#: chooses. A Burmy's cloak is where it last fought, a Wormadam's is what its Burmy wore, a
#: Shellos's is which coast it lives on, and an Unown's is fixed before you ever see it. Sinnoh
#: is where forms stop being a curiosity and start being a thing to keep track of - it has more
#: of them than the three generations before it put together.
PAIR_FORM_CHANGES: dict[str, FormChange] = {
    # The meteorites a Deoxys is changed at, which Generation 4 is the first to have: before
    # these, the cartridge decided its forme and nothing could undo it.
    **spread(
        FormChange(
            requirement="Touch one of the meteorites there; they cycle through all four formes",
            where="Veilstone City",
        ),
        "deoxys-attack",
        "deoxys-defense",
        "deoxys-speed",
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
    **spread(
        FormChange(
            requirement=(
                "Which coast it lives on decides it: the West Sea is west of Mt. Coronet and "
                "the East Sea east of it, and a Shellos does not change shore"
            )
        ),
        "shellos-east",
        "gastrodon-east",
    ),
    **spread(
        FormChange(
            requirement=(
                "Its letter is fixed before you meet it; the rooms of the Solaceon Ruins hold "
                "different sets of them"
            ),
            where="Solaceon Ruins",
        ),
        "unown-b",
        "unown-c",
        "unown-d",
        "unown-e",
        "unown-f",
        "unown-g",
        "unown-h",
        "unown-i",
        "unown-j",
        "unown-k",
        "unown-l",
        "unown-m",
        "unown-n",
        "unown-o",
        "unown-p",
        "unown-q",
        "unown-r",
        "unown-s",
        "unown-t",
        "unown-u",
        "unown-v",
        "unown-w",
        "unown-x",
        "unown-y",
        "unown-z",
        "unown-exclamation",
        "unown-question",
    ),
}

#: And the three the third version added, which are the first forms in the series a player makes
#: on purpose.
#:
#: Rotom's appliances, the Griseous Orb and the Gracidea all arrive in Platinum, and all three
#: are an item or a room rather than an accident of where something was standing. Every later
#: generation keeps them: the boxes move to a shop basement in Unova, and the Orb turns up in a
#: different place in every pair since.
PLATINUM_FORM_CHANGES: dict[str, FormChange] = {
    **PAIR_FORM_CHANGES,
    **spread(
        FormChange(
            requirement=(
                "Let it possess one of the appliances in Rotom's Room, which the Secret Key opens"
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
            "In the Distortion World it is always in this form; anywhere else, while it holds "
            "the Griseous Orb that Turnback Cave leads to"
        )
    ),
    "shaymin-sky": FormChange(
        requirement=(
            "Use the Gracidea on it in daylight; it goes back to Land Forme at night and while "
            "it is frozen"
        )
    ),
}


#: The day a person read each page the tables below were typed from.
#:
#: A fetched citation takes its date from the cache entry the answer came out of. These have no
#: fetch to take one from, so the day is written down beside the table that was read - which is
#: the only place it can come from once the reading is over.
READ_ON = ReadByHand(
    {
        "Baby_Pok%C3%A9mon": date(2026, 9, 22),
        "In-game_trade": date(2026, 9, 22),
        "List_of_Pok%C3%A9mon_with_form_differences": date(2026, 9, 23),
    }
)


def acquisition_methods(
    context: BuildContext,
    *,
    game_id: str,
    version: str,
    entries: Sequence[DexEntry],
    gifts: Mapping[str, GiftDetail] | None = None,
    excluded: Mapping[str, str] | None = None,
    version_group: str | None = None,
    trades: Sequence[InGameTrade] = (),
    eggs: Mapping[str, EggFrom] | None = None,
    form_changes: Mapping[str, FormChange] | None = None,
) -> list[AcquisitionMethod]:
    """Every way to get something in one Sinnoh cartridge.

    The steps are the same for all three - what the grass, the water, the rods and the honey
    trees hold, what is handed over or left standing in one spot, what an NPC will swap for,
    what evolves into what - but the tables behind them belong to the game. The pair shares
    every one of them; Platinum shares none, down to which version group its evolutions are
    stamped with. So the machinery is written here once and each game brings what it knows.

    A table left out is a step that has not been gathered yet, not a game with nothing to
    declare. Platinum arrives with its encounters first, the way the pair did, and picks the
    rest up as the steps that gather them run. Handing this an empty gift table instead would
    print PokeAPI's bare rows and call it step 4.

    The wild and gift steps read the same encounter tables and walk into the same places, so
    they share one place lookup: Route 205 is named once however many times it comes up, the
    way it is in Hoenn and Kanto.
    """
    api = context.require_api()
    # Every species the living dex here asks for, which is not the game's own Pokedex. Those
    # are two different lists, and asking only about the second is what left every entry
    # outside the regional dex with nothing recorded against it - in games that produce plenty
    # of them.
    species = context.living_dex(through=NATIONAL_DEX_THROUGH, entries=entries)
    places = LocationNames(api, refresh=context.refresh)

    found: list[AcquisitionMethod] = [
        *wild_encounters(
            api,
            game_id=game_id,
            version=version,
            species=species,
            forms=context.forms_here(),
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
                details=gifts,
                excluded=excluded,
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
                forms=context.forms_here(),
                all_forms=context.forms,
                refresh=context.refresh,
            )
        )

    if eggs:
        found.extend(
            breeding_encounters(
                game_id=game_id,
                day_care=DAY_CARE,
                eggs=eggs,
                citation=READ_ON("Baby_Pok%C3%A9mon"),
            )
        )

    found.extend(
        trade_encounters(
            game_id=game_id,
            trades=trades,
            citation=READ_ON("In-game_trade"),
        )
    )

    found.extend(
        form_change_encounters(
            game_id=game_id,
            forms=context.forms_here(),
            changes=form_changes or {},
            citation=READ_ON("List_of_Pok%C3%A9mon_with_form_differences"),
        )
    )

    return found


def pair_acquisition_methods(
    context: BuildContext,
    *,
    game_id: str,
    version: str,
    entries: Sequence[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something in one of the pair, with the pair's tables filled in.

    The halves differ by one word - which version PokeAPI is asked about - so one function
    answers for both and each game brings its own version name. Two copies of this is how one
    of them gets edited and the other does not.
    """
    return acquisition_methods(
        context,
        game_id=game_id,
        version=version,
        entries=entries,
        gifts=gifts(version),
        excluded=NOT_A_GIFT[version],
        version_group=PAIR_VERSION_GROUP,
        trades=TRADES,
        form_changes=PAIR_FORM_CHANGES,
    )


# The pair passes no eggs, and that absence is a fact rather than a gap. Generation 4 brought
# most of the baby Pokemon there are, and then put them in Sinnoh's own grass: Cleffa and
# Chingling in Mt. Coronet, Pichu and Mime Jr. in the Trophy Garden, Azurill in the Great Marsh,
# Budew in Eterna Forest, Mantyke on the water, Munchlax on the honey trees. Happiny and Riolu
# are handed over as eggs. Every baby in the pair's 151 entries has a source that is not an egg
# the player has to make, which is why Ruby and Sapphire hatch three and these two hatch none.
#
# Platinum is the exception, and only because its dex is longer: it counts Elekid and Magby as
# Sinnoh's, and neither one is anywhere in Sinnoh. Its table is in its own file.
