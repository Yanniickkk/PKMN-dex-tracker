"""What the Johto cartridges have in common, whichever generation they are from.

Two sets of games are set here. HeartGold and SoulSilver are Generation 4 and a version pair,
the way Diamond and Pearl are; Gold, Silver and Crystal are the same region two generations
earlier, and they will read from this file too. That is the difference between this module and
:mod:`kanto`, which says "the Generation 3 Kanto cartridges" in its first line: this one is
about the place, not about the hardware that happened to be in a player's hands.

So the split is drawn twice over:

* What is true of Johto - its Pokedex, where the day care is, what walks in its grass - lives
  here, and a table that belongs to one pair rather than to the region says so in its name.
* What is true of the hardware and the generation - which cartridges trade with which, how far
  the National Dex reaches, whether there is a Pal Park at all - lives with the generation:
  :mod:`ds` for HeartGold and SoulSilver, and its own module for Gold and Silver when they
  arrive.

Nothing here should have to be edited to add Gold and Silver. Something that does have to be
edited is a fact about the DS pair that has been written down as a fact about Johto.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from ..breeding import EggFrom, breeding_encounters
from ..evolutions import evolution_encounters
from ..games import BuildContext
from ..gifts import GiftDetail, GiftDetails, gift_encounters
from ..models import AcquisitionMethod, DexEntry, DexTarget, Game, GiftKind, TransferEdge
from ..places import LocationNames
from ..sources import bulbapedia
from ..trades import InGameTrade, trade_encounters
from ..wild import wild_encounters
from . import ds, exclusives

#: The region itself. Kanto is playable in every game set here, but it is a second half of the
#: map rather than a second region for these entities: a HeartGold cartridge is a Johto game.
REGION = "Johto"

#: Where an egg is left and collected. The same building in every game set here: Gold and Silver
#: put the day care on Route 34 and HeartGold did not move it.
DAY_CARE = "Route 34, Pokemon Day Care"

#: PokeAPI's name for the 251-entry Johto dex, the one Gold, Silver and Crystal show.
#:
#: Not used yet - those three are not written - and named here anyway, beside the other one. A
#: single constant called "the Johto dex" is how the next reader learns there is only one.
ORIGINAL_DEX = "original-johto"

#: PokeAPI's name for the 256-entry Johto dex, the one HeartGold and SoulSilver show.
#:
#: The five extra entries are the Generation 4 evolutions of Pokemon that were already in it -
#: Yanmega, Ambipom, Lickilicky, Tangrowth, Mamoswine - and each one is filed directly behind
#: what it evolves from rather than added at the end. So this is not the original with five more
#: at the back: everything from Yanmega on is renumbered, 150 entries of it, and Celebi is #256
#: where it used to be #251.
#:
#: Which is the opposite of what Sinnoh does. Platinum's 210 keep Diamond's 151 numbers exactly
#: and append the rest, so a player moving between them recognises every number. A Gold player
#: coming to HeartGold does not, and the two dexes need separate names for that reason.
UPDATED_DEX = "updated-johto"


#: The same sentence for each of a set of three: one is taken and the others are somebody
#: else's problem. Three sets of them in these games, which is what makes them unusual.
STARTER_ELM = "Pick one of the three in his lab; the other two take a trade"
STARTER_OAK = "Pick one of the three, after Red is beaten; the other two take a trade"
STARTER_STEVEN = "Pick one of the three, once a Kanto first partner has been taken"

#: Who revives a fossil in these games, wherever it was dug up.
MUSEUM = "A scientist in the Pewter Museum"


#: What only the game knows about each thing HeartGold and SoulSilver hand over or leave
#: standing in one spot.
#:
#: Named for the pair rather than for the region, as the module docstring asks: Gold, Silver and
#: Crystal hand over their own things in their own places, and the two tables will sit side by
#: side without either being mistaken for "Johto's".
#:
#: One table for both halves. What they disagree about - which of two the Game Corner sells,
#: which legendary sleeps in the Embedded Tower, what level the cover legendary is caught at -
#: PokeAPI already files per version, so none of it needs a switch here.
DS_PAIR_GIFTS: dict[str, GiftDetails] = {
    # Johto's own three, from the lab next door to the house you start in.
    "chikorita": GiftDetail(kind=GiftKind.STARTER, npc="Professor Elm", requirement=STARTER_ELM),
    "cyndaquil": GiftDetail(kind=GiftKind.STARTER, npc="Professor Elm", requirement=STARTER_ELM),
    "totodile": GiftDetail(kind=GiftKind.STARTER, npc="Professor Elm", requirement=STARTER_ELM),
    # And two more sets afterwards, which is what makes these games unusual: a player who
    # finishes one has had three first partners handed over rather than one.
    "bulbasaur": GiftDetail(kind=GiftKind.STARTER, npc="Professor Oak", requirement=STARTER_OAK),
    "charmander": GiftDetail(kind=GiftKind.STARTER, npc="Professor Oak", requirement=STARTER_OAK),
    "squirtle": GiftDetail(kind=GiftKind.STARTER, npc="Professor Oak", requirement=STARTER_OAK),
    "treecko": GiftDetail(kind=GiftKind.STARTER, npc="Steven", requirement=STARTER_STEVEN),
    "torchic": GiftDetail(kind=GiftKind.STARTER, npc="Steven", requirement=STARTER_STEVEN),
    "mudkip": GiftDetail(kind=GiftKind.STARTER, npc="Steven", requirement=STARTER_STEVEN),
    # Every fossil of three generations is revived in one museum, and which of them a player
    # holds is the fossil itself, which the encounter's own conditions name. Where each one is
    # dug up is not in PokeAPI and is not guessed at here.
    "omanyte": GiftDetail(kind=GiftKind.FOSSIL, npc=MUSEUM),
    "kabuto": GiftDetail(kind=GiftKind.FOSSIL, npc=MUSEUM),
    "aerodactyl": GiftDetail(kind=GiftKind.FOSSIL, npc=MUSEUM),
    "lileep": GiftDetail(kind=GiftKind.FOSSIL, npc=MUSEUM),
    "anorith": GiftDetail(kind=GiftKind.FOSSIL, npc=MUSEUM),
    "cranidos": GiftDetail(kind=GiftKind.FOSSIL, npc=MUSEUM),
    "shieldon": GiftDetail(kind=GiftKind.FOSSIL, npc=MUSEUM),
    "togepi": GiftDetail(kind=GiftKind.EGG, npc="Professor Elm's assistant"),
    # Primo's three, one egg per save. The password is a set of phrases picked in conversation,
    # printed in magazines at the time and freely known now; nothing about it needs an event.
    "mareep": GiftDetail(kind=GiftKind.EGG, npc="Primo"),
    "wooper": GiftDetail(kind=GiftKind.EGG, npc="Primo"),
    "slugma": GiftDetail(kind=GiftKind.EGG, npc="Primo"),
    "tyrogue": GiftDetail(npc="The Karate King in Mt. Mortar"),
    "sudowoodo": GiftDetail(requirement="Water it with the SquirtBottle"),
    "gyarados": GiftDetail(requirement="The red one, in the middle of the lake"),
    # Three species that are handed over twice in two different places, which is what `where`
    # is for. A table keyed by species alone would have told a player that a slot machine prize
    # came from Bill.
    "eevee": (
        GiftDetail(npc="Bill", where="Goldenrod City, Bills House"),
        GiftDetail(),
    ),
    "dratini": (
        GiftDetail(
            npc="The Master of the Dragon Shrine",
            requirement=(
                "Answer his quiz; all of it right the first time and it knows ExtremeSpeed"
            ),
            where="Dragon's Den",
        ),
        GiftDetail(),
    ),
    "snorlax": (
        GiftDetail(requirement="Wake it with the Poke Flute, on the Kanto radio", where="Route 11"),
        GiftDetail(),
    ),
    # The Embedded Tower, the one place in these games where a legendary waits behind an item
    # rather than behind a story. The orbs are in-game: Mr. Pokemon hands one over once Red is
    # beaten and a Kanto first partner has been taken.
    "kyogre": GiftDetail(requirement="The Blue Orb, from Mr. Pokemon"),
    "groudon": GiftDetail(requirement="The Red Orb, from Mr. Pokemon"),
    "rayquaza": GiftDetail(
        requirement=(
            "The Jade Orb, which Professor Oak gives for being shown a Kyogre and a Groudon "
            "both caught in this tower - so one of the two has to come from the other version"
        ),
    ),
}


#: Where the pair's own battle sprites live in the sprite repository.
#:
#: One sheet for the two of them, as every pair in this dataset has. HeartGold and SoulSilver
#: redrew Generation 4's sprites rather than reusing Diamond and Pearl's or Platinum's, so a
#: player of these games saw these pictures and no others - which is the whole point of the
#: step. The set reaches 493, the same as their National Dex.
DS_PAIR_SPRITE_SET = "generation-iv/heartgold-soulsilver"

#: What PokeAPI calls the pair when it says which version group an evolution started in.
#:
#: The two halves are one group, as every pair in this dataset is. It is also the group that
#: brought the last of Generation 4's own evolution methods, so nothing in the series so far is
#: too new for these games.
DS_PAIR_VERSION_GROUP = "heartgold-soulsilver"

#: The ten NPCs who will swap something, and what each one wants.
#:
#: No API carries these. The names are the original trainers the games record on what they hand
#: over, which is how a player can tell a traded Pokemon from a caught one - and four of them
#: are characters a player already knows, because HeartGold gave its new trades to Brock,
#: Jasmine, Lt. Surge and Steven rather than to invented strangers.
#:
#: Named for the pair: Gold and Silver have their own six, in some of the same towns.
DS_PAIR_TRADES = (
    InGameTrade(gets="onix", wants="bellsprout", location="Violet City", npc="Rudy"),
    InGameTrade(
        gets="machop",
        wants="drowzee",
        location="Goldenrod City, Department Store",
        npc="Jose",
    ),
    InGameTrade(gets="voltorb", wants="krabby", location="Olivine City", npc="Richard"),
    InGameTrade(gets="dodrio", wants="dragonair", location="Blackthorn City", npc="Ayana"),
    InGameTrade(gets="magneton", wants="dugtrio", location="Power Plant", npc="Lorenzo"),
    InGameTrade(gets="xatu", wants="haunter", location="Pewter City", npc="Mondo"),
    # A Pikachu for a Pikachu, and the one handed over is foreign - which is worth having for
    # reasons the games never explain and every breeder knows.
    InGameTrade(
        gets="pikachu",
        wants="pikachu",
        location="Saffron City, Magnet Train Station",
        npc="Lt. Surge",
    ),
    InGameTrade(
        gets="beldum",
        wants="forretress",
        location="Saffron City, Silph Co",
        npc="Steven",
    ),
    InGameTrade(
        gets="rhyhorn",
        wants="bonsly",
        location="Diglett's Cave",
        npc="Brock",
        requirement="Saturdays between 5 and 8 in the evening, after he is beaten at Pewter Gym",
    ),
    # The one trader in the dataset who names no price. `wants` is left out rather than filled
    # in with something she never asked for.
    InGameTrade(
        gets="steelix",
        location="Olivine City, Gym",
        npc="Jasmine",
        requirement=(
            "Between 1 and 2 in the afternoon, after she is beaten in a rematch; "
            "she offers it on the second time she is spoken to"
        ),
    ),
)

#: The babies these games ask for that only the day care produces.
#:
#: Johto is where breeding was invented, and the list is still shorter than it looks: Azurill,
#: Budew and Chingling are in its own grass, so an egg is not the only way to one and they are
#: not here. What is left is the six babies of this region that hatch and nothing else, and the
#: six the generation after it added.
#:
#: The incense is Generation 4's doing, and only for the babies it invented: a Marill left in
#: the day care lays another Marill unless a parent holds a Sea Incense, while a Pikachu has
#: always simply laid a Pichu. Getting that backwards would send a player shopping for an item
#: they do not need, or leave them waiting for an egg that will not come.
DS_PAIR_EGGS: dict[str, EggFrom] = {
    # Generation 2's own, which need nothing but two parents.
    "pichu": EggFrom(parents=("pikachu", "raichu")),
    "cleffa": EggFrom(parents=("clefairy", "clefable")),
    "igglybuff": EggFrom(parents=("jigglypuff", "wigglytuff")),
    "smoochum": EggFrom(parents=("jynx",)),
    "elekid": EggFrom(parents=("electabuzz", "electivire")),
    "magby": EggFrom(parents=("magmar", "magmortar")),
    # And Generation 4's, each behind an incense.
    "wynaut": EggFrom(
        parents=("wobbuffet",),
        requirement="A parent has to hold a Lax Incense",
    ),
    "happiny": EggFrom(
        parents=("chansey", "blissey"),
        requirement="A parent has to hold a Luck Incense",
    ),
    "mantyke": EggFrom(
        parents=("mantine",),
        requirement="A parent has to hold a Wave Incense",
    ),
    "mime-jr": EggFrom(
        parents=("mr-mime",),
        requirement="A parent has to hold an Odd Incense",
    ),
    "munchlax": EggFrom(
        parents=("snorlax",),
        requirement="A parent has to hold a Full Incense",
    ),
    # Which is the only way to the Bonsly that Brock wants for his Rhyhorn: the trade asks for
    # one and nothing in these games hands one over.
    "bonsly": EggFrom(
        parents=("sudowoodo",),
        requirement="A parent has to hold a Rock Incense",
    ),
}


#: Never in any game set here, in either generation: the two the series has always handed out
#: rather than hidden. Both are in the Johto dex all the same, which is why they need a reason
#: rather than being quietly absent.
#:
#: What reached one generation is not what reached the other, so the sentence is here and the
#: distributions are named beside the games they were for.
MEW_REASON = "Distribution event only"
CELEBI_REASON = "Distribution event only"

#: What step 7 found for the DS pair, read off each species' *In events* table.
#:
#: Mew came over Wi-Fi rather than over a counter, which is what the generation changed: no
#: queue, no shop, a download. Three of them reached these games.
DS_PAIR_MEW_EVENT = (
    "the Susumu Mew over Japanese Wi-Fi in November 2009 and again in early 2010, and the Fall "
    "2010 Mew over Wi-Fi in English, French, German, Italian and Spanish"
)

#: And Celebi, which is more than a dex entry here: the event one is what puts the GS Ball in
#: the player's hands and Giovanni in Ilex Forest, so the distribution carried a piece of the
#: game with it.
DS_PAIR_CELEBI_EVENT = (
    "the Cinema Celebi in Japan in 2010 and the Winter 2011 Celebi across Europe and the "
    "Americas - the one that puts the GS Ball in Ilex Forest"
)

#: The one version exclusive of the eleven that any event ever covered, and it was not a
#: Pokemon that was handed out but a place to walk: the Sightseeing route for the Pokewalker,
#: which was itself an event download.
DS_PAIR_SIGHTSEEING = (
    "the Sightseeing route for the Pokewalker holds one, and that route was an event download"
)


def only_on(partner: str, event: str | None = None) -> str:
    """Why an entry in this dex is not in this cartridge, when the other half has it."""
    return ds.only_on(partner, event)


def mew_reason(event: str | None) -> str:
    """Why nothing in this game produces a Mew, and which distributions ever reached it."""
    return exclusives.with_event(MEW_REASON, event)


def celebi_reason(event: str | None) -> str:
    """Why nothing in this game produces a Celebi, and which distributions ever reached it."""
    return exclusives.with_event(CELEBI_REASON, event)


def ds_cartridge(
    *,
    game_id: str,
    title: str,
    version: str,
    released: date,
    pair_partner: str,
    sprite_set: str | None = None,
) -> Game:
    """One Johto cartridge on the DS: a Generation 4 cartridge that happens to be set here.

    Named for the hardware rather than called ``cartridge`` outright, because Gold and Silver
    are Johto cartridges too and none of what :mod:`ds` fills in is true of them. They get a
    factory of their own beside this one, reading their own generation's module. The region is
    the one argument both will pass.

    ``pair_partner`` is required: HeartGold and SoulSilver have no third version, so a cartridge
    here always has another half.
    """
    return ds.cartridge(
        game_id=game_id,
        title=title,
        version=version,
        region=REGION,
        released=released,
        sprite_set=sprite_set,
        pair_partner=pair_partner,
    )


def ds_edges(game_id: str) -> list[TransferEdge]:
    """Every route one of the DS pair brings: its own generation's trades, and Pal Park.

    Also named for the hardware. Gold and Silver's routes are nothing like these - a Time
    Capsule back to Generation 1, and the Virtual Console releases that reach Pokemon Bank are
    separate entities again - and none of that is a fact about Johto.
    """
    return ds.edges(game_id)


def updated_dex_entries(
    context: BuildContext,
    *,
    game_id: str,
    unobtainable: Mapping[str, str] | None = None,
) -> list[DexEntry]:
    """The Johto dex as HeartGold and SoulSilver number it: Chikorita #001 to Celebi #256.

    This is the game's own Pokedex, not the list a living dex in it is aiming at. That list is
    the National Dex, which the entity already says it reaches 493 of; this one is what the
    game's own Pokedex shows.

    Both halves show the same 256 entries in the same order, the way Diamond and Pearl share
    their 151: a version pair is one dataset with a switch in it, and the switch is not here.

    Johto's own form questions wait for the shared forms table, which is still empty. Unown has
    twenty-eight shapes in the Ruins of Alph and they change nothing but the look of it; the
    Rotom appliances and the Giratina forme that Platinum brought are in the National Dex these
    games reach but not in this list.
    """
    return _dex_entries(context, game_id=game_id, dex=UPDATED_DEX, unobtainable=unobtainable)


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


def acquisition_methods(
    context: BuildContext,
    *,
    game_id: str,
    version: str,
    entries: Sequence[DexEntry],
    through: int | None,
    gifts: Mapping[str, GiftDetails] | None = None,
    version_group: str | None = None,
    trades: Sequence[InGameTrade] = (),
    eggs: Mapping[str, EggFrom] | None = None,
) -> list[AcquisitionMethod]:
    """Every way to get something in one Johto cartridge.

    ``through`` is how far this game's National Dex reaches, and it is an argument rather than a
    constant for the reason the module docstring gives: Gold and Silver reach 251 and HeartGold
    and SoulSilver 493, and neither number is a fact about Johto.

    A table left out is a step nobody has done yet rather than a game with nothing to declare.
    What an NPC will swap for and what evolves into what arrive with the steps that gather them;
    handing this an empty gift table instead would print PokeAPI's bare rows and call it step 4.

    The wild and gift steps read the same encounter tables and walk into the same places, so
    they share one place lookup: Route 34 is named once however many times it comes up.

    Johto hangs more on its conditions than any region before it. The Pokegear radio changes
    what is in the grass, the Safari Zone changes what is in an area depending on what has been
    put there, the Bug-Catching Contest replaces the National Park for a day, and the headbutt
    trees are three groups a save decides between. All of that is read in :mod:`conditions`,
    which is shared, so Gold and Silver will find most of it already written.
    """
    api = context.require_api()
    # Every species the living dex here asks for, which is not the game's own Pokedex. Kanto is
    # half of these games and none of it is in their 256 entries.
    species = context.living_dex(through=through, entries=entries)
    today = date.today()
    places = LocationNames(api, refresh=context.refresh)

    found: list[AcquisitionMethod] = [
        *wild_encounters(
            api,
            game_id=game_id,
            version=version,
            species=species,
            retrieved_on=today,
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
                retrieved_on=today,
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
                retrieved_on=today,
                refresh=context.refresh,
            )
        )

    if eggs:
        found.extend(
            breeding_encounters(
                game_id=game_id,
                day_care=DAY_CARE,
                eggs=eggs,
                citation=bulbapedia("Baby_Pok%C3%A9mon", retrieved_on=today),
            )
        )

    found.extend(
        trade_encounters(
            game_id=game_id,
            trades=trades,
            citation=bulbapedia("In-game_trade", retrieved_on=today),
        )
    )

    return found


def ds_acquisition_methods(
    context: BuildContext,
    *,
    game_id: str,
    version: str,
    entries: Sequence[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something in HeartGold or SoulSilver.

    The two halves differ by one word - which version PokeAPI is asked about - so one function
    answers for both and each game brings its own version name. Two copies of this is how one of
    them gets edited and the other does not.
    """
    return acquisition_methods(
        context,
        game_id=game_id,
        version=version,
        entries=entries,
        through=ds.NATIONAL_DEX_THROUGH,
        gifts=DS_PAIR_GIFTS,
        version_group=DS_PAIR_VERSION_GROUP,
        trades=DS_PAIR_TRADES,
        eggs=DS_PAIR_EGGS,
    )
