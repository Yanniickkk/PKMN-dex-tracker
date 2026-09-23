"""Pokemon Platinum: everything but the smoke test.

Phase 2 steps 1 to 7 for this game: the 210 entries it asks a player to fill, every wild slot
that fills one, everything the game hands over or leaves standing in a corner, what its four
traders will swap for, what evolves into what on this cartridge, the sprite sheet a player of it
actually saw, and where the five entries it cannot produce could ever have come from.

It reads from :mod:`sinnoh` the way Emerald reads from :mod:`hoenn`: a third version is still
one of the region's cartridges, and writing its region and its reach out by hand was how its
Pal Park edges got left behind when Ruby and Sapphire arrived.

The dex is the one thing it does not share with Diamond and Pearl. Emerald shows the same 202
entries the Hoenn pair does; Platinum widened Sinnoh's list from 151 to 210, so a third version
turns out not to be a third version in every respect.
"""

from __future__ import annotations

from datetime import date

from ..breeding import EggFrom
from ..games import BuildContext, GameRegistry
from ..gifts import GiftDetail
from ..models import AcquisitionMethod, DexEntry, GameData, GiftKind, TransferEdge
from . import sinnoh

GAME_ID = "platinum"

#: What PokeAPI calls this game when it lists which version an encounter belongs to. The same
#: word as its id here, unlike Ruby and Sapphire, whose ids and versions only happen to match.
POKEAPI_VERSION = "platinum"

#: What PokeAPI calls this game when it says which version group an evolution started in. Its
#: own group, the way Emerald has its own: the third version is not the pair, and asking for
#: ``diamond-pearl`` here would miss everything Platinum added.
POKEAPI_VERSION_GROUP = "platinum"

#: Where this game's battle sprites live in the sprite repository.
#:
#: Its own sheet, not the pair's. Platinum redrew every one of them, which is why the pair's
#: constant is named for the pair: a Sinnoh player sees different artwork depending on which of
#: the three cartridges is in the slot. Emerald did the same to Ruby and Sapphire's.
SPRITE_SET = "generation-iv/platinum"


#: What only the game knows about each thing it hands over or leaves standing in one spot.
#:
#: Platinum shares none of this with Diamond and Pearl, which is the surprise of the third
#: version: it moved the starters, it swapped where Porygon comes from, it added four more
#: things to pick up, and it changed the terms on both cover legendaries.
GIFTS: dict[str, GiftDetail] = {
    # Route 201, not Lake Verity. Rowan stops you on the way out of Twinleaf Town here.
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
    # Both fossils are here, where the pair had one each - but a save file still only gets one
    # of them, and which one is decided by a number the player never chose. It is the only
    # requirement in this dataset that turns on something set when the game was started.
    "cranidos": GiftDetail(
        kind=GiftKind.FOSSIL,
        npc="A scientist in the Oreburgh Mining Museum",
        requirement=(
            "Skull Fossil, dug up in the Underground - and only in a save whose Trainer ID "
            "ends in an odd number"
        ),
    ),
    "shieldon": GiftDetail(
        kind=GiftKind.FOSSIL,
        npc="A scientist in the Oreburgh Mining Museum",
        requirement=(
            "Armor Fossil, dug up in the Underground - and only in a save whose Trainer ID "
            "ends in an even number"
        ),
    ),
    # PokeAPI drops the day of the week here, though it carries it for the pair and Bulbapedia
    # says Platinum kept it. Written out rather than trusted to the conditions.
    "drifloon": GiftDetail(
        requirement="On a Friday, once Team Galactic is beaten at the Valley Windworks",
    ),
    "spiritomb": GiftDetail(
        requirement=(
            "An Odd Keystone in the Hallowed Tower, after talking to 32 people in the Underground"
        ),
    ),
    "riolu": GiftDetail(
        kind=GiftKind.EGG,
        npc="Riley",
        requirement="Given on Iron Island, once Team Galactic is beaten there",
    ),
    # New here: the pair have a Togepi only on Route 230, and only with the Poke Radar.
    "togepi": GiftDetail(
        kind=GiftKind.EGG,
        npc="Cynthia",
        requirement="Given in the Eterna City gate, once Jupiter is beaten",
    ),
    "eevee": GiftDetail(npc="Bebe"),
    # A gift here, a Game Corner prize in the pair. Nothing about Platinum's Game Corner sells
    # a Pokemon at all.
    "porygon": GiftDetail(npc="A person in Veilstone City"),
    "rotom": GiftDetail(
        requirement="The television in the Old Chateau, after dark; only one",
    ),
    "uxie": GiftDetail(requirement="Only one in the game"),
    "azelf": GiftDetail(requirement="Only one in the game"),
    # Both cover legendaries are here, and neither is the walk-up encounter the pair had at the
    # Spear Pillar: Giratina drags them off, and they are waiting at level 70 after the Elite
    # Four, for a player carrying the right Orb.
    "dialga": GiftDetail(
        requirement=(
            "Only one; at the Spear Pillar after the Hall of Fame, with the Adamant Orb from "
            "Cynthia's grandmother in Celestic Town"
        ),
    ),
    "palkia": GiftDetail(
        requirement=(
            "Only one; at the Spear Pillar after the Hall of Fame, with the Lustrous Orb from "
            "Cynthia's grandmother in Celestic Town"
        ),
    ),
    # Giratina is deliberately absent. It stands in two places on different terms - the
    # Distortion World, and Turnback Cave if it was not caught there - and this table has one
    # line per species, so a sentence here would be wrong about one of the two. The conditions
    # on the rows say it better than a single line could.
}


