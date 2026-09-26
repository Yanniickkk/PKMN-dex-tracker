using LivingDex.Core.Reference;

namespace LivingDex.Core.UserData;

/// <summary>
/// Changing what a document says about a whole collection: its settings, and whether it is in
/// use, archived, or gone.
/// </summary>
/// <remarks>
/// Beside <see cref="CaptureEditing"/>, which does the same for one entry, and for the same
/// reason: the rules about what may change, and what changing it would cost the records, belong
/// to the data rather than to the screen that draws a button.
///
/// Three of those rules are worth stating here, because every method below is one of them:
/// the main game never changes, a linked game may not be taken away while it still holds
/// something, and a collection is archived before it can be deleted.
/// </remarks>
public static class CollectionEditing
{
    /// <summary>One collection by id, or null when the document has no such collection.</summary>
    public static DexCollection? CollectionWith(this UserDataDocument document, DexCollectionId id)
    {
        ArgumentNullException.ThrowIfNull(document);

        return document.Collections.FirstOrDefault(one => one.Id == id);
    }

    /// <summary>The collections still in use, in the order they were created.</summary>
    public static IReadOnlyList<DexCollection> InUse(this UserDataDocument document)
    {
        ArgumentNullException.ThrowIfNull(document);

        return [.. document.Collections.Where(one => !one.IsArchived)];
    }

    /// <summary>
    /// The collections that have been put away, most recently archived first.
    /// </summary>
    /// <remarks>
    /// Newest first because the archive is read to find something that was just put away far
    /// more often than something from a year ago. Ties keep the order they are stored in, which
    /// is the order they were created.
    /// </remarks>
    public static IReadOnlyList<DexCollection> ArchivedCollections(this UserDataDocument document)
    {
        ArgumentNullException.ThrowIfNull(document);

        return
        [
            .. document.Collections
                .Where(one => one.IsArchived)
                .OrderByDescending(one => one.ArchivedOn!.Value),
        ];
    }

    /// <summary>How many records this collection has, whatever they say.</summary>
    public static int RecordCountOf(this UserDataDocument document, DexCollectionId id)
    {
        ArgumentNullException.ThrowIfNull(document);

        return document.Records.Count(record => record.Collection == id);
    }

    /// <summary>
    /// What this collection still has sitting in one game.
    /// </summary>
    /// <remarks>
    /// The question a linked game has to answer before it can be unlinked. Unlinking a game that
    /// holds twelve Pokémon would leave twelve records pointing at a game the collection no
    /// longer knows about: the grid would show them as caught somewhere it cannot name, and the
    /// route that was going to bring them home is gone from the screen that explains it. So the
    /// player is asked to transfer them first, and this is what the asking is based on.
    /// </remarks>
    public static IReadOnlyList<CaptureRecord> StillHeldIn(
        this UserDataDocument document,
        DexCollectionId collection,
        GameId game)
    {
        ArgumentNullException.ThrowIfNull(document);

        return
        [
            .. document.Records.Where(record =>
                record.Collection == collection
                && record.Status != CaptureStatus.NotCaught
                && record.HoldingGame == game),
        ];
    }

    /// <summary>
    /// The games this collection holds something in that <paramref name="collection"/> does not
    /// list, main game or linked. Empty is what a consistent collection looks like.
    /// </summary>
    public static IReadOnlyList<GameId> GamesLeftHolding(
        this UserDataDocument document,
        DexCollection collection)
    {
        ArgumentNullException.ThrowIfNull(document);
        ArgumentNullException.ThrowIfNull(collection);

        var known = new HashSet<GameId>(collection.LinkedGames) { collection.MainGame };

        return
        [
            .. document.Records
                .Where(record =>
                    record.Collection == collection.Id
                    && record.Status != CaptureStatus.NotCaught
                    && record.HoldingGame is { } game
                    && !known.Contains(game))
                .Select(record => record.HoldingGame!.Value)
                .Distinct(),
        ];
    }

