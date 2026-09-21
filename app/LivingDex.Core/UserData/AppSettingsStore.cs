using System.Text.Json;
using LivingDex.Core.Dataset;

namespace LivingDex.Core.UserData;

/// <summary>Which colours the app uses.</summary>
public enum AppTheme
{
    /// <summary>Follow whatever Windows is set to. What a fresh install does.</summary>
    System,

    Light,

    Dark,
}

/// <summary>
/// Settings that belong to this machine rather than to the data. They deliberately do not live
/// in the data file: where that file is kept is exactly what cannot be read from inside it, and
/// a theme is about this screen rather than about the collection.
/// </summary>
/// <param name="DataFilePath">Where the player chose to keep their data, if they have chosen.</param>
/// <param name="Theme">Which colours to use.</param>
public sealed record AppSettings(string? DataFilePath, AppTheme Theme = AppTheme.System)
{
    /// <summary>Nothing chosen yet.</summary>
    public static AppSettings Empty { get; } = new((string?)null);
}

/// <summary>
/// Reads and writes <see cref="AppSettings"/>.
/// </summary>
/// <remarks>
/// Separate from anything that uses one setting, so that changing one never drops another. The
/// file is small and rewritten whole, so every write starts from what is already there.
/// </remarks>
public sealed class AppSettingsStore
{
    private readonly string _path;

    public AppSettingsStore(string path)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(path);
        _path = path;
    }

    /// <summary>Where machine settings live when the app is not told otherwise.</summary>
    // Qualified: the instance Path property below shadows System.IO.Path here.
    public static string DefaultPath { get; } = System.IO.Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
        "LivingDexTracker",
        "settings.json");

    /// <summary>The file this store reads and writes.</summary>
    public string Path => _path;

    /// <summary>
    /// The settings as stored. Unreadable settings read as empty rather than throwing: losing a
    /// remembered path costs one dialog, and is not worth refusing to start over.
    /// </summary>
    public AppSettings Load()
    {
        if (!File.Exists(_path))
        {
            return AppSettings.Empty;
        }

        try
        {
            // ReadAllText rather than ReadAllBytes: an editor that saves this file with a byte
            // order mark would otherwise make it unparseable, and the player would be asked for
            // the location again with no idea why.
            return JsonSerializer.Deserialize<AppSettings>(
                File.ReadAllText(_path),
                DatasetJson.Options) ?? AppSettings.Empty;
        }
        catch (JsonException)
        {
            return AppSettings.Empty;
        }
        catch (IOException)
        {
            return AppSettings.Empty;
        }
    }

    /// <summary>Writes the settings whole.</summary>
    public void Save(AppSettings settings)
    {
        ArgumentNullException.ThrowIfNull(settings);

        Directory.CreateDirectory(System.IO.Path.GetDirectoryName(_path)!);
        File.WriteAllBytes(_path, JsonSerializer.SerializeToUtf8Bytes(settings, DatasetJson.Options));
    }

    /// <summary>
    /// Changes part of the settings, leaving the rest as it was. Every caller should go through
    /// this rather than building an <see cref="AppSettings"/> from scratch, or saving one setting
    /// would quietly reset the others.
    /// </summary>
    public AppSettings Update(Func<AppSettings, AppSettings> change)
    {
        ArgumentNullException.ThrowIfNull(change);

        var updated = change(Load());
        Save(updated);
        return updated;
    }
}
