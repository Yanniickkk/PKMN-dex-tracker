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
public sealed record DexProgress(int Total, int InMainGame, int CaughtElsewhere)
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

    /// <summary>Counts the entries of a dex by what the player has done about them.</summary>
    public static DexProgress Of(IEnumerable<DexLine> lines, CaptureIndex captures)
    {
        ArgumentNullException.ThrowIfNull(lines);
        ArgumentNullException.ThrowIfNull(captures);

        var total = 0;
        var inMainGame = 0;
        var elsewhere = 0;

        foreach (var line in lines)
        {
            total++;

            switch (captures.StatusOf(line.Target))
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
        }

        return new DexProgress(total, inMainGame, elsewhere);
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
