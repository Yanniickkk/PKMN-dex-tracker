using System.Text;
using System.Text.Json;
using LivingDex.Core.Dataset;
using LivingDex.Core.Reference;
using LivingDex.Core.UserData;

namespace LivingDex.Core.Tests.UserData;

public sealed class UserDataStoreTests : IDisposable
{
    private static readonly DexCollectionId Collection = new("test-collection");
    private static readonly GameId Platinum = new("platinum");
    private static readonly GameId Emerald = new("emerald");

    private readonly string _directory;
    private readonly string _dataFile;

    public UserDataStoreTests()
    {
        _directory = Path.Combine(Path.GetTempPath(), "livingdex-tests-" + Guid.NewGuid().ToString("n"));
        Directory.CreateDirectory(_directory);
        _dataFile = Path.Combine(_directory, "livingdex.json");
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

    private static UserDataDocument DocumentWith(params string[] species) =>
        new(
            UserDataDocument.CurrentSchemaVersion,
            [new DexCollection(Collection, "Platinum living dex", Platinum, [Emerald], FormSelection.Default)],
            [.. species.Select(name => CaptureRecord.CaughtIn(Collection, DexTarget.ForSpecies(new SpeciesId(name)), Platinum, Platinum))]);

    private static IEnumerable<string> SpeciesIn(UserDataDocument document) =>
        document.Records.Select(record => record.Target.Species.Value).Order(StringComparer.Ordinal);

    [Fact]
    public async Task A_first_run_sees_an_empty_document_rather_than_an_error()
    {
        var store = new UserDataStore(_dataFile);

        var snapshot = await store.LoadAsync();

        Assert.Empty(snapshot.Document.Collections);
        Assert.Empty(snapshot.Document.Records);
        Assert.True(snapshot.Revision.IsMissing);
    }

    [Fact]
    public async Task What_is_saved_is_what_is_read_back()
    {
        var store = new UserDataStore(_dataFile);
        var document = DocumentWith("chimchar");

        var save = await store.SaveAsync(document, FileRevision.None);
        var snapshot = await store.LoadAsync();

        Assert.Equal(SaveStatus.Saved, save.Status);
        Assert.Equal(save.Revision, snapshot.Revision);
        Assert.Equal(["chimchar"], SpeciesIn(snapshot.Document));
        Assert.Equal(Platinum, snapshot.Document.Records[0].HoldingGame);
        Assert.Equal(CaptureStatus.InMainGame, snapshot.Document.Records[0].Status);
    }

    [Fact]
    public async Task The_form_selection_is_stored_as_one_switch_per_kind()
    {
        var store = new UserDataStore(_dataFile);
        await store.SaveAsync(DocumentWith("chimchar"), FileRevision.None);

        using var document = JsonDocument.Parse(await File.ReadAllTextAsync(_dataFile));
        var forms = document.RootElement.GetProperty("collections")[0].GetProperty("forms");

        Assert.True(forms.GetProperty("regional").GetBoolean());
        Assert.True(forms.GetProperty("functional").GetBoolean());
        Assert.False(forms.GetProperty("cosmetic").GetBoolean());
        Assert.False(forms.GetProperty("genderDifferences").GetBoolean());

        // "Any" is derived from the four, so storing it would be a second place to disagree.
        Assert.False(forms.TryGetProperty("any", out _));
    }

    [Fact]
    public async Task The_data_directory_is_created_on_first_save()
    {
        var nested = Path.Combine(_directory, "somewhere", "else", "livingdex.json");
        var store = new UserDataStore(nested);

        await store.SaveAsync(DocumentWith("chimchar"), FileRevision.None);

        Assert.True(File.Exists(nested));
    }

    [Fact]
    public async Task A_save_against_a_stale_revision_is_refused_and_changes_nothing()
    {
        var store = new UserDataStore(_dataFile);
        var first = await store.SaveAsync(DocumentWith("chimchar"), FileRevision.None);
        var second = await store.SaveAsync(DocumentWith("chimchar", "turtwig"), first.Revision);

        // The first revision is now two saves out of date.
        var stale = await store.SaveAsync(DocumentWith("piplup"), first.Revision);

        Assert.Equal(SaveStatus.Conflict, stale.Status);
        Assert.Equal(second.Revision, stale.Revision);
        Assert.Equal(["chimchar", "turtwig"], SpeciesIn((await store.LoadAsync()).Document));
    }

    [Fact]
    public async Task A_conflict_hands_back_what_is_on_disk_so_the_caller_can_merge()
    {
        var store = new UserDataStore(_dataFile);
        var first = await store.SaveAsync(DocumentWith("chimchar"), FileRevision.None);
        await store.SaveAsync(DocumentWith("chimchar", "turtwig"), first.Revision);

        var stale = await store.SaveAsync(DocumentWith("piplup"), first.Revision);

        Assert.NotNull(stale.OnDisk);
        Assert.Equal(["chimchar", "turtwig"], SpeciesIn(stale.OnDisk));
    }

    [Fact]
    public async Task Two_machines_editing_the_same_file_lose_nothing()
    {
        // Two installations pointed at one synced file. Both read the same starting point.
        var machineA = new UserDataStore(_dataFile);
        var machineB = new UserDataStore(_dataFile);

        var seed = await machineA.SaveAsync(DocumentWith("chimchar"), FileRevision.None);

        var onA = await machineA.LoadAsync();
        var onB = await machineB.LoadAsync();
        Assert.Equal(onA.Revision, onB.Revision);

        // A catches Turtwig and saves first.
        var savedByA = await machineA.SaveAsync(DocumentWith("chimchar", "turtwig"), onA.Revision);
        Assert.Equal(SaveStatus.Saved, savedByA.Status);

        // B catches Piplup and saves against the revision it still believes in.
        var refusedForB = await machineB.SaveAsync(DocumentWith("chimchar", "piplup"), onB.Revision);

        // B is told no, rather than quietly erasing Turtwig.
        Assert.Equal(SaveStatus.Conflict, refusedForB.Status);
        Assert.Equal(["chimchar", "turtwig"], SpeciesIn(refusedForB.OnDisk!));

        // B merges what it was handed with its own change, and saves against the current revision.
        var merged = new UserDataDocument(
            UserDataDocument.CurrentSchemaVersion,
            refusedForB.OnDisk!.Collections,
            [.. refusedForB.OnDisk.Records, CaptureRecord.CaughtIn(Collection, DexTarget.ForSpecies(new SpeciesId("piplup")), Platinum, Platinum)]);

        var savedByB = await machineB.SaveAsync(merged, refusedForB.Revision);

        Assert.Equal(SaveStatus.Saved, savedByB.Status);
        Assert.Equal(["chimchar", "piplup", "turtwig"], SpeciesIn((await machineA.LoadAsync()).Document));
        Assert.NotEqual(seed.Revision, savedByB.Revision);
    }

    [Fact]
    public async Task Concurrent_saves_never_leave_a_half_written_file()
    {
        var store = new UserDataStore(_dataFile);
        var start = await store.SaveAsync(DocumentWith("chimchar"), FileRevision.None);

        // Ten writers all believing they hold the current revision. Exactly one can be right.
        var attempts = await Task.WhenAll(Enumerable.Range(0, 10).Select(index =>
            new UserDataStore(_dataFile).SaveAsync(
                DocumentWith("chimchar", "species-" + index.ToString(System.Globalization.CultureInfo.InvariantCulture)),
                start.Revision)));

        Assert.Equal(1, attempts.Count(attempt => attempt.Status == SaveStatus.Saved));
        Assert.Equal(9, attempts.Count(attempt => attempt.Status == SaveStatus.Conflict));

        // Whatever landed, the file is complete and parses.
        var snapshot = await store.LoadAsync();
        Assert.Equal(2, snapshot.Document.Records.Count);
    }

    [Fact]
    public async Task No_temporary_files_are_left_behind()
    {
        var store = new UserDataStore(_dataFile);
        var first = await store.SaveAsync(DocumentWith("chimchar"), FileRevision.None);
        await store.SaveAsync(DocumentWith("chimchar", "turtwig"), first.Revision);

        Assert.Empty(Directory.GetFiles(_directory, "*.tmp-*"));
    }

    [Fact]
    public async Task Each_save_leaves_the_previous_content_as_a_backup()
    {
        var store = new UserDataStore(_dataFile);
        var first = await store.SaveAsync(DocumentWith("chimchar"), FileRevision.None);
        await store.SaveAsync(DocumentWith("chimchar", "turtwig"), first.Revision);

        var backups = Directory.GetFiles(store.BackupDirectory);
        Assert.Single(backups);

        var backed = JsonSerializer.Deserialize<UserDataDocument>(
            await File.ReadAllBytesAsync(backups[0]),
            DatasetJson.Options)!;

        Assert.Equal(["chimchar"], SpeciesIn(backed));
    }

    [Fact]
    public async Task Backups_stop_piling_up()
    {
        var store = new UserDataStore(_dataFile, backupsToKeep: 3);
        var revision = FileRevision.None;

        for (var index = 0; index < 8; index++)
        {
            var save = await store.SaveAsync(
                DocumentWith("species-" + index.ToString(System.Globalization.CultureInfo.InvariantCulture)),
                revision);

            revision = save.Revision;
        }

        Assert.Equal(3, Directory.GetFiles(store.BackupDirectory).Length);
    }

    [Fact]
    public async Task A_file_that_is_not_user_data_is_reported_rather_than_silently_replaced()
    {
        await File.WriteAllTextAsync(_dataFile, "{ this is not json");
        var store = new UserDataStore(_dataFile);

        await Assert.ThrowsAsync<UserDataCorruptException>(() => store.LoadAsync());
    }

    [Fact]
    public async Task An_outside_edit_is_noticed_without_reading_the_whole_file()
    {
        var store = new UserDataStore(_dataFile);
        var save = await store.SaveAsync(DocumentWith("chimchar"), FileRevision.None);

        Assert.Equal(save.Revision, await store.ReadRevisionAsync());

        await new UserDataStore(_dataFile).SaveAsync(DocumentWith("chimchar", "turtwig"), save.Revision);

        Assert.NotEqual(save.Revision, await store.ReadRevisionAsync());
    }

    [Fact]
    public async Task A_file_written_before_the_archive_existed_reads_as_collections_in_use()
    {
        // The exact shape the app wrote until archiving was added: no archivedOn anywhere. A
        // player's file is the one thing here that cannot be regenerated, so an older one has to
        // keep opening.
        await File.WriteAllTextAsync(
            _dataFile,
            """
            {
              "schemaVersion": 1,
              "collections": [
                {
                  "id": "test-collection",
                  "name": "Platinum living dex",
                  "mainGame": "platinum",
                  "linkedGames": [ "emerald" ],
                  "forms": { "regional": true, "functional": true, "cosmetic": false, "genderDifferences": false }
                }
              ],
              "records": []
            }
            """);

        var collection = Assert.Single((await new UserDataStore(_dataFile).LoadAsync()).Document.Collections);

        Assert.Null(collection.ArchivedOn);
        Assert.False(collection.IsArchived);
        Assert.Equal("Platinum living dex", collection.Name);
    }

    [Fact]
    public async Task An_archived_collection_survives_the_round_trip_and_an_unarchived_one_writes_no_field()
    {
        var store = new UserDataStore(_dataFile);
        var archived = new DateOnly(2026, 9, 26);
        var document = DocumentWith("chimchar");
        document = document with
        {
            Collections = [document.Collections[0] with { ArchivedOn = archived }],
        };

        await store.SaveAsync(document, FileRevision.None);
        Assert.Equal(archived, (await store.LoadAsync()).Document.Collections[0].ArchivedOn);

        var back = document with { Collections = [document.Collections[0] with { ArchivedOn = null }] };
        var save = await store.SaveAsync(back, await store.ReadRevisionAsync());

        Assert.Equal(SaveStatus.Saved, save.Status);
        Assert.DoesNotContain("archivedOn", await File.ReadAllTextAsync(_dataFile), StringComparison.Ordinal);
    }

    [Fact]
    public async Task A_file_with_a_byte_order_mark_is_read_rather_than_refused()
    {
        // What Notepad writes. Three invisible bytes should not cost somebody their evening.
        var document = DocumentWith("chimchar");
        var json = JsonSerializer.Serialize(document, DatasetJson.Options);
        await File.WriteAllTextAsync(_dataFile, json, new UTF8Encoding(encoderShouldEmitUTF8Identifier: true));

        var snapshot = await new UserDataStore(_dataFile).LoadAsync();

        Assert.Equal(["chimchar"], SpeciesIn(snapshot.Document));
    }

    [Fact]
    public async Task Json_that_is_not_this_app_s_data_is_refused_rather_than_read_as_empty()
    {
        // Without this it would open as an empty document and the next save would write the
        // player's real file - or somebody else's file - away.
        await File.WriteAllTextAsync(_dataFile, """{ "something": "else" }""");

        var refused = await Assert.ThrowsAsync<UserDataCorruptException>(
            () => new UserDataStore(_dataFile).LoadAsync());

        Assert.Contains("schema version", refused.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task A_file_from_a_newer_version_says_so_rather_than_calling_it_corrupt()
    {
        await File.WriteAllTextAsync(
            _dataFile,
            """{ "schemaVersion": 99, "collections": [], "records": [] }""");

        var refused = await Assert.ThrowsAsync<UserDataCorruptException>(
            () => new UserDataStore(_dataFile).LoadAsync());

        Assert.Contains("newer version", refused.Message, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("99", refused.Message, StringComparison.Ordinal);
    }

    [Fact]
    public async Task A_hand_written_file_without_its_lists_still_opens()
    {
        await File.WriteAllTextAsync(_dataFile, """{ "schemaVersion": 1 }""");

        var snapshot = await new UserDataStore(_dataFile).LoadAsync();

        Assert.Empty(snapshot.Document.Collections);
        Assert.Empty(snapshot.Document.Records);
    }

    [Fact]
    public async Task A_file_something_else_is_holding_is_reported_as_busy_rather_than_broken()
    {
        var store = new UserDataStore(_dataFile);
        await store.SaveAsync(DocumentWith("chimchar"), FileRevision.None);

        // What a sync client does while it uploads, and what another program does while it has
        // the file open.
        using var held = new FileStream(_dataFile, FileMode.Open, FileAccess.Read, FileShare.None);

        var busy = await Assert.ThrowsAsync<UserDataBusyException>(() => store.LoadAsync());

        Assert.Equal(_dataFile, busy.Path);
        Assert.Contains("holding", busy.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task A_save_that_cannot_reach_the_file_is_reported_as_busy_and_changes_nothing()
    {
        var store = new UserDataStore(_dataFile);
        var save = await store.SaveAsync(DocumentWith("chimchar"), FileRevision.None);

        using (var held = new FileStream(_dataFile, FileMode.Open, FileAccess.ReadWrite, FileShare.Read))
        {
            await Assert.ThrowsAsync<UserDataBusyException>(
                () => store.SaveAsync(DocumentWith("chimchar", "turtwig"), save.Revision));
        }

        // The old file is exactly what it was, and no temporary file is left lying beside it.
        Assert.Equal(["chimchar"], SpeciesIn((await store.LoadAsync()).Document));
        Assert.Empty(Directory.GetFiles(_directory, "*.tmp-*"));
    }
}
