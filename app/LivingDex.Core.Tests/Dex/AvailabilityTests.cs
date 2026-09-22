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
}
