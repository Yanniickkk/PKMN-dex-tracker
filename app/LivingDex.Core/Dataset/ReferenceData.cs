using LivingDex.Core.Reference;

namespace LivingDex.Core.Dataset;

/// <summary>
/// The reference tables in memory, with the lookups the app asks for over and over.
/// </summary>
/// <remarks>
/// Built once from the dataset on disk and treated as read-only. The pipeline is what changes
/// the numbers in it; nothing in the app writes here.
/// </remarks>
public sealed class ReferenceData
{
    private readonly Dictionary<GameId, Game> _gamesById;
    private readonly Dictionary<SpeciesId, Species> _speciesById;
    private readonly Dictionary<SpeciesId, List<Form>> _formsBySpecies;
    private readonly Dictionary<GameId, List<DexEntry>> _dexByGame;

    public ReferenceData(
        IEnumerable<Game> games,
        IEnumerable<Species> species,
        IEnumerable<Form> forms,
        IEnumerable<DexEntry> dexEntries)
    {
        ArgumentNullException.ThrowIfNull(games);
        ArgumentNullException.ThrowIfNull(species);
        ArgumentNullException.ThrowIfNull(forms);
        ArgumentNullException.ThrowIfNull(dexEntries);

        Games = [.. games];
        Species = [.. species];
        Forms = [.. forms];
        DexEntries = [.. dexEntries];

        _gamesById = Games.ToDictionary(game => game.Id);
        _speciesById = Species.ToDictionary(one => one.Id);

        _formsBySpecies = Forms
            .GroupBy(form => form.Species)
            .ToDictionary(group => group.Key, group => group.ToList());

        _dexByGame = DexEntries
            .GroupBy(entry => entry.Game)
            .ToDictionary(group => group.Key, group => group.ToList());
    }

    /// <summary>Every game, including transfer-only nodes.</summary>
    public IReadOnlyList<Game> Games { get; }

    /// <summary>Every species.</summary>
    public IReadOnlyList<Species> Species { get; }

    /// <summary>Every form.</summary>
    public IReadOnlyList<Form> Forms { get; }

    /// <summary>Every game's dex lines.</summary>
    public IReadOnlyList<DexEntry> DexEntries { get; }

    /// <summary>The game with this id, or null.</summary>
    public Game? FindGame(GameId id) => _gamesById.GetValueOrDefault(id);

    /// <summary>The species with this id, or null.</summary>
    public Species? FindSpecies(SpeciesId id) => _speciesById.GetValueOrDefault(id);

    /// <summary>Every form of a species, or an empty list.</summary>
    public IReadOnlyList<Form> FormsOf(SpeciesId species) =>
        _formsBySpecies.TryGetValue(species, out var forms) ? forms : [];

    /// <summary>One game's dex lines, or an empty list.</summary>
    public IReadOnlyList<DexEntry> DexOf(GameId game) =>
        _dexByGame.TryGetValue(game, out var entries) ? entries : [];
}
