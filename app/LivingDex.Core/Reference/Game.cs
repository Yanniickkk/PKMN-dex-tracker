namespace LivingDex.Core.Reference;

/// <summary>How a game was released. Virtual Console releases are separate entities from the
/// cartridges, because only they reach Pokémon Bank.</summary>
public enum GameRelease
{
    Cartridge,
    VirtualConsole,
}

/// <summary>Which list of entries a collection uses when this game is the main game.</summary>
public enum DexSource
{
    /// <summary>The National Dex, for games that have one.</summary>
    NationalDex,

    /// <summary>This game's own dex, including DLC areas. The only option from Gen 8 onward.</summary>
    GameDex,
}

/// <summary>
/// One game version. Red and Blue are two <see cref="Game"/> values, not one "Red/Blue" row —
/// version exclusives are the whole reason the tracker exists.
/// </summary>
/// <param name="Id">Stable id, for example <c>platinum</c>.</param>
/// <param name="Title">Full title as printed, for example <c>Pokémon Platinum Version</c>.</param>
/// <param name="Version">The version name within its family, for example <c>Platinum</c>.</param>
/// <param name="Generation">1 through 9.</param>
/// <param name="Region">The region the game is set in, for example <c>Sinnoh</c>.</param>
/// <param name="Release">Cartridge or Virtual Console.</param>
/// <param name="HasNationalDex">False from Gen 8 onward.</param>
/// <param name="DexSource">Which list the dex builder uses for this game.</param>
/// <param name="PairPartner">The other half of a version pair, when there is one.</param>
public sealed record Game(
    GameId Id,
    string Title,
    string Version,
    int Generation,
    string Region,
    GameRelease Release,
    bool HasNationalDex,
    DexSource DexSource,
    GameId? PairPartner);
