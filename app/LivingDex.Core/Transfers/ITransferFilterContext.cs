using LivingDex.Core.Reference;

namespace LivingDex.Core.Transfers;

/// <summary>
/// The reference data the transfer graph needs to answer yes or no. Kept to these few questions
/// so the graph can be tested without a full dataset.
/// </summary>
public interface ITransferFilterContext
{
    /// <summary>
    /// The National Dex number of a species, or null when the species is unknown. A range filter
    /// refuses anything it cannot number.
    /// </summary>
    int? NationalDexNumber(SpeciesId species);

    /// <summary>Whether a game's own dex has an entry for this target.</summary>
    bool DexContains(GameId game, DexTarget target);

    /// <summary>
    /// Which generation a node belongs to, or null when the graph has never heard of it.
    /// </summary>
    /// <remarks>
    /// The only question here that is about the route rather than about a Pokemon, and it is
    /// what <see cref="HistoryWindow"/> is read against. A service answers with the generation
    /// it was built for: Bank is Generation 6, which is why it talks to eight games and stops.
    ///
    /// A null refuses any edge with a window, the way an unnumbered species is refused by a
    /// range filter. An edge that carries anything whatever its history never asks.
    /// </remarks>
    int? GenerationOf(GameId game);
}

/// <summary>
/// An <see cref="ITransferFilterContext"/> over reference data already in memory.
/// </summary>
public sealed class ReferenceFilterContext : ITransferFilterContext
{
    private readonly Dictionary<SpeciesId, int> _nationalDexNumbers;
    private readonly HashSet<(GameId Game, DexTarget Target)> _dexEntries;
    private readonly HashSet<(GameId Game, SpeciesId Species)> _dexSpecies;
    private readonly Dictionary<GameId, int> _generations;

    /// <param name="species">Every species in the dataset.</param>
    /// <param name="dexEntries">Every game's dex lines.</param>
    /// <param name="games">
    /// Every game and node, for the history windows. Optional because a graph whose edges carry
    /// no window never asks — which is every edge the dataset had before Pokémon Bank.
    /// </param>
    public ReferenceFilterContext(
        IEnumerable<Species> species,
        IEnumerable<DexEntry> dexEntries,
        IEnumerable<Game>? games = null)
    {
        ArgumentNullException.ThrowIfNull(species);
        ArgumentNullException.ThrowIfNull(dexEntries);

        _nationalDexNumbers = species.ToDictionary(one => one.Id, one => one.NationalDexNumber);
        _generations = (games ?? []).ToDictionary(one => one.Id, one => one.Generation);

        var entries = dexEntries as IReadOnlyCollection<DexEntry> ?? [.. dexEntries];
        _dexEntries = [.. entries.Select(entry => (entry.Game, entry.Target))];
        _dexSpecies = [.. entries.Select(entry => (entry.Game, entry.Target.Species))];
    }

    public int? NationalDexNumber(SpeciesId species) =>
        _nationalDexNumbers.TryGetValue(species, out var number) ? number : null;

    public int? GenerationOf(GameId game) =>
        _generations.TryGetValue(game, out var generation) ? generation : null;

    public bool DexContains(GameId game, DexTarget target)
    {
        if (_dexEntries.Contains((game, target)))
        {
            return true;
        }

        // A game that lists only the base species still accepts that species when the caller
        // asks about a form of it that the game does not enumerate separately.
        return target.IsForm && _dexSpecies.Contains((game, target.Species));
    }
}
