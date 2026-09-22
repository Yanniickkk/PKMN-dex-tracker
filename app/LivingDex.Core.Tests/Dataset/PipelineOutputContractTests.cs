using System.Text.Json;
using LivingDex.Core.Dataset;
using LivingDex.Core.Dex;
using LivingDex.Core.Reference;
using LivingDex.Core.UserData;

namespace LivingDex.Core.Tests.Dataset;

/// <summary>
/// Reads the sample dataset the Python pipeline emits.
/// </summary>
/// <remarks>
/// The two halves of this project share no code — only this file format. The sample is
/// regenerated and compared by <c>pipeline/tests/test_emit.py</c>, so if either side changes
/// the wire shape, one of the two suites fails instead of the app quietly getting it wrong
/// months later.
/// </remarks>
public class PipelineOutputContractTests
{
    private static readonly string SampleDirectory = FindSample();

    private static string FindSample()
    {
        var directory = new DirectoryInfo(AppContext.BaseDirectory);

        while (directory is not null && !File.Exists(Path.Combine(directory.FullName, "LivingDex.slnx")))
        {
            directory = directory.Parent;
        }

        Assert.NotNull(directory);
        return Path.Combine(directory.FullName, "pipeline", "tests", "expected", "sample-dataset");
    }

    private static T Read<T>(params string[] pathParts)
    {
        var path = Path.Combine([SampleDirectory, .. pathParts]);
        Assert.True(File.Exists(path), $"the pipeline sample is missing {path}");

        return JsonSerializer.Deserialize<T>(File.ReadAllText(path), DatasetJson.Options)!;
    }

    [Fact]
    public void The_index_carries_the_stamp_and_the_games()
    {
        var index = Read<DatasetIndex>(DatasetLayout.IndexFile);

        Assert.Equal("0.1.0-sample", index.Stamp.Version);
        Assert.Equal(new DateOnly(2026, 9, 21), index.Stamp.BuiltOn);
        Assert.Equal(
            [
                new GameId("diamond"),
                new GameId("emerald"),
                new GameId("home"),
                new GameId("platinum"),
                new GameId("sword"),
            ],
            index.Games);
    }

    [Fact]
    public void Species_read_back_with_their_types_and_chain()
    {
        var species = Read<IReadOnlyList<Species>>(DatasetLayout.SpeciesFile);
        var monferno = species.Single(one => one.Id == new SpeciesId("monferno"));

        Assert.Equal(391, monferno.NationalDexNumber);
        Assert.Equal([PokemonType.Fire, PokemonType.Fighting], monferno.Types);
        Assert.Equal(new EvolutionChainId("chimchar"), monferno.EvolutionChain);
    }

    [Fact]
    public void A_form_without_its_own_types_reads_back_as_null_rather_than_empty()
    {
        var forms = Read<IReadOnlyList<Form>>(DatasetLayout.FormsFile);

        var alolan = forms.Single(one => one.Id == new FormId("vulpix-alola"));
        var female = forms.Single(one => one.Id == new FormId("pikachu-female"));

        Assert.Equal([PokemonType.Ice], alolan.Types);
        Assert.Equal(FormKind.Regional, alolan.Kind);
        Assert.Null(female.Types);
        Assert.Equal(FormKind.Gender, female.Kind);
    }

    [Fact]
    public void Every_species_filter_shape_survives_the_crossing()
    {
        var edges = Read<IReadOnlyList<TransferEdge>>(DatasetLayout.TransfersFile);

        Assert.IsType<AllSpeciesFilter>(edges.Single(edge => edge.Mechanism == TransferMechanism.Trade).Filter);
        Assert.IsType<PresentInTargetDexFilter>(edges.Single(edge => edge.Mechanism == TransferMechanism.Home).Filter);

        var palPark = edges.Single(edge => edge.Mechanism == TransferMechanism.PalPark);
        var range = Assert.IsType<NationalDexRangeFilter>(palPark.Filter);

        Assert.Equal(new GameId("emerald"), palPark.From);
        Assert.Equal(TransferDirection.OneWay, palPark.Direction);
        Assert.Equal(1, range.From);
        Assert.Equal(386, range.To);
    }

    [Fact]
    public void Evolution_conditions_survive_the_crossing()
    {
        var rules = Read<IReadOnlyList<EvolutionRule>>(DatasetLayout.EvolutionRulesFile);

        var toMonferno = rules.Single(rule => rule.Id == new EvolutionRuleId("chimchar-to-monferno"));
        Assert.Equal(DexTarget.ForSpecies(new SpeciesId("chimchar")), toMonferno.From);
        Assert.Equal(EvolutionTrigger.LevelUp, toMonferno.Trigger);
        Assert.Equal(14, Assert.IsType<MinimumLevelCondition>(toMonferno.Conditions[0]).Level);

        var toLeafeon = rules.Single(rule => rule.Id == new EvolutionRuleId("eevee-to-leafeon"));
        Assert.Equal("Eterna Forest", Assert.IsType<LocationCondition>(toLeafeon.Conditions[0]).Location);
    }

