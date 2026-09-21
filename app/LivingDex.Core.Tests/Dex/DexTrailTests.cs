using LivingDex.Core.Dataset;
using LivingDex.Core.Dex;
using LivingDex.Core.Reference;

namespace LivingDex.Core.Tests.Dex;

public class DexTrailTests
{
    private static DexLine Line(string species, int number) =>
        new(DexTarget.ForSpecies(new SpeciesId(species)), number, species, FormKind: null);

    private static readonly DexLine Infernape = Line("infernape", 392);
    private static readonly DexLine Monferno = Line("monferno", 391);
    private static readonly DexLine Chimchar = Line("chimchar", 390);

    [Fact]
    public void A_new_trail_is_one_step_with_nowhere_to_go_back_to()
    {
        var trail = DexTrail.StartingAt(Infernape);

        Assert.Equal(Infernape, trail.Current);
        Assert.Single(trail.Steps);
        Assert.False(trail.CanGoBack);
    }

    [Fact]
    public void Each_step_down_is_remembered_in_order()
    {
        var trail = DexTrail.StartingAt(Infernape);

        trail.GoTo(Monferno);
        trail.GoTo(Chimchar);

        Assert.Equal([Infernape, Monferno, Chimchar], trail.Steps);
        Assert.Equal(Chimchar, trail.Current);
        Assert.True(trail.CanGoBack);
    }

    [Fact]
    public void Going_back_drops_the_last_step_only()
    {
        var trail = DexTrail.StartingAt(Infernape);
        trail.GoTo(Monferno);
        trail.GoTo(Chimchar);

        trail.Back();

        Assert.Equal([Infernape, Monferno], trail.Steps);
    }

    [Fact]
    public void Going_back_from_the_start_does_nothing()
    {
        var trail = DexTrail.StartingAt(Infernape);

        trail.Back();

        Assert.Equal([Infernape], trail.Steps);
    }

    [Fact]
    public void A_breadcrumb_click_drops_everything_after_it()
    {
        var trail = DexTrail.StartingAt(Infernape);
        trail.GoTo(Monferno);
        trail.GoTo(Chimchar);

        trail.TruncateTo(0);

        Assert.Equal([Infernape], trail.Steps);
    }

    [Fact]
    public void Clicking_the_step_you_are_on_changes_nothing()
    {
        var trail = DexTrail.StartingAt(Infernape);
        trail.GoTo(Monferno);

        trail.TruncateTo(1);
        trail.TruncateTo(7);

        Assert.Equal([Infernape, Monferno], trail.Steps);
    }

    [Fact]
    public void Walking_back_into_the_trail_folds_it_rather_than_lengthening_it()
    {
        // Chains can loop, and a trail that grows on every loop would never stop.
        var trail = DexTrail.StartingAt(Infernape);
        trail.GoTo(Monferno);
        trail.GoTo(Chimchar);

        trail.GoTo(Monferno);

        Assert.Equal([Infernape, Monferno], trail.Steps);
        Assert.Equal(Monferno, trail.Current);
    }

    [Fact]
    public void Two_lines_for_one_entry_are_treated_as_the_same_step()
    {
        // The same target can arrive as a different DexLine: one built by the dex builder, one
        // made up for an entry the dex does not contain.
        var trail = DexTrail.StartingAt(Infernape);
        trail.GoTo(Monferno);

        trail.GoTo(new DexLine(Infernape.Target, 392, "Infernape (elsewhere)", FormKind: null));

        Assert.Single(trail.Steps);
        Assert.Equal(Infernape, trail.Current);
    }
}

public class DexLinesTests
{
    private static readonly SpeciesId Vulpix = new("vulpix");
    private static readonly FormId Alolan = new("vulpix-alola");

    private static ReferenceData Reference() => new(
        [],
        [new Species(Vulpix, 37, "Vulpix", [PokemonType.Fire], new EvolutionChainId("37"))],
        [new Form(Alolan, Vulpix, "Alolan", FormKind.Regional, [], [PokemonType.Ice])],
        []);

    [Fact]
    public void A_species_outside_the_dex_still_gets_its_name_and_number()
    {
        var line = DexLines.For(Reference(), DexTarget.ForSpecies(Vulpix));

        Assert.Equal("Vulpix", line.Name);
        Assert.Equal(37, line.Number);
        Assert.Null(line.FormKind);
        Assert.False(line.IsForm);
    }

    [Fact]
    public void A_form_keeps_its_kind_and_its_base_species_number()
    {
        var line = DexLines.For(Reference(), DexTarget.ForForm(Vulpix, Alolan));

        Assert.Equal("Vulpix (Alolan)", line.Name);
        Assert.Equal(37, line.Number);
        Assert.Equal(FormKind.Regional, line.FormKind);
    }

    [Fact]
    public void Something_the_dataset_has_never_heard_of_still_produces_a_line()
    {
        // A rule can point at a species a partial dataset does not carry. The popup has to draw
        // something rather than throw halfway through a chain.
        var line = DexLines.For(Reference(), DexTarget.ForSpecies(new SpeciesId("missingno")));

        Assert.Equal("missingno", line.Name);
        Assert.Equal(0, line.Number);
    }
}
