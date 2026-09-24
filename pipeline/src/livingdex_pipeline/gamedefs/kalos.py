"""What the Kalos games have in common, whichever generation they are from.

X and Y are Generation 6 and a version pair, the way Diamond and Pearl are. They are not the
only games set here: Legends: Z-A is Lumiose City on the Switch, three generations later, and
it will read from this file too. So this module is about the place rather than about the
hardware that happened to be in a player's hands, and it is :mod:`johto` rather than
:mod:`kanto` that shows what that costs - a region whose games are two generations apart has to
keep every fact about a console, a dex limit or a trade set out of the file that names it.

The split is drawn the same way twice over:

* What is true of Kalos - its three Pokedexes, where the day care is, what walks in its grass -
  lives here, and a table that belongs to one pair rather than to the region says so in its
  name.
* What is true of the hardware and the generation - which games trade with which, how far the
  National Dex reaches, what the way out of the generation is - lives with the generation:
  :mod:`gen6` for X and Y, and whatever Generation 9 turns out to need for Z-A.

The factories are named for the generation for that reason. Nothing here should have to be
edited to add Z-A; something that does have to be edited is a fact about Generation 6 that has
been written down as a fact about Kalos.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from ..breeding import CAUGHT, breeding_encounters, day_care_eggs
from ..evolutions import evolution_encounters
from ..formchanges import FormChange, form_change_encounters, spread
from ..games import BuildContext
from ..gifts import GiftDetail, GiftDetails, RecordedGift, gift_encounters, recorded_gifts
from ..models import (
    AcquisitionMethod,
    DexEntry,
    DexTarget,
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
from . import exclusives, gen6

#: The region itself. Kalos and nothing else: unlike Johto, which hands a player Kanto after
#: the Elite Four, X and Y never leave it.
REGION = "Kalos"

#: Where an egg is left and collected. One building, on the route the first Snorlax sleeps on.
DAY_CARE = "Route 7, Pokemon Day Care"

#: Where the pair's own pictures live in the sprite repository.
#:
#: The first generation that has none. X and Y are in 3D: there is no battle sprite sheet to
#: take, and what stands in for one is a front-on shot of each model. It shows in the files -
#: every sheet before this one is a grid of one size, 64x64 in Generation 3 and 96x96 in
#: Generation 5, and these are cropped to whatever the Pokemon is: 43x48 for a Bulbasaur, 121x129
#: for a Rayquaza. The app draws them into a 56 pixel box and lets them keep their shape.
#:
#: Named for the pair rather than for the region or the generation. Omega Ruby and Alpha
#: Sapphire have a sheet of their own, and a Kalos game on the Switch will have neither.
XY_SPRITE_SET = "generation-vi/x-y"

#: The three Pokedexes X and Y show, as PokeAPI names them and as the games do.
#:
#: Three, not one, and this is the first game in the series to do it. A player is handed the
#: Central Kalos Pokedex in Lumiose City, the Coastal one at Ambrette Town and the Mountain one
#: at Anistar, and each numbers from #001 and shares not one species with the other two. There
#: is no fourth list that contains all of them: "the Kalos dex" is these three, and a number
#: without one of these names beside it means nothing here.
#:
#: In this order, which is the order a player is given them in rather than alphabetical or by
#: size - and the order the switch in the app will list them in.
DEXES: tuple[tuple[str, str], ...] = (
    ("kalos-central", "Central Kalos"),
    ("kalos-coastal", "Coastal Kalos"),
    ("kalos-mountain", "Mountain Kalos"),
)

#: How many entries the three hold between them: 153, 153 and 151.
#:
#: Four hundred and fifty-seven, of which the games ask for four hundred and fifty-four. The
#: three left over are Diancie, Hoopa and Volcanion, which sit at the end of the Central list
#: and are not counted towards completing it - the only entries in any dex in this dataset that
#: the game itself excuses a player from. What they are instead is step 7's business.
DEX_TOTAL = 457

#: What these games call a place PokeAPI spells without the punctuation.
#:
#: One so far, and it is the slug's doing rather than a disagreement between games: a sub-area
#: has no name of its own in PokeAPI and is generated from the URL, where an apostrophe cannot
#: live. Zygarde's Chamber is the room at the bottom of Terminus Cave.
RENAMED_SUB_AREAS = {"Zygardes Chamber": "Zygarde's Chamber"}

#: What a whole place asks of a player before any of its slots can be walked into.
#:
#: The Friend Safari is the hardest thing in this region to say honestly. PokeAPI files it as
#: eighteen ordinary areas full of ordinary tables, and it is nothing of the kind: it is in
#: Kiloude City, which opens after the Hall of Fame; what lives in a Safari is decided by the
#: friend code of a person registered on the player's own 3DS, so no two players see the same
#: list; and the percentage on each row is not how often that Pokemon turns up but how likely
#: that friend's Safari is to hold it at all. Three sentences, because a player told "Route 4,
#: 15%" and left to find out the rest is worse served than one told nothing.
#: The name PokeAPI and the games both give the eighteen areas in Kiloude City.
FRIEND_SAFARI = "Friend Safari"

PLACE_GATES: dict[str, str] = {
    FRIEND_SAFARI: (
        "Only in Kiloude City after the Hall of Fame, and only in the Safari of somebody "
        "registered on the 3DS friend list, whose friend code decides what it holds - so the "
        "percentage is how likely that Safari is to hold it, not how often it turns up"
    ),
}


#: The two fossils of this region, and which of the pair in the Glittering Cave revives into it.
_FROM_THE_GLITTERING_CAVE = {
    "tyrunt": ("Jaw Fossil", "Amaura"),
    "amaura": ("Sail Fossil", "Tyrunt"),
}

#: What X and Y know about the things they hand over that PokeAPI cannot say.
#:
#: Six starters is the first thing to notice. Kalos gives a player one of Chespin, Fennekin and
#: Froakie at a table in Aquacorde Town and then Professor Sycamore gives another of Bulbasaur,
#: Charmander and Squirtle in his Lumiose City lab - the first game since FireRed to hand over a
#: second one, and the reason two of the three Kanto lines are in a Kalos living dex without a
#: trade.
#:
#: What is not here is as deliberate. Lapras is handed over on Route 12 and this file says
#: nothing else about it, because nothing else about it has been read: the record still carries
#: the place and the level, which is what PokeAPI knows, and an invented NPC would be worse than
#: a blank. The legendary birds say nothing here either - what makes each of them appear is on
#: the encounter's own conditions, and a sentence written here would replace them.
XY_GIFTS: dict[str, GiftDetails] = {
    **{
        species: GiftDetail(
            kind=GiftKind.STARTER,
            requirement="Pick one of the three at the table in Aquacorde Town",
        )
        for species in ("chespin", "fennekin", "froakie")
    },
    **{
        species: GiftDetail(
            kind=GiftKind.STARTER,
            npc="Professor Sycamore",
            requirement="Pick one of the three he offers in his Lumiose City lab",
        )
        for species in ("bulbasaur", "charmander", "squirtle")
    },
    **{
        species: GiftDetail(
            kind=GiftKind.FOSSIL,
            requirement=(
                f"Revived at the Ambrette Town Fossil Lab from the {fossil}, one of the two "
                f"offered in the Glittering Cave; the other one is {other}'s"
            ),
        )
        for species, (fossil, other) in _FROM_THE_GLITTERING_CAVE.items()
    },
    "lucario": GiftDetail(
        npc="Korrina",
        requirement=(
            "Kept after the one-on-one battle atop the Tower of Mastery that follows her Gym, "
            "win or lose; it is holding the Lucarionite"
        ),
    ),
    "snorlax": GiftDetail(
        requirement=(
            "Asleep on the bridge, and woken with the Poke Flute borrowed at Parfum Palace; if "
            "it is knocked out rather than caught it comes back after the Hall of Fame"
        ),
    ),
}


#: What PokeAPI calls the pair when it says which version group an evolution started in.
XY_VERSION_GROUP = "x-y"

#: The six traders both halves have, in the order a player meets them.
#:
#: Two of the six will take anything in the party, which is new: an in-game trade has always
#: been a swap of one named species for another, and Diantha and the woman in the hotels simply
#: want something. Both of those hand over a held item worth more than the Pokemon - the
#: Gardevoirite and a Rare Candy - and the Magikarp one is a joke at the player's expense: a
#: level 5 Magikarp for the Gyarados it becomes.
XY_TRADES = (
    InGameTrade(gets="farfetchd", wants="bunnelby", location="Santalune City", npc="Cliff"),
    InGameTrade(gets="steelix", wants="luvdisc", location="Cyllage City", npc="Farris"),
    InGameTrade(gets="bisharp", wants="jigglypuff", location="Snowbelle City", npc="Punky"),
    InGameTrade(
        gets="ralts",
        location="Lumiose City",
        npc="Diantha",
        requirement="She takes anything in the party; the Ralts is holding the Gardevoirite",
    ),
    InGameTrade(gets="magikarp", wants="gyarados", location="Kalos hotels", npc="Caveat"),
    InGameTrade(
        gets="eevee",
        location="Kalos hotels",
        npc="Elena",
        requirement="She takes anything in the party; the Eevee is holding a Rare Candy",
    ),
)

#: Which of the three Shauna offers, and what a save had to start with to be offered it.
#:
#: She takes the first partner your own is strong against and hands it back in Vaniville Town at
#: the end, so a save reaches two of the three - its own and hers - and the third is in neither
#: game by any means at all. That is the closest thing X and Y have to a version exclusive that
#: is not one: it divides saves rather than cartridges.
SHAUNA_TRADE = {"fennekin": "chespin", "froakie": "fennekin", "chespin": "froakie"}


def xy_trades() -> tuple[InGameTrade, ...]:
    """The six both halves share, and the three shapes Shauna's one trade can take."""
    return (
        *XY_TRADES,
        *(
            InGameTrade(
                gets=hers,
                location="Vaniville Town",
                npc="Shauna",
                requirement=(
                    f"She takes anything in the party, and only in a save that started with "
                    f"{yours.title()}: she picks the first partner yours is strong against"
                ),
            )
            for yours, hers in SHAUNA_TRADE.items()
        ),
    )