#: The babies nothing in Sinnoh produces, and what has to be left at the day care for one.
#:
#: Two, where Diamond and Pearl have none - and not because Platinum's grass is poorer. Its dex
#: is 59 entries longer, and two of the 59 are babies whose grown forms it counts but whose own
#: forms live nowhere in the region. Electabuzz is on the Valley Windworks and Magmar in Stark
#: Mountain; what hatches from them is not.
#:
#: Either stage works as the parent. Naming only the unevolved one would make Electivire look
#: like a dead end to anyone who had already evolved theirs.
EGGS: dict[str, EggFrom] = {
    "elekid": EggFrom(parents=("electabuzz", "electivire")),
    "magby": EggFrom(parents=("magmar", "magmortar")),
}

#: In the Sinnoh dex and never in this cartridge, and what step 7 found about each.
#:
#: All four of the pair's version exclusives, which is the surprise. Emerald took most of Ruby
#: and Sapphire's exclusives in; Platinum took none of these, so a third version turns out not
#: to be the generous one by default. Two are Diamond's and two are Pearl's, so the sentence
#: names the half that has them.
#:
#: Their evolutions are not on this list and that is deliberate. Mismagius is caught nowhere
#: here either, but it evolves from a Misdreavus that comes over the link - the distinction
#: that once put Banette on Ruby's list.
#:
#: Every value is None, and step 7 read all four *In events* tables to say so. Stunky and
#: Glameow have never been distributed at all, in any game. Murkrow and Misdreavus have been,
#: twice each - for Gold and Silver in 2002, and for the Generation 3 games in 2006 - and
#: neither giveaway was for a game that existed yet. Same answer as the pair got.
ONLY_ON_DIAMOND: dict[str, str | None] = {
    "murkrow": None,
    "stunky": None,
}

ONLY_ON_PEARL: dict[str, str | None] = {
    "misdreavus": None,
    "glameow": None,
}

#: Dex entries no amount of playing this cartridge will fill, and why.
#:
#: A reason rather than a gap: the validator can tell "we checked and it cannot be caught" from
#: "we have not gathered this yet", and only the second is a fault.
UNOBTAINABLE: dict[str, str] = {
    "manaphy": sinnoh.manaphy_reason(sinnoh.THIRD_MANAPHY_EVENT),
    **{species: sinnoh.only_on("Diamond", event) for species, event in ONLY_ON_DIAMOND.items()},
    **{species: sinnoh.only_on("Pearl", event) for species, event in ONLY_ON_PEARL.items()},
}


def build(context: BuildContext) -> GameData:
    entries = dex_entries(context)

    return GameData(
        game=sinnoh.cartridge(
            game_id=GAME_ID,
            title="Pokémon Platinum Version",
            version="Platinum",
            released=date(2008, 9, 13),
            # The third version of Diamond and Pearl rather than half of a pair.
            pair_partner=None,
            sprite_set=SPRITE_SET,
        ),
        dex_entries=entries,
        acquisition_methods=acquisition_methods(context, entries),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """The extended Sinnoh dex: the pair's 151, their numbers kept, and 59 more after them.

    The unobtainable table is what this step added: all four of the pair's version exclusives,
    and the one that only a Pokemon Ranger cartridge produces.
    """
    return sinnoh.extended_dex_entries(context, game_id=GAME_ID, unobtainable=UNOBTAINABLE)


def acquisition_methods(
    context: BuildContext,
    entries: list[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something here: caught, handed over, traded for or evolved.

    The four traders are the one thing it does share with the pair, down to the houses they
    stand in. The version group is its own, and asking for the pair's would miss everything
    Platinum added - Gallade, Magnezone, Rhyperior, the whole point of a third version. And it
    is the one Sinnoh game with anything to hatch.

    No excluded table: PokeAPI lists both fossils for Platinum and this time it is right. The
    Underground here holds whichever the Trainer ID asks for, so the cartridge revives both and
    a save file gets one.
    """
    return sinnoh.acquisition_methods(
        context,
        game_id=GAME_ID,
        version=POKEAPI_VERSION,
        entries=entries,
        gifts=GIFTS,
        version_group=POKEAPI_VERSION_GROUP,
        trades=sinnoh.TRADES,
        eggs=EGGS,
        form_changes=sinnoh.PLATINUM_FORM_CHANGES,
    )


def edges() -> list[TransferEdge]:
    return sinnoh.edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Platinum EN boxart.png")
