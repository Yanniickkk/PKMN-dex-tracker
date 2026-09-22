"""The dataset schema, mirroring ``LivingDex.Core.Reference`` on the C# side.

The two sides are coupled only by the JSON these produce, so anything that changes here has
to change there. ``tests/test_models.py`` pins the wire shape, and a C# test reads a sample
emitted by this module, so a drift on either side fails a build rather than surfacing in the
app months later.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class Model(BaseModel):
    """Base for everything written to disk: camelCase out, either spelling in."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
        frozen=True,
    )

    def to_json(self) -> str:
        return self.model_dump_json(by_alias=True, exclude_none=True, indent=2)


class GameRelease(StrEnum):
    CARTRIDGE = "cartridge"
    VIRTUAL_CONSOLE = "virtualConsole"
    #: Bank and HOME: not games, but nodes in the transfer graph.
    SERVICE = "service"


class DexSource(StrEnum):
    NATIONAL_DEX = "nationalDex"
    GAME_DEX = "gameDex"


class PokemonType(StrEnum):
    NORMAL = "normal"
    FIRE = "fire"
    WATER = "water"
    ELECTRIC = "electric"
    GRASS = "grass"
    ICE = "ice"
    FIGHTING = "fighting"
    POISON = "poison"
    GROUND = "ground"
    FLYING = "flying"
    PSYCHIC = "psychic"
    BUG = "bug"
    ROCK = "rock"
    GHOST = "ghost"
    DRAGON = "dragon"
    DARK = "dark"
    STEEL = "steel"
    FAIRY = "fairy"


class FormKind(StrEnum):
    REGIONAL = "regional"
    FUNCTIONAL = "functional"
    COSMETIC = "cosmetic"
    GENDER = "gender"


class TransferMechanism(StrEnum):
    TRADE = "trade"
    TIME_CAPSULE = "timeCapsule"
    PAL_PARK = "palPark"
    POKE_TRANSFER = "pokeTransfer"
    POKE_TRANSPORTER = "pokeTransporter"
    BANK = "bank"
    HOME = "home"


class TransferDirection(StrEnum):
    ONE_WAY = "oneWay"
    BOTH_WAYS = "bothWays"


class EvolutionTrigger(StrEnum):
    LEVEL_UP = "levelUp"
    USE_ITEM = "useItem"
    TRADE = "trade"
    OTHER = "other"


class EncounterMethod(StrEnum):
    WALK = "walk"
    SURF = "surf"
    OLD_ROD = "oldRod"
    GOOD_ROD = "goodRod"
    SUPER_ROD = "superRod"
    ROCK_SMASH = "rockSmash"
    HEADBUTT = "headbutt"
    HONEY_TREE = "honeyTree"
    SWARM = "swarm"
    OTHER = "other"


class GiftKind(StrEnum):
    STARTER = "starter"
    FOSSIL = "fossil"
    NPC_GIFT = "npcGift"
    EGG = "egg"
    STATIC_ENCOUNTER = "staticEncounter"


class DexTarget(Model):
    """A species, or one specific form of it."""

    species: str
    form: str | None = None

    def __str__(self) -> str:
        return f"{self.species}/{self.form}" if self.form else self.species


class SourceCitation(Model):
    source: str
    url: str | None = None
    retrieved_on: date


class Game(Model):
    id: str
    title: str
    version: str
    generation: int
    region: str
    release: GameRelease
    #: The day it first went on sale, in Japan. The original release rather than a local one,
    #: because the order games came out in is one order and every region saw it shifted: Emerald
    #: reached Japan before FireRed reached America.
    #:
    #: Required, unlike the fields below it: every game has one, and it is what orders a picker.
    released: date
    # The number, not a yes-or-no: the dex builder needs to know where the National Dex stops.
    national_dex_through: int | None = None
    dex_source: DexSource
    pair_partner: str | None = None
    #: Which battle sprites this game shows, as the directory they are written to - for example
    #: ``generation-iii/emerald``. A game with none of its own leaves it out and falls back to
    #: the shared set, which is the current artwork for every species.
    sprite_set: str | None = None


class Species(Model):
    id: str
    national_dex_number: int
    name: str
    types: list[PokemonType]
    evolution_chain: str


class Form(Model):
    id: str
    species: str
    name: str
    kind: FormKind
    games: list[str]
    # Only when the form is typed differently from its species, as every regional form is.
    types: list[PokemonType] | None = None


class DexEntry(Model):
    game: str
    target: DexTarget
    number: int
    # Why this entry cannot be filled in this game, when that is a known fact rather than a
    # gap in the data. A reason rather than a flag, so the validator can tell "we checked,
    # and it cannot be caught" apart from "we have nothing".
    unobtainable_reason: str | None = None


# --- Species filters on transfer edges -------------------------------------------------------


class AllSpeciesFilter(Model):
    filter: Literal["all"] = "all"


