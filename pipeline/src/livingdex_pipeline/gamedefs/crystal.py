"""Pokemon Crystal: everything but the smoke test.

Phase 2 steps 1 to 7 for this game: the 251 entries it asks a player to fill, every wild slot
that fills one across both halves of its map, everything it hands over or leaves standing in one
spot - Celebi included - what its eight traders will swap for, what evolves into what here, and
which babies only the day care brings, the sprite sheet a player of it actually saw, and
where the fifteen entries it cannot produce could ever have come from.

This is the Virtual Console release rather than the 2000 cartridge, and it is the only Crystal
in this dataset - see :mod:`vc` for why, and here the difference is larger than anywhere else in
the series. The 3DS release turns on the GS Ball event that the cartridge kept for Japan, so
this entity can produce a Celebi where the cartridge most players owned could not.

Everything it shares with Gold and Silver is in :mod:`johto`, which is about the region rather
than the generation: HeartGold and SoulSilver are set there too. Everything it shares with the
rest of its generation is in :mod:`gbc`. What is left is its name, that it is nobody's other
half, and which version PokeAPI is asked about.
"""

from __future__ import annotations

from datetime import date

from ..games import BuildContext, GameRegistry
from ..gifts import GiftDetail, GiftDetails, RecordedGift
from ..models import AcquisitionMethod, DexEntry, GameData, TransferEdge
from ..sources import ReadByHand
from ..trades import InGameTrade
from . import johto

GAME_ID = "crystal"

#: What PokeAPI calls this game when it lists which version an encounter belongs to.
POKEAPI_VERSION = "crystal"

#: The Virtual Console release, worldwide on one day, five months after Gold and Silver's. The
#: cartridge was December 2000 in Japan and November 2001 in Europe, and neither is what this
#: entity is.
RELEASED = date(2018, 1, 26)

#: Where this game's own battle sprites live in the sprite repository.
#:
#: The third sheet of three. Gold and Silver drew all 251 twice over and Crystal drew them a
#: third time, which is why a Generation 2 sheet belongs to a game rather than to a pair.
#:
#: ``transparent`` for the reason the other two give, and checked again rather than assumed -
#: which was worth it: this game's default sheet is 56x56 where Gold's and Silver's are 40x40,
#: and it still has no alpha chunk at all. Only the transparent set carries ``tRNS``, in all
#: three.
SPRITE_SET = "generation-ii/crystal/transparent"


#: What Crystal hands over that the shared Generation 2 table does not describe.
#:
#: Four rows, and three of them are this game's whole reason for existing. It keeps everything
#: else :data:`johto.GBC_GIFTS` says: the same three in Elm's lab, the same Egg brought to Violet
#: City, the same Bill, the same Mania, the same trap floor under Mahogany Town.
GIFTS: dict[str, GiftDetails] = {
    **johto.GBC_GIFTS,
    # Gold and Silver sell a Dratini in the Goldenrod Game Corner for 2100 coins. Here the
    # Dragon Shrine is open - it is shut in those two, and everything to do with it with it -
    # and the Master hands one over for answering five questions about how a trainer should
    # treat a Pokemon. Answer all five right the first time and it knows ExtremeSpeed, which
    # nothing else in Generation 2 or 4 can teach it.
    "dratini": GiftDetail(
        npc="The Master of the Dragon Shrine",
        requirement=(
            "For passing his five-question quiz; answered perfectly the first time, it knows "
            "ExtremeSpeed"
        ),
    ),
    # The one the version is named around. Gold and Silver set all three beasts roaming; here
    # Suicune is seen three times on the overworld and then waits, and the Clear Bell is what
    # opens the tower to it.
    "suicune": GiftDetail(
        requirement=(
            "Clear Bell, from the Radio Tower Director once Team Rocket is beaten - and after "
            "Suicune has been seen in Cianwood City, on Route 42 and on Route 36"
        ),
    ),
    # And the hardest thing to get in three generations of this dataset.
    "ho-oh": GiftDetail(
        requirement=(
            "Rainbow Wing, from a Sage once the Hall of Fame is entered and all three legendary "
            "beasts are caught with your own trainer ID"
        ),
    ),
    "lugia": GiftDetail(
        requirement=(
            "Silver Wing, which has to be in the Bag for anything to be there at all - and one "
            "that faints or is run from does not come back"
        ),
    ),
    # The entry three generations of this dataset could not fill. The GS Ball was Japan's alone
    # on the cartridge; the Virtual Console release hands it over in every language, at the
    # Goldenrod Pokemon Center, once the Hall of Fame is entered. PokeAPI knows this and marks
    # the encounter `other-virtual-console`, which is the rarest thing a source can do: say out
    # loud that a re-release changed what is catchable.
    "celebi": GiftDetail(
        requirement=(
            "GS Ball, taken to the shrine in Ilex Forest. On the Virtual Console release it is "
            "handed over at the Goldenrod Pokemon Center once the Hall of Fame is entered; the "
            "cartridge only ever gave it out in Japan"
        ),
    ),
}

#: Babies PokeAPI files as gifts here, which they are not.
#:
#: It lists seven eggs at Route 34 for this game and none at all for Gold and Silver, and Route
#: 34 is the day care: what it is describing is breeding, in the one generation that invented
#: it. So they are taken back out and left to the egg table, which names the parents a player
#: actually has to leave there - and all three games then say the same thing about a Pichu.
NOT_A_GIFT: dict[str, str] = dict.fromkeys(
    ("pichu", "cleffa", "igglybuff", "tyrogue", "smoochum", "elekid", "magby"),
    "the day care on Route 34 hatches it, which this dataset records as breeding",
)


