using LivingDex.Core.Reference;

namespace LivingDex.Core.UserData;

/// <summary>
/// The capture records of one collection, keyed by what they are about.
/// </summary>
/// <remarks>
/// The data file keeps every collection's records in one flat list, because they are saved as a
/// unit. A screen only ever shows one collection and asks per entry, so it needs the other shape.
/// Built once per screen rather than searched per tile: a National Dex grid asks a thousand
/// times, and a list scan would make that a thousand scans of the whole file's records.
/// </remarks>
public sealed class CaptureIndex
{
    private readonly Dictionary<DexTarget, CaptureRecord> _byTarget;

    private CaptureIndex(Dictionary<DexTarget, CaptureRecord> byTarget) => _byTarget = byTarget;

    /// <summary>Nothing recorded. What a collection starts as.</summary>
    public static CaptureIndex Empty { get; } = new([]);

    /// <summary>
    /// The records belonging to <paramref name="collection"/>, indexed. Records of other
    /// collections are skipped.
    /// </summary>
    public static CaptureIndex For(DexCollectionId collection, IEnumerable<CaptureRecord> records)
    {
        ArgumentNullException.ThrowIfNull(records);

        var byTarget = new Dictionary<DexTarget, CaptureRecord>();

        foreach (var record in records.Where(record => record.Collection == collection))
        {
            // Last one wins. Two records for one target should not happen, and the validator
            // reports it, but a hand-edited file can contain them: the app appends, so the later
            // record is the more recent statement of what the player did.
            byTarget[record.Target] = record;
        }

        return new CaptureIndex(byTarget);
    }

    /// <summary>How many entries this collection has a record for, whatever they say.</summary>
    public int Count => _byTarget.Count;

    /// <summary>
    /// How far along an entry is. An entry with no record at all is
    /// <see cref="CaptureStatus.NotCaught"/>: a fresh collection has no records, and that is not
    /// the same as a missing entry.
    /// </summary>
    public CaptureStatus StatusOf(DexTarget target) =>
        _byTarget.TryGetValue(target, out var record) ? record.Status : CaptureStatus.NotCaught;

    /// <summary>
    /// The record for an entry, or null when there is none. For the note, the catch date and the
    /// holding game, which <see cref="StatusOf"/> deliberately does not carry.
    /// </summary>
    public CaptureRecord? RecordFor(DexTarget target) =>
        _byTarget.TryGetValue(target, out var record) ? record : null;
}
