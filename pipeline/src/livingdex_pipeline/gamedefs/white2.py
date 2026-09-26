"""Pokemon White 2: entity and edges.

Phase 2 steps 1 to 7 for this game.

Not a third version, for the reasons Black 2 gives: these two are a sequel pair with their own
story and their own 301-entry Pokedex, so what :mod:`unova` knows about Black and White is not
theirs to reuse. Step 1 sees none of that - it is one more cartridge with a partner and a set
of routes - but every step after it has to ask which pair it is answering for.

The routes are the same four-cartridge set, so registering this game and its partner lights up
the four trades Black and White have been declaring into an empty space. The Pokemon Dream
Radar, which sends into these two and nowhere else, is not one of them: the thing at the other
end of that route is a 3DS download rather than a cartridge, so Phase 3 made it a row on the
entry instead of an edge. See :data:`unova.DREAM_RADAR`.
"""

from __future__ import annotations

from datetime import date

from ..games import BuildContext, GameRegistry
from ..models import AcquisitionMethod, DexEntry, GameData, TransferEdge
from . import unova

GAME_ID = "white-2"

#: The other half of the pair. The sequels are a pair of their own rather than two more
#: versions of Black and White, so this points at Black 2 and not at Black.
PAIR_PARTNER = "black-2"

#: How the Hidden Grotto page's Games column spells this half.
#:
#: A second name for the same game, from a second source, and it is not derivable from the
#: first: PokeAPI says "white-2" and a wiki table header says "W2". Written down rather than
#: built out of the id, because the next source will spell it a third way.
GROTTO_COLUMN = "W2"

#: What PokeAPI calls this game when it lists which version an encounter belongs to.
POKEAPI_VERSION = "white-2"

#: The same day as Black 2, as every pair in this dataset has been.
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
#: alone, because with four cartridges that is no longer the same thing. Zekrom is in Black 2,
#: as the pair partner always is, and it is also in White - which was written two years
#: earlier and did not have to change a line for that to become true.
#:
#: And step 7 found nothing at all against any of the thirteen. The first pair's four
#: legendaries each had a distribution, every one of them aimed at the half that could not catch
#: it; here not one of the thirteen was ever handed out for these two - not the ordinary
#: families and not the cover legendary either.
ELSEWHERE_IN_GENERATION_5: dict[str, tuple[str, ...]] = {
    # The five whole families, all of them from older generations and none of them anything
    # the first pair disagreed about.
    "spoink": ("Black 2",),
    "grumpig": ("Black 2",),
    "buneary": ("Black 2",),
    "lopunny": ("Black 2",),
    "magby": ("Black 2",),
    "magmar": ("Black 2",),
    "magmortar": ("Black 2",),
    # The three the first pair split too, so these have been in Black's half all along.
    "gothita": ("Black", "Black 2"),
    "gothorita": ("Black", "Black 2"),
    "gothitelle": ("Black", "Black 2"),
    "vullaby": ("Black", "Black 2"),
    "mandibuzz": ("Black", "Black 2"),
    # And the cover legendary, which is the one entry a player can see is missing from the
    # outside - White 2's box has Kyurem on it, and the dragon inside that Kyurem is Reshiram.
    "zekrom": ("White", "Black 2"),
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
            title="Pokémon White Version 2",
            version="White 2",
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
    registry.register(GAME_ID, build, edges(), box_art="White 2 EN boxart.png")
