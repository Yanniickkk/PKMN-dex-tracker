using LivingDex.Core.Reference;

namespace LivingDex.Core.Transfers;

/// <summary>One leg of a route: a single move from one game into another.</summary>
/// <param name="From">The game left behind.</param>
/// <param name="To">The game arrived in.</param>
/// <param name="Mechanism">How that leg is made, so the UI can name it.</param>
public sealed record TransferHop(GameId From, GameId To, TransferMechanism Mechanism)
{
    public override string ToString() => $"{From} -> {To} ({Mechanism})";
}

/// <summary>An ordered chain of hops that gets one species from one game to another.</summary>
/// <param name="Hops">At least one hop, each starting where the previous one ended.</param>
public sealed record TransferRoute(IReadOnlyList<TransferHop> Hops)
{
    /// <summary>Where the chain starts.</summary>
    public GameId From => Hops[0].From;

    /// <summary>Where the chain ends.</summary>
    public GameId To => Hops[^1].To;

    /// <summary>How many moves the player has to make.</summary>
    public int Length => Hops.Count;

    /// <summary>
    /// What the route asks the player to actually do, with runs of the same mechanism collapsed.
    /// </summary>
    /// <remarks>
    /// Three trades in a row is one kind of work, not three: the cartridge you pass through on
    /// the way does not change what you are doing. This is what makes two routes the same
    /// answer, so it decides both what the popup prints and which routes it bothers offering.
    /// </remarks>
    public IReadOnlyList<TransferMechanism> Shape
    {
        get
        {
            var steps = new List<TransferMechanism>();

            foreach (var mechanism in Hops.Select(hop => hop.Mechanism))
            {
                if (steps.Count == 0 || steps[^1] != mechanism)
                {
                    steps.Add(mechanism);
                }
            }

            return steps;
        }
    }

    public override string ToString() =>
        string.Join(" -> ", Hops.Select(hop => hop.From.Value).Append(To.Value));
}

/// <summary>Why there is no route, in a form the UI can branch on.</summary>
public enum NoRouteReason
{
    /// <summary>A route was found.</summary>
    None,

    /// <summary>Source and destination are the same game; nothing to transfer.</summary>
    SameGame,

    /// <summary>One of the two games is not in the graph.</summary>
    UnknownGame,

    /// <summary>The games are not connected at all, for any species.</summary>
    NotConnected,

    /// <summary>
    /// The games are connected, but every route refuses this particular species somewhere along
    /// the way.
    /// </summary>
    SpeciesNotCarried,

    /// <summary>A route exists but is longer than the search was willing to look.</summary>
    TooManyHops,
}

/// <summary>
/// The answer to a route question: the routes that work, or why none do.
/// </summary>
/// <param name="Routes">Shortest first. Empty when there is no route.</param>
/// <param name="Reason">Why the list is empty, or <see cref="NoRouteReason.None"/>.</param>
/// <param name="Explanation">
/// One sentence for the UI to show where a route would have gone. Empty when there are routes.
/// </param>
public sealed record TransferRouteResult(
    IReadOnlyList<TransferRoute> Routes,
    NoRouteReason Reason,
    string Explanation)
{
    /// <summary>True when at least one route works.</summary>
    public bool Any => Routes.Count > 0;

    /// <summary>The fewest-hops route, or null when there is none.</summary>
    public TransferRoute? Shortest => Routes.Count > 0 ? Routes[0] : null;

    /// <summary>
    /// One route per genuinely different way of making the move, shortest of each, excluding
    /// <see cref="Shortest"/>. What a collapsible "other ways" list should hold.
    /// </summary>
    /// <remarks>
    /// Not every route: routes that read the same are the same advice. Five Generation 3
    /// cartridges all trade with each other, which makes sixteen routes from LeafGreen into
    /// FireRed - one link cable, and fifteen detours through Ruby, Sapphire and Emerald that
    /// ask for exactly the same thing. Offering those as "fifteen other ways" is noise, and it
    /// grows with every game added.
    ///
    /// What makes a route different is its <see cref="TransferRoute.Shape"/>. Pal Park straight
    /// into Platinum and trading first are two ways; trading three times and trading once are
    /// one. <see cref="Routes"/> still holds all of them, for anything that wants the graph
    /// rather than the advice.
    /// </remarks>
    public IEnumerable<TransferRoute> Alternatives =>
        Routes
            .GroupBy(route => string.Join(">", route.Shape))
            // Routes come shortest first and grouping keeps first-seen order, so each group
            // opens with the shortest of its kind and the first group is the shortest overall's.
            .Select(group => group.First())
            .Skip(1);

    internal static TransferRouteResult Found(IReadOnlyList<TransferRoute> routes) =>
        new(routes, NoRouteReason.None, string.Empty);

    internal static TransferRouteResult NotFound(NoRouteReason reason, string explanation) =>
        new([], reason, explanation);
}
