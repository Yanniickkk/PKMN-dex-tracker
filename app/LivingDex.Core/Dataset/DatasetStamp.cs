namespace LivingDex.Core.Dataset;

/// <summary>
/// Identifies the dataset build the app is running against. The pipeline writes this
/// alongside the data (Phase 0.6) and the UI surfaces it (Phase 3), so a bug report can
/// name the exact data it came from.
/// </summary>
/// <param name="Version">Dataset version, e.g. <c>1.4.0</c>.</param>
/// <param name="BuiltOn">The day the pipeline produced this dataset.</param>
public sealed record DatasetStamp(string Version, DateOnly BuiltOn)
{
    public override string ToString() => $"{Version} ({BuiltOn:yyyy-MM-dd})";
}
