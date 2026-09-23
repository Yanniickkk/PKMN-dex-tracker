"""What the Unova games share, which is also what Generation 5 shares.

Black and White are a version pair. Black 2 and White 2 are not a third version but a pair of
their own: sequels, set two years later in the same region, with their own story, their own
half of the map and a Pokedex almost twice as long. Nothing else in the series works that way,
and it is the reason this module keeps the two pairs apart wherever they disagree - what is
shared is written once and what is not is named for the pair it belongs to.

Every other generation in this dataset has a module for the hardware and a module for the
region, for the reason :mod:`ds` gives: Sinnoh's day care is not a fact about a DS. Generation 5
never left Unova. There is one region, one piece of hardware and four games, so the line those
two modules are drawn along has nothing on either side of it, and drawing it anyway would mean
two files that both say "Generation 5" and neither of which is about anything else. If a second
region ever arrives here, :mod:`gba` and :mod:`hoenn` show where the seam goes.

The hardware is the DS again, which is why the pattern of naming a generation's module after
the machine it ran on stops at :mod:`ds`. What Generation 5 has of its own is not a console: it
is a National Dex reaching 649, four cartridges that trade freely with each other, the Poke
Transfer standing where Pal Park stood, and Poke Transporter out to Bank.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from ..breeding import EggFrom, breeding_encounters
from ..evolutions import evolution_encounters
from ..games import BuildContext
from ..gifts import Exclusion, GiftDetail, GiftDetails, gift_encounters
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
from . import bank, ds, exclusives

GENERATION = 5

REGION = "Unova"

#: Where an egg is left and collected, in all four.
DAY_CARE = "Route 3, Pokemon Day Care"

#: The National Dex of this generation stops at Genesect.
#:
#: It is also the first one a player can read from the start: Black and White show the Unova
#: dex until the Elite Four like every game before them, but the 156 species they added are the
#: only ones in it, so the National Dex behind it is where every older Pokemon in the game is.
NATIONAL_DEX_THROUGH = 649

#: Every Generation 5 cartridge that trades with every other. All four share one Union Room and
#: one GTS, and the sequels trade with the originals as freely as with each other.
#:
#: A game declares the whole set whether or not the others are built yet: the registry holds an
#: edge back until both ends exist, so adding Black 2 later lights its routes up without anyone
#: editing Black.
CARTRIDGES = ("black", "white", "black-2", "white-2")


#: Where the sprites of all four Generation 5 games live in the sprite repository.
#:
#: One sheet for the whole generation, which is new: every generation before this one either
#: redrew itself for its third version, as Platinum did, or for its remakes, as HeartGold and
#: SoulSilver did. The sequels reuse these drawings exactly, so a player of any of the four saw
#: the same Pokemon.
#:
#: No ``transparent`` on the end, unlike Generations 1 and 2. Those sheets were palette images
#: with no alpha at all and every sprite arrived in a white box; these are 96x96 with a
#: transparency chunk, cut out the way Generation 3's and 4's already were.
#:
#: The animated sheet beside this one is the other thing these games are known for - Generation 5
#: is the only one whose battle sprites move - and it is not used: they are GIFs, the grid draws a
#: still picture, and a folder of animations nobody plays is megabytes in the exe for nothing.
SPRITE_SET = "generation-v/black-white"

#: PokeAPI's name for the 156-entry Unova dex, the one Black and White show.
#:
#: Named for the pair rather than for the region, because the sequels do not show it. Black 2
#: and White 2 have :data:`B2W2_DEX`, which is twice as long and keeps twelve of these numbers -
#: Victini through Watchog - before renumbering everything after them. So the two lists are not
#: one list with more at the end, the way Platinum's is Diamond's: they disagree about what
#: nearly every number means, as Johto's two dexes do.
BW_DEX = "original-unova"

#: PokeAPI's name for the 301-entry Unova dex, the one Black 2 and White 2 show.
#:
#: Not used yet - the sequels are not written. It is here so that the pair's dex has something
#: to be named apart from, which is the mistake this dataset has made before: a region with two
#: dexes and one constant called ``DEX``.
B2W2_DEX = "updated-unova"


def cartridge(
    *,
    game_id: str,
    title: str,
    version: str,
    released: date,
    sprite_set: str | None = None,
    pair_partner: str | None = None,
) -> Game:
    """One Generation 5 cartridge, with the facts all four of them share filled in."""
    return Game(
        id=game_id,
        title=title,
        version=version,
        generation=GENERATION,
        region=REGION,
        release=GameRelease.CARTRIDGE,
        released=released,
        national_dex_through=NATIONAL_DEX_THROUGH,
        dex_source=DexSource.NATIONAL_DEX,
        pair_partner=pair_partner,
        sprite_set=sprite_set,
    )


def link_trade_edges(game_id: str) -> list[TransferEdge]:
    """What this cartridge trades with, both ways and carrying anything it can hold.

    Only its own generation. Backwards is the Poke Transfer, which is one way and belongs to
    the receiver; forwards is Bank, which is not a game.
    """
    return [
        TransferEdge(
            **{"from": game_id},
            to=partner,
            mechanism=TransferMechanism.TRADE,
            direction=TransferDirection.BOTH_WAYS,
            filter=AllSpeciesFilter(),
        )
        for partner in CARTRIDGES
        if partner != game_id
    ]


def edges(game_id: str) -> list[TransferEdge]:
    """Every route one Generation 5 cartridge brings.

    Its trades, the Poke Transfer carrying Generation 4 into it, and Poke Transporter out to
    Bank. All three together for the reason :mod:`gb` gives: a game that declares its routes in
    two places grows one of them and not the other.

    This is where the cartridge chain ends. A Pokemon caught in Ruby reaches a living dex kept
    today by migrating into Generation 4, transferring into one of these four, and being sent to
    Bank from here - three one-way steps, in that order, and there is no fourth cartridge to
    move it onto. The Virtual Console releases reach Bank too, and by then they are the only
    other thing that does.
    """
    return [
        *link_trade_edges(game_id),
        *ds.poke_transfer_edges(into=game_id),
        bank.transporter_edge(game_id),
    ]


def handed_out(*events: str) -> str:
    """One sentence naming every distribution that ever handed this species out."""
    return exclusives.handed_out(*events)


def only_on(partner: str, event: str | None = None) -> str:
    """Why an entry in this dex is not in this half, when the other half has it."""
    return exclusives.only_on(partner, generation=GENERATION, event=event)


#: Dex entries neither half fills, and what step 7 found about each.
#:
#: Six, and every one of them is really in the game - which is what makes this generation's list
#: different from Sinnoh's or Kanto's. Nothing here is missing because the cartridge never held
#: it; it is missing because the door in front of it was a giveaway, and the giveaways are over.
#: Three of the six are the Mythical Pokemon this generation was built around, and the other
#: three are a Pokemon and the two it hides behind.
#:
#: Read off each species' own *In events* table rather than assumed, and the tables are worth
#: reading closely: a distribution that says "B2 W2" did not reach these two.
BW_UNOBTAINABLE: dict[str, str] = {
    "victini": exclusives.with_event(
        "Liberty Garden only opens with the Liberty Pass, which went out over Nintendo Wi-Fi in "
        "2011; the service closed in 2014",
        exclusives.handed_out(
            "the Movie 14 Victini over Wi-Fi from December 2011",
            "the Eind Victini in Japan before it",
        ),
    ),
    # The one entry in the six that no distribution ever covered anywhere. What was handed out
    # was the key rather than the Pokemon: a Celebi for the Generation 4 games, brought across
    # with the Relocator, which the man in Castelia City asks to see.
    "zorua": (
        "Only from the man in Castelia City, and only to a player carrying the event Celebi "
        "that was distributed for the Generation 4 games. No distribution ever handed out a "
        "Zorua for these two"
    ),
    "zoroark": exclusives.with_event(
        "Only in Lostlorn Forest, and only to a player carrying one of the shiny Raikou, Entei "
        "or Suicune distributed for the Generation 4 games",
        exclusives.handed_out(
            "the Summer 2011 Zoroark in Europe",
            "Zoroark Month in Australia and North America",
            "Pokemon Smash! in Japan before both",
        ),
    ),
    "keldeo": exclusives.with_event(
        "Nothing in Unova produces one; it was only ever given away",
        exclusives.handed_out(
            "the Summer 2012 Keldeo in shops from August 2012 to January 2013",
            "the Shokotan Keldeo in Japan and Taiwan before it",
        ),
    ),
    "meloetta": exclusives.with_event(
        "Nothing in Unova produces one; it was only ever given away",
        exclusives.handed_out(
            "the Spring 2013 Meloetta in shops",
            "the Cinema Meloetta in Japan, Taiwan and South Korea before it",
        ),
    ),
    # The sharpest of the six, and the reason step 7 reads the games column rather than counting
    # rows: Genesect was handed out plenty, and in the West every one of those was for the
    # sequels. A player of Black in Europe or America was never offered one at all.
    "genesect": exclusives.with_event(
        "Nothing in Unova produces one; it was only ever given away",
        exclusives.handed_out(
            "the P2 Laboratory Genesect in Japan and Taiwan in 2013",
            "the Cinema Genesect there the summer after",
        )
        + ", and no distribution outside Japan and South Korea ever covered these two rather "
        "than the sequels",
    ),
}


def bw_dex_entries(
    context: BuildContext,
    *,
    game_id: str,
    unobtainable: Mapping[str, str] | None = None,
) -> list[DexEntry]:
    """The Unova dex as Black and White number it: Victini #000 to Genesect #155.

    It starts at zero, which no other dex in this dataset does. Victini is #000 in both of
    these games and the app already prints three digits, so it shows up as ``#000`` exactly as
    the games do.

    And it is the 156 species Generation 5 added, all of them and nothing else - the whole
    block from Victini to Genesect, with no older Pokemon anywhere in it. That is unique in the
    series: a player of Black meets nothing they have seen before until the National Dex opens
    after the Elite Four, and until then the regional list is complete as it stands.

    Which makes the difference between this list and a living dex sharper here than anywhere
    else. A living dex in Black is 649 entries; this is 156 of them, and the other 493 are
    reachable only by trading or by the Poke Transfer. The entity says 649 and this says 156,
    and both are true.

    Nothing here carries a form yet. The questions the dex does raise are Deerling and Sawsbuck,
    who wear a season each; Basculin, whose two stripes are the same typing with different
    abilities; and Unfezant, Frillish and Jellicent, where the two sexes are drawn differently.
    All of them wait for the shared forms table, which is still empty, the way Burmy's cloaks do
    in Sinnoh. The formes this generation is best known for are not a question in these two at
    all - the Therian trio and Kyurem's fusions arrive with the sequels and the Reveal Glass.
    """
    return _dex_entries(context, game_id=game_id, dex=BW_DEX, unobtainable=unobtainable)


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


#: What these games call a place PokeAPI files under another name.
#:
#: One entry, and it is not a renaming at all but a misfiling: PokeAPI puts the roaming Tornadus
#: and Thundurus in the Team Flare Secret HQ, which is in Kalos, two generations away, and is not
#: a place either of these games has. Bulbapedia is plain about where they are - "Roaming Unova" -
#: and a player told to look in Kalos has been sent somewhere that does not exist for them.
#:
#: The same mechanism the Bell Tower needed in Johto, used for a different fault in the source.
RENAMED_PLACES = {"Team Flare Secret HQ": "Roaming Unova"}

#: The fossil each older Fossil revives into, and what the Nacrene Museum machine says about it.
#:
#: Seven of the nine are from earlier generations, and in these games they come from one place: a
#: Worker in Twist Mountain who hands out one a day once Ghetsis is beaten. So none of them is
#: reachable before the story ends, and no two of them on the same day.
_FROM_TWIST_MOUNTAIN = {
    "omanyte": "Helix Fossil",
    "kabuto": "Dome Fossil",
    "aerodactyl": "Old Amber",
    "lileep": "Root Fossil",
    "anorith": "Claw Fossil",
    "cranidos": "Skull Fossil",
    "shieldon": "Armor Fossil",
}

#: And the two this generation brought, which are a choice rather than a queue.
#:
#: A person in the Relic Castle offers one of the two and keeps the other, the way Mt. Moon has
#: offered the Helix or the Dome since Red and Blue. So a single save fills one of these two
#: entries and the other waits for a trade - which is not a version exclusive and looks exactly
#: like one.
_FROM_RELIC_CASTLE = {"tirtouga": "Cover Fossil", "archen": "Plume Fossil"}

#: Which first partner earns which monkey, from the woman outside the Dreamyard ruins.
#:
#: She hands over the one the player's own starter beats: a Tepig gets the Pansage. All three are
#: also in the rustling grass of Pinwheel Forest and Lostlorn Forest, so this decides which one is
#: free rather than which one is possible.
_MONKEY_FOR = {"pansage": "Tepig", "pansear": "Oshawott", "panpour": "Snivy"}

#: What only the game knows about each thing it hands over or leaves standing in one spot.
#:
#: One table for both halves. What they disagree about - which cover legendary is in the tower,
#: which of the forces of nature roams - PokeAPI already files per version, so none of it needs a
#: switch here.
BW_GIFTS: dict[str, GiftDetails] = {
    **{
        species: GiftDetail(
            kind=GiftKind.STARTER,
            npc="Professor Juniper",
            requirement="Pick one of the three; Cheren and Bianca take the other two",
        )
        for species in ("snivy", "tepig", "oshawott")
    },
    **{
        species: GiftDetail(
            npc="A woman outside the Dreamyard ruins",
            requirement=f"Only in a save that started with {starter}",
        )
        for species, starter in _MONKEY_FOR.items()
    },
    **{
        species: GiftDetail(
            kind=GiftKind.FOSSIL,
            npc="The museum's machine in Nacrene City",
            requirement=(
                f"Revived from the {fossil}, which a Worker in Twist Mountain hands out "
                "one a day once Ghetsis is beaten"
            ),
        )
        for species, fossil in _FROM_TWIST_MOUNTAIN.items()
    },
    **{
        species: GiftDetail(
            kind=GiftKind.FOSSIL,
            npc="The museum's machine in Nacrene City",
            requirement=(
                f"Revived from the {fossil}, one of the two a person in the Relic Castle "
                "offers; the other one stays with them"
            ),
        )
        for species, fossil in _FROM_RELIC_CASTLE.items()
    },
    "larvesta": GiftDetail(
        kind=GiftKind.EGG,
        npc="A Pokemon Ranger in a house on Route 18",
    ),
    "magikarp": GiftDetail(
        npc="The Magikarp salesman on Marvelous Bridge",
        requirement="Bought for 500 Pokedollars",
    ),
    # Not a gift and not quite a static either: it lies on the ground looking like a Poke Ball,
    # and picking it up starts a battle.
    **{
        species: GiftDetail(
            kind=GiftKind.STATIC_ENCOUNTER,
            requirement="Disguised as a Poke Ball lying on the ground",
        )
        for species in ("foongus", "amoonguss")
    },
    "musharna": GiftDetail(
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement="Every Friday, once Ghetsis is beaten",
    ),
    # The four that stood in the data with a place and a level and nothing about how to reach
    # them. PokeAPI carries no condition on any of these rows, and the place alone is not the
    # answer: three of the five are behind a door, and two of them behind each other.
    #
    # Read off Bulbapedia's *Swords of Justice* page and the two locations' own pages rather
    # than the species pages, which say only "Mistralton Cave" and "Relic Castle" - the same
    # thing PokeAPI says, and the same thing Pokemon Database says. Three sources agreeing about
    # the place is not three sources answering the question.
    "cobalion": GiftDetail(
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement="In the Guidance Chamber, which takes Surf to reach",
    ),
    # And these two do not exist until the first one has been walked up to, which is the part
    # no source but the page about all three of them says.
    "terrakion": GiftDetail(
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement="In the Trial Chamber, and only once Cobalion has been met",
    ),
    "virizion": GiftDetail(
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement="Only once Cobalion has been met in Mistralton Cave",
    ),
    # Not the postgame, which was the easy thing to assume: the cave opens when the crater
    # freezes over on the way in. What waits for the Hall of Fame is the second chance.
    "kyurem": GiftDetail(
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement=(
            "In the cave depths, on the first visit; if it faints or is run from it waits "
            "there again once the Hall of Fame is entered"
        ),
    ),
    "volcarona": GiftDetail(
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement=(
            "On the lowest floor, once Ghetsis is beaten; if it faints or is run from it "
            "waits there again once the Hall of Fame is entered"
        ),
    ),
    "landorus": GiftDetail(
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement="With Tornadus and Thundurus in the party",
    ),
    # The story's own Pokemon, and the only one in the dataset that is caught in the middle of
    # the final battle. If it faints there it waits at the top of Dragonspiral Tower instead,
    # which is the second row PokeAPI files and the one that needs the sentence.
    **{
        species: (
            GiftDetail(
                kind=GiftKind.STATIC_ENCOUNTER,
                where="N's Castle, Throne Room",
                requirement="During the last battle of the story",
            ),
            GiftDetail(
                kind=GiftKind.STATIC_ENCOUNTER,
                where="Dragonspiral Tower, 7F",
                requirement="Only if it was not caught at N's Castle",
            ),
        )
        for species in ("reshiram", "zekrom")
    },
    **{
        species: GiftDetail(
            kind=GiftKind.STATIC_ENCOUNTER,
            requirement=(
                "Roams Unova after the Legend Badge, once the storm on Route 7 has been walked "
                "into; the gates' bulletin boards say which route it is on"
            ),
        )
        for species in ("tornadus", "thundurus")
    },
}

#: Rows PokeAPI files under these games that a player of them cannot act on, and why.
#:
#: Three species and one place. The three are the generation's event Pokemon, and they are not a
#: disagreement about the data: each one is really there, behind a distribution that has ended.
#: The Liberty Pass went out over Nintendo Wi-Fi in 2011 and the service closed in 2014; the
#: Celebi that unlocks Zorua and the shiny beast that unlocks Zoroark were Generation 4 giveaways
#: brought across with the Relocator. A dex tile that says "Castelia City" to someone who cannot
#: get there is worse than one that says why they cannot - which is what step 7 will write.
#:
#: The place is a source error rather than a rule: PokeAPI lists the Friday Musharna twice, once
#: in the Dreamyard with the conditions and once in the basement without them, and Bulbapedia is
#: clear that there is one Musharna and it is in the basement.
BW_NOT_A_GIFT: dict[str, Exclusion] = {
    "victini": (
        "Liberty Garden only opens with the Liberty Pass, which was handed out over Nintendo "
        "Wi-Fi in 2011 and cannot be got today"
    ),
    "zorua": (
        "Only from the man in Castelia City, and only to a player carrying the event Celebi "
        "that was distributed for the Generation 4 games"
    ),
    "zoroark": (
        "Only in Lostlorn Forest, and only to a player carrying one of the shiny event beasts "
        "distributed for the Generation 4 games"
    ),
    "musharna": {
        "Dreamyard": (
            "one Musharna listed twice: it is in the basement, which is the other row PokeAPI "
            "files, and only that one is kept"
        )
    },
}


#: What PokeAPI calls the pair when it says which version group an evolution started in.
#:
#: One group for the two halves, as every pair in this dataset has. It is the group that brought
#: the trade evolutions this generation is awkward for - Boldore and Gurdurr both want a link
#: cable, and Karrablast and Shelmet only evolve by being traded for each other, which is two
#: players and not one.
BW_VERSION_GROUP = "black-white"

#: The four traders both halves have, and what each one wants.
#:
#: Small for a Unova game and every one of them worth something: two of the four are the only
#: way to a Rotom and a Munchlax here, neither of which is in this generation's dex at all.
#:
#: Nobody is named by the game as a trader; the name is the original trainer stamped on what
#: they hand over, which is the same name a player sees in the summary screen forever after.
BW_SHARED_TRADES = (
    # The stripe a player gets depends on which half they own, and this dataset has no form
    # table yet to hold that - so both halves record a Basculin and the difference waits.
    InGameTrade(gets="basculin", wants="minccino", location="Driftveil City", npc="Kyle"),
    InGameTrade(gets="emolga", wants="boldore", location="Route 7", npc="Manny"),
    InGameTrade(gets="rotom", wants="ditto", location="Route 15", npc="Lillian"),
    InGameTrade(
        gets="munchlax",
        wants="cinccino",
        location="Undella Town",
        npc="Ander",
        requirement="Only in summer",
    ),
)

#: And the fifth, which is the pair's own switch written as a trade.
#:
#: Dye swaps each half the other half's exclusive: Petilil for a Cottonee in Black, Cottonee for
#: a Petilil in White. So two of the six species that look like version exclusives are not - the
#: game hands them over itself, and step 7 has to know that before it writes anyone off.
BW_DYE_TRADE = {
    "black": InGameTrade(gets="petilil", wants="cottonee", location="Nacrene City", npc="Dye"),
    "white": InGameTrade(gets="cottonee", wants="petilil", location="Nacrene City", npc="Dye"),
}


#: The babies nothing in these games can be met as, and what has to be in the day care for one.
#:
#: Four, and they are four of fifteen. Unova's grass is full of grown-up Pokemon from earlier
#: generations - Clefable in the rustling grass of the Giant Chasm, Wigglytuff on Route 14 - and
#: their babies are nowhere, which is the opposite of Sinnoh, where the babies were in the grass
#: and the day care was not needed at all.
#:
#: The other eleven are left out on purpose. Pichu wants a Pikachu and there is no Pikachu here;
#: Togepi wants a Togetic, Elekid an Electabuzz, Happiny a Chansey, and this game produces none
#: of them. A record saying "hatch one" where the parent has to be traded in first is the lie the
#: no-breeding-dead-ends rule is watching for, so those wait for the transfer graph instead.
BW_EGGS: dict[str, EggFrom] = {
    "cleffa": EggFrom(parents=("clefairy", "clefable")),
    "igglybuff": EggFrom(parents=("jigglypuff", "wigglytuff")),
    "smoochum": EggFrom(parents=("jynx",)),
    # The one that costs money. Generation 4's babies each hide behind an incense, and a Chimecho
    # left in the day care lays another Chimecho without one - so this entry is not open until
    # the National Pokedex is, which is when the Driftveil Market starts selling it.
    "chingling": EggFrom(
        parents=("chimecho",),
        requirement=(
            "A parent has to hold a Pure Incense, which the Driftveil Market sells once the "
            "National Pokedex is open"
        ),
    ),
}


def bw_trades(version: str) -> tuple[InGameTrade, ...]:
    """The five this half offers, in the order a player meets them."""
    return (BW_DYE_TRADE[version], *BW_SHARED_TRADES)


def bw_acquisition_methods(
    context: BuildContext,
    *,
    game_id: str,
    version: str,
    entries: Sequence[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something in Black or White, with the pair's tables filled in.

    The halves differ by one word - which version PokeAPI is asked about - so one function
    answers for both and each game brings its own version name. Two copies of this is how one
    of them gets edited and the other does not.
    """
    return acquisition_methods(
        context,
        game_id=game_id,
        version=version,
        entries=entries,
        gifts=BW_GIFTS,
        excluded=BW_NOT_A_GIFT,
        version_group=BW_VERSION_GROUP,
        trades=bw_trades(version),
        eggs=BW_EGGS,
    )