#: What PokeAPI calls Crystal when it says which version group an evolution started in.
#:
#: Its own, where Gold and Silver share one, which is what every third version in this dataset
#: has had. Nothing evolves differently here.
VERSION_GROUP = "crystal"

#: The eight trades Crystal offers: the generation's seven, and one nobody else has.
#:
#: The extra is in the same house in Pewter City that trades the Rapidash - a Xatu for a Haunter,
#: from a trainer the game records as PAUL. It is the only in-game trade in Generation 2 that is
#: not in all three releases.
TRADES = (
    *johto.GBC_TRADES,
    InGameTrade(gets="xatu", wants="haunter", location="Pewter City", npc="Paul"),
)


#: The one gift PokeAPI does not carry for this game.
#:
#: The Karate King hands over a level 10 Tyrogue in all three Generation 2 releases and PokeAPI
#: has the row for Gold and Silver only. Without it this game has no Tyrogue at all and no
#: Hitmon either: all three of those evolve from it and nothing here hatches one, so the gap
#: closes a circle rather than leaving a hole - which is exactly what the no-breeding-dead-ends
#: rule is watching for.
#:
#: Written down and cited, like the Bug-Catching Contest, and for the same reason: the
#: alternative is a dataset that says something is impossible when it is not.
HANDED_OVER = (
    RecordedGift(
        species="tyrogue",
        location="Mt. Mortar, B1F",
        level=10,
        npc="The Karate King",
        requirement="Beat him in Mt. Mortar",
    ),
)


#: In the Johto dex, in one or both halves of the pair, and never here.
#:
#: Five, and they are not a version switch: nothing in this game is held back for Gold or
#: Silver to have instead. They are five the third version simply dropped, which is the opposite
#: of what a third version usually does - Yellow, Emerald and Platinum all add.
#:
#: Read off each species' own game-locations table rather than from PokeAPI's silence, after the
#: legendary birds taught that lesson in Gold: every one of the five says "Trade" in its Crystal
#: row, and names routes in the halves that do have it.
#:
#: Every event is None, and Remoraid is the reason to say so out loud rather than assume it: it
#: is the only one of the five that Generation 2 ever distributed at all - twice, at Gotta Catch
#: 'Em All Station! in the United States in 2002 - and both went onto cartridges, which a 3DS
#: download is not.
ELSEWHERE_IN_GENERATION_2: dict[str, tuple[str, str | None]] = {
    # Silver's alone: Gold has no Vulpix either.
    "vulpix": ("Silver", None),
    # And Gold's alone, the same way round.
    "mankey": ("Gold", None),
    "mareep": ("Gold and Silver", None),
    "girafarig": ("Gold and Silver", None),
    "remoraid": ("Gold and Silver", None),
}

#: Dex entries no amount of playing this release will fill, and why.
#:
#: Fifteen, where each half of the pair has seventeen - and the two it does not share are the
#: whole point of this game. Celebi is not here: this is the only release in three generations
#: that produces one.
UNOBTAINABLE: dict[str, str] = {
    **johto.GBC_UNOBTAINABLE,
    **{
        species: johto.gbc_only_on(partner, event)
        for species, (partner, event) in ELSEWHERE_IN_GENERATION_2.items()
    },
}


def build(context: BuildContext) -> GameData:
    entries = dex_entries(context)

    return GameData(
        game=johto.gbc_release(
            game_id=GAME_ID,
            title="Pokémon Crystal Version",
            version="Crystal",
            released=RELEASED,
            sprite_set=SPRITE_SET,
        ),
        dex_entries=entries,
        acquisition_methods=acquisition_methods(context, entries),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """The 251 this game asks for, Bulbasaur #001 to Celebi #251.

    The same list as Gold and Silver's, numbered the same way and for the same reason: these
    games list in the Johto order and print the old numbers beside it, so a Crystal player reads
    Chikorita as #152. :mod:`gbc` carries the whole of it.

    What is not the same is the last entry. Celebi is #251 in all three, and in this one it is
    an entry a player can actually fill - which is why it is the one thing missing from the
    unobtainable table step 7 added.
    """
    return johto.gbc_dex_entries(context, game_id=GAME_ID, unobtainable=UNOBTAINABLE)


#: The day a person read the page the table below was typed from.
#:
#: Only one, and it is this game's rather than Johto's: the Suicune that stands in Mt. Mortar is
#: Crystal's alone, so :mod:`johto` has no date for it and is handed the citation instead of a
#: page name.
READ_ON = ReadByHand({"Mt._Mortar": date(2026, 9, 22)})


def acquisition_methods(
    context: BuildContext,
    entries: list[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something here: caught, handed over, traded for, evolved or hatched.

    The contest and the Tin Tower's name arrive with this, because both belong to the generation
    rather than to the pair: `gbc_acquisition_methods` hands every Generation 2 release the same
    ten hand-written slots and the same renaming, without asking which release it is.
    """
    return johto.gbc_acquisition_methods(
        context,
        game_id=GAME_ID,
        version=POKEAPI_VERSION,
        entries=entries,
        gifts=GIFTS,
        excluded=NOT_A_GIFT,
        version_group=VERSION_GROUP,
        trades=TRADES,
        eggs=johto.GBC_EGGS,
        handed_over=HANDED_OVER,
        handed_over_from=READ_ON("Mt._Mortar"),
    )


def edges() -> list[TransferEdge]:
    return johto.gbc_edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Crystal EN boxart.png")
