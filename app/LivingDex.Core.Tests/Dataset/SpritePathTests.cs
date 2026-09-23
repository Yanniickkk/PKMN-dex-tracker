using LivingDex.Core.Dataset;
using LivingDex.Core.Reference;

namespace LivingDex.Core.Tests.Dataset;

/// <summary>
/// Which picture a collection draws: its game's own battle sprites where they exist, and the
/// shared set where they do not.
/// </summary>
public sealed class SpritePathTests
{
    private static LoadedDataset Shipping(params string[] sprites) => new(
        new DatasetStamp("0.1.0", new DateOnly(2026, 9, 22)),
        new ReferenceData([], [], [], []),
        new Dictionary<GameId, string>(),
        new HashSet<string>(StringComparer.Ordinal),
        sprites.ToHashSet(StringComparer.Ordinal));

    private static SpeciesId Pikachu => new("pikachu");

    [Fact]
    public void A_game_with_no_set_of_its_own_draws_the_shared_sprite()
    {
        var dataset = Shipping("pikachu");

        Assert.Equal("sprites/pikachu.png", dataset.SpritePath(Pikachu, null));
    }

    [Fact]
    public void A_game_with_a_set_draws_that_generation_s_sprite()
    {
        var dataset = Shipping("pikachu", "generation-iii/emerald/pikachu");

        Assert.Equal(
            "sprites/generation-iii/emerald/pikachu.png",
            dataset.SpritePath(Pikachu, "generation-iii/emerald"));
    }

    [Fact]
    public void A_species_the_set_never_drew_falls_back_to_the_shared_sprite()
    {
        // Turtwig is Generation IV. An Emerald collection can still hold one, transferred in,
        // and a blank tile would be a worse answer than today's artwork.
        var dataset = Shipping("turtwig", "generation-iii/emerald/pikachu");

        Assert.Equal(
            "sprites/turtwig.png",
            dataset.SpritePath(new SpeciesId("turtwig"), "generation-iii/emerald"));
    }

    [Fact]
    public void A_form_the_set_drew_gets_its_own_picture()
    {
        var dataset = Shipping(
            "deerling",
            "generation-v/black-white/deerling",
            "generation-v/black-white/deerling-summer");

        Assert.Equal(
            "sprites/generation-v/black-white/deerling-summer.png",
            dataset.SpritePath(
                DexTarget.ForForm(new SpeciesId("deerling"), new FormId("deerling-summer")),
                "generation-v/black-white"));
    }

    [Fact]
    public void A_form_the_set_never_drew_falls_back_to_its_species_before_the_shared_set()
    {
        // Most sheets drew very few forms. The Generation V one has Deerling's seasons and
        // nothing for Wash Rotom, which those games themselves did draw - and a tile with
        // Rotom's picture and the form's name reads better than today's artwork or a hole.
        var dataset = Shipping("rotom", "generation-v/black-white/rotom");

        Assert.Equal(
            "sprites/generation-v/black-white/rotom.png",
            dataset.SpritePath(
                DexTarget.ForForm(new SpeciesId("rotom"), new FormId("rotom-wash")),
                "generation-v/black-white"));
    }

    [Fact]
    public void A_build_that_shipped_no_sprites_still_names_a_path()
    {
        // Nothing to draw, but the caller gets the path it would have been: the missing file is
        // what every-species-has-a-sprite already warns about, not something to handle twice.
        Assert.Equal("sprites/pikachu.png", Shipping().SpritePath(Pikachu, "generation-iii/emerald"));
    }

    [Fact]
    public void A_game_with_no_set_at_all_still_draws_the_right_form()
    {
        // Generation VII is why this exists: the source has no battle sprites for those games,
        // and most of Alola's Kanto Pokémon are the regional form. Without a picture of the form
        // in the shared set, an Alolan Rattata's tile would draw a Kantonian one.
        var dataset = Shipping("rattata", "rattata-alola");

        Assert.Equal(
            "sprites/rattata-alola.png",
            dataset.SpritePath(
                DexTarget.ForForm(new SpeciesId("rattata"), new FormId("rattata-alola")),
                null));
    }

    [Fact]
    public void A_sheet_is_preferred_to_the_shared_set_even_for_a_form_it_never_drew()
    {
        // The sheet is what the game actually drew, so a Wash Rotom in Black keeps the
        // Generation V Rotom it has always had rather than gaining today's artwork of the form.
        var dataset = Shipping(
            "rotom",
            "rotom-wash",
            "generation-v/black-white/rotom");

        Assert.Equal(
            "sprites/generation-v/black-white/rotom.png",
            dataset.SpritePath(
                DexTarget.ForForm(new SpeciesId("rotom"), new FormId("rotom-wash")),
                "generation-v/black-white"));
    }
}
