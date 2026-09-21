using LivingDex.Core.Reference;
using LivingDex.Core.UserData;

namespace LivingDex.Core.Tests.UserData;

public class CollectionDraftTests
{
    private static readonly GameId Platinum = new("platinum");
    private static readonly GameId Emerald = new("emerald");

    private static CollectionDraft Filled(params string[] existingNames)
    {
        var draft = new CollectionDraft(existingNames)
        {
            Name = "Platinum living dex",
            MainGame = Platinum,
        };

        draft.SetLinked(Emerald, true);
        return draft;
    }

    [Fact]
    public void A_new_draft_starts_on_the_first_step_with_nothing_filled_in()
    {
        var draft = new CollectionDraft();

        Assert.Equal(CollectionWizardStep.NameAndMainGame, draft.Step);
        Assert.False(draft.CanGoBack);
        Assert.False(draft.CanAdvance);
        Assert.False(draft.CanCreate);
    }

    [Fact]
    public void The_first_step_asks_for_both_things_it_needs()
    {
        var draft = new CollectionDraft();

        Assert.Equal(2, draft.Problems.Count);

        draft.Name = "My dex";
        Assert.Single(draft.Problems);

        draft.MainGame = Platinum;
        Assert.Empty(draft.Problems);
        Assert.True(draft.CanAdvance);
    }

    [Fact]
    public void A_name_of_only_spaces_is_not_a_name()
    {
        var draft = new CollectionDraft { Name = "   ", MainGame = Platinum };

        Assert.Contains("Give the collection a name.", draft.Problems);
    }

    [Fact]
    public void A_name_already_in_use_is_refused()
    {
        var draft = new CollectionDraft(["Platinum living dex"])
        {
            Name = "platinum LIVING dex",
            MainGame = Platinum,
        };

        // Case does not make it a different collection to a person reading the list.
        Assert.Contains(draft.Problems, problem => problem.Contains("already have", StringComparison.Ordinal));
    }

    [Fact]
    public void Linking_no_games_at_all_is_a_valid_answer()
    {
        var draft = new CollectionDraft { Name = "One game only", MainGame = Platinum };
        draft.GoNext();

        Assert.Equal(CollectionWizardStep.LinkedGames, draft.Step);
        Assert.Empty(draft.Problems);
    }

    [Fact]
    public void Linking_the_main_game_to_itself_is_refused()
    {
        var draft = new CollectionDraft { Name = "Odd", MainGame = Platinum };
        draft.SetLinked(Platinum, true);
        draft.GoNext();

        Assert.Contains(draft.Problems, problem => problem.Contains("feeds itself", StringComparison.Ordinal));
        Assert.False(draft.CanAdvance);
    }

    [Fact]
    public void A_linked_game_can_be_taken_back_off()
    {
        var draft = new CollectionDraft();

        draft.SetLinked(Emerald, true);
        Assert.True(draft.IsLinked(Emerald));

        draft.SetLinked(Emerald, false);
        Assert.False(draft.IsLinked(Emerald));
        Assert.Empty(draft.LinkedGames);
    }

    [Fact]
    public void Every_form_selection_is_allowed_including_none()
    {
        var draft = Filled();
        draft.GoNext();
        draft.GoNext();

        Assert.Equal(CollectionWizardStep.Forms, draft.Step);

        foreach (var selection in new[] { FormSelection.None, FormSelection.Default, FormSelection.All })
        {
            draft.Forms = selection;
            Assert.Empty(draft.Problems);
        }
    }

    [Fact]
    public void A_step_that_is_not_finished_does_not_let_you_past_it()
    {
        var draft = new CollectionDraft { Name = "No game picked" };

        Assert.False(draft.GoNext());
        Assert.Equal(CollectionWizardStep.NameAndMainGame, draft.Step);
    }

    [Fact]
    public void Going_back_always_works_even_when_the_step_is_broken()
    {
        var draft = Filled();
        draft.GoNext();

        // Break the step you are on; you still have to be able to retreat and fix it.
        draft.SetLinked(Platinum, true);

        Assert.False(draft.CanAdvance);
        Assert.True(draft.GoBack());
        Assert.Equal(CollectionWizardStep.NameAndMainGame, draft.Step);
    }

    [Fact]
    public void The_first_step_has_nothing_to_go_back_to()
    {
        var draft = new CollectionDraft();

        Assert.False(draft.GoBack());
    }

    [Fact]
    public void The_last_step_does_not_advance_any_further()
    {
        var draft = Filled();
        draft.GoNext();
        draft.GoNext();

        Assert.True(draft.IsLastStep);
        Assert.False(draft.GoNext());
        Assert.Equal(CollectionWizardStep.Forms, draft.Step);
    }

    [Fact]
    public void A_finished_draft_becomes_a_collection()
    {
        var draft = Filled();
        draft.Forms = FormSelection.All;

        var collection = draft.Build();

        Assert.Equal("Platinum living dex", collection.Name);
        Assert.Equal(Platinum, collection.MainGame);
        Assert.Equal([Emerald], collection.LinkedGames);
        Assert.Equal(FormSelection.All, collection.Forms);
        Assert.NotEqual(default, collection.Id);
    }

    [Fact]
    public void The_name_is_stored_without_the_spaces_the_player_left_around_it()
    {
        var draft = new CollectionDraft { Name = "  Platinum living dex  ", MainGame = Platinum };

        Assert.Equal("Platinum living dex", draft.Build().Name);
    }

    [Fact]
    public void Two_collections_do_not_share_an_id()
    {
        Assert.NotEqual(Filled().Build().Id, Filled().Build().Id);
    }

    [Fact]
    public void An_unfinished_draft_refuses_to_pretend_it_is_a_collection()
    {
        var draft = new CollectionDraft { Name = "No game picked" };

        Assert.Throws<InvalidOperationException>(draft.Build);
    }
}
