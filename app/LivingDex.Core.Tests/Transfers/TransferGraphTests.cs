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
    private static readonly GameId X = new("x");
    private static readonly GameId Bank = new("bank");
    private static readonly GameId Home = new("home");
    private static readonly GameId Sword = new("sword");
    private static readonly GameId LetsGoPikachu = new("lets-go-pikachu");
    private static readonly GameId LetsGoEevee = new("lets-go-eevee");

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
            new(Red, Bank, TransferMechanism.PokeTransporter, TransferDirection.OneWay, new AllSpeciesFilter()),
            new(Bank, Home, TransferMechanism.Home, TransferDirection.OneWay, new AllSpeciesFilter()),

            // Bank's two halves. It takes anything X holds and hands back only what has never
            // been outside Generations 3 to 6, which is why they are two edges and not one.
            new(X, Bank, TransferMechanism.Bank, TransferDirection.OneWay, new AllSpeciesFilter()),
            new(Bank, X, TransferMechanism.Bank, TransferDirection.OneWay, new AllSpeciesFilter())
            {
                History = new HistoryWindow(3, 6),
            },

            // HOME will only put something into a game whose dex has room for it - and the
            // deposit is a separate edge, because that filter read backwards asks HOME.
            new(Sword, Home, TransferMechanism.Home, TransferDirection.OneWay, new AllSpeciesFilter()),
            new(Home, Sword, TransferMechanism.Home, TransferDirection.OneWay, new PresentInTargetDexFilter()),

            // The Let's Go pair: a cable between the halves, and HOME which takes anything and
            // hands back only what started in one of the two.
            Trade(LetsGoPikachu, LetsGoEevee),
            new(LetsGoPikachu, Home, TransferMechanism.Home, TransferDirection.OneWay, new AllSpeciesFilter()),
            new(Home, LetsGoPikachu, TransferMechanism.Home, TransferDirection.OneWay, new AllSpeciesFilter())
            {
                Origin = new OriginRequirement([LetsGoPikachu, LetsGoEevee]),
            },
            new(LetsGoEevee, Home, TransferMechanism.Home, TransferDirection.OneWay, new AllSpeciesFilter()),
            new(Home, LetsGoEevee, TransferMechanism.Home, TransferDirection.OneWay, new AllSpeciesFilter())
            {
                Origin = new OriginRequirement([LetsGoPikachu, LetsGoEevee]),
            },
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

        return new TransferGraph(edges, new ReferenceFilterContext(species, dexEntries, Games()), maxHops);
    }

    /// <summary>
    /// Which generation each of these belongs to, which is all a history window reads.
    /// </summary>
    /// <remarks>
    /// Bank is Generation 6, the generation it was built for. Nothing else about these entities
    /// matters here, so they are made with the same few fields rather than described properly.
    /// </remarks>
    private static IEnumerable<Game> Games()
    {
        (GameId Id, int Generation)[] all =
        [
            (Red, 1), (Gold, 2), (Crystal, 2),
            (Ruby, 3), (Sapphire, 3), (Emerald, 3), (FireRed, 3),
            (Diamond, 4), (Pearl, 4), (Platinum, 4),
            (Black, 5), (X, 6), (Bank, 6), (Home, 8), (Sword, 8),
            (LetsGoPikachu, 7), (LetsGoEevee, 7),
        ];

        return all.Select(one => new Game(
            one.Id,
            one.Id.Value,
            one.Id.Value,
            one.Generation,
            string.Empty,
            GameRelease.Cartridge,
            null,
            DexSource.GameDex,
            null));
    }

    [Fact]
    public void A_detour_that_asks_for_the_same_thing_is_not_another_way()
    {
        // Four cartridges that all trade with each other: Ruby to FireRed is one link cable, and
        // the other four routes are that same cable with a pointless stop on the way. The real
        // dataset has five of these, which is sixteen routes between the halves of a pair - and
        // a popup that offered fifteen of them as "other ways".
        var graph = new TransferGraph(
            [
                Trade(Ruby, Sapphire),
                Trade(Ruby, Emerald),
                Trade(Ruby, FireRed),
                Trade(Sapphire, Emerald),
                Trade(Sapphire, FireRed),
                Trade(Emerald, FireRed),
            ],
            new ReferenceFilterContext([], []));

        var result = graph.RoutesBetween(Ruby, FireRed, DexTarget.ForSpecies(Pikachu));

        // The graph still knows them all; what changes is what the popup is told to offer.
        Assert.Equal(5, result.Routes.Count);
        Assert.Empty(result.Alternatives);
        Assert.Equal(1, result.Shortest?.Length);
    }

    [Fact]
    public void A_route_that_asks_for_something_else_is_another_way()
    {
        // Pal Park straight in, or trade to the cartridge that has one first. Those are two
        // different things to do, so both are offered.
        var result = BuildGraph().RoutesBetween(Ruby, Platinum, DexTarget.ForSpecies(Treecko));

        var ways = result.Alternatives.Prepend(result.Shortest!).Select(TransferNames.Of).ToList();

        Assert.Equal(ways, ways.Distinct());
        Assert.Contains("Pal Park", string.Join(" | ", ways), StringComparison.Ordinal);
        Assert.Contains("trading", string.Join(" | ", ways), StringComparison.Ordinal);
    }

    [Fact]
    public void Two_ways_between_the_same_pair_of_games_are_two_routes()
    {
        // Parallel edges: one hop, two mechanisms. The popup offers the second as an
        // alternative, so they must not collapse into one.
        var graph = new TransferGraph(
            [
                new TransferEdge(Emerald, Platinum, TransferMechanism.PalPark, TransferDirection.OneWay, new AllSpeciesFilter()),
                new TransferEdge(Emerald, Platinum, TransferMechanism.Trade, TransferDirection.OneWay, new AllSpeciesFilter()),
            ],
            new ReferenceFilterContext([], []));

        var result = graph.RoutesBetween(Emerald, Platinum, DexTarget.ForSpecies(Pikachu));

        Assert.Equal(2, result.Routes.Count);
        Assert.Single(result.Alternatives);
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
    public void A_game_can_feed_another_even_when_it_cannot_send_everything_it_holds()
    {
        var graph = BuildGraph();

        // Turtwig cannot make the Pal Park hop, but Emerald is still a feeder for Platinum.
        Assert.Equal(NoRouteReason.SpeciesNotCarried, graph.RoutesBetween(Emerald, Platinum, Turtwig).Reason);
        Assert.True(graph.RoutesBetween(Emerald, Platinum).Any);
    }

    [Fact]
    public void The_game_level_question_gives_the_same_refusals_as_the_species_one()
    {
        var graph = BuildGraph();

        Assert.Equal(NoRouteReason.SameGame, graph.RoutesBetween(Platinum, Platinum).Reason);
        Assert.Equal(NoRouteReason.UnknownGame, graph.RoutesBetween(new GameId("legends-z-a"), Platinum).Reason);
        Assert.Equal(NoRouteReason.NotConnected, graph.RoutesBetween(Gold, Emerald).Reason);
        Assert.Equal(NoRouteReason.NotConnected, graph.RoutesBetween(Platinum, Emerald).Reason);
    }

    [Fact]
    public void The_game_level_question_still_reports_a_route_that_is_too_long()
    {
        var cut = BuildGraph(maxHops: 4).RoutesBetween(Ruby, Home);

        Assert.False(cut.Any);
        Assert.Equal(NoRouteReason.TooManyHops, cut.Reason);
    }

    [Fact]
    public void The_game_level_question_names_how_the_feed_would_happen()
    {
        var result = BuildGraph().RoutesBetween(Emerald, Platinum);

        Assert.Equal(TransferMechanism.PalPark, result.Shortest!.Hops[0].Mechanism);
    }

    [Fact]
    public void A_route_reads_as_something_a_player_would_recognise()
    {
        var graph = BuildGraph();

        Assert.Equal("Pal Park", TransferNames.Of(graph.RoutesBetween(Emerald, Platinum).Shortest!));

        // Ruby -> Diamond -> Pearl -> Platinum is Pal Park and then two trades, and two trades
        // in a row is still just trading.
        var viaDiamond = graph.RoutesBetween(Ruby, Platinum).Shortest!;
        Assert.Equal(3, viaDiamond.Length);
        Assert.Equal("Pal Park, then trading", TransferNames.Of(viaDiamond));
    }

    [Fact]
    public void A_both_ways_edge_works_in_both_directions()
    {
        var graph = BuildGraph();

        Assert.True(graph.RoutesBetween(Diamond, Pearl, Pikachu).Any);
        Assert.True(graph.RoutesBetween(Pearl, Diamond, Pikachu).Any);
    }

    [Fact]
    public void A_deposit_is_its_own_edge_because_the_target_dex_filter_read_backwards_asks_the_service()
    {
        // The trap this shape exists to avoid. A both-ways edge carries one filter in both
        // directions, and PresentInTargetDexFilter asks whether the game being transferred into
        // lists the species. Run backwards it asks HOME, which has no dex of its own, so a
        // single both-ways edge would refuse every deposit ever made.
        var graph = new TransferGraph(
            [new(Home, Sword, TransferMechanism.Home, TransferDirection.BothWays, new PresentInTargetDexFilter())],
            new ReferenceFilterContext(
                [new(Zacian, 888, "Zacian", [PokemonType.Fairy], new EvolutionChainId("zacian"))],
                [new(Sword, DexTarget.ForSpecies(Zacian), 888)],
                Games()));

        Assert.True(graph.RoutesBetween(Home, Sword, Zacian).Any);
        Assert.False(graph.RoutesBetween(Sword, Home, Zacian).Any);

        // Two one-way edges, which is what the pipeline writes, answer both questions.
        Assert.True(BuildGraph().RoutesBetween(Sword, Home, Zacian).Any);
    }

    [Fact]
    public void Bank_hands_back_what_it_took_from_generation_5_and_not_what_it_took_from_generation_1()
    {
        // The restriction that made a window necessary. Bank takes a Pokemon out of a Virtual
        // Console Red as readily as out of Black, and X can read only one of the two - so the
        // same two-hop shape is a route in one case and nothing at all in the other.
        var graph = BuildGraph();

        var fromBlack = graph.RoutesBetween(Black, X, DexTarget.ForSpecies(Treecko));
        var fromRed = graph.RoutesBetween(Red, X, DexTarget.ForSpecies(Pikachu));

        Assert.Equal([Black, Bank, X], fromBlack.Shortest!.Hops.Select(hop => hop.From).Append(X));
        Assert.False(fromRed.Any);
        Assert.Equal(NoRouteReason.NotConnected, fromRed.Reason);
    }

    [Fact]
    public void A_window_is_read_against_the_whole_route_rather_than_the_step_taking_it()
    {
        // Nothing on the Bank-to-X edge knows where a Pokemon came from, and that is the point:
        // the answer is in the three games behind it. Ruby reaches X the long way round - Pal
        // Park, the Poke Transfer, Transporter, Bank - and every one of those is inside the
        // window, so the route stands where Red's identical last two hops do not.
        var graph = BuildGraph();

        var route = graph.RoutesBetween(Ruby, X, DexTarget.ForSpecies(Treecko));

        Assert.True(route.Any);
        Assert.Equal([Ruby, Diamond, Pearl, Platinum, Black, Bank, X],
            route.Shortest!.Hops.Select(hop => hop.From).Append(X));
    }

    [Fact]
    public void A_window_refuses_a_route_even_when_no_species_was_named()
    {
        // The linked-game picker asks "could this game ever feed that one" and deliberately
        // ignores species filters, because a game can be a good feeder and still refuse some of
        // what lives in it. A window is not that kind of no: nothing whatever comes out of Bank
        // into X once it has been in a Virtual Console game, so it has to bite here too.
        var graph = BuildGraph();

        Assert.True(graph.RoutesBetween(Black, X).Any);
        Assert.False(graph.RoutesBetween(Red, X).Any);

        Assert.Contains(Black, graph.ReachableFrom(X));
        Assert.DoesNotContain(Red, graph.ReachableFrom(X));
    }

    [Fact]
    public void A_node_of_unknown_generation_is_refused_by_a_window_rather_than_waved_through()
    {
        // The same stance a range filter takes towards a species it cannot number. A graph built
        // without its games knows nothing about where anything has been, and a window that
        // cannot be checked is not a window that passes.
        var graph = new TransferGraph(
            [
                new(Black, Bank, TransferMechanism.PokeTransporter, TransferDirection.OneWay, new AllSpeciesFilter()),
                new(Bank, X, TransferMechanism.Bank, TransferDirection.OneWay, new AllSpeciesFilter())
                {
                    History = new HistoryWindow(3, 6),
                },
            ],
            new ReferenceFilterContext([], []));

        Assert.False(graph.RoutesBetween(Black, X).Any);
    }

    // --- where a Pokemon started, which only the Let's Go pair asks ---------------------------

    [Fact]
    public void Nothing_reaches_Lets_Go_from_a_game_it_did_not_start_in()
    {
        var graph = BuildGraph();

        // Red -> Bank -> HOME is a real route and HOME really does send into Let's Go. What it
        // sends is only what came out of Let's Go in the first place, so this Pikachu - which
        // HOME converted to Sword and Shield's format on the way in - has nowhere to go.
        var routes = graph.RoutesBetween(Red, LetsGoPikachu, Pikachu);

        Assert.False(routes.Any);
        Assert.Equal(NoRouteReason.NotConnected, routes.Reason);
        Assert.DoesNotContain(Red, graph.ReachableFrom(LetsGoPikachu));
    }

    [Fact]
    public void A_Pokemon_that_started_in_the_other_half_comes_back_through_HOME()
    {
        var graph = BuildGraph();

        // The pair counts as one origin, so this is a real route - and so is the cable, which
        // is the shorter of the two and comes first.
        var routes = graph.RoutesBetween(LetsGoEevee, LetsGoPikachu, Pikachu);

        Assert.True(routes.Any);
        Assert.Contains(
            routes.Routes,
            route => route.Hops.Any(hop => hop.To == Home));
    }

    [Fact]
    public void HOME_itself_is_not_an_origin_the_graph_can_vouch_for()
    {
        var graph = BuildGraph();

        // A Pokemon in a HOME box started somewhere, and nothing in this dataset records where.
        // Refusing is the same answer a history window gives when it cannot see the whole route.
        Assert.False(graph.RoutesBetween(Home, LetsGoPikachu, Pikachu).Any);
    }

    [Fact]
    public void An_origin_does_not_touch_the_edges_that_do_not_have_one()
    {
        var graph = BuildGraph();

        // The same HOME the Let's Go edges hang off still feeds Sword the way it always did.
        Assert.True(graph.RoutesBetween(Black, Sword, Pikachu).Any);
        Assert.Contains(Black, graph.ReachableFrom(Sword));
    }
}
