using LivingDex.Core.Dataset;
using LivingDex.Core.Reference;

namespace LivingDex.Core.Dex;

/// <summary>
/// The path taken while drilling down a chain of entries, newest last.
/// </summary>
/// <remarks>
/// Kept as a path rather than a single "current entry" so the popup can show where the player
/// came from and let them step back up. It is not browser history: it only ever holds one route
/// down a chain, and walking back to an entry already on it folds the path rather than
/// lengthening it, so an evolution that loops cannot grow it without end.
/// </remarks>
public sealed class DexTrail
{
    private readonly List<DexLine> _steps;

    private DexTrail(DexLine start) => _steps = [start];

    /// <summary>A trail of one: the entry the player opened.</summary>
    public static DexTrail StartingAt(DexLine line)
    {
        ArgumentNullException.ThrowIfNull(line);
        return new DexTrail(line);
    }

    /// <summary>Every step, in the order they were taken.</summary>
    public IReadOnlyList<DexLine> Steps => _steps;

    /// <summary>The entry on screen.</summary>
    public DexLine Current => _steps[^1];

    /// <summary>Whether there is anywhere to go back to.</summary>
    public bool CanGoBack => _steps.Count > 1;

    /// <summary>
    /// Steps down to another entry. An entry already on the trail is returned to rather than
    /// added again.
    /// </summary>
    public void GoTo(DexLine line)
    {
        ArgumentNullException.ThrowIfNull(line);

        var existing = _steps.FindIndex(step => step.Target == line.Target);
        if (existing >= 0)
        {
            TruncateTo(existing);
            return;
        }

        _steps.Add(line);
    }

    /// <summary>Steps back up one. Does nothing at the start of the trail.</summary>
    public void Back()
    {
        if (CanGoBack)
        {
            _steps.RemoveAt(_steps.Count - 1);
        }
    }

    /// <summary>
    /// Jumps back to one step, dropping everything after it. What a breadcrumb click does.
    /// An index outside the trail is ignored rather than throwing: it can only come from a
    /// stale render.
    /// </summary>
    public void TruncateTo(int index)
    {
        if (index < 0 || index >= _steps.Count - 1)
        {
            return;
        }

        _steps.RemoveRange(index + 1, _steps.Count - index - 1);
    }
}

/// <summary>Makes a dex line for an entry the dex itself does not contain.</summary>
public static class DexLines
{
    /// <summary>
    /// The line to show for an entry that is not in the collection's dex.
    /// </summary>
    /// <remarks>
    /// Drilling down a chain can reach one: a baby Pokemon the main game's dex does not list, or
    /// a form the player has switched off. Refusing to show it would break the chain exactly
    /// where it is most worth reading, so a line is made from the reference tables instead. The
    /// number is the National Dex number, which is the only number such an entry has.
    /// </remarks>
    public static DexLine For(ReferenceData reference, DexTarget target)
    {
        ArgumentNullException.ThrowIfNull(reference);

        var form = target.Form is { } id
            ? reference.FormsOf(target.Species).FirstOrDefault(one => one.Id == id)
            : null;

        return new DexLine(
            target,
            reference.FindSpecies(target.Species)?.NationalDexNumber ?? 0,
            reference.NameOf(target),
            form?.Kind);
    }
}
