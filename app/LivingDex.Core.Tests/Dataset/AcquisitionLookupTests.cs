using LivingDex.Core.Dataset;
using LivingDex.Core.Reference;

namespace LivingDex.Core.Tests.Dataset;

/// <summary>
/// The lookups the "available in game" filter and the detail popup ask for.
/// </summary>
public class AcquisitionLookupTests
{
    private static readonly GameId Platinum = new("platinum");
    private static readonly GameId Emerald = new("emerald");
    private static readonly DexTarget Chimchar = DexTarget.ForSpecies(new SpeciesId("chimchar"));
    private static readonly DexTarget Starly = DexTarget.ForSpecies(new SpeciesId("starly"));

    private static readonly SourceCitation Citation = new(
        "bulbapedia",
        new Uri("https://bulbapedia.bulbagarden.net/wiki/Route_201"),
        new DateOnly(2026, 9, 21));

    private static ReferenceData Reference(params AcquisitionMethod[] methods) =>
        new([], [], [], [], acquisitionMethods: methods);

    [Fact]
    public void A_game_with_no_methods_has_no_acquisition_data()
    {
        var reference = Reference();

        Assert.False(reference.HasAcquisitionData(Platinum));
        Assert.Empty(reference.MethodsFor(Platinum, Chimchar));
    }

    [Fact]
    public void Methods_are_found_by_game_and_target_together()
    {
        var reference = Reference(
            new GiftAcquisition
            {
                Game = Platinum,
                Target = Chimchar,
                Source = Citation,
                GiftKind = GiftKind.Starter,
                Location = "Route 201",
                Level = 5,
            },
            new WildAcquisition
            {
                Game = Platinum,
                Target = Starly,
                Source = Citation,
                Location = "Route 202",
                Method = EncounterMethod.Walk,
                Levels = new LevelRange(3, 4),
                RatePercent = 55,
            });

        Assert.Single(reference.MethodsFor(Platinum, Chimchar));
        Assert.Single(reference.MethodsFor(Platinum, Starly));

        // The same species in another game is a different question.
        Assert.Empty(reference.MethodsFor(Emerald, Chimchar));
        Assert.True(reference.HasAcquisitionData(Platinum));
        Assert.False(reference.HasAcquisitionData(Emerald));
    }

    [Fact]
    public void Every_way_to_get_one_entry_comes_back_together()
    {
        var reference = Reference(
            new GiftAcquisition
            {
                Game = Platinum,
                Target = Chimchar,
                Source = Citation,
                GiftKind = GiftKind.Starter,
                Location = "Route 201",
                Level = 5,
            },
            new TradeAcquisition
            {
                Game = Platinum,
                Target = Chimchar,
                Source = Citation,
                Wants = Starly,
                Location = "Eterna City",
            });

        Assert.Equal(2, reference.MethodsFor(Platinum, Chimchar).Count);
    }
}

/// <summary>Which types an entry has, which a form may override.</summary>
public class TypeLookupTests
{
    private static readonly SpeciesId Vulpix = new("vulpix");
    private static readonly FormId Alolan = new("vulpix-alola");
    private static readonly FormId Cosmetic = new("vulpix-shiny-looking");

    private static ReferenceData Reference() => new(
        [],
        [new Species(Vulpix, 37, "Vulpix", [PokemonType.Fire], new EvolutionChainId("37"))],
        [
            new Form(Alolan, Vulpix, "Alolan", FormKind.Regional, [], [PokemonType.Ice]),
            new Form(Cosmetic, Vulpix, "Odd looking", FormKind.Cosmetic, []),
        ],
        []);

    [Fact]
    public void A_species_has_its_own_types()
    {
        Assert.Equal([PokemonType.Fire], Reference().TypesOf(DexTarget.ForSpecies(Vulpix)));
    }

    [Fact]
    public void A_form_that_sets_types_overrides_the_species()
    {
        Assert.Equal([PokemonType.Ice], Reference().TypesOf(DexTarget.ForForm(Vulpix, Alolan)));
    }

    [Fact]
    public void A_form_that_does_not_set_types_keeps_the_species_typing()
    {
        // Types are stored only when they differ, so null has to mean "the same", not "none".
        Assert.Equal([PokemonType.Fire], Reference().TypesOf(DexTarget.ForForm(Vulpix, Cosmetic)));
    }

    [Fact]
    public void An_unknown_species_has_no_types_rather_than_throwing()
    {
        Assert.Empty(Reference().TypesOf(DexTarget.ForSpecies(new SpeciesId("missingno"))));
    }
}
