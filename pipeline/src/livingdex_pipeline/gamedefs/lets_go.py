"""What the two Let's Go games share: a Kanto nothing else in the dataset has.

The last two games of Generation 7, and the two that :mod:`alola` is named for a region rather
than a generation because of. They are set in Kanto, they came out a year after Ultra Sun and
Ultra Moon, and they have nothing else in common with the four cartridges: no Alola dex, no
Bank, no trade with any of them, and a Pokedex of 153 where those have 802.

**Why this file and not** :mod:`kanto`. That module holds what is true of the place across the
generations that have visited it, and names anything belonging to one pair after its hardware -
``gb_dex_entries``, ``GBA_PAIR_SPRITE_SET``. The overlap with these two is real and it is step
2's and step 3's to find: the same 151 species, the same towns, the same routes, mostly the same
grass. What is here is what belongs to this pair and would be a lie about Kanto - a dex that
holds two species Kanto never had, a region where Alolan forms walk around, and a way in from a
phone. When those steps come, whatever turns out to be about Kanto moves there and is named
``switch_``, the way FireRed's is named ``gba_``.

**Why this file and not** :mod:`kanto` **plus a hardware module**, which is the other half of
that convention: :mod:`gb`, :mod:`gba`, :mod:`ds` and :mod:`gen6` each hold what a generation's
cartridges share, and the Switch equivalent would be a module these two would sit in alone.
Sword and Shield are on the same console and share none of this - they talk to HOME the ordinary
way, they trade with each other and with Brilliant Diamond and Scarlet in turn, and they are
Generation 8. A ``switch.py`` would have to say "except in Let's Go" about every line in it,
which is the sentence a ``gen7.py`` would have had to say about Alola.

**What these two cannot do is the shape of the whole file.** Bulbapedia's list of firsts says it
twice over: they are the first core games "to not be compatible with previous core series titles
in any way since Pokemon Ruby and Sapphire, and as such, the first to be unable to trade with
other core series games in their generation", and the first "to not feature breeding since its
introduction in Pokemon Gold and Silver". So the graph around them is three routes and not
thirty: the cable between the halves, and HOME in each direction - where the way back asks a
question no edge in this dataset had ever asked.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from ..evolutions import evolution_encounters
from ..games import BuildContext
from ..gifts import GiftDetail, GiftDetails, RecordedGift, gift_encounters, recorded_gifts
from ..models import (
    AcquisitionMethod,
    AllSpeciesFilter,
    DexEntry,
    DexSource,
    DexTarget,
    Game,
    GameRelease,
    GiftKind,
    OriginRequirement,
    TransferDirection,
    TransferEdge,
    TransferMechanism,
)
from ..outside import SentIn, sent_in
from ..places import LocationNames
from ..sources import ReadByHand
from ..trades import InGameTrade, trade_encounters
from ..wild import wild_encounters
from . import exclusives, home, kanto

#: Kanto again, and the fifth pair of games to be set there.
REGION = kanto.REGION

#: Generation 7, which is where Bulbapedia puts them and not where a console would.
#:
#: They came out a year after Ultra Sun and Ultra Moon on the console that Generation 8 belongs
#: to, and they are still Generation 7: what decides it is the species the game knows, and
#: these know 153 of Generation 1's Kanto with one Mythical Pokemon added. Meltan is the only
#: species introduced by a Generation 7 game that is not in an Alola dex.
GENERATION = 7

#: One day, everywhere, in nine languages.
#:
#: The second release in this dataset with no Japanese date to prefer - Ultra Sun and Ultra Moon
#: were the first - and it went further than they did: these two shipped in Simplified and
#: Traditional Chinese on day one. Mainland China got its own release six years later, in
#: September 2024, on the Tencent Switch; this dataset holds the international one.
#:
#: Step 7 corrected what this note used to say about that release - that it "trades only with
#: itself". It does not: Bulbapedia says an event Pokemon from those games shows its real met
#: location once it is traded locally to an international copy, which is a trade between the two
#: releases described in passing. It matters because all three distributions these games have
#: ever had were for that release; see :data:`CHINESE_EVENTS`.
RELEASED = date(2018, 11, 16)

#: PokeAPI's name for the 153-entry list both halves show.
#:
#: Not :data:`kanto.DEX`, which is the 151 that Red, Blue, FireRed and LeafGreen show and which
#: this one contains exactly: the first 151 numbers agree entry for entry, and Meltan and
#: Melmetal are added at #152 and #153. Platinum's situation rather than Johto's - a number
#: these games share with an older one means what it always meant - and the opposite of what the
#: second Alola pair did to the first.
#:
#: The two at the end are the whole reason this is a separate list, and they are stranger than
#: the count makes them sound: **the only species introduced by a Generation 7 game that is not
#: in an Alola dex**, in a Pokedex that is otherwise Generation 1 from end to end. Neither can
#: be caught in Kanto. Meltan comes out of a Mystery Box in Pokemon GO and through the GO Park,
#: and Melmetal is what 400 Meltan Candy makes of one - in GO, not here. What that means for
#: these two entries is step 4's answer.
DEX = "letsgo-kanto"

#: The two halves, which are the whole of what these games can reach by cable.
#:
#: Named here rather than worked out from each game's ``pair_partner`` because two other things
#: need the pair as a set: the trade between them, and the origin HOME asks about - where being
#: from *either* half is one answer.
PAIR = ("lets-go-pikachu", "lets-go-eevee")

#: PokeAPI's name for the version group the two halves share, which their evolution rules hang
#: off. One for the pair, where Alola needs two: nothing about evolving changed between these.
VERSION_GROUP = "lets-go-pikachu-lets-go-eevee"

#: The folder both halves draw their pictures from, which is theirs alone.
#:
#: Not :data:`alola.SPRITE_SET`, though both are Generation 7 and both come off the Bulbagarden
#: Archives: these games are the series' first with no battle sprite at all. What the wiki keeps
#: under ``7p`` is a render of the model that walks around the overworld, and putting Alola's
#: flat 240 pixel drawing on a Let's Go tile would show a Pokemon from a game whose whole point
#: is that you can see it standing there.
#:
#: PokeAPI does have a Let's Go folder and it cannot be used; :mod:`archives` says why.
SPRITE_SET = "generation-vii/lets-go"

#: What the three birds ask, which is the same of all three and is step 3's finding from the
#: other end: the static is where the *first* one comes from, and the second is a rare spawn.
BIRD = (
    "Five minutes to beat it, with every stat raised, before it can be caught; once one is "
    "caught the same bird starts turning up over Kanto as a rare spawn"
)

#: What only the game knows about each thing these two hand over or leave standing in one spot.
#:
#: PokeAPI carries the method, the place and the level, and calls a starter, a fossil, a
#: purchase and a present from a stranger by one word. Who hands it over and what has to be
#: true first are read off Bulbapedia's list of these games' event Pokemon.
#:
#: **One table for both halves, which no pair before them could have had.** Bulbapedia calls
#: these the first core games with no mutually exclusive Pokemon, and the gifts keep to it: the
#: only two rows that are not in both are the Persian and the Arcanine, and those are one gift
#: with a different animal in it. A species the other half does not hand over has no row there
#: for this table to describe, so nothing has to be said twice.
#:
#: **Four rows carry a level, which no game before this pair has had to do.** PokeAPI puts the
#: Persian and the Arcanine at 32, the Porygon at 36 and the Electrode at 43, and Bulbapedia's
#: list of these games' event Pokemon and Serebii's gift page agree with each other against it
#: at 16, 16, 34 and 42. The Electrode says where those numbers probably come from: 43 is what
#: the Electrode in the same room of the same Power Plant was in Red and Blue, and Bulbapedia's
#: Power Plant page prints the two side by side - 43 in Generation I, 42 in this one. The
#: wording has been corrected in every game file in this dataset; this is the first time the
#: number has been.
#:
#: **Kanto's three starters are not starters here**, which is the sharpest thing in the table.
#: Bulbasaur, Charmander and Squirtle are not lined up in Oak's laboratory to be chosen between:
#: they are three separate presents from three strangers in three towns, and what each one asks
#: is how many species have been caught. All three can be had in one save, so the choice Red
#: made in 1996 is gone along with the grass - which is why none of them carries
#: :attr:`GiftKind.STARTER` here and all three do in every other Kanto.
GIFTS: dict[str, GiftDetails] = {
    # The partner, which is the premise of both games and the one Pokemon in either that goes
    # nowhere afterwards. Step 8 gave it the form it always was: the wild Pikachu of Viridian
    # Forest and the wild Eevee of Route 17 are ordinary ones, and this is not either.
    "pikachu": GiftDetail(
        kind=GiftKind.STARTER,
        form="pikachu-starter",
        npc="Professor Oak",
        requirement="The partner, which cannot be traded away, put into HOME or evolved",
    ),
    "eevee": GiftDetail(
        kind=GiftKind.STARTER,
        form="eevee-starter",
        npc="Professor Oak",
        requirement="The partner, which cannot be traded away, put into HOME or evolved",
    ),
    "bulbasaur": GiftDetail(
        npc="A woman in Cerulean City",
        requirement="After 30 or more Pokemon have been caught",
    ),
    "charmander": GiftDetail(
        npc="A man north of Route 24",
        requirement="After 50 or more Pokemon have been caught",
    ),
    "squirtle": GiftDetail(
        npc="Officer Jenny in Vermilion City",
        requirement="After 60 or more Pokemon have been caught",
    ),
    # The one gift the halves disagree about, and they disagree about the animal rather than
    # about whether there is one: the same errand outside the same building, and it is paid in
    # the line this half's own grass does not hold. Catch five of the Growlithe only Let's Go,
    # Pikachu! has and the Black Belt hands over a Persian, whose Meowth is Eevee's alone.
    "persian": GiftDetail(
        level=16,
        npc="A Black Belt outside the Pokemon Fan Club",
        requirement="Catch five Growlithe and show them to him",
    ),
    "arcanine": GiftDetail(
        level=16,
        npc="A Beauty outside the Pokemon Fan Club",
        requirement="Catch five Meowth and show them to her",
    ),
    "hitmonlee": GiftDetail(
        npc="Koichi, the Fighting Dojo master",
        requirement="Beat him, then pick one of the two; the other stays behind",
    ),
    "hitmonchan": GiftDetail(
        npc="Koichi, the Fighting Dojo master",
        requirement="Beat him, then pick one of the two; the other stays behind",
    ),
    # PokeAPI files this one inside Silph Co. and Bulbapedia has the scientist waiting outside
    # by the Pokemon Center. Both are Saffron City and the errand is the same one, so the place
    # stays as the source spells it and the sentence says what actually has to be done.
    "porygon": GiftDetail(
        level=34,
        npc="A Silph Co. scientist",
        requirement="After Team Rocket is driven out of the building",
    ),
    # He has asked 500 for a Magikarp in every Kanto there has ever been, and in this one he has
    # moved from the Pokemon Center near Mt. Moon to the one on Route 4.
    "magikarp": GiftDetail(
        npc="The Magikarp salesman",
        requirement="Bought for 500 Pokedollars",
    ),
    # **The first Kanto where the fossil passed over is not lost for good.** Red, Blue, Yellow,
    # FireRed and LeafGreen all keep the one left behind at the end of Mt. Moon, and
    # :data:`kanto.SHARED_GIFTS` says so in those words. This pair hides more of both in
    # Cerulean Cave as ordinary ground items, so a living dex here gets both halves of a choice
    # that was permanent for twenty-two years.
    "omanyte": GiftDetail(
        kind=GiftKind.FOSSIL,
        npc="The Cinnabar Lab scientist",
        requirement=(
            "Helix Fossil, offered by Super Nerd Miguel at the end of Mt. Moon - and the one "
            "turned down there is hidden in Cerulean Cave later, which no Kanto before this "
            "one allowed"
        ),
    ),
    "kabuto": GiftDetail(
        kind=GiftKind.FOSSIL,
        npc="The Cinnabar Lab scientist",
        requirement=(
            "Dome Fossil, offered by Super Nerd Miguel at the end of Mt. Moon - and the one "
            "turned down there is hidden in Cerulean Cave later, which no Kanto before this "
            "one allowed"
        ),
    ),
    "aerodactyl": GiftDetail(
        kind=GiftKind.FOSSIL,
        npc="The Cinnabar Lab scientist",
        requirement=(
            "Old Amber, from the back of the Pewter Museum of Science, which takes Chop Down "
            "to reach"
        ),
    ),
    # Two of them, one per road out of Lavender Town, and they are why a gift table can be keyed
    # by place: the same species at the same level woken the same way, and the only thing
    # telling them apart is which stat the one in front of you starts with.
    "snorlax": (
        GiftDetail(
            where="Route 12",
            requirement=(
                "Poke Flute to wake the one asleep across the road, and five minutes to beat "
                "it; this one starts with its Attack raised"
            ),
        ),
        GiftDetail(
            where="Route 16",
            requirement=(
                "Poke Flute to wake the one asleep across the road, and five minutes to beat "
                "it; this one starts with its Defense raised"
            ),
        ),
    ),
    "electrode": GiftDetail(
        level=42,
        requirement=(
            "One of the four fake item balls in the Power Plant, and five minutes to beat what "
            "comes out of it"
        ),
    ),
    "articuno": GiftDetail(requirement=BIRD),
    "zapdos": GiftDetail(requirement=BIRD),
    "moltres": GiftDetail(requirement=BIRD),
    "mewtwo": GiftDetail(
        requirement=(
            "Cerulean Cave, which opens after the Hall of Fame, and five minutes to beat it "
            "with every stat raised before it can be caught"
        ),
    ),
}

#: The one gift PokeAPI does not carry for these two.
#:
#: A Silph Co. employee hands over a Lapras while Team Rocket still holds the building, in both
#: halves, and PokeAPI has no encounter for it in either. Kanto has handed a Lapras over in that
#: room since Red - :data:`kanto.SHARED_GIFTS` describes it there, off a row PokeAPI does have -
#: so this is the same gift in the same place, missing from one version's tables.
#:
#: It closes no hole in the dex: step 3 found Lapras swimming off two sea routes as a rare
#: spawn, which is new in this pair. It is written down because leaving it out would say this
#: Kanto had stopped doing something it has done for twenty-two years.
#: Where that Lapras was read, spelled the way the article's own url spells it.
SILPH_LAPRAS_PAGE = (
    "List_of_in-game_event_Pok%C3%A9mon_in_Pok%C3%A9mon:"
    "_Let%27s_Go,_Pikachu!_and_Let%27s_Go,_Eevee!"
)

HANDED_OVER: tuple[RecordedGift, ...] = (
    RecordedGift(
        species="lapras",
        location="Saffron City, Silph Co",
        level=34,
        npc="A Silph Co. employee",
        requirement="While Team Rocket still holds the building",
    ),
)

#: Where the GO Park was read, spelled the way the article's own url spells it.
GO_PARK_PAGE = "GO_Park"

#: What Pokemon GO sends into this pair that the pair itself cannot produce.
#:
#: **Two, out of everything GO could send.** The park takes any of the first 150 and their
#: Alolan forms, and Kanto is full of them; what it adds to this dataset is Meltan and Melmetal,
#: which are #152 and #153 of a Pokedex this Kanto cannot fill without a phone.
#:
#: Melmetal is the sharper of the two: it arrives **already evolved**, because the 400 Meltan
#: Candy that makes one is spent in GO and nothing in Kanto can evolve the Meltan that comes out
#: of the park. So the row is not "evolve it here" - it is a second thing the park hands over.
#:
#: The eleven Pokemon only the other half of the pair has are deliberately not here. GO has
#: every one of them and the park would bring them across, and trading with the other half is a
#: way this dataset already records - which is the line Yannick drew on 26 September 2026:
#: only what nothing else in the dataset provides.
GO_PARK: tuple[SentIn, ...] = (
    SentIn(
        species="meltan",
        how=(
            "Caught in Pokemon GO, where a Mystery Box makes it appear, and sent to the GO Park "
            "in Fuchsia City. The box is opened by sending a Pokemon the other way, so the park "
            "unlocks its own source"
        ),
    ),
    SentIn(
        species="melmetal",
        how=(
            "Evolved in Pokemon GO with 400 Meltan Candy and sent to the GO Park in Fuchsia "
            "City. It arrives already evolved: nothing in Kanto can evolve a Meltan"
        ),
    ),
)

#: Why the park never counts towards being able to get one here.
#:
#: The same treatment the Friend Safari has had since Generation 6, and for a plainer reason:
#: this one is not in the game at all. A player with the cartridge and no phone cannot be told
#: to go and use it.
GO_PARK_DOES_NOT_COUNT = (
    "It is caught in another game on another device: Pokemon GO, on a phone, with a Nintendo "
    "Switch Online account tying the two together"
)

#: Where a trader was read, spelled the way the article's own url spells it.
TRADERS_PAGE = (
    "List_of_in-game_trade_Pok%C3%A9mon_in_Pok%C3%A9mon:"
    "_Let%27s_Go,_Pikachu!_and_Let%27s_Go,_Eevee!"
)

#: What each trader asks and hands back, which is the same bargain eight times over.
#:
#: **Every in-game trade in this pair hands over an Alolan form**, and Bulbapedia says why it
#: matters: they are "the only way to obtain Alolan forms outside of GO Park or trading with
#: other players". Each trader wants the Kantonian form of the very species they are handing
#: back Alolan - a Rattata for a Rattata, a Geodude for a Geodude - which is the whole shape of
#: the bargain and is why no ``wants`` here is a surprise.
#:
#: They are step 8's rather than step 5's for that reason: a record whose target is a form
#: cannot be written before the form table says which forms this game has, and that table is
#: :data:`forms.LETS_GO_FORMS`, two doors up.
#:
#: Six of the eight stand in both halves. The Camper in Celadon City and the Punk Guy on
#: Cinnabar Island ask for a different Pokemon depending on the cartridge, which is how the two
#: halves end up with fourteen Alolan forms each and four of them different - see
#: :func:`traders` and :data:`ONLY_ON`.
#:
#: **And every one of them can be traded with again, as often as a player likes.** No trader
#: before these has offered a second one of anything: Bill's Eevee, Hila's Machop and the rest
#: are each one Pokemon and then a closed conversation.
SHARED_TRADERS: tuple[InGameTrade, ...] = (
    InGameTrade(
        gets="rattata",
        form="rattata-alola",
        wants="rattata",
        location="Cerulean City, Pokemon Center",
        npc="Tatianna",
    ),
    InGameTrade(
        gets="geodude",
        form="geodude-alola",
        wants="geodude",
        location="Vermilion City, Pokemon Center",
        npc="Higeo",
    ),
    InGameTrade(
        gets="diglett",
        form="diglett-alola",
        wants="diglett",
        location="Lavender Town, Pokemon Center",
        npc="Diggette",
    ),
    InGameTrade(
        gets="raichu",
        form="raichu-alola",
        wants="raichu",
        location="Saffron City, Pokemon Center",
        npc="Psytrice",
    ),
    InGameTrade(
        gets="marowak",
        form="marowak-alola",
        wants="marowak",
        location="Fuchsia City, Pokemon Center",
        npc="Genmar",
    ),
    InGameTrade(
        gets="exeggutor",
        form="exeggutor-alola",
        wants="exeggutor",
        location="Indigo Plateau, Pokemon League",
        npc="Exemann",
    ),
)

#: The two who want a different Pokemon in each half, and the whole of what the halves' form
#: tables disagree about.
TRADERS_BY_HALF: dict[str, tuple[InGameTrade, ...]] = {
    "lets-go-pikachu": (
        InGameTrade(
            gets="sandshrew",
            form="sandshrew-alola",
            wants="sandshrew",
            location="Celadon City, Pokemon Center",
            npc="Nicholice",
        ),
        InGameTrade(
            gets="grimer",
            form="grimer-alola",
            wants="grimer",
            location="Cinnabar Island, Pokemon Center",
            npc="Darko",
        ),
    ),
    "lets-go-eevee": (
        InGameTrade(
            gets="vulpix",
            form="vulpix-alola",
            wants="vulpix",
            location="Celadon City, Pokemon Center",
            npc="Nicholice",
        ),
        InGameTrade(
            gets="meowth",
            form="meowth-alola",
            wants="meowth",
            location="Cinnabar Island, Pokemon Center",
            npc="Darko",
        ),
    ),
}


def traders(game_id: str) -> tuple[InGameTrade, ...]:
    """The eight this half has: the six both stand in, and its own two."""
    return (*SHARED_TRADERS, *TRADERS_BY_HALF[game_id])


#: The three distributions these two games have ever had, and the one thing they share.
#:
#: **Every one of them was for the mainland Chinese release**, which came out in September 2024
#: on the Tencent Switch, six years after the cartridges this dataset holds. Each was a password
#: rather than a serial code, each may be redeemed once per save file, and each is refused
#: unless the save's origin language is Simplified Chinese. The Arbok is the strangest of the
#: three: Shiny, level 50, eight in every IV, handed out over a fortnight for the Year of the
#: Snake.
#:
#: They are named because step 7's question is what a player can be told, and the honest answer
#: has two halves: nothing you can play produces one, and the event that once did was for a
#: different set of cartridges. Bulbapedia adds the part that keeps that from being useless - an
#: event Pokemon from those games shows its real met location when it is traded locally to an
#: international copy, so there is a way across and it runs through somebody else's Switch.
CHINESE_EVENTS: dict[str, str] = {
    "arbok": "the Year of the Snake Shiny Arbok of January 2025",
    "meltan": "the Chinese Release Commemoration Meltan of October 2024",
    "melmetal": "the Pokemon Day Melmetal of February 2025",
}


def only_in_china(species: str) -> str:
    """What step 7 found for one species, and who it was really for."""
    return (
        f"{exclusives.handed_out(CHINESE_EVENTS[species])}, and it was for the mainland Chinese "
        "cartridges rather than these: one of those Pokemon reaches an international copy only "
        "by a local trade with somebody who has that release"
    )


#: What each half's grass holds that the other half's does not: six lines apiece.
#:
#: Eleven species each way once the evolutions are counted, which is the number step 3 found in
#: the grass - and after step 5 the bases are the whole of it, because either half can evolve
#: what it is handed. Ordinary version exclusives, then, and the smallest split a Kanto pair has
#: had: Red and Blue divide eleven *lines*.
#:
#: **What is not ordinary is where the other half's two show up.** The Black Belt outside the
#: Vermilion Fan Club wants five Growlithe - which only Let's Go, Pikachu! has - and pays in a
#: Persian, whose Meowth only Let's Go, Eevee! has. The Beauty in the same spot wants five
#: Meowth and pays in an Arcanine. So each half hands over the evolved form of a line it does
#: not hold, for five of a line it does, and neither of those two lines is listed here as a
#: whole: Persian is obtainable in Pikachu and Meowth is not.
ONLY_ON: dict[str, dict[str, str | None]] = {
    "lets-go-pikachu": dict.fromkeys(
        ("sandshrew", "oddish", "mankey", "growlithe", "grimer", "scyther")
    ),
    "lets-go-eevee": {
        "ekans": None,
        # The one entry in either half that is listed beside its own base rather than left to
        # inherit from it: step 7 found a distribution for the Arbok and none for the Ekans it
        # evolves from, and a reason written out is a reason `reach.spread_unobtainable` leaves
        # alone.
        "arbok": only_in_china("arbok"),
        "vulpix": None,
        "meowth": None,
        "bellsprout": None,
        "koffing": None,
        "pinsir": None,
    },
}

#: What each half is called in a sentence a player reads.
TITLE: dict[str, str] = {
    "lets-go-pikachu": "Let's Go, Pikachu!",
    "lets-go-eevee": "Let's Go, Eevee!",
}


def only_on(partner: str, event: str | None = None) -> str:
    """Why an entry in this dex is not in this half, and the one route to it.

    Not :func:`exclusives.only_on`, which says "only in Generation 7" and would be wrong twice
    over here. Ekans is in Alola as well, so the other half is not the only Generation 7 game
    with one; and no Generation 7 game but the other half can reach these two anyway. The cable
    between the halves is the whole of what a player can be told to do.
    """
    return exclusives.with_event(
        f"{partner} only; trade one in over the cable between the halves, which is the only "
        "route either of these games has",
        event,
    )


#: The one thing PokeAPI's chain says about this pair that is not true of it.
#:
#: Meltan becomes Melmetal on 400 Meltan Candy, and that happens in Pokemon GO: Bulbapedia's
#: game-locations table lists "Evolve Meltan" under GO and gives these two "Transfer from
#: Pokemon GO to GO Park" instead. A chain has no column for where its rule can be used, so the
#: reader is told here - the same shape, and the same argument, as a gift the source files under
#: the wrong version.
#:
#: Nothing was broken by it, which is the interesting part: Meltan is unobtainable here, so the
#: Melmetal that evolves from it was unreachable and ``no-evolution-dead-ends`` had nothing to
#: report. A record can be wrong without failing anything, and that is what a reader has to be
#: protected from.
NOT_AN_EVOLUTION_HERE: dict[str, str] = {
    "melmetal": (
        "400 Meltan Candy in Pokemon GO makes one, and nothing in Kanto can evolve the Meltan "
        "that comes out of the GO Park"
    ),
    # **The three evolutions that depend on where you are standing**, which is step 8's other
    # finding. Fifteen of the eighteen Alolan forms evolve out of an Alolan form and the source
    # says so - a detail that requires `rattata-alola` is a second way rather than a replacement,
    # and both halves keep the Kantonian way beside it. These three require no form at all,
    # because a Pikachu, a Cubone and an Exeggcute are one Pokemon each: what the stone or the
    # level makes of them is decided by the region, and this region is Kanto. Bulbapedia agrees
    # entry for entry - every one of the three reads "Trade" in its Alolan row here.
    "raichu-alola": (
        "A Thunder Stone in Kanto makes the Kantonian Raichu; the Alolan one is what Psytrice "
        "in the Saffron City Pokemon Center hands over"
    ),
    "marowak-alola": (
        "A Cubone raised in Kanto becomes the Kantonian Marowak; the Alolan one is Genmar's, in "
        "the Fuchsia City Pokemon Center"
    ),
    "exeggutor-alola": (
        "A Leaf Stone in Kanto makes the Kantonian Exeggutor; the Alolan one is what Exemann "
        "trades for at the Pokemon League"
    ),
}

#: The three entries in this Pokedex that neither half can produce, and why.
#:
#: One table for both, like the gifts and for the same reason: these two split nothing. Three of
#: 153, and not one of them is the usual kind of answer - no distribution that closed, no
#: species the other half kept back. Two of them are behind a phone and the third is behind a
#: controller.
#:
#: **The GO Park is the question step 1 left here, and the answer is a reason rather than a
#: record.** :func:`edges` sets out why it is not a route: Pokemon GO is not a game in this
#: dataset, it has no Pokedex to fill and nothing in it is caught in the sense this tracker
#: means. What that function went on to guess was that the park must therefore be an
#: acquisition, "the same shape as an egg from an NPC". It is not, and the Pokemon Dream Radar
#: is the precedent that settled it: a source that is not a game, sending one way into two
#: cartridges and nowhere else. Phase 3 decided the two together, as the item asked, and gave
#: them one shape - :class:`models.OutsideAcquisition`, which :data:`GO_PARK` fills in here.
#:
#: **The reason below stays anyway**, which is Yannick's decision of 26 September 2026 and is
#: worth the room: it says why Kanto itself has none, and the row underneath says by what road
#: one arrives. Neither sentence can do the other's work.
UNOBTAINABLE: dict[str, str] = {
    # Never in these games, and the one Mythical Pokemon here whose route is hardware. Not a
    # distribution that ended: the code inside a Poke Ball Plus has been good since the day
    # these games went on sale, the accessory is still sold, and there is one Mew in each one
    # ever made. Step 7 looks at this wording again beside the rest of the events.
    "mew": (
        "Nothing in Kanto produces one: the only Mew here is the Mystery Gift redeemed with "
        "the serial code inside a Poke Ball Plus, one per accessory ever made, open since the "
        "day the games went on sale and never closed - and step 7 found it is the only Mystery "
        "Gift these cartridges have ever been sent"
    ),
    "meltan": exclusives.with_event(
        "Only through the GO Park: Pokemon GO sends into these two one way and into nothing "
        "else, and GO is not a game in this dataset - it has no Pokedex to fill and nothing in "
        "it is caught in the sense this tracker means. Doable today rather than closed, and it "
        "closes its own circle: the Mystery Box that makes Meltan appear in GO is unlocked by "
        "sending something to the GO Park in the first place",
        only_in_china("meltan"),
    ),
    "melmetal": exclusives.with_event(
        "Only through the GO Park, and it arrives already evolved: 400 Meltan Candy makes one "
        "in Pokemon GO, where the Meltan has to be caught anyway, and nothing in Kanto can "
        "evolve the Meltan that comes out of the park. Doable today rather than closed - the "
        "park takes Kanto's 151, their Alolan forms, and these two",
        only_in_china("melmetal"),
    ),
}


def cartridge(
    *,
    game_id: str,
    title: str,
    version: str,
    pair_partner: str,
    sprite_set: str | None = SPRITE_SET,
) -> Game:
    """One half of the pair, with everything the two of them agree about filled in.

    No ``national_dex_through``: these have no National Pokedex, like the four Alola cartridges
    before them, and unlike those four they cannot hold what is not in their own list either.
    Their boxes take the 153 species the Pokedex shows and nothing else, so the grid is that
    list - which is what :class:`DexSource.GAME_DEX` says and step 2 fills in.
    """
    return Game(
        id=game_id,
        title=title,
        version=version,
        generation=GENERATION,
        region=REGION,
        release=GameRelease.CARTRIDGE,
        released=RELEASED,
        national_dex_through=None,
        dex_source=DexSource.GAME_DEX,
        pair_partner=pair_partner,
        sprite_set=sprite_set,
    )


def unobtainable_in(game_id: str) -> dict[str, str]:
    """Everything one half cannot produce: the three neither can, and the other half's six.

    One function rather than a table per game, because the two halves disagree about nothing
    else. :data:`UNOBTAINABLE` is the same three lines in both and :data:`ONLY_ON` is the same
    six the other way round, so a table written out per half would be the same file twice with
    two words swapped.
    """
    other = next(one for one in PAIR if one != game_id)

    return {
        **UNOBTAINABLE,
        **{species: only_on(TITLE[other], event) for species, event in ONLY_ON[other].items()},
    }


def dex_entries(
    context: BuildContext,
    *,
    game_id: str,
    unobtainable: Mapping[str, str] | None = None,
) -> list[DexEntry]:
    """The Let's Go Pokedex, Bulbasaur #001 to Melmetal #153, as both halves number it.

    One function for the two of them, the way :func:`kanto.dex_entries` is one for four: the
    halves show the same list in the same order, and what differs between them is which entries
    their own Kanto never holds - the ``unobtainable`` table each game brings.

    No ``dex`` name on the entries. These games show one list, so a number can only belong to
    one; X and Y's three are the only reason that field exists.

    **No forms either, and that is a real answer rather than a gap.** The Pokedex here has 153
    entries and an Alolan Rattata does not get one of its own - it shares Rattata's, exactly as
    it does in Sun and Moon. What the GO Park counts separately for its candy minigame is
    another matter and is the park's own bookkeeping. Which forms these games actually hold is
    step 8's, and until it runs the form table deliberately says they hold none; see
    :data:`forms.FORMS_NAMED_BY_THE_GAME`.
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