#: The one thing in these games PokeAPI has no encounter for at all.
#:
#: Aerodactyl is #068 in the Coastal Kalos dex and the encounter tables have nothing for it in
#: either half - which read as an entry neither game can fill, and would have been the only such
#: entry in the region that was not a Mythical. It is simply missing: the Fossil Lab in Ambrette
#: Town revives an Old Amber like any other fossil, and the Old Amber is in the Glittering Cave,
#: under a rock, for anyone who has Rock Smash.
#:
#: Written by hand and cited to the pages it was read on, the same last resort the Bug-Catching
#: Contest needed in Johto - and with the same warning: nothing re-fetches this, so it goes
#: stale without saying so.
XY_HANDED_OVER = (
    RecordedGift(
        species="aerodactyl",
        kind=GiftKind.FOSSIL,
        location="Ambrette Town, Fossil Lab",
        requirement=(
            "Revived from the Old Amber, which is under a rock in the Glittering Cave and takes "
            "Rock Smash to get at"
        ),
    ),
)


#: Dex entries neither half fills, and what step 7 found about each.
#:
#: Three, and they are the three the Central Kalos list holds without asking for them: Diancie,
#: Hoopa and Volcanion sit at #151 to #153 and do not count towards completing it. The games
#: know they cannot be caught, which is why a player is excused - and the dataset says so anyway,
#: because a living dex asks for all 721 whatever the regional list requires.
#:
#: All three were given away and nothing else, which is the cleanest case step 7 ever meets: no
#: cave to search, no version to trade with, and a date that has passed. Every distribution went
#: to X and Y alike, and most of them to Omega Ruby and Alpha Sapphire as well.
XY_UNOBTAINABLE: dict[str, str] = {
    "diancie": exclusives.with_event(
        "Nothing in Kalos produces one; it was only ever given away",
        exclusives.handed_out(
            "the Cinema Diancie in Japan from July 2014",
            "the October 2014 Diancie in America",
            "the November 2014 Diancie in Europe",
        ),
    ),
    "hoopa": exclusives.with_event(
        "Nothing in Kalos produces one; it was only ever given away",
        exclusives.handed_out(
            "the Cinema Hoopa in Japan from July 2015",
            "the Manesh Hoopa in Japan and America",
            "the Harry Hoopa in Europe",
        ),
    ),
    "volcanion": exclusives.with_event(
        "Nothing in Kalos produces one; it was only ever given away",
        exclusives.handed_out(
            "the Nebel Volcanion in Japan from April 2016",
            "the Helen Volcanion in Europe and America from that October",
        ),
    ),
}


