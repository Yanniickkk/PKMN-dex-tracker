using System.Reflection;
using System.Text.Json;
using LivingDex.Core.Reference;

namespace LivingDex.Core.Dataset;

/// <summary>What a load produced.</summary>
/// <param name="Stamp">Which build of the dataset this is.</param>
/// <param name="Reference">The tables, indexed and ready to query.</param>
/// <param name="BoxArt">
/// The file shipped for each game that has one, by game. A file name rather than a flag,
/// because covers keep whatever kind their source holds - some PNG, some JPEG - and the app
/// serves what it was handed rather than insisting on one.
/// </param>
/// <param name="MethodIcons">
/// The ways of obtaining a Pokemon an icon was shipped for, by the key the pipeline names them
/// with. Asked before rendering one, so a build that skipped them leaves the app drawing its own
/// rather than showing a broken image.
/// </param>
public sealed record LoadedDataset(
    DatasetStamp Stamp,
    ReferenceData Reference,
    IReadOnlyDictionary<GameId, string> BoxArt,
    IReadOnlySet<string> MethodIcons)
{
    /// <summary>Whether an image was shipped for this game.</summary>
    public bool HasBoxArt(GameId game) => BoxArt.ContainsKey(game);

    /// <summary>
    /// What to ask the web view for, for example <c>boxart/emerald.jpg</c>, or null when this
    /// game has no cover.
    /// </summary>
    public string? BoxArtPath(GameId game) =>
        BoxArt.TryGetValue(game, out var file) ? $"{DatasetLayout.BoxArtDirectory}/{file}" : null;

    /// <summary>
    /// What to ask the web view for, for example <c>icons/good-rod.png</c>, or null when no icon
    /// was shipped for that way of obtaining something.
    /// </summary>
    public string? MethodIconPath(string key) =>
        MethodIcons.Contains(key) ? $"{DatasetLayout.IconsDirectory}/{key}.png" : null;

    /// <summary>True when no dataset was found at all.</summary>
    public bool IsEmpty => Reference.Games.Count == 0;

    /// <summary>What a build with no dataset embedded looks like.</summary>
    public static LoadedDataset None { get; } = new(
        new DatasetStamp("0.0.0", DateOnly.MinValue),
        new ReferenceData([], [], [], []),
        new Dictionary<GameId, string>(),
        new HashSet<string>(StringComparer.Ordinal));
}

/// <summary>Thrown when a dataset is present but unreadable, which is a build problem.</summary>
public sealed class DatasetLoadException : Exception
{
    public DatasetLoadException()
    {
    }

    public DatasetLoadException(string message)
        : base(message)
    {
    }

    public DatasetLoadException(string message, Exception innerException)
        : base(message, innerException)
    {
    }
}

/// <summary>
/// Reads the dataset out of the assembly it was built into.
/// </summary>
/// <remarks>
/// The dataset is embedded rather than shipped as files beside the exe, for the same reason the
/// web assets are: the app is one file, and half a delivery should not be possible. The cost is
/// that rebuilding the dataset means rebuilding the app, which takes about two seconds.
/// </remarks>
public static class DatasetLoader
{
    private const string Prefix = "dataset/";

    /// <summary>
    /// Reads the dataset embedded in <paramref name="assembly"/>, or
    /// <see cref="LoadedDataset.None"/> when there is none.
    /// </summary>
    /// <exception cref="DatasetLoadException">A file is present but cannot be read.</exception>
    public static LoadedDataset Load(Assembly assembly)
    {
        ArgumentNullException.ThrowIfNull(assembly);

        var names = new HashSet<string>(assembly.GetManifestResourceNames(), StringComparer.Ordinal);

        var index = Read<DatasetIndex>(assembly, names, DatasetLayout.IndexFile);
        if (index is null)
        {
            return LoadedDataset.None;
        }

        var games = new List<Game>(index.Games.Count);
        var dexEntries = new List<DexEntry>();
        var methods = new List<AcquisitionMethod>();

        foreach (var gameId in index.Games)
        {
            var data = Read<GameData>(assembly, names, DatasetLayout.GameFile(gameId))
                ?? throw new DatasetLoadException(
                    $"The index lists {gameId} but there is no file for it in the dataset.");

            games.Add(data.Game);
            dexEntries.AddRange(data.DexEntries);
            methods.AddRange(data.AcquisitionMethods);
        }

        var reference = new ReferenceData(
            games,
            Read<IReadOnlyList<Species>>(assembly, names, DatasetLayout.SpeciesFile) ?? [],
            Read<IReadOnlyList<Form>>(assembly, names, DatasetLayout.FormsFile) ?? [],
            dexEntries,
            Read<IReadOnlyList<TransferEdge>>(assembly, names, DatasetLayout.TransfersFile) ?? [],
            Read<IReadOnlyList<EvolutionRule>>(assembly, names, DatasetLayout.EvolutionRulesFile) ?? [],
            methods);

        // One cover per game, keyed by the game its file is named after.
        var boxArtPrefix = $"{Prefix}{DatasetLayout.BoxArtDirectory}/";
        var boxArt = names
            .Where(name => name.StartsWith(boxArtPrefix, StringComparison.Ordinal))
            .Select(name => name[boxArtPrefix.Length..])
            .ToDictionary(
                file => new GameId(System.IO.Path.GetFileNameWithoutExtension(file)),
                file => file);

        var iconPrefix = $"{Prefix}{DatasetLayout.IconsDirectory}/";
        var icons = names
            .Where(name => name.StartsWith(iconPrefix, StringComparison.Ordinal))
            .Select(name => System.IO.Path.GetFileNameWithoutExtension(name[iconPrefix.Length..]))
            .ToHashSet(StringComparer.Ordinal);

        return new LoadedDataset(index.Stamp, reference, boxArt, icons);
    }

    private static T? Read<T>(Assembly assembly, HashSet<string> names, string path)
        where T : class
    {
        var name = Prefix + path.Replace('\\', '/');
        if (!names.Contains(name))
        {
            return null;
        }

        using var stream = assembly.GetManifestResourceStream(name);
        if (stream is null)
        {
            return null;
        }

        try
        {
            return JsonSerializer.Deserialize<T>(stream, DatasetJson.Options);
        }
        catch (JsonException exception)
        {
            throw new DatasetLoadException($"{name} is not readable as {typeof(T).Name}.", exception);
        }
    }
}
