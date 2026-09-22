"""What the Generation 3 Hoenn cartridges have in common.

Ruby and Sapphire are a version pair, and a pair is the one case where two games really are
one dataset with a switch in it: the same region, the same National Dex reach, the same
Pokedex, the same link cable. What differs is a list of version exclusives. Writing that twice
is how a shared table gets edited in one file and not the other, so the shared half lives here
and each game brings only what is true about itself.

They are still two entities. A player picks Ruby as a linked game without picking Sapphire, so
each has its own id, its own file, its own box art and its own row in the picker. Shared code
is not a shared game.

Emerald sits here too for the parts it shares - the same region, the same reach, the same
cable - while keeping its own dex numbering and its own redrawn sprites in its own file.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from ..breeding import EggFrom, breeding_encounters
from ..evolutions import evolution_encounters
from ..games import BuildContext
from ..gifts import GiftDetail, gift_encounters
from ..models import (
    AcquisitionMethod,
    AllSpeciesFilter,
    DexEntry,
    DexSource,
    DexTarget,
    Game,
    GameRelease,
    GiftKind,
    TransferDirection,
    TransferEdge,
    TransferMechanism,
)
from ..places import LocationNames
from ..sources import bulbapedia
from ..trades import InGameTrade, trade_encounters
from ..wild import wild_encounters

GENERATION = 3

REGION = "Hoenn"

#: The National Dex opens after the Elite Four in all three, and stops at Deoxys.
NATIONAL_DEX_THROUGH = 386

#: PokeAPI's name for the Generation 3 Hoenn dex, the 202-entry one all three share. Not
#: "updated-hoenn", which is the 211-entry dex of Omega Ruby and Alpha Sapphire.
DEX = "hoenn"

#: What PokeAPI calls the pair when it says which version group an evolution started in. Ruby
#: and Sapphire are one group; Emerald is its own, and reads that name from its own file.
PAIR_VERSION_GROUP = "ruby-sapphire"

#: Where the pair's own battle sprites live in the sprite repository. One sheet for the two of
#: them: Ruby and Sapphire were drawn from the same set, and Emerald redrew it later, which is
#: why the third version names a directory of its own.
PAIR_SPRITE_SET = "generation-iii/ruby-sapphire"

#: The Hoenn day care, which is on the same route in all three cartridges.
DAY_CARE = "Route 117, Pokemon Day Care"

#: Every Generation 3 cartridge that trades with every other over a link cable.
#:
#: Colosseum and XD trade with them as well, but they are not in the plan, so nothing here
#: claims them. A game declares the whole set whether or not the others are built yet: the
#: registry holds an edge back until both ends exist, and adding a cartridge later lights its
#: routes up without anyone editing the games that were already written.
GBA_CARTRIDGES = ("ruby", "sapphire", "emerald", "firered", "leafgreen")


def cartridge(
    *,
    game_id: str,
    title: str,
    version: str,
    sprite_set: str | None = None,
    pair_partner: str | None = None,
) -> Game:
    """One Hoenn cartridge, with the facts all three of them share filled in.

    ``pair_partner`` is the whole difference between Ruby and Sapphire on one hand and Emerald
    on the other: the first two are halves of a pair and name each other, and the third is a
    third version and names nobody.
    """
    return Game(
        id=game_id,
        title=title,
        version=version,
        generation=GENERATION,
        region=REGION,
        release=GameRelease.CARTRIDGE,
        # The number rather than a yes or no: the dex builder has to know where it stops.
        national_dex_through=NATIONAL_DEX_THROUGH,
        dex_source=DexSource.NATIONAL_DEX,
        pair_partner=pair_partner,
        sprite_set=sprite_set,
    )


def link_trade_edges(game_id: str) -> list[TransferEdge]:
    """What this cartridge can send and receive over a link cable.

    Trading inside a generation goes both ways and carries anything the game can hold, so one
    edge per partner says it all. Both ends may declare the same edge; they collapse into one,
    so neither game has to know whether the other got there first.

    Pal Park into Generation 4 is not here. It is one way, and it belongs to the game that
    receives - that is where the National Dex limit it applies is a fact about the receiver.
    """
    return [
        TransferEdge(
            **{"from": game_id},
            to=partner,
            mechanism=TransferMechanism.TRADE,
            direction=TransferDirection.BOTH_WAYS,
            filter=AllSpeciesFilter(),
        )
        for partner in GBA_CARTRIDGES
        if partner != game_id
    ]


def dex_entries(
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

    Steps 3 to 5, and every one of them the same for both halves except for one word - which
    version PokeAPI is asked about. Everything else they share, which is why the tables this
    reads are module-level here rather than passed in: two copies of the same three trades is
    how one of them gets edited and the other does not.

    The wild and gift steps read the same encounter tables and walk into the same places, so
    they share one place lookup: Route 119 is named once however many times it comes up.
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
            details=PAIR_GIFTS,
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
        *breeding_encounters(
            game_id=game_id,
            day_care=DAY_CARE,
            eggs=PAIR_EGGS,
            citation=bulbapedia("Baby_Pok%C3%A9mon", retrieved_on=today),
        ),
        *trade_encounters(
            game_id=game_id,
            trades=PAIR_TRADES,
            citation=bulbapedia("In-game_trade", retrieved_on=today),
        ),
    ]


#: The Bonus Disc that came with Pokemon Colosseum in the West, and the Tanabata giveaways in
#: Japan. Nothing in any of the three games produces one, so all three say the same thing.
JIRACHI_REASON = (
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
DEOXYS_REASON = (
    "Distribution event only: the Space Center Deoxys in the United States and the Doel Deoxys "
    "in the Netherlands, both in 2006"
)


def only_on(partner: str, event: str | None = None) -> str:
    """Why an entry in this dex is not in this cartridge, when the other half has it.

    A version exclusive is still an entry you have to fill, and the transfer graph is how -
    which is the whole reason the two halves declare a route to each other.

    ``event`` is what step 7 found. It does not change that the cartridge cannot produce one; it
    answers the next question, which is where one could ever have come from.
    """
    reason = f"{partner} only in Generation 3; trade one in"

    return f"{reason}. {event[0].upper()}{event[1:]}" if event else reason


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
PAIR_GIFTS: dict[str, GiftDetail] = {
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
    # The Mirage Tower holds one of the two fossils and crumbles once it is taken. Emerald gives
    # the other one back later in the Desert Underpass; these two never do, so here the choice
    # really is final.
    "lileep": GiftDetail(
        kind=GiftKind.FOSSIL,
        npc="Devon Corporation scientist",
        requirement="Root Fossil from the Mirage Tower; the other fossil is lost for good",
    ),
    "anorith": GiftDetail(
        kind=GiftKind.FOSSIL,
        npc="Devon Corporation scientist",
        requirement="Claw Fossil from the Mirage Tower; the other fossil is lost for good",
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
PAIR_TRADES = (
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
PAIR_EGGS: dict[str, EggFrom] = {
    "pichu": EggFrom(parents=("pikachu", "raichu")),
    "igglybuff": EggFrom(parents=("jigglypuff", "wigglytuff")),
    "azurill": EggFrom(parents=("marill", "azumarill")),
}
