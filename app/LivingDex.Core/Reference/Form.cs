namespace LivingDex.Core.Reference;

/// <summary>
/// What kind of form this is. The collection settings decide which kinds are expanded into
/// their own dex entries.
/// </summary>
public enum FormKind
{
    /// <summary>Alolan, Galarian, Hisuian, Paldean.</summary>
    Regional,

    /// <summary>Changes stats, typing or ability, for example Rotom's appliances.</summary>
    Functional,

    /// <summary>Appearance only, for example Vivillon patterns.</summary>
    Cosmetic,

    /// <summary>A visible male/female difference.</summary>
    Gender,
}

/// <summary>
/// A form of a species.
/// </summary>
/// <param name="Id">Stable id, for example <c>vulpix-alola</c>.</param>
/// <param name="Species">The species this is a form of.</param>
/// <param name="Name">Display name of the form, for example <c>Alolan</c>.</param>
/// <param name="Kind">Which setting controls whether this form gets its own entry.</param>
/// <param name="Games">The games this form exists in.</param>
/// <param name="Types">
/// Set only when the form's typing differs from the species, as it does for every regional
/// form. Null means the species' types apply.
/// </param>
public sealed record Form(
    FormId Id,
    SpeciesId Species,
    string Name,
    FormKind Kind,
    IReadOnlyList<GameId> Games,
    IReadOnlyList<PokemonType>? Types = null);
