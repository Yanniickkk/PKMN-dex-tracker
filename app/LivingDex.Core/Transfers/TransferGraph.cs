using System.Globalization;
using LivingDex.Core.Reference;

namespace LivingDex.Core.Transfers;

/// <summary>
/// Answers which games can feed which, and how to get one species from one game to another.
/// </summary>
/// <remarks>
/// Every edge comes from the dataset. Nothing about Pal Park, the Time Capsule or HOME is
/// written here, so adding a game is a data change rather than a code change.
/// </remarks>
public sealed class TransferGraph
{
    /// <summary>How many hops a route may have before the search gives up.</summary>
    public const int DefaultMaxHops = 8;

    /// <summary>How many routes to return before the search stops looking for more.</summary>
    public const int DefaultMaxRoutes = 25;

    private sealed record DirectedEdge(
        GameId From,
        GameId To,
        TransferMechanism Mechanism,
        SpeciesFilter Filter,
        HistoryWindow? History)
    {
        public TransferHop ToHop() => new(From, To, Mechanism);
    }

    /// <summary>
    /// The spread of generations a route has passed through so far, which is all a
    /// <see cref="HistoryWindow"/> needs to know about it.
    /// </summary>
    /// <remarks>
    /// Two numbers rather than the list of games, because a window only asks how far out the
    /// route reaches in either direction. It makes the search state small enough to walk
    /// exhaustively: the earliest only falls and the latest only rises, so a node is revisited
    /// at most once per pair.
    ///
    /// <paramref name="Complete"/> is false once a node of unknown generation has been passed.
    /// Such a route is refused by any window, the way a range filter refuses a species it cannot
    /// number.
    /// </remarks>
    private readonly record struct RouteHistory(int Earliest, int Latest, bool Complete)
    {
        /// <summary>A route that has been nowhere yet.</summary>
        public static RouteHistory Empty => new(int.MaxValue, int.MinValue, true);

        /// <summary>The same route with one more node behind it.</summary>
        public RouteHistory With(int? generation) => generation is { } one
            ? new RouteHistory(Math.Min(Earliest, one), Math.Max(Latest, one), Complete)
            : this with { Complete = false };

        /// <summary>Whether everything behind the route falls inside the window.</summary>
        public bool Inside(HistoryWindow window) =>
            Complete && Earliest >= window.From && Latest <= window.To;
    }

    private readonly Dictionary<GameId, List<DirectedEdge>> _outgoing = [];
    private readonly Dictionary<GameId, List<DirectedEdge>> _incoming = [];
    private readonly HashSet<GameId> _games = [];
    private readonly Dictionary<GameId, IReadOnlySet<GameId>> _reachable = [];
    private readonly ITransferFilterContext _context;
    private readonly int _maxHops;
    private readonly int _maxRoutes;

    /// <param name="edges">The graph, straight from the dataset.</param>
    /// <param name="context">Reference data the species filters need.</param>
    /// <param name="maxHops">Longest route to consider.</param>
    /// <param name="maxRoutes">Most routes to return.</param>
    public TransferGraph(
        IEnumerable<TransferEdge> edges,
        ITransferFilterContext context,
        int maxHops = DefaultMaxHops,
        int maxRoutes = DefaultMaxRoutes)
    {
        ArgumentNullException.ThrowIfNull(edges);
        ArgumentNullException.ThrowIfNull(context);
        ArgumentOutOfRangeException.ThrowIfLessThan(maxHops, 1);
        ArgumentOutOfRangeException.ThrowIfLessThan(maxRoutes, 1);

        _context = context;
        _maxHops = maxHops;
        _maxRoutes = maxRoutes;

        foreach (var edge in edges)
        {
            Add(new DirectedEdge(edge.From, edge.To, edge.Mechanism, edge.Filter, edge.History));

            if (edge.Direction == TransferDirection.BothWays)
            {
                Add(new DirectedEdge(edge.To, edge.From, edge.Mechanism, edge.Filter, edge.History));
            }
        }

        // Fixed ordering so routes come back in the same order on every run.
        foreach (var list in _outgoing.Values.Concat(_incoming.Values))
        {
            list.Sort(static (left, right) =>
            {
                var byGame = string.CompareOrdinal(left.To.Value + left.From.Value, right.To.Value + right.From.Value);
                return byGame != 0 ? byGame : left.Mechanism.CompareTo(right.Mechanism);
            });
        }
    }

