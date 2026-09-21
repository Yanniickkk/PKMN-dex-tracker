using System.Text.Json.Serialization;

namespace LivingDex.Core.Reference;

/// <summary>
/// The four sections of the detail popup, in the order they are shown.
/// </summary>
public enum AcquisitionKind
{
    Gift = 0,
    Wild = 1,
    Evolution = 2,
    Trade = 3,
}

/// <summary>
/// One way to get one target in one game. The four kinds carry different fields, so they are
/// separate types rather than one record with mostly-null columns.
/// </summary>
[JsonPolymorphic(TypeDiscriminatorPropertyName = "kind")]
[JsonDerivedType(typeof(GiftAcquisition), "gift")]
[JsonDerivedType(typeof(WildAcquisition), "wild")]
[JsonDerivedType(typeof(EvolutionAcquisition), "evolution")]
[JsonDerivedType(typeof(TradeAcquisition), "trade")]
public abstract record AcquisitionMethod
{
    /// <summary>The game this method applies to.</summary>
    [JsonPropertyOrder(-3)]
    public required GameId Game { get; init; }

    /// <summary>The species or form obtained.</summary>
    [JsonPropertyOrder(-2)]
    public required DexTarget Target { get; init; }

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
}

/// <summary>Obtained by evolving something else, which must itself be obtainable.</summary>
public sealed record EvolutionAcquisition : AcquisitionMethod
{
    [JsonIgnore]
    public override AcquisitionKind Kind => AcquisitionKind.Evolution;

    /// <summary>The rule that applies. Its To side is this method target.</summary>
    public required EvolutionRuleId Rule { get; init; }
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

    /// <summary>What the player has to hand over.</summary>
    public required DexTarget Wants { get; init; }

    /// <summary>What has to be true first.</summary>
    public string? Requirement { get; init; }
}
