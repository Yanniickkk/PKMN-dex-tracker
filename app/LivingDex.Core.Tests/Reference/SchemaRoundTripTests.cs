using System.Text.Json;
using LivingDex.Core.Dataset;
using LivingDex.Core.Reference;

namespace LivingDex.Core.Tests.Reference;

public class SchemaRoundTripTests
{
    private static readonly SourceCitation Citation = new(
        "bulbapedia",
        new Uri("https://bulbapedia.bulbagarden.net/wiki/Route_201"),
        new DateOnly(2026, 9, 21));

    private static T RoundTrip<T>(T value)
    {
        var json = JsonSerializer.Serialize(value, DatasetJson.Options);
        return JsonSerializer.Deserialize<T>(json, DatasetJson.Options)!;
    }

    private static JsonElement Serialize<T>(T value) =>
        JsonDocument.Parse(JsonSerializer.Serialize(value, DatasetJson.Options)).RootElement.Clone();

    [Fact]
    public void Ids_are_plain_strings_on_disk()
    {
        var entry = Serialize(new DexEntry(
            new GameId("platinum"),
            DexTarget.ForSpecies(new SpeciesId("chimchar")),
            4));

        Assert.Equal("platinum", entry.GetProperty("game").GetString());
        Assert.Equal("chimchar", entry.GetProperty("target").GetProperty("species").GetString());
    }

    [Fact]
    public void A_species_entry_carries_no_form()
    {
        var target = DexTarget.ForSpecies(new SpeciesId("chimchar"));

        Assert.False(target.IsForm);
        Assert.Equal(target, RoundTrip(target));
    }

    [Fact]
    public void Derived_state_is_not_written_to_disk()
    {
        var json = Serialize(DexTarget.ForSpecies(new SpeciesId("chimchar")));

        // IsForm is computed from Form; storing it would let a hand-edited file contradict itself.
        Assert.False(json.TryGetProperty("isForm", out _));
    }

    [Fact]
    public void An_acquisition_method_leads_with_what_it_is_and_ends_with_where_it_came_from()
    {
        var json = Serialize<AcquisitionMethod>(new GiftAcquisition
        {
            Game = new GameId("platinum"),
            Target = DexTarget.ForSpecies(new SpeciesId("chimchar")),
            Source = Citation,
            GiftKind = GiftKind.Starter,
            Location = "Route 201",
        });

        var names = json.EnumerateObject().Select(property => property.Name).ToArray();

        Assert.Equal("kind", names[0]);
        Assert.Equal("game", names[1]);
        Assert.Equal("target", names[2]);
        Assert.Equal("source", names[^1]);
    }

    [Fact]
    public void A_form_entry_still_knows_its_species()
    {
        var target = DexTarget.ForForm(new SpeciesId("vulpix"), new FormId("vulpix-alola"));
        var restored = RoundTrip(target);

        Assert.True(target.IsForm);
        Assert.Equal(new SpeciesId("vulpix"), restored.Species);
        Assert.Equal(new FormId("vulpix-alola"), restored.Form);
    }

    [Fact]
    public void Enums_are_camel_case_strings()
    {
        var game = new Game(
            new GameId("sword"),
            "Pokemon Sword",
            "Sword",
            8,
            "Galar",
            GameRelease.Cartridge,
            NationalDexThrough: null,
            DexSource.GameDex,
            new GameId("shield"));

        var json = Serialize(game);

        Assert.Equal("cartridge", json.GetProperty("release").GetString());
        Assert.Equal("gameDex", json.GetProperty("dexSource").GetString());
        Assert.Equal(game, RoundTrip(game));
    }

    [Fact]
    public void A_game_without_a_pair_partner_omits_the_field()
    {
        var game = new Game(
            new GameId("emerald"),
            "Pokemon Emerald",
            "Emerald",
            3,
            "Hoenn",
            GameRelease.Cartridge,
            NationalDexThrough: 386,
            DexSource.NationalDex,
            PairPartner: null);

        Assert.False(Serialize(game).TryGetProperty("pairPartner", out _));
        Assert.Null(RoundTrip(game).PairPartner);
    }

