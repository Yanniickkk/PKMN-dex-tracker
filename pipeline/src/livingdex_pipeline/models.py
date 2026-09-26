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
    #: An older game sold again on the Nintendo Switch, under the name Nintendo gives that
    #: shelf. Not the same thing as a Virtual Console release and kept apart from it on
    #: purpose: those reach Pokemon Bank and these reach Pokemon HOME, which is the only
    #: reason either is an entity of its own.
    NINTENDO_CLASSICS = "nintendoClassics"
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
    # Generation 5's own. Unova hides a second table inside the first almost everywhere: a
    # darker patch of the same grass with its own species in it, and four kinds of moving spot
    # - grass that rustles, a cloud of dust in a cave, a ripple on the water, a shadow crossing
    # a bridge - that hold what is otherwise nowhere. Sixty-two of the two hundred and fourteen
    # species a player of Black can catch are only in one of those, so calling them "other"
    # would leave a third of the game with no answer to "where do I find it".
    #
    # Named the way `honeyTree` is, for the same reason: a generation's own way of starting an
    # encounter is a method rather than a note on one.
    DARK_GRASS = "darkGrass"
    RUSTLING_GRASS = "rustlingGrass"
    DUST_CLOUD = "dustCloud"
    RIPPLING_WATER = "ripplingWater"
    BRIDGE_SHADOW = "bridgeShadow"
    # And the sequels' own, which is the first method in this dataset that no encounter table
    # anywhere mentions: twenty hidden patches of grass, read off a wiki page rather than out
    # of an API. A grotto is not a rarer slot in an ordinary place - it is its own place, with
    # its own table, holding species that are nowhere else in the game.
    HIDDEN_GROTTO = "hiddenGrotto"
    # Generation 6's four. Kalos stops hiding its second tables and puts them in plain sight: a
    # horde of five walks up at once, a patch of coloured flowers holds what the grass around it
    # does not, the berry trees at the Berry Fields each have a resident, and five different
    # things jump a player who is minding their own business - out of the cave ceiling, out of
    # the ground, out of the sky, out of a bush and out of a bin.
    #
    # The ambushes are one method with the place it comes from said beside it, unlike Unova's
    # four spots, which are four. A spot is somewhere a player chooses to walk into; an ambush
    # is the same event with different scenery, and five enum values would be five names for
    # "something jumped out".
    HORDE = "horde"
    FLOWER_PATCH = "flowerPatch"
    BERRY_TREE = "berryTree"
    AMBUSH = "ambush"
    # Alola's own two, and the first is the generation's signature: a wild Pokemon at low
    # health calls for help and another comes. Whole species are in these games only as the ally
    # somebody else calls - a hundred and forty-six slots in Sun alone - so "you cannot meet this
    # one, only be introduced to it" is a way of starting an encounter rather than a note on one.
    #
    # The other is Unova's four moving spots come back as one. Something stirs and a table of
    # its own is under it: grass that rustles on a route, a cloud of sand in Haina Desert, a
    # patch of bubbles on the sea. The source gives all three as one method whose English names
    # only the water - "fishing at bubbling spots" - which is why this is named for what the
    # three have in common instead. What a player is actually looking at is the ground they are
    # standing on, and a record says where it is.
    SOS = "sos"
    MOVING_SPOT = "movingSpot"
    # And the two the Hoenn remakes brought, which are the two halves of Hoenn nobody could
    # reach before: under the sea and over it. Diving is an HM taught in Mossdeep and a table of
    # its own beneath the water a player is surfing on; Soaring is the Eon Flute, a Latias or
    # Latios underfoot, and flocks met in mid-air. Neither is a rarer kind of surfing or walking.
    DIVE = "dive"
    SOARING = "soaring"
    # And Let's Go's three, which are one idea: **there is no encounter table to walk into.**
    # Every wild Pokemon in those two games is standing, swimming or flying where the player
    # can see it, and an encounter starts by touching that one. No tall grass, no random
    # battle, no rod, no Repel - the whole vocabulary the twenty-eight games before them share
    # is gone, so mapping this onto `walk` and `surf` would say a player pushes into grass and
    # hopes, which is the one thing these games never ask.
    #
    # Three and not one, because they are three places to look rather than three names for
    # looking: on the ground, on the water a Lapras is carrying you over, and in the sky. The
    # sky is not a rarer kind of ground - a Charizard passes overhead and is gone, and it is
    # the only place a wild Charizard or Dragonite exists at all.
    #
    # What is *not* a method here is rarity. The source keeps a second table beside each of
    # these for the ones that turn up far less often - Chansey on every route, Lapras on two
    # sea routes - and that is the same slot in the same place met less often, so it is a
    # sentence on the record rather than a fourth, fifth and sixth name. The same call Kalos's
    # flower patches got.
    OVERWORLD = "overworld"
    OVERWORLD_WATER = "overworldWater"
    OVERWORLD_FLYING = "overworldFlying"
    # And Paldea's one, which is the fourth place Scarlet and Violet put something and the only
    # one of the five their pages tick that the three above cannot say.
    #
    # **Measured before it was named, which is the rule this enum has kept since Hisui.** Of
    # the 3,409 rows in those games' tables, 393 are ticked underwater and **197 of those are
    # ticked underwater and nothing else** - an Arrokuda is never on the surface, and a player
    # who surfs past one will not find it. That is a different place to look rather than a
    # rarer kind of swimming.
    #
    # The same measurement refused a fifth. The terrain block has a Sky column beside its
    # Overland one - a Pikipek circling high against a Gastly hovering at head height - and of
    # its 246 ticks exactly **four** are the only tick on their row, all four a Braviary in
    # Area Zero, which is on the ground elsewhere in the same game. Two names for one event
    # with different scenery, which is the call Kalos's five ambushes got, so both are
    # :attr:`OVERWORLD_FLYING`.
    #
    # Not :attr:`DIVE`, which is Mossdeep's HM and a table of its own beneath the water a
    # player is surfing on. There is no move here: a player swims and presses a button.
    OVERWORLD_UNDERWATER = "overworldUnderwater"
    # And Galar's two, which are the first ways of getting a Pokemon in this dataset that are
    # not a place at all. A Max Raid is a beam of light over a den, four trainers against one
    # Dynamax Pokemon and a single throw at the end of it; a Dynamax Adventure is the Crown
    # Tundra's run through a cave with three strangers, ending at a legendary that one of the
    # four gets to keep. Both are the only way to get some species in these games - most of the
    # legendaries of the six generations before this one come out of the Max Lair and nowhere
    # else - so neither can be `other`, which is where a method goes to stop being an answer.
    #
    # Wild all the same: what is caught was not handed over, hatched, traded or evolved, and it
    # is standing in a place a player can walk to.
    MAX_RAID = "maxRaid"
    DYNAMAX_ADVENTURE = "dynamaxAdventure"
    # And Hisui's two, in a game where the whole vocabulary above is gone: no grass, no rod, no
    # random battle, and nothing rolled when a player walks. What is standing in the world is
    # what is there, which is Let's Go's answer - so `overworld`, `overworldWater` and
    # `overworldFlying` do most of the work here, and these two are what those three cannot say.
    #
    # A space-time distortion is a patch of the map that goes purple for a few minutes and fills
    # with Pokemon that are not in Hisui at all. Measured before it was named: **of the 69
    # species that appear in one, 30 appear in nothing else in the game** - every Johto and
    # Unova starter, the whole Eevee family, Porygon's line, Gengar, Scizor, Magmortar. Calling
    # that `other` would tell a player that a third of what the game holds has no answer.
    #
    # The other is three pieces of scenery with something inside: a tree that shakes, an ore
    # deposit that shakes, and the wooden boxes in the Celestica ruins. A ball is thrown at it
    # and what falls out can be caught. One method with the scenery said beside it rather than
    # three, which is the call Kalos's five ambushes got - a tree and a crate are the same event
    # with different furniture. It is Johto's headbutt trees three hundred years earlier, and it
    # is not `headbutt`, because there is no move and two of the three are not trees.
    SPACE_TIME_DISTORTION = "spaceTimeDistortion"
    SHAKEN_LOOSE = "shakenLoose"
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
    #: Which of the game's own Pokedexes this entry is numbered in, when the game shows more
    #: than one. None for every game that shows a single list, which is all twenty written
    #: before X and Y: a number that can only belong to one list does not need to name it.
    #:
    #: X and Y hand a player three - Central, Coastal and Mountain Kalos - and the three share
    #: nothing. Each starts at #001, each holds species the others do not, and no game ever
    #: shows a number that spans them. Without a name on each entry the three would arrive as
    #: one list with three species numbered #001, and the only way out would be to renumber
    #: them 1 to 457 - which would be a dex no player has ever seen.
    dex: str | None = None
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


