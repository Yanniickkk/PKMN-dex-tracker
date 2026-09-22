"""Pokemon Ruby: entity, edges and dex.

Phase 2 steps 1 to 6 for this game: what is in it, how to get hold of each thing, and what
each one looks like. Only the events of step 7 are left, and the smoke test of step 8.

Everything it shares with Sapphire is in :mod:`hoenn`, the dex included - the two of them and
Emerald number those 202 entries identically. What is left is what is true about Ruby in
particular, which at this step is its name and which cartridge is its other half.
"""

from __future__ import annotations

from datetime import date

from ..games import BuildContext, GameRegistry
from ..models import AcquisitionMethod, DexEntry, GameData, TransferEdge
from . import hoenn

GAME_ID = "ruby"

#: The other half of the pair. Groudon, Zangoose and Solrock are here; Kyogre, Seviper and
#: Lunatone are on Sapphire, and the trade between them is the whole reason this app exists.
PAIR_PARTNER = "sapphire"

#: What PokeAPI calls this game when it lists which version an encounter belongs to. It is the
#: whole difference between this file and its partner's.
POKEAPI_VERSION = "ruby"

#: In the Hoenn dex and never in this cartridge, and what step 7 found about each.
#:
#: Six, mirroring the other half exactly - which is what a version pair is. They are still
#: entries to fill, and the trade route between the two halves is how. The value is the event
#: that handed one out, where there was one; the legendary never had a Generation 3 giveaway.
#:
#: Banette was in this list until the check that now guards it: this cartridge has wild Shuppet
#: and evolves one, so it was never a version exclusive at all. The list was worked out from
#: encounter tables before the evolutions existed, and nobody went back.
ONLY_ON_SAPPHIRE: dict[str, str | None] = {
    "lotad": hoenn.FIFTH_CAMPAIGN,
    "lombre": (
        "no event handed one out, but a Lotad from that same 2006 campaign evolves into one"
    ),
    "sableye": hoenn.FIFTH_CAMPAIGN_AND_NEW_YORK,
    "seviper": hoenn.FIFTH_CAMPAIGN_AND_NEW_YORK,
    "lunatone": hoenn.FIFTH_CAMPAIGN,
    "kyogre": None,
}

#: Dex entries no amount of playing this cartridge will fill, and why.
#:
#: A reason rather than a gap: the validator can tell "we checked and it cannot be caught" from
#: "we have not gathered this yet", and only the second is a fault.
UNOBTAINABLE: dict[str, str] = {
    "jirachi": hoenn.JIRACHI_REASON,
    "deoxys": hoenn.DEOXYS_REASON,
    **{species: hoenn.only_on("Sapphire", event) for species, event in ONLY_ON_SAPPHIRE.items()},
}


def build(context: BuildContext) -> GameData:
    entries = dex_entries(context)

    return GameData(
        game=hoenn.cartridge(
            game_id=GAME_ID,
            title="Pokémon Ruby Version",
            version="Ruby",
            released=date(2002, 11, 21),
            pair_partner=PAIR_PARTNER,
            sprite_set=hoenn.PAIR_SPRITE_SET,
        ),
        dex_entries=entries,
        acquisition_methods=acquisition_methods(context, entries),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """The Hoenn dex, the same 202 entries and numbering all three cartridges show.

    The unobtainable table is what step 4 added: the seven the other half keeps, and the one
    nothing in any Generation 3 game produces. What is left unexplained after this is evolutions,
    which is step 5.
    """
    return hoenn.dex_entries(context, game_id=GAME_ID, unobtainable=UNOBTAINABLE)


def acquisition_methods(
    context: BuildContext,
    entries: list[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something here: caught, handed over, evolved, hatched or traded for."""
    return hoenn.pair_acquisition_methods(
        context,
        game_id=GAME_ID,
        version=POKEAPI_VERSION,
        entries=entries,
    )


def edges() -> list[TransferEdge]:
    return hoenn.link_trade_edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Ruby EN boxart.png")
