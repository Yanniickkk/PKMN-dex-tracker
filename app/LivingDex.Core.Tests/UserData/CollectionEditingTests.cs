using LivingDex.Core.Reference;
using LivingDex.Core.UserData;

namespace LivingDex.Core.Tests.UserData;

public class CollectionEditingTests
{
    private static readonly GameId Platinum = new("platinum");
    private static readonly GameId Emerald = new("emerald");
    private static readonly GameId FireRed = new("firered");
    private static readonly DexTarget Chimchar = DexTarget.ForSpecies(new SpeciesId("chimchar"));
    private static readonly DexTarget Torchic = DexTarget.ForSpecies(new SpeciesId("torchic"));
    private static readonly DateOnly Today = new(2026, 9, 26);

    private static DexCollection Mine { get; } = new(
        DexCollectionId.New(),
        "Platinum living dex",
        Platinum,
        [Emerald],
        FormSelection.Default);

    private static UserDataDocument Document(params CaptureRecord[] records) =>
        UserDataDocument.Empty with { Collections = [Mine], Records = records };

    [Fact]
    public void A_collection_is_found_by_its_id_and_a_stranger_is_not()
    {
        var document = Document();

        Assert.Equal(Mine, document.CollectionWith(Mine.Id));
        Assert.Null(document.CollectionWith(DexCollectionId.New()));
    }

    [Fact]
    public void A_new_collection_is_in_use_and_not_in_the_archive()
    {
        var document = Document();

        Assert.Single(document.InUse());
        Assert.Empty(document.ArchivedCollections());
        Assert.False(Mine.IsArchived);
    }

    [Fact]
    public void Archiving_moves_it_across_and_keeps_every_record()
    {
        var document = Document(CaptureRecord.CaughtIn(Mine.Id, Chimchar, Platinum, Platinum));

        var archived = document.Archived(Mine.Id, Today);

        Assert.Empty(archived.InUse());
        Assert.Equal(Today, Assert.Single(archived.ArchivedCollections()).ArchivedOn);
        Assert.Single(archived.Records);
    }

    [Fact]
    public void Archiving_twice_keeps_the_day_it_was_first_put_away()
    {
        var archived = Document().Archived(Mine.Id, Today);

        var again = archived.Archived(Mine.Id, Today.AddDays(30));

        Assert.Equal(Today, Assert.Single(again.Collections).ArchivedOn);
    }

    [Fact]
    public void Restoring_puts_it_back_in_use()
    {
        var document = Document().Archived(Mine.Id, Today).Restored(Mine.Id);

        Assert.Single(document.InUse());
        Assert.Empty(document.ArchivedCollections());
    }

    [Fact]
    public void The_archive_reads_newest_first()
    {
        var older = Mine with { Id = DexCollectionId.New(), Name = "Older", ArchivedOn = Today.AddDays(-10) };
        var newer = Mine with { Id = DexCollectionId.New(), Name = "Newer", ArchivedOn = Today };
        var document = UserDataDocument.Empty with { Collections = [older, newer] };

        Assert.Equal(["Newer", "Older"], document.ArchivedCollections().Select(one => one.Name));
    }

    [Fact]
    public void Deleting_takes_the_records_with_it()
    {
        var other = DexCollectionId.New();
        var document = Document(
            CaptureRecord.CaughtIn(Mine.Id, Chimchar, Platinum, Platinum),
            CaptureRecord.CaughtIn(other, Torchic, Emerald, Emerald));

        var left = document.Archived(Mine.Id, Today).Without(Mine.Id);

        Assert.Empty(left.Collections);
        Assert.Equal(other, Assert.Single(left.Records).Collection);
    }

