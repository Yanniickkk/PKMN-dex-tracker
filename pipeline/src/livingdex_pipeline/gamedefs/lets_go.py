"""What the two Let's Go games share: a Kanto nothing else in the dataset has.

The last two games of Generation 7, and the two that :mod:`alola` is named for a region rather
than a generation because of. They are set in Kanto, they came out a year after Ultra Sun and
Ultra Moon, and they have nothing else in common with the four cartridges: no Alola dex, no
Bank, no trade with any of them, and a Pokedex of 153 where those have 802.

**Why this file and not** :mod:`kanto`. That module holds what is true of the place across the
generations that have visited it, and names anything belonging to one pair after its hardware -
``gb_dex_entries``, ``GBA_PAIR_SPRITE_SET``. The overlap with these two is real and it is step
2's and step 3's to find: the same 151 species, the same towns, the same routes, mostly the same
grass. What is here is what belongs to this pair and would be a lie about Kanto - a dex that
holds two species Kanto never had, a region where Alolan forms walk around, and a way in from a
phone. When those steps come, whatever turns out to be about Kanto moves there and is named
``switch_``, the way FireRed's is named ``gba_``.

**Why this file and not** :mod:`kanto` **plus a hardware module**, which is the other half of
that convention: :mod:`gb`, :mod:`gba`, :mod:`ds` and :mod:`gen6` each hold what a generation's
cartridges share, and the Switch equivalent would be a module these two would sit in alone.
Sword and Shield are on the same console and share none of this - they talk to HOME the ordinary
way, they trade with each other and with Brilliant Diamond and Scarlet in turn, and they are
Generation 8. A ``switch.py`` would have to say "except in Let's Go" about every line in it,
which is the sentence a ``gen7.py`` would have had to say about Alola.

**What these two cannot do is the shape of the whole file.** Bulbapedia's list of firsts says it
twice over: they are the first core games "to not be compatible with previous core series titles
in any way since Pokemon Ruby and Sapphire, and as such, the first to be unable to trade with
other core series games in their generation", and the first "to not feature breeding since its
introduction in Pokemon Gold and Silver". So the graph around them is three routes and not
thirty: the cable between the halves, and HOME in each direction - where the way back asks a
question no edge in this dataset had ever asked.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date

from ..games import BuildContext
from ..models import (
    AllSpeciesFilter,
    DexEntry,
    DexSource,
    DexTarget,
    Game,
    GameRelease,
    OriginRequirement,
    TransferDirection,
    TransferEdge,
    TransferMechanism,
)
from . import home, kanto

#: Kanto again, and the fifth pair of games to be set there.
REGION = kanto.REGION

#: Generation 7, which is where Bulbapedia puts them and not where a console would.
#:
#: They came out a year after Ultra Sun and Ultra Moon on the console that Generation 8 belongs
#: to, and they are still Generation 7: what decides it is the species the game knows, and
#: these know 153 of Generation 1's Kanto with one Mythical Pokemon added. Meltan is the only
#: species introduced by a Generation 7 game that is not in an Alola dex.
GENERATION = 7

#: One day, everywhere, in nine languages.
#:
#: The second release in this dataset with no Japanese date to prefer - Ultra Sun and Ultra Moon
#: were the first - and it went further than they did: these two shipped in Simplified and
#: Traditional Chinese on day one. Mainland China got its own release six years later, in
#: September 2024, which is a separate set of cartridges that trades only with itself; this
#: dataset holds the international one.
RELEASED = date(2018, 11, 16)

#: PokeAPI's name for the 153-entry list both halves show.
#:
#: Not :data:`kanto.DEX`, which is the 151 that Red, Blue, FireRed and LeafGreen show and which
#: this one contains exactly: the first 151 numbers agree entry for entry, and Meltan and
#: Melmetal are added at #152 and #153. Platinum's situation rather than Johto's - a number
#: these games share with an older one means what it always meant - and the opposite of what the
#: second Alola pair did to the first.
#:
#: The two at the end are the whole reason this is a separate list, and they are stranger than
#: the count makes them sound: **the only species introduced by a Generation 7 game that is not
#: in an Alola dex**, in a Pokedex that is otherwise Generation 1 from end to end. Neither can
#: be caught in Kanto. Meltan comes out of a Mystery Box in Pokemon GO and through the GO Park,
#: and Melmetal is what 400 Meltan Candy makes of one - in GO, not here. What that means for
#: these two entries is step 4's answer.
DEX = "letsgo-kanto"

#: The two halves, which are the whole of what these games can reach by cable.
#:
#: Named here rather than worked out from each game's ``pair_partner`` because two other things
#: need the pair as a set: the trade between them, and the origin HOME asks about - where being
#: from *either* half is one answer.
PAIR = ("lets-go-pikachu", "lets-go-eevee")


def cartridge(
    *,
    game_id: str,
    title: str,
    version: str,
    pair_partner: str,
    sprite_set: str | None = None,
) -> Game:
    """One half of the pair, with everything the two of them agree about filled in.

    No ``national_dex_through``: these have no National Pokedex, like the four Alola cartridges
    before them, and unlike those four they cannot hold what is not in their own list either.
    Their boxes take the 153 species the Pokedex shows and nothing else, so the grid is that
    list - which is what :class:`DexSource.GAME_DEX` says and step 2 fills in.
    """
    return Game(
        id=game_id,
        title=title,
        version=version,
        generation=GENERATION,
        region=REGION,
        release=GameRelease.CARTRIDGE,
        released=RELEASED,
        national_dex_through=None,
        dex_source=DexSource.GAME_DEX,
        pair_partner=pair_partner,
        sprite_set=sprite_set,
    )


def dex_entries(
    context: BuildContext,
    *,
    game_id: str,
    unobtainable: Mapping[str, str] | None = None,
) -> list[DexEntry]:
    """The Let's Go Pokedex, Bulbasaur #001 to Melmetal #153, as both halves number it.

    One function for the two of them, the way :func:`kanto.dex_entries` is one for four: the
    halves show the same list in the same order, and what differs between them is which entries
    their own Kanto never holds - the ``unobtainable`` table each game brings.

    No ``dex`` name on the entries. These games show one list, so a number can only belong to
    one; X and Y's three are the only reason that field exists.

    **No forms either, and that is a real answer rather than a gap.** The Pokedex here has 153
    entries and an Alolan Rattata does not get one of its own - it shares Rattata's, exactly as
    it does in Sun and Moon. What the GO Park counts separately for its candy minigame is
    another matter and is the park's own bookkeeping. Which forms these games actually hold is
    step 8's, and until it runs the form table deliberately says they hold none; see
    :data:`forms.FORMS_NAMED_BY_THE_GAME`.
    """
    reasons = unobtainable or {}
    api = context.require_api()

    return [
        DexEntry(
            game=game_id,
            target=DexTarget(species=species),
            number=number,
            unobtainable_reason=reasons.get(species),
        )
        for number, species in api.pokedex(DEX, refresh=context.refresh)
    ]


def trade_edges(game_id: str) -> list[TransferEdge]:
    """The one cable these games have, which runs to the other half of the pair.

    Every pair since Red and Blue has had this edge and only these two have had nothing beside
    it. There is no route to Ultra Sun, which came out a year earlier on hardware in the same
    living room; there is no GTS and no Wonder Trade; and Bank, which is how the rest of
    Generation 7 reaches anything, does not know these games exist.

    One thing the filter cannot say, because a filter is about species and this is about one
    Pokemon: the partner Pikachu or Eevee the player starts with may not be traded at all, nor
    put into HOME. Every other Pikachu in the game may.
    """
    return [
        TransferEdge(
            **{"from": game_id},
            to=partner,
            mechanism=TransferMechanism.TRADE,
            direction=TransferDirection.BOTH_WAYS,
            filter=AllSpeciesFilter(),
        )
        for partner in PAIR
        if partner != game_id
    ]


def home_edges(game_id: str) -> list[TransferEdge]:
    """HOME both ways, and the way back is unlike every other edge in the dataset.

    The deposit is the ordinary one: HOME holds everything, so it takes anything these games
    can. The withdrawal is the reason :class:`OriginRequirement` exists. Bulbapedia states it
    plainly - only a Pokemon originally from Let's Go, Pikachu! or Let's Go, Eevee! can be moved
    into either of them - and it adds that anything arriving in HOME from Bank or the GO
    Transporter is converted to Sword and Shield's format on the way in and can never enter them
    at all.

    So this is not :func:`home.home_edges`, which is what the Generation 8 and 9 games get, and
    :mod:`home` says so in its own docstring rather than leaving it to be discovered here. That
    function's withdrawal asks whether the target's dex lists the species; this one asks where
    the Pokemon was caught, and every species it would refuse is in the dex already.

    **What it means for a living dex is worth saying out loud: this route adds nothing.** HOME
    can hand these games back only what they produced in the first place, so no tile in a Let's
    Go grid is ever filled by way of it. It is in the graph because it is true and because a
    player who has put a box on the shelf should be able to see that they can take it down
    again, not because it makes anything obtainable.
    """
    return [
        TransferEdge(
            **{"from": game_id},
            to=home.NODE,
            mechanism=TransferMechanism.HOME,
            direction=TransferDirection.ONE_WAY,
            filter=AllSpeciesFilter(),
        ),
        TransferEdge(
            **{"from": home.NODE},
            to=game_id,
            mechanism=TransferMechanism.HOME,
            direction=TransferDirection.ONE_WAY,
            filter=AllSpeciesFilter(),
            origin=OriginRequirement(games=list(PAIR)),
        ),
    ]


def edges(game_id: str) -> list[TransferEdge]:
    """Every route one of these two brings: the cable to its other half, and HOME both ways.

    Three, where an Alola cartridge brings five and a Generation 4 one brings eleven.

    **And one route that is deliberately not here: the GO Park.** Pokemon GO sends Kanto's 151,
    their Alolan forms and Meltan into these games one way, into a complex of twenty parks that
    replaced the Safari Zone in Fuchsia City, and it is the only way a player gets an Alolan
    Rattata or a Meltan at all. It is not an edge because GO is not a game in this dataset and
    should not be: it has no Pokedex to fill, nothing in it is caught in the sense this tracker
    means, and :mod:`home` already writes down that decision for the same reason. What arrives
    through the park is a way of obtaining a species in *these* games, which makes it step 4's
    answer rather than a route between two entities - the same shape as an egg from an NPC.
    """
    return [*trade_edges(game_id), *home_edges(game_id)]
