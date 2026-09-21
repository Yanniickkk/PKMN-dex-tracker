using LivingDex.Core.Dex;
using LivingDex.Core.Reference;
using LivingDex.Core.UserData;

namespace LivingDex.Core.Tests.Dex;

public class DexProgressTests
{
    private static readonly DexCollectionId Mine = DexCollectionId.New();
    private static readonly GameId Platinum = new("platinum");
    private static readonly GameId Emerald = new("emerald");

    private static DexLine Line(string species, int number) =>
        new(DexTarget.ForSpecies(new SpeciesId(species)), number, species, FormKind: null);

    private static readonly DexLine[] ThreeLines =
    [
        Line("turtwig", 387),
        Line("chimchar", 390),
        Line("piplup", 393),
    ];

    [Fact]
    public void A_fresh_collection_has_everything_still_to_do()
    {
        var progress = DexProgress.Of(ThreeLines, CaptureIndex.Empty);

        Assert.Equal(3, progress.Total);
        Assert.Equal(0, progress.InMainGame);
        Assert.Equal(0, progress.CaughtElsewhere);
        Assert.Equal(3, progress.NotCaught);
        Assert.Equal(0, progress.PercentComplete);
        Assert.False(progress.IsComplete);
    }

    [Fact]
    public void The_two_caught_states_are_counted_apart()
    {
        var captures = CaptureIndex.For(
            Mine,
            [
                CaptureRecord.CaughtIn(Mine, ThreeLines[0].Target, Platinum, Platinum),
                CaptureRecord.CaughtIn(Mine, ThreeLines[1].Target, Emerald, Platinum),
            ]);

        var progress = DexProgress.Of(ThreeLines, captures);

        Assert.Equal(1, progress.InMainGame);
        Assert.Equal(1, progress.CaughtElsewhere);
        Assert.Equal(1, progress.NotCaught);
        Assert.Equal(2, progress.Caught);
    }

    [Fact]
    public void A_record_for_something_outside_this_dex_is_not_counted()
    {
        // The player switched a form off, or changed the main game. The record stays in the
        // file, but it is not part of what this dex asks for.
        var captures = CaptureIndex.For(
            Mine,
            [
                CaptureRecord.CaughtIn(Mine, ThreeLines[0].Target, Platinum, Platinum),
                CaptureRecord.CaughtIn(Mine, DexTarget.ForSpecies(new SpeciesId("mew")), Platinum, Platinum),
            ]);

        var progress = DexProgress.Of(ThreeLines, captures);

        Assert.Equal(3, progress.Total);
        Assert.Equal(1, progress.InMainGame);
    }

    [Fact]
    public void Everything_in_the_main_game_is_complete()
    {
        var captures = CaptureIndex.For(
            Mine,
            [.. ThreeLines.Select(line => CaptureRecord.CaughtIn(Mine, line.Target, Platinum, Platinum))]);

        var progress = DexProgress.Of(ThreeLines, captures);

        Assert.True(progress.IsComplete);
        Assert.Equal(100, progress.PercentComplete);
        Assert.Equal(0, progress.NotCaught);
    }

    [Fact]
    public void Caught_everywhere_but_not_home_yet_is_not_complete()
    {
        var captures = CaptureIndex.For(
            Mine,
            [.. ThreeLines.Select(line => CaptureRecord.CaughtIn(Mine, line.Target, Emerald, Platinum))]);

        var progress = DexProgress.Of(ThreeLines, captures);

        Assert.False(progress.IsComplete);
        Assert.Equal(0, progress.PercentComplete);
        Assert.Equal(100, progress.PercentCaught);
    }

    [Fact]
    public void The_last_missing_entry_never_rounds_away()
    {
        var progress = new DexProgress(Total: 1025, InMainGame: 1024, CaughtElsewhere: 1);

        Assert.Equal(99, progress.PercentComplete);
        Assert.False(progress.IsComplete);
    }

    [Fact]
    public void The_first_entry_done_never_rounds_away_either()
    {
        var progress = new DexProgress(Total: 1025, InMainGame: 1, CaughtElsewhere: 0);

        Assert.Equal(1, progress.PercentComplete);
    }

    [Fact]
    public void An_empty_dex_is_zero_rather_than_a_division_by_zero()
    {
        var progress = DexProgress.Of([], CaptureIndex.Empty);

        Assert.Equal(0, progress.Total);
        Assert.Equal(0, progress.PercentComplete);
        Assert.False(progress.IsComplete);
    }
}
