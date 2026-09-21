using LivingDex.Core.Reference;

namespace LivingDex.Core.UserData;

/// <summary>
/// The three states a tile can be in. "Caught" splits in two because a living dex is only
/// finished when everything sits in the main game, and the difference drives both the tile
/// colour and the "still to transfer" figure.
/// </summary>
public enum CaptureStatus
{
    /// <summary>Not obtained anywhere yet.</summary>
    NotCaught,

    /// <summary>Obtained, but sitting in a linked game. Still to transfer.</summary>
    CaughtElsewhere,

    /// <summary>Present in the main game. Done.</summary>
    InMainGame,
}

/// <summary>
/// What the player has done about one entry.
/// </summary>
/// <remarks>
/// Keyed by <see cref="DexTarget"/> rather than by a dex entry id. A dex entry id belongs to one
/// game's numbering, so it would break the moment the player flips the forms setting or the
/// collection's main game changes; the species-and-form pair survives both.
/// A record is kept even when the status returns to <see cref="CaptureStatus.NotCaught"/>, so a
/// note or a catch date is not thrown away by an accidental click.
/// </remarks>
public sealed record CaptureRecord
{
    /// <summary>The collection this belongs to.</summary>
    public required DexCollectionId Collection { get; init; }

    /// <summary>The species or form.</summary>
    public required DexTarget Target { get; init; }

    /// <summary>How far along this entry is.</summary>
    public required CaptureStatus Status { get; init; }

    /// <summary>
    /// The game currently holding it. Null when <see cref="Status"/> is
    /// <see cref="CaptureStatus.NotCaught"/>, and equal to the collection's main game when the
    /// status is <see cref="CaptureStatus.InMainGame"/>.
    /// </summary>
    public GameId? HoldingGame { get; init; }

    /// <summary>The day it was caught, when the player recorded one.</summary>
    public DateOnly? CaughtOn { get; init; }

    /// <summary>Free text from the player.</summary>
    public string? Note { get; init; }

    /// <summary>Nothing obtained yet, but any note or date the player wrote is kept.</summary>
    public static CaptureRecord NotCaught(DexCollectionId collection, DexTarget target) => new()
    {
        Collection = collection,
        Target = target,
        Status = CaptureStatus.NotCaught,
    };

    /// <summary>
    /// Caught in <paramref name="holdingGame"/>. The status follows from whether that is the
    /// collection's main game, so the two can never contradict each other.
    /// </summary>
    public static CaptureRecord CaughtIn(
        DexCollectionId collection,
        DexTarget target,
        GameId holdingGame,
        GameId mainGame,
        DateOnly? caughtOn = null,
        string? note = null) => new()
        {
            Collection = collection,
            Target = target,
            Status = holdingGame == mainGame ? CaptureStatus.InMainGame : CaptureStatus.CaughtElsewhere,
            HoldingGame = holdingGame,
            CaughtOn = caughtOn,
            Note = note,
        };

    /// <summary>
    /// True when <see cref="Status"/> and <see cref="HoldingGame"/> disagree. Hand-edited files
    /// and older versions of the app can produce this; the validator in Phase 0.7 reports it.
    /// </summary>
    public bool IsInconsistentFor(GameId mainGame) => Status switch
    {
        CaptureStatus.NotCaught => HoldingGame is not null,
        CaptureStatus.InMainGame => HoldingGame != mainGame,
        CaptureStatus.CaughtElsewhere => HoldingGame is null || HoldingGame == mainGame,
        _ => true,
    };
}
