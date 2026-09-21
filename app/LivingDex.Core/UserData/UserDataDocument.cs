namespace LivingDex.Core.UserData;

/// <summary>
/// Everything the player owns, in one file. Collections and capture records live together
/// because they are saved and backed up as one unit.
/// </summary>
/// <param name="SchemaVersion">
/// Bumped when the shape changes in a way an older build cannot read. Written so a future
/// version can migrate rather than guess.
/// </param>
/// <param name="Collections">The collections.</param>
/// <param name="Records">Capture records across all collections.</param>
public sealed record UserDataDocument(
    int SchemaVersion,
    IReadOnlyList<DexCollection> Collections,
    IReadOnlyList<CaptureRecord> Records)
{
    /// <summary>The version this build writes.</summary>
    public const int CurrentSchemaVersion = 1;

    /// <summary>What a brand new data file contains.</summary>
    public static UserDataDocument Empty { get; } = new(CurrentSchemaVersion, [], []);
}
