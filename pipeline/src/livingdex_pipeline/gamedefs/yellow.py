"""Pokemon Yellow: everything but the smoke test.

Phase 2 steps 1 to 7 for this game: the 151 entries it asks a player to fill, every wild
slot that fills one, everything the game hands over or leaves standing in one spot, what its
seven traders will swap for, what evolves into what here, the sprite sheet a player of it
actually saw, and where the eight entries it cannot produce could ever have come from.

This is the Virtual Console release rather than the 1998 cartridge, and it is the only Yellow in
this dataset - see :mod:`vc` for why. Everything it shares with Red and Blue is in :mod:`kanto`
and :mod:`gb`. What is left is its name, that it is nobody's other half, and which version
PokeAPI is asked about.

The Pikachu that walks behind the player is the reason this game exists and is nothing this
dataset has a field for. What it does change is what can be caught, which is step 3's business.
"""

from __future__ import annotations

from datetime import date

from ..games import BuildContext, GameRegistry
from ..gifts import GiftDetail
from ..models import AcquisitionMethod, DexEntry, GameData, GiftKind, TransferEdge
from ..trades import InGameTrade
from . import kanto

GAME_ID = "yellow"

#: What PokeAPI calls this game when it lists which version an encounter belongs to.
POKEAPI_VERSION = "yellow"

#: The Virtual Console release, worldwide on the same day as Red and Blue - which the cartridges
#: were not: Yellow followed them by two years. The entity is the 3DS one, so it is the 2016
#: date that belongs here.
RELEASED = date(2016, 2, 27)

#: Where Yellow's own battle sprites live in the sprite repository.
#:
#: Its own sheet, and the one thing in this file that is not a rewrite of the pair's but a
#: redrawing of it: the same 151 Pokemon, drawn again for the same hardware. It is the reason
#: this game gets a sprite set at all rather than pointing at Red and Blue's.
#:
#: ``transparent`` for the reason :mod:`kanto` gives about the pair's sheet, and it is the same
#: story here: the default Yellow sheet is a 40x40 palette image with no alpha channel, so every
#: sprite would arrive in a white box. The transparent set is the same drawings at 96x96 with
#: the background cut out.
SPRITE_SET = "generation-i/yellow/transparent"


#: What Yellow hands over that Kanto's shared table gets wrong, and the one thing only it has.
#:
#: Four entries, and they are the whole reason this game exists. Professor Oak's lab holds one
#: Pikachu rather than a choice of three, and the three it replaced are scattered across Kanto
#: in the hands of strangers - which means a player of Yellow ends up with all four rather than
#: one, and that no two of them are asked for in the same way.
#:
#: Everything else is Generation 1's table unchanged: the same fossils on Cinnabar, the same
#: Hitmon in the same dojo, the same Eevee in the Celadon Mansion, the same Mewtwo behind the
#: same Elite Four. Yellow's Game Corner needs no table either, though it charges differently
#: and stocks different species - Vulpix and Wigglytuff for coins here, and both Scyther and
#: Pinsir where the pair split them - because the coins arrive as a condition on the encounter.
GIFTS: dict[str, GiftDetail] = {
    **kanto.GB_GIFTS,
    # The one that walks behind you. It cannot be evolved and will not enter its ball, which is
    # why Raichu is a problem this game has and the other two do not - step 5 answers that.
    "pikachu": GiftDetail(
        kind=GiftKind.STARTER,
        npc="Professor Oak",
        requirement="The only starter here; the other three are handed over later, one at a time",
    ),
    # Not a starter in this game and not Oak's: a girl in a house west of the Pokemon Center,
    # who is looking after it and wants to know the Pikachu behind you is well treated first.
    "bulbasaur": GiftDetail(
        npc="A girl in a house in Cerulean City",
        requirement="Pikachu's friendship at 147 or higher",
    ),
    "charmander": GiftDetail(
        npc="A boy on Route 24, past Nugget Bridge",
        requirement="He gives it to a trainer he believes will look after it better",
    ),
    "squirtle": GiftDetail(
        npc="Officer Jenny in Vermilion City",
        requirement="Thunder Badge, from the gym in the same town",
    ),
}


#: What PokeAPI calls Yellow when it says which version group an evolution started in.
#:
#: Its own, where Red and Blue share one. Nothing evolves differently here, but the Pikachu Oak
#: hands over refuses the Thunder Stone, and no grass in the game holds another - so the one
#: evolution this generation is named for is the one a player of Yellow cannot perform.
VERSION_GROUP = "yellow"

