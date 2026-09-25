using LivingDex.Core.Dex;
using LivingDex.Core.Reference;

namespace LivingDex.Core.Tests.Dex;

public class AcquisitionSectionsTests
{
    private static readonly GameId Platinum = new("platinum");
    private static readonly GameId Emerald = new("emerald");
    private static readonly GameId Sapphire = new("sapphire");
    private static readonly DexTarget Chimchar = DexTarget.ForSpecies(new SpeciesId("chimchar"));
    private static readonly DexTarget Starly = DexTarget.ForSpecies(new SpeciesId("starly"));

    private static readonly SourceCitation Citation = new(
        "bulbapedia",
        new Uri("https://bulbapedia.bulbagarden.net/wiki/Route_201"),
        new DateOnly(2026, 9, 21));

    private static GiftAcquisition Gift() => new()
    {
        Game = Platinum,
        Target = Chimchar,
        Source = Citation,
        GiftKind = GiftKind.Starter,
        Location = "Route 201",
        Level = 5,
    };

    private static WildAcquisition Wild(string location = "Route 202", GameId? game = null) => new()
    {
        Game = game ?? Platinum,
        Target = Starly,
        Source = Citation,
        Location = location,
        Method = EncounterMethod.Walk,
        Levels = new LevelRange(3, 4),
        RatePercent = 55,
    };

    private static EvolutionAcquisition Evolution() => new()
    {
        Game = Platinum,
        Target = Chimchar,
        Source = Citation,
        Rule = new EvolutionRuleId("chimchar-monferno"),
    };

    private static BreedingAcquisition Breeding() => new()
    {
        Game = Platinum,
        Target = DexTarget.ForSpecies(new SpeciesId("pichu")),
        Parents = [DexTarget.ForSpecies(new SpeciesId("pikachu"))],
        Location = "Solaceon Town",
        Source = Citation,
    };

    private static TradeAcquisition Trade() => new()
    {
        Game = Platinum,
        Target = Chimchar,
        Source = Citation,
        Wants = Starly,
        Location = "Eterna City",
    };

    [Fact]
    public void Nothing_to_show_is_no_sections_rather_than_four_empty_ones()
    {
        Assert.Empty(AcquisitionSections.Of([]));
    }

    [Fact]
    public void The_sections_come_back_in_the_fixed_order()
    {
        // Handed in backwards on purpose: the order is the section's, not the caller's.
        var sections = AcquisitionSections.Of([Trade(), Breeding(), Evolution(), Wild(), Gift()]);

        Assert.Equal(
            [
                AcquisitionKind.Gift,
                AcquisitionKind.Wild,
                AcquisitionKind.Evolution,
                AcquisitionKind.Breeding,
                AcquisitionKind.Trade,
            ],
            sections.Select(section => section.Kind));
    }

    [Fact]
    public void A_kind_with_no_methods_is_left_out()
    {
        var sections = AcquisitionSections.Of([Trade(), Gift()]);

        Assert.Equal([AcquisitionKind.Gift, AcquisitionKind.Trade], sections.Select(section => section.Kind));
    }

    [Fact]
    public void Several_methods_of_one_kind_stay_together_in_the_order_given()
    {
        var first = Wild("Route 202");
        var second = Wild("Route 203");

        var sections = AcquisitionSections.Of([first, second]);

        var only = Assert.Single(sections);
        Assert.Equal([first, second], only.Methods);
    }

    [Fact]
    public void Within_a_section_the_main_game_comes_first()
    {
        var emerald = Wild("Safari Zone", Emerald);
        var platinum = Wild("Trophy Garden");

        var sections = AcquisitionSections.Of([emerald, platinum], [Platinum, Emerald]);

        var only = Assert.Single(sections);
        Assert.Equal([platinum, emerald], only.Methods);
    }

    [Fact]
    public void Linked_games_follow_in_the_order_the_collection_lists_them()
    {
        var sapphire = Wild("Route 110", Sapphire);
        var emerald = Wild("Safari Zone", Emerald);
        var platinum = Wild("Trophy Garden");

        var sections = AcquisitionSections.Of([sapphire, emerald, platinum], [Platinum, Emerald, Sapphire]);

        Assert.Equal([platinum, emerald, sapphire], Assert.Single(sections).Methods);
    }

    [Fact]
    public void Two_methods_from_one_game_keep_the_order_the_dataset_gave_them()
    {
        var first = Wild("Route 218");
        var second = Wild("Trophy Garden");
        var emerald = Wild("Safari Zone", Emerald);

        var sections = AcquisitionSections.Of([first, emerald, second], [Platinum, Emerald]);

        Assert.Equal([first, second, emerald], Assert.Single(sections).Methods);
    }

    [Fact]
    public void A_method_from_a_game_outside_the_collection_is_listed_last()
    {
        // Not expected, but a dataset can hold one. It must not push the main game down.
        var stranger = Wild("Somewhere", new GameId("ruby"));
        var platinum = Wild("Trophy Garden");

        var sections = AcquisitionSections.Of([stranger, platinum], [Platinum, Emerald]);

        Assert.Equal([platinum, stranger], Assert.Single(sections).Methods);
    }

    [Fact]
    public void With_no_game_order_the_methods_keep_the_order_they_came_in()
    {
        var emerald = Wild("Safari Zone", Emerald);
        var platinum = Wild("Trophy Garden");

        Assert.Equal([emerald, platinum], Assert.Single(AcquisitionSections.Of([emerald, platinum])).Methods);
    }

