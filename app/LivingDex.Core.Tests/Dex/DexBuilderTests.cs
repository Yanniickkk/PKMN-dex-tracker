using LivingDex.Core.Dataset;
using LivingDex.Core.Dex;
using LivingDex.Core.Reference;
using LivingDex.Core.UserData;

namespace LivingDex.Core.Tests.Dex;

public class DexBuilderTests
{
    private static readonly GameId Platinum = new("platinum");
    private static readonly GameId Sword = new("sword");
    private static readonly DexCollectionId CollectionId = new("test");

    private static readonly SpeciesId Bulbasaur = new("bulbasaur");
    private static readonly SpeciesId Pikachu = new("pikachu");
    private static readonly SpeciesId Vulpix = new("vulpix");
    private static readonly SpeciesId Rotom = new("rotom");
    private static readonly SpeciesId Turtwig = new("turtwig");
    private static readonly SpeciesId Vivillon = new("vivillon");
    private static readonly SpeciesId Zacian = new("zacian");
    private static readonly SpeciesId Rowlet = new("rowlet");

    private static readonly FormId VulpixAlola = new("vulpix-alola");
    private static readonly FormId PikachuFemale = new("pikachu-female");
    private static readonly FormId RotomHeat = new("rotom-heat");
    private static readonly FormId VivillonMeadow = new("vivillon-meadow");

    private static ReferenceData Reference()
    {
        Game[] games =
        [
            new(Platinum, "Pokemon Platinum Version", "Platinum", 4, "Sinnoh", GameRelease.Cartridge, 493, DexSource.NationalDex, null),
            new(Sword, "Pokemon Sword", "Sword", 8, "Galar", GameRelease.Cartridge, null, DexSource.GameDex, new GameId("shield")),
        ];

        Species[] species =
        [
            new(Bulbasaur, 1, "Bulbasaur", [PokemonType.Grass, PokemonType.Poison], new EvolutionChainId("bulbasaur")),
            new(Pikachu, 25, "Pikachu", [PokemonType.Electric], new EvolutionChainId("pichu")),
            new(Vulpix, 37, "Vulpix", [PokemonType.Fire], new EvolutionChainId("vulpix")),
            new(Rotom, 479, "Rotom", [PokemonType.Electric, PokemonType.Ghost], new EvolutionChainId("rotom")),
            new(Turtwig, 387, "Turtwig", [PokemonType.Grass], new EvolutionChainId("turtwig")),
            new(Vivillon, 666, "Vivillon", [PokemonType.Bug, PokemonType.Flying], new EvolutionChainId("scatterbug")),
            new(Rowlet, 722, "Rowlet", [PokemonType.Grass, PokemonType.Flying], new EvolutionChainId("rowlet")),
            new(Zacian, 888, "Zacian", [PokemonType.Fairy], new EvolutionChainId("zacian")),
        ];

        Form[] forms =
        [
            new(VulpixAlola, Vulpix, "Alolan", FormKind.Regional, [Sword], [PokemonType.Ice]),
            new(PikachuFemale, Pikachu, "Female", FormKind.Gender, [Platinum, Sword]),
            new(RotomHeat, Rotom, "Heat", FormKind.Functional, [Platinum]),
            new(VivillonMeadow, Vivillon, "Meadow", FormKind.Cosmetic, [Sword]),
        ];

        // Sword has its own dex, and numbers Alolan Vulpix as a line of its own. Platinum has
        // one too, and a National Dex on top: the two lists are what the switch chooses between.
        DexEntry[] dexEntries =
        [
            new(Sword, DexTarget.ForSpecies(Vulpix), 100),
            new(Sword, DexTarget.ForForm(Vulpix, VulpixAlola), 101),
            new(Sword, DexTarget.ForSpecies(Pikachu), 194),
            new(Sword, DexTarget.ForSpecies(Vivillon), 300),
            new(Sword, DexTarget.ForSpecies(Zacian), 888),
            new(Platinum, DexTarget.ForSpecies(Turtwig), 1),
            new(Platinum, DexTarget.ForSpecies(Rotom), 152),
        ];

        return new ReferenceData(games, species, forms, dexEntries);
    }

