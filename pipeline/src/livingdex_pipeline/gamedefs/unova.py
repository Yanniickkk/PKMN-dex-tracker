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
from ..formchanges import FormChange, form_change_encounters, spread
from ..games import BuildContext
from ..gifts import Exclusion, GiftDetail, GiftDetails, gift_encounters
from ..grottoes import grotto_encounters
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
#: Named apart from :data:`BW_DEX` rather than called ``DEX``, which is the mistake this dataset
#: has made before: a region with two dexes and one constant for both of them.
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


def only_on(partners: Sequence[str] | str, event: str | None = None) -> str:
    """Why an entry in this dex is not in this game, and which of the other three has it.

    Several games rather than one, which is what four cartridges in one generation does to a
    version exclusive. Black's Zekrom is in White, as it always was, and since the sequels were
    written it is in Black 2 as well - so the answer to "where do I get one" grew a second half
    without anything about Black changing. Naming only the pair partner would leave a player
    with a Black 2 in the drawer looking for a trade they do not need.
    """
    named = partners if isinstance(partners, str) else _listed(partners)

    return exclusives.only_on(named, generation=GENERATION, event=event)


def _listed(names: Sequence[str]) -> str:
    if len(names) < 3:
        return " and ".join(names)

    return f"{', '.join(names[:-1])} and {names[-1]}"


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


#: Dex entries neither sequel fills, and what step 7 found about each.
#:
#: Seven where the first pair has six, and the two lists overlap in only three names. Reading
#: Black's answers into Black 2 would have been wrong about four of the seven, in both
#: directions: Zorua and Zoroark are simply handed over here, and three Pokemon that walk about
#: freely in the first pair cannot be met in these two at all.
#:
#: Those three are the forces of nature, and they are the sharpest thing this step turned up.
#: They are not behind a distribution that ended - they are behind another game. The Pokemon
#: Dream Radar is a 3DS download that sends what it catches down into these two cartridges and
#: into nothing else, and it is the only way any of the three reaches Unova a second time.
#:
#: Read off each species' own *In events* table, and the tables repay the reading twice over:
#: Victini and Genesect swap places between the two pairs.
B2W2_UNOBTAINABLE: dict[str, str] = {
    # The mirror of the first pair's Genesect, and the reason step 7 reads the games column.
    # Victini is not shut behind a distribution here - it is not in the game at all, because
    # Liberty Garden is not on the sequels' map. Exactly one distribution ever reached these two
    # and it was in Japanese, in Japan, for six weeks.
    "victini": exclusives.with_event(
        "Liberty Garden is not on the sequels' map, and nothing else here produces one",
        exclusives.handed_out("the Pokemon Center Tohoku Victini in Japan over the winter of 2012")
        + ", and every other Victini distribution was for the first pair rather than these two",
    ),
    "keldeo": exclusives.with_event(
        "Nothing in Unova produces one; it was only ever given away",
        exclusives.handed_out(
            "the Winter 2013 Keldeo over Wi-Fi",
            "the Shokotan Keldeo in Japan and Taiwan before it",
            "the Sacred Swordsman Keldeo in South Korea",
        ),
    ),
    "meloetta": exclusives.with_event(
        "Nothing in Unova produces one; it was only ever given away",
        exclusives.handed_out(
            "the Spring 2013 Meloetta in Europe, the Americas and Australia",
            "the Cinema Meloetta in Japan, Taiwan and South Korea before it",
        ),
    ),
    # And the other half of the mirror. The first pair was never offered a Genesect outside
    # Japan and South Korea; these two were offered one everywhere, over Wi-Fi, five weeks after
    # they came out in the West.
    "genesect": exclusives.with_event(
        "Nothing in Unova produces one; it was only ever given away",
        exclusives.handed_out(
            "the Plasma Genesect over Wi-Fi in the autumn of 2012",
            "the P2 Laboratory Genesect in Japan and Taiwan",
            "the Cinema Genesect there the summer after",
        ),
    ),
    # The three that are behind another game rather than behind a date. Tornadus and Thundurus
    # roam the first pair's Unova and are nowhere in the sequels' - what replaced them is the
    # Pokemon Dream Radar, which is a Nintendo 3DS download rather than a cartridge, has no dex
    # of its own, and sends one way into these two and nowhere else. It is written down as a
    # Phase 3 item; until it is, this is the honest answer.
    **{
        species: (
            "Only from the Pokemon Dream Radar, a Nintendo 3DS download that sends into these "
            "two and nowhere else. No distribution ever handed one out for them"
        )
        for species in ("tornadus", "thundurus")
    },
    # And the third waits on the other two, so the Radar is two steps back rather than one.
    "landorus": (
        "Only at the Abundant Shrine, and only with Tornadus and Thundurus in the party - both "
        "of which the Pokemon Dream Radar is the only source of here. No distribution ever "
        "handed one out for these two"
    ),
}


