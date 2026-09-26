using LivingDex.Core.Reference;

namespace LivingDex.Core.UserData;

/// <summary>
/// A collection being changed: its name, which games feed it, and how finely it counts forms.
/// </summary>
/// <remarks>
/// The counterpart of <see cref="CollectionDraft"/> for a collection that already exists, and
/// not a wizard: a player editing something is looking for one field, and three steps to reach
/// it would be three steps in the way.
///
/// <b>The main game is not here and there is no setter for it.</b> It is the thing every record
/// in the file is read against - a holding game equal to it means the entry is done, and
/// anything else means it is still to transfer - so changing it would silently reinterpret every
/// record the collection has at once, and the routes that made the old main game reachable might
/// not exist from the new one. A second collection costs nothing; a hundred misread records
/// cannot be undone.
///
/// <b>A linked game may be taken away only when it holds nothing.</b> The rule is enforced when
/// the document is written, by <see cref="CollectionEditing.WithCollection"/>; what this class
/// gives a screen is the chance to ask first, with <see cref="Unlinking"/>.
/// </remarks>
public sealed class CollectionEdit
{
    private readonly DexCollection _stored;
    private readonly HashSet<GameId> _linkedGames;
    private readonly HashSet<string> _takenNames;

    /// <param name="stored">The collection as the data file holds it.</param>
    /// <param name="otherNames">
    /// The names of every other collection, archived ones included. Archived names stay taken
    /// because an archived collection can come back, and restoring it must never be the moment
    /// two collections turn out to share a name.
    /// </param>
    public CollectionEdit(DexCollection stored, IEnumerable<string>? otherNames = null)
    {
        ArgumentNullException.ThrowIfNull(stored);

        _stored = stored;
        _linkedGames = [.. stored.LinkedGames];
        _takenNames = new HashSet<string>(otherNames ?? [], StringComparer.OrdinalIgnoreCase);

        Name = stored.Name;
        Forms = stored.Forms;
    }

    /// <summary>Which collection this is.</summary>
    public DexCollectionId Id => _stored.Id;

    /// <summary>The game the dex is built from. Read-only, and the remarks say why.</summary>
    public GameId MainGame => _stored.MainGame;

    /// <summary>What the player calls it.</summary>
    public string Name { get; set; }

    /// <summary>Which kinds of form get their own entry.</summary>
    public FormSelection Forms { get; set; }

    /// <summary>The games chosen as feeders, in a stable order.</summary>
    public IReadOnlyList<GameId> LinkedGames =>
        [.. _linkedGames.OrderBy(game => game.Value, StringComparer.Ordinal)];

    /// <summary>Whether a game is currently chosen as a feeder.</summary>
    public bool IsLinked(GameId game) => _linkedGames.Contains(game);

    /// <summary>The games that were linked when this was opened and are not any more.</summary>
    public IReadOnlyList<GameId> Unlinking =>
        [.. _stored.LinkedGames.Where(game => !_linkedGames.Contains(game))];

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

    /// <summary>True when anything has actually been changed.</summary>
    /// <remarks>
    /// So that Save can be offered rather than always lit, and so a screen that was only looked
    /// at writes nothing: every write rotates a backup, and a file full of identical backups
    /// hides the version someone actually wants back.
    /// </remarks>
    public bool HasChanges =>
        Name.Trim() != _stored.Name
        || Forms != _stored.Forms
        || !LinkedGames.SequenceEqual(_stored.LinkedGames.OrderBy(game => game.Value, StringComparer.Ordinal));

    /// <summary>What is wrong with it, in the order it should be read.</summary>
    public IReadOnlyList<string> Problems
    {
        get
        {
            var problems = new List<string>();

            if (string.IsNullOrWhiteSpace(Name))
            {
                problems.Add("Give the collection a name.");
            }
            else if (_takenNames.Contains(Name.Trim()))
            {
                problems.Add($"You already have a collection called \"{Name.Trim()}\".");
            }

            if (_linkedGames.Contains(MainGame))
            {
                problems.Add("The main game feeds itself; it does not need to be linked.");
            }

            return problems;
        }
    }

    /// <summary>True when what is on screen can be written.</summary>
    public bool CanSave => HasChanges && Problems.Count == 0;

    /// <summary>
    /// The collection as edited. The id, the main game and the archive date are the stored ones:
    /// this screen does not touch any of the three.
    /// </summary>
    /// <exception cref="InvalidOperationException">Something is still wrong; see <see cref="Problems"/>.</exception>
    public DexCollection Build()
    {
        if (Problems.Count > 0)
        {
            throw new InvalidOperationException(
                "The collection is not valid: " + string.Join(" ", Problems));
        }

        return _stored with
        {
            Name = Name.Trim(),
            LinkedGames = [.. LinkedGames],
            Forms = Forms,
        };
    }
}
