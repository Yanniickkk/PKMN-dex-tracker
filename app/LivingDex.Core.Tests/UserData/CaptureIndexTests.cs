using LivingDex.Core.Reference;
using LivingDex.Core.UserData;

namespace LivingDex.Core.Tests.UserData;

public class CaptureIndexTests
{
    private static readonly DexCollectionId Mine = DexCollectionId.New();
    private static readonly DexCollectionId Someone = DexCollectionId.New();
    private static readonly GameId Platinum = new("platinum");
    private static readonly GameId Emerald = new("emerald");
    private static readonly DexTarget Chimchar = DexTarget.ForSpecies(new SpeciesId("chimchar"));
    private static readonly DexTarget Turtwig = DexTarget.ForSpecies(new SpeciesId("turtwig"));

    [Fact]
    public void An_entry_with_no_record_counts_as_not_caught()
    {
        var index = CaptureIndex.For(Mine, []);

        Assert.Equal(CaptureStatus.NotCaught, index.StatusOf(Chimchar));
        Assert.Null(index.RecordFor(Chimchar));
    }

    [Fact]
    public void Each_of_the_three_states_is_reported_back()
    {
        var index = CaptureIndex.For(
            Mine,
            [
                CaptureRecord.NotCaught(Mine, Turtwig),
                CaptureRecord.CaughtIn(Mine, Chimchar, Emerald, Platinum),
            ]);

        Assert.Equal(CaptureStatus.NotCaught, index.StatusOf(Turtwig));
        Assert.Equal(CaptureStatus.CaughtElsewhere, index.StatusOf(Chimchar));
        Assert.Equal(
            CaptureStatus.InMainGame,
            CaptureIndex
                .For(Mine, [CaptureRecord.CaughtIn(Mine, Chimchar, Platinum, Platinum)])
                .StatusOf(Chimchar));
    }

    [Fact]
    public void Records_of_another_collection_are_not_visible()
    {
        var index = CaptureIndex.For(
            Mine,
            [CaptureRecord.CaughtIn(Someone, Chimchar, Platinum, Platinum)]);

        Assert.Equal(CaptureStatus.NotCaught, index.StatusOf(Chimchar));
        Assert.Equal(0, index.Count);
    }

    [Fact]
    public void A_form_is_kept_apart_from_its_base_species()
    {
        var vulpix = new SpeciesId("vulpix");
        var alolan = DexTarget.ForForm(vulpix, new FormId("vulpix-alola"));

        var index = CaptureIndex.For(
            Mine,
            [CaptureRecord.CaughtIn(Mine, alolan, Platinum, Platinum)]);

        Assert.Equal(CaptureStatus.InMainGame, index.StatusOf(alolan));
        Assert.Equal(CaptureStatus.NotCaught, index.StatusOf(DexTarget.ForSpecies(vulpix)));
    }

    [Fact]
    public void Two_records_for_one_entry_leave_the_later_one_standing()
    {
        // A hand-edited file can contain this. Whatever it does, it must not throw halfway
        // through building a grid.
        var index = CaptureIndex.For(
            Mine,
            [
                CaptureRecord.NotCaught(Mine, Chimchar),
                CaptureRecord.CaughtIn(Mine, Chimchar, Platinum, Platinum),
            ]);

        Assert.Equal(CaptureStatus.InMainGame, index.StatusOf(Chimchar));
        Assert.Equal(1, index.Count);
    }

    [Fact]
    public void The_record_behind_a_status_is_available_for_the_detail_view()
    {
        var caught = new DateOnly(2026, 3, 4);
        var index = CaptureIndex.For(
            Mine,
            [CaptureRecord.CaughtIn(Mine, Chimchar, Emerald, Platinum, caught, "traded from a friend")]);

        var record = index.RecordFor(Chimchar);

        Assert.NotNull(record);
        Assert.Equal(Emerald, record.HoldingGame);
        Assert.Equal(caught, record.CaughtOn);
        Assert.Equal("traded from a friend", record.Note);
    }
}

public class CaptureStatusNamesTests
{
    [Fact]
    public void An_entry_in_the_main_game_names_that_game()
    {
        Assert.Equal("In Platinum", CaptureStatusNames.Of(CaptureStatus.InMainGame, "Platinum"));
    }

    [Fact]
    public void An_entry_elsewhere_names_where_it_is_and_what_is_left_to_do()
    {
        Assert.Equal(
            "In Emerald, still to transfer",
            CaptureStatusNames.Of(CaptureStatus.CaughtElsewhere, "Platinum", "Emerald"));
    }

    [Fact]
    public void An_entry_elsewhere_with_no_game_recorded_still_reads_as_a_sentence()
    {
        // A hand-edited file can say caughtElsewhere without a holding game.
        Assert.Equal(
            "Caught, still to transfer",
            CaptureStatusNames.Of(CaptureStatus.CaughtElsewhere, "Platinum", holdingGameName: null));
    }

    [Fact]
    public void A_missing_entry_says_so_without_naming_a_game()
    {
        Assert.Equal("Not caught", CaptureStatusNames.Of(CaptureStatus.NotCaught, "Platinum"));
    }
}
