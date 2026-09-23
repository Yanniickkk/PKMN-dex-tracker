"""Pokemon Omega Ruby: what it is, and the routes it brings.

Phase 2 step 1 for this game, and nothing after it yet. What it says about itself is here; what
is true of Hoenn is in :mod:`hoenn`, and what is true of the four cartridges of its generation -
the trades between all of them, the National Dex to Volcanion, Bank standing where the Poke
Transfer stood - is in :mod:`gen6`.

A remake beside the game it remakes, which this dataset has done twice before - FireRed next
to Red, HeartGold next to Gold - and will do again for Sinnoh. What the two share is the region
and little else: the Pokedex is 211 entries rather than 202, the pictures are models rather
than drawings, and they cannot exchange so much as one Pokemon. What a Ruby has to travel to
reach here is Pal Park into Generation 4, the Poke Transfer into Generation 5, Poke Transporter
into Bank and Bank into this game - five games and two services, and every step of it is
already declared.

What is left for this file is its name, that Alpha Sapphire is its other half, which version
PokeAPI is asked about, and the day it came out. That day is nearly the same worldwide date X
and Y had a year earlier - Japan, America, Australia, Korea, Hong Kong and Taiwan together, and
Europe a week behind - so the Japanese date this dataset keeps is also the date almost everybody
saw.
"""

from __future__ import annotations

from datetime import date

from ..games import BuildContext, GameRegistry
from ..models import AcquisitionMethod, DexEntry, GameData, TransferEdge
from . import hoenn

GAME_ID = "omega-ruby"

#: The other half of the pair. Which species that switch decides is step 4's answer, not this
#: step's; all that is claimed here is that the two halves exist and know about each other.
PAIR_PARTNER = "alpha-sapphire"

#: What PokeAPI calls this game when it lists which version an encounter belongs to. It is the
#: whole difference between this file and its partner's - for the records that come from
#: PokeAPI at all, which here is the Mirage spots and what step 4 will add.
POKEAPI_VERSION = "omega-ruby"

#: How Bulbapedia's location pages spell this half in the Games column of a table.
#:
#: A letter rather than a word, and the cell's colour rather than the letter is what says
#: whether a species is here - which is why this is the whole of what tells the two halves
#: apart in the wild step.
WIKI_COLUMN = "OR"

#: Japan, America, Australia, Korea, Hong Kong and Taiwan on one day in November 2014; Europe on
#: the twenty-eighth. Not quite the single worldwide day X and Y had, and nothing like the
#: months every game before that generation spent out in Japan and nowhere else.
RELEASED = date(2014, 11, 21)


#: In the Hoenn dex and never in this half, and which one does have it.
#:
#: Seven, and the other half keeps seven too - which is what a version pair has always looked
#: like, and what Ruby and Sapphire looked like with six. The three extra faces are the
#: Lotad line's third stage and Ludicolo's: the remakes' Pokedex has every stage of both lines
#: where Generation 3's stopped short, so a line that is missing is now three entries rather
#: than two.
#:
#: Worked out after the evolutions and the day care of step 5 rather than from the encounter
#: tables, for the reason Black's file gives: an evolution record exists for a Ludicolo this
#: game can never start, and only a table built after those records knows the difference.
#:
#: The value is the event that handed one out, where there was one. Two of the seven had
#: one: the legendary, which the Dahara City giveaways covered in 2015, and one other.
ONLY_ON_ALPHA_SAPPHIRE: dict[str, str | None] = {
    "lotad": None,
    "lombre": None,
    "ludicolo": None,
    # One of the two the wiki's event tables turned up, and a distribution with a joke in it:
    # the other Sableye of Generation 6, Shigeki Morimoto's, went to Alpha Sapphire alone -
    # which is the half that catches them.
    "sableye": hoenn.handed_out("the Mega Campaign Sableye in Japan in January 2016"),
    "seviper": None,
    "lunatone": None,
    "kyogre": hoenn.handed_out(
        "the Dahara City Kyogre in Japan and South Korea over 2015"
    ),
}

#: Dex entries no amount of playing this release will fill, and why.
#:
#: Eight: the seven the other half keeps, and Jirachi, which nothing in any game has ever
#: produced. Four of the eight were handed out at some point, and step 7 says where.
UNOBTAINABLE: dict[str, str] = {
    "jirachi": hoenn.ORAS_JIRACHI_REASON,
    **{
        species: hoenn.gen6_only_on("Alpha Sapphire", event)
    for species, event in ONLY_ON_ALPHA_SAPPHIRE.items()
    },
}


def build(context: BuildContext) -> GameData:
    """The game entity, the list it shows, and every way this game fills it."""
    entries = dex_entries(context)

    return GameData(
        game=hoenn.gen6_cartridge(
            game_id=GAME_ID,
            title="Pokémon Omega Ruby",
            version="Omega Ruby",
            released=RELEASED,
            pair_partner=PAIR_PARTNER,
            sprite_set=hoenn.ORAS_SPRITE_SET,
        ),
        dex_entries=entries,
        acquisition_methods=acquisition_methods(context, entries),
    )


def dex_entries(context: BuildContext) -> list[DexEntry]:
    """The Hoenn dex of the remakes: 211 entries, the same ones both halves show.

    Not the list Ruby shows. The nine Generation 4 relatives these games added go in beside
    their families, so this game's #032 is Gallade where Ruby's is Surskit, and 171 entries
    disagree in the same way. Which of them a player here cannot fill is steps 4 to 7.
    """
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
    registry.register(GAME_ID, build, edges(), box_art="Omega Ruby EN boxart.png")
