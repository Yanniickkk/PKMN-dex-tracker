namespace LivingDex.Core.UserData;

/// <summary>What became of an attempt to change the data file.</summary>
public enum UpdateOutcome
{
    /// <summary>Written.</summary>
    Saved,

    /// <summary>The change asked for nothing, so nothing was written.</summary>
    NothingToDo,

    /// <summary>
    /// Something else kept writing the file while this was being saved. Nothing was lost, and
    /// nothing was written either.
    /// </summary>
    Conflict,
}

/// <summary>
/// Reading the data file, changing it, and writing it back without losing anyone else's work.
/// </summary>
/// <remarks>
/// Every screen that writes needs the same three lines - load, change, save, and try again if
/// the file moved on in between - and a save is refused rather than merged, so the retry is not
/// optional. Written once here so four screens cannot each get it slightly differently.
/// </remarks>
public static class UserDataEditing
{
    /// <summary>
    /// Applies <paramref name="change"/> to what is on disk and writes the result.
    /// </summary>
    /// <param name="store">The file to change.</param>
    /// <param name="change">
    /// What to do to the document. Called with what the file holds right now, and called again
    /// on the newer version if the save was refused - so it must work from whatever it is given
    /// rather than from what the screen was showing. Returning the document it was handed means
    /// there is nothing to do.
    /// </param>
    /// <param name="attempts">
    /// How many times to read and write before giving up. Twice is enough for a sync client
    /// landing a file at the wrong moment; a third failure means something is writing
    /// continuously, and the player should be told rather than have the app spin.
    /// </param>
    /// <param name="cancellationToken">Cancels the update.</param>
    /// <exception cref="UserDataCorruptException">The file cannot be read.</exception>
    public static async Task<UpdateOutcome> UpdateAsync(
        this UserDataStore store,
        Func<UserDataDocument, UserDataDocument> change,
        int attempts = 3,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(store);
        ArgumentNullException.ThrowIfNull(change);
        ArgumentOutOfRangeException.ThrowIfLessThan(attempts, 1);

        for (var attempt = 0; attempt < attempts; attempt++)
        {
            var snapshot = await store.LoadAsync(cancellationToken).ConfigureAwait(false);
            var changed = change(snapshot.Document);

            // Reference equality on purpose: the caller says "nothing to do" by handing back
            // what it was given. Two documents that merely look alike are still a write the
            // caller asked for.
            if (ReferenceEquals(changed, snapshot.Document))
            {
                return UpdateOutcome.NothingToDo;
            }

            var result = await store.SaveAsync(changed, snapshot.Revision, cancellationToken)
                .ConfigureAwait(false);

            if (result.Status == SaveStatus.Saved)
            {
                return UpdateOutcome.Saved;
            }
        }

        return UpdateOutcome.Conflict;
    }
}