def b2w2_dex_entries(
    context: BuildContext,
    *,
    game_id: str,
    unobtainable: Mapping[str, str] | None = None,
) -> list[DexEntry]:
    """The Unova dex as Black 2 and White 2 number it: Victini #000 to Genesect #300.

    Twice the length of the list the first pair showed, and it starts at zero the same way.
    Every one of those 156 is still in it - nothing was dropped when the region was revisited -
    and the 145 it adds are all from older generations: 38 from Generation 1, 32 from
    Generation 2, 43 from Generation 3 and 32 from Generation 4. So the difference is one of
    kind rather than of size. Black and White showed a regional dex with no older Pokemon
    anywhere in it, which nothing else in the series has done; the sequels put the series back
    the way it has always been, in the same region, two years later.

    Which makes the two lists disagree almost everywhere. Twelve numbers survive - Victini
    through Watchog, the first pair's #000 to #011 - and from #012 they part: Black has
    Lillipup there and Black 2 has Purrloin. That is Johto's situation rather than Platinum's.
    Platinum's dex is Diamond's with more on the end, so a number means the same thing in both;
    here a number means two different things, and a dataset with one constant called ``DEX``
    would have quietly said otherwise.

    A living dex is still 649, and this is 301 of them. The gap is narrower than the first
    pair's - 156 against 649 - and it is the same kind of gap: what the regional list leaves out
    is not unobtainable, it is simply not what the game numbers.

    Nothing here carries a form yet, and the sequels add to the queue rather than shorten it.
    The first pair's questions are all still open - Deerling and Sawsbuck with a season each,
    Basculin's two stripes, the drawn-apart sexes of Unfezant, Frillish and Jellicent - and
    these two bring the formes this generation is remembered for: the Therian trio through the
    Reveal Glass, Kyurem's two fusions through the DNA Splicers, and Keldeo's Resolute form. All
    of them wait for the shared forms table, which is still empty.
    """
    return _dex_entries(context, game_id=game_id, dex=B2W2_DEX, unobtainable=unobtainable)


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
#: Two entries, and neither is a renaming of the kind the Bell Tower needed - where two games
#: genuinely called one place different things. Both are the source being wrong.
#:
#: The first is a misfiling: PokeAPI puts the roaming Tornadus and Thundurus in the Team Flare
#: Secret HQ, which is in Kalos, two generations away, and is not a place either of the first
#: pair has. Bulbapedia is plain about where they are - "Roaming Unova" - and a player told to
#: look in Kalos has been sent somewhere that does not exist for them.
#:
#: The second is a name nobody was ever shown. PokeAPI's English for the forest the sequels hide
#: behind the regional dex is "Nature Sanctuary", which is its Japanese name carried across; the
#: English games call it the Nature Preserve, and Bulbapedia's "Nature Sanctuary" is a redirect
#: to that page rather than an article of its own. It is the only place in these four games that
#: no player could search a guide for under the name the dataset would have printed.
RENAMED_PLACES = {
    "Team Flare Secret HQ": "Roaming Unova",
    "Nature Sanctuary": "Nature Preserve",
}

