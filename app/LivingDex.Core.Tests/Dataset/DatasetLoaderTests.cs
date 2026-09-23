using LivingDex.Core.Dataset;
using LivingDex.Core.Dex;
using LivingDex.Core.Reference;
using LivingDex.Core.Transfers;
using LivingDex.Core.UserData;

namespace LivingDex.Core.Tests.Dataset;

/// <summary>
/// The loader, run against the pipeline's own sample dataset embedded in this test assembly the
/// same way the real one is embedded in the app.
/// </summary>
public class DatasetLoaderTests
{
    private static readonly LoadedDataset Loaded = DatasetLoader.Load(typeof(DatasetLoaderTests).Assembly);

    [Fact]
    public void An_assembly_with_no_dataset_loads_as_empty_rather_than_failing()
    {
        // LivingDex.Core itself carries no dataset; only the app and this test project do.
        var none = DatasetLoader.Load(typeof(DatasetLoader).Assembly);

        Assert.True(none.IsEmpty);
        Assert.Empty(none.Reference.Games);
    }

    [Fact]
    public void The_stamp_comes_back_so_the_app_can_say_which_data_it_is_showing()
    {
        Assert.False(Loaded.IsEmpty);
        Assert.Equal("0.1.0-sample", Loaded.Stamp.Version);
        Assert.Equal(new DateOnly(2026, 9, 21), Loaded.Stamp.BuiltOn);
    }

    [Fact]
    public void Every_game_in_the_index_is_loaded()
    {
        Assert.Equal(
            ["bank", "diamond", "emerald", "home", "pearl", "platinum", "shield", "sword"],
            Loaded.Reference.Games.Select(game => game.Id.Value).Order(StringComparer.Ordinal));
    }

    [Fact]
    public void Dex_entries_are_gathered_from_every_game_file()
    {
        var sword = Loaded.Reference.DexOf(new GameId("sword"));

        Assert.Equal(2, sword.Count);
        Assert.Contains(sword, entry => entry.Target.Form == new FormId("vulpix-alola"));
    }

    [Fact]
    public void The_shared_tables_come_along_too()
    {
        Assert.Equal(4, Loaded.Reference.Species.Count);
        Assert.Equal(2, Loaded.Reference.Forms.Count);
        Assert.Equal(2, Loaded.Reference.EvolutionRules.Count);
        Assert.Equal(7, Loaded.Reference.TransferEdges.Count);
    }

    [Fact]
    public void What_is_loaded_is_enough_to_build_a_dex()
    {
        var collection = new DexCollection(
            new DexCollectionId("test"),
            "Sample",
            new GameId("sword"),
            [],
            FormSelection.Default);

        var lines = new DexBuilder(Loaded.Reference).Build(collection);

        Assert.Equal(
            [DexTarget.ForSpecies(new SpeciesId("vulpix")), DexTarget.ForForm(new SpeciesId("vulpix"), new FormId("vulpix-alola"))],
            lines.Select(line => line.Target));
    }

    [Fact]
    public void The_transfer_graph_can_be_built_from_what_is_loaded()
    {
        var graph = new TransferGraph(
            Loaded.Reference.TransferEdges,
            new ReferenceFilterContext(
                Loaded.Reference.Species,
                Loaded.Reference.DexEntries,
                Loaded.Reference.Games));

        Assert.True(graph.RoutesBetween(new GameId("emerald"), new GameId("platinum")).Any);
        Assert.False(graph.RoutesBetween(new GameId("platinum"), new GameId("emerald")).Any);

        // The window the sample carries survives the loader, and the generations it is read
        // against come out of the game files beside it.
        var withdrawal = Loaded.Reference.TransferEdges
            .Single(edge => edge.Mechanism == TransferMechanism.Bank);

        Assert.Equal(new HistoryWindow(3, 6), withdrawal.History);
        Assert.Equal(6, Loaded.Reference.FindGame(new GameId("bank"))!.Generation);
        Assert.Contains(new GameId("bank"), graph.ReachableFrom(new GameId("platinum")));
    }
}