    [Fact]
    public void A_collection_in_use_cannot_be_deleted()
    {
        var document = Document();

        var refused = Assert.Throws<InvalidOperationException>(() => document.Without(Mine.Id));

        Assert.Contains("archived", refused.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void Deleting_something_that_is_not_there_says_so()
    {
        Assert.Throws<ArgumentException>(() => Document().Without(DexCollectionId.New()));
    }

    [Fact]
    public void Records_are_counted_per_collection()
    {
        var document = Document(
            CaptureRecord.CaughtIn(Mine.Id, Chimchar, Platinum, Platinum),
            CaptureRecord.CaughtIn(DexCollectionId.New(), Torchic, Emerald, Emerald));

        Assert.Equal(1, document.RecordCountOf(Mine.Id));
    }

    [Fact]
    public void What_a_game_still_holds_counts_only_this_collection_and_only_what_is_caught()
    {
        var elsewhere = DexCollectionId.New();
        var document = Document(
            CaptureRecord.CaughtIn(Mine.Id, Chimchar, Emerald, Platinum),
            CaptureRecord.NotCaught(Mine.Id, Torchic) with { Note = "next" },
            CaptureRecord.CaughtIn(elsewhere, Torchic, Emerald, Platinum));

        var held = document.StillHeldIn(Mine.Id, Emerald);

        Assert.Equal(Chimchar, Assert.Single(held).Target);
        Assert.Empty(document.StillHeldIn(Mine.Id, FireRed));
    }

    [Fact]
    public void A_linked_game_holding_nothing_can_be_unlinked()
    {
        var document = Document(CaptureRecord.CaughtIn(Mine.Id, Chimchar, Platinum, Platinum));

        var saved = document.WithCollection(Mine with { LinkedGames = [] });

        Assert.Empty(Assert.Single(saved.Collections).LinkedGames);
    }

    [Fact]
    public void A_linked_game_still_holding_something_refuses_to_be_unlinked()
    {
        var document = Document(CaptureRecord.CaughtIn(Mine.Id, Chimchar, Emerald, Platinum));

        var refused = Assert.Throws<InvalidOperationException>(
            () => document.WithCollection(Mine with { LinkedGames = [] }));

        Assert.Contains("Transfer them first", refused.Message, StringComparison.Ordinal);
    }

    [Fact]
    public void Adding_a_linked_game_asks_nothing_of_the_records()
    {
        var document = Document(CaptureRecord.CaughtIn(Mine.Id, Chimchar, Emerald, Platinum));

        var saved = document.WithCollection(Mine with { LinkedGames = [Emerald, FireRed] });

        Assert.Equal(2, Assert.Single(saved.Collections).LinkedGames.Count);
    }

    [Fact]
    public void The_main_game_cannot_be_changed()
    {
        var refused = Assert.Throws<InvalidOperationException>(
            () => Document().WithCollection(Mine with { MainGame = Emerald }));

        Assert.Contains("main game cannot be changed", refused.Message, StringComparison.Ordinal);
    }

    [Fact]
    public void An_archived_collection_cannot_be_edited()
    {
        var document = Document().Archived(Mine.Id, Today);
        var stored = Assert.Single(document.Collections);

        var refused = Assert.Throws<InvalidOperationException>(
            () => document.WithCollection(stored with { Name = "Renamed" }));

        Assert.Contains("Restore it first", refused.Message, StringComparison.Ordinal);
    }

    [Fact]
    public void Archiving_is_not_an_edit()
    {
        var refused = Assert.Throws<InvalidOperationException>(
            () => Document().WithCollection(Mine with { ArchivedOn = Today }));

        Assert.Contains("Archiving is not an edit", refused.Message, StringComparison.Ordinal);
    }

    [Fact]
    public void Saving_a_collection_the_file_does_not_have_says_so()
    {
        var stranger = Mine with { Id = DexCollectionId.New() };

        Assert.Throws<ArgumentException>(() => Document().WithCollection(stranger));
    }

    [Fact]
    public void A_game_no_longer_listed_but_still_holding_something_is_reported()
    {
        // What a hand-edited file, or an older build, can leave behind. Nothing in the app
        // produces it, which is exactly why it is worth being able to see.
        var document = Document(CaptureRecord.CaughtIn(Mine.Id, Chimchar, FireRed, Platinum));

        Assert.Equal([FireRed], document.GamesLeftHolding(Mine));
        Assert.Empty(document.GamesLeftHolding(Mine with { LinkedGames = [Emerald, FireRed] }));
    }
}
