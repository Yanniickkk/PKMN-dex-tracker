using LivingDex.Core.Reference;
using LivingDex.Core.Transfers;

namespace LivingDex.Desktop.Components;

/// <summary>One game that can feed a main game, and how what it sends gets there.</summary>
public sealed record LinkedGameCandidate(Game Game, string Route);

/// <summary>
/// Which games may be linked to a main game, and in what order they are offered.
/// </summary>
/// <remarks>
/// Asked by the wizard when a collection is made and by the edit screen when one is changed, and
/// both have to get the same answer: a game that could not be linked on Monday must not appear
/// as one that can on Tuesday.
/// </remarks>
public static class LinkedGames
{
    /// <summary>
    /// Every game, in the order a player thinks of them: by generation, and inside a generation
    /// by the day it came out.
    /// </summary>
    /// <remarks>
    /// Release order, not alphabetical: Ruby and Sapphire came first, FireRed and LeafGreen a
    /// year later, Emerald after that, and a player who grew up with them expects to read them
    /// that way. Title breaks a tie, which is what keeps the two halves of a pair - released on
    /// the same day - next to each other and always in the same order.
    ///
    /// Games, so the transfer nodes are left out. Pokémon Bank is in the dataset because the
    /// routes through it have to point at something, and it is not a main game - there is
    /// nothing to fill in it - nor a linked one: a linked game is somewhere a player can get
    /// something, and nothing was ever caught in Bank. It still does its work in the routes the
    /// games below are offered by.
    /// </remarks>
    public static IReadOnlyList<Game> Playable(IEnumerable<Game> games)
    {
        ArgumentNullException.ThrowIfNull(games);

        return
        [
            .. games
                .Where(game => game.Release != GameRelease.Service)
                .OrderBy(game => game.Generation)
                .ThenBy(game => game.Released ?? DateOnly.MaxValue)
                .ThenBy(game => game.Title, StringComparer.Ordinal),
        ];
    }

    /// <summary>
    /// Every game the transfer graph can route into <paramref name="main"/>, main game excluded.
    /// </summary>
    /// <remarks>
    /// Only those: a game with no route is not a choice the player can make, and a picker full of
    /// covers that refuse to be ticked is a list of dead ends to read through.
    /// </remarks>
    public static IReadOnlyList<LinkedGameCandidate> For(
        GameId main,
        IEnumerable<Game> games,
        TransferGraph graph)
    {
        ArgumentNullException.ThrowIfNull(graph);

        return
        [
            .. Playable(games)
                .Where(game => game.Id != main)
                .Select(game => (Game: game, Route: RouteInto(game.Id, main, graph)))
                .Where(one => one.Route is not null)
                .Select(one => new LinkedGameCandidate(one.Game, one.Route!)),
        ];
    }

    /// <summary>How a game reaches the main game, or null when it cannot.</summary>
    private static string? RouteInto(GameId feeder, GameId main, TransferGraph graph)
    {
        var result = graph.RoutesBetween(feeder, main);
        return result.Shortest is { } route ? $"via {TransferNames.Of(route)}" : null;
    }
}