    [Fact]
    public void Each_acquisition_kind_survives_a_round_trip_as_its_own_type()
    {
        AcquisitionMethod[] methods =
        [
            new GiftAcquisition
            {
                Game = new GameId("platinum"),
                Target = DexTarget.ForSpecies(new SpeciesId("chimchar")),
                Source = Citation,
                GiftKind = GiftKind.Starter,
                Location = "Route 201",
                Level = 5,
            },
            new WildAcquisition
            {
                Game = new GameId("platinum"),
                Target = DexTarget.ForSpecies(new SpeciesId("starly")),
                Source = Citation,
                Location = "Route 202",
                Method = EncounterMethod.Walk,
                Levels = new LevelRange(3, 4),
                RatePercent = 55,
            },
            new EvolutionAcquisition
            {
                Game = new GameId("platinum"),
                Target = DexTarget.ForSpecies(new SpeciesId("monferno")),
                Source = Citation,
                Rule = new EvolutionRuleId("chimchar-to-monferno"),
            },
            new TradeAcquisition
            {
                Game = new GameId("platinum"),
                Target = DexTarget.ForSpecies(new SpeciesId("chatot")),
                Source = Citation,
                Location = "Eterna City",
                Wants = DexTarget.ForSpecies(new SpeciesId("buizel")),
            },
        ];

        foreach (var method in methods)
        {
            var restored = RoundTrip(method);

            Assert.Equal(method.GetType(), restored.GetType());
            Assert.Equal(method, restored);
        }
    }

    [Fact]
    public void The_acquisition_discriminator_is_the_kind_the_ui_orders_by()
    {
        var json = Serialize<AcquisitionMethod>(new EvolutionAcquisition
        {
            Game = new GameId("platinum"),
            Target = DexTarget.ForSpecies(new SpeciesId("monferno")),
            Source = Citation,
            Rule = new EvolutionRuleId("chimchar-to-monferno"),
        });

        Assert.Equal("evolution", json.GetProperty("kind").GetString());
    }

    [Fact]
    public void Sections_are_ordered_gift_wild_evolution_trade()
    {
        Assert.Equal(
            [AcquisitionKind.Gift, AcquisitionKind.Wild, AcquisitionKind.Evolution, AcquisitionKind.Trade],
            Enum.GetValues<AcquisitionKind>().OrderBy(kind => (int)kind));
    }

    [Fact]
    public void Species_filters_keep_their_type()
    {
        SpeciesFilter[] filters =
        [
            new AllSpeciesFilter(),
            new NationalDexRangeFilter(1, 251),
            new PresentInTargetDexFilter(),
        ];

        foreach (var filter in filters)
        {
            Assert.Equal(filter, RoundTrip(filter));
        }
    }

    [Fact]
    public void A_transfer_edge_keeps_its_filter_through_a_round_trip()
    {
        var edge = new TransferEdge(
            new GameId("emerald"),
            new GameId("platinum"),
            TransferMechanism.PalPark,
            TransferDirection.OneWay,
            new NationalDexRangeFilter(1, 386));

        var restored = RoundTrip(edge);

        Assert.Equal(edge, restored);
        Assert.Equal(new NationalDexRangeFilter(1, 386), Assert.IsType<NationalDexRangeFilter>(restored.Filter));
    }