    private static DexCollection Collection(GameId mainGame, FormSelection? forms = null) =>
        new(CollectionId, "Test", mainGame, [], forms ?? FormSelection.None);

    private static IReadOnlyList<DexLine> Build(GameId mainGame, FormSelection? forms = null) =>
        new DexBuilder(Reference()).Build(Collection(mainGame, forms));

    private static IEnumerable<DexTarget> TargetsOf(IEnumerable<DexLine> lines) =>
        lines.Select(line => line.Target);

    [Fact]
    public void A_national_dex_game_covers_everything_up_to_where_its_dex_ends()
    {
        var lines = Build(Platinum);

        Assert.Equal(
            ["bulbasaur", "pikachu", "vulpix", "turtwig", "rotom"],
            lines.Select(line => line.Target.Species.Value));

        // Rowlet is 722 and Zacian is 888; Platinum's National Dex stops at 493.
        Assert.DoesNotContain(Rowlet, lines.Select(line => line.Target.Species));
        Assert.DoesNotContain(Zacian, lines.Select(line => line.Target.Species));
    }

    [Fact]
    public void A_game_without_a_national_dex_uses_its_own_list_and_its_own_numbers()
    {
        var lines = Build(Sword);

        Assert.Equal(
            [Vulpix, Pikachu, Vivillon, Zacian],
            lines.Select(line => line.Target.Species));

        // Sword's own numbering, not the National Dex one.
        Assert.Equal(194, lines.Single(line => line.Target.Species == Pikachu).Number);
        Assert.Equal(100, lines.Single(line => line.Target.Species == Vulpix).Number);
    }

    [Fact]
    public void No_kinds_selected_gives_one_line_per_species()
    {
        var lines = Build(Sword, FormSelection.None);

        Assert.All(lines, line => Assert.False(line.IsForm));
        Assert.Equal(lines.Select(line => line.Target.Species).Distinct().Count(), lines.Count);
    }

    [Fact]
    public void Each_kind_is_its_own_switch()
    {
        var alolan = DexTarget.ForForm(Vulpix, VulpixAlola);
        var meadow = DexTarget.ForForm(Vivillon, VivillonMeadow);
        var female = DexTarget.ForForm(Pikachu, PikachuFemale);

        var regionalOnly = TargetsOf(Build(Sword, new FormSelection(Regional: true, Functional: false, Cosmetic: false, GenderDifferences: false)));
        Assert.Contains(alolan, regionalOnly);
        Assert.DoesNotContain(meadow, regionalOnly);
        Assert.DoesNotContain(female, regionalOnly);

        var cosmeticOnly = TargetsOf(Build(Sword, new FormSelection(Regional: false, Functional: false, Cosmetic: true, GenderDifferences: false)));
        Assert.Contains(meadow, cosmeticOnly);
        Assert.DoesNotContain(alolan, cosmeticOnly);

        var genderOnly = TargetsOf(Build(Sword, new FormSelection(Regional: false, Functional: false, Cosmetic: false, GenderDifferences: true)));
        Assert.Contains(female, genderOnly);
        Assert.DoesNotContain(alolan, genderOnly);
    }

    [Fact]
    public void Functional_forms_are_their_own_switch_too()
    {
        var heat = DexTarget.ForForm(Rotom, RotomHeat);

        var functionalOnly = new FormSelection(Regional: false, Functional: true, Cosmetic: false, GenderDifferences: false);
        Assert.Contains(heat, TargetsOf(Build(Platinum, functionalOnly)));

        var regionalOnly = new FormSelection(Regional: true, Functional: false, Cosmetic: false, GenderDifferences: false);
        Assert.DoesNotContain(heat, TargetsOf(Build(Platinum, regionalOnly)));
    }

