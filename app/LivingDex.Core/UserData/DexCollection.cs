using System.Text.Json.Serialization;
using LivingDex.Core.Reference;

namespace LivingDex.Core.UserData;

/// <summary>Identifies one collection the player is filling in.</summary>
[JsonConverter(typeof(StringIdJsonConverter<DexCollectionId>))]
public readonly record struct DexCollectionId(string Value) : IStringId<DexCollectionId>
{
    public static DexCollectionId From(string value) => new(value);

    public static DexCollectionId New() => new(Guid.NewGuid().ToString("n"));

    public override string ToString() => Value;
}

/// <summary>
/// A living dex the player is working on: which game it is for, which games may feed it, and
/// how finely it counts forms.
/// </summary>
/// <param name="Id">Stable id, generated when the collection is created.</param>
/// <param name="Name">What the player calls it.</param>
/// <param name="MainGame">The game the dex is built from and transferred into.</param>
/// <param name="LinkedGames">Games the player owns that can feed the main game.</param>
/// <param name="Forms">Which kinds of form get an entry of their own.</param>
public sealed record DexCollection(
    DexCollectionId Id,
    string Name,
    GameId MainGame,
    IReadOnlyList<GameId> LinkedGames,
    FormSelection Forms);