    /// <summary>Every game mentioned by an edge.</summary>
    public IReadOnlyCollection<GameId> Games => _games;

    /// <summary>
    /// Which games can send into <paramref name="game"/>, directly or through other games.
    /// </summary>
    /// <remarks>
    /// Species filters are not applied: this answers "could this game ever feed that one", which
    /// is what the linked-game picker needs. Whether one particular species survives the trip is
    /// <see cref="RoutesBetween(GameId, GameId, DexTarget)"/>.
    ///
    /// History windows are applied, because they are not about a species at all. Nothing
    /// whatever can be moved from a Virtual Console Red into X, so Red is not a game that could
    /// ever feed X and saying otherwise would be a different kind of wrong from "not this
    /// Pokemon". That is why this is a forward search from each candidate rather than one walk
    /// backwards: where a route has been is only known going forwards.
    ///
    /// No hop limit, unlike the route search. Telling "too far to bother looking" apart from
    /// "there is no way at all" is the whole reason this is asked.
    /// </remarks>
    public IReadOnlySet<GameId> ReachableFrom(GameId game)
    {
        if (_reachable.TryGetValue(game, out var cached))
        {
            return cached;
        }

        var found = new HashSet<GameId>();
        if (_games.Contains(game))
        {
            foreach (var candidate in _games.Where(one => one != game && CanReach(one, game)))
            {
                found.Add(candidate);
            }
        }

        _reachable[game] = found;

        return found;
    }

    /// <summary>Whether anything at all could get from one node to another, however many hops.</summary>
    private bool CanReach(GameId from, GameId destination)
    {
        var start = RouteHistory.Empty.With(_context.GenerationOf(from));
        var seen = new HashSet<(GameId, RouteHistory)> { (from, start) };
        var queue = new Queue<(GameId Node, RouteHistory History)>();
        queue.Enqueue((from, start));

        while (queue.Count > 0)
        {
            var (node, history) = queue.Dequeue();
            if (!_outgoing.TryGetValue(node, out var edges))
            {
                continue;
            }

            foreach (var edge in edges.Where(edge => Takes(edge, history)))
            {
                if (edge.To == destination)
                {
                    return true;
                }

                var next = (edge.To, history.With(_context.GenerationOf(edge.To)));
                if (seen.Add(next))
                {
                    queue.Enqueue(next);
                }
            }
        }

        return false;
    }

    /// <summary>
    /// Every way anything could get from one game to another, shortest first, with no species
    /// in mind.
    /// </summary>
    /// <remarks>
    /// This is the question a linked-game picker asks: could this game ever feed that one?
    /// Whether one particular Pokémon survives the trip is
    /// <see cref="RoutesBetween(GameId, GameId, DexTarget)"/>, and a game can be a perfectly
    /// good feeder while refusing some of what lives in it.
    /// </remarks>
    public TransferRouteResult RoutesBetween(GameId from, GameId to)
    {
        if (Refuse(from, to) is { } refusal)
        {
            return refusal;
        }

        var routes = FindRoutes(from, to, DexTarget.ForSpecies(new SpeciesId(string.Empty)), applyFilters: false);

        return routes.Count > 0 ? TransferRouteResult.Found(routes) : NoPath(from, to);
    }

    /// <inheritdoc cref="RoutesBetween(GameId, GameId, DexTarget)"/>
    public TransferRouteResult RoutesBetween(GameId from, GameId to, SpeciesId species) =>
        RoutesBetween(from, to, DexTarget.ForSpecies(species));