#: The day a person read each page the tables below were typed from.
#:
#: A fetched citation takes its date from the cache entry the answer came out of. These have no
#: fetch to take one from, so the day is written down beside the table that was read - which is
#: the only place it can come from once the reading is over.
READ_ON = ReadByHand(
    {
        SILPH_LAPRAS_PAGE: date(2026, 9, 24),
        TRADERS_PAGE: date(2026, 9, 24),
        GO_PARK_PAGE: date(2026, 9, 26),
    }
)


def acquisition_methods(
    context: BuildContext,
    *,
    game_id: str,
    version: str,
    entries: Sequence[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something in one half of the pair.

    Two tables now, which are steps 3 and 4. A table left out is a step that has not been
    gathered yet rather than a game with nothing to declare - :mod:`alola` says the same thing
    about the same shape, and the trades and the evolutions arrive as their steps run.

    Both halves pass the same gift table, which no pair before them could have done; see
    :data:`GIFTS` for why, and for what these games did to the three starters.

    **No eggs, and that is one of step 4's five things answered with nothing.** Every game from
    Gold and Silver on has had a day care and something only it produces; these two are the
    first core games since breeding was invented that have neither, which the module docstring
    quotes Bulbapedia's list of firsts for. So there is no egg table to leave out and no baby
    to be short of: nothing in this Pokedex hatches.

    **And no trades, which is step 5's answer rather than a table not gathered yet.** There are
    eight of them, one in each of seven Pokemon Centers and one in the Pokemon League lobby, and
    Bulbapedia's in-game trade list for these two says what they are in a line: every one hands
    over an Alolan form, and they are "the only way to obtain Alolan forms outside of GO Park or
    trading with other players". Tatianna wants a Rattata for an Alolan Rattata in Cerulean City,
    Higeo a Geodude in Vermilion, Diggette a Diglett in Lavender, Nicholice a Sandshrew in
    Celadon, Psytrice a Raichu in Saffron, Genmar a Marowak in Fuchsia, Darko a Grimer in
    Cinnabar - a Meowth in the other half - and Exemann an Exeggutor at the League. All eight can
    be done over and over, which no trader in this dataset has ever allowed.

    So they are step 8's, and that is the workflow's own answer rather than a dodge: a record
    whose target is a form cannot be written before the game's form table says which forms it
    has, :data:`forms.FORMS_NAMED_BY_THE_GAME` deliberately says these two have none until that
    table is written out by hand, and "how each one is come by" is step 8's second bullet.
    Writing them now would mean either naming forms nothing records - which the form reader
    refuses, and rightly - or saying a Lass in Cerulean City swaps a Rattata for a Rattata.

    **The cost of waiting is nothing a player can see.** All eight targets are species this half
    already fills some other way, so not one of the 153 tiles depends on them. These are the
    first in-game trades in the dataset that add no species to a living dex at all.

    The species asked about are the game's own 153 and not a National Dex slice, which is what
    :meth:`BuildContext.living_dex` does when a game has no National Dex to slice: these boxes
    hold what the Pokedex lists and nothing else, so the living dex and the Pokedex are the
    same list for the first time since Yellow.
    """
    api = context.require_api()
    species = context.living_dex(through=None, entries=entries)
    places = LocationNames(api, refresh=context.refresh)

    return [
        *wild_encounters(
            api,
            game_id=game_id,
            version=version,
            species=species,
            forms=context.forms_here(),
            refresh=context.refresh,
            places=places,
        ),
        *gift_encounters(
            api,
            game_id=game_id,
            version=version,
            species=species,
            details=GIFTS,
            forms=context.forms_here(),
            refresh=context.refresh,
            places=places,
        ),
        *recorded_gifts(
            game_id=game_id,
            gifts=HANDED_OVER,
            species=species,
            citation=READ_ON(SILPH_LAPRAS_PAGE),
        ),
        *trade_encounters(
            game_id=game_id,
            trades=traders(game_id),
            citation=READ_ON(TRADERS_PAGE),
        ),
        *sent_in(
            game_id=game_id,
            sent_from="Pokemon GO",
            rows=list(GO_PARK),
            does_not_count=GO_PARK_DOES_NOT_COUNT,
            citation=READ_ON(GO_PARK_PAGE),
        ),
        *evolution_encounters(
            api,
            game_id=game_id,
            version_group=VERSION_GROUP,
            species=species,
            forms=context.forms_here(),
            all_forms=context.forms,
            excluded=NOT_AN_EVOLUTION_HERE,
            refresh=context.refresh,
        ),
    ]


def trade_edges(game_id: str) -> list[TransferEdge]:
    """The one cable these games have, which runs to the other half of the pair.

    Every pair since Red and Blue has had this edge and only these two have had nothing beside
    it. There is no route to Ultra Sun, which came out a year earlier on hardware in the same
    living room; there is no GTS and no Wonder Trade; and Bank, which is how the rest of
    Generation 7 reaches anything, does not know these games exist.

    One thing the filter cannot say, because a filter is about species and this is about one
    Pokemon: the partner Pikachu or Eevee the player starts with may not be traded at all, nor
    put into HOME. Every other Pikachu in the game may.
    """
    return [
        TransferEdge(
            **{"from": game_id},
            to=partner,
            mechanism=TransferMechanism.TRADE,
            direction=TransferDirection.BOTH_WAYS,
            filter=AllSpeciesFilter(),
        )
        for partner in PAIR
        if partner != game_id
    ]


def home_edges(game_id: str) -> list[TransferEdge]:
    """HOME both ways, and the way back is unlike every other edge in the dataset.

    The deposit is the ordinary one: HOME holds everything, so it takes anything these games
    can. The withdrawal is the reason :class:`OriginRequirement` exists. Bulbapedia states it
    plainly - only a Pokemon originally from Let's Go, Pikachu! or Let's Go, Eevee! can be moved
    into either of them - and it adds that anything arriving in HOME from Bank or the GO
    Transporter is converted to Sword and Shield's format on the way in and can never enter them
    at all.

    So this is not :func:`home.home_edges`, which is what the Generation 8 and 9 games get, and
    :mod:`home` says so in its own docstring rather than leaving it to be discovered here. That
    function's withdrawal asks whether the target's dex lists the species; this one asks where
    the Pokemon was caught, and every species it would refuse is in the dex already.

    **What it means for a living dex is worth saying out loud: this route adds nothing.** HOME
    can hand these games back only what they produced in the first place, so no tile in a Let's
    Go grid is ever filled by way of it. It is in the graph because it is true and because a
    player who has put a box on the shelf should be able to see that they can take it down
    again, not because it makes anything obtainable.
    """
    return [
        TransferEdge(
            **{"from": game_id},
            to=home.NODE,
            mechanism=TransferMechanism.HOME,
            direction=TransferDirection.ONE_WAY,
            filter=AllSpeciesFilter(),
        ),
        TransferEdge(
            **{"from": home.NODE},
            to=game_id,
            mechanism=TransferMechanism.HOME,
            direction=TransferDirection.ONE_WAY,
            filter=AllSpeciesFilter(),
            origin=OriginRequirement(games=list(PAIR)),
        ),
    ]


def edges(game_id: str) -> list[TransferEdge]:
    """Every route one of these two brings: the cable to its other half, and HOME both ways.

    Three, where an Alola cartridge brings five and a Generation 4 one brings eleven.

    **And one route that is deliberately not here: the GO Park.** Pokemon GO sends Kanto's 151,
    their Alolan forms, Meltan and Melmetal into these games one way, into a complex of twenty
    parks that replaced the Safari Zone in Fuchsia City, and it is the only way a player gets an
    Alolan Rattata or a Meltan at all. It is not an edge because GO is not a game in this
    dataset and should not be: it has no Pokedex to fill, nothing in it is caught in the sense
    this tracker means, and :mod:`home` already writes down that decision for the same reason.

    What this paragraph said next, before step 4 ran, was that the park must therefore be a way
    of obtaining a species here - "the same shape as an egg from an NPC". It is not one of the
    six kinds, and Phase 3 gave it a seventh: :class:`models.OutsideAcquisition`, decided
    alongside the Dream Radar as the item asked. :data:`GO_PARK` is the two species it brings,
    and neither of them counts towards being able to get one here.
    """
    return [*trade_edges(game_id), *home_edges(game_id)]
