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
/// <param name="ArchivedOn">
/// The day it was put away, or null while it is in use.
/// </param>
/// <remarks>
/// Archiving rather than deleting is the only way out of the collections list, and the date is
/// kept rather than a flag because the archive is a place the player reads: "Platinum living
/// dex, archived on 3 March" answers the question a bare tick never does. Deleting happens from
/// the archive and takes the records with it, so the one irreversible step is never the one
/// reached by a stray click.
///
/// Optional on purpose: a data file written before this existed has no such field, and reads
/// back as a collection that is in use - which is what every collection in it was.
/// </remarks>
public sealed record DexCollection(
    DexCollectionId Id,
    string Name,
    GameId MainGame,
    IReadOnlyList<GameId> LinkedGames,
    FormSelection Forms,
    DateOnly? ArchivedOn = null)
{
    /// <summary>Whether it has been put away. Derived from <see cref="ArchivedOn"/>.</summary>
    [JsonIgnore]
    public bool IsArchived => ArchivedOn is not null;
}