class HistoryWindow(Model):
    """Which generations a Pokemon may have passed through for an edge to take it.

    Every other thing an edge can refuse is a fact about the Pokemon: its National Dex number,
    whether the game on the far side lists it. This one is about where it has been, and it is
    the first question here that no single record can answer - the same Charizard is taken or
    refused depending on which cartridge it was caught on three transfers ago.

    Pokemon Bank is why it exists. Bank will hand a Pokemon to X or to Omega Ruby only if
    everything behind it is Generation 3 through 6: one that came out of a Virtual Console Red
    is refused, and so is one that has ever been in Sun. Bulbapedia writes those as two
    sentences and they are one fact - the Generation 6 games cannot read what either end
    writes - and both halves are a window on a route rather than anything about a species.

    Inclusive at both ends, like :class:`NationalDexRangeFilter`. Read against every game on the
    route so far, which is what makes it different from a filter: a filter is asked about the
    Pokemon making the trip, this is asked about the trip.
    """

    from_: int = Field(alias="from")
    to: int


class OriginRequirement(Model):
    """Where a Pokemon has to have started out for an edge to take it.

    The third question an edge can ask and the last one left, after "what is it" and "where has
    it been". Let's Go, Pikachu! and Let's Go, Eevee! are the only games that ask it, and
    Bulbapedia puts it in one sentence: only a Pokemon originally from one of those two may be
    moved into them. A Charmander caught in Let's Go may leave for HOME and come home again; a
    Charmander caught in Red, carried through four services and thirty years to the same HOME
    box, may not.

    Not a :class:`SpeciesFilter`, because it is not about the species - every species this asks
    about is in the game's own dex already. Not a :class:`HistoryWindow` either, though it is
    the same kind of fact: a window is a stretch of generations and this is a set of games, and
    a Pokemon from Sun is refused by a window that would have to admit it.

    ``games`` is a list because the pair counts as one origin: a Pokemon caught in Let's Go,
    Eevee! may be withdrawn into Let's Go, Pikachu!, which is the same thing a link cable
    between the two does.

    **What this does not say**, because nothing in the schema can: Bulbapedia's sentence has a
    second half - once such a Pokemon has been moved on into a newer game, or has visited
    Pokemon Champions, it may never go back. That is a fact about a journey this dataset does
    not record, and a tracker that shows where a Pokemon can be obtained does not need it: the
    only thing this edge can hand back is something that was caught there to begin with, and
    that entry is filled either way.
    """

    games: list[str]


