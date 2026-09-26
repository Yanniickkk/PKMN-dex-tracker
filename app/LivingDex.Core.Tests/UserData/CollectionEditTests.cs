using LivingDex.Core.Reference;
using LivingDex.Core.UserData;

namespace LivingDex.Core.Tests.UserData;

public class CollectionEditTests
{
    private static readonly GameId Platinum = new("platinum");
    private static readonly GameId Emerald = new("emerald");
    private static readonly GameId FireRed = new("firered");

    private static DexCollection Stored { get; } = new(
        DexCollectionId.New(),
        "Platinum living dex",
        Platinum,
        [Emerald],
        FormSelection.Default);

    [Fact]
    public void An_edit_opens_on_what_is_stored()
    {
        var edit = new CollectionEdit(Stored);

        Assert.Equal("Platinum living dex", edit.Name);
        Assert.Equal(Platinum, edit.MainGame);
        Assert.Equal([Emerald], edit.LinkedGames);
        Assert.Equal(FormSelection.Default, edit.Forms);
        Assert.False(edit.HasChanges);
        Assert.False(edit.CanSave);
    }

    [Fact]
    public void Nothing_touched_is_nothing_to_save()
    {
        var edit = new CollectionEdit(Stored);

        // Setting a field to what it already says is not a change, and neither is trimming.
        edit.Name = "  Platinum living dex  ";
        edit.SetLinked(Emerald, true);

        Assert.False(edit.HasChanges);
    }

    [Fact]
    public void A_new_name_is_a_change_and_is_trimmed_into_the_collection()
    {
        var edit = new CollectionEdit(Stored) { Name = "  Sinnoh  " };

        Assert.True(edit.CanSave);
        Assert.Equal("Sinnoh", edit.Build().Name);
    }

    [Fact]
    public void An_empty_name_is_refused()
    {
        var edit = new CollectionEdit(Stored) { Name = "   " };

        Assert.Contains("Give the collection a name.", edit.Problems);
        Assert.False(edit.CanSave);
        Assert.Throws<InvalidOperationException>(edit.Build);
    }

    [Fact]
    public void Another_collections_name_is_refused_and_its_own_is_not()
    {
        var edit = new CollectionEdit(Stored, ["Emerald dex"]) { Name = "Emerald dex" };
        Assert.Single(edit.Problems);

        edit.Name = "Platinum living dex";
        Assert.Empty(edit.Problems);
    }

    [Fact]
    public void Linking_and_unlinking_show_up_in_what_is_built()
    {
        var edit = new CollectionEdit(Stored);
        edit.SetLinked(FireRed, true);
        edit.SetLinked(Emerald, false);

        Assert.True(edit.CanSave);
        Assert.Equal([FireRed], edit.Build().LinkedGames);
    }

    [Fact]
    public void What_is_being_unlinked_is_the_question_a_screen_has_to_ask()
    {
        var edit = new CollectionEdit(Stored);
        Assert.Empty(edit.Unlinking);

        edit.SetLinked(Emerald, false);
        Assert.Equal([Emerald], edit.Unlinking);

        // Adding one was never linked to begin with, so it is not being taken away.
        edit.SetLinked(FireRed, true);
        Assert.Equal([Emerald], edit.Unlinking);
    }

    [Fact]
    public void The_main_game_cannot_be_linked_to_itself()
    {
        var edit = new CollectionEdit(Stored);
        edit.SetLinked(Platinum, true);

        Assert.Contains("The main game feeds itself; it does not need to be linked.", edit.Problems);
    }

    [Fact]
    public void The_id_the_main_game_and_the_archive_date_survive_an_edit()
    {
        var archived = Stored with { ArchivedOn = new DateOnly(2026, 9, 26) };
        var edit = new CollectionEdit(archived) { Name = "Renamed" };

        var built = edit.Build();

        Assert.Equal(archived.Id, built.Id);
        Assert.Equal(Platinum, built.MainGame);
        Assert.Equal(archived.ArchivedOn, built.ArchivedOn);
    }

    [Fact]
    public void Changing_the_forms_is_a_change()
    {
        var edit = new CollectionEdit(Stored) { Forms = FormSelection.All };

        Assert.True(edit.CanSave);
        Assert.Equal(FormSelection.All, edit.Build().Forms);
    }
}
