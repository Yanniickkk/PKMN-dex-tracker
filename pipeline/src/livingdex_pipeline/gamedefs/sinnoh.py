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

from ..evolutions import evolution_encounters
from ..games import BuildContext
from ..gifts import GiftDetail, gift_encounters
from ..models import AcquisitionMethod, DexEntry, DexTarget, Game, GiftKind, TransferEdge
from ..places import LocationNames
from ..sources import bulbapedia
from ..trades import InGameTrade, trade_encounters
from ..wild import wild_encounters
from . import ds, exclusives

GENERATION = ds.GENERATION

REGION = "Sinnoh"

#: The National Dex opens after the Elite Four here as well, and stops at Arceus.
NATIONAL_DEX_THROUGH = ds.NATIONAL_DEX_THROUGH

#: PokeAPI's name for the 151-entry Sinnoh dex, the one Diamond and Pearl show.
#:
#: Not "extended-sinnoh", which is the 210-entry dex Platinum shows: the third version added 59
#: species to the regional list, so unlike the Hoenn three the Sinnoh three do *not* share one
#: dex. Platinum names its own, which is why this constant says which pair it belongs to.
PAIR_DEX = "original-sinnoh"

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


def pair_dex_entries(
    context: BuildContext,
    *,
    game_id: str,
    unobtainable: Mapping[str, str] | None = None,
) -> list[DexEntry]:
    """The Sinnoh dex as Diamond and Pearl number it: Turtwig #001 to Manaphy #151.

    This is the game's own Pokedex, not the list a living dex in it is aiming at. That list is
    the National Dex, which the entity already says it reaches 493 of.

    Sinnoh is the first region in this dataset with real form questions in its own dex. Burmy
    and Wormadam wear three cloaks, and Wormadam's change its typing, which makes them forms
    that a living dex has to count separately; Shellos and Gastrodon come in two colours that
    change nothing but their looks. Both wait for the shared forms table, which is still empty,
    the way Deoxys does in Hoenn. Rotom's appliances are not a question here at all: those
    arrived with Platinum.
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
        for number, species in api.pokedex(PAIR_DEX, refresh=context.refresh)
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

    Not quite a plain exclusive. The Underground of one half holds the Skull Fossil and the
    other the Armor Fossil, and a fossil is an item: it can come across held by a traded
    Pokemon, and be revived here. So there are two ways over the link rather than one, and a
    player who cannot find anyone with a spare Cranidos still has the other.
    """
    return exclusives.with_event(
        f"{partner} only in Generation {GENERATION}; trade one in, or trade for a Pokemon "
        f"holding the {fossil} and revive that",
        event,
    )


#: What step 7 found about Manaphy: nine distributions between 2006 and 2011 handed one out.
#:
#: The only entry of the ten this pair cannot produce that any event ever covered - and it was
#: covered nine times over, on three continents. Named rather than counted for the two a reader
#: is most likely to recognise; the rest were PalCity, the Nintendo World Store, E for All, JB
#: Hi-Fi, Nintendo of Korea and the Summer Nintendo Zone.
MANAPHY_EVENT = (
    "nine distributions between 2006 and 2011 handed one out as well, from the World Hobby Fair "
    'in Japan to the Toys "R" Us Manaphy in the United States'
)

#: Why nothing in Sinnoh produces a Manaphy.
#:
#: Its egg is a reward in Pokemon Ranger, a different game on the same handheld, and it is sent
#: across rather than found.
MANAPHY_REASON = exclusives.with_event(
    "Pokemon Ranger only: the egg is a reward in that game and is sent across to this one",
    MANAPHY_EVENT,
)


#: The four NPCs who will swap something, and what each one wants.
#:
#: No API carries these. The names are the original trainers the games record on what they hand
#: over, which is how a player can tell a traded Pokemon from a caught one. Both halves offer
#: the same four: unlike the gifts, the pair does not disagree here.
#:
#: The Haunter is worth knowing about and there is no field that says it: it is handed over
#: holding an Everstone, so the trade that would normally finish a Gengar does not. Gengar is
#: still only in the Old Chateau, and only in dual-slot mode.
PAIR_TRADES = (
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

    Steps 3 to 5: what the grass, the water, the rods and the honey trees hold, what is handed
    over or left standing in one spot, what an NPC will swap for, and what evolves into what
    here.

    The wild and gift steps read the same encounter tables and walk into the same places, so
    they share one place lookup: Route 205 is named once however many times it comes up, the
    way it is in Hoenn and Kanto.
    """
    api = context.require_api()
    species = [entry.target.species for entry in entries]
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
            excluded=NOT_A_GIFT[version],
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
            trades=PAIR_TRADES,
            citation=bulbapedia("In-game_trade", retrieved_on=today),
        ),
    ]


# The day care in Solaceon Town is not here, and its absence is a fact rather than a gap.
# Generation 4 brought most of the baby Pokemon there are, and then put them in Sinnoh's own
# grass: Cleffa and Chingling in Mt. Coronet, Pichu and Mime Jr. in the Trophy Garden, Azurill
# in the Great Marsh, Budew in Eterna Forest, Mantyke on the water, Munchlax on the honey trees.
# Happiny and Riolu are handed over as eggs. Every baby in these 151 entries has a source that
# is not an egg the player has to make, which is why Ruby and Sapphire hatch three and these
# two hatch none.
