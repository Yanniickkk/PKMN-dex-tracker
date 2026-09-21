using LivingDex.Core.Reference;

namespace LivingDex.Core.Transfers;

/// <summary>
/// What to call a transfer mechanism on screen.
/// </summary>
/// <remarks>
/// In Core rather than in a page because more than one screen needs it: the linked-game picker
/// names how a game would feed yours, and the detail popup names the route for anything that
/// has to be transferred in. Two lists of these would drift.
/// </remarks>
public static class TransferNames
{
    /// <summary>The name a player would recognise.</summary>
    public static string Of(TransferMechanism mechanism) => mechanism switch
    {
        TransferMechanism.Trade => "trading",
        TransferMechanism.TimeCapsule => "the Time Capsule",
        TransferMechanism.PalPark => "Pal Park",
        TransferMechanism.PokeTransfer => "the Poké Transfer",
        TransferMechanism.PokeTransporter => "Poké Transporter",
        TransferMechanism.Bank => "Pokémon Bank",
        TransferMechanism.Home => "Pokémon HOME",
        _ => mechanism.ToString(),
    };

    /// <summary>
    /// How a route reads as a sentence fragment, for example <c>Pal Park, then trading</c>.
    /// Repeated mechanisms are collapsed: three trades in a row is still "trading".
    /// </summary>
    public static string Of(TransferRoute route)
    {
        ArgumentNullException.ThrowIfNull(route);

        var steps = new List<string>();

        foreach (var name in route.Hops.Select(hop => Of(hop.Mechanism)))
        {
            if (steps.Count == 0 || steps[^1] != name)
            {
                steps.Add(name);
            }
        }

        return steps.Count switch
        {
            0 => string.Empty,
            1 => steps[0],
            _ => string.Join(", then ", steps),
        };
    }
}