    /// <summary>
    /// The document with <paramref name="collection"/> in place of the one it has under that id.
    /// </summary>
    /// <remarks>
    /// The last line of defence rather than the first: a screen asks before it offers, and this
    /// refuses anyway, because the file can have moved on between the asking and the saving.
    /// </remarks>
    /// <exception cref="ArgumentException">There is no collection with that id.</exception>
    /// <exception cref="InvalidOperationException">
    /// The main game changed, the collection is archived, or a game it dropped still holds
    /// something.
    /// </exception>
    public static UserDataDocument WithCollection(
        this UserDataDocument document,
        DexCollection collection)
    {
        ArgumentNullException.ThrowIfNull(document);
        ArgumentNullException.ThrowIfNull(collection);

        var stored = document.CollectionWith(collection.Id)
            ?? throw new ArgumentException(
                $"This file has no collection {collection.Id}.", nameof(collection));

        // Every record in the file is read against the main game: a holding game equal to it
        // means "done" and anything else means "still to transfer". Change it and every record
        // at once quietly means something else, and the routes that made the old main game
        // reachable may not exist from the new one. A second collection costs nothing.
        if (collection.MainGame != stored.MainGame)
        {
            throw new InvalidOperationException(
                "A collection's main game cannot be changed. Make a second collection instead.");
        }

        if (stored.IsArchived)
        {
            throw new InvalidOperationException(
                "An archived collection cannot be edited. Restore it first.");
        }

        if (collection.ArchivedOn != stored.ArchivedOn)
        {
            throw new InvalidOperationException(
                "Archiving is not an edit; use Archive and Restore.");
        }

        foreach (var dropped in stored.LinkedGames.Where(game => !collection.LinkedGames.Contains(game)))
        {
            var held = document.StillHeldIn(collection.Id, dropped);
            if (held.Count > 0)
            {
                throw new InvalidOperationException(
                    $"{dropped.Value} still holds {held.Count} of this collection's Pokémon. "
                    + "Transfer them first.");
            }
        }

        return document with
        {
            Collections = [.. document.Collections.Select(one => one.Id == collection.Id ? collection : one)],
        };
    }

    /// <summary>The document with that collection put away, dated <paramref name="day"/>.</summary>
    /// <remarks>
    /// Nothing else changes: the records stay exactly where they are, because an archived
    /// collection is one that can come back. Archiving something already archived leaves the
    /// original date alone rather than restamping it.
    /// </remarks>
    /// <exception cref="ArgumentException">There is no collection with that id.</exception>
    public static UserDataDocument Archived(
        this UserDataDocument document,
        DexCollectionId id,
        DateOnly day)
    {
        ArgumentNullException.ThrowIfNull(document);

        var stored = document.CollectionWith(id)
            ?? throw new ArgumentException($"This file has no collection {id}.", nameof(id));

        return stored.IsArchived
            ? document
            : document.Replace(stored with { ArchivedOn = day });
    }

    /// <summary>The document with that collection back in use.</summary>
    /// <exception cref="ArgumentException">There is no collection with that id.</exception>
    public static UserDataDocument Restored(this UserDataDocument document, DexCollectionId id)
    {
        ArgumentNullException.ThrowIfNull(document);

        var stored = document.CollectionWith(id)
            ?? throw new ArgumentException($"This file has no collection {id}.", nameof(id));

        return stored.IsArchived ? document.Replace(stored with { ArchivedOn = null }) : document;
    }

    /// <summary>
    /// The document without that collection, and without the records that belonged to it.
    /// </summary>
    /// <remarks>
    /// The one thing here that cannot be undone, which is why it is only reachable from the
    /// archive: a collection has to have been put away, deliberately, before this can be asked
    /// for at all. The records go with it because a record names its collection and nothing
    /// else: left behind, they would be rows no screen can show and no player can reach.
    /// </remarks>
    /// <exception cref="ArgumentException">There is no collection with that id.</exception>
    /// <exception cref="InvalidOperationException">It has not been archived.</exception>
    public static UserDataDocument Without(this UserDataDocument document, DexCollectionId id)
    {
        ArgumentNullException.ThrowIfNull(document);

        var stored = document.CollectionWith(id)
            ?? throw new ArgumentException($"This file has no collection {id}.", nameof(id));

        if (!stored.IsArchived)
        {
            throw new InvalidOperationException(
                "A collection is archived before it is deleted, so that deleting is never the "
                + "first thing a stray click does.");
        }

        return document with
        {
            Collections = [.. document.Collections.Where(one => one.Id != id)],
            Records = [.. document.Records.Where(record => record.Collection != id)],
        };
    }

    private static UserDataDocument Replace(this UserDataDocument document, DexCollection collection) =>
        document with
        {
            Collections = [.. document.Collections.Select(one => one.Id == collection.Id ? collection : one)],
        };
}
