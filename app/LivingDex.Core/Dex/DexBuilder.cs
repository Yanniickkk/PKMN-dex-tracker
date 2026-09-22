using LivingDex.Core.Dataset;
using LivingDex.Core.Reference;
using LivingDex.Core.UserData;

namespace LivingDex.Core.Dex;

/// <summary>One line of a collection's dex, ready for the grid.</summary>
/// <param name="Target">The species or form this line is for.</param>
/// <param name="Number">
/// The number shown and sorted on: the National Dex number, or this game's own number when the
/// game has no National Dex. A form takes its base species' number.
/// </param>
/// <param name="Name">What to print, for example <c>Vulpix (Alolan)</c>.</param>
/// <param name="FormKind">Which form this is, or null for the base species.</param>
public sealed record DexLine(DexTarget Target, int Number, string Name, FormKind? FormKind)
{
    /// <summary>True when this line is a form rather than the base species.</summary>
    public bool IsForm => Target.IsForm;
}

/// <summary>Thrown when a collection points at something the dataset cannot build a dex from.</summary>
public sealed class DexBuildException : Exception
{
    public DexBuildException()
    {
    }

    public DexBuildException(string message)
        : base(message)
    {
    }

    public DexBuildException(string message, Exception innerException)
        : base(message, innerException)
    {
    }
}

/// <summary>
/// Turns a collection's settings into the list of entries the player is trying to fill.
/// </summary>
public sealed class DexBuilder
{
    private readonly ReferenceData _reference;

    public DexBuilder(ReferenceData reference)
    {
        ArgumentNullException.ThrowIfNull(reference);
        _reference = reference;
    }

    /// <summary>
    /// The entry list for a collection, built from whichever list the main game says is its own.
    /// </summary>
    /// <exception cref="DexBuildException">
    /// The main game is not in the dataset, or it claims a National Dex without saying where
    /// that dex ends.
    /// </exception>
    public IReadOnlyList<DexLine> Build(DexCollection collection) => Build(collection, source: null);

    /// <summary>
    /// The entry list for a collection: the National Dex or the main game's own dex, expanded or
    /// collapsed according to the collection's form selection, ordered by number with each base species
    /// followed by its forms.
    /// </summary>
    /// <param name="collection">The collection to build for.</param>
    /// <param name="source">
    /// Which of the two lists to build, or null for whichever the game itself names. A game with
    /// a National Dex has both: Diamond asks a player for 493 entries and shows a Sinnoh Pokedex
    /// of 151 with its own numbering, and which of the two is on screen is the player's choice
    /// rather than a fact about the game.
    /// </param>
    /// <exception cref="DexBuildException">
    /// The main game is not in the dataset, or it claims a National Dex without saying where
    /// that dex ends.
    /// </exception>
    public IReadOnlyList<DexLine> Build(DexCollection collection, DexSource? source)
    {
        ArgumentNullException.ThrowIfNull(collection);

        var game = _reference.FindGame(collection.MainGame)
            ?? throw new DexBuildException($"No game named {collection.MainGame} in the dataset.");

        var numbers = BaseSpeciesNumbers(game, source ?? game.DexSource);
        var lines = new List<DexLine>(numbers.Count);

        foreach (var (species, number) in numbers)
        {
            var target = DexTarget.ForSpecies(species);
            lines.Add(new DexLine(target, number, _reference.NameOf(target), FormKind: null));

            if (!collection.Forms.Any)
            {
                continue;
            }

            // Ordered by form id so the lines under a species are stable between runs.
            var forms = _reference.FormsOf(species)
                .Where(form => form.Games.Contains(game.Id))
                .Where(form => collection.Forms.Includes(form.Kind))
                .OrderBy(form => form.Id.Value, StringComparer.Ordinal);

            lines.AddRange(forms.Select(form =>
            {
                var formTarget = DexTarget.ForForm(species, form.Id);
                return new DexLine(formTarget, number, _reference.NameOf(formTarget), form.Kind);
            }));
        }

        // Number first, then the base species ahead of its own forms. The per-species form order
        // is already fixed above, and OrderBy is stable, so it survives this sort.
        return [.. lines.OrderBy(line => line.Number).ThenBy(line => line.IsForm)];
    }

    /// <summary>
    /// The species the collection covers and the number each one is shown under.
    /// </summary>
    /// <remarks>
    /// Both dex sources are reduced to one species-to-number map before forms are considered.
    /// A game's own dex may already list forms as separate lines; collapsing them here and then
    /// expanding from the form table keeps the two sources on the same footing, and stops a form
    /// appearing twice when it is both numbered by the game and listed in the form table.
    /// </remarks>
    private Dictionary<SpeciesId, int> BaseSpeciesNumbers(Game game, DexSource source)
    {
        if (source == DexSource.NationalDex)
        {
            var through = game.NationalDexThrough
                ?? throw new DexBuildException(
                    $"{game.Id} builds from the National Dex but does not say which number it ends at.");

            return _reference.Species
                .Where(species => species.NationalDexNumber <= through)
                .ToDictionary(species => species.Id, species => species.NationalDexNumber);
        }

        var numbers = new Dictionary<SpeciesId, int>();

        foreach (var entry in _reference.DexOf(game.Id))
        {
            // A species listed several times, once per form, is shown under its lowest number.
            if (!numbers.TryGetValue(entry.Target.Species, out var existing) || entry.Number < existing)
            {
                numbers[entry.Target.Species] = entry.Number;
            }
        }

        return numbers;
    }
}
