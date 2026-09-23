using System.Text.Json.Serialization;

namespace LivingDex.Core.Reference;

/// <summary>
/// The sections of the detail popup, in the order they are shown.
/// </summary>
/// <remarks>
/// The numbers are display order and nothing else: they are never serialised, because the JSON
/// discriminator already carries the kind. Inserting one in the middle is therefore free.
/// </remarks>
public enum AcquisitionKind
{
    Gift = 0,
    Wild = 1,
    Evolution = 2,
    Breeding = 3,
    Trade = 4,
    FormChange = 5,
}

/// <summary>
/// One way to get one target in one game. The kinds carry different fields, so they are
/// separate types rather than one record with mostly-null columns.
/// </summary>
[JsonPolymorphic(TypeDiscriminatorPropertyName = "kind")]
[JsonDerivedType(typeof(GiftAcquisition), "gift")]
[JsonDerivedType(typeof(WildAcquisition), "wild")]
[JsonDerivedType(typeof(EvolutionAcquisition), "evolution")]
[JsonDerivedType(typeof(BreedingAcquisition), "breeding")]
[JsonDerivedType(typeof(TradeAcquisition), "trade")]
[JsonDerivedType(typeof(FormChangeAcquisition), "formChange")]
public abstract record AcquisitionMethod
{
    /// <summary>The game this method applies to.</summary>
    [JsonPropertyOrder(-3)]
    public required GameId Game { get; init; }

    /// <summary>The species or form obtained.</summary>
    [JsonPropertyOrder(-2)]
    public required DexTarget Target { get; init; }

    /// <summary>
    /// Why this way does not count towards being able to get one here, when it does not.
    /// </summary>
    /// <remarks>
    /// A real way that a player cannot be told to go and use. Kalos's Friend Safari is the
    /// first: the tables are true, and which of them a player can reach was decided by somebody
    /// else's friend code, with a third of every Safari shut since the 3DS network closed in
    /// April 2024. The row is kept and shown — it is part of what the game has — and it is left
    /// out of "can I get this here", which is what the availability check and the filter
    /// beside the grid answer.
    ///
    /// A reason rather than a flag, so the popup can say why instead of quietly showing a row
    /// that the filter disagrees with.
    /// </remarks>
    [JsonPropertyOrder(99)]
    public string? DoesNotCount { get; init; }

    /// <summary>Whether this way counts towards being able to get one here.</summary>
    [JsonIgnore]
    public bool Counts => DoesNotCount is null;

    /// <summary>Where this record came from.</summary>
    [JsonPropertyOrder(100)]
    public required SourceCitation Source { get; init; }

    /// <summary>
    /// Which section of the detail popup this belongs under. Not serialised: it would collide
    /// with the JSON discriminator, which already carries the same information.
    /// </summary>
    [JsonIgnore]
    public abstract AcquisitionKind Kind { get; }
}

/// <summary>What sort of one-off a gift is.</summary>
public enum GiftKind
{
    Starter,
    Fossil,
    NpcGift,
    Egg,
    StaticEncounter,
}

/// <summary>Handed over or placed in the world: starters, fossils, eggs, legendary statics.</summary>
public sealed record GiftAcquisition : AcquisitionMethod
{
    [JsonIgnore]
    public override AcquisitionKind Kind => AcquisitionKind.Gift;

    /// <summary>Which sort of one-off this is.</summary>
    public required GiftKind GiftKind { get; init; }

    /// <summary>Where it happens, for example Route 201 or Oreburgh Mine.</summary>
    public required string Location { get; init; }

    /// <summary>The character who hands it over, when there is one.</summary>
    public string? Npc { get; init; }

    /// <summary>The level it is received at, when that is fixed.</summary>
    public int? Level { get; init; }

    /// <summary>What has to be true first, for example: after the first gym badge.</summary>
    public string? Requirement { get; init; }
}

/// <summary>How a wild encounter is started.</summary>
public enum EncounterMethod
{
    Walk,
    Surf,
    OldRod,
    GoodRod,
    SuperRod,
    RockSmash,
    Headbutt,
    HoneyTree,
    Swarm,

    /// <summary>The darker patch of grass beside the ordinary kind, with its own table.</summary>
    DarkGrass,

    /// <summary>Grass that shakes: Generation 5's rarest walk-up encounters.</summary>
    RustlingGrass,

    /// <summary>A cloud of dust in a cave, which is sometimes a Pokemon and sometimes a gem.</summary>
    DustCloud,

    /// <summary>A ripple on the water, surfed into.</summary>
    RipplingWater,

    /// <summary>A shadow crossing a bridge, walked under.</summary>
    BridgeShadow,

    /// <summary>One of the twenty hidden patches of grass in the Unova sequels.</summary>
    HiddenGrotto,

    /// <summary>Five at once, which is Kalos's own way of filling a patch of grass.</summary>
    Horde,

