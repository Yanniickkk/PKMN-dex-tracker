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
    private readonly Dictionary<(GameId Game, DexTarget Target), DexEntry> _entryByTarget;
    private readonly Dictionary<EvolutionRuleId, EvolutionRule> _evolutionRulesById;
    private readonly Dictionary<(GameId Game, DexTarget Target), List<AcquisitionMethod>> _methodsByEntry;
    private readonly HashSet<GameId> _gamesWithMethods;

    /// <summary>No dataset at all. What a screen holds before one is loaded.</summary>
    public static ReferenceData Empty { get; } = new([], [], [], []);

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

        // Last one wins rather than throwing: a dex that numbered the same target twice is a
        // pipeline fault the validator reports, and it must not stop the app from opening.
        _entryByTarget = new Dictionary<(GameId, DexTarget), DexEntry>();
        foreach (var entry in DexEntries)
        {
            _entryByTarget[(entry.Game, entry.Target)] = entry;
        }

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

    /// <summary>
    /// What this game calls each of its own Pokédexes, in the order the file lists them, or an
    /// empty list for a game whose dex has no name because it only has one.
    /// </summary>
    /// <remarks>
    /// The order is the pipeline's, and the pipeline writes them in the order the game hands
    /// them over: Central Kalos, then Coastal, then Mountain. Sorting them here would put
    /// Coastal first and teach a player an order the game never used.
    /// </remarks>
    public IReadOnlyList<string> DexNamesOf(GameId game) =>
        [.. DexOf(game).Select(entry => entry.Dex).OfType<string>().Distinct()];

    /// <summary>
    /// How many lists a player of this game can choose between, which is what a dex switch is
    /// for. One means there is nothing to choose and the switch should not be drawn.
    /// </summary>
    /// <remarks>
    /// <para>
    /// There are two ways to have more than one, and until Legends: Z-A only the first was
    /// asked about. Diamond has a National Dex of 493 and a Sinnoh Pokédex of 151 with its own
    /// numbering: two. Sword has no National Dex at all and three lists of its own: also two -
    /// three, in fact - and the grid used to ask only whether the game had a National Dex.
    /// </para>
    /// <para>
    /// What that cost is worth naming, because it was invisible: a game with several lists and
    /// no National Dex got no switch, so the grid showed the first of its lists and offered no
    /// way to the others. 184 of Sword and Shield's 584 entries, and 132 of Legends: Z-A's 364
    /// - the whole Hyperspace Pokédex - were in the dataset and unreachable in the app.
    /// </para>
    /// <para>
    /// A game that names no list at all still has one: twenty games were written before a dex
    /// needed a name, and a number that can only belong to one list does not need one.
    /// </para>
    /// </remarks>
    public int DexChoiceCount(GameId game)
    {
        var entries = DexOf(game);
        if (entries.Count == 0)
        {
            return 0;
        }

        var named = DexNamesOf(game).Count;
        var ofItsOwn = named == 0 ? 1 : named;

        return FindGame(game) is { HasNationalDex: true } ? ofItsOwn + 1 : ofItsOwn;
    }

    /// <summary>
    /// One entry of one game's dex, or null when that game does not list it.
    /// </summary>
    /// <remarks>
    /// The entry rather than the dex, because what the popup wants from it is one field: why
    /// this game cannot fill it, when the pipeline found a reason.
    /// </remarks>
    public DexEntry? FindDexEntry(GameId game, DexTarget target) =>
        _entryByTarget.GetValueOrDefault((game, target));
}