#: And one below a location, where the fault is a different one.
#:
#: A location's English name was written by a person; a sub-area's is generated from the slug,
#: so nobody ever read it. The building on Route 6 where a scientist studies what the seasons do
#: to Deerling is the Season Research Lab, and the slug calls it ``weather-institute``, which is
#: a building in Hoenn. "Route 6, Weather Institute" sends a player to another region for
#: something standing in front of them.
RENAMED_SUB_AREAS = {"Weather Institute": "Season Research Lab"}

#: A door a whole place is behind, which PokeAPI has no way of writing down.
#:
#: Conditions in the source hang on a row of an encounter table, so they can say "only while it
#: is swarming" and cannot say "only if you are allowed in here at all". The Nature Preserve is
#: the case that makes the difference matter: its tables are ordinary grass and water, twenty-
#: four slots of nothing unusual, and eight of the species in them are nowhere else in the game.
#: Kecleon is nowhere else in the generation.
#:
#: What it takes is the Permit, which Professor Juniper hands over for *seeing* - not catching -
#: every entry in the sequels' 301-entry dex except the four Mythical Pokemon. So it is the last
#: thing a player does rather than something they can plan around, and a record that says
#: "Nature Preserve, dark grass, 10%" without saying so is telling them to walk somewhere there
#: is no road to.
PLACE_GATES: dict[str, str] = {
    "Nature Preserve": (
        "Only by plane from Mistralton City, with the Permit Professor Juniper hands over for "
        "seeing all 297 entries in the sequels' dex that are not Mythical"
    ),
}

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


#: The Kanto, Hoenn and Sinnoh fossils, and what the sequels do differently with them.
#:
#: Still revived by the museum's machine in Nacrene City, and no longer a queue with an order to
#: it: a Worker in Twist Mountain hands out one a day and which one is random, so a player after
#: a particular one is soft-resetting rather than waiting a particular number of days. The gate
#: moved too - the National Dex rather than Ghetsis, which is a later door than the first pair's.
_B2W2_FROM_TWIST_MOUNTAIN = {
    "omanyte": "Helix Fossil",
    "kabuto": "Dome Fossil",
    "aerodactyl": "Old Amber",
    "lileep": "Root Fossil",
    "anorith": "Claw Fossil",
    "cranidos": "Skull Fossil",
    "shieldon": "Armor Fossil",
}

#: And Unova's own two, which stopped being a choice a save has to live with.
#:
#: Still one or the other in Nacrene City, as the Relic Castle offered one or the other in the
#: first pair. What is new is that the one left behind can be bought afterwards, in an Antique
#: Shop on Join Avenue - so both entries are fillable in a single save here, and in Black and
#: White the other one waits for a trade. Same two species, same choice, opposite answer.
_B2W2_FROM_NACRENE = {"tirtouga": "Cover Fossil", "archen": "Plume Fossil"}

#: The weekly visitors, per half, and the day each one turns up on.
#:
#: Two of them in each game and both are mirrored: the bird of prey that half keeps stands on
#: Route 4, and a Jellicent surfaces in Undella Bay. A player who reads "Route 4, level 25" and
#: goes on a Tuesday finds nothing at all, and nothing in the source says why - PokeAPI carries
#: no condition on either row.
_WEEKLY = {
    "black-2": {"mandibuzz": "Thursday", "jellicent": "Monday"},
    "white-2": {"braviary": "Monday", "jellicent": "Thursday"},
}

#: Which key catching Regirock hands this half, and which one it has to be sent.
#:
#: The one place in this dataset where a species is obtainable and still needs another cartridge.
#: Catching Regirock is rewarded with a key, and it is the wrong key for the other chamber:
#: Black 2 is given the Iron Key and White 2 the Iceberg Key, so Regice in Black 2 and Registeel
#: in White 2 both wait on a key sent over the Unova Link from a copy of the other game. That is
#: not a trade and not a version exclusive, and it looks exactly like both.
_KEYS = {
    "black-2": ("Iron Key", "registeel", "regice", "White 2"),
    "white-2": ("Iceberg Key", "regice", "registeel", "Black 2"),
}

_CHAMBER = {"registeel": ("Iron Chamber", "Iron Key"), "regice": ("Iceberg Chamber", "Iceberg Key")}