    /// <summary>
    /// Every way to get <paramref name="target"/> from one game to another, shortest first.
    /// </summary>
    /// <param name="from">Where it is now.</param>
    /// <param name="to">Where it needs to end up.</param>
    /// <param name="target">The species or form making the trip.</param>
    /// <returns>
    /// The routes, or an empty list with a <see cref="NoRouteReason"/> and a sentence explaining
    /// what stopped it.
    /// </returns>
    public TransferRouteResult RoutesBetween(GameId from, GameId to, DexTarget target)
    {
        if (Refuse(from, to) is { } refusal)
        {
            return refusal;
        }

        var routes = FindRoutes(from, to, target, applyFilters: true);
        if (routes.Count > 0)
        {
            return TransferRouteResult.Found(routes);
        }

        // Distinguishing "not connected" from "connected but not for this species" is the whole
        // point of the reason: one is permanent, the other is about this Pokemon.
        var ignoringFilters = FindRoutes(from, to, target, applyFilters: false);
        if (ignoringFilters.Count > 0)
        {
            return TransferRouteResult.NotFound(
                NoRouteReason.SpeciesNotCarried,
                ExplainBlockedRoute(ignoringFilters[0], target));
        }

        return NoPath(from, to);
    }

    /// <summary>The refusals that do not depend on the graph at all.</summary>
    private TransferRouteResult? Refuse(GameId from, GameId to)
    {
        if (!_games.Contains(from) || !_games.Contains(to))
        {
            var unknown = !_games.Contains(from) ? from : to;
            return TransferRouteResult.NotFound(
                NoRouteReason.UnknownGame,
                $"{unknown} is not in the transfer graph.");
        }

        return from == to
            ? TransferRouteResult.NotFound(
                NoRouteReason.SameGame,
                $"{to} already holds it; there is nothing to transfer.")
            : null;
    }

    /// <summary>Not connected at all, or connected further away than the search looks.</summary>
    private TransferRouteResult NoPath(GameId from, GameId to) =>
        ReachableFrom(to).Contains(from)
            ? TransferRouteResult.NotFound(
                NoRouteReason.TooManyHops,
                $"Getting from {from} to {to} takes more than {_maxHops.ToString(CultureInfo.InvariantCulture)} transfers.")
            : TransferRouteResult.NotFound(
                NoRouteReason.NotConnected,
                $"Nothing can be moved from {from} to {to}.");

    private void Add(DirectedEdge edge)
    {
        _games.Add(edge.From);
        _games.Add(edge.To);

        if (!_outgoing.TryGetValue(edge.From, out var outgoing))
        {
            _outgoing[edge.From] = outgoing = [];
        }

        if (!_incoming.TryGetValue(edge.To, out var incoming))
        {
            _incoming[edge.To] = incoming = [];
        }

        outgoing.Add(edge);
        incoming.Add(edge);
    }

    /// <summary>
    /// Iterative deepening rather than one deep search: it guarantees the shortest routes are
    /// found first, so cutting off at <see cref="_maxRoutes"/> never drops a shorter route in
    /// favour of a longer one already collected.
    /// </summary>
    private List<TransferRoute> FindRoutes(GameId from, GameId to, DexTarget target, bool applyFilters)
    {
        var routes = new List<TransferRoute>();

        // Without this, enumerating simple paths across a generation's near-complete trade clique
        // is exponential: a red-to-scarlet lookup took the better part of a second. The distance
        // map ignores filters and history windows, so it never over-estimates and never prunes a
        // real route.
        var distanceToDestination = DistancesTo(to);
        if (!distanceToDestination.ContainsKey(from))
        {
            return routes;
        }

        var history = RouteHistory.Empty.With(_context.GenerationOf(from));

        for (var depth = 1; depth <= _maxHops && routes.Count < _maxRoutes; depth++)
        {
            Walk(from, to, target, applyFilters, depth, history, distanceToDestination, [from], [], routes);
        }

        return routes;
    }

