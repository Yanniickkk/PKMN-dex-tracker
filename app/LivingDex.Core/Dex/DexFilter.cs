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

    /// <summary>Show only entries the main game has a known way to obtain.</summary>
    public bool AvailableInMainGame { get; init; }

    /// <summary>True when nothing is ticked and nothing is typed.</summary>
    public bool IsEmpty =>
        string.IsNullOrWhiteSpace(Search)
        && !StillToCatch
        && !NotYetTransferred
        && !AvailableInMainGame;

    /// <summary>
    /// The lines that pass, in the order they came in.
    /// </summary>
    /// <param name="lines">The whole dex.</param>
    /// <param name="captures">What the player has done about each entry.</param>
    /// <param name="isAvailable">
    /// Whether the main game has a known way to obtain a target. Passed in rather than looked up
    /// here, so the rules can be tested without a dataset.
    /// </param>
    public IReadOnlyList<DexLine> Apply(
        IReadOnlyList<DexLine> lines,
        CaptureIndex captures,
        Func<DexTarget, bool> isAvailable)
    {
        ArgumentNullException.ThrowIfNull(lines);
        ArgumentNullException.ThrowIfNull(captures);
        ArgumentNullException.ThrowIfNull(isAvailable);

        if (IsEmpty)
        {
            return lines;
        }

        var needle = Fold(Search);

        return [.. lines.Where(line =>
            MatchesSearch(line, needle)
            && MatchesStatus(captures.StatusOf(line.Target))
            && (!AvailableInMainGame || isAvailable(line.Target)))];
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