class TransferEdge(Model):
    from_: str = Field(alias="from")
    to: str
    mechanism: TransferMechanism
    direction: TransferDirection
    filter: SpeciesFilter
    #: Where this edge refuses to take something that has been, when it refuses at all. Absent
    #: on every edge but Bank's withdrawals, which is every edge written before Phase 3.
    history: HistoryWindow | None = None
    #: Where a Pokemon has to have come from, when the edge asks at all. Absent on every edge
    #: but HOME's two withdrawals into the Let's Go pair.
    origin: OriginRequirement | None = None


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
    #: How likely this slot is, when the game counts in weights instead of percentages.
    #:
    #: **Scarlet and Violet are the first, and they are the reason this field exists.** Every
    #: game before them either rolls a slot out of a hundred - which is what ``rate_percent``
    #: is - or stands a Pokemon in the world and rolls nothing, which is Let's Go, Hisui and
    #: Lumiose, and leaves both fields empty. These do a third thing: a spawn point picks from
    #: the species that can be there, each with a weight of 1 or 5 or 60 or 400, and the page
    #: says only that a higher weight generally means more likely.
    #:
    #: It is not a percentage and must not be recorded as one. The denominator depends on the
    #: biome, the terrain and the hour all at once, and two weights are only comparable to each
    #: other when all three match - so 60 against 1 in the same Prairie says a great deal, and
    #: 60 in a lake against 60 in a cave says nothing. Dividing would hand a player a number no
    #: game ever showed them, which is the objection every invented figure in this dataset has
    #: been refused for.
    probability_weight: int | None = None
    time_of_day: str | None = None
    season: str | None = None
    weather: str | None = None
    #: What else has to be true for this slot to hold this species: a Game Boy Advance cartridge
    #: in the slot underneath, the day the Great Marsh rotates it in, a honey tree of the right
    #: group. Time of day, season and weather have fields of their own; this is everything else,
    #: and a slot without it is one a player meets by playing.
    requirement: str | None = None
    #: Why this slot does not count towards being able to get one here, when it does not.
    #:
    #: A real way that a player cannot be told to go and use. The Friend Safari is the first:
    #: it is in the game, the tables are real, and reaching it wants somebody else's 3DS friend
    #: code and - for a third of it - the network that closed in April 2024. Counting it would
    #: tell a player of X that they can have a Spritzee, which is true of nobody without a
    #: friend who happens to have the right code.
    #:
    #: A reason rather than a flag, like a dex entry's, so the app can say why rather than
    #: quietly leaving the row out of an answer. The row is still shown: the question it is kept
    #: out of is "can I get this here", not "what does this game have".
    #:
    #: Only wild slots so far. It belongs on the others the day one of them needs it.
    does_not_count: str | None = None
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
    # Left out by the traders who will take anything. Jasmine hands over a Steelix for whatever
    # is in the party, and naming a species there would have invented a price she never asked.
    wants: DexTarget | None = None
    requirement: str | None = None
    source: SourceCitation