    /// <summary>Fewest hops from each game to <paramref name="destination"/>, ignoring filters.</summary>
    private Dictionary<GameId, int> DistancesTo(GameId destination)
    {
        var distance = new Dictionary<GameId, int> { [destination] = 0 };
        var queue = new Queue<GameId>();
        queue.Enqueue(destination);

        while (queue.Count > 0)
        {
            var current = queue.Dequeue();
            if (!_incoming.TryGetValue(current, out var edges))
            {
                continue;
            }

            foreach (var edge in edges.Where(edge => !distance.ContainsKey(edge.From)))
            {
                distance[edge.From] = distance[current] + 1;
                queue.Enqueue(edge.From);
            }
        }

        return distance;
    }

    private void Walk(
        GameId current,
        GameId destination,
        DexTarget target,
        bool applyFilters,
        int remainingHops,
        RouteHistory history,
        Dictionary<GameId, int> distanceToDestination,
        HashSet<GameId> visited,
        List<TransferHop> hops,
        List<TransferRoute> routes)
    {
        if (routes.Count >= _maxRoutes || remainingHops == 0 || !_outgoing.TryGetValue(current, out var edges))
        {
            return;
        }

        foreach (var edge in edges)
        {
            if (visited.Contains(edge.To))
            {
                continue;
            }

            // Nothing down this branch can reach the destination inside the remaining budget.
            if (!distanceToDestination.TryGetValue(edge.To, out var distance) || distance > remainingHops - 1)
            {
                continue;
            }

            // Checked whether or not filters are on, because a window is not about a species:
            // nothing at all comes back out of Bank into X once it has been in a Virtual Console
            // game, so this is not a route that carries some Pokemon and refuses others.
            if (!Takes(edge, history))
            {
                continue;
            }

            if (applyFilters && !Carries(edge, target))
            {
                continue;
            }

            hops.Add(edge.ToHop());

            if (edge.To == destination)
            {
                // Only exact-length routes: shorter ones were collected on an earlier pass.
                if (remainingHops == 1)
                {
                    routes.Add(new TransferRoute([.. hops]));
                }
            }
            else
            {
                visited.Add(edge.To);
                Walk(
                    edge.To,
                    destination,
                    target,
                    applyFilters,
                    remainingHops - 1,
                    history.With(_context.GenerationOf(edge.To)),
                    distanceToDestination,
                    visited,
                    hops,
                    routes);
                visited.Remove(edge.To);
            }

            hops.RemoveAt(hops.Count - 1);

            if (routes.Count >= _maxRoutes)
            {
                return;
            }
        }
    }

    /// <summary>Whether this edge will take a route that has been where this one has been.</summary>
    private static bool Takes(DirectedEdge edge, RouteHistory history) =>
        edge.History is not { } window || history.Inside(window);

    private bool Carries(DirectedEdge edge, DexTarget target) => edge.Filter switch
    {
        AllSpeciesFilter => true,
        NationalDexRangeFilter range =>
            _context.NationalDexNumber(target.Species) is { } number && number >= range.From && number <= range.To,
        PresentInTargetDexFilter => _context.DexContains(edge.To, target),
        _ => false,
    };

    private string ExplainBlockedRoute(TransferRoute route, DexTarget target)
    {
        foreach (var hop in route.Hops)
        {
            var edge = _outgoing[hop.From].First(candidate => candidate.To == hop.To && candidate.Mechanism == hop.Mechanism);
            if (Carries(edge, target))
            {
                continue;
            }

            return edge.Filter switch
            {
                NationalDexRangeFilter range =>
                    $"{target} cannot make the {hop.Mechanism} step from {hop.From} to {hop.To}: it only carries National Dex " +
                    $"{range.From.ToString(CultureInfo.InvariantCulture)} to {range.To.ToString(CultureInfo.InvariantCulture)}.",
                PresentInTargetDexFilter =>
                    $"{target} cannot make the {hop.Mechanism} step from {hop.From} to {hop.To}: {hop.To} has no dex entry for it.",
                _ =>
                    $"{target} cannot make the {hop.Mechanism} step from {hop.From} to {hop.To}.",
            };
        }

        return $"No route from {route.From} to {route.To} carries {target}.";
    }
}
