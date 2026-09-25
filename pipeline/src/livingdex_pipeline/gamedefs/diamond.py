"""Pokemon Diamond: everything but the smoke test.

Phase 2 steps 1 to 7 for this game: the 151 entries it asks a player to fill, every wild slot
that fills one, everything the game hands over or leaves standing in a corner, what its four
traders will swap for, what evolves into what on this cartridge, the sprite sheet a player of
it actually saw, and where the five entries it cannot produce could ever have come from.

Everything it shares with Pearl is in :mod:`sinnoh`, the dex included - the two of them number
those 151 entries identically. Everything it shares with the Johto cartridges of its own
generation is in :mod:`ds`. What is left is its name, which cartridge is its other half, and
which version PokeAPI is asked about.
"""

from __future__ import annotations

from datetime import date

from ..games import BuildContext, GameRegistry
from ..models import AcquisitionMethod, DexEntry, GameData, TransferEdge
from . import sinnoh

GAME_ID = "diamond"

#: The other half of the pair. Which species that switch decides is step 4's answer, not this
#: step's; all that is claimed here is that the two halves exist and know about each other.
PAIR_PARTNER = "pearl"

#: What PokeAPI calls this game when it lists which version an encounter belongs to. It is the
#: whole difference between this file and its partner's.
POKEAPI_VERSION = "diamond"

#: In the Sinnoh dex and never in this cartridge, and what step 7 found about each.
#:
#: Four, mirroring the other half exactly - which is what a version pair is. They are still
#: entries to fill, and the link between the two halves is how.
#:
#: Worked out *after* the trades and evolutions of step 5 rather than from the encounter tables
#: alone, deliberately. Doing it the other way round is what once put Banette on Ruby's list:
#: Mismagius is caught nowhere here either, but it evolves from something that comes over the
#: link, so it is not on this list.
#:
#: The value is the event that handed one out, and every one of them is None. Step 7 read the
#: *In events* table on all four pages and on the other half's four: not one distribution was
#: ever for Diamond or Pearl. Glameow and Stunky have no events at all, and what Misdreavus,
#: Murkrow, Cranidos and Shieldon do have is for Gold and Silver, for the Generation 3 games,
#: or for Black and White. That is the opposite of the Kanto pair, where a single day in a
#: shop in 2004 covered most of the fourteen - so the emptiness here is a finding, not a gap
#: nobody got round to.
ONLY_ON_PEARL: dict[str, str | None] = {
    "misdreavus": None,
    "glameow": None,
    "palkia": None,
}

#: The other half's fossil, which takes its own sentence: a fossil can travel held by a traded
#: Pokemon, so there are two ways across the link rather than one.
#:
#: None for the same reason as the four above: the one distribution it ever had was a Japanese
#: summer camp in 2012, for Black and White.
SHIELDON_EVENT: str | None = None

#: Dex entries no amount of playing this cartridge will fill, and why.
#:
#: A reason rather than a gap: the validator can tell "we checked and it cannot be caught" from
#: "we have not gathered this yet", and only the second is a fault.
UNOBTAINABLE: dict[str, str] = {
    "manaphy": sinnoh.manaphy_reason(sinnoh.PAIR_MANAPHY_EVENT),
    "shieldon": sinnoh.fossil_only_on("Pearl", "Armor Fossil", SHIELDON_EVENT),
    **{species: sinnoh.only_on("Pearl", event) for species, event in ONLY_ON_PEARL.items()},
}


def build(context: BuildContext) -> GameData:
    entries = dex_entries(context)

    return GameData(
        game=sinnoh.cartridge(
            game_id=GAME_ID,
            title="Pokémon Diamond Version",
            version="Diamond",
            released=date(2006, 9, 28),
            pair_partner=PAIR_PARTNER,
            sprite_set=sinnoh.PAIR_SPRITE_SET,
        ),
        dex_entries=entries,
        acquisition_methods=acquisition_methods(context, entries),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """The Sinnoh dex, the same 151 entries and numbering both halves show.

    The unobtainable table is what this step added: the four the other half keeps, its fossil,
    and the one that only a Pokemon Ranger cartridge produces.
    """
    return sinnoh.original_dex_entries(context, game_id=GAME_ID, unobtainable=UNOBTAINABLE)


def acquisition_methods(
    context: BuildContext,
    entries: list[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something here: caught, handed over, traded for or evolved."""
    return sinnoh.pair_acquisition_methods(
        context,
        game_id=GAME_ID,
        version=POKEAPI_VERSION,
        entries=entries,
    )


def edges() -> list[TransferEdge]:
    return sinnoh.edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Diamond EN boxart.jpg")