    [Fact]
    public void The_default_selection_leaves_out_the_ones_that_are_only_a_repaint()
    {
        var lines = TargetsOf(Build(Sword, FormSelection.Default));

        Assert.Contains(DexTarget.ForForm(Vulpix, VulpixAlola), lines);
        Assert.DoesNotContain(DexTarget.ForForm(Vivillon, VivillonMeadow), lines);
        Assert.DoesNotContain(DexTarget.ForForm(Pikachu, PikachuFemale), lines);
    }

    [Fact]
    public void Selecting_everything_includes_every_kind()
    {
        var lines = TargetsOf(Build(Sword, FormSelection.All));

        Assert.Contains(DexTarget.ForForm(Vulpix, VulpixAlola), lines);
        Assert.Contains(DexTarget.ForForm(Vivillon, VivillonMeadow), lines);
        Assert.Contains(DexTarget.ForForm(Pikachu, PikachuFemale), lines);
    }

    [Fact]
    public void A_master_checkbox_has_something_to_bind_to()
    {
        Assert.False(FormSelection.None.Any);
        Assert.True(FormSelection.Default.Any);
        Assert.True(FormSelection.All.Any);
        Assert.True(new FormSelection(false, false, true, false).Any);
    }

    [Fact]
    public void Forms_that_do_not_exist_in_the_main_game_are_left_out_whatever_the_setting_says()
    {
        var onSword = TargetsOf(Build(Sword, FormSelection.All));
        var onPlatinum = TargetsOf(Build(Platinum, FormSelection.All));

        // Alolan Vulpix exists in Sword only.
        Assert.Contains(DexTarget.ForForm(Vulpix, VulpixAlola), onSword);
        Assert.DoesNotContain(DexTarget.ForForm(Vulpix, VulpixAlola), onPlatinum);

        // Rotom's appliance form exists in Platinum only.
        Assert.Contains(DexTarget.ForForm(Rotom, RotomHeat), onPlatinum);
        Assert.DoesNotContain(DexTarget.ForForm(Rotom, RotomHeat), onSword);
    }

    [Fact]
    public void A_form_takes_the_number_and_name_of_its_base_species()
    {
        var line = Build(Sword, FormSelection.All).Single(one => one.Target.Form == VulpixAlola);

        Assert.Equal(100, line.Number);
        Assert.Equal("Vulpix (Alolan)", line.Name);
        Assert.Equal(FormKind.Regional, line.FormKind);
    }

    [Fact]
    public void Lines_run_by_number_with_each_species_ahead_of_its_own_forms()
    {
        var lines = Build(Sword, FormSelection.All);

        Assert.Equal(
            [
                (100, false),
                (100, true),
                (194, false),
                (194, true),
                (300, false),
                (300, true),
                (888, false),
            ],
            lines.Select(line => (line.Number, line.IsForm)));
    }

    [Fact]
    public void A_form_the_game_numbers_separately_does_not_appear_twice()
    {
        // Sword's dex lists Alolan Vulpix as its own line, and the form table lists it too.
        var lines = Build(Sword, FormSelection.All);

        Assert.Single(lines, line => line.Target == DexTarget.ForForm(Vulpix, VulpixAlola));
        Assert.Single(lines, line => line.Target == DexTarget.ForSpecies(Vulpix));
    }

    [Fact]
    public void Toggling_the_form_settings_leaves_capture_records_alone()
    {
        var builder = new DexBuilder(Reference());
        var alolanVulpix = DexTarget.ForForm(Vulpix, VulpixAlola);

        var withRegional = builder.Build(Collection(Sword, FormSelection.Default));
        Assert.Contains(alolanVulpix, TargetsOf(withRegional));

        // The player catches it.
        var records = new List<CaptureRecord>
        {
            CaptureRecord.CaughtIn(CollectionId, alolanVulpix, Sword, Sword, new DateOnly(2026, 9, 21), "in the Isle of Armor"),
        };

        // They turn regional forms off. The line disappears from the grid...
        var withoutRegional = builder.Build(Collection(Sword, FormSelection.Default with { Regional = false }));
        Assert.DoesNotContain(alolanVulpix, TargetsOf(withoutRegional));

        // ...but the record is untouched, because building a dex only reads reference data.
        Assert.Single(records);
        Assert.Equal("in the Isle of Armor", records[0].Note);

        // Turning the setting back on lines the record up with its entry again. This is why
        // records are keyed by species-and-form and not by a dex entry id.
        var again = builder.Build(Collection(Sword, FormSelection.Default));
        Assert.Contains(again, line => line.Target == records[0].Target);
    }

