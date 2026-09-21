using LivingDex.Core.Reference;
using LivingDex.Core.UserData;

namespace LivingDex.Core.Tests.UserData;

public class CaptureEditingTests
{
    private static readonly DexCollectionId Mine = DexCollectionId.New();
    private static readonly DexCollectionId Other = DexCollectionId.New();
    private static readonly GameId Platinum = new("platinum");
    private static readonly GameId Emerald = new("emerald");
    private static readonly DexTarget Chimchar = DexTarget.ForSpecies(new SpeciesId("chimchar"));
    private static readonly DexTarget Turtwig = DexTarget.ForSpecies(new SpeciesId("turtwig"));

    private static UserDataDocument Document(params CaptureRecord[] records) =>
        UserDataDocument.Empty with { Records = records };

    private static readonly DateOnly Today = new(2026, 9, 21);

    [Fact]
    public void Catching_something_dates_it_today()
    {
        var record = CaptureRecord.NotCaught(Mine, Chimchar)
            .WithStatus(CaptureStatus.InMainGame, Platinum, Emerald, Today);

        Assert.Equal(CaptureStatus.InMainGame, record.Status);
        Assert.Equal(Platinum, record.HoldingGame);
        Assert.Equal(Today, record.CaughtOn);
    }

    [Fact]
    public void A_date_already_recorded_is_not_overwritten_by_today()
    {
        var caught = new DateOnly(2020, 1, 2);
        var record = (CaptureRecord.NotCaught(Mine, Chimchar) with { CaughtOn = caught })
            .WithStatus(CaptureStatus.CaughtElsewhere, Platinum, Emerald, Today);

        Assert.Equal(caught, record.CaughtOn);
    }

    [Fact]
    public void Going_back_to_not_caught_keeps_the_date_and_drops_the_game()
    {
        var record = CaptureRecord.CaughtIn(Mine, Chimchar, Emerald, Platinum, Today)
            .WithStatus(CaptureStatus.NotCaught, Platinum, Emerald, Today);

        Assert.Equal(CaptureStatus.NotCaught, record.Status);
        Assert.Null(record.HoldingGame);
        Assert.Equal(Today, record.CaughtOn);
    }

    [Fact]
    public void Moving_elsewhere_keeps_the_game_it_is_already_in()
    {
        var sapphire = new GameId("sapphire");
        var record = CaptureRecord.CaughtIn(Mine, Chimchar, sapphire, Platinum)
            .WithStatus(CaptureStatus.CaughtElsewhere, Platinum, Emerald, Today);

        Assert.Equal(sapphire, record.HoldingGame);
    }

    [Fact]
    public void Moving_out_of_the_main_game_does_not_claim_it_is_still_there()
    {
        var record = CaptureRecord.CaughtIn(Mine, Chimchar, Platinum, Platinum)
            .WithStatus(CaptureStatus.CaughtElsewhere, Platinum, Emerald, Today);

        Assert.Equal(Emerald, record.HoldingGame);
    }

    [Fact]
    public void Elsewhere_with_nowhere_to_go_leaves_the_record_alone()
    {
        // A collection with no linked games. The screen disables the button; this is the
        // belt to that braces.
        var caught = CaptureRecord.CaughtIn(Mine, Chimchar, Platinum, Platinum);

        var record = caught.WithStatus(CaptureStatus.CaughtElsewhere, Platinum, null, Today);

        Assert.Equal(caught, record);
    }

    [Fact]
    public void A_first_record_is_added()
    {
        var caught = CaptureRecord.CaughtIn(Mine, Chimchar, Platinum, Platinum);

        var document = Document().WithRecord(caught);

        Assert.Equal([caught], document.Records);
    }

    [Fact]
    public void A_second_record_for_one_entry_replaces_the_first()
    {
        var document = Document(CaptureRecord.CaughtIn(Mine, Chimchar, Emerald, Platinum))
            .WithRecord(CaptureRecord.CaughtIn(Mine, Chimchar, Platinum, Platinum));

        var only = Assert.Single(document.Records);
        Assert.Equal(CaptureStatus.InMainGame, only.Status);
    }

    [Fact]
    public void Other_entries_and_other_collections_are_left_alone()
    {
        var elsewhere = CaptureRecord.CaughtIn(Mine, Turtwig, Emerald, Platinum);
        var someone = CaptureRecord.CaughtIn(Other, Chimchar, Platinum, Platinum);

        var document = Document(elsewhere, someone)
            .WithRecord(CaptureRecord.CaughtIn(Mine, Chimchar, Platinum, Platinum));

        Assert.Equal(3, document.Records.Count);
        Assert.Contains(elsewhere, document.Records);
        Assert.Contains(someone, document.Records);
    }

    [Fact]
    public void A_record_that_says_nothing_is_removed_rather_than_stored()
    {
        // Clicking a tile and unclicking it should leave the file as it was.
        var document = Document(CaptureRecord.CaughtIn(Mine, Chimchar, Platinum, Platinum))
            .WithRecord(CaptureRecord.NotCaught(Mine, Chimchar));

        Assert.Empty(document.Records);
    }

    [Fact]
    public void Not_caught_is_kept_when_it_still_carries_a_note_or_a_date()
    {
        var kept = CaptureRecord.NotCaught(Mine, Chimchar) with { Note = "seen it in the wild once" };

        var document = Document().WithRecord(kept);

        Assert.Equal([kept], document.Records);
    }

    [Fact]
    public void Duplicates_for_one_entry_collapse_into_the_record_being_written()
    {
        // A hand-edited file can hold two. Writing to that entry tidies it up.
        var document = Document(
                CaptureRecord.CaughtIn(Mine, Chimchar, Emerald, Platinum),
                CaptureRecord.CaughtIn(Mine, Chimchar, Platinum, Platinum))
            .WithRecord(CaptureRecord.CaughtIn(Mine, Chimchar, Emerald, Platinum));

        var only = Assert.Single(document.Records);
        Assert.Equal(Emerald, only.HoldingGame);
    }

    [Fact]
    public void The_record_for_an_entry_is_found_by_collection_and_target_together()
    {
        var mine = CaptureRecord.CaughtIn(Mine, Chimchar, Platinum, Platinum);
        var document = Document(CaptureRecord.CaughtIn(Other, Chimchar, Emerald, Emerald), mine);

        Assert.Equal(mine, document.RecordFor(Mine, Chimchar));
        Assert.Null(document.RecordFor(Mine, Turtwig));
    }
}
