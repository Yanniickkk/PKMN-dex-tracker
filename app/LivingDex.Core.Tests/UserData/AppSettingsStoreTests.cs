using LivingDex.Core.UserData;

namespace LivingDex.Core.Tests.UserData;

public sealed class AppSettingsStoreTests : IDisposable
{
    private readonly string _directory;
    private readonly AppSettingsStore _store;

    public AppSettingsStoreTests()
    {
        _directory = Path.Combine(Path.GetTempPath(), "livingdex-appsettings-" + Guid.NewGuid().ToString("n"));
        Directory.CreateDirectory(_directory);
        _store = new AppSettingsStore(Path.Combine(_directory, "settings.json"));
    }

    public void Dispose()
    {
        try
        {
            Directory.Delete(_directory, recursive: true);
        }
        catch (IOException)
        {
        }
    }

    [Fact]
    public void A_fresh_install_follows_the_system_and_has_no_data_file_yet()
    {
        var settings = _store.Load();

        Assert.Null(settings.DataFilePath);
        Assert.Equal(AppTheme.System, settings.Theme);
    }

    [Fact]
    public void What_is_saved_is_what_is_read_back()
    {
        _store.Save(new AppSettings("C:/somewhere/livingdex.json", AppTheme.Dark));

        var settings = _store.Load();

        Assert.Equal("C:/somewhere/livingdex.json", settings.DataFilePath);
        Assert.Equal(AppTheme.Dark, settings.Theme);
    }

    [Fact]
    public void Changing_one_setting_leaves_the_others_alone()
    {
        // The whole reason this store exists: writing a theme must not forget where the data is.
        _store.Save(new AppSettings("C:/somewhere/livingdex.json"));
        _store.Update(settings => settings with { Theme = AppTheme.Light });

        var settings = _store.Load();

        Assert.Equal("C:/somewhere/livingdex.json", settings.DataFilePath);
        Assert.Equal(AppTheme.Light, settings.Theme);
    }

    [Fact]
    public void Remembering_a_data_file_keeps_the_theme()
    {
        _store.Update(settings => settings with { Theme = AppTheme.Dark });

        new DataFileLocator(_store, new NeverAsked()).Remember("C:/elsewhere/livingdex.json");

        var settings = _store.Load();

        Assert.Equal("C:/elsewhere/livingdex.json", settings.DataFilePath);
        Assert.Equal(AppTheme.Dark, settings.Theme);
    }

    [Fact]
    public void A_theme_is_stored_by_name_rather_than_by_number()
    {
        _store.Update(settings => settings with { Theme = AppTheme.Dark });

        var raw = File.ReadAllText(_store.Path);

        // Readable, and renumbering the enum later cannot silently change what a file means.
        Assert.Contains("\"theme\": \"dark\"", raw, StringComparison.Ordinal);
    }

    [Fact]
    public void Unreadable_settings_read_as_a_fresh_install_rather_than_throwing()
    {
        File.WriteAllText(_store.Path, "not json at all");

        Assert.Equal(AppSettings.Empty, _store.Load());
    }

    private sealed class NeverAsked : IDataFileLocationPrompt
    {
        public string? AskWhereToKeepData(string suggestedPath) =>
            throw new InvalidOperationException("The picker should not have been shown.");
    }
}