class FormChangeAcquisition(Model):
    """A form of something already caught, and what turns it into this one.

    The sixth kind, and the one the other five could not be bent into. A form is not caught,
    handed over, hatched, traded or evolved: the Pokemon is already yours and something changes
    it. Filing that under any of the others would have said the wrong thing twice - "gift" puts
    an NPC where there is none, and "evolution" says a rule made it that nothing can undo.
    """

    kind: Literal["formChange"] = "formChange"
    game: str
    #: The form. Its species is what has to be caught first.
    target: DexTarget
    #: What makes the change, in words a player can act on.
    requirement: str
    #: Where it happens, when it is somewhere rather than something.
    location: str | None = None
    source: SourceCitation


class OutsideAcquisition(Model):
    """Caught somewhere this dataset does not hold, and sent in.

    The seventh kind, and the first that is not about the game at all. Two things in the series
    put Pokemon into a cartridge without being cartridges themselves: the Pokemon Dream Radar,
    a Nintendo 3DS download that sends what it catches down into Black 2 and White 2, and
    Pokemon GO, which reaches Let's Go through the GO Park. Neither has a Pokedex to fill and
    nothing is caught in either in the sense this tracker means, so neither is a game here -
    and a transfer edge would have had to point at one.

    What is left is this: a row on the entry saying where it really comes from and what the
    player has to do there. It is shown and it never counts - :attr:`does_not_count` is
    required rather than optional, because a way that leaves this dataset is by definition a
    way this dataset cannot promise.

    Scope, decided by Yannick on 26 September 2026: only where nothing in the game produces one
    anyway. The Radar also hands out fifteen Dream World Pokemon with Hidden Abilities and
    Black 2 can catch every one of them, so those are not written down here.
    """

    kind: Literal["outside"] = "outside"
    game: str
    target: DexTarget
    #: Where it is really caught, named as a player would name it: "the Pokemon Dream Radar".
    sent_from: str
    #: What the player does there, in words they can act on.
    how: str
    #: What else has to be true. The Radar's Dialga wants a Pokemon Diamond card in the same
    #: Nintendo 3DS, and its Thundurus wants its Tornadus caught first.
    requirement: str | None = None
    #: Why this never counts towards being able to get one here. Required, not optional.
    does_not_count: str
    source: SourceCitation


AcquisitionMethod = Annotated[
    GiftAcquisition
    | WildAcquisition
    | EvolutionAcquisition
    | BreedingAcquisition
    | TradeAcquisition
    | FormChangeAcquisition
    | OutsideAcquisition,
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
