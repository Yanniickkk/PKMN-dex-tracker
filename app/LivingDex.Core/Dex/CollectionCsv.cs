using System.Globalization;
using System.Text;
using LivingDex.Core.Reference;
using LivingDex.Core.UserData;

namespace LivingDex.Core.Dex;

/// <summary>
/// One dex as a spreadsheet.
/// </summary>
/// <remarks>
/// What a player does with this is the whole design: they open it in Excel or LibreOffice, sort
/// it, hand it to somebody, or keep a copy of where they got to. So it is one row per tile of
/// the dex they are looking at, in the order the grid shows them, with the columns a person
/// would want to sort on - and no columns that only mean something inside this app.
///
/// RFC 4180 to the letter: commas between fields, CRLF between rows, a field holding a comma, a
/// quote or a newline wrapped in quotes with its own quotes doubled. A note is free text a
/// player typed, so every one of those really happens.
/// </remarks>
public static class CollectionCsv
{
    /// <summary>The header row, which is also the order the fields are written in.</summary>
    private static readonly string[] Header =
    [
        "Number", "Name", "Form", "Status", "Held in", "Caught on", "Out of reach", "Note",
    ];

    /// <summary>
    /// Writes the dex as CSV text.
    /// </summary>
    /// <param name="lines">The entries to write, in the order they should appear.</param>
    /// <param name="captures">What the player has done about each one.</param>
    /// <param name="mainGameName">The collection's main game, as a player would name it.</param>
    /// <param name="nameOfGame">
    /// What to call a linked game. Passed in because a game's title belongs to the dataset and
    /// this does not read one.
    /// </param>
    /// <param name="isReachable">
    /// Whether anything in the collection can produce an entry, or null to leave the column
    /// empty. Same answer as the figure above the grid, and passed in for the same reason.
    /// </param>
    public static string Of(
        IEnumerable<DexLine> lines,
        CaptureIndex captures,
        string mainGameName,
        Func<GameId, string>? nameOfGame = null,
        Func<DexTarget, bool>? isReachable = null)
    {
        ArgumentNullException.ThrowIfNull(lines);
        ArgumentNullException.ThrowIfNull(captures);
        ArgumentException.ThrowIfNullOrWhiteSpace(mainGameName);

        var csv = new StringBuilder();
        Row(csv, Header);

        foreach (var line in lines)
        {
            var record = captures.RecordFor(line.Target);
            var status = record?.Status ?? CaptureStatus.NotCaught;

            var heldIn = record?.HoldingGame is { } game
                ? nameOfGame?.Invoke(game) ?? game.Value
                : string.Empty;

            Row(
                csv,
                [
                    line.Number.ToString(CultureInfo.InvariantCulture),
                    line.Name,
                    line.FormKind?.ToString() ?? string.Empty,
                    CaptureStatusNames.Of(status, mainGameName, heldIn.Length == 0 ? null : heldIn),
                    heldIn,

                    // ISO, because a date that reads as 03/04 means two different days either
                    // side of the Channel and a spreadsheet will not ask which was meant.
                    record?.CaughtOn?.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture) ?? string.Empty,

                    isReachable is null ? string.Empty : isReachable(line.Target) ? "no" : "yes",
                    record?.Note ?? string.Empty,
                ]);
        }

        return csv.ToString();
    }

    /// <summary>
    /// A suggested file name: the collection, the day, and nothing that needs escaping.
    /// </summary>
    public static string FileNameFor(string collectionName, DateOnly today)
    {
        var safe = new string([.. (collectionName ?? string.Empty).Select(
            character => char.IsLetterOrDigit(character) ? character : '-')]).Trim('-');

        while (safe.Contains("--", StringComparison.Ordinal))
        {
            safe = safe.Replace("--", "-", StringComparison.Ordinal);
        }

        var stamp = today.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);

        return safe.Length == 0 ? $"living-dex-{stamp}.csv" : $"{safe}-{stamp}.csv";
    }

    private static void Row(StringBuilder csv, string[] fields)
    {
        for (var index = 0; index < fields.Length; index++)
        {
            if (index > 0)
            {
                csv.Append(',');
            }

            csv.Append(Escaped(fields[index]));
        }

        csv.Append("\r\n");
    }

    private static string Escaped(string field)
    {
        var needsQuotes =
            field.Contains(',', StringComparison.Ordinal)
            || field.Contains('"', StringComparison.Ordinal)
            || field.Contains('\n', StringComparison.Ordinal)
            || field.Contains('\r', StringComparison.Ordinal)
            // A field that starts or ends with a space keeps it only inside quotes.
            || field != field.Trim();

        return needsQuotes
            ? $"\"{field.Replace("\"", "\"\"", StringComparison.Ordinal)}\""
            : field;
    }
}
