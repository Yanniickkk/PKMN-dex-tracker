using System.Text.Json.Serialization;

namespace LivingDex.Core.Reference;

/// <summary>The mechanism a transfer uses. Named so a route can be explained to the player.</summary>
public enum TransferMechanism
{
    /// <summary>Link trade between two games of the same generation.</summary>
    Trade,

    /// <summary>Generation 1 to 2, subject to the move restriction.</summary>
    TimeCapsule,

    /// <summary>Generation 3 to 4.</summary>
    PalPark,

    /// <summary>Generation 4 to 5.</summary>
    PokeTransfer,

    /// <summary>Virtual Console and Generation 5 into Bank.</summary>
    PokeTransporter,

    /// <summary>Into or out of Bank.</summary>
    Bank,

    /// <summary>Into or out of HOME.</summary>
    Home,
}

/// <summary>Whether an edge works one way or both.</summary>
public enum TransferDirection
{
    /// <summary>Source to target only. Most generation jumps are one way.</summary>
    OneWay,

    /// <summary>Usable in both directions.</summary>
    BothWays,
}

/// <summary>
/// Which species an edge will carry. Separate types rather than flags, because the rules have
/// nothing in common beyond being a filter.
/// </summary>
[JsonPolymorphic(TypeDiscriminatorPropertyName = "filter")]
[JsonDerivedType(typeof(AllSpeciesFilter), "all")]
[JsonDerivedType(typeof(NationalDexRangeFilter), "nationalDexRange")]
[JsonDerivedType(typeof(PresentInTargetDexFilter), "presentInTargetDex")]
public abstract record SpeciesFilter;

/// <summary>Everything the source game can hold.</summary>
public sealed record AllSpeciesFilter : SpeciesFilter;

/// <summary>
/// Only National Dex numbers in this inclusive range. The Time Capsule is 1 to 251, Pal Park is
/// 1 to 386.
/// </summary>
public sealed record NationalDexRangeFilter(int From, int To) : SpeciesFilter;

/// <summary>
/// Only species that appear in the dex of the game being transferred into. This is what makes
/// HOME refuse a deposit into a Generation 8 or 9 game with no entry for that species.
/// </summary>
public sealed record PresentInTargetDexFilter : SpeciesFilter;

/// <summary>
/// One link in the transfer graph. Edges are data, never hardcoded, so adding a game does not
/// mean changing the engine.
/// </summary>
/// <param name="From">The game a Pokemon leaves.</param>
/// <param name="To">The game it arrives in.</param>
/// <param name="Mechanism">How the move is made.</param>
/// <param name="Direction">Whether the same mechanism also works in reverse.</param>
/// <param name="Filter">Which species this edge will carry.</param>
public sealed record TransferEdge(
    GameId From,
    GameId To,
    TransferMechanism Mechanism,
    TransferDirection Direction,
    SpeciesFilter Filter);
