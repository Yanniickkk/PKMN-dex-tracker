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
/// Which generations a Pokemon may have passed through for an edge to take it.
/// </summary>
/// <remarks>
/// Not a <see cref="SpeciesFilter"/>, and the difference is the point. A filter is asked about
/// the Pokemon making the trip; this is asked about the trip. The same Charizard is taken or
/// refused depending on which cartridge it was caught on three transfers ago, so no record
/// about a species can answer it and the route has to be read instead.
///
/// Pokémon Bank is why it exists: it hands a Pokemon back to X or Omega Ruby only if everything
/// behind it is Generations 3 through 6. One that came out of a Virtual Console Red is refused,
/// and so is one that has ever been in Sun — those games cannot read what either end writes.
///
/// Inclusive at both ends, like <see cref="NationalDexRangeFilter"/>.
/// </remarks>
/// <param name="From">The earliest generation anything on the route may come from.</param>
/// <param name="To">The latest.</param>
public sealed record HistoryWindow(int From, int To);

/// <summary>
/// Where a Pokemon has to have started out for an edge to take it.
/// </summary>
/// <remarks>
/// The third question an edge can ask, after "what is it" and "where has it been", and the only
/// games that ask it are Let's Go, Pikachu! and Let's Go, Eevee!: only a Pokemon originally from
/// one of those two may be moved into them. A Charmander caught in Let's Go may leave for HOME
/// and come home again; one caught in Red and carried to the same HOME box may not.
///
/// Neither a <see cref="SpeciesFilter"/> nor a <see cref="HistoryWindow"/>. Every species it
/// refuses is in the game's own dex already, so it is not about the species; and a window is a
/// stretch of generations, which would have to admit a Pokemon from Sun.
///
/// The pair counts as one origin, which is why this is a list: a Pokemon caught in Let's Go,
/// Eevee! may be withdrawn into Let's Go, Pikachu!.
/// </remarks>
/// <param name="Games">The games a Pokemon may have started in for this edge to take it.</param>
public sealed record OriginRequirement(IReadOnlyList<GameId> Games);

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
    SpeciesFilter Filter)
{
    /// <summary>
    /// Where this edge refuses to take something that has been, or null when it takes anything
    /// whatever its history.
    /// </summary>
    /// <remarks>
    /// Null on every edge but Bank's withdrawals, which is every edge in the dataset written
    /// before Bank was. Not a constructor parameter for that reason: an edge without one is
    /// still a perfectly good edge.
    /// </remarks>
    public HistoryWindow? History { get; init; }

    /// <summary>
    /// Where a Pokemon has to have come from for this edge to take it, or null when it takes
    /// anything whatever its origin.
    /// </summary>
    /// <remarks>
    /// Null on every edge but HOME's two withdrawals into the Let's Go pair, and an init
    /// property for the same reason <see cref="History"/> is.
    /// </remarks>
    public OriginRequirement? Origin { get; init; }
}
