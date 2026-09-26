using LivingDex.Core.Dataset;
using LivingDex.Core.Dex;
using LivingDex.Core.Reference;
using LivingDex.Core.UserData;

namespace LivingDex.Core.Tests.Dex;

/// <summary>
/// Whether a game can actually produce an entry, as opposed to merely knowing a rule about it.
/// </summary>
public class AvailabilityTests
{
    private static readonly GameId Platinum = new("platinum");
    private static readonly GameId Emerald = new("emerald");
    private static readonly DexCollectionId CollectionId = new("test");

    private static readonly SpeciesId Bulbasaur = new("bulbasaur");
    private static readonly SpeciesId Ivysaur = new("ivysaur");
    private static readonly SpeciesId Venusaur = new("venusaur");
    private static readonly SpeciesId Electabuzz = new("electabuzz");
    private static readonly SpeciesId Elekid = new("elekid");
    private static readonly SpeciesId Deoxys = new("deoxys");
    private static readonly FormId DeoxysAttack = new("deoxys-attack");

    private static readonly SourceCitation Citation =
        new("pokeapi", null, new DateOnly(2026, 9, 22));

    private static DexTarget Of(SpeciesId species) => DexTarget.ForSpecies(species);

    private static Game Game(GameId id) =>
        new(id, id.Value, id.Value, 4, "Sinnoh", GameRelease.Cartridge, 493, DexSource.NationalDex, null);

    private static EvolutionRule Rule(SpeciesId from, SpeciesId to) =>
        new(new EvolutionRuleId($"{from.Value}-to-{to.Value}"), Of(from), Of(to), EvolutionTrigger.LevelUp, []);

    private static WildAcquisition Wild(GameId game, SpeciesId species) =>
        new WildAcquisition
        {
            Game = game,
            Target = Of(species),
            Source = Citation,
            Location = "Route 201",
            Method = EncounterMethod.Walk,
            Levels = new LevelRange(2, 3),
        };

    private static EvolutionAcquisition Evolves(GameId game, SpeciesId from, SpeciesId to) =>
        new EvolutionAcquisition
        {
            Game = game,
            Target = Of(to),
            Source = Citation,
            Rule = new EvolutionRuleId($"{from.Value}-to-{to.Value}"),
        };

    private static FormChangeAcquisition Changes(GameId game, SpeciesId species, FormId form) =>
        new FormChangeAcquisition
        {
            Game = game,
            Target = DexTarget.ForForm(species, form),
            Source = Citation,
            Requirement = "Touch the meteorite",
        };

    private static BreedingAcquisition Hatches(GameId game, SpeciesId baby, SpeciesId parent) =>
        new BreedingAcquisition
        {
            Game = game,
            Target = Of(baby),
            Source = Citation,
            Parents = [Of(parent)],
            Location = "Solaceon Town",
        };

    /// <summary>
    /// Platinum knows the whole Bulbasaur chain and produces none of it. It does produce an
    /// Electabuzz, and hatches an Elekid from one.
    /// </summary>
    private static ReferenceData Reference() =>
        new(
            [Game(Platinum), Game(Emerald)],
            [],
            [],
            [],
            evolutionRules: [Rule(Bulbasaur, Ivysaur), Rule(Ivysaur, Venusaur)],
            acquisitionMethods:
            [
                Evolves(Platinum, Bulbasaur, Ivysaur),
                Evolves(Platinum, Ivysaur, Venusaur),
                Wild(Platinum, Electabuzz),
                Hatches(Platinum, Elekid, Electabuzz),
                Wild(Emerald, Bulbasaur),
                // Platinum can cycle a Deoxys through its formes and cannot produce a Deoxys.
                Changes(Platinum, Deoxys, DeoxysAttack),
                // Emerald can do both.
                Wild(Emerald, Deoxys),
                Changes(Emerald, Deoxys, DeoxysAttack),
            ]);

    private static CaptureIndex Holding(SpeciesId species, GameId game) =>
        CaptureIndex.For(
            CollectionId,
            [
                CaptureRecord.CaughtIn(CollectionId, Of(species), game, game, new DateOnly(2026, 9, 22)),
            ]);

    [Fact]
    public void An_evolution_of_something_the_game_cannot_produce_is_not_available()
    {
        var availability = new Availability(Reference(), CaptureIndex.Empty);

        // The whole bug: Platinum has a method for Ivysaur, and no Platinum player will ever
        // have one without bringing the Bulbasaur themselves.
        Assert.False(availability.In(Platinum, Of(Bulbasaur)));
        Assert.False(availability.In(Platinum, Of(Ivysaur)));
        Assert.False(availability.In(Platinum, Of(Venusaur)));
    }

    [Fact]
    public void Bringing_the_earlier_stage_in_makes_the_rest_of_the_chain_available()
    {
        var availability = new Availability(Reference(), Holding(Bulbasaur, Platinum));

        Assert.True(availability.In(Platinum, Of(Ivysaur)));
        // And the stage after it, which depends on the Ivysaur that is now reachable.
        Assert.True(availability.In(Platinum, Of(Venusaur)));

        // Owning one is not the same as the game producing one. You cannot get a Bulbasaur in
        // Platinum; you carried it in.
        Assert.False(availability.In(Platinum, Of(Bulbasaur)));
    }

    [Fact]
    public void A_bulbasaur_sitting_in_another_game_does_not_help_platinum()
    {
        // Caught in Emerald and still there: Platinum cannot evolve what it does not hold.
        var availability = new Availability(Reference(), Holding(Bulbasaur, Emerald));

        Assert.False(availability.In(Platinum, Of(Ivysaur)));
        // The game that does have one can, of course.
        Assert.True(availability.In(Emerald, Of(Bulbasaur)));
    }

