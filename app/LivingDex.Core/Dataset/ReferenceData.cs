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
    private readonly Dictionary<EvolutionRuleId, EvolutionRule> _evolutionRulesById;
    private readonly Dictionary<(GameId Game, DexTarget Target), List<AcquisitionMethod>> _methodsByEntry;
    private readonly HashSet<GameId> _gamesWithMethods;

    public ReferenceData(
        IEnumerable<Game> games,
        IEnumerable<Species> species,
        IEnumerable<Form> forms,
        IEnumerable<DexEntry> dexEntries,
        IEnumerable<TransferEdge>? transferEdges = null,
        IEnumerable<EvolutionRule>? evolutionRules = null,
        IEnumerable<AcquisitionMethod>? acquisitionMethods = null)
    {
        ArgumentNullException.ThrowIfNull(games);
        ArgumentNullException.ThrowIfNull(species);
        ArgumentNullException.ThrowIfNull(forms);
        ArgumentNullException.ThrowIfNull(dexEntries);

        Games = [.. games];
        Species = [.. species];
        Forms = [.. forms];
        DexEntries = [.. dexEntries];
        TransferEdges = [.. transferEdges ?? []];
        EvolutionRules = [.. evolutionRules ?? []];
        AcquisitionMethods = [.. acquisitionMethods ?? []];

        _gamesById = Games.ToDictionary(game => game.Id);
        _speciesById = Species.ToDictionary(one => one.Id);

        _formsBySpecies = Forms
            .GroupBy(form => form.Species)
            .ToDictionary(group => group.Key, group => group.ToList());

        _dexByGame = DexEntries
            .GroupBy(entry => entry.Game)
            .ToDictionary(group => group.Key, group => group.ToList());

        _evolutionRulesById = EvolutionRules.ToDictionary(rule => rule.Id);

        _methodsByEntry = AcquisitionMethods
            .GroupBy(method => (method.Game, method.Target))
            .ToDictionary(group => group.Key, group => group.ToList());

        _gamesWithMethods = [.. AcquisitionMethods.Select(method => method.Game)];
    }

    /// <summary>Every game, including transfer-only nodes.</summary>
    public IReadOnlyList<Game> Games { get; }

    /// <summary>Every species.</summary>
    public IReadOnlyList<Species> Species { get; }

    /// <summary>Every form.</summary>
    public IReadOnlyList<Form> Forms { get; }

    /// <summary>Every game's dex lines.</summary>
    public IReadOnlyList<DexEntry> DexEntries { get; }

    /// <summary>The transfer graph.</summary>
    public IReadOnlyList<TransferEdge> TransferEdges { get; }

    /// <summary>Every evolution rule, shared across games.</summary>
    public IReadOnlyList<EvolutionRule> EvolutionRules { get; }

    /// <summary>Every way to obtain something, across every game.</summary>
    public IReadOnlyList<AcquisitionMethod> AcquisitionMethods { get; }

    /// <summary>The game with this id, or null.</summary>
    public Game? FindGame(GameId id) => _gamesById.GetValueOrDefault(id);

    /// <summary>The species with this id, or null.</summary>
    public Species? FindSpecies(SpeciesId id) => _speciesById.GetValueOrDefault(id);

    /// <summary>Every form of a species, or an empty list.</summary>
    public IReadOnlyList<Form> FormsOf(SpeciesId species) =>
        _formsBySpecies.TryGetValue(species, out var forms) ? forms : [];

    /// <summary>The evolution rule with this id, or null.</summary>
    public EvolutionRule? FindEvolutionRule(EvolutionRuleId id) => _evolutionRulesById.GetValueOrDefault(id);

    /// <summary>
    /// What to call one entry on screen, for example <c>Vulpix (Alolan)</c>. One place, because
    /// the grid, the detail popup and everything that names a trade or an evolution have to
    /// agree.
    /// </summary>
    public string NameOf(DexTarget target)
    {
        var species = FindSpecies(target.Species)?.Name ?? target.Species.Value;

        if (target.Form is not { } form)
        {
            return species;
        }

        var name = FormsOf(target.Species).FirstOrDefault(one => one.Id == form)?.Name;
        return name is null ? $"{species} ({form.Value})" : $"{species} ({name})";
    }

    /// <summary>
    /// The typing of one entry: the form's own when it has one, the species' otherwise.
    /// </summary>
    /// <remarks>
    /// A form's types are set only when they differ, which is why the fallback matters: an
    /// Alolan Vulpix is Ice, a Vivillon pattern is whatever Vivillon is.
    /// </remarks>
    public IReadOnlyList<PokemonType> TypesOf(DexTarget target)
    {
        if (target.Form is { } form)
        {
            var types = FormsOf(target.Species).FirstOrDefault(one => one.Id == form)?.Types;
            if (types is not null)
            {
                return types;
            }
        }

        return FindSpecies(target.Species)?.Types ?? [];
    }

    /// <summary>Every way to get one entry in one game, or an empty list.</summary>
    public IReadOnlyList<AcquisitionMethod> MethodsFor(GameId game, DexTarget target) =>
        _methodsByEntry.TryGetValue((game, target), out var methods) ? methods : [];

    /// <summary>
    /// Whether the dataset knows any way at all to obtain anything in this game.
    /// </summary>
    /// <remarks>
    /// Not the same question as whether one entry is obtainable. A game whose acquisition data
    /// has not been gathered yet answers no to every entry, and a screen that asks "can I catch
    /// this here" needs to tell that apart from "no, you cannot" before it shows the answer as
    /// fact.
    /// </remarks>
    public bool HasAcquisitionData(GameId game) => _gamesWithMethods.Contains(game);

    /// <summary>One game's dex lines, or an empty list.</summary>
    public IReadOnlyList<DexEntry> DexOf(GameId game) =>
        _dexByGame.TryGetValue(game, out var entries) ? entries : [];
}