#: What only the game knows about each thing it hands over or leaves standing in one spot.
#:
#: One table for both halves, as the first pair has. What they disagree about - which bird is on
#: Route 4, which of the eon duo is in the Dreamyard, which stone is at Dragonspiral Tower -
#: PokeAPI files per version already, so only the day of the week needs a switch here.
#:
#: The Swords of Justice are missing from it on purpose. They moved out of their chambers and
#: onto Routes 11, 13 and 22, nothing in the source conditions the first row, and the page about
#: all three says nothing about an order this time - so the place and the level are the whole
#: answer, and a sentence would be an invention. The same goes for Volcarona, whose two rows
#: PokeAPI does condition, correctly and in the right order.
B2W2_GIFTS: dict[str, GiftDetails] = {
    **{
        species: GiftDetail(
            kind=GiftKind.STARTER,
            npc="Bianca",
            requirement="Pick one of the three she brings to the Aspertia City outlook",
        )
        for species in ("snivy", "tepig", "oshawott")
    },
    **{
        species: GiftDetail(
            kind=GiftKind.FOSSIL,
            npc="The museum's machine in Nacrene City",
            requirement=(
                f"Revived from the {fossil}, which a Worker in Twist Mountain hands out one a "
                "day once the National Dex has been received; which fossil it is is random"
            ),
        )
        for species, fossil in _B2W2_FROM_TWIST_MOUNTAIN.items()
    },
    **{
        species: GiftDetail(
            kind=GiftKind.FOSSIL,
            npc="The museum's machine in Nacrene City",
            requirement=(
                f"Revived from the {fossil}, one of the two offered in Nacrene City; the other "
                "one can be bought later at an Antique Shop on Join Avenue"
            ),
        )
        for species, fossil in _B2W2_FROM_NACRENE.items()
    },
    "happiny": GiftDetail(
        kind=GiftKind.EGG,
        npc="A Pokemon Breeder in the Nacrene Gate",
    ),
    "deerling": GiftDetail(
        npc="A scientist in the Season Research Lab on Route 6",
        requirement="Wears whichever season the game is in when it is handed over",
    ),
    "eevee": GiftDetail(
        npc="Amanita, on the third floor of the Game Freak building in Castelia City",
        requirement="After the Hall of Fame; it is always male and has its Hidden Ability",
    ),
    "magikarp": GiftDetail(
        npc="The Magikarp salesman on Marvelous Bridge",
        requirement="Bought for 500 Pokedollars",
    ),
    # N's own, handed over rather than caught - and the whole reason this entry reads
    # differently in the sequels than in the first pair, where it took an event Celebi nobody
    # can be given any more.
    "zorua": GiftDetail(
        npc="Rood, at Team Plasma's safehouse in Driftveil City",
        requirement="N's Zorua, offered for adoption once Rood has been battled",
    ),
    # The two the postgame tower hands out, and the only shiny Pokemon in this dataset that a
    # player is simply given. Which of the two depends on the half, and PokeAPI files that.
    **{
        species: GiftDetail(
            npc="Benga",
            requirement=(
                f"Shiny, for beating Benga in Area 10 of the {tower}; it holds an Exp. Share"
            ),
        )
        for species, tower in (("gible", "Black Tower"), ("dratini", "White Treehollow"))
    },
    # Not a gift and not quite a static either: it lies on the ground looking like a Poke Ball,
    # and picking it up starts a battle. The same trick the first pair plays.
    **{
        species: GiftDetail(
            kind=GiftKind.STATIC_ENCOUNTER,
            requirement="Disguised as a Poke Ball lying on the ground",
        )
        for species in ("foongus", "amoonguss")
    },
    "crustle": GiftDetail(
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement="Blocking the way during the story; the Colress MCHN is what moves it",
    ),
    # The one entry in these two games that is both shiny and behind the Permit, which makes it
    # the last thing a player of Black 2 can reach and the thing they reach it for.
    "haxorus": GiftDetail(
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement=(
            "Shiny, on the first visit to the Nature Preserve - which only opens with the "
            "Permit Professor Juniper hands over for seeing all 297 entries in the dex that "
            "are not Mythical; if it faints or is run from it waits there again once the Hall "
            "of Fame is entered"
        ),
    ),
    # The fourth giant needs both halves whichever half is being played, because the three it
    # asks for cannot all be caught on one cartridge. The other three are per half, below.
    "regigigas": GiftDetail(
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement=(
            "With Regirock, Regice and Registeel in the party - which takes a key from the "
            "other half of the pair whichever half this is"
        ),
    ),
    "heatran": GiftDetail(
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement="Once the Magma Stone is carried down to the mountain's lowest floor",
    ),
    "cresselia": GiftDetail(
        kind=GiftKind.STATIC_ENCOUNTER,
        requirement=(
            "By returning the Lunar Wing from the Strange House to the girl on the bridge"
        ),
    ),
    # The lake trio, which arrive in Unova rather than living there: they are in the Cave of
    # Being until Professor Juniper is spoken to, and none of them can be caught in it.
    **{
        species: GiftDetail(
            kind=GiftKind.STATIC_ENCOUNTER,
            requirement=(
                "Waits here once Professor Juniper has been spoken to in the Cave of Being, "
                "which she stands in after the Champion is beaten"
            ),
        )
        for species in ("uxie", "mesprit", "azelf")
    },
    **{
        species: GiftDetail(
            kind=GiftKind.STATIC_ENCOUNTER,
            requirement="In the northern Dreamyard, past the ruins; only one to a save",
        )
        for species in ("latias", "latios")
    },
    # The cover legendaries, which are not the story's this time: the story's Kyurem takes N's
    # dragon and gives it back. What Dragonspiral Tower holds is the stone, and it is found
    # after the Champion rather than walked into during the last battle.
    **{
        species: GiftDetail(
            kind=GiftKind.STATIC_ENCOUNTER,
            requirement=(
                f"Woken from the {stone} at the top of Dragonspiral Tower, after the Champion "
                "is beaten"
            ),
        )
        for species, stone in (("zekrom", "Dark Stone"), ("reshiram", "Light Stone"))
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
    # The stripe a player gets depends on which half they own. A trade can carry a form now,
    # so what is missing is no longer the schema but the fact: Bulbapedia lists both stripes
    # against this one trade and does not say which cartridge gets which.
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


#: What PokeAPI calls the sequels when it says which version group an evolution started in.
#:
#: Their own group, not the first pair's, and the evolutions in it are the same ones. It matters
#: anyway: an evolution is recorded per version group, and reading Black's group into Black 2
#: would be claiming that a rule nobody checked still holds two years later.
B2W2_VERSION_GROUP = "black-2-white-2"

#: The five both halves offer, in the order a player meets them.
#:
#: Two of them are the first pair's traders doing something else. Manny still stands on Route 7
#: and the trade has turned around - he handed over an Emolga for a Boldore in Black and White,
#: and here he wants the Emolga and gives a Gigalith - and Lillian on Route 15 still swaps a
#: Rotom for a Ditto, which is the one trade in Unova that did not change at all.
#:
#: Diana's two are the awkward ones and worth keeping in this order. She asks for an Excadrill
#: first and a Hippowdon after, and both times she battles the player with what they just handed
#: over, which is what the wiki's dagger means.
B2W2_SHARED_TRADES = (
    InGameTrade(gets="gigalith", wants="emolga", location="Route 7", npc="Manny"),
    InGameTrade(gets="tangrowth", wants="mantine", location="Humilau City", npc="Slick"),
    InGameTrade(gets="rotom", wants="ditto", location="Route 15", npc="Lillian"),
    InGameTrade(gets="ambipom", wants="excadrill", location="Accumula Town", npc="Diana"),
    InGameTrade(
        gets="alakazam",
        wants="hippowdon",
        location="Accumula Town",
        npc="Diana",
        requirement="Her second trade, offered once the Excadrill has been handed over",
    ),
)

#: And the sixth, which is the pair's own switch written as a trade - again.
#:
#: Exactly what Dye does in the first pair, two years later, on a different route and with two
#: different people doing it: Black 2 hands over a Cottonee and is given a Petilil, White 2 the
#: other way round. So the same two species look like version exclusives in all four games and
#: are not in any of them.
B2W2_COTTON_TRADE = {
    "black-2": InGameTrade(gets="petilil", wants="cottonee", location="Route 4", npc="Calla"),
    "white-2": InGameTrade(gets="cottonee", wants="petilil", location="Route 4", npc="Cotton"),
}


def b2w2_trades(version: str) -> tuple[InGameTrade, ...]:
    """The six this half offers, in the order a player meets them."""
    return (B2W2_COTTON_TRADE[version], *B2W2_SHARED_TRADES)


#: The babies nothing in the sequels can be met as, and what has to be in the day care for one.
#:
#: Twenty-seven, where the first pair needs four - and it is the same fact about Unova, much
#: larger. The grass here is full of grown-up Pokemon from older generations and almost none of
#: their young: Hariyama on Route 23 and no Makuhita anywhere, Pelipper in Undella Bay and no
#: Wingull, Banette in the Strange House and no Shuppet. Twenty-two of these twenty-seven are
#: a species whose only adult a player meets is already fully grown.
#:
#: Worked out from what the game actually produces rather than guessed at, which is what the
#: first pair's note about Pichu and Togepi is warning against: a parent that has to be traded
#: in first is a dead end dressed up as a way. Every parent named here is reachable in this
#: half without leaving it.
B2W2_EGGS: dict[str, EggFrom] = {
    "abra": EggFrom(parents=("alakazam",)),
    "hoothoot": EggFrom(parents=("noctowl",)),
    "cleffa": EggFrom(parents=("clefairy", "clefable")),
    "igglybuff": EggFrom(parents=("jigglypuff", "wigglytuff")),
    "aipom": EggFrom(parents=("ambipom",)),
    "snubbull": EggFrom(parents=("granbull",)),
    "swinub": EggFrom(parents=("piloswine", "mamoswine")),
    "larvitar": EggFrom(parents=("pupitar", "tyranitar")),
    "lotad": EggFrom(parents=("lombre", "ludicolo")),
    "seedot": EggFrom(parents=("nuzleaf", "shiftry")),
    "wingull": EggFrom(parents=("pelipper",)),
    "shroomish": EggFrom(parents=("breloom",)),
    "slakoth": EggFrom(parents=("vigoroth", "slaking")),
    "makuhita": EggFrom(parents=("hariyama",)),
    "meditite": EggFrom(parents=("medicham",)),
    "electrike": EggFrom(parents=("manectric",)),
    "shuppet": EggFrom(parents=("banette",)),
    # The two genderless families, where the day care needs a Ditto rather than a pair. Both
    # of the adults are reachable and neither has a mate anywhere in the game.
    "beldum": EggFrom(
        parents=("metang", "metagross"),
        requirement="Genderless, so the other half of the pairing has to be a Ditto",
    ),
    "golett": EggFrom(
        parents=("golurk",),
        requirement="Genderless, so the other half of the pairing has to be a Ditto",
    ),
    "bidoof": EggFrom(parents=("bibarel",)),
    # The one that costs money, as Chingling does in the first pair - and it costs less trouble
    # here: the Driftveil Market sells the incense from the start rather than once the National
    # Pokedex is open.
    "budew": EggFrom(
        parents=("roselia", "roserade"),
        requirement=("A parent has to hold a Rose Incense, which the Driftveil Market sells"),
    ),
    "blitzle": EggFrom(parents=("zebstrika",)),
    "tympole": EggFrom(parents=("palpitoad", "seismitoad")),
    "vanillite": EggFrom(parents=("vanillish", "vanilluxe")),
    "deino": EggFrom(parents=("zweilous", "hydreigon")),
    "larvesta": EggFrom(parents=("volcarona",)),
}

#: And the one each half has of its own, which is the oldest version exclusive in the series.
#:
#: Caterpie and Weedle, still opposite each other twelve years on - and in these two games
#: neither of them is in the grass at all. What each half has is the moth or the wasp, in one
#: Hidden Grotto in Pinwheel Forest, and the caterpillar is only an egg.
B2W2_FIRST_BUG = {
    "black-2": ("weedle", "beedrill"),
    "white-2": ("caterpie", "butterfree"),
}


def b2w2_eggs(version: str) -> dict[str, EggFrom]:
    """The twenty-seven this half's day care can produce."""
    baby, parent = B2W2_FIRST_BUG[version]

    return {**B2W2_EGGS, baby: EggFrom(parents=(parent,))}


def b2w2_gifts(version: str) -> dict[str, GiftDetails]:
    """What this half hands over, with the four entries the two halves word differently.

    Everything the sequels share is in :data:`B2W2_GIFTS`. What is not shared is a day of the
    week and a key, and neither is a version exclusive - both games have all four species, and
    both games describe getting them differently. A single table would have had to say "every
    Monday in Black 2 and every Thursday in White 2" on a record that already knows which game
    it belongs to.
    """
    key, rewarded, sent, other = _KEYS[version]

    return {
        **B2W2_GIFTS,
        **{
            species: GiftDetail(kind=GiftKind.STATIC_ENCOUNTER, requirement=f"Every {day}")
            for species, day in _WEEKLY[version].items()
        },
        "regirock": GiftDetail(
            kind=GiftKind.STATIC_ENCOUNTER,
            requirement=(
                "In the Rock Peak Chamber, which opens once the ruins' riddle has been "
                f"answered; catching it is rewarded with the {key}"
            ),
        ),
        rewarded: GiftDetail(
            kind=GiftKind.STATIC_ENCOUNTER,
            requirement=(
                f"In the {_CHAMBER[rewarded][0]}, which the {key} opens - the reward for "
                "catching Regirock"
            ),
        ),
        sent: GiftDetail(
            kind=GiftKind.STATIC_ENCOUNTER,
            requirement=(
                f"In the {_CHAMBER[sent][0]}, which only the {_CHAMBER[sent][1]} opens - and "
                f"that key is {other}'s reward for catching Regirock, sent over from a copy of "
                f"{other} through the Unova Link"
            ),
        ),
    }


def bw_trades(version: str) -> tuple[InGameTrade, ...]:
    """The five this half offers, in the order a player meets them."""
    return (BW_DYE_TRADE[version], *BW_SHARED_TRADES)


#: How each of this generation's forms is come by, for the games that can make one.
#:
#: Five families, and they are five different kinds of answer: a clock, a cartridge, an item, a
#: fusion and a move. Only the last three are something a player does.
#:
#: What is not here is everything Unova inherited. Burmy's cloaks, Shellos's two seas and the
#: letters of Unown are in these games' dexes and are made in Sinnoh, Johto and Kanto; the
#: records that explain them belong to those games, and the transfer graph carries them here.
#: Rotom is the exception and has its own entry, because the sequels' Unova can make one.
B2W2_ONLY = ("black-2", "white-2")

BW_FORM_CHANGES: dict[str, FormChange] = {
    **spread(
        FormChange(
            requirement="Touch the meteorite there; it cycles through all four formes",
            where="Nacrene City, Nacrene Museum",
        ),
        "deoxys-attack",
        "deoxys-defense",
        "deoxys-speed",
    ),
    # Not a change a player makes at all: the coat is whatever season the DS clock says, and the
    # season turns over on the first of the month. Worth a record anyway, because "how do I get
    # a winter Deerling" has an answer and it is "wait, or change the date".
    **spread(
        FormChange(
            requirement=(
                "Its coat is whichever season Unova is in, and the season follows the DS clock "
                "- one month each, turning over on the first"
            )
        ),
        "deerling-summer",
        "deerling-autumn",
        "deerling-winter",
        "sawsbuck-summer",
        "sawsbuck-autumn",
        "sawsbuck-winter",
    ),
    # And the one that is not a change either: the stripe is the water. Both are in both games,
    # which is why this is not a version exclusive - and until these games were given their own
    # forms to ask about, the sentence below was all the dataset had, and it read as though a
    # Black player could not catch a blue one at all.
    "basculin-blue-striped": FormChange(
        requirement=(
            "Both stripes are in both games and the water tells them apart: Black and Black 2 "
            "hold the red one in ordinary water and White and White 2 the blue, and each game "
            "keeps its other stripe in the rippling water instead"
        )
    ),
    # Rotom's appliances moved with the player. Sinnoh keeps them behind the Secret Key and
    # Johto behind a broken lift; Unova simply leaves them in boxes in a shop's basement.
    **spread(
        FormChange(
            requirement="Let it possess one of the appliances in the boxes there",
            where="Shopping Mall Nine, basement",
        ),
        "rotom-heat",
        "rotom-wash",
        "rotom-frost",
        "rotom-fan",
        "rotom-mow",
    ),
    # The Griseous Orb is in all four games and in a different place in each pair.
    "giratina-origin": FormChange(
        requirement=(
            "While it holds the Griseous Orb, which the Shadow Triad hand over on Marvelous "
            "Bridge in Black and White and which lies in Dragonspiral Tower in the sequels"
        )
    ),
}

#: And the three the sequels brought, which are the reason the Reveal Glass exists.
B2W2_FORM_CHANGES: dict[str, FormChange] = {
    **spread(
        FormChange(
            requirement=(
                "Use the Reveal Glass on it, which Cedric Juniper hands over in the Abundant "
                "Shrine's house once the trio has been caught"
            )
        ),
        "tornadus-therian",
        "thundurus-therian",
        "landorus-therian",
    ),
    "kyurem-black": FormChange(
        requirement="Fuse it with Zekrom using the DNA Splicers; the fusion can be undone again"
    ),
    "kyurem-white": FormChange(
        requirement="Fuse it with Reshiram using the DNA Splicers; the fusion can be undone again"
    ),
    "keldeo-resolute": FormChange(
        requirement=(
            "Teach it Secret Sword, which the Swords of Justice do once all three have been "
            "caught and Keldeo is brought to them"
        ),
        where="Pledge Grove",
    ),
}


def b2w2_form_changes() -> dict[str, FormChange]:
    """What the sequels can make, which is everything the first pair can and three more."""
    return {**BW_FORM_CHANGES, **B2W2_FORM_CHANGES}


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
        form_changes=BW_FORM_CHANGES,
    )


def b2w2_acquisition_methods(
    context: BuildContext,
    *,
    game_id: str,
    version: str,
    column: str,
    entries: Sequence[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something in Black 2 or White 2, the grottoes included.

    The one thing the sequels need that the first pair did not. PokeAPI's encounter tables have
    no Hidden Grotto in them at all, and twenty of them are hidden around this Unova holding
    species that are nowhere else in the game - so a build from that source alone is not short
    of detail, it is wrong about what these two cartridges contain.

    ``column`` is how the wiki page's Games column spells this half: "B2" or "W2".
    """
    return acquisition_methods(
        context,
        game_id=game_id,
        version=version,
        entries=entries,
        gifts=b2w2_gifts(version),
        version_group=B2W2_VERSION_GROUP,
        trades=b2w2_trades(version),
        eggs=b2w2_eggs(version),
        form_changes=b2w2_form_changes(),
        grotto_column=column,
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
    form_changes: Mapping[str, FormChange] | None = None,
    grotto_column: str | None = None,
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
    places = LocationNames(
        api,
        refresh=context.refresh,
        renamed=RENAMED_PLACES,
        renamed_sub_areas=RENAMED_SUB_AREAS,
    )

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
        )
    ]

    if grotto_column is not None:
        found.extend(
            grotto_encounters(
                context.require_wiki(),
                game_id=game_id,
                column=grotto_column,
                species=set(species),
                refresh=context.refresh,
            )
        )

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

    found.extend(
        form_change_encounters(
            game_id=game_id,
            forms=context.forms_here(),
            changes=form_changes or {},
            citation=bulbapedia("List_of_Pok%C3%A9mon_with_form_differences", retrieved_on=today),
        )
    )

    return found
