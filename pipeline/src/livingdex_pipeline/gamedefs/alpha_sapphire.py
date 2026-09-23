"""Pokemon Alpha Sapphire: what it is, and the routes it brings.

Phase 2 step 1 for this game, and nothing after it yet. The other half of Omega Ruby, and the
same file with one word changed - the version PokeAPI is asked about. What is true of Hoenn is
in :mod:`hoenn`, what is true of Generation 6 is in :mod:`gen6`, and what the two halves share
is written once in whichever of those it belongs to.

The remake of Sapphire, which is in this dataset already and which it cannot trade with. See
:mod:`omega_ruby` for what a remake costs a region module.
"""

from __future__ import annotations

from datetime import date

from ..games import BuildContext, GameRegistry
from ..models import AcquisitionMethod, DexEntry, GameData, TransferEdge
from . import hoenn

GAME_ID = "alpha-sapphire"

#: The other half of the pair. Which species that switch decides is step 4's answer, not this
#: step's; all that is claimed here is that the two halves exist and know about each other.
PAIR_PARTNER = "omega-ruby"

#: What PokeAPI calls this game when it lists which version an encounter belongs to. It is the
#: whole difference between this file and its partner's - for the records that come from
#: PokeAPI at all, which here is the Mirage spots and what step 4 will add.
POKEAPI_VERSION = "alpha-sapphire"

#: How Bulbapedia's location pages spell this half in the Games column of a table.
#:
#: A letter rather than a word, and the cell's colour rather than the letter is what says
#: whether a species is here - which is why this is the whole of what tells the two halves
#: apart in the wild step.
WIKI_COLUMN = "AS"

#: The same day as its other half, as every pair in this dataset has had: 21 November 2014 in
#: Japan and nearly everywhere else, and a week later in Europe.
RELEASED = date(2014, 11, 21)


#: In the Hoenn dex and never in this half, and which one does have it.
#:
#: Seven, mirroring the other half exactly - which is what a version pair is. Seedot's whole
#: line is here where Ruby and Sapphire only split the first two stages, because the remakes'
#: Pokedex holds every stage of both lines.
#:
#: Worked out after the evolutions and the day care of step 5, not from the encounter tables.
ONLY_ON_OMEGA_RUBY: dict[str, str | None] = {
    "seedot": None,
    "nuzleaf": None,
    "shiftry": None,
    "mawile": hoenn.handed_out("the XY&Z Mawile in South Korea in the autumn of 2016"),
    "zangoose": None,
    "solrock": None,
    "groudon": hoenn.handed_out(
        "the Dahara City Groudon in Japan and South Korea over 2015"
    ),
}

#: Dex entries no amount of playing this release will fill, and why.
#:
#: Eight: the seven the other half keeps, and Jirachi, which nothing in any game has ever
#: produced. Four of the eight were handed out at some point, and step 7 says where.
UNOBTAINABLE: dict[str, str] = {
    "jirachi": hoenn.ORAS_JIRACHI_REASON,
    **{
        species: hoenn.gen6_only_on("Omega Ruby", event)
    for species, event in ONLY_ON_OMEGA_RUBY.items()
    },
}


def build(context: BuildContext) -> GameData:
    """The game entity, the list it shows, and every way this game fills it."""
    entries = dex_entries(context)

    return GameData(
        game=hoenn.gen6_cartridge(
            game_id=GAME_ID,
            title="Pokémon Alpha Sapphire",
            version="Alpha Sapphire",
            released=RELEASED,
            pair_partner=PAIR_PARTNER,
            sprite_set=hoenn.ORAS_SPRITE_SET,
        ),
        dex_entries=entries,
        acquisition_methods=acquisition_methods(context, entries),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """The same 211 entries and the same numbering its other half shows."""
    return hoenn.gen6_dex_entries(context, game_id=GAME_ID, unobtainable=UNOBTAINABLE)


def acquisition_methods(
    context: BuildContext,
    entries: list[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something here. Wild slots so far, read off the wiki."""
    return hoenn.gen6_acquisition_methods(
        context,
        game_id=GAME_ID,
        version=POKEAPI_VERSION,
        column=WIKI_COLUMN,
        entries=entries,
    )


def edges() -> list[TransferEdge]:
    return hoenn.gen6_edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Alpha Sapphire EN boxart.png")
