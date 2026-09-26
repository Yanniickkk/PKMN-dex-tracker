"""Pokemon Black 2: entity and edges.

Phase 2 steps 1 to 7 for this game.

Not a third version. Black 2 is a sequel - two years later in the same Unova, with its own
story, its own half of the map and a Pokedex of 301 entries rather than 156 - and the series
has never done that before or since. Step 1 cannot see any of it: a sequel and a third version
are the same shape of thing to this step, one cartridge with a partner and a set of routes.
What it does mean is that none of Black's later steps can be leaned on. The dex is a different
list, not a longer one, and the grass is in different places, so :mod:`unova` keeps the two
pairs apart wherever they disagree.

The routes are the same four-cartridge set Black and White declare, which is what lights their
held-back edges up: all four trade with each other, Generation 4 comes in over the Poke
Transfer, and Poke Transporter goes out to Bank. One route into this game is missing on purpose
- the Pokemon Dream Radar on the 3DS sends its catches down into these two and into nothing
else - because the thing at the other end is not a cartridge. Phase 3 gave it a shape that is
not a route at all: :class:`models.OutsideAcquisition`, a row on the entry rather than an edge
between two games. :data:`unova.DREAM_RADAR` is what it sends.
"""

from __future__ import annotations

from datetime import date

from ..games import BuildContext, GameRegistry
from ..models import AcquisitionMethod, DexEntry, GameData, TransferEdge
from . import unova

GAME_ID = "black-2"

#: The other half of the pair. The sequels are a pair of their own rather than two more
#: versions of Black and White, so this points at White 2 and not at White.
PAIR_PARTNER = "white-2"

#: How the Hidden Grotto page's Games column spells this half.
#:
#: A second name for the same game, from a second source, and it is not derivable from the
#: first: PokeAPI says "black-2" and a wiki table header says "B2". Written down rather than
#: built out of the id, because the next source will spell it a third way.
GROTTO_COLUMN = "B2"

#: What PokeAPI calls this game when it lists which version an encounter belongs to.
POKEAPI_VERSION = "black-2"

#: Japan, June 2012 - twenty-one months after Black, and the last main-series pair on the DS.
RELEASED = date(2012, 6, 23)


#: In the sequels' dex and never in this half, and which other Generation 5 games do have it.
#:
#: Thirteen, mirroring the other half exactly, and almost twice the first pair's seven. What
#: grew is the part nobody thinks of as a version exclusive: the first pair split five of its
#: own new species and the two cover legendaries, and these two split five whole families
#: from older generations as well. A player who knows Black and White's list by heart knows
#: less than half of this one.
#:
#: Each entry names every other Generation 5 game that has it rather than the pair partner
#: alone, because with four cartridges that is no longer the same thing. Reshiram is in White 2,
#: as the pair partner always is, and it is also in Black - which was written two years
#: earlier and did not have to change a line for that to become true.
#:
#: And step 7 found nothing at all against any of the thirteen. The first pair's four
#: legendaries each had a distribution, every one of them aimed at the half that could not catch
#: it; here not one of the thirteen was ever handed out for these two - not the ordinary
#: families and not the cover legendary either.
ELSEWHERE_IN_GENERATION_5: dict[str, tuple[str, ...]] = {
    # The five whole families, all of them from older generations and none of them anything
    # the first pair disagreed about.
    "numel": ("White 2",),
    "camerupt": ("White 2",),
    "skitty": ("White 2",),
    "delcatty": ("White 2",),
    "elekid": ("White 2",),
    "electabuzz": ("White 2",),
    "electivire": ("White 2",),
    # The three the first pair split too, so these have been in White's half all along.
    "solosis": ("White", "White 2"),
    "duosion": ("White", "White 2"),
    "reuniclus": ("White", "White 2"),
    "rufflet": ("White", "White 2"),
    "braviary": ("White", "White 2"),
    # And the cover legendary, which is the one entry a player can see is missing from the
    # outside - Black 2's box has Kyurem on it, and the dragon inside that Kyurem is Zekrom.
    "reshiram": ("Black", "White 2"),
}

#: Dex entries no amount of playing this release will fill, and why.
#:
#: Twenty: the seven neither sequel reaches and the thirteen the other half keeps.
UNOBTAINABLE: dict[str, str] = {
    **unova.B2W2_UNOBTAINABLE,
    **{
        species: unova.only_on(elsewhere)
        for species, elsewhere in ELSEWHERE_IN_GENERATION_5.items()
    },
}


def build(context: BuildContext) -> GameData:
    entries = dex_entries(context)

    return GameData(
        game=unova.cartridge(
            game_id=GAME_ID,
            title="Pokémon Black Version 2",
            version="Black 2",
            released=RELEASED,
            pair_partner=PAIR_PARTNER,
            sprite_set=unova.SPRITE_SET,
        ),
        dex_entries=entries,
        acquisition_methods=acquisition_methods(context, entries),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """The Unova dex as the sequels number it: 301 entries, the same list in both halves.

    Not Black's list with more on the end. It keeps all 156 of them and adds 145 from older
    generations, and only the first twelve numbers survive the renumbering - which is why
    :mod:`unova` names the two dexes apart. What the two halves of this pair disagree about is
    which of these entries a player can fill, and the unobtainable table is that answer: seven
    neither sequel reaches and thirteen this one leaves to the other.
    """
    return unova.b2w2_dex_entries(context, game_id=GAME_ID, unobtainable=UNOBTAINABLE)


def acquisition_methods(
    context: BuildContext,
    entries: list[DexEntry],
) -> list[AcquisitionMethod]:
    """Every way to get something here. Wild slots so far, read for this version alone."""
    return unova.b2w2_acquisition_methods(
        context,
        game_id=GAME_ID,
        version=POKEAPI_VERSION,
        column=GROTTO_COLUMN,
        entries=entries,
    )


def edges() -> list[TransferEdge]:
    return unova.edges(GAME_ID)


def register(registry: GameRegistry) -> None:
    registry.register(GAME_ID, build, edges(), box_art="Black 2 EN boxart.png")
