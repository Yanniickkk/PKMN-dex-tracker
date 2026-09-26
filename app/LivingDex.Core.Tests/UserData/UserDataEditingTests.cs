using System.Text.Json;
using LivingDex.Core.Dataset;
using LivingDex.Core.Reference;
using LivingDex.Core.UserData;

namespace LivingDex.Core.Tests.UserData;

public sealed class UserDataEditingTests : IDisposable
{
    private static readonly DexCollectionId Collection = new("test-collection");
    private static readonly GameId Platinum = new("platinum");

    private readonly string _directory;
    private readonly string _dataFile;

    public UserDataEditingTests()
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

    private static DexCollection Mine { get; } =
        new(Collection, "Platinum living dex", Platinum, [], FormSelection.Default);

    /// <summary>
    /// Another writer landing on the file, from inside the change function. Written straight to
    /// disk rather than through the store: the point is that the file moved on, and a test that
    /// blocked on a Task while the store held its lock would be testing the lock instead.
    /// </summary>
    private void SomebodyElseWrites(UserDataDocument document) =>
        File.WriteAllBytes(_dataFile, JsonSerializer.SerializeToUtf8Bytes(document, DatasetJson.Options));

    [Fact]
    public async Task A_change_is_read_applied_and_written()
    {
        var store = new UserDataStore(_dataFile);

        var outcome = await store.UpdateAsync(document => document with { Collections = [Mine] });

        Assert.Equal(UpdateOutcome.Saved, outcome);
        Assert.Single((await store.LoadAsync()).Document.Collections);
    }

    [Fact]
    public async Task Handing_back_the_same_document_writes_nothing()
    {
        var store = new UserDataStore(_dataFile);
        await store.UpdateAsync(document => document with { Collections = [Mine] });
        var before = await store.ReadRevisionAsync();

        var outcome = await store.UpdateAsync(document => document);

        Assert.Equal(UpdateOutcome.NothingToDo, outcome);
        Assert.Equal(before, await store.ReadRevisionAsync());
    }

    [Fact]
    public async Task A_file_that_moved_on_is_read_again_rather_than_overwritten()
    {
        var store = new UserDataStore(_dataFile);
        await store.UpdateAsync(document => document with { Collections = [Mine] });

        var attempts = 0;

        var outcome = await store.UpdateAsync(document =>
        {
            // Someone else writes between the read and the save, once.
            if (attempts++ == 0)
            {
                var other = Mine with { Id = DexCollectionId.New(), Name = "Written elsewhere" };
                SomebodyElseWrites(document with { Collections = [.. document.Collections, other] });
            }

            return document with
            {
                Records =
                [
                    .. document.Records,
                    CaptureRecord.CaughtIn(
                        Collection,
                        DexTarget.ForSpecies(new SpeciesId("chimchar")),
                        Platinum,
                        Platinum),
                ],
            };
        });

        var document = (await store.LoadAsync()).Document;

        Assert.Equal(UpdateOutcome.Saved, outcome);
        Assert.Equal(2, attempts);
        // Both survive: the second attempt read the file the other writer had left.
        Assert.Equal(2, document.Collections.Count);
        Assert.Single(document.Records);
    }

    [Fact]
    public async Task A_file_that_never_stops_moving_is_reported_rather_than_forced()
    {
        var store = new UserDataStore(_dataFile);
        await store.UpdateAsync(document => document with { Collections = [Mine] });

        var attempts = 0;

        var outcome = await store.UpdateAsync(
            document =>
            {
                attempts++;
                var other = Mine with { Id = DexCollectionId.New(), Name = "Written elsewhere " + attempts };
                SomebodyElseWrites(document with { Collections = [.. document.Collections, other] });

                return document with { Collections = [Mine] };
            },
            attempts: 2);

        Assert.Equal(UpdateOutcome.Conflict, outcome);
        Assert.Equal(2, attempts);
        // Nothing of the caller's landed: the other writer's file is what is there.
        Assert.Equal(3, (await store.LoadAsync()).Document.Collections.Count);
    }

    [Fact]
    public async Task What_the_change_refuses_reaches_the_caller()
    {
        var store = new UserDataStore(_dataFile);
        await store.UpdateAsync(document => document with { Collections = [Mine] });

        // The guards in CollectionEditing throw, and that is how a screen learns why.
        await Assert.ThrowsAsync<InvalidOperationException>(
            () => store.UpdateAsync(document => document.Without(Collection)));
    }
}