    [Fact]
    public void Something_the_game_catches_outright_is_available()
    {
        var availability = new Availability(Reference(), CaptureIndex.Empty);

        Assert.True(availability.In(Platinum, Of(Electabuzz)));
    }

    [Fact]
    public void An_egg_is_available_when_a_parent_is()
    {
        var availability = new Availability(Reference(), CaptureIndex.Empty);

        // Electabuzz is on a route here, so the Elekid that hatches from it can be had.
        Assert.True(availability.In(Platinum, Of(Elekid)));
    }

    [Fact]
    public void An_egg_whose_parents_cannot_be_had_is_not_available()
    {
        var reference = new ReferenceData(
            [Game(Platinum)],
            [],
            [],
            [],
            acquisitionMethods: [Hatches(Platinum, Elekid, Electabuzz)]);

        var availability = new Availability(reference, CaptureIndex.Empty);

        Assert.False(availability.In(Platinum, Of(Elekid)));
    }

    [Fact]
    public void An_evolution_whose_rule_is_missing_is_not_a_way_to_get_anything()
    {
        // The rule table does not have it, so nothing can say what it evolves from. The
        // validator reports that separately; here it simply does not count as a way.
        var reference = new ReferenceData(
            [Game(Platinum)],
            [],
            [],
            [],
            acquisitionMethods: [Evolves(Platinum, Bulbasaur, Ivysaur)]);

        var availability = new Availability(reference, CaptureIndex.Empty);

        Assert.False(availability.In(Platinum, Of(Ivysaur)));
    }

    [Fact]
    public void A_game_with_nothing_recorded_produces_nothing()
    {
        var availability = new Availability(ReferenceData.Empty, CaptureIndex.Empty);

        Assert.False(availability.In(Platinum, Of(Bulbasaur)));
    }

    [Fact]
    public void A_way_the_dataset_records_and_does_not_count_is_not_availability()
    {
        // Kalos's Friend Safari: the table is real, and which Safari a player can walk into was
        // settled by somebody else's friend code. "Available in X" must not promise it.
        var safari = Wild(Platinum, Bulbasaur) with
        {
            DoesNotCount = "a Friend Safari holds what a stranger's friend code decided",
        };

        var reference = new ReferenceData(
            [Game(Platinum)],
            [],
            [],
            [],
            acquisitionMethods: [safari]);

        var availability = new Availability(reference, CaptureIndex.Empty);

        Assert.False(availability.In(Platinum, Of(Bulbasaur)));
        // And it is still there to be read: the popup shows what the game has, reason included.
        Assert.Single(reference.MethodsFor(Platinum, Of(Bulbasaur)));
        Assert.False(safari.Counts);
    }

    [Fact]
    public void A_source_outside_the_dataset_is_read_and_never_counted()
    {
        // The Pokemon Dream Radar and Pokemon GO: real ways, in another program on another
        // device. The row is what the popup shows; the tile stays out of reach, and the model
        // makes that structural rather than optional - every one of these carries its reason.
        var radar = new OutsideAcquisition
        {
            Game = Platinum,
            Target = Of(Bulbasaur),
            SentFrom = "the Pokemon Dream Radar",
            How = "Caught in the Interdream Zone and sent down to the cartridge",
            DoesNotCount = "It is caught in a separate Nintendo 3DS download",
            Source = Citation,
        };

        var reference = new ReferenceData(
            [Game(Platinum)],
            [],
            [],
            [],
            acquisitionMethods: [radar]);

        var availability = new Availability(reference, CaptureIndex.Empty);

        Assert.False(availability.In(Platinum, Of(Bulbasaur)));
        Assert.Single(reference.MethodsFor(Platinum, Of(Bulbasaur)));
        Assert.False(radar.Counts);
    }

    [Fact]
    public void Nothing_can_be_evolved_from_something_only_an_uncounted_way_produces()
    {
        // The same lie one step further on: an Ivysaur evolved from a Bulbasaur nobody can be
        // told how to get is not available either.
        var safari = Wild(Platinum, Bulbasaur) with { DoesNotCount = "needs somebody else's 3DS" };

        var reference = new ReferenceData(
            [Game(Platinum)],
            [],
            [],
            [],
            evolutionRules: [Rule(Bulbasaur, Ivysaur)],
            acquisitionMethods: [safari, Evolves(Platinum, Bulbasaur, Ivysaur)]);

        var availability = new Availability(reference, CaptureIndex.Empty);

        Assert.False(availability.In(Platinum, Of(Ivysaur)));
    }

    [Fact]
    public void A_form_of_something_the_game_cannot_produce_is_not_available()
    {
        var availability = new Availability(Reference(), CaptureIndex.Empty);

        // The same bug as Ivysaur's, one record kind further on. Platinum knows how to touch
        // the meteorite and has no way at all of producing a Deoxys to touch it with.
        Assert.False(availability.In(Platinum, DexTarget.ForForm(Deoxys, DeoxysAttack)));

        // Emerald catches one, so its formes really are available there.
        Assert.True(availability.In(Emerald, DexTarget.ForForm(Deoxys, DeoxysAttack)));
    }

    [Fact]
    public void Bringing_the_species_in_makes_its_forms_available()
    {
        var availability = new Availability(Reference(), Holding(Deoxys, Platinum));

        // Which is the whole point of an item that changes something: the Deoxys was carried
        // in, and the meteorite is waiting.
        Assert.True(availability.In(Platinum, DexTarget.ForForm(Deoxys, DeoxysAttack)));
    }
}
