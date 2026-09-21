using LivingDex.Core.UserData;

namespace LivingDex.Core.Tests.UserData;

public sealed class DataFileLocatorTests : IDisposable
{
    private readonly string _directory;
    private readonly string _settingsFile;

    public DataFileLocatorTests()
    {
        _directory = Path.Combine(Path.GetTempPath(), "livingdex-settings-" + Guid.NewGuid().ToString("n"));
        Directory.CreateDirectory(_directory);
        _settingsFile = Path.Combine(_directory, "settings.json");
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

    private sealed class FakePrompt(string? answer) : IDataFileLocationPrompt
    {
        public int TimesAsked { get; private set; }

        public string? SuggestedPath { get; private set; }

        public string? AskWhereToKeepData(string suggestedPath)
        {
            TimesAsked++;
            SuggestedPath = suggestedPath;
            return answer;
        }
    }

    [Fact]
    public void A_first_run_asks_where_to_keep_the_data()
    {
        var chosen = Path.Combine(_directory, "chosen.json");
        var prompt = new FakePrompt(chosen);

        var resolved = new DataFileLocator(_settingsFile, prompt).Resolve();

        Assert.Equal(chosen, resolved);
        Assert.Equal(1, prompt.TimesAsked);
        Assert.Equal(DataFileLocator.DefaultDataFilePath, prompt.SuggestedPath);
    }

    [Fact]
    public void The_answer_is_remembered_so_the_question_is_asked_once()
    {
        var chosen = Path.Combine(_directory, "chosen.json");
        var first = new FakePrompt(chosen);
        new DataFileLocator(_settingsFile, first).Resolve();

        var second = new FakePrompt(answer: null);
        var resolved = new DataFileLocator(_settingsFile, second).Resolve();

        Assert.Equal(chosen, resolved);
        Assert.Equal(0, second.TimesAsked);
    }

    [Fact]
    public void Cancelling_falls_back_to_the_default_and_is_still_remembered()
    {
        var prompt = new FakePrompt(answer: null);

        var resolved = new DataFileLocator(_settingsFile, prompt).Resolve();

        // Cancelling should not leave the app with nowhere to save, and should not turn the
        // picker into something that reappears on every launch.
        Assert.Equal(DataFileLocator.DefaultDataFilePath, resolved);
        Assert.Equal(DataFileLocator.DefaultDataFilePath, new DataFileLocator(_settingsFile, prompt).Resolve());
        Assert.Equal(1, prompt.TimesAsked);
    }

    [Fact]
    public void Unreadable_settings_cost_one_dialog_rather_than_a_failure_to_start()
    {
        File.WriteAllText(_settingsFile, "not json at all");
        var chosen = Path.Combine(_directory, "chosen.json");
        var prompt = new FakePrompt(chosen);

        var resolved = new DataFileLocator(_settingsFile, prompt).Resolve();

        Assert.Equal(chosen, resolved);
        Assert.Equal(1, prompt.TimesAsked);
    }

    [Fact]
    public void Settings_saved_with_a_byte_order_mark_are_still_read()
    {
        // Notepad and PowerShell both write one. Losing the remembered path over an
        // invisible three bytes would look like the app forgetting for no reason.
        var chosen = Path.Combine(_directory, "chosen.json");
        File.WriteAllText(
            _settingsFile,
            "{\"dataFilePath\": \"" + chosen.Replace("\\", "\\\\", StringComparison.Ordinal) + "\"}",
            new System.Text.UTF8Encoding(encoderShouldEmitUTF8Identifier: true));

        var prompt = new FakePrompt(answer: null);

        Assert.Equal(chosen, new DataFileLocator(_settingsFile, prompt).Resolve());
        Assert.Equal(0, prompt.TimesAsked);
    }

    [Fact]
    public void A_path_can_be_changed_later_without_going_through_the_picker()
    {
        var locator = new DataFileLocator(_settingsFile, new FakePrompt(answer: null));
        var moved = Path.Combine(_directory, "moved.json");

        locator.Remember(moved);

        Assert.Equal(moved, locator.Load().DataFilePath);
        Assert.Equal(moved, new DataFileLocator(_settingsFile, new FakePrompt(answer: null)).Resolve());
    }
}