    [Fact]
    public void Changing_the_main_game_keeps_records_that_the_new_game_also_has_an_entry_for()
    {
        var builder = new DexBuilder(Reference());
        var record = CaptureRecord.CaughtIn(CollectionId, DexTarget.ForSpecies(Pikachu), Sword, Sword);

        // Pikachu is numbered 194 in Sword and 25 in the National Dex, but it is the same entry
        // as far as the record is concerned.
        Assert.Contains(builder.Build(Collection(Sword)), line => line.Target == record.Target);
        Assert.Contains(builder.Build(Collection(Platinum)), line => line.Target == record.Target);
    }

    [Fact]
    public void A_game_with_both_lists_builds_whichever_is_asked_for()
    {
        var builder = new DexBuilder(Reference());

        var national = builder.Build(Collection(Platinum), DexSource.NationalDex);
        var regional = builder.Build(Collection(Platinum), DexSource.GameDex);

        // Everything up to 493, numbered as the National Dex numbers it.
        Assert.Contains(national, line => line.Target.Species == Bulbasaur && line.Number == 1);
        Assert.Contains(national, line => line.Target.Species == Turtwig && line.Number == 387);

        // The game's own list, numbered as the game numbers it: Turtwig first, not 387th.
        Assert.Equal(2, regional.Count);
        Assert.Equal([Turtwig, Rotom], regional.Select(line => line.Target.Species));
        Assert.Equal([1, 152], regional.Select(line => line.Number));
    }

    [Fact]
    public void Switching_between_the_two_lists_keeps_every_target_it_still_shows()
    {
        // The whole reason a switch is safe: records are keyed by target, and a target is the
        // same target under either numbering. Turtwig is 387 in one list and 1 in the other.
        var builder = new DexBuilder(Reference());
        var turtwig = DexTarget.ForSpecies(Turtwig);

        Assert.Contains(builder.Build(Collection(Platinum), DexSource.NationalDex), line => line.Target == turtwig);
        Assert.Contains(builder.Build(Collection(Platinum), DexSource.GameDex), line => line.Target == turtwig);
    }

    [Fact]
    public void Asking_for_nothing_in_particular_builds_the_list_the_game_names()
    {
        var builder = new DexBuilder(Reference());

        // Platinum says National Dex, so that is what it builds without being told otherwise.
        Assert.Equal(
            builder.Build(Collection(Platinum), DexSource.NationalDex).Count,
            builder.Build(Collection(Platinum)).Count);

        // Sword has no National Dex, so both answers are its own list.
        Assert.Equal(
            builder.Build(Collection(Sword), DexSource.GameDex).Count,
            builder.Build(Collection(Sword)).Count);
    }

    [Fact]
    public void A_collection_pointing_at_an_unknown_game_says_so()
    {
        var builder = new DexBuilder(Reference());

        var exception = Assert.Throws<DexBuildException>(() => builder.Build(Collection(new GameId("legends-z-a"))));

        Assert.Contains("legends-z-a", exception.Message, StringComparison.Ordinal);
    }

    [Fact]
    public void A_game_claiming_a_national_dex_without_saying_where_it_ends_is_a_data_error()
    {
        var broken = new ReferenceData(
            [new(Platinum, "Broken", "Platinum", 4, "Sinnoh", GameRelease.Cartridge, null, DexSource.NationalDex, null)],
            [],
            [],
            []);

        Assert.Throws<DexBuildException>(() => new DexBuilder(broken).Build(Collection(Platinum)));
    }
}
