using System.Text.Json.Serialization;
using LivingDex.Core.Reference;

namespace LivingDex.Core.UserData;

/// <summary>
/// Which kinds of form get an entry of their own in a collection. One switch per
/// <see cref="FormKind"/>, because the kinds are worth very different amounts of work: chasing
/// every regional form is a real goal, chasing every Vivillon pattern is usually not.
/// </summary>
/// <remarks>
/// There is no separate "include forms at all" switch. It would be a second place to say
/// something the four switches already say, and the two could then disagree. A UI that wants a
/// master checkbox binds it to <see cref="Any"/> and uses <see cref="All"/> and
/// <see cref="None"/> to set it.
/// </remarks>
/// <param name="Regional">Alolan, Galarian, Hisuian, Paldean.</param>
/// <param name="Functional">
/// Forms that change stats, typing or ability, for example Rotom's appliances.
/// </param>
/// <param name="Cosmetic">
/// Appearance only, for example Vivillon patterns. Off by default: turning this on for a
/// Generation 8 or 9 collection adds hundreds of entries.
/// </param>
/// <param name="GenderDifferences">Visible male and female differences.</param>
public sealed record FormSelection(
    bool Regional,
    bool Functional,
    bool Cosmetic,
    bool GenderDifferences)
{
    /// <summary>Base species only.</summary>
    public static FormSelection None { get; } = new(false, false, false, false);

    /// <summary>Every kind of form.</summary>
    public static FormSelection All { get; } = new(true, true, true, true);

    /// <summary>
    /// What a new collection starts with: the forms that are a different Pokémon to catch, and
    /// not the ones that are the same Pokémon in a different colour.
    /// </summary>
    public static FormSelection Default { get; } = new(
        Regional: true,
        Functional: true,
        Cosmetic: false,
        GenderDifferences: false);

    /// <summary>
    /// Whether any kind of form is included. What a master "include forms" checkbox shows.
    /// </summary>
    [JsonIgnore]
    public bool Any => Regional || Functional || Cosmetic || GenderDifferences;

    /// <summary>Whether entries of this kind belong in the dex.</summary>
    public bool Includes(FormKind kind) => kind switch
    {
        FormKind.Regional => Regional,
        FormKind.Functional => Functional,
        FormKind.Cosmetic => Cosmetic,
        FormKind.Gender => GenderDifferences,
        _ => false,
    };
}
