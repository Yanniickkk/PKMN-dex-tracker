"""Pokemon Emerald: entity, dex, and the ways to fill it.

Steps 1 to 5 for this game. The machinery lives in shared modules - :mod:`wild`, :mod:`gifts`
and :mod:`evolutions` read PokeAPI the same way for every game - and what is here is what is
true about Emerald in particular: which cartridges it trades with, which dex it shows, who
hands over a starter, what a legendary is waiting behind, who will swap a Ralts for a Seedot,
and which babies only the day care produces.
"""

from __future__ import annotations

from datetime import date

from ..breeding import EggFrom, breeding_encounters
from ..evolutions import evolution_encounters
from ..games import BuildContext, GameRegistry
from ..gifts import GiftDetail, gift_encounters
from ..models import (
    AcquisitionMethod,
    AllSpeciesFilter,
    DexEntry,
    DexSource,
    DexTarget,
    Game,
    GameData,
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

GAME_ID = "emerald"

#: The other Generation 3 cartridges Emerald can trade with over a link cable. Colosseum and XD
#: also trade with it, but they are not in the plan, so they are not claimed here.
GBA_PARTNERS = ("ruby", "sapphire", "firered", "leafgreen")

#: PokeAPI's name for the Generation 3 Hoenn dex, the 202-entry one Ruby, Sapphire and Emerald
#: share. Not "updated-hoenn", which is the 211-entry dex of Omega Ruby and Alpha Sapphire.
HOENN_DEX = "hoenn"

#: What PokeAPI calls this game when it lists which version an encounter belongs to.
POKEAPI_VERSION = "emerald"

#: What PokeAPI calls this game when it says which version group an evolution started in.
#: Emerald is its own group rather than part of Ruby and Sapphire's, and the difference is the
#: whole reason a game names it instead of naming a generation.
POKEAPI_VERSION_GROUP = "emerald"

#: Where this game's own battle sprites live in the sprite repository. Emerald redrew Ruby and
#: Sapphire's, so it has a set of its own rather than sharing theirs, and it stops at 386 -
#: exactly as far as its National Dex reaches.
SPRITE_SET = "generation-iii/emerald"

#: Dex entries no amount of playing Emerald will fill, and why.
#:
#: A reason rather than a gap: the validator can tell "we checked and it cannot be caught" from
#: "we have not gathered this yet", and only the second is a fault.
UNOBTAINABLE: dict[str, str] = {
    # The Bonus Disc that came with Pokemon Colosseum, at shops and events in 2003 and 2004.
    # Nothing in the game itself produces one.
    "jirachi": "Distribution event only (the Pokemon Colosseum Bonus Disc)",
    # In the Hoenn dex, not in the game. Emerald kept Seviper and Solrock and left the other
    # half of each pair on the cartridge it came from; both are still entries you have to fill,
    # and the transfer graph is how - which is the whole reason a route from Ruby exists.
    "zangoose": "Ruby only in Generation 3; trade one in",
    "lunatone": "Sapphire only in Generation 3; trade one in",
    # In Ruby and Sapphire's grass and not in Emerald's. Step 3 found no encounter for either,
    # which read like a hole in the data until it was checked: it is the game.
    "roselia": "Ruby and Sapphire only in Generation 3; trade one in",
    "meditite": "Ruby and Sapphire only in Generation 3; trade one in",
    # The one entry here that is nearly obtainable. Emerald keeps Surskit for the daily swarm,
    # and an Emerald swarm only offers it once records have been mixed with a Ruby or Sapphire
    # cartridge - so it still takes a second game, the same as the three above. A wild record
    # would say "Route 102, walking" and send a player to wait for something that never comes,
    # because the schema has nowhere to hang the condition that matters.
    "surskit": (
        "Swarm only, and an Emerald swarm offers it only after mixing records with a "
        "Ruby or Sapphire cartridge"
    ),
}

#: The four NPCs who will trade, and what each one wants for it.
#:
#: No API carries these. The names are the original trainers the game records on what it hands
#: over, which is how a player can tell a traded Pokemon from a caught one.
#:
#: None of the four is the only way to get what it gives, so nothing in the dex depends on
#: them. They are here because they are true, and because a player wondering where a Meowth
#: comes from in a Hoenn game deserves an answer.
TRADES = (
    InGameTrade(gets="seedot", wants="ralts", location="Rustboro City", npc="Kobe"),
    InGameTrade(gets="plusle", wants="volbeat", location="Fortree City", npc="Roman"),
    InGameTrade(gets="horsea", wants="bagon", location="Pacifidlog Town", npc="Skylar"),
    InGameTrade(
        gets="meowth",
        wants="skitty",
        location="Battle Frontier",
        npc="Isis",
        requirement="After reaching the Battle Frontier, which opens once the Elite Four are done",
    ),
)

#: The babies nothing else in this game produces.
#:
#: Wynaut is not here although it breeds too: Emerald hands one over in an egg, and a record
#: for the long way round adds nothing. Generation 3 asks for no incense, so no parent here
#: has to be holding anything.
EGGS: dict[str, EggFrom] = {
    "pichu": EggFrom(parents=("pikachu", "raichu")),
    "igglybuff": EggFrom(parents=("jigglypuff", "wigglytuff")),
    "azurill": EggFrom(parents=("marill", "azumarill")),
}

#: Who hands a Pokemon over, and what has to be true first.
#:
#: PokeAPI knows the method, the place and the level; the rest is this game's own business. It
#: also calls a starter, a revived fossil and a present from a stranger all "gift", so the ones
#: that are something more particular say so here.
GIFTS: dict[str, GiftDetail] = {
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
    "lileep": GiftDetail(
        kind=GiftKind.FOSSIL,
        npc="Devon Corporation scientist",
        requirement="Root Fossil from the Mirage Tower; only one of the two fossils can be taken",
    ),
    "anorith": GiftDetail(
        kind=GiftKind.FOSSIL,
        npc="Devon Corporation scientist",
        requirement="Claw Fossil from the Mirage Tower; only one of the two fossils can be taken",
    ),
    "beldum": GiftDetail(
        npc="Steven",
        requirement="In the Poke Ball in his house, after the Elite Four",
    ),
    "castform": GiftDetail(
        npc="Weather Institute scientist",
        requirement="After driving Team Aqua out of the Weather Institute",
    ),
    "wynaut": GiftDetail(
        npc="Woman in Lavaridge Town",
        requirement="Hatches from the egg she gives you",
    ),
    "kecleon": GiftDetail(requirement="Devon Scope, to see it at all"),
    "rayquaza": GiftDetail(requirement="After the fight at Sootopolis City"),
    # The cave is real but its entrance moves around Hoenn after the Elite Four.
    "groudon": GiftDetail(requirement="The cave moves; the TV weather report says where it is"),
    "kyogre": GiftDetail(requirement="The cave moves; the TV weather report says where it is"),
    "regirock": GiftDetail(requirement="Braille puzzle, with Relicanth and Wailord in the party"),
    "regice": GiftDetail(requirement="Braille puzzle, with Relicanth and Wailord in the party"),
    "registeel": GiftDetail(requirement="Braille puzzle, with Relicanth and Wailord in the party"),
    # Both tickets were handed out at events. The Pokemon are in the game; the boat ride to them
    # was never sold.
    "latias": GiftDetail(requirement="Eon Ticket, a distribution event"),
    "latios": GiftDetail(requirement="Eon Ticket, a distribution event"),
    "deoxys": GiftDetail(requirement="Aurora Ticket, a distribution event"),
}


def build(context: BuildContext) -> GameData:
    entries = dex_entries(context)

    return GameData(
        game=Game(
            id=GAME_ID,
            title="Pokémon Emerald Version",
            version="Emerald",
            generation=3,
            region="Hoenn",
            release=GameRelease.CARTRIDGE,
            # Emerald's own dex is the 202-entry Hoenn one, but the National Dex opens after the
            # Elite Four and that is what a living dex in this game is aiming at.
            national_dex_through=386,
            dex_source=DexSource.NATIONAL_DEX,
            # The third version of Ruby and Sapphire rather than half of a pair.
            pair_partner=None,
            sprite_set=SPRITE_SET,
        ),
        dex_entries=entries,
        acquisition_methods=acquisition_methods(context, entries),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """The Hoenn dex as Emerald numbers it: Treecko is #001, Deoxys is #202.

    This is the game's own dex, not the list a living dex in Emerald is aiming at. That list is
    the National Dex, which the entity already says it reaches 386 of; this one is what the
    game's own Pokedex shows and what the coverage report measures encounters against.

    Ruby, Sapphire and Emerald share these 202 entries and their numbering, so PokeAPI's
    ``hoenn`` dex answers for all three.
    """
    api = context.require_api()

    return [
        DexEntry(
            game=GAME_ID,
            target=DexTarget(species=species),
            number=number,
            unobtainable_reason=UNOBTAINABLE.get(species),
        )
        for number, species in api.pokedex(HOENN_DEX, refresh=context.refresh)
    ]


def edges() -> list[TransferEdge]:
    """What Emerald can send and receive.

    Trading inside a generation goes both ways and carries anything the game can hold, so one
    edge per partner says it all. The partners are declared whether or not they are in the
    dataset yet: the registry holds an edge back until both ends exist, so this file states what
    is true about Emerald rather than what happens to be built already.

    Pal Park into Generation 4 is not here. It is one way, and it belongs to the game that
    receives - that is where the National Dex limit it applies is a fact about the receiver.
    """
    return [
        TransferEdge(
            **{"from": GAME_ID},
            to=partner,
            mechanism=TransferMechanism.TRADE,
            direction=TransferDirection.BOTH_WAYS,
            filter=AllSpeciesFilter(),
        )
        for partner in GBA_PARTNERS
    ]


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Emerald EN boxart.jpg")


def acquisition_methods(context: BuildContext, entries: list[DexEntry]) -> list[AcquisitionMethod]:
    """Every way to get something in Emerald.

    Step 3 fills the wild slots, step 4 the gifts and statics, and step 5 the rest: what
    evolves into what here, who will trade, and which babies only the day care lays. Two thirds
    of the Hoenn dex is an evolution of something else, so until this step ran the game looked
    as though seventy of its entries had no answer at all.

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
            game_id=GAME_ID,
            version=POKEAPI_VERSION,
            species=species,
            retrieved_on=today,
            refresh=context.refresh,
            places=places,
        ),
        *gift_encounters(
            api,
            game_id=GAME_ID,
            version=POKEAPI_VERSION,
            species=species,
            retrieved_on=today,
            details=GIFTS,
            refresh=context.refresh,
            places=places,
        ),
        *evolution_encounters(
            api,
            game_id=GAME_ID,
            version_group=POKEAPI_VERSION_GROUP,
            species=species,
            retrieved_on=today,
            refresh=context.refresh,
        ),
        *breeding_encounters(
            game_id=GAME_ID,
            # Hoenn has one day care, and it is on the route between Mauville and Verdanturf.
            day_care="Route 117, Pokemon Day Care",
            eggs=EGGS,
            citation=bulbapedia("Baby_Pok%C3%A9mon", retrieved_on=today),
        ),
        *trade_encounters(
            game_id=GAME_ID,
            trades=TRADES,
            citation=bulbapedia("In-game_trade", retrieved_on=today),
        ),
    ]
