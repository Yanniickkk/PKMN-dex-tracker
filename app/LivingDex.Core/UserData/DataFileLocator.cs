namespace LivingDex.Core.UserData;

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
    private readonly AppSettingsStore _settings;
    private readonly IDataFileLocationPrompt _prompt;

    /// <param name="settings">Where the remembered path is stored.</param>
    /// <param name="prompt">How to ask on first run.</param>
    public DataFileLocator(AppSettingsStore settings, IDataFileLocationPrompt prompt)
    {
        ArgumentNullException.ThrowIfNull(settings);
        ArgumentNullException.ThrowIfNull(prompt);

        _settings = settings;
        _prompt = prompt;
    }

    /// <param name="settingsPath">Where the remembered path is stored.</param>
    /// <param name="prompt">How to ask on first run.</param>
    public DataFileLocator(string settingsPath, IDataFileLocationPrompt prompt)
        : this(new AppSettingsStore(settingsPath), prompt)
    {
    }

    /// <inheritdoc cref="AppSettingsStore.DefaultPath"/>
    public static string DefaultSettingsPath => AppSettingsStore.DefaultPath;

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
        var settings = _settings.Load();
        if (!string.IsNullOrWhiteSpace(settings.DataFilePath))
        {
            return settings.DataFilePath;
        }

        var chosen = _prompt.AskWhereToKeepData(DefaultDataFilePath);
        var path = string.IsNullOrWhiteSpace(chosen) ? DefaultDataFilePath : chosen;

        Remember(path);
        return path;
    }

    /// <inheritdoc cref="AppSettingsStore.Load"/>
    public AppSettings Load() => _settings.Load();

    /// <summary>Stores the chosen path so the picker is not shown again.</summary>
    public void Remember(string dataFilePath)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(dataFilePath);

        // Through Update, not a fresh AppSettings: writing one setting must not reset the others.
        _settings.Update(settings => settings with { DataFilePath = dataFilePath });
    }
}
