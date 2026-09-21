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
            [new DexCollection(Collection, "Platinum living dex", Platinum, [Emerald], FormsIncluded: false, GenderDifferencesIncluded: false)],
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
}
