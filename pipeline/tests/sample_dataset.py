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
        TransferEdge(
            **{"from": "home"},
            to="sword",
            mechanism=TransferMechanism.HOME,
            direction=TransferDirection.BOTH_WAYS,
            filter=PresentInTargetDexFilter(),
        ),
    ]


def platinum() -> GameData:
    return GameData(
        game=Game(
            id="platinum",
            title="Pokemon Platinum Version",
            version="Platinum",
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
        ],
    )


def sword() -> GameData:
    return GameData(
        game=Game(
            id="sword",
            title="Pokemon Sword",
            version="Sword",
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
    """A source game for the Pal Park edge. Its own dex is not the point of the sample."""
    return GameData(
        game=Game(
            id="emerald",
            title="Pokemon Emerald Version",
            version="Emerald",
            generation=3,
            region="Hoenn",
            release=GameRelease.CARTRIDGE,
            national_dex_through=386,
            dex_source=DexSource.NATIONAL_DEX,
        )
    )


def diamond() -> GameData:
    return GameData(
        game=Game(
            id="diamond",
            title="Pokemon Diamond Version",
            version="Diamond",
            generation=4,
            region="Sinnoh",
            release=GameRelease.CARTRIDGE,
            national_dex_through=493,
            dex_source=DexSource.NATIONAL_DEX,
            pair_partner="pearl",
        )
    )


def home() -> GameData:
    """A transfer-only node: not a game, but the graph needs it to exist."""
    return GameData(
        game=Game(
            id="home",
            title="Pokemon HOME",
            version="HOME",
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
    for game in (platinum(), sword(), emerald(), diamond(), home()):
        writer.write_game(game)

    writer.write_index(stamp_for(VERSION, BUILT_ON), writer.known_games())
    return writer
