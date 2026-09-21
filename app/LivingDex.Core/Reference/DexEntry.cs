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
/// <param name="UnobtainableReason">
/// Why this entry cannot be filled in this game, when that is a known fact rather than a gap in
/// the data — an event-only distribution, say. A reason rather than a flag: the validator has to
/// tell "we checked, and it cannot be caught" apart from "we have nothing", and the UI has to be
/// able to say which.
/// </param>
public sealed record DexEntry(
    GameId Game,
    DexTarget Target,
    int Number,
    string? UnobtainableReason = null)
{
    /// <summary>
    /// Whether this entry is known to be unfillable. Derived from
    /// <see cref="UnobtainableReason"/>, so a file cannot claim it without saying why.
    /// </summary>
    [JsonIgnore]
    public bool IsUnobtainable => UnobtainableReason is not null;
}
