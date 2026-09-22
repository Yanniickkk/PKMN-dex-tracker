"""What the Generation 3 Kanto cartridges have in common.

FireRed and LeafGreen are a version pair in the same sense Ruby and Sapphire are: one dataset
with a switch in it, the switch being a list of version exclusives. The shared half lives here
and each game brings only what is true about itself.

They are still two entities, with their own ids, their own box art and their own row in the
picker. A player who owns one of them owns one of them.

This file holds the region, the pair's Pokedex, their sprite sheet, every way they have of
producing something - caught, handed over, traded for or evolved - and the distributions that
once handed out what they cannot produce at all. What FireRed and LeafGreen share with the
Hoenn cartridges rather than with each other is in :mod:`gba`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from ..evolutions import evolution_encounters
from ..games import BuildContext
from ..gifts import GiftDetail, gift_encounters
from ..models import AcquisitionMethod, DexEntry, DexTarget, Game, GiftKind, TransferEdge
from ..places import LocationNames
from ..sources import bulbapedia
from ..trades import InGameTrade, trade_encounters
from ..wild import wild_encounters
from . import gba

GENERATION = gba.GENERATION

#: Kanto proper. The Sevii Islands are part of these two games and of no other, but they are
#: an area within them rather than a region of their own, so they are named where they are
#: used - in a location - and not here.
REGION = "Kanto"

#: The National Dex opens after the Elite Four here as well, and stops at Deoxys.
NATIONAL_DEX_THROUGH = gba.NATIONAL_DEX_THROUGH

#: PokeAPI's name for the 151-entry Kanto dex. FireRed and LeafGreen show the same one Red and
#: Blue did, in the same order, which is why PokeAPI files all of them under one name instead of
#: giving this pair a dex of its own - it checks out: the resource lists ``firered-leafgreen``
#: among the version groups it belongs to.
#:
#: Not the National Dex the games also have. That one arrives after the Elite Four, it is not
#: the game's own Pokedex, and the entity already says how far it reaches.
DEX = "kanto"

#: What PokeAPI calls the pair when it says which version group an evolution started in. The
#: two halves are one group, the way Ruby and Sapphire are.
PAIR_VERSION_GROUP = "firered-leafgreen"

#: Where the pair's own battle sprites live in the sprite repository. One sheet for the two of
#: them: FireRed and LeafGreen were drawn from the same set, which is why it is named here and
#: not in either game's file.
PAIR_SPRITE_SET = "generation-iii/firered-leafgreen"


def cartridge(
    *,
    game_id: str,
    title: str,
    version: str,
    released: date,
    pair_partner: str,
    sprite_set: str | None = None,
) -> Game:
    """One half of the pair.

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


def link_trade_edges(game_id: str) -> list[TransferEdge]:
    """What this cartridge can send and receive over a link cable: every other GBA cartridge."""
    return gba.link_trade_edges(game_id)


def only_on(partner: str, event: str | None = None) -> str:
    """Why an entry in this dex is not in this cartridge, when the other half has it."""
    return gba.only_on(partner, event)


