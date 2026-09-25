"""What the Kanto games have in common, whichever generation they are from.

Two sets of games are set here, as in :mod:`johto`. Red and Blue are Generation 1 and a version
pair; FireRed and LeafGreen are Generation 3 and the same pair again, remade. So this module is
about the place and not about the hardware, and the split is drawn twice over:

* What is true of Kanto - its Pokedex, what walks in its grass, who trades what in which town -
  lives here, and a table that belongs to one pair rather than to the region says so in its
  name.
* What is true of the hardware and the generation - which games trade with which, how far the
  National Dex reaches, whether there is a Time Capsule or a Pal Park - lives with the
  generation: :mod:`gb` for Red and Blue, :mod:`gba` for FireRed and LeafGreen.

The factories are named for the hardware for that reason. Nothing here should have to be edited
to add Yellow; something that does have to be edited is a fact about one pair that has been
written down as a fact about the place.

The Sevii Islands are part of FireRed and LeafGreen and of no other game, but they are an area
within them rather than a region of their own, so they are named where they are used - in a
location - and not here.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from ..evolutions import evolution_encounters
from ..formchanges import FormChange, form_change_encounters, spread
from ..games import BuildContext
from ..gifts import GiftDetail, gift_encounters
from ..models import AcquisitionMethod, DexEntry, DexTarget, Game, GiftKind, TransferEdge
from ..places import LocationNames
from ..sources import ReadByHand
from ..trades import InGameTrade, trade_encounters
from ..wild import wild_encounters
from . import exclusives, gb, gba

#: Kanto proper.
REGION = "Kanto"

#: PokeAPI's name for the 151-entry Kanto dex, which every game set here shows.
#:
#: One dex for both pairs, and PokeAPI says so itself: the resource lists ``red-blue`` and
#: ``firered-leafgreen`` among the version groups it belongs to. FireRed and LeafGreen show the
#: list Red and Blue did, in the same order, which is the opposite of what Johto did when it
#: came back - there the remake renumbered 150 entries.
#:
#: For Red and Blue it is the whole dex; for FireRed and LeafGreen it is the game's own list and
#: the National Dex arrives after the Elite Four. Each entity says which of the two it has.
DEX = "kanto"

#: What PokeAPI calls the pair when it says which version group an evolution started in. The
#: two halves are one group, the way Ruby and Sapphire are.
PAIR_VERSION_GROUP = "firered-leafgreen"

#: Where the Generation 3 pair's own battle sprites live in the sprite repository. One sheet for
#: the two of them: FireRed and LeafGreen were drawn from the same set, which is why it is named
#: here and not in either game's file.
GBA_PAIR_SPRITE_SET = "generation-iii/firered-leafgreen"

#: And where Red and Blue's are. One sheet again, and the oldest in the dataset: 151 sprites
#: drawn for a screen with four shades on it.
#:
#: ``transparent`` is not a detail. Generation 1's default sheet is a 56x56 palette image with
#: no alpha channel at all, so every sprite arrives in a white box - which looked exactly like
#: a white box on a dark grid. The transparent set is the same drawings at 96x96 with the
#: background cut out, which is what every other generation's sheet already gives.
#:
#: The repository also keeps a ``gray`` set, which is those same sprites in the Game Boy's own
#: palette. This is the coloured version, for the reason the entity gives: what is in the
#: dataset is the 3DS release, and a 3DS shows these games in colour.
GB_PAIR_SPRITE_SET = "generation-i/red-blue/transparent"


def gb_release(
    *,
    game_id: str,
    title: str,
    version: str,
    released: date,
    pair_partner: str | None = None,
    sprite_set: str | None = None,
) -> Game:
    """One Kanto game on the Game Boy: a Generation 1 release that happens to be set here.

    Named for the hardware rather than called ``game`` outright, because Kanto has two pairs
    forty years of hardware apart and almost nothing either generation module fills in is true
    of the other. The region is the one argument both pass.

    ``pair_partner`` is optional here and required of the Generation 3 factory below, which is
    the difference between the two sets: Red and Blue have Yellow beside them, and FireRed and
    LeafGreen never had a third version.
    """
    return gb.release(
        game_id=game_id,
        title=title,
        version=version,
        region=REGION,
        released=released,
        sprite_set=sprite_set,
        pair_partner=pair_partner,
    )


def gb_edges(game_id: str) -> list[TransferEdge]:
    """Every route a Generation 1 release brings: its own trades, the Time Capsule, Bank."""
    return gb.edges(game_id)


def gb_only_on(partner: str, event: str | None = None) -> str:
    """Why an entry in this dex is not in this Generation 1 release, when the other half has it."""
    return gb.only_on(partner, event)


def gba_cartridge(
    *,
    game_id: str,
    title: str,
    version: str,
    released: date,
    pair_partner: str,
    sprite_set: str | None = None,
) -> Game:
    """One half of the Generation 3 pair.

    ``pair_partner`` is required rather than optional, unlike the Hoenn factory: there is no
    third version of FireRed and LeafGreen, so a cartridge here always has another half.
    """
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
    """What this cartridge can send and receive over a link cable: every other GBA cartridge."""
    return gba.link_trade_edges(game_id)


def gba_only_on(partner: str, event: str | None = None) -> str:
    """Why an entry in this dex is not in this cartridge, when the other half has it."""
    return gba.only_on(partner, event)


#: Never in either half of the Generation 3 pair, and in no other Generation 3 game but
#: Emerald's Faraway Island - which takes an Old Sea Map that was itself only ever handed out at
#: events.
#:
#: Step 7 named the three that reached these cartridges. There were dozens more in Generation 1;
#: those went onto a Game Boy cartridge and cannot reach a Game Boy Advance one.
GBA_MEW_REASON = (
    "Distribution event only: the Hadou Mew in Japan in 2005, the Mystery Mew in the United "
    "States in 2006, and the Aura Mew across Europe in 2007"
)

#: Never in Red or Blue either, and the distributions that reached *them* are not the famous
#: ones.
#:
#: This is where modelling the Virtual Console release rather than the cartridge pays: the Mews
#: of 1996 to 2000 - the Nintendo tours, the shopping centres, the Toys "R" Us queues - went
#: onto Game Boy cartridges, and a 3DS download is not one of those. Two later distributions
#: were for these releases, and Bulbapedia marks them as such.
GB_MEW_REASON = (
    "Distribution event only, and not the famous ones: the Mews handed out between 1996 and "
    "2000 went onto cartridges. Two events were for the Virtual Console releases, both in 2016 "
    "- the Game Freak Mew in Japan in the spring, and the Mew at Nintendo UK's Pokemon Festival "
    "that November"
)

#: The one American distribution that covers most of what these cartridges cannot produce: a
#: single day in 2004 on which shops handed out one of the other half's exclusives.
TRADE_AND_BATTLE_DAY = "the Pokemon Trade and Battle Day in the United States on 25 September 2004"

#: The Japanese campaign that did the same two years later. Not the Fifth Campaign, which is the
#: one the Hoenn cartridges name: the campaigns ran in different months and covered different
#: species, and it is the Third that reached FireRed and LeafGreen.
THIRD_CAMPAIGN = "a 2006 Japanese campaign (Gather More Pokemon! Third Campaign)"

#: A Japanese giveaway of eggs in the spring of 2004, a few weeks before these games reached
#: the West at all.
EGG_PRESENT = "the Egg Pokemon Present in Japan in 2004"

#: And its successor a year later, also Japanese.
POKEPARK_EGG = "the PokePark Egg in Japan in 2005"


def handed_out(*events: str) -> str:
    """One sentence naming every distribution that ever handed this species out."""
    return exclusives.handed_out(*events)


def dex_entries(
    context: BuildContext,
    *,
    game_id: str,
    unobtainable: Mapping[str, str] | None = None,
) -> list[DexEntry]:
    """The Kanto dex, Bulbasaur #001 to Mew #151, as every game set here numbers it.

    One function for four games, which is unusual and is the region's doing: FireRed and
    LeafGreen show the list Red and Blue did, in the same order. Johto's remake renumbered 150
    entries; Kanto's changed nothing.

    What the list *is* differs between the two pairs, and the entity is what says so. In Red and
    Blue it is the whole dex a living one aims at - there is no National Dex behind it. In
    FireRed and LeafGreen it is the game's own Pokedex and the National Dex arrives after the
    Elite Four, 386 entries deep.

    What differs between two halves of one pair is which entries their own grass never holds,
    and that is the ``unobtainable`` table each game brings.

    Kanto has no forms to decide about: every one of the 151 is a plain species in all four
    games. The regional forms these species later grew are Alolan and Galarian, which is
    Generation 7 and 8 and no business of any of them.
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
        for number, species in api.pokedex(DEX, refresh=context.refresh)
    ]