class NationalDexRangeFilter(Model):
    filter: Literal["nationalDexRange"] = "nationalDexRange"
    from_: int = Field(alias="from")
    to: int


class PresentInTargetDexFilter(Model):
    filter: Literal["presentInTargetDex"] = "presentInTargetDex"


SpeciesFilter = Annotated[
    AllSpeciesFilter | NationalDexRangeFilter | PresentInTargetDexFilter,
    Field(discriminator="filter"),
]


class TransferEdge(Model):
    from_: str = Field(alias="from")
    to: str
    mechanism: TransferMechanism
    direction: TransferDirection
    filter: SpeciesFilter


# --- Evolution -------------------------------------------------------------------------------


class MinimumLevelCondition(Model):
    condition: Literal["minimumLevel"] = "minimumLevel"
    level: int


class HeldItemCondition(Model):
    condition: Literal["heldItem"] = "heldItem"
    item: str


class UsedItemCondition(Model):
    condition: Literal["usedItem"] = "usedItem"
    item: str


class FriendshipCondition(Model):
    condition: Literal["friendship"] = "friendship"
    minimum: int


class TimeOfDayCondition(Model):
    condition: Literal["timeOfDay"] = "timeOfDay"
    time_of_day: str


class LocationCondition(Model):
    condition: Literal["location"] = "location"
    location: str


class KnownMoveCondition(Model):
    condition: Literal["knownMove"] = "knownMove"
    move: str


class GenderCondition(Model):
    condition: Literal["gender"] = "gender"
    gender: str


class TradePartnerCondition(Model):
    condition: Literal["tradePartner"] = "tradePartner"
    species: str


class OtherCondition(Model):
    condition: Literal["other"] = "other"
    description: str


EvolutionCondition = Annotated[
    MinimumLevelCondition
    | HeldItemCondition
    | UsedItemCondition
    | FriendshipCondition
    | TimeOfDayCondition
    | LocationCondition
    | KnownMoveCondition
    | GenderCondition
    | TradePartnerCondition
    | OtherCondition,
    Field(discriminator="condition"),
]


class EvolutionRule(Model):
    id: str
    from_: DexTarget = Field(alias="from")
    to: DexTarget
    trigger: EvolutionTrigger
    conditions: list[EvolutionCondition] = Field(default_factory=list)


# --- Acquisition -----------------------------------------------------------------------------


class LevelRange(Model):
    minimum: int
    maximum: int


class GiftAcquisition(Model):
    kind: Literal["gift"] = "gift"
    game: str
    target: DexTarget
    gift_kind: GiftKind
    location: str
    npc: str | None = None
    level: int | None = None
    requirement: str | None = None
    source: SourceCitation


class WildAcquisition(Model):
    kind: Literal["wild"] = "wild"
    game: str
    target: DexTarget
    location: str
    sub_area: str | None = None
    method: EncounterMethod
    levels: LevelRange
    rate_percent: float | None = None
    time_of_day: str | None = None
    season: str | None = None
    weather: str | None = None
    #: What else has to be true for this slot to hold this species: a Game Boy Advance cartridge
    #: in the slot underneath, the day the Great Marsh rotates it in, a honey tree of the right
    #: group. Time of day, season and weather have fields of their own; this is everything else,
    #: and a slot without it is one a player meets by playing.
    requirement: str | None = None
    source: SourceCitation


class EvolutionAcquisition(Model):
    kind: Literal["evolution"] = "evolution"
    game: str
    target: DexTarget
    rule: str
    source: SourceCitation


class BreedingAcquisition(Model):
    kind: Literal["breeding"] = "breeding"
    game: str
    target: DexTarget
    #: Any one of these, left at the day care, can produce the target. A baby often has
    #: several parents that work - a Pichu hatches from a Pikachu or a Raichu - and naming
    #: only the first would make the other look like a way that does not exist.
    parents: list[DexTarget]
    location: str
    requirement: str | None = None
    source: SourceCitation


class TradeAcquisition(Model):
    kind: Literal["trade"] = "trade"
    game: str
    target: DexTarget
    location: str
    npc: str | None = None
    wants: DexTarget
    requirement: str | None = None
    source: SourceCitation


AcquisitionMethod = Annotated[
    GiftAcquisition
    | WildAcquisition
    | EvolutionAcquisition
    | BreedingAcquisition
    | TradeAcquisition,
    Field(discriminator="kind"),
]


# --- Files on disk ---------------------------------------------------------------------------


class DatasetStamp(Model):
    version: str
    built_on: date


class DatasetIndex(Model):
    stamp: DatasetStamp
    games: list[str]


class GameData(Model):
    """One game file: the game, its dex, and every way to obtain each entry."""

    game: Game
    dex_entries: list[DexEntry] = Field(default_factory=list)
    acquisition_methods: list[AcquisitionMethod] = Field(default_factory=list)
