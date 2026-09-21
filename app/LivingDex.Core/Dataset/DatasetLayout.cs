using LivingDex.Core.Reference;

namespace LivingDex.Core.Dataset;

/// <summary>
/// Where each part of the dataset lives on disk. One file per game plus shared tables, so that
/// adding Emerald touches exactly one game file and nothing of Platinum.
/// </summary>
public static class DatasetLayout
{
    /// <summary>Version stamp and the list of games present.</summary>
    public const string IndexFile = "index.json";

    /// <summary>Every species, shared across all games.</summary>
    public const string SpeciesFile = "species.json";

    /// <summary>Every form, shared across all games.</summary>
    public const string FormsFile = "forms.json";

    /// <summary>Every evolution rule. Which games can use one is decided per game.</summary>
    public const string EvolutionRulesFile = "evolution-rules.json";

    /// <summary>The transfer graph.</summary>
    public const string TransfersFile = "transfers.json";

    /// <summary>Directory holding one file per game.</summary>
    public const string GamesDirectory = "games";

    /// <summary>Directory holding battle sprites.</summary>
    public const string SpritesDirectory = "sprites";

    /// <summary>Directory holding one box art image per game.</summary>
    public const string BoxArtDirectory = "boxart";

    /// <summary>Directory holding one icon per way of obtaining a Pokemon.</summary>
    public const string IconsDirectory = "icons";

    /// <summary>The file holding everything specific to one game.</summary>
    public static string GameFile(GameId game) => $"{GamesDirectory}/{game.Value}.json";
}

/// <summary>
/// Contents of <see cref="DatasetLayout.IndexFile"/>.
/// </summary>
/// <param name="Stamp">Which build this is.</param>
/// <param name="Games">The games with a file under <see cref="DatasetLayout.GamesDirectory"/>.</param>
public sealed record DatasetIndex(DatasetStamp Stamp, IReadOnlyList<GameId> Games);

/// <summary>
/// Contents of one game file: the game itself, its dex, and every way to obtain each entry.
/// Nothing here is shared with another game.
/// </summary>
/// <param name="Game">The game.</param>
/// <param name="DexEntries">Its dex, in that game numbering.</param>
/// <param name="AcquisitionMethods">Every way to get something in this game.</param>
public sealed record GameData(
    Game Game,
    IReadOnlyList<DexEntry> DexEntries,
    IReadOnlyList<AcquisitionMethod> AcquisitionMethods);
