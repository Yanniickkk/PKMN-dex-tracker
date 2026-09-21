using LivingDex.Core.Reference;

namespace LivingDex.Core.UserData;

/// <summary>
/// Changing what a document says about one entry.
/// </summary>
/// <remarks>
/// Here rather than in the screen that edits it: the rules about what a record means when it is
/// empty, and about there being one record per entry, belong to the data.
/// </remarks>
public static class CaptureEditing
{
    /// <summary>
    /// The document with <paramref name="record"/> in place of whatever it said about that entry.
    /// </summary>
    /// <remarks>
    /// A record that says nothing - not caught, no date, no note - is removed rather than
    /// stored. The file should not grow by one line every time a tile is clicked and unclicked,
    /// and an absent record already means "not caught".
    /// Any duplicates for the same entry collapse into the one being written, which is how a
    /// hand-edited file gets tidied up by being used.
    /// </remarks>
    public static UserDataDocument WithRecord(this UserDataDocument document, CaptureRecord record)
    {
        ArgumentNullException.ThrowIfNull(document);
        ArgumentNullException.ThrowIfNull(record);

        var others = document.Records
            .Where(one => one.Collection != record.Collection || one.Target != record.Target)
            .ToList();

        if (SaysNothing(record))
        {
            return document with { Records = others };
        }

        others.Add(record);
        return document with { Records = others };
    }

    /// <summary>
    /// The record moved to another state, with the holding game and the catch date brought in
    /// line with it.
    /// </summary>
    /// <param name="record">What is stored now.</param>
    /// <param name="status">Where the entry should be.</param>
    /// <param name="mainGame">The collection's main game.</param>
    /// <param name="elsewhereGame">
    /// Which linked game to assume when moving to <see cref="CaptureStatus.CaughtElsewhere"/>
    /// and no other game is recorded. Null when the collection has none, in which case that move
    /// is refused and the record comes back unchanged.
    /// </param>
    /// <param name="today">
    /// The date to stamp a fresh catch with. Passed in rather than read from the clock, so the
    /// rule is testable and so "today" is decided once per action rather than per field.
    /// </param>
    public static CaptureRecord WithStatus(
        this CaptureRecord record,
        CaptureStatus status,
        GameId mainGame,
        GameId? elsewhereGame,
        DateOnly today)
    {
        ArgumentNullException.ThrowIfNull(record);

        GameId? holding;

        switch (status)
        {
            case CaptureStatus.InMainGame:
                holding = mainGame;
                break;

            case CaptureStatus.CaughtElsewhere:
                // Keep the game it is already in, unless that is the main game it is leaving.
                holding = record.HoldingGame is { } held && held != mainGame ? held : elsewhereGame;
                if (holding is null)
                {
                    return record;
                }

                break;

            default:
                holding = null;
                break;
        }

        return record with
        {
            Status = status,
            HoldingGame = holding,
            // Catching something dates it today unless a date is already recorded; going back to
            // not caught keeps whatever date was there, because that is the player's note about
            // when it happened and an accidental click must not erase it.
            CaughtOn = status == CaptureStatus.NotCaught ? record.CaughtOn : record.CaughtOn ?? today,
        };
    }

    /// <summary>The record for one entry, or null.</summary>
    public static CaptureRecord? RecordFor(
        this UserDataDocument document,
        DexCollectionId collection,
        DexTarget target)
    {
        ArgumentNullException.ThrowIfNull(document);

        return document.Records.LastOrDefault(
            record => record.Collection == collection && record.Target == target);
    }

    private static bool SaysNothing(CaptureRecord record) =>
        record.Status == CaptureStatus.NotCaught
        && record.CaughtOn is null
        && string.IsNullOrWhiteSpace(record.Note);
}
