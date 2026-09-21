using System.Text.Json.Serialization;

namespace LivingDex.Core.Reference;

/// <summary>
/// What a dex entry or an acquisition method is about: a species, or one specific form of it.
/// A form target always carries its species, so callers never have to look it up.
/// </summary>
/// <param name="Species">The species.</param>
/// <param name="Form">The form, or null for the base species.</param>
public readonly record struct DexTarget(SpeciesId Species, FormId? Form)
{
    public static DexTarget ForSpecies(SpeciesId species) => new(species, null);

    public static DexTarget ForForm(SpeciesId species, FormId form) => new(species, form);

    /// <summary>Derived from <see cref="Form"/>; not written to disk.</summary>
    [JsonIgnore]
    public bool IsForm => Form is not null;

    public override string ToString() => Form is { } form ? $"{Species}/{form}" : Species.ToString();
}

/// <summary>
/// One line of one game's dex: what it is, and the number it has in that game.
/// </summary>
/// <param name="Game">The game whose dex this line belongs to.</param>
/// <param name="Target">The species or form.</param>
/// <param name="Number">The number in this game's dex, which is not the National Dex number.</param>
public sealed record DexEntry(GameId Game, DexTarget Target, int Number);
