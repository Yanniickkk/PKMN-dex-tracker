using LivingDex.Core.Dex;
using LivingDex.Core.Reference;
using LivingDex.Core.UserData;

namespace LivingDex.Core.Tests.Dex;

public class DexFilterTests
{
    private static readonly DexCollectionId Mine = DexCollectionId.New();
    private static readonly GameId Platinum = new("platinum");
    private static readonly GameId Emerald = new("emerald");

    private static DexLine Line(string species, int number, string? name = null) =>
        new(DexTarget.ForSpecies(new SpeciesId(species)), number, name ?? species, FormKind: null);

    private static readonly DexLine Turtwig = Line("turtwig", 387, "Turtwig");
    private static readonly DexLine Chimchar = Line("chimchar", 390, "Chimchar");
    private static readonly DexLine Piplup = Line("piplup", 393, "Piplup");
    private static readonly DexLine[] Dex = [Turtwig, Chimchar, Piplup];

    /// <summary>Turtwig in Platinum, Chimchar in Emerald, Piplup nowhere.</summary>
    private static readonly CaptureIndex Captures = CaptureIndex.For(
        Mine,
        [
            CaptureRecord.CaughtIn(Mine, Turtwig.Target, Platinum, Platinum),
            CaptureRecord.CaughtIn(Mine, Chimchar.Target, Emerald, Platinum),
        ]);

    private static bool Everything(GameId game, DexTarget target) => true;

    private static bool Nothing(GameId game, DexTarget target) => false;

    /// <summary>Platinum can get Piplup, Emerald can get Chimchar, and neither has the third.</summary>
    private static bool OneEach(GameId game, DexTarget target) =>
        (game == Platinum && target == Piplup.Target)
        || (game == Emerald && target == Chimchar.Target);

    [Fact]
    public void An_empty_filter_returns_the_dex_untouched()
    {
        Assert.Same(Dex, DexFilter.None.Apply(Dex, Captures, Everything));
        Assert.True(DexFilter.None.IsEmpty);
    }

    [Fact]
    public void Still_to_catch_leaves_only_what_is_not_caught_anywhere()
    {
        var filter = new DexFilter { StillToCatch = true };

        Assert.Equal([Piplup], filter.Apply(Dex, Captures, Everything));
    }

    [Fact]
    public void Not_yet_transferred_leaves_only_what_is_waiting_in_another_game()
    {
        var filter = new DexFilter { NotYetTransferred = true };

        Assert.Equal([Chimchar], filter.Apply(Dex, Captures, Everything));
    }

    [Fact]
    public void Both_status_switches_together_mean_everything_not_done()
    {
        // They widen rather than narrow: an entry cannot be both, so reading them as "and"
        // would always return nothing.
        var filter = new DexFilter { StillToCatch = true, NotYetTransferred = true };

        Assert.Equal([Chimchar, Piplup], filter.Apply(Dex, Captures, Everything));
    }

    [Fact]
    public void Availability_narrows_rather_than_widens()
    {
        var onlyPiplup = new DexFilter { AvailableIn = [Platinum] };

        Assert.Equal(
            [Piplup],
            onlyPiplup.Apply(Dex, Captures, (_, target) => target == Piplup.Target));
        Assert.Empty(onlyPiplup.Apply(Dex, Captures, Nothing));
    }

    [Fact]
    public void One_game_asks_about_that_game_and_no_other()
    {
        // The collection covers both, and the question is about one of them at a time.
        Assert.Equal([Piplup], new DexFilter { AvailableIn = [Platinum] }.Apply(Dex, Captures, OneEach));
        Assert.Equal([Chimchar], new DexFilter { AvailableIn = [Emerald] }.Apply(Dex, Captures, OneEach));
    }

    [Fact]
    public void Several_games_widen_each_other()
    {
        // "What can I get out of either of these" - an entry passes when any ticked game has it,
        // the same way the two status switches widen rather than narrow.
        var either = new DexFilter { AvailableIn = [Platinum, Emerald] };

        Assert.Equal([Chimchar, Piplup], either.Apply(Dex, Captures, OneEach));
    }

    [Fact]
    public void No_game_ticked_asks_nothing_about_availability()
    {
        // Not "show nothing": the question simply is not being asked.
        var filter = new DexFilter { AvailableIn = [] };

        Assert.True(filter.IsEmpty);
        Assert.Same(Dex, filter.Apply(Dex, Captures, Nothing));
    }

    [Fact]
    public void A_search_and_a_switch_both_have_to_pass()
    {
        var filter = new DexFilter { Search = "chim", StillToCatch = true };

        // Chimchar matches the text but is already caught, so nothing is left.
        Assert.Empty(filter.Apply(Dex, Captures, Everything));
    }

    [Fact]
    public void The_search_ignores_case_and_matches_anywhere_in_the_name()
    {
        var filter = new DexFilter { Search = "TWIG" };

        Assert.Equal([Turtwig], filter.Apply(Dex, Captures, Everything));
    }

    [Fact]
    public void The_search_ignores_accents_in_both_directions()
    {
        var flabebe = Line("flabebe", 669, "Flabébé");
        DexLine[] dex = [flabebe];

        Assert.Equal([flabebe], new DexFilter { Search = "flabebe" }.Apply(dex, CaptureIndex.Empty, Everything));
        Assert.Equal([flabebe], new DexFilter { Search = "flabébé" }.Apply(dex, CaptureIndex.Empty, Everything));
    }

    [Fact]
    public void Folding_maps_every_accent_it_knows_to_one_plain_letter()
    {
        // The two tables are paired by position. A letter added to one and not the other would
        // silently shift every mapping after it, so the lengths are pinned here.
        Assert.Equal("e", DexFilter.Fold("é"));
        Assert.Equal("aaaaaaceeeeiiiinooooouuuuyy", DexFilter.Fold(
            "ÀÁÂÃÄÅÇÈÉÊË"
            + "ÌÍÎÏÑÒÓÔÕÖÙÚÛÜÝŸ"));
    }

    [Fact]
    public void A_name_the_id_spells_differently_is_still_found()
    {
        var farfetchd = new DexLine(
            DexTarget.ForSpecies(new SpeciesId("farfetchd")),
            83,
            "Farfetch'd",
            FormKind: null);

        Assert.Equal([farfetchd], new DexFilter { Search = "farfetchd" }.Apply([farfetchd], CaptureIndex.Empty, Everything));
        Assert.Equal([farfetchd], new DexFilter { Search = "fetch'd" }.Apply([farfetchd], CaptureIndex.Empty, Everything));
    }

    [Fact]
    public void A_form_is_found_by_its_form_name_as_well_as_the_species()
    {
        var alolan = new DexLine(
            DexTarget.ForForm(new SpeciesId("vulpix"), new FormId("vulpix-alola")),
            37,
            "Vulpix (Alolan)",
            FormKind.Regional);

        Assert.Equal(
            [alolan],
            new DexFilter { Search = "alolan" }.Apply([alolan], CaptureIndex.Empty, Everything));
    }

    [Fact]
    public void Whitespace_is_not_a_search()
    {
        var filter = new DexFilter { Search = "   " };

        Assert.True(filter.IsEmpty);
        Assert.Equal(3, filter.Apply(Dex, Captures, Everything).Count);
    }

    [Fact]
    public void A_search_that_matches_nothing_returns_nothing_rather_than_everything()
    {
        Assert.Empty(new DexFilter { Search = "mew" }.Apply(Dex, Captures, Everything));
    }
}
