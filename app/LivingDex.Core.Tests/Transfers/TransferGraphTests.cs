using LivingDex.Core.Reference;
using LivingDex.Core.Transfers;

namespace LivingDex.Core.Tests.Transfers;

public class TransferGraphTests
{
    private static readonly GameId Red = new("red");
    private static readonly GameId Gold = new("gold");
    private static readonly GameId Crystal = new("crystal");
    private static readonly GameId Ruby = new("ruby");
    private static readonly GameId Sapphire = new("sapphire");
    private static readonly GameId Emerald = new("emerald");
    private static readonly GameId FireRed = new("firered");
    private static readonly GameId Diamond = new("diamond");
    private static readonly GameId Pearl = new("pearl");
    private static readonly GameId Platinum = new("platinum");
    private static readonly GameId Black = new("black");
    private static readonly GameId Bank = new("bank");
    private static readonly GameId Home = new("home");
    private static readonly GameId Sword = new("sword");

    private static readonly SpeciesId Pikachu = new("pikachu");
    private static readonly SpeciesId Treecko = new("treecko");
    private static readonly SpeciesId Turtwig = new("turtwig");
    private static readonly SpeciesId Zacian = new("zacian");
    private static readonly SpeciesId Decidueye = new("decidueye");

    private static TransferEdge Trade(GameId left, GameId right) =>
        new(left, right, TransferMechanism.Trade, TransferDirection.BothWays, new AllSpeciesFilter());

    private static TransferGraph BuildGraph(int maxHops = TransferGraph.DefaultMaxHops)
    {
        TransferEdge[] edges =
        [
            // Within a generation, anything trades either way.
            new(Red, Gold, TransferMechanism.TimeCapsule, TransferDirection.BothWays, new NationalDexRangeFilter(1, 151)),
            Trade(Gold, Crystal),
            Trade(Ruby, Sapphire),
            Trade(Sapphire, Emerald),
            Trade(Emerald, FireRed),
            Trade(Diamond, Pearl),
            Trade(Pearl, Platinum),

            // Pal Park only goes forward, and only carries what existed in Generation 3.
            new(Emerald, Platinum, TransferMechanism.PalPark, TransferDirection.OneWay, new NationalDexRangeFilter(1, 386)),
            new(Emerald, Diamond, TransferMechanism.PalPark, TransferDirection.OneWay, new NationalDexRangeFilter(1, 386)),
            new(Ruby, Diamond, TransferMechanism.PalPark, TransferDirection.OneWay, new NationalDexRangeFilter(1, 386)),

            new(Platinum, Black, TransferMechanism.PokeTransfer, TransferDirection.OneWay, new NationalDexRangeFilter(1, 493)),
            new(Black, Bank, TransferMechanism.PokeTransporter, TransferDirection.OneWay, new AllSpeciesFilter()),
            new(Bank, Home, TransferMechanism.Home, TransferDirection.OneWay, new AllSpeciesFilter()),

            // HOME will only put something into a game whose dex has room for it.
            new(Home, Sword, TransferMechanism.Home, TransferDirection.BothWays, new PresentInTargetDexFilter()),
        ];

        Species[] species =
        [
            new(Pikachu, 25, "Pikachu", [PokemonType.Electric], new EvolutionChainId("pichu")),
            new(Treecko, 252, "Treecko", [PokemonType.Grass], new EvolutionChainId("treecko")),
            new(Turtwig, 387, "Turtwig", [PokemonType.Grass], new EvolutionChainId("turtwig")),
            new(Zacian, 888, "Zacian", [PokemonType.Fairy], new EvolutionChainId("zacian")),
            new(Decidueye, 724, "Decidueye", [PokemonType.Grass, PokemonType.Ghost], new EvolutionChainId("rowlet")),
        ];

        // Sword has its own dex. Decidueye is deliberately missing from it.
        DexEntry[] dexEntries =
        [
            new(Sword, DexTarget.ForSpecies(Pikachu), 194),
            new(Sword, DexTarget.ForSpecies(Zacian), 888),
            new(Home, DexTarget.ForSpecies(Pikachu), 25),
            new(Home, DexTarget.ForSpecies(Zacian), 888),
            new(Home, DexTarget.ForSpecies(Decidueye), 724),
        ];

        return new TransferGraph(edges, new ReferenceFilterContext(species, dexEntries), maxHops);
    }

    [Fact]
    public void The_graph_is_whatever_the_data_says_and_nothing_more()
    {
        var empty = new TransferGraph([], new ReferenceFilterContext([], []));

        Assert.Empty(empty.Games);
        Assert.Empty(empty.ReachableFrom(Platinum));
    }

    [Fact]
    public void Platinum_accepts_generation_3_and_4_only()
    {
        var reachable = BuildGraph().ReachableFrom(Platinum);

        Assert.Equal(
            [Diamond, Emerald, FireRed, Pearl, Ruby, Sapphire],
            reachable.Order(Comparer<GameId>.Create((left, right) => string.CompareOrdinal(left.Value, right.Value))));

        // Generation 2 and earlier never reach it, and neither does anything after Generation 4:
        // Poke Transfer and HOME only go forward.
        Assert.DoesNotContain(Gold, reachable);
        Assert.DoesNotContain(Crystal, reachable);
        Assert.DoesNotContain(Red, reachable);
        Assert.DoesNotContain(Black, reachable);
        Assert.DoesNotContain(Home, reachable);
    }