    [Fact]
    public void Every_acquisition_kind_lands_as_the_right_type()
    {
        var platinum = Read<GameData>("games", "platinum.json");

        Assert.Equal(new GameId("platinum"), platinum.Game.Id);
        Assert.Equal(493, platinum.Game.NationalDexThrough);
        Assert.True(platinum.Game.HasNationalDex);
        Assert.Equal(DexSource.NationalDex, platinum.Game.DexSource);

        var gift = Assert.IsType<GiftAcquisition>(platinum.AcquisitionMethods[0]);
        Assert.Equal(GiftKind.Starter, gift.GiftKind);
        Assert.Equal("Professor Rowan", gift.Npc);
        Assert.Equal(5, gift.Level);
        Assert.Equal("bulbapedia", gift.Source.Source);
        Assert.Equal(new DateOnly(2026, 9, 21), gift.Source.RetrievedOn);

        var wild = Assert.IsType<WildAcquisition>(platinum.AcquisitionMethods[1]);
        Assert.Equal(EncounterMethod.Walk, wild.Method);
        Assert.Equal(new LevelRange(3, 4), wild.Levels);
        Assert.Equal(55, wild.RatePercent);
        Assert.Equal("morning", wild.TimeOfDay);
        Assert.Null(wild.Season);

        var evolution = Assert.IsType<EvolutionAcquisition>(platinum.AcquisitionMethods[2]);
        Assert.Equal(new EvolutionRuleId("chimchar-to-monferno"), evolution.Rule);

        var trade = Assert.IsType<TradeAcquisition>(platinum.AcquisitionMethods[3]);
        Assert.Equal(DexTarget.ForSpecies(new SpeciesId("buizel")), trade.Wants);

        // [4] is a second wild slot, there so that one of Pichu's parents can be got and the
        // breeding dead-end check has nothing to say about the sample.
        var breeding = Assert.IsType<BreedingAcquisition>(platinum.AcquisitionMethods[5]);
        Assert.Equal(
            [DexTarget.ForSpecies(new SpeciesId("pikachu")), DexTarget.ForSpecies(new SpeciesId("raichu"))],
            breeding.Parents);
        Assert.Equal("Solaceon Town", breeding.Location);
        Assert.StartsWith("A parent holding a Light Ball", breeding.Requirement, StringComparison.Ordinal);
    }

    [Fact]
    public void A_game_says_which_battle_sprites_it_shows()
    {
        var emerald = Read<GameData>("games", "emerald.json");
        var platinum = Read<GameData>("games", "platinum.json");

        Assert.Equal("generation-iii/emerald", emerald.Game.SpriteSet);
        // Absent rather than empty: a game with none of its own falls back to the shared set.
        Assert.Null(platinum.Game.SpriteSet);
    }

    [Fact]
    public void A_game_without_a_national_dex_reads_back_as_not_having_one()
    {
        var sword = Read<GameData>("games", "sword.json");

        Assert.Null(sword.Game.NationalDexThrough);
        Assert.False(sword.Game.HasNationalDex);
        Assert.Equal(DexSource.GameDex, sword.Game.DexSource);
        Assert.Equal(new GameId("shield"), sword.Game.PairPartner);
        Assert.Equal(2, sword.AcquisitionMethods.Count);
    }

    [Fact]
    public void An_entry_that_cannot_be_filled_says_why_rather_than_carrying_a_bare_flag()
    {
        var platinum = Read<GameData>("games", "platinum.json");

        var catchable = platinum.DexEntries.Single(entry => entry.Target.Species == new SpeciesId("chimchar"));
        var stated = platinum.DexEntries.Single(entry => entry.Target.Species == new SpeciesId("darkrai"));

        Assert.False(catchable.IsUnobtainable);
        Assert.Null(catchable.UnobtainableReason);

        Assert.True(stated.IsUnobtainable);
        Assert.Equal("event distribution only", stated.UnobtainableReason);
    }

    [Fact]
    public void A_transfer_only_node_is_an_entity_like_any_other()
    {
        var home = Read<GameData>("games", "home.json");

        // Not a cartridge and not Virtual Console: HOME is a service, and the graph needs it.
        Assert.Equal(GameRelease.Service, home.Game.Release);
        Assert.False(home.Game.HasNationalDex);
        Assert.Empty(home.DexEntries);
    }

    [Fact]
    public void A_dex_entry_can_name_a_form_or_just_a_species()
    {
        var sword = Read<GameData>("games", "sword.json");

        Assert.Equal(DexTarget.ForSpecies(new SpeciesId("vulpix")), sword.DexEntries[0].Target);
        Assert.Equal(
            DexTarget.ForForm(new SpeciesId("vulpix"), new FormId("vulpix-alola")),
            sword.DexEntries[1].Target);
    }

    [Fact]
    public void The_sample_is_enough_to_drive_the_dex_builder()
    {
        var reference = new ReferenceData(
            [Read<GameData>("games", "platinum.json").Game, Read<GameData>("games", "sword.json").Game],
            Read<IReadOnlyList<Species>>(DatasetLayout.SpeciesFile),
            Read<IReadOnlyList<Form>>(DatasetLayout.FormsFile),
            [.. Read<GameData>("games", "sword.json").DexEntries]);

        var collection = new DexCollection(
            new DexCollectionId("sample"),
            "Sample",
            new GameId("sword"),
            [],
            FormSelection.Default);

        var lines = new DexBuilder(reference).Build(collection);

        Assert.Equal(
            [DexTarget.ForSpecies(new SpeciesId("vulpix")), DexTarget.ForForm(new SpeciesId("vulpix"), new FormId("vulpix-alola"))],
            lines.Select(line => line.Target));
    }
}