    [Fact]
    public void Evolution_conditions_keep_their_type()
    {
        var rule = new EvolutionRule(
            new EvolutionRuleId("eevee-to-leafeon"),
            DexTarget.ForSpecies(new SpeciesId("eevee")),
            DexTarget.ForSpecies(new SpeciesId("leafeon")),
            EvolutionTrigger.LevelUp,
            [new LocationCondition("Eterna Forest")]);

        var restored = RoundTrip(rule);

        // Records holding a collection compare that collection by reference, so the parts are
        // checked individually rather than with Assert.Equal(rule, restored).
        Assert.Equal(rule.Id, restored.Id);
        Assert.Equal(rule.From, restored.From);
        Assert.Equal(rule.To, restored.To);
        Assert.Equal(rule.Trigger, restored.Trigger);
        Assert.Equal(rule.Conditions, restored.Conditions);
        Assert.Equal("Eterna Forest", Assert.IsType<LocationCondition>(restored.Conditions[0]).Location);
    }

    [Fact]
    public void The_kind_is_restored_from_the_discriminator_rather_than_stored_twice()
    {
        var json = Serialize<AcquisitionMethod>(new WildAcquisition
        {
            Game = new GameId("platinum"),
            Target = DexTarget.ForSpecies(new SpeciesId("starly")),
            Source = Citation,
            Location = "Route 202",
            Method = EncounterMethod.Walk,
            Levels = new LevelRange(3, 4),
        });

        // "kind" appears once, as the discriminator; the Kind property is not written beside it.
        var kindProperties = json.EnumerateObject().Count(property => property.NameEquals("kind"));

        Assert.Equal(1, kindProperties);
        Assert.Equal("wild", json.GetProperty("kind").GetString());
    }

    [Fact]
    public void A_form_without_its_own_types_falls_back_to_the_species()
    {
        var form = new Form(
            new FormId("pikachu-female"),
            new SpeciesId("pikachu"),
            "Female",
            FormKind.Gender,
            [new GameId("platinum")]);

        Assert.False(Serialize(form).TryGetProperty("types", out _));
        Assert.Null(RoundTrip(form).Types);
    }

    [Fact]
    public void A_regional_form_overrides_the_species_types()
    {
        var form = new Form(
            new FormId("vulpix-alola"),
            new SpeciesId("vulpix"),
            "Alolan",
            FormKind.Regional,
            [new GameId("sun"), new GameId("moon")],
            [PokemonType.Ice]);

        Assert.Equal([PokemonType.Ice], RoundTrip(form).Types);
    }

    [Fact]
    public void A_game_file_round_trips_with_mixed_acquisition_kinds()
    {
        var data = new GameData(
            new Game(
                new GameId("platinum"),
                "Pokemon Platinum Version",
                "Platinum",
                4,
                "Sinnoh",
                GameRelease.Cartridge,
                NationalDexThrough: 493,
                DexSource.NationalDex,
                PairPartner: null),
            [new DexEntry(new GameId("platinum"), DexTarget.ForSpecies(new SpeciesId("chimchar")), 4)],
            [
                new GiftAcquisition
                {
                    Game = new GameId("platinum"),
                    Target = DexTarget.ForSpecies(new SpeciesId("chimchar")),
                    Source = Citation,
                    GiftKind = GiftKind.Starter,
                    Location = "Route 201",
                    Level = 5,
                },
                new EvolutionAcquisition
                {
                    Game = new GameId("platinum"),
                    Target = DexTarget.ForSpecies(new SpeciesId("monferno")),
                    Source = Citation,
                    Rule = new EvolutionRuleId("chimchar-to-monferno"),
                },
            ]);

        var restored = RoundTrip(data);

        Assert.Equal(data.Game, restored.Game);
        Assert.Equal(data.DexEntries, restored.DexEntries);
        Assert.Equal(2, restored.AcquisitionMethods.Count);
        Assert.IsType<GiftAcquisition>(restored.AcquisitionMethods[0]);
        Assert.IsType<EvolutionAcquisition>(restored.AcquisitionMethods[1]);
    }

    [Fact]
    public void A_game_file_path_is_derived_from_the_game_id()
    {
        Assert.Equal("games/platinum.json", DatasetLayout.GameFile(new GameId("platinum")));
    }
}