    [Fact]
    public void Every_kind_has_a_heading_of_its_own()
    {
        var headings = Enum.GetValues<AcquisitionKind>().Select(AcquisitionNames.Of).ToList();

        Assert.Equal(headings.Count, headings.Distinct(StringComparer.Ordinal).Count());
        Assert.DoesNotContain(headings, heading => string.IsNullOrWhiteSpace(heading));
    }

    [Fact]
    public void Every_encounter_method_and_gift_kind_reads_as_words()
    {
        Assert.Equal("Old Rod", AcquisitionNames.Of(EncounterMethod.OldRod));
        Assert.Equal("Starter", AcquisitionNames.Of(GiftKind.Starter));
        Assert.DoesNotContain(
            Enum.GetValues<GiftKind>().Select(AcquisitionNames.Of),
            name => string.IsNullOrWhiteSpace(name));
    }

    [Fact]
    public void Generation_5s_own_ways_of_meeting_something_are_named_rather_than_lumped()
    {
        // Unova hides a second table inside the first almost everywhere, and a third of what a
        // player can catch there is only in one of these. "another way" is the fallback for a
        // method nobody has read, and none of these five is that.
        EncounterMethod[] ownToUnova =
        [
            EncounterMethod.DarkGrass,
            EncounterMethod.RustlingGrass,
            EncounterMethod.DustCloud,
            EncounterMethod.RipplingWater,
            EncounterMethod.BridgeShadow,
        ];

        var names = ownToUnova.Select(AcquisitionNames.Of).ToList();

        Assert.DoesNotContain("another way", names);
        Assert.Equal(names.Count, names.Distinct(StringComparer.Ordinal).Count());
        Assert.Equal("dark grass", AcquisitionNames.Of(EncounterMethod.DarkGrass));
        Assert.Equal("rustling grass", AcquisitionNames.Of(EncounterMethod.RustlingGrass));
    }

    [Fact]
    public void Hisuis_own_two_ways_are_named_and_neither_is_the_fallback()
    {
        // Legends: Arceus throws away the whole vocabulary above: no grass, no rod, nothing
        // rolled when a player walks. Let's Go's three overworld words do most of the work, and
        // these two are what those three cannot say.
        EncounterMethod[] ownToHisui =
        [
            EncounterMethod.SpaceTimeDistortion,
            EncounterMethod.ShakenLoose,
        ];

        var names = ownToHisui.Select(AcquisitionNames.Of).ToList();

        // "another way" is where a method goes to stop being an answer, and 30 of the 69 species
        // a distortion holds are in nothing else in that game.
        Assert.DoesNotContain("another way", names);
        Assert.Equal("a space-time distortion", AcquisitionNames.Of(EncounterMethod.SpaceTimeDistortion));
        Assert.Equal("shaking it loose", AcquisitionNames.Of(EncounterMethod.ShakenLoose));
    }

    [Fact]
    public void Every_encounter_method_reads_as_words_rather_than_as_another_way()
    {
        // The guard for the next game that adds one: a value with no name here falls through to
        // "another way", which says nothing, and nothing in the dataset uses `Other`.
        var unnamed = Enum.GetValues<EncounterMethod>()
            .Where(one => one != EncounterMethod.Other)
            .Where(one => AcquisitionNames.Of(one) == "another way")
            .ToList();

        Assert.Empty(unnamed);
    }

    [Fact]
    public void Changing_a_form_is_its_own_section_and_the_last_one()
    {
        // The only kind that needs the Pokemon already. Everything above it answers "how do I
        // get one"; this answers "and then what", so it reads last.
        Assert.Equal("Changing its form", AcquisitionNames.Of(AcquisitionKind.FormChange));
        Assert.Equal(
            AcquisitionKind.FormChange,
            Enum.GetValues<AcquisitionKind>().Max());
    }

    [Fact]
    public void Generation_6s_own_ways_are_named_too_and_an_ambush_is_one_of_them()
    {
        // Kalos puts its second tables in plain sight: five at once, a patch of flowers, a
        // berry tree, and five different things that jump a player. The last five are one
        // method - what jumped is written beside the slot - so there are four names here.
        EncounterMethod[] ownToKalos =
        [
            EncounterMethod.Horde,
            EncounterMethod.FlowerPatch,
            EncounterMethod.BerryTree,
            EncounterMethod.Ambush,
        ];

        var names = ownToKalos.Select(AcquisitionNames.Of).ToList();

        Assert.DoesNotContain("another way", names);
        Assert.Equal(names.Count, names.Distinct(StringComparer.Ordinal).Count());
        Assert.Equal("a horde", AcquisitionNames.Of(EncounterMethod.Horde));
        Assert.Equal("an ambush", AcquisitionNames.Of(EncounterMethod.Ambush));
    }

    [Fact]
    public void The_two_halves_of_Hoenn_nobody_could_reach_before_are_named_as_well()
    {
        // The remakes' own: the table under the water a player is surfing on, and the flocks
        // met in mid-air while Soaring on a Latios. Neither is a rarer kind of what it looks
        // like from the surface, and "another way" would be the whole of what a player is told.
        Assert.Equal("diving", AcquisitionNames.Of(EncounterMethod.Dive));
        Assert.Equal("soaring", AcquisitionNames.Of(EncounterMethod.Soaring));
        Assert.NotEqual(AcquisitionNames.Of(EncounterMethod.Surf), AcquisitionNames.Of(EncounterMethod.Dive));
    }

    [Fact]
    public void A_hidden_grotto_is_a_place_rather_than_another_way()
    {
        // The sequels' own, and the only method in the dataset that no encounter table
        // anywhere lists. Twenty of them hold species that are nowhere else in those games, so
        // "another way" would be the answer to the one question a player is asking.
        Assert.Equal("a Hidden Grotto", AcquisitionNames.Of(EncounterMethod.HiddenGrotto));
    }
}
