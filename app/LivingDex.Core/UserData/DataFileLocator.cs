using System.Text.Json;
using LivingDex.Core.Dataset;

namespace LivingDex.Core.UserData;

/// <summary>
/// Settings that belong to this machine rather than to the data. They deliberately do not live
/// in the data file: where that file is kept is exactly what cannot be read from inside it.
/// </summary>
/// <param name="DataFilePath">Where the player chose to keep their data, if they have chosen.</param>
public sealed record AppSettings(string? DataFilePath)
{
    /// <summary>Nothing chosen yet.</summary>
    public static AppSettings Empty { get; } = new((string?)null);
}

/// <summary>Asks the player where to keep their data. Implemented by the UI layer.</summary>
public interface IDataFileLocationPrompt
{
    /// <summary>
    /// Shows the picker.
    /// </summary>
    /// <param name="suggestedPath">Where the app would put the file if left alone.</param>
    /// <returns>The chosen path, or null if the player cancelled.</returns>
    string? AskWhereToKeepData(string suggestedPath);
}

/// <summary>
/// Works out which data file to use: the remembered one, or one the player picks on first run.
/// </summary>
public sealed class DataFileLocator
{
    private readonly string _settingsPath;
    private readonly IDataFileLocationPrompt _prompt;

    /// <param name="settingsPath">Where the remembered path is stored.</param>
    /// <param name="prompt">How to ask on first run.</param>
    public DataFileLocator(string settingsPath, IDataFileLocationPrompt prompt)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(settingsPath);
        ArgumentNullException.ThrowIfNull(prompt);

        _settingsPath = settingsPath;
        _prompt = prompt;
    }

    /// <summary>Where machine settings live when the app is not told otherwise.</summary>
    public static string DefaultSettingsPath { get; } = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
        "LivingDexTracker",
        "settings.json");

    /// <summary>
    /// What the picker starts on. Documents rather than AppData, because the player is meant to
    /// be able to put this in a synced folder and find it again.
    /// </summary>
    public static string DefaultDataFilePath { get; } = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),
        "Living Dex Tracker",
        "livingdex.json");

    /// <summary>
    /// The data file to use. Asks on first run and remembers the answer; a cancelled picker
    /// falls back to <see cref="DefaultDataFilePath"/> rather than leaving the app with nowhere
    /// to save, and is remembered too so the question is asked once.
    /// </summary>
    public string Resolve()
    {
        var settings = Load();
        if (!string.IsNullOrWhiteSpace(settings.DataFilePath))
        {
            return settings.DataFilePath;
        }

        var chosen = _prompt.AskWhereToKeepData(DefaultDataFilePath);
        var path = string.IsNullOrWhiteSpace(chosen) ? DefaultDataFilePath : chosen;

        Remember(path);
        return path;
    }

    /// <summary>The settings as stored. Unreadable settings read as empty rather than throwing:
    /// losing a remembered path costs one dialog, and is not worth refusing to start over.</summary>
    public AppSettings Load()
    {
        if (!File.Exists(_settingsPath))
        {
            return AppSettings.Empty;
        }

        try
        {
            return JsonSerializer.Deserialize<AppSettings>(
                File.ReadAllBytes(_settingsPath),
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

    /// <summary>Stores the chosen path so the picker is not shown again.</summary>
    public void Remember(string dataFilePath)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(dataFilePath);

        Directory.CreateDirectory(Path.GetDirectoryName(_settingsPath)!);
        File.WriteAllBytes(
            _settingsPath,
            JsonSerializer.SerializeToUtf8Bytes(new AppSettings(dataFilePath), DatasetJson.Options));
    }
}
