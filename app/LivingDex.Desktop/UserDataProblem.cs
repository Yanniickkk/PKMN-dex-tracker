using LivingDex.Core.UserData;

namespace LivingDex.Desktop;

/// <summary>
/// What to tell the player when their data file cannot be read or written.
/// </summary>
/// <remarks>
/// One place rather than one per screen. Five screens read the file and every one of them used
/// to write its own sentence, which is how "your data file could not be read" ended up being
/// what a player saw when a sync client had the file for half a second.
///
/// Three things belong in every one of these: what happened, which file, and what to do about
/// it. The last one is the part a message without it leaves a player to guess at.
/// </remarks>
/// <param name="Headline">What happened, in one line.</param>
/// <param name="Detail">The exception's own account, which names the file.</param>
/// <param name="Advice">What to do about it, or null when there is nothing useful to say.</param>
public sealed record UserDataProblem(string Headline, string Detail, string? Advice)
{
    /// <summary>
    /// Turns a failure from <see cref="UserDataStore"/> into something worth reading.
    /// </summary>
    /// <param name="exception">What was thrown.</param>
    /// <param name="backupDirectory">
    /// Where the rolling backups are, when the caller knows. It is the only way back from a file
    /// that really is broken, so it is worth naming.
    /// </param>
    public static UserDataProblem From(Exception exception, string? backupDirectory = null)
    {
        ArgumentNullException.ThrowIfNull(exception);

        return exception switch
        {
            UserDataBusyException busy => new UserDataProblem(
                "Your data file is in use right now.",
                busy.Message,
                "A sync client or another program has it open; nothing has been changed. "
                + "Close it, or try again in a moment."),

            UserDataCorruptException corrupt => new UserDataProblem(
                "Your data file could not be read.",
                corrupt.Message,
                string.IsNullOrEmpty(backupDirectory)
                    ? "Nothing has been changed, and nothing will be written to it until it can be read."
                    : $"Nothing has been written to it. Every previous version is kept in {backupDirectory}."),

            _ => new UserDataProblem(
                "Something went wrong with your data file.",
                exception.Message,
                null),
        };
    }

    /// <summary>
    /// The whole thing as one line, for the places with room for a sentence rather than a
    /// notice. The headline is left out there: it is a label for the notice's first line, and
    /// inline it would only say the detail again.
    /// </summary>
    public string Sentence => Advice is null ? Detail : $"{Detail} {Advice}";

    /// <summary>Whether this is one of the failures this class has something useful to say about.</summary>
    public static bool IsAboutTheFile(Exception exception) =>
        exception is UserDataBusyException or UserDataCorruptException;
}