    /// <summary>A patch of coloured flowers, with a table the grass around it does not have.</summary>
    FlowerPatch,

    /// <summary>A tree at the Kalos Berry Fields, each colour of which keeps its own resident.</summary>
    BerryTree,

    /// <summary>
    /// Something that jumps out: off a cave ceiling, out of the ground, out of the sky, out of a
    /// bush or out of a bin. One method with the scenery said beside it rather than five.
    /// </summary>
    Ambush,

    Other,
}

/// <summary>An inclusive level range, for example 3 to 5.</summary>
public readonly record struct LevelRange(int Minimum, int Maximum)
{
    public override string ToString() => Minimum == Maximum ? $"{Minimum}" : $"{Minimum}-{Maximum}";
}

/// <summary>A wild encounter slot.</summary>
public sealed record WildAcquisition : AcquisitionMethod
{
    [JsonIgnore]
    public override AcquisitionKind Kind => AcquisitionKind.Wild;

    /// <summary>The route, cave or town.</summary>
    public required string Location { get; init; }

    /// <summary>A named part of the location, for example a specific floor or patch.</summary>
    public string? SubArea { get; init; }

    /// <summary>How the encounter is started.</summary>
    public required EncounterMethod Method { get; init; }

    /// <summary>The levels it appears at.</summary>
    public required LevelRange Levels { get; init; }

    /// <summary>Slot chance as a percentage, when the source gives one.</summary>
    public double? RatePercent { get; init; }

    /// <summary>Restricted to this part of the day, for example: morning.</summary>
    public string? TimeOfDay { get; init; }

    /// <summary>Restricted to this season. Generation 5 only.</summary>
    public string? Season { get; init; }

    /// <summary>Restricted to this weather.</summary>
    public string? Weather { get; init; }

    /// <summary>
    /// What else has to be true for this slot to hold this species: a Game Boy Advance cartridge
    /// in the slot underneath, the day the Great Marsh rotates it in, a honey tree of the right
    /// group. Time of day, season and weather have fields of their own; this is everything else,
    /// and a slot without it is one a player meets by playing.
    /// </summary>
    public string? Requirement { get; init; }
}

/// <summary>Obtained by evolving something else, which must itself be obtainable.</summary>
public sealed record EvolutionAcquisition : AcquisitionMethod
{
    [JsonIgnore]
    public override AcquisitionKind Kind => AcquisitionKind.Evolution;

    /// <summary>The rule that applies. Its To side is this method target.</summary>
    public required EvolutionRuleId Rule { get; init; }
}

/// <summary>
/// Hatched from an egg the day care produces. The baby Pokemon of a generation have no other
/// source: nothing meets a Pichu in the grass, and nothing evolves into one.
/// </summary>
public sealed record BreedingAcquisition : AcquisitionMethod
{
    [JsonIgnore]
    public override AcquisitionKind Kind => AcquisitionKind.Breeding;

    /// <summary>
    /// Any one of these, left at the day care, produces the target. A Pichu hatches from a
    /// Pikachu or from a Raichu, and naming only the first would hide a way that works.
    /// </summary>
    public required IReadOnlyList<DexTarget> Parents { get; init; }

    /// <summary>Where the day care is, for example Route 117.</summary>
    public required string Location { get; init; }

    /// <summary>What else has to be true, for example an incense a parent has to hold.</summary>
    public string? Requirement { get; init; }
}

/// <summary>An in-game trade with an NPC. Player-to-player trading is a transfer, not this.</summary>
public sealed record TradeAcquisition : AcquisitionMethod
{
    [JsonIgnore]
    public override AcquisitionKind Kind => AcquisitionKind.Trade;

    /// <summary>Where the trade happens.</summary>
    public required string Location { get; init; }

    /// <summary>The character who trades.</summary>
    public string? Npc { get; init; }

    /// <summary>
    /// What the player has to hand over, or nothing when the trader will take anything. Jasmine
    /// gives away a Steelix for whatever is in the party.
    /// </summary>
    public DexTarget? Wants { get; init; }

    /// <summary>What has to be true first.</summary>
    public string? Requirement { get; init; }
}

/// <summary>
/// A form of something already caught, and what turns it into this one.
/// </summary>
/// <remarks>
/// The sixth kind, and the one the other five could not be bent into. A form is not caught,
/// handed over, hatched, traded or evolved: the Pokemon is already yours and something changes
/// it. Filing it under any of the others would have said the wrong thing twice — a gift puts an
/// NPC where there is none, and an evolution says a rule made it that nothing can undo.
/// </remarks>
public sealed record FormChangeAcquisition : AcquisitionMethod
{
    [JsonIgnore]
    public override AcquisitionKind Kind => AcquisitionKind.FormChange;

    /// <summary>What makes the change, in words a player can act on.</summary>
    public required string Requirement { get; init; }

    /// <summary>Where it happens, when it is somewhere rather than something.</summary>
    public string? Location { get; init; }
}