def acquisition_methods(
    context: BuildContext,
    *,
    game_id: str,
    version: str,
    entries: Sequence[DexEntry],
    gifts: Mapping[str, GiftDetails] | None = None,
    excluded: Mapping[str, Exclusion] | None = None,
    version_group: str | None = None,
    trades: Sequence[InGameTrade] = (),
    eggs: Mapping[str, EggFrom] | None = None,
) -> list[AcquisitionMethod]:
    """Every way to get something in one Unova cartridge.

    Caught, handed over, traded for or evolved. A table left out is a step that has not run,
    not a game with nothing to declare.

    The species asked about are the whole living dex rather than the game's own Pokedex, and in
    these two that gap is the widest in the dataset: 156 entries against 649. Unova's postgame is
    where nearly all of the older species are, so asking only about the regional list would leave
    two thirds of what a player can actually catch here unrecorded.
    """
    api = context.require_api()
    species = context.living_dex(through=NATIONAL_DEX_THROUGH, entries=entries)
    today = date.today()
    # The wild and gift steps read the same encounter tables and walk into the same places, so
    # they share one lookup - and one correction: whatever the forces of nature are filed under,
    # both steps call it the same thing.
    places = LocationNames(api, refresh=context.refresh, renamed=RENAMED_PLACES)

    found: list[AcquisitionMethod] = [
        *wild_encounters(
            api,
            game_id=game_id,
            version=version,
            species=species,
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
                refresh=context.refresh,
            )
        )

    if eggs:
        found.extend(
            breeding_encounters(
                game_id=game_id,
                day_care=DAY_CARE,
                eggs=eggs,
                citation=bulbapedia("Pok%C3%A9mon_Day_Care", retrieved_on=today),
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
