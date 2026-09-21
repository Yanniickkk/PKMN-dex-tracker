using LivingDex.Core.Reference;

namespace LivingDex.Core.Transfers;

/// <summary>
/// The reference data a <see cref="SpeciesFilter"/> needs to answer yes or no. Kept to these two
/// questions so the graph can be tested without a full dataset.
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
}

/// <summary>
/// An <see cref="ITransferFilterContext"/> over reference data already in memory.
/// </summary>
public sealed class ReferenceFilterContext : ITransferFilterContext
{
    private readonly Dictionary<SpeciesId, int> _nationalDexNumbers;
    private readonly HashSet<(GameId Game, DexTarget Target)> _dexEntries;
    private readonly HashSet<(GameId Game, SpeciesId Species)> _dexSpecies;

    /// <param name="species">Every species in the dataset.</param>
    /// <param name="dexEntries">Every game's dex lines.</param>
    public ReferenceFilterContext(IEnumerable<Species> species, IEnumerable<DexEntry> dexEntries)
    {
        ArgumentNullException.ThrowIfNull(species);
        ArgumentNullException.ThrowIfNull(dexEntries);

        _nationalDexNumbers = species.ToDictionary(one => one.Id, one => one.NationalDexNumber);

        var entries = dexEntries as IReadOnlyCollection<DexEntry> ?? [.. dexEntries];
        _dexEntries = [.. entries.Select(entry => (entry.Game, entry.Target))];
        _dexSpecies = [.. entries.Select(entry => (entry.Game, entry.Target.Species))];
    }

    public int? NationalDexNumber(SpeciesId species) =>
        _nationalDexNumbers.TryGetValue(species, out var number) ? number : null;

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
