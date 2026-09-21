namespace LivingDex.Core.UserData;

/// <summary>
/// What a capture state is called on screen.
/// </summary>
/// <remarks>
/// In Core rather than in a page for the same reason as
/// <see cref="Transfers.TransferNames"/>: the grid puts it on a tile, and the detail popup and
/// the filters say the same things. The wording names the game the player is looking at, because
/// "caught elsewhere" is the code's word for it and not something a player would say.
/// </remarks>
public static class CaptureStatusNames
{
    /// <summary>
    /// One line describing where an entry stands.
    /// </summary>
    /// <param name="status">The state.</param>
    /// <param name="mainGameName">The collection's main game, as a player would name it.</param>
    /// <param name="holdingGameName">
    /// The game holding it, when that is known and is not the main game. A record can be
    /// <see cref="CaptureStatus.CaughtElsewhere"/> without naming a game if the file was edited
    /// by hand, so this may be null even then.
    /// </param>
    public static string Of(CaptureStatus status, string mainGameName, string? holdingGameName = null) =>
        status switch
        {
            CaptureStatus.InMainGame => $"In {mainGameName}",
            CaptureStatus.CaughtElsewhere when !string.IsNullOrWhiteSpace(holdingGameName) =>
                $"In {holdingGameName}, still to transfer",
            CaptureStatus.CaughtElsewhere => "Caught, still to transfer",
            _ => "Not caught",
        };
}