def handed_out(*events: str) -> str:
    """One sentence naming every distribution that ever handed this species out."""
    return exclusives.handed_out(*events)


def with_event(reason: str, event: str | None) -> str:
    """One reason, with what step 7 found about it added as a second sentence."""
    return exclusives.with_event(reason, event)


#: How each of this pair's forms is come by, keyed by form.
#:
#: Kalos is the first region where this is most of a step rather than a footnote. X and Y hold
#: 199 forms between them, and the families that are new here - Vivillon's patterns, Furfrou's
#: trims, Flabebe's colours, Pumpkaboo's sizes - are settled when the Pokemon is generated and
#: cannot be changed afterwards at all. What a player can act on is where to look and what to
#: breed, so that is what these sentences say.
#:
#: The four items that change an older legendary are all in these games, and every one of them
#: is handed over for showing the legendary itself - which a Kalos save can only have by
#: transfer. So the Reveal Glass, the DNA Splicers, the Griseous Orb and the Gracidea are each a
#: favour done for a Pokemon that came from somewhere else.
XY_FORM_CHANGES: dict[str, FormChange] = {
    **spread(
        FormChange(
            requirement="Touch one of the meteorites there; they cycle through all four formes",
            where="Ambrette Town, Fossil Lab",
        ),
        "deoxys-attack",
        "deoxys-defense",
        "deoxys-speed",
    ),
    # The forces of nature, and the one item a player has to bring all three of them to.
    **spread(
        FormChange(
            requirement=(
                "Use the Reveal Glass on it, which a Scientist near the Shalour City exit hands "
                "over for being shown Tornadus, Thundurus and Landorus - none of which Kalos has"
            ),
            where="Reflection Cave",
        ),
        "tornadus-therian",
        "thundurus-therian",
        "landorus-therian",
    ),
    "kyurem-black": FormChange(
        requirement=(
            "Fuse it with Zekrom using the DNA Splicers, which a Punk Girl in Kiloude City hands "
            "over for being shown a Kyurem; the fusion can be undone again"
        ),
    ),
    "kyurem-white": FormChange(
        requirement=(
            "Fuse it with Reshiram using the DNA Splicers, which a Punk Girl in Kiloude City "
            "hands over for being shown a Kyurem; the fusion can be undone again"
        ),
    ),
    "giratina-origin": FormChange(
        requirement="While it holds the Griseous Orb, which lies in Terminus Cave",
    ),
    "shaymin-sky": FormChange(
        requirement=(
            "Use the Gracidea on it, which the Snowbelle City Pokemon Center hands over for "
            "being shown a Shaymin; it turns back at night and in a box"
        ),
    ),
    "keldeo-resolute": FormChange(
        requirement=(
            "While it knows Secret Sword, which the Swords of Justice teach it at the Pledge "
            "Grove in Unova and which it keeps wherever it goes afterwards"
        ),
    ),
    # Burmy's cloak is the terrain of its last battle, which is something a player can do here
    # even though no Burmy is caught in Kalos. Wormadam's is fixed at the moment it evolves.
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
#:
#: Keyed by species rather than by listing nineteen Vivillon patterns and nine Furfrou trims: the
#: answer is the same for every one of them, and a list that long is a list to get wrong.
XY_FORM_CHANGES_BY_SPECIES: dict[str, FormChange] = {
    # The one that is a fact about the console rather than about the game.
    "vivillon": FormChange(
        requirement=(
            "Its pattern is the one the 3DS's own country and region give, settled when the "
            "Scatterbug is generated; one console reaches one of the eighteen and the rest come "
            "by trading. Fancy and Poke Ball were only ever handed out at events"
        ),
    ),
    # And the one that cannot be kept at all, which is worth saying out loud: a trim lasts five
    # days and is lost the moment the Furfrou is put in a box, so no living dex can hold one.
    "furfrou": FormChange(
        requirement=(
            "Have it groomed at Friseur Furfrou, which keeps the trim for five days and loses it "
            "the moment the Furfrou is put in a box - and in X and Y a trim is not a Pokedex "
            "entry of its own"
        ),
        where="Lumiose City",
    ),
    **spread(
        FormChange(
            requirement=(
                "Catch one holding that colour of flower, or hatch one from a mother that holds "
                "it; the colour carries through both evolutions and cannot be changed"
            ),
        ),
        "flabebe",
        "floette",
        "florges",
    ),
    **spread(
        FormChange(
            requirement=(
                "Catch one that size on Route 16, which holds all four, or hatch one from a "
                "mother of it; the size carries through the trade it evolves by"
            ),
        ),
        "pumpkaboo",
        "gourgeist",
    ),
    # Seasons ended with Generation 5, so Kalos has one coat in its grass and three that can
    # only be bred or brought over.
    **spread(
        FormChange(
            requirement=(
                "Kalos has no seasons: every wild one wears the spring coat, and the other three "
                "only hatch from a mother wearing one or come over from Generation 5"
            ),
        ),
        "deerling",
        "sawsbuck",
    ),
    "rotom": FormChange(
        requirement="Let it possess one of the appliances in the boxes there",
        where="Lumiose City, Sycamore Pokemon Lab 2F",
    ),
}

#: Forms this pair holds and has no way of producing, left without a record on purpose.
#:
#: The Eternal Flower Floette is AZ's and no game has ever handed one over. Unown's letters,
#: Basculin's stripe and Shellos's sea are settled where the Pokemon is caught, and none of those
#: three is caught in Kalos - so what a player brings in is what they keep, and there is nothing
#: here to tell them to do. A form with no sentence gets no record rather than a guessed one.
XY_NO_WAY_HERE = frozenset(
    {"floette-eternal", "basculin-blue-striped", "shellos-east", "gastrodon-east"}
)


def xy_form_changes(forms: Sequence[Form]) -> dict[str, FormChange]:
    """One sentence for every form given that has one, and nothing for the rest.

    Built from the forms rather than handed back whole, so what comes out is about the game
    that asked: a table keyed by id and a table keyed by species, with the id winning where
    both have something to say.
    """
    changes: dict[str, FormChange] = {}

    for form in forms:
        if form.id in XY_NO_WAY_HERE:
            continue

        change = XY_FORM_CHANGES.get(form.id) or XY_FORM_CHANGES_BY_SPECIES.get(form.species)
        if change is not None:
            changes[form.id] = change

    return changes


def gen6_cartridge(
    *,
    game_id: str,
    title: str,
    version: str,
    released: date,
    pair_partner: str,
    sprite_set: str | None = None,
) -> Game:
    """One Kalos cartridge of Generation 6: a Generation 6 cartridge that happens to be set here.

    Named for the generation rather than called ``cartridge`` outright, for the reason
    :mod:`johto` gives: Z-A is a Kalos game as well and none of what :mod:`gen6` fills in is
    true of it. It will get a factory of its own beside this one, reading its own generation's
    module, and the region is the one argument both will pass.

    ``pair_partner`` is required: X and Y have no third version, so a Generation 6 cartridge
    here always has another half.
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
    """Every route one of the pair brings: its own generation's trades, and Bank both ways.

    Named for the generation too, and this is the half of the split that would go wrong
    quietest. A Kalos game reaches Bank; Z-A reaches HOME, which is a different service with a
    different set of games behind it, and a route written down here as "what a Kalos game does"
    would be handed to it without anybody looking.
    """
    return gen6.edges(game_id)


def gen6_dex_entries(
    context: BuildContext,
    *,
    game_id: str,
    unobtainable: Mapping[str, str] | None = None,
) -> list[DexEntry]:
    """All three Kalos Pokedexes, each entry saying which of them it is numbered in.

    One call, three lists, kept apart. Every game before these two had a single Pokedex and an
    entry's number needed no more explanation than the game's name; here #001 is Chespin in
    Central Kalos, Drifloon in Coastal and Diglett in Mountain, and an entry that does not say
    which list it belongs to is not a fact about anything.

    The order is the order the games hand them over, and it is kept: a reader of the file, and
    the switch in the app, sees Central, then Coastal, then Mountain.

    Nothing here carries a form. The Kalos lists number species, and what the region raises -
    Vivillon's twenty patterns, Furfrou's nine trims, Flabebe's five colours, Meowstic and
    Pyroar drawn differently by sex - is in the shared forms table already, waiting for step 8
    to say how each one is come by.
    """
    reasons = unobtainable or {}
    api = context.require_api()

    return [
        DexEntry(
            game=game_id,
            target=DexTarget(species=species),
            dex=name,
            number=number,
            unobtainable_reason=reasons.get(species),
        )
        for dex, name in DEXES
        for number, species in api.pokedex(dex, refresh=context.refresh)
    ]


#: Why the Friend Safari's slots are real and still do not count as a way to get one.
#:
#: The tables are true and a player with the right friend can walk into them. What they cannot
#: do is be told to: a Safari holds what somebody else's friend code decided, there is no way to
#: choose which one, and a third of every Safari has been shut since the 3DS network closed. So
#: the rows are kept and shown, and the dataset does not answer "yes, in X" on their strength -
#: which would tell a player of X they can have a Spritzee when what they can have is a friend
#: who might.
#:
#: This is the first place in the dataset that is recorded and not counted. Everything before it
#: was one or the other.
FRIEND_SAFARI_DOES_NOT_COUNT = (
    "A Friend Safari holds what somebody else's friend code decided, and there is no choosing "
    "which; the dataset does not count it as a way to get one here"
)

NOT_COUNTED: dict[str, str] = {FRIEND_SAFARI: FRIEND_SAFARI_DOES_NOT_COUNT}


def gen6_acquisition_methods(
    context: BuildContext,
    *,
    game_id: str,
    version: str,
    entries: Sequence[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something in one Kalos cartridge: caught, handed over, traded for,
    evolved.

    The species asked about are the whole living dex rather than the three Kalos Pokedexes: a
    player of X is filling 721 entries and a good deal of what fills them is caught in Kalos
    without being listed in any of its three regional lists.
    """
    api = context.require_api()
    species = context.living_dex(through=gen6.NATIONAL_DEX_THROUGH, entries=entries)
    wanted = set(species)
    places = LocationNames(api, refresh=context.refresh, renamed_sub_areas=RENAMED_SUB_AREAS)

    found: list[AcquisitionMethod] = [
        *wild_encounters(
            api,
            game_id=game_id,
            version=version,
            species=species,
            forms=context.forms_here(),
            refresh=context.refresh,
            places=places,
            gates=PLACE_GATES,
            not_counted=NOT_COUNTED,
        ),
        *gift_encounters(
            api,
            game_id=game_id,
            version=version,
            species=species,
            details=XY_GIFTS,
            refresh=context.refresh,
            places=places,
        ),
        *evolution_encounters(
            api,
            game_id=game_id,
            version_group=XY_VERSION_GROUP,
            species=species,
            forms=context.forms_here(),
            all_forms=context.forms,
            refresh=context.refresh,
        ),
        *recorded_gifts(
            game_id=game_id,
            gifts=XY_HANDED_OVER,
            species=species,
            citation=bulbapedia("Old_Amber", retrieved_on=date.today()),
        ),
        *trade_encounters(
            game_id=game_id,
            trades=xy_trades(),
            citation=bulbapedia("In-game_trade", retrieved_on=date.today()),
        ),
    ]

    # Last, and from what the four steps above came to rather than from a table: the day care
    # can only be asked for what nothing else here produces, so it cannot be worked out until
    # everything else has been.
    found.extend(
        breeding_encounters(
            game_id=game_id,
            day_care=DAY_CARE,
            eggs=day_care_eggs(
                api,
                chains={one.id: one.evolution_chain for one in context.species if one.id in wanted},
                caught={
                    one.target.species
                    for one in found
                    if one.kind in CAUGHT and getattr(one, "does_not_count", None) is None
                },
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
            changes=xy_form_changes(context.forms_here()),
            citation=bulbapedia(
                "List_of_Pok%C3%A9mon_with_form_differences", retrieved_on=date.today()
            ),
        )
    )

    return found


def gen6_only_on(partner: str, event: str | None = None) -> str:
    """Why an entry in the Kalos dexes is not in this half of the pair.

    Named for the generation like the factories above it, and for the same reason: a Kalos game
    on the Switch would be saying "Generation 6" to a player who is not playing one.
    """
    return gen6.only_on(partner, event)