    [Fact]
    public void Generation_2_cannot_reach_generation_3()
    {
        var result = BuildGraph().RoutesBetween(Gold, Emerald, Pikachu);

        Assert.False(result.Any);
        Assert.Equal(NoRouteReason.NotConnected, result.Reason);
        Assert.Contains("gold", result.Explanation, StringComparison.Ordinal);
        Assert.Contains("emerald", result.Explanation, StringComparison.Ordinal);
    }

    [Fact]
    public void Home_refuses_a_species_the_target_dex_has_no_entry_for()
    {
        var graph = BuildGraph();

        var accepted = graph.RoutesBetween(Home, Sword, Zacian);
        var refused = graph.RoutesBetween(Home, Sword, Decidueye);

        Assert.True(accepted.Any);
        Assert.False(refused.Any);
        Assert.Equal(NoRouteReason.SpeciesNotCarried, refused.Reason);
        Assert.Contains("no dex entry", refused.Explanation, StringComparison.Ordinal);
    }

    [Fact]
    public void A_species_that_did_not_exist_yet_cannot_come_forward_through_pal_park()
    {
        var graph = BuildGraph();

        // Treecko is National Dex 252 and travels; Turtwig is 387 and is outside what Pal Park
        // carries, which is the point of the range filter.
        Assert.True(graph.RoutesBetween(Emerald, Platinum, Treecko).Any);

        var refused = graph.RoutesBetween(Emerald, Platinum, Turtwig);

        Assert.Equal(NoRouteReason.SpeciesNotCarried, refused.Reason);
        Assert.Contains("National Dex 1 to 386", refused.Explanation, StringComparison.Ordinal);
    }

    [Fact]
    public void The_shortest_route_comes_first_and_the_rest_are_alternatives()
    {
        var result = BuildGraph().RoutesBetween(Emerald, Platinum, Treecko);

        Assert.True(result.Any);
        Assert.NotNull(result.Shortest);

        // Pal Park straight into Platinum, rather than via Diamond and Pearl.
        Assert.Equal(1, result.Shortest.Length);
        Assert.Equal(TransferMechanism.PalPark, result.Shortest.Hops[0].Mechanism);

        Assert.All(
            result.Routes.Zip(result.Routes.Skip(1)),
            pair => Assert.True(pair.First.Length <= pair.Second.Length));
        Assert.NotEmpty(result.Alternatives);
    }

    [Fact]
    public void A_route_is_a_chain_where_each_hop_starts_where_the_last_one_ended()
    {
        var result = BuildGraph().RoutesBetween(Ruby, Black, Treecko);

        Assert.True(result.Any);

        var route = result.Shortest!;
        Assert.Equal(Ruby, route.From);
        Assert.Equal(Black, route.To);
        Assert.All(
            route.Hops.Zip(route.Hops.Skip(1)),
            pair => Assert.Equal(pair.First.To, pair.Second.From));
    }

    [Fact]
    public void The_filter_is_applied_at_every_hop_not_just_the_first()
    {
        // Ruby to Black is fine for Treecko, but Turtwig fails at the Pal Park hop in the middle
        // rather than at the Poke Transfer hop that would have accepted it.
        var refused = BuildGraph().RoutesBetween(Ruby, Black, Turtwig);

        Assert.Equal(NoRouteReason.SpeciesNotCarried, refused.Reason);
        Assert.Contains("PalPark", refused.Explanation, StringComparison.Ordinal);
    }

    [Fact]
    public void Transferring_into_the_game_it_is_already_in_is_not_an_error_worth_a_route()
    {
        var result = BuildGraph().RoutesBetween(Platinum, Platinum, Pikachu);

        Assert.False(result.Any);
        Assert.Equal(NoRouteReason.SameGame, result.Reason);
    }

    [Fact]
    public void A_game_the_dataset_has_never_heard_of_says_so()
    {
        var result = BuildGraph().RoutesBetween(new GameId("legends-z-a"), Platinum, Pikachu);

        Assert.Equal(NoRouteReason.UnknownGame, result.Reason);
        Assert.Contains("legends-z-a", result.Explanation, StringComparison.Ordinal);
    }

    [Fact]
    public void A_route_longer_than_the_search_allows_is_reported_as_such_not_as_disconnected()
    {
        // Ruby has no Pal Park of its own into Platinum, so the way forward is
        // Ruby -> Diamond -> Pearl -> Platinum -> Black -> Bank -> Home: six hops.
        var full = BuildGraph(maxHops: 6).RoutesBetween(Ruby, Home, Treecko);
        Assert.True(full.Any);
        Assert.Equal(6, full.Shortest!.Length);

        var cut = BuildGraph(maxHops: 4).RoutesBetween(Ruby, Home, Treecko);

        Assert.False(cut.Any);
        Assert.Equal(NoRouteReason.TooManyHops, cut.Reason);
    }

    [Fact]
    public void A_one_way_edge_is_not_quietly_usable_in_reverse()
    {
        var graph = BuildGraph();

        Assert.True(graph.RoutesBetween(Emerald, Platinum, Treecko).Any);

        var backwards = graph.RoutesBetween(Platinum, Emerald, Treecko);

        Assert.False(backwards.Any);
        Assert.Equal(NoRouteReason.NotConnected, backwards.Reason);
    }

    [Fact]
    public void A_both_ways_edge_works_in_both_directions()
    {
        var graph = BuildGraph();

        Assert.True(graph.RoutesBetween(Home, Sword, Zacian).Any);
        Assert.True(graph.RoutesBetween(Sword, Home, Zacian).Any);
    }
}