#: Which Deoxys each of the Generation 3 cartridges makes, which is not a choice anybody has.
#:
#: The one form in the series decided by the box the game came in. Deoxys is the same Pokemon in
#: all three and takes a different shape in each, and there is nothing to do about it - no item,
#: no place, no order of events. It is also why :data:`forms.ONLY_IN` exists: the source can say
#: which version *group* a form belongs to, and FireRed and LeafGreen are one group with two
#: answers between them.
DEOXYS_FORM = {"firered": "deoxys-attack", "leafgreen": "deoxys-defense", "emerald": "deoxys-speed"}

#: And Unown, which Kanto keeps in a corner of the Sevii Islands.
#:
#: Johto invented the letters and Kanto moved them: the same twenty-six plus the two this
#: generation added, in seven chambers instead of four puzzles.
GBA_UNOWN: dict[str, FormChange] = spread(
    FormChange(
        requirement=(
            "Its letter is fixed before you meet it; each of the seven chambers holds its own "
            "set, and the chambers open once the Ruin Valley writing has been read"
        ),
        where="Tanoby Ruins",
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
)


def gba_form_changes(version: str) -> dict[str, FormChange]:
    """What this cartridge can make: the letters, and whichever Deoxys it was built with."""
    return {
        **GBA_UNOWN,
        DEOXYS_FORM[version]: FormChange(
            requirement=(
                f"Deoxys takes this shape in {version.title()} and no other. Nothing in the game "
                "changes it; the cartridge decides"
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
    through: int | None,
    gifts: Mapping[str, GiftDetail] | None = None,
    version_group: str | None = None,
    trades: Sequence[InGameTrade] = (),
    form_changes: Mapping[str, FormChange] | None = None,
) -> list[AcquisitionMethod]:
    """Every way to get something in one Kanto game.

    ``through`` is how far this game's National Dex reaches, and it is an argument rather than a
    constant because the two pairs do not agree: FireRed reaches 386 and Red has no National Dex
    at all, so it asks for its own 151 and nothing else.

    A table left out is a step nobody has done yet rather than a game with nothing to declare.
    What is handed over, what an NPC will swap for and what evolves into what arrive with the
    steps that gather them; handing this an empty gift table instead would print PokeAPI's bare
    rows and call it step 4.

    The day care on Four Island is not here, and its absence is a fact rather than a gap. A
    Kanto dex is 151 entries and every baby Pokemon is Generation 2 or later, so nothing any of
    these games can hatch is anything this dex asks for. Ruby and Sapphire hatch three because
    their dex has three to hatch.

    The wild and gift steps read the same encounter tables and walk into the same places, so
    they share one place lookup: Route 4 is named once however many times it comes up.
    """
    api = context.require_api()
    # Every species the living dex here asks for. For FireRed that is far more than its own
    # Pokedex; for Red it is exactly its own Pokedex, because there is nothing else to want.
    species = context.living_dex(through=through, entries=entries)
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


def gba_pair_acquisition_methods(
    context: BuildContext,
    *,
    game_id: str,
    version: str,
    entries: Sequence[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something in FireRed or LeafGreen, with their tables filled in.

    The halves differ by one word - which version PokeAPI is asked about - so one function
    answers for both and each game brings its own version name. Two copies of this is how one
    of them gets edited and the other does not.
    """
    return acquisition_methods(
        context,
        game_id=game_id,
        version=version,
        entries=entries,
        through=gba.NATIONAL_DEX_THROUGH,
        gifts=gba_gifts(version),
        version_group=PAIR_VERSION_GROUP,
        trades=trades(version),
        form_changes=gba_form_changes(version),
    )


def gb_acquisition_methods(
    context: BuildContext,
    *,
    game_id: str,
    version: str,
    entries: Sequence[DexEntry],
    gifts: Mapping[str, GiftDetail] | None = None,
    version_group: str | None = None,
    trades: Sequence[InGameTrade] = (),
) -> list[AcquisitionMethod]:
    """Every way to get something in one Generation 1 release, whichever of the three it is.

    ``through`` is None rather than 151, and that is the generation rather than the game: a
    release with no National Dex asks for its own dex, which is the branch `living_dex` has
    always had and nothing had ever used.

    No eggs either, and not because nobody has looked: Generation 1's day care raises a Pokemon
    and nothing else. Breeding arrives with Generation 2, and so do the babies that would need
    it.

    The tables are arguments rather than constants because the three releases do not agree about
    them. Red and Blue share theirs down to the coin; Yellow hands over four different starters,
    trades different things and is its own version group, so it brings its own.
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
    )


def gb_pair_acquisition_methods(
    context: BuildContext,
    *,
    game_id: str,
    version: str,
    entries: Sequence[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something in Red or Blue, which is the same way in both but for grass."""
    return gb_acquisition_methods(
        context,
        game_id=game_id,
        version=version,
        entries=entries,
        gifts=GB_GIFTS,
        version_group=GB_PAIR_VERSION_GROUP,
        trades=GB_PAIR_TRADES,
    )


#: What only the game knows about each thing Kanto hands over or leaves standing in one spot.
#:
#: PokeAPI carries the method, the place and the level. It does not carry who hands it over or
#: what has to be true first, and it calls a starter, a fossil and a present from a stranger by
#: the same word - `gift` - which is why the kinds are corrected here.
#:
#: One table for four of the five games. Kanto's gifts are the part the remake left alone: the
#: same scientist on Cinnabar reviving the same fossil, the same choice of one Hitmon in the
#: same dojo, the same man in the Celadon Mansion with the same Eevee. What a pair or a single
#: release adds is in its own table, here or in its own file.
#:
#: The three in Oak's lab are the exception, and Yellow is why: it overrides all three, because
#: there they are not starters at all and no two of them come from the same person.
SHARED_GIFTS: dict[str, GiftDetail] = {
    "bulbasaur": GiftDetail(
        kind=GiftKind.STARTER,
        npc="Professor Oak",
        requirement="Pick one of the three; the other two take a trade",
    ),
    "charmander": GiftDetail(
        kind=GiftKind.STARTER,
        npc="Professor Oak",
        requirement="Pick one of the three; the other two take a trade",
    ),
    "squirtle": GiftDetail(
        kind=GiftKind.STARTER,
        npc="Professor Oak",
        requirement="Pick one of the three; the other two take a trade",
    ),
    # Mt. Moon offers the Dome Fossil or the Helix Fossil and keeps the one left behind. Unlike
    # Emerald, which gives the second one back in the Desert Underpass, nothing here ever does:
    # Bulbapedia lists Mt. Moon as the only way to either, and it is a choice between them.
    "omanyte": GiftDetail(
        kind=GiftKind.FOSSIL,
        npc="Cinnabar Island Pokemon Lab scientist",
        requirement="Helix Fossil from Mt. Moon; the other fossil is lost for good",
    ),
    "kabuto": GiftDetail(
        kind=GiftKind.FOSSIL,
        npc="Cinnabar Island Pokemon Lab scientist",
        requirement="Dome Fossil from Mt. Moon; the other fossil is lost for good",
    ),
    # The third fossil is nobody's rival: the Old Amber is its own item, out of a display case
    # in the Pewter Museum of Science, and taking it costs you neither of the other two.
    "aerodactyl": GiftDetail(
        kind=GiftKind.FOSSIL,
        npc="Cinnabar Island Pokemon Lab scientist",
        requirement="Old Amber from the Pewter Museum of Science",
    ),
    "hitmonlee": GiftDetail(
        npc="The Fighting Dojo master",
        requirement="Pick one of the two in Saffron City; the other stays behind",
    ),
    "hitmonchan": GiftDetail(
        npc="The Fighting Dojo master",
        requirement="Pick one of the two in Saffron City; the other stays behind",
    ),
    "eevee": GiftDetail(npc="A man in the Celadon Mansion"),
    "lapras": GiftDetail(npc="A Silph Co. employee"),
    # He stands in a Pokemon Center near Mt. Moon and asks 500 for a Magikarp, which is a joke
    # the games have never dropped. Where exactly is the record's own business: Red has him in
    # two of them.
    "magikarp": GiftDetail(
        npc="The Magikarp salesman",
        requirement="Bought for 500 Pokedollars",
    ),
    "snorlax": GiftDetail(requirement="Poke Flute, to wake the one asleep across the road"),
}

#: What FireRed and LeafGreen add to that, and where they disagree with Red and Blue.
GBA_PAIR_GIFTS: dict[str, GiftDetail] = {
    **SHARED_GIFTS,
    # Not the Hypno the same forest holds in its grass: this is the one that frightened Lostelle,
    # and it is standing there because her father asked you to go and find her.
    "hypno": GiftDetail(requirement="The Hypno that frightened Lostelle, in Berry Forest"),
    "mewtwo": GiftDetail(
        requirement=(
            "Cerulean Cave, which opens once the Network Machine on the Sevii Islands works"
        ),
    ),
}

#: And what Generation 1 adds, in all three of its releases.
#:
#: Almost nothing, which is the point: one door opens differently and everything else in Kanto
#: is where the remake later left it. Their Game Corner needs no table at all - PokeAPI carries
#: what each window charges as a condition on the encounter, which it does not for the remake.
#:
#: Not ``GB_PAIR`` because it is not the pair's: Yellow's Cerulean Cave opens on the same Elite
#: Four, and what Yellow does disagree about it says in its own file.
GB_GIFTS: dict[str, GiftDetail] = {
    **SHARED_GIFTS,
    "mewtwo": GiftDetail(requirement="Cerulean Cave, which opens once the Elite Four are beaten"),
}


#: What the Rocket Game Corner charges for each Pokemon in its windows, in coins, per version.
#:
#: The one table these two disagree about in more than which species: the same Abra is 180 coins
#: on one cartridge and 120 on the other, and Porygon is 9999 against 6500. A species listed for
#: one version only is that version's exclusive prize - Scyther on FireRed, Pinsir on LeafGreen -
#: and the other half simply never meets it here.
GBA_PRIZE_CORNER: dict[str, dict[str, int]] = {
    "abra": {"firered": 180, "leafgreen": 120},
    "clefairy": {"firered": 500, "leafgreen": 750},
    "dratini": {"firered": 2800, "leafgreen": 4600},
    "porygon": {"firered": 9999, "leafgreen": 6500},
    "scyther": {"firered": 5500},
    "pinsir": {"leafgreen": 2500},
}


def gba_gifts(version: str) -> dict[str, GiftDetail]:
    """The gift table as one half of the pair sees it, prices included."""
    priced = {
        species: GiftDetail(
            requirement=f"Rocket Game Corner prize, {coins[version]} coins",
        )
        for species, coins in GBA_PRIZE_CORNER.items()
        if version in coins
    }

    return {**GBA_PAIR_GIFTS, **priced}


#: What PokeAPI calls Red and Blue when it says which version group an evolution started in.
#:
#: The one group in the series that introduced nothing: everything here is the original, and
#: four of its evolutions need a link cable - Kadabra, Machoke, Graveler and Haunter - which in
#: this generation means a second Game Boy and a second player.
GB_PAIR_VERSION_GROUP = "red-blue"

#: The nine trades Red and Blue share, and what each one wants.
#:
#: Nobody is named, and that is the games rather than a gap in the table. Generation 1 stores no
#: trainer name on a traded Pokemon: the Original Trainer is a hardcoded string that reads
#: "TRAINER" in whatever language the cartridge is. What the games do give is a nickname - the
#: Farfetch'd is DUX, the Mr. Mime is MARCEL, the Jynx is LOLA - and there is no field for that,
#: so it is written down here rather than lost.
#:
#: Japanese Red and Green trade the other Nidoran, and Japanese Blue trades nine different
#: Pokemon altogether. Neither is in this dataset, so neither is here.
GB_PAIR_TRADES = (
    InGameTrade(gets="mr-mime", wants="abra", location="Route 2"),
    InGameTrade(gets="nidoran-f", wants="nidoran-m", location="Underground Path"),
    InGameTrade(gets="nidorina", wants="nidorino", location="Route 11"),
    InGameTrade(gets="lickitung", wants="slowbro", location="Route 18"),
    InGameTrade(gets="jynx", wants="poliwhirl", location="Cerulean City"),
    InGameTrade(gets="farfetchd", wants="spearow", location="Vermilion City"),
    InGameTrade(gets="electrode", wants="raichu", location="Cinnabar Island, Pokemon Lab"),
    InGameTrade(gets="tangela", wants="venonat", location="Cinnabar Island, Pokemon Lab"),
    InGameTrade(gets="seel", wants="ponyta", location="Cinnabar Island, Pokemon Lab"),
)

#: The six NPCs who trade the same thing on both cartridges, and what each one wants.
#:
#: No API carries these. The names are the original trainers the games record on what they hand
#: over, which is how a player can tell a traded Pokemon from a caught one.
SHARED_TRADES = (
    InGameTrade(gets="mr-mime", wants="abra", location="Route 2", npc="Reyley"),
    InGameTrade(gets="jynx", wants="poliwhirl", location="Cerulean City", npc="Dontae"),
    InGameTrade(gets="farfetchd", wants="spearow", location="Vermilion City", npc="Elyssa"),
    InGameTrade(
        gets="electrode",
        wants="raichu",
        location="Cinnabar Island, Pokemon Lab",
        npc="Clifton",
    ),
    InGameTrade(
        gets="tangela",
        wants="venonat",
        location="Cinnabar Island, Pokemon Lab",
        npc="Norma",
    ),
    InGameTrade(
        gets="seel",
        wants="ponyta",
        location="Cinnabar Island, Pokemon Lab",
        npc="Garett",
    ),
)

#: The three trades the halves disagree about, by version.
#:
#: Two of them are the same NPC asking for the opposite Nidoran, which is the pair switch doing
#: what it always does. The third is stranger: the man on Route 18 hands over the same Lickitung
#: in both games but wants a Golduck on FireRed and a Slowbro on LeafGreen.
SPLIT_TRADES: dict[str, tuple[InGameTrade, ...]] = {
    "firered": (
        InGameTrade(
            gets="nidoran-f",
            wants="nidoran-m",
            location="Underground Path, Routes 5 to 6",
            npc="Saige",
        ),
        InGameTrade(gets="nidorina", wants="nidorino", location="Route 11", npc="Turner"),
        InGameTrade(gets="lickitung", wants="golduck", location="Route 18", npc="Haden"),
    ),
    "leafgreen": (
        InGameTrade(
            gets="nidoran-m",
            wants="nidoran-f",
            location="Underground Path, Routes 5 to 6",
            npc="Saige",
        ),
        InGameTrade(gets="nidorino", wants="nidorina", location="Route 11", npc="Turner"),
        InGameTrade(gets="lickitung", wants="slowbro", location="Route 18", npc="Haden"),
    ),
}


def trades(version: str) -> tuple[InGameTrade, ...]:
    """Every in-game trade one half of the pair offers."""
    return SHARED_TRADES + SPLIT_TRADES[version]
