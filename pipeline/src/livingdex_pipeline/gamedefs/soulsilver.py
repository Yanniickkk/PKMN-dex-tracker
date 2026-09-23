"""Pokemon SoulSilver: everything but the smoke test.

Phase 2 steps 1 to 7 for this game: the 256 entries its own Pokedex holds, every wild slot in
the two regions it is set across, everything it hands over or leaves standing in one spot, what
its ten traders will swap for, what evolves and what hatches, the sprite sheet a player of it
actually saw, and where the eight entries it cannot produce could ever have come from.

Everything it shares with HeartGold is in :mod:`johto`, which is about the region rather than
the generation - Gold, Silver and Crystal are set there too. Everything it shares with the
Sinnoh cartridges of its own generation is in :mod:`ds`. What is left is its name, which
cartridge is its other half, and which version PokeAPI is asked about.
"""

from __future__ import annotations

from datetime import date

from ..games import BuildContext, GameRegistry
from ..models import AcquisitionMethod, DexEntry, GameData, TransferEdge
from . import johto

GAME_ID = "soulsilver"

#: The other half of the pair. Which species that switch decides is step 4's answer, not this
#: step's; all that is claimed here is that the two halves exist and know about each other.
PAIR_PARTNER = "heartgold"

#: What PokeAPI calls this game when it lists which version an encounter belongs to. It is the
#: whole difference between this file and its partner's.
POKEAPI_VERSION = "soulsilver"

#: The Japanese release, as for every other game in the dataset.
RELEASED = date(2009, 9, 12)

#: In the Johto dex and never in this cartridge, and what step 7 found about each.
#:
#: Five, against the other half's six - a version pair does not have to be symmetrical, and
#: this one is not.
#:
#: Worked out *after* the trades and evolutions of step 5 rather than from the encounter tables
#: alone, deliberately. Arcanine is caught nowhere here either, but it evolves from a Growlithe
#: that comes over the link, so it is not on this list - the distinction that once put Banette
#: on Ruby's list.
#:
#: Every value is None, and that is the finding: not one distribution of any of these five was
#: ever for HeartGold or SoulSilver. What they have is for Generation 1 to 3 or for Black and
#: White.
ONLY_ON_HEARTGOLD: dict[str, str | None] = {
    "spinarak": None,
    "growlithe": None,
    "mankey": None,
    "gligar": None,
    "phanpy": None,
    # Found by the pass that walked every game's evolutions back to what starts them. Mantine
    # surfaces on Route 41 in HeartGold and nowhere at all here, and this half's only other
    # route to one is a Mantyke - which hatches from a Mantine. A circle, and the entry had
    # never been written off.
    "mantine": None,
}

#: Dex entries no amount of playing this cartridge will fill, and why.
#:
#: A reason rather than a gap: the validator can tell "we checked and it cannot be caught" from
#: "we have not gathered this yet", and only the second is a fault.
UNOBTAINABLE: dict[str, str] = {
    "mew": johto.mew_reason(johto.DS_PAIR_MEW_EVENT),
    "celebi": johto.celebi_reason(johto.DS_PAIR_CELEBI_EVENT),
    **{species: johto.only_on("HeartGold", event) for species, event in ONLY_ON_HEARTGOLD.items()},
}


def build(context: BuildContext) -> GameData:
    entries = dex_entries(context)

    return GameData(
        game=johto.ds_cartridge(
            game_id=GAME_ID,
            title="Pokémon SoulSilver Version",
            version="SoulSilver",
            released=RELEASED,
            pair_partner=PAIR_PARTNER,
            sprite_set=johto.DS_PAIR_SPRITE_SET,
        ),
        dex_entries=entries,
        acquisition_methods=acquisition_methods(context, entries),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """The Johto dex, the same 256 entries and numbering both halves show.

    The unobtainable table is what step 7 added: the other half's exclusives, and the two the
    series has always handed out rather than hidden.
    """
    return johto.updated_dex_entries(context, game_id=GAME_ID, unobtainable=UNOBTAINABLE)


def acquisition_methods(
    context: BuildContext,
    entries: list[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something here. Step 3 fills the wild slots; the rest is steps 4 and 5."""
    return johto.ds_acquisition_methods(
        context,
        game_id=GAME_ID,
        version=POKEAPI_VERSION,
        entries=entries,
    )


def edges() -> list[TransferEdge]:
    return johto.ds_edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="SoulSilver EN boxart.jpg")
