namespace LivingDex.Core.Reference;

/// <summary>
/// A species, independent of any game. Shared across the whole dataset rather than repeated
/// per game.
/// </summary>
/// <param name="Id">Stable id, for example <c>chimchar</c>.</param>
/// <param name="NationalDexNumber">Its National Dex number.</param>
/// <param name="Name">Display name, for example <c>Chimchar</c>.</param>
/// <param name="Types">One or two types. A <see cref="Form"/> may override these.</param>
/// <param name="EvolutionChain">The chain this species belongs to.</param>
public sealed record Species(
    SpeciesId Id,
    int NationalDexNumber,
    string Name,
    IReadOnlyList<PokemonType> Types,
    EvolutionChainId EvolutionChain);
