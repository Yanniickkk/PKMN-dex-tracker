using System.Text;
using LivingDex.Core.Reference;
using LivingDex.Core.UserData;

namespace LivingDex.Core.Dex;

/// <summary>
/// Which entries of a dex to show.
/// </summary>
/// <remarks>
/// The switches combine the way a player would expect: the two status switches widen the
/// result, everything else narrows it. Ticking nothing shows the whole dex.
/// </remarks>
public sealed record DexFilter
{
    /// <summary>Nothing ticked: the whole dex.</summary>
    public static DexFilter None { get; } = new();

    /// <summary>Part of a name, ignoring case and accents. Null or blank means no search.</summary>
    public string? Search { get; init; }

    /// <summary>Show entries not obtained anywhere yet.</summary>
    public bool StillToCatch { get; init; }

    /// <summary>Show entries obtained but not yet in the main game.</summary>
    public bool NotYetTransferred { get; init; }

    /// <summary>
    /// Show only entries one of these games has a known way to obtain. Empty asks nothing.
    /// </summary>
    /// <remarks>
    /// A list rather than a single game, and the games widen each other the way the two status
    /// switches do: a collection is the main game plus everything that can feed it, and "what
    /// can I get out of Ruby or Sapphire" is a question a player with both actually has. Ticking
    /// one is the common case and is what this was before it could hold more than one.
    ///
    /// Beware comparing two filters with <c>==</c>: a record holding a collection compares that
    /// collection by reference. Nothing here does, and nothing should start.
    /// </remarks>
    public IReadOnlyList<GameId> AvailableIn { get; init; } = [];

    /// <summary>
    /// Leave out the entries nothing in this collection can produce.
    /// </summary>
    /// <remarks>
    /// Different from ticking every game under <see cref="AvailableIn"/>, which asks the same
    /// question and answers it the other way up: this one narrows a list a player is working
    /// through, rather than being the thing they are looking at. It is what turns "584 entries,
    /// 36 of them impossible here" into the list they can actually act on.
    /// </remarks>
    public bool HideUnreachable { get; init; }

    /// <summary>True when nothing is ticked and nothing is typed.</summary>
    public bool IsEmpty =>
        string.IsNullOrWhiteSpace(Search)
        && !StillToCatch
        && !NotYetTransferred
        && !HideUnreachable
        && AvailableIn.Count == 0;

    /// <summary>
    /// The lines that pass, in the order they came in.
    /// </summary>
    /// <param name="lines">The whole dex.</param>
    /// <param name="captures">What the player has done about each entry.</param>
    /// <param name="isAvailable">
    /// Whether one game has a known way to obtain a target. Passed in rather than looked up
    /// here, so the rules can be tested without a dataset.
    /// </param>
    /// <param name="isReachable">
    /// Whether anything in this collection can produce a target. Required by
    /// <see cref="HideUnreachable"/> and unused otherwise.
    /// </param>
    /// <exception cref="ArgumentNullException">
    /// <see cref="HideUnreachable"/> is set and nothing was passed to answer it. Refused rather
    /// than treated as "everything is reachable", which would quietly show the entries the
    /// player asked to be rid of.
    /// </exception>
    public IReadOnlyList<DexLine> Apply(
        IReadOnlyList<DexLine> lines,
        CaptureIndex captures,
        Func<GameId, DexTarget, bool> isAvailable,
        Func<DexTarget, bool>? isReachable = null)
    {
        ArgumentNullException.ThrowIfNull(lines);
        ArgumentNullException.ThrowIfNull(captures);
        ArgumentNullException.ThrowIfNull(isAvailable);

        if (HideUnreachable)
        {
            ArgumentNullException.ThrowIfNull(isReachable);
        }

        if (IsEmpty)
        {
            return lines;
        }

        var needle = Fold(Search);

        return [.. lines.Where(line =>
            MatchesSearch(line, needle)
            && MatchesStatus(captures.StatusOf(line.Target))
            && MatchesAvailability(line, isAvailable)
            && (!HideUnreachable || isReachable!(line.Target)))];
    }

    /// <summary>
    /// A name reduced to what a player would type: lower case, accents dropped. Without this,
    /// "flabebe" finds nothing and the search looks broken.
    /// </summary>
    /// <remarks>
    /// The accents are mapped by hand rather than by Unicode normalisation. This app runs with
    /// <c>InvariantGlobalization</c>, which keeps the single file small but also makes
    /// <see cref="string.Normalize(NormalizationForm)"/> a no-op: it returns the string
    /// unchanged, so decomposing and dropping the marks would quietly do nothing at all.
    /// </remarks>
    public static string Fold(string? text)
    {
        if (string.IsNullOrWhiteSpace(text))
        {
            return string.Empty;
        }

        var lowered = text.Trim().ToLowerInvariant();
        var builder = new StringBuilder(lowered.Length);

        foreach (var character in lowered)
        {
            var index = Accented.IndexOf(character, StringComparison.Ordinal);
            builder.Append(index < 0 ? character : Plain[index]);
        }

        return builder.ToString();
    }

    /// <summary>Accented letters, paired by position with <see cref="Plain"/>.</summary>
    private const string Accented = "àáâãäåçèéêë"
        + "ìíîïñòóôõöùúûüýÿ";

    private const string Plain = "aaaaaaceeee" + "iiiinooooouuuuyy";

    private static bool MatchesSearch(DexLine line, string needle) =>
        needle.Length == 0
        || Fold(line.Name).Contains(needle, StringComparison.Ordinal)
        // Also the species id, which is already folded and stripped of punctuation. It is what
        // makes "farfetchd" find Farfetch'd and "mrmime" find Mr. Mime.
        || line.Target.Species.Value.Contains(needle, StringComparison.Ordinal);

    private bool MatchesAvailability(DexLine line, Func<GameId, DexTarget, bool> isAvailable)
    {
        // No game ticked is not "show nothing": it is "do not ask about availability at all".
        if (AvailableIn.Count == 0)
        {
            return true;
        }

        return AvailableIn.Any(game => isAvailable(game, line.Target));
    }

    private bool MatchesStatus(CaptureStatus status)
    {
        // Neither ticked is not "show nothing": it is "do not ask about status at all".
        if (!StillToCatch && !NotYetTransferred)
        {
            return true;
        }

        return (StillToCatch && status == CaptureStatus.NotCaught)
            || (NotYetTransferred && status == CaptureStatus.CaughtElsewhere);
    }
}