#: Never in either half, and in no other Generation 3 game but Emerald's Faraway Island - which
#: takes an Old Sea Map that was itself only ever handed out at events.
#:
#: Step 7 named the three that reached these cartridges. There were dozens more in Generation 1;
#: those went onto a Game Boy cartridge and cannot reach a Game Boy Advance one.
MEW_REASON = (
    "Distribution event only: the Hadou Mew in Japan in 2005, the Mystery Mew in the United "
    "States in 2006, and the Aura Mew across Europe in 2007"
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
    """One sentence naming every distribution that ever handed this species out.

    Written as a list of events rather than one sentence per event because most of these were
    covered twice, and "an event existed" is the answer a player is after - which one is detail
    they can read once and forget.
    """
    named = (
        " and ".join(events) if len(events) < 3 else f"{', '.join(events[:-1])} and {events[-1]}"
    )

    return f"{named} handed one out"


def dex_entries(
    context: BuildContext,
    *,
    game_id: str,
    unobtainable: Mapping[str, str] | None = None,
) -> list[DexEntry]:
    """The Kanto dex as both halves number it: Bulbasaur #001 to Mew #151.

    This is the game's own Pokedex, not the list a living dex in it is aiming at. That list is
    the National Dex, which the entity already says it reaches 386 of; this one is what the
    game's own Pokedex shows and what the coverage report measures encounters against.

    The pair share these entries *and their numbering*, which is why one function answers for
    both. What differs between them is which entries their own grass never holds, and that is
    the ``unobtainable`` table each game brings.

    Kanto has no forms to decide about: every one of the 151 is a plain species here. The
    regional forms these species later grew are Alolan and Galarian, which is Generation 7 and
    8 and no business of a Game Boy Advance cartridge.
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


def pair_acquisition_methods(
    context: BuildContext,
    *,
    game_id: str,
    version: str,
    entries: Sequence[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something in one of the pair.

    The halves differ by one word - which version PokeAPI is asked about - so one function
    answers for both and each game brings its own version name. Two copies of this is how one
    of them gets edited and the other does not.

    Steps 3 to 5: what the grass, the water and the rods hold, what is handed over or waiting
    in one spot, what an NPC will swap for, and what evolves into what here.

    The day care on Four Island is not here, and its absence is a fact rather than a gap. A
    Kanto dex is 151 entries and every baby Pokemon is Generation 2 or later, so nothing these
    games can hatch is anything this dex asks for. Ruby and Sapphire hatch three because their
    dex has three to hatch.

    The wild and gift steps read the same encounter tables and walk into the same places, so
    they share one place lookup: Route 4 is named once however many times it comes up.
    """
    api = context.require_api()
    # Every species the living dex here asks for, which is not the game's own Pokedex. Those
    # are two different lists, and asking only about the second is what left every entry
    # outside the regional dex with nothing recorded against it - in games that produce plenty
    # of them.
    species = context.living_dex(through=NATIONAL_DEX_THROUGH, entries=entries)
    today = date.today()
    places = LocationNames(api, refresh=context.refresh)

    return [
        *wild_encounters(
            api,
            game_id=game_id,
            version=version,
            species=species,
            retrieved_on=today,
            refresh=context.refresh,
            places=places,
        ),
        *gift_encounters(
            api,
            game_id=game_id,
            version=version,
            species=species,
            retrieved_on=today,
            details=gifts(version),
            refresh=context.refresh,
            places=places,
        ),
        *evolution_encounters(
            api,
            game_id=game_id,
            version_group=PAIR_VERSION_GROUP,
            species=species,
            retrieved_on=today,
            refresh=context.refresh,
        ),
        *trade_encounters(
            game_id=game_id,
            trades=trades(version),
            citation=bulbapedia("In-game_trade", retrieved_on=today),
        ),
    ]


#: What only the game knows about each thing it hands over or leaves standing in one spot.
#:
#: PokeAPI carries the method, the place and the level. It does not carry who hands it over or
#: what has to be true first, and it calls a starter, a fossil and a present from a stranger by
#: the same word - `gift` - which is why the kinds are corrected here.
#:
#: One table for the pair: both halves hand over the same things in the same places. The one
#: thing they disagree about is what the Game Corner charges, and that is :data:`PRIZE_CORNER`.
PAIR_GIFTS: dict[str, GiftDetail] = {
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
    "magikarp": GiftDetail(
        npc="The Magikarp salesman",
        requirement="Bought for 500 Pokedollars in the Route 4 Pokemon Center",
    ),
    "snorlax": GiftDetail(requirement="Poke Flute, to wake the one asleep across the road"),
    # Not the Hypno the same forest holds in its grass: this is the one that frightened Lostelle,
    # and it is standing there because her father asked you to go and find her.
    "hypno": GiftDetail(requirement="The Hypno that frightened Lostelle, in Berry Forest"),
    "mewtwo": GiftDetail(
        requirement=(
            "Cerulean Cave, which opens once the Network Machine on the Sevii Islands works"
        ),
    ),
}


#: What the Rocket Game Corner charges for each Pokemon in its windows, in coins, per version.
#:
#: The one table these two disagree about in more than which species: the same Abra is 180 coins
#: on one cartridge and 120 on the other, and Porygon is 9999 against 6500. A species listed for
#: one version only is that version's exclusive prize - Scyther on FireRed, Pinsir on LeafGreen -
#: and the other half simply never meets it here.
PRIZE_CORNER: dict[str, dict[str, int]] = {
    "abra": {"firered": 180, "leafgreen": 120},
    "clefairy": {"firered": 500, "leafgreen": 750},
    "dratini": {"firered": 2800, "leafgreen": 4600},
    "porygon": {"firered": 9999, "leafgreen": 6500},
    "scyther": {"firered": 5500},
    "pinsir": {"leafgreen": 2500},
}


def gifts(version: str) -> dict[str, GiftDetail]:
    """The gift table as one half of the pair sees it, prices included."""
    priced = {
        species: GiftDetail(
            requirement=f"Rocket Game Corner prize, {coins[version]} coins",
        )
        for species, coins in PRIZE_CORNER.items()
        if version in coins
    }

    return {**PAIR_GIFTS, **priced}


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