#: The seven trades Yellow offers, and what each one wants.
#:
#: Not one of them is a trade Red and Blue have. Those two offer nine and Yellow offers seven,
#: in some of the same places, and the only species handed over in both is the Mr. Mime on
#: Route 2 - which wants an Abra there and a Clefairy here. It is the same rewrite the grass
#: got. Gone with the pair's trades are the only ways either of the other two has to a Jynx and
#: a Farfetch'd; Yellow answers the second with wild ones on Routes 12 and 13 and does not
#: answer the first at all, which is step 7's business.
#:
#: Nobody is named here for the reason the pair's table gives: Generation 1 stores no trainer
#: name on a traded Pokemon, only the hardcoded "TRAINER". The nicknames it does give are MILES,
#: RICKY, GURIO, SPIKE, BUFFY, CEZANNE and STICKY, in the order below, and there is no field for
#: them - so they are written down here rather than lost.
TRADES = (
    InGameTrade(gets="mr-mime", wants="clefairy", location="Route 2"),
    InGameTrade(gets="machoke", wants="cubone", location="Underground Path"),
    InGameTrade(gets="dugtrio", wants="lickitung", location="Route 11"),
    InGameTrade(gets="parasect", wants="tangela", location="Route 18"),
    InGameTrade(gets="rhydon", wants="golduck", location="Cinnabar Island, Pokemon Lab"),
    InGameTrade(gets="dewgong", wants="growlithe", location="Cinnabar Island, Pokemon Lab"),
    InGameTrade(gets="muk", wants="kangaskhan", location="Cinnabar Island, Pokemon Lab"),
)


#: In the Kanto dex and never in this release, which of the other two does have it, and what
#: step 7 found about each.
#:
#: Eight rather than the six a half of a pair keeps from the other half, and they are not a
#: version split at all: Yellow follows the anime, so the Pokemon the anime had no use for left
#: the game and did not come back anywhere. The whole Weedle line went, and Ekans, Meowth and
#: Koffing with it - Team Rocket's own - along with Electabuzz, Magmar and Jynx.
#:
#: Worked out after the trades and evolutions of step 5 rather than from the encounter tables,
#: for the reason Red's list gives. Kakuna, Beedrill, Arbok, Persian and Weezing are caught
#: nowhere here either and are not on this list, because each evolves from something that comes
#: over the link. Raichu is the sharpest case of all: no grass in Yellow holds a Pikachu and the
#: one Oak hands over refuses the Thunder Stone - but a Pikachu traded in is not that Pikachu
#: and evolves like any other, so Raichu is reachable and is not listed.
#:
#: Every event is None, and the reason is the one Red's table gives: the Generation 1
#: distributions went onto Game Boy cartridges, and only Mew was ever handed out for a Virtual
#: Console release.
ELSEWHERE_IN_GENERATION_1: dict[str, tuple[str, str | None]] = {
    "weedle": ("Red and Blue", None),
    "ekans": ("Red", None),
    "meowth": ("Blue", None),
    "koffing": ("Red and Blue", None),
    # The odd one: no grass in either half holds a Jynx either. What the pair has is an NPC in
    # Cerulean City who will swap one for a Poliwhirl, and Yellow's traders swap other things.
    "jynx": ("Red and Blue", None),
    "electabuzz": ("Red", None),
    "magmar": ("Blue", None),
}

#: Dex entries no amount of playing this release will fill, and why.
#:
#: A reason rather than a gap: the validator can tell "we checked and it cannot be caught" from
#: "we have not gathered this yet", and only the second is a fault.
UNOBTAINABLE: dict[str, str] = {
    "mew": kanto.GB_MEW_REASON,
    **{
        species: kanto.gb_only_on(partner, event)
        for species, (partner, event) in ELSEWHERE_IN_GENERATION_1.items()
    },
}


def build(context: BuildContext) -> GameData:
    entries = dex_entries(context)

    return GameData(
        game=kanto.gb_release(
            game_id=GAME_ID,
            # The box says "Special Pikachu Edition" underneath, and so does every catalogue.
            title="Pokémon Yellow Version: Special Pikachu Edition",
            version="Yellow",
            released=RELEASED,
            sprite_set=SPRITE_SET,
        ),
        dex_entries=entries,
        acquisition_methods=acquisition_methods(context, entries),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """The Kanto dex, the same 151 entries and numbering all five Kanto games show.

    Yellow rearranged a great deal of what is *in* those games - the starter, which of the three
    the rival takes, where half of Kanto's grass holds something else entirely - and renumbered
    nothing. The dex it shows is Red and Blue's, in Red and Blue's order.

    Here it is the whole of it, as in the other two: a living dex in Yellow is 151 tiles rather
    than 151 of something larger, because there is no National Dex in this generation to be a
    part of.

    The unobtainable table is what step 7 added: the seven the anime had no use for, and Mew.
    """
    return kanto.dex_entries(context, game_id=GAME_ID, unobtainable=UNOBTAINABLE)


def acquisition_methods(
    context: BuildContext,
    entries: list[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something here: caught, handed over, traded for or evolved.

    Yellow brings its own gift table rather than the pair's, and that is not tidiness. It hands
    over a Pikachu that will not stay in its ball and the other three starters one at a time
    from strangers; its traders ask for different things, and PokeAPI files its evolutions under
    a version group of its own. Reusing Red and Blue's tables would print their Kanto and call
    it Yellow's.
    """
    return kanto.gb_acquisition_methods(
        context,
        game_id=GAME_ID,
        version=POKEAPI_VERSION,
        entries=entries,
        gifts=GIFTS,
        version_group=VERSION_GROUP,
        trades=TRADES,
    )


def edges() -> list[TransferEdge]:
    return kanto.gb_edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Yellow EN boxart.png")
