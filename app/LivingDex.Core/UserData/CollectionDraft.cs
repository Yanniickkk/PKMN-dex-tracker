using LivingDex.Core.Reference;

namespace LivingDex.Core.UserData;

/// <summary>The steps of the collection wizard, in order.</summary>
public enum CollectionWizardStep
{
    /// <summary>What to call it, and which game it is for.</summary>
    NameAndMainGame = 0,

    /// <summary>Which games the player owns that can feed it.</summary>
    LinkedGames = 1,

    /// <summary>How finely it counts forms.</summary>
    Forms = 2,
}

/// <summary>
/// A collection being filled in, one step at a time.
/// </summary>
/// <remarks>
/// Deliberately free of any UI: the wizard screen renders this and calls into it, which keeps
/// the rules about what a valid collection is testable without a browser. A step reports what is
/// wrong with it rather than just whether it is wrong, so the screen can say so.
/// </remarks>
public sealed class CollectionDraft
{
    private readonly HashSet<GameId> _linkedGames = [];
    private readonly HashSet<string> _takenNames;

    /// <param name="existingNames">
    /// Names already in use. Two collections called "Living dex" would be a coin toss every time
    /// the player picks one.
    /// </param>
    public CollectionDraft(IEnumerable<string>? existingNames = null) =>
        _takenNames = new HashSet<string>(existingNames ?? [], StringComparer.OrdinalIgnoreCase);

    /// <summary>The step the player is on.</summary>
    public CollectionWizardStep Step { get; private set; } = CollectionWizardStep.NameAndMainGame;

    /// <summary>What the player calls it.</summary>
    public string Name { get; set; } = string.Empty;

    /// <summary>The game the dex is built from, or null until one is picked.</summary>
    public GameId? MainGame { get; set; }

    /// <summary>Which kinds of form get their own entry.</summary>
    public FormSelection Forms { get; set; } = FormSelection.Default;

    /// <summary>The games chosen as feeders, in a stable order.</summary>
    public IReadOnlyCollection<GameId> LinkedGames =>
        [.. _linkedGames.OrderBy(game => game.Value, StringComparer.Ordinal)];

    /// <summary>Whether a game is currently chosen as a feeder.</summary>
    public bool IsLinked(GameId game) => _linkedGames.Contains(game);

    /// <summary>Adds or removes a feeder game.</summary>
    public void SetLinked(GameId game, bool linked)
    {
        if (linked)
        {
            _linkedGames.Add(game);
        }
        else
        {
            _linkedGames.Remove(game);
        }
    }

    /// <summary>True when there is a step before this one.</summary>
    public bool CanGoBack => Step > CollectionWizardStep.NameAndMainGame;

    /// <summary>True when this is the step that finishes the wizard.</summary>
    public bool IsLastStep => Step == CollectionWizardStep.Forms;

    /// <summary>What is wrong with the step the player is on, in the order it should be read.</summary>
    public IReadOnlyList<string> Problems => ProblemsWith(Step);

    /// <summary>True when the current step is complete enough to move on.</summary>
    public bool CanAdvance => Problems.Count == 0;

    /// <summary>True when every step is complete, so the collection can be created.</summary>
    public bool CanCreate => Enum.GetValues<CollectionWizardStep>().All(step => ProblemsWith(step).Count == 0);

    /// <summary>What is wrong with a given step.</summary>
    public IReadOnlyList<string> ProblemsWith(CollectionWizardStep step)
    {
        var problems = new List<string>();

        switch (step)
        {
            case CollectionWizardStep.NameAndMainGame:
                if (string.IsNullOrWhiteSpace(Name))
                {
                    problems.Add("Give the collection a name.");
                }
                else if (_takenNames.Contains(Name.Trim()))
                {
                    problems.Add($"You already have a collection called \"{Name.Trim()}\".");
                }

                if (MainGame is null)
                {
                    problems.Add("Pick the game this dex is for.");
                }

                break;

            case CollectionWizardStep.LinkedGames:
                // None is a perfectly good answer: plenty of people play one game.
                if (MainGame is { } main && _linkedGames.Contains(main))
                {
                    problems.Add("The main game feeds itself; it does not need to be linked.");
                }

                break;

            case CollectionWizardStep.Forms:
                // Every combination is valid, including none at all.
                break;

            default:
                problems.Add("Unknown step.");
                break;
        }

        return problems;
    }

    /// <summary>Moves to the next step, if the current one allows it.</summary>
    public bool GoNext()
    {
        if (IsLastStep || !CanAdvance)
        {
            return false;
        }

        Step++;
        return true;
    }

    /// <summary>Moves back a step. Never validates: going back to fix something must always work.</summary>
    public bool GoBack()
    {
        if (!CanGoBack)
        {
            return false;
        }

        Step--;
        return true;
    }

    /// <summary>
    /// The collection the player has described.
    /// </summary>
    /// <exception cref="InvalidOperationException">Something is still missing; see <see cref="CanCreate"/>.</exception>
    public DexCollection Build()
    {
        if (!CanCreate)
        {
            throw new InvalidOperationException(
                "The collection is not complete: " + string.Join(" ", ProblemsWith(CollectionWizardStep.NameAndMainGame)));
        }

        return new DexCollection(
            DexCollectionId.New(),
            Name.Trim(),
            MainGame!.Value,
            [.. LinkedGames],
            Forms);
    }
}
