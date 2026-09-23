"""A small dataset that uses every shape in the schema.

Written to ``tests/expected/sample-dataset`` and committed, because a C# test reads the same
files. If the two sides ever disagree about the wire format, one of the two suites fails.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from livingdex_pipeline.emit import DatasetWriter, stamp_for
from livingdex_pipeline.models import (
    AllSpeciesFilter,
    BreedingAcquisition,
    DexEntry,
    DexSource,
    DexTarget,
    EncounterMethod,
    EvolutionAcquisition,
    EvolutionRule,
    EvolutionTrigger,
    Form,
    FormKind,
    Game,
    GameData,
    GameRelease,
    GiftAcquisition,
    GiftKind,
    HistoryWindow,
    LevelRange,
    LocationCondition,
    MinimumLevelCondition,
    NationalDexRangeFilter,
    PokemonType,
    PresentInTargetDexFilter,
    SourceCitation,
    Species,
    TradeAcquisition,
    TransferDirection,
    TransferEdge,
    TransferMechanism,
    WildAcquisition,
)

RETRIEVED_ON = date(2026, 9, 21)
BUILT_ON = date(2026, 9, 21)
VERSION = "0.1.0-sample"

CITATION = SourceCitation(
    source="bulbapedia",
    url="https://bulbapedia.bulbagarden.net/wiki/Route_201",
    retrieved_on=RETRIEVED_ON,
)


def species() -> list[Species]:
    return [
        Species(
            id="chimchar",
            national_dex_number=390,
            name="Chimchar",
            types=[PokemonType.FIRE],
            evolution_chain="chimchar",
        ),
        Species(
            id="monferno",
            national_dex_number=391,
            name="Monferno",
            types=[PokemonType.FIRE, PokemonType.FIGHTING],
            evolution_chain="chimchar",
        ),
        Species(
            id="vulpix",
            national_dex_number=37,
            name="Vulpix",
            types=[PokemonType.FIRE],
            evolution_chain="vulpix",
        ),
        # In Platinum's dex here and produced by nothing, so the coverage report has one entry
        # of each kind to count: caught here, a transfer away, and checked and stated.
        Species(
            id="darkrai",
            national_dex_number=491,
            name="Darkrai",
            types=[PokemonType.DARK],
            evolution_chain="darkrai",
        ),
    ]


def forms() -> list[Form]:
    return [
        Form(
            id="vulpix-alola",
            species="vulpix",
            name="Alolan",
            kind=FormKind.REGIONAL,
            games=["sword"],
            types=[PokemonType.ICE],
        ),
        # No types: this one is typed like its species, and the field should be absent.
        Form(
            id="pikachu-female",
            species="pikachu",
            name="Female",
            kind=FormKind.GENDER,
            games=["platinum", "sword"],
        ),
    ]


def evolution_rules() -> list[EvolutionRule]:
    return [
        EvolutionRule(
            id="chimchar-to-monferno",
            **{"from": DexTarget(species="chimchar")},
            to=DexTarget(species="monferno"),
            trigger=EvolutionTrigger.LEVEL_UP,
            conditions=[MinimumLevelCondition(level=14)],
        ),
        EvolutionRule(
            id="eevee-to-leafeon",
            **{"from": DexTarget(species="eevee")},
            to=DexTarget(species="leafeon"),
            trigger=EvolutionTrigger.LEVEL_UP,
            conditions=[LocationCondition(location="Eterna Forest")],
        ),
    ]


def transfers() -> list[TransferEdge]:
    return [
        TransferEdge(
            **{"from": "emerald"},
            to="platinum",
            mechanism=TransferMechanism.PAL_PARK,
            direction=TransferDirection.ONE_WAY,
            filter=NationalDexRangeFilter(**{"from": 1}, to=386),
        ),
        TransferEdge(
            **{"from": "diamond"},
            to="platinum",
            mechanism=TransferMechanism.TRADE,
            direction=TransferDirection.BOTH_WAYS,
            filter=AllSpeciesFilter(),
        ),
        # Two one-way edges rather than one both-ways edge, which is what HOME really is and
        # what it has to be: the filter asks whether the game being transferred *into* lists the
        # species, and read backwards that question is asked of HOME, whose dex is empty.
        TransferEdge(
            **{"from": "sword"},
            to="home",
            mechanism=TransferMechanism.HOME,
            direction=TransferDirection.ONE_WAY,
            filter=AllSpeciesFilter(),
        ),
        TransferEdge(
            **{"from": "home"},
            to="sword",
            mechanism=TransferMechanism.HOME,
            direction=TransferDirection.ONE_WAY,
            filter=PresentInTargetDexFilter(),
        ),
        TransferEdge(
            **{"from": "bank"},
            to="home",
            mechanism=TransferMechanism.HOME,
            direction=TransferDirection.ONE_WAY,
            filter=AllSpeciesFilter(),
        ),
        # The two shapes a real Bank edge has, on the only game this sample has to hang them
        # on. Bank never spoke to a DS game, and the pair is here because what the C# side has
        # to be able to read is a deposit that takes everything beside a withdrawal that asks
        # where a Pokemon has been - which is the one thing in the schema no record can answer.
        TransferEdge(
            **{"from": "platinum"},
            to="bank",
            mechanism=TransferMechanism.POKE_TRANSPORTER,
            direction=TransferDirection.ONE_WAY,
            filter=AllSpeciesFilter(),
        ),
        TransferEdge(
            **{"from": "bank"},
            to="platinum",
            mechanism=TransferMechanism.BANK,
            direction=TransferDirection.ONE_WAY,
            filter=AllSpeciesFilter(),
            history=HistoryWindow(**{"from": 3}, to=6),
        ),
    ]


def platinum() -> GameData:
    return GameData(
        game=Game(
            id="platinum",
            title="Pokemon Platinum Version",
            version="Platinum",
            released=date(2000, 1, 1),
            generation=4,
            region="Sinnoh",
            release=GameRelease.CARTRIDGE,
            national_dex_through=493,
            dex_source=DexSource.NATIONAL_DEX,
        ),
        dex_entries=[
            DexEntry(game="platinum", target=DexTarget(species="chimchar"), number=4),
            DexEntry(game="platinum", target=DexTarget(species="monferno"), number=5),
            # Known not to be catchable here, as opposed to simply undocumented.
            DexEntry(
                game="platinum",
                target=DexTarget(species="darkrai"),
                number=6,
                unobtainable_reason="event distribution only",
            ),
        ],
        acquisition_methods=[
            GiftAcquisition(
                game="platinum",
                target=DexTarget(species="chimchar"),
                gift_kind=GiftKind.STARTER,
                location="Route 201",
                npc="Professor Rowan",
                level=5,
                source=CITATION,
            ),
            WildAcquisition(
                game="platinum",
                target=DexTarget(species="starly"),
                location="Route 202",
                method="walk",
                levels=LevelRange(minimum=3, maximum=4),
                rate_percent=55.0,
                time_of_day="morning",
                source=CITATION,
            ),
            EvolutionAcquisition(
                game="platinum",
                target=DexTarget(species="monferno"),
                rule="chimchar-to-monferno",
                source=CITATION,
            ),
            TradeAcquisition(
                game="platinum",
                target=DexTarget(species="chatot"),
                location="Eterna City",
                wants=DexTarget(species="buizel"),
                source=CITATION,
            ),
            # One of Pichu's two parents, so the sample exercises "any one parent is enough"
            # rather than tripping the breeding dead-end check on its own data.
            # A slot with something a player has to arrange first, so the field is pinned on
            # both sides of the wire: Generation 4 is full of them.
            WildAcquisition(
                game="platinum",
                target=DexTarget(species="pikachu"),
                location="Trophy Garden",
                method=EncounterMethod.WALK,
                levels=LevelRange(minimum=16, maximum=18),
                requirement="Only on days Mr. Backlot mentions it in the Trophy Garden",
                source=CITATION,
            ),
            # Two parents and a requirement, so the list and the optional field are both pinned.
            BreedingAcquisition(
                game="platinum",
                target=DexTarget(species="pichu"),
                parents=[DexTarget(species="pikachu"), DexTarget(species="raichu")],
                location="Solaceon Town",
                requirement="A parent holding a Light Ball hatches a Pichu that knows Volt Tackle",
                source=CITATION,
            ),
        ],
    )


def sword() -> GameData:
    return GameData(
        game=Game(
            id="sword",
            title="Pokemon Sword",
            version="Sword",
            released=date(2000, 1, 1),
            generation=8,
            region="Galar",
            release=GameRelease.CARTRIDGE,
            dex_source=DexSource.GAME_DEX,
            pair_partner="shield",
        ),
        dex_entries=[
            DexEntry(game="sword", target=DexTarget(species="vulpix"), number=100),
            # A form entry, to pin how a target with a form is written.
            DexEntry(
                game="sword",
                target=DexTarget(species="vulpix", form="vulpix-alola"),
                number=101,
            ),
        ],
        acquisition_methods=[
            WildAcquisition(
                game="sword",
                target=DexTarget(species="vulpix"),
                location="Route 2",
                method=EncounterMethod.WALK,
                levels=LevelRange(minimum=10, maximum=14),
                weather="intense sun",
                source=CITATION,
            ),
            WildAcquisition(
                game="sword",
                target=DexTarget(species="vulpix", form="vulpix-alola"),
                location="Route 2",
                method=EncounterMethod.WALK,
                levels=LevelRange(minimum=10, maximum=14),
                weather="snowstorm",
                source=CITATION,
            ),
        ],
    )


def emerald() -> GameData:
    """A source game for the Pal Park edge. Its own dex is not the point of the sample.

    It is the one game here with a sprite set, so the field is pinned on both sides of the wire.
    Nothing builds it, so nothing tries to fetch the set.
    """
    return GameData(
        game=Game(
            id="emerald",
            title="Pokemon Emerald Version",
            version="Emerald",
            released=date(2000, 1, 1),
            generation=3,
            region="Hoenn",
            release=GameRelease.CARTRIDGE,
            national_dex_through=386,
            dex_source=DexSource.NATIONAL_DEX,
            sprite_set="generation-iii/emerald",
        )
    )


def diamond() -> GameData:
    return GameData(
        game=Game(
            id="diamond",
            title="Pokemon Diamond Version",
            version="Diamond",
            released=date(2000, 1, 1),
            generation=4,
            region="Sinnoh",
            release=GameRelease.CARTRIDGE,
            national_dex_through=493,
            dex_source=DexSource.NATIONAL_DEX,
            pair_partner="pearl",
        )
    )


def shield() -> GameData:
    """Sword's other half, and the one game here that names its Pokedexes.

    A pair only holds up when both halves are there, and this half carries the newest shape in
    the schema: two entries, the same number, different lists. X and Y are why the field exists
    - three Kalos Pokedexes that each start at #001 - and without the name on each entry those
    two hundred below are one list in which #001 means several things.
    """
    return GameData(
        game=Game(
            id="shield",
            title="Pokemon Shield",
            version="Shield",
            released=date(2000, 1, 1),
            generation=8,
            region="Galar",
            release=GameRelease.CARTRIDGE,
            dex_source=DexSource.GAME_DEX,
            pair_partner="sword",
        ),
        dex_entries=[
            DexEntry(
                game="shield",
                target=DexTarget(species="vulpix"),
                dex="Galar",
                number=100,
            ),
            DexEntry(
                game="shield",
                target=DexTarget(species="chimchar"),
                dex="Isle of Armor",
                number=100,
            ),
        ],
        # A dex entry with no way to fill it is a game nobody has gathered yet, and the sample
        # has to pass its own validator - so this half hands both of them over.
        acquisition_methods=[
            GiftAcquisition(
                game="shield",
                target=DexTarget(species="vulpix"),
                gift_kind=GiftKind.NPC_GIFT,
                location="Wedgehurst",
                npc="A boy on the station platform",
                level=5,
                source=CITATION,
            ),
            GiftAcquisition(
                game="shield",
                target=DexTarget(species="chimchar"),
                gift_kind=GiftKind.NPC_GIFT,
                location="Master Dojo",
                npc="Mustard",
                level=5,
                source=CITATION,
            ),
            # A way that is recorded and does not count, beside a way that does. Kalos's Friend
            # Safari is the real one: true tables in a place a player cannot be sent to.
            WildAcquisition(
                game="shield",
                target=DexTarget(species="chimchar"),
                location="Friend Safari",
                sub_area="Fire",
                method=EncounterMethod.WALK,
                levels=LevelRange(minimum=30, maximum=30),
                rate_percent=33.0,
                does_not_count="a friend code decided what it holds",
                source=CITATION,
            ),
        ],
    )


def pearl() -> GameData:
    """Diamond's other half, for the same reason."""
    return GameData(
        game=Game(
            id="pearl",
            title="Pokemon Pearl Version",
            version="Pearl",
            released=date(2000, 1, 1),
            generation=4,
            region="Sinnoh",
            release=GameRelease.CARTRIDGE,
            national_dex_through=493,
            dex_source=DexSource.NATIONAL_DEX,
            pair_partner="diamond",
        )
    )


def bank() -> GameData:
    """The other transfer-only node, and the one an edge here reads a history window off."""
    return GameData(
        game=Game(
            id="bank",
            title="Pokemon Bank",
            version="Bank",
            released=date(2013, 12, 25),
            generation=6,
            region="",
            release=GameRelease.SERVICE,
            dex_source=DexSource.GAME_DEX,
        )
    )


def home() -> GameData:
    """A transfer-only node: not a game, but the graph needs it to exist."""
    return GameData(
        game=Game(
            id="home",
            title="Pokemon HOME",
            version="HOME",
            released=date(2000, 1, 1),
            generation=8,
            region="none",
            release=GameRelease.SERVICE,
            dex_source=DexSource.GAME_DEX,
        )
    )


def write_sample_dataset(root: Path) -> DatasetWriter:
    writer = DatasetWriter(root)
    writer.write_species(species())
    writer.write_forms(forms())
    writer.write_evolution_rules(evolution_rules())
    writer.write_transfers(transfers())
    for game in (
        platinum(),
        sword(),
        shield(),
        emerald(),
        diamond(),
        pearl(),
        home(),
        bank(),
    ):
        writer.write_game(game)

    writer.write_index(stamp_for(VERSION, BUILT_ON), writer.known_games())
    return writer
