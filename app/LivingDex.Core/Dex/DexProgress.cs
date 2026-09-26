using LivingDex.Core.Reference;
using LivingDex.Core.UserData;

namespace LivingDex.Core.Dex;

/// <summary>
/// How far along a collection is.
/// </summary>
/// <remarks>
/// Counted over the dex the collection actually shows, not over the records in the file. A file
/// keeps records the current dex has no line for — a form the player has since switched off, or
/// one caught before the main game changed — and counting those would put the total out of reach
/// or push it past the end.
/// </remarks>
/// <param name="Total">Entries in the dex.</param>
/// <param name="InMainGame">Entries sitting in the main game. This is what "done" means.</param>
/// <param name="CaughtElsewhere">Entries obtained but still in a linked game.</param>
/// <param name="Unreachable">
/// Entries still to get that nothing in this collection can produce.
/// </param>
public sealed record DexProgress(int Total, int InMainGame, int CaughtElsewhere, int Unreachable = 0)
{
    /// <summary>An empty dex.</summary>
    public static DexProgress Empty { get; } = new(0, 0, 0);

    /// <summary>Entries not obtained anywhere yet.</summary>
    public int NotCaught => Total - InMainGame - CaughtElsewhere;

    /// <summary>Entries obtained, wherever they are.</summary>
    public int Caught => InMainGame + CaughtElsewhere;

    /// <summary>True when every entry is in the main game.</summary>
    public bool IsComplete => Total > 0 && InMainGame == Total;

    /// <summary>
    /// How far along, as a whole percent.
    /// </summary>
    /// <remarks>
    /// Never rounds up to 100 while anything is left, and never down to 0 once something is
    /// done: a dex of 1025 that says "100%" with one Pokémon missing is the single most
    /// annoying thing a tracker can do.
    /// </remarks>
    public int PercentComplete => Fraction(InMainGame);

    /// <summary>The same figure for everything obtained, main game or not.</summary>
    public int PercentCaught => Fraction(Caught);

    /// <summary>
    /// Counts the entries of a dex by what the player has done about them.
    /// </summary>
    /// <param name="lines">The dex on screen.</param>
    /// <param name="captures">What the player has done about each entry.</param>
    /// <param name="isReachable">
    /// Whether anything in this collection has a way to produce an entry. Passed in rather than
    /// worked out here, so the figure and the "Available in" filter beside it can never give
    /// different answers about the same entry, and so this stays testable without a dataset.
    /// Null asks nothing, and <see cref="Unreachable"/> is then zero.
    /// </param>
    /// <remarks>
    /// The unreachable ones stay in <see cref="Total"/>. They are entries of this game's dex,
    /// and a total that quietly left out the awkward ones would be a different number wearing
    /// the dex's name. They are counted separately so the screen can say what the percentage
    /// cannot: that some of what is left is not a matter of playing longer.
    ///
    /// Only what is still to get is counted: an entry sitting in the main game is done, however
    /// it got there. A Mew from a 2006 distribution is somebody's Mew, not a hole in their dex.
    /// </remarks>
    public static DexProgress Of(
        IEnumerable<DexLine> lines,
        CaptureIndex captures,
        Func<DexTarget, bool>? isReachable = null)
    {
        ArgumentNullException.ThrowIfNull(lines);
        ArgumentNullException.ThrowIfNull(captures);

        var total = 0;
        var inMainGame = 0;
        var elsewhere = 0;
        var unreachable = 0;

        foreach (var line in lines)
        {
            total++;
            var status = captures.StatusOf(line.Target);

            switch (status)
            {
                case CaptureStatus.InMainGame:
                    inMainGame++;
                    break;
                case CaptureStatus.CaughtElsewhere:
                    elsewhere++;
                    break;
                default:
                    break;
            }

            if (status != CaptureStatus.InMainGame && isReachable?.Invoke(line.Target) == false)
            {
                unreachable++;
            }
        }

        return new DexProgress(total, inMainGame, elsewhere, unreachable);
    }

    private int Fraction(int part)
    {
        if (Total <= 0 || part <= 0)
        {
            return 0;
        }

        if (part >= Total)
        {
            return 100;
        }

        return Math.Clamp((int)Math.Round(part * 100.0 / Total, MidpointRounding.AwayFromZero), 1, 99);
    }
}
