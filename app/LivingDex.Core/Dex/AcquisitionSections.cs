using LivingDex.Core.Reference;

namespace LivingDex.Core.Dex;

/// <summary>One section of the detail popup: every way of one kind to get one entry.</summary>
/// <param name="Kind">Which section this is.</param>
/// <param name="Methods">The ways, in the order they should be listed.</param>
public sealed record AcquisitionSection(AcquisitionKind Kind, IReadOnlyList<AcquisitionMethod> Methods);

/// <summary>
/// Groups the ways to get one entry into the popup's sections.
/// </summary>
/// <remarks>
/// The order is fixed rather than sorted by how many there are or where they come from: gift,
/// wild, evolution, breeding, trade. It runs from the most definite way to the least — a starter
/// you are handed cannot be missed, a wild slot is a chance, an evolution needs something else
/// first, breeding needs that and a long walk on top, and a trade needs something you are willing
/// to give away. A player reading top to bottom meets the surest option first.
/// </remarks>
public static class AcquisitionSections
{
    /// <summary>
    /// The sections with something in them, in the order they are shown. A kind nobody has a
    /// method for is left out rather than shown empty.
    /// </summary>
    /// <param name="methods">Every way to get one entry, across the games being considered.</param>
    /// <param name="gameOrder">
    /// The games in the order their methods should be listed within a section: the main game
    /// first, then the linked ones. A game not in this list is listed after the ones that are.
    /// Leave it out to keep the order the methods came in.
    /// </param>
    public static IReadOnlyList<AcquisitionSection> Of(
        IEnumerable<AcquisitionMethod> methods,
        IReadOnlyList<GameId>? gameOrder = null)
    {
        ArgumentNullException.ThrowIfNull(methods);

        return
        [
            .. methods
                .GroupBy(method => method.Kind)
                // By the enum's own value: AcquisitionKind is declared in display order, and
                // that declaration is the single place the order lives.
                .OrderBy(group => (int)group.Key)
                .Select(group => new AcquisitionSection(
                    group.Key,
                    // OrderBy is stable, so methods of one game keep the order the dataset gave
                    // them. Only the games move.
                    [.. group.OrderBy(method => Rank(method.Game, gameOrder))])),
        ];
    }

    /// <summary>
    /// Where a game sits in the list. Anything unexpected sorts last rather than first: a method
    /// from a game the collection does not include is the least likely to be useful, and it
    /// must not push the main game down the list.
    /// </summary>
    private static int Rank(GameId game, IReadOnlyList<GameId>? gameOrder)
    {
        if (gameOrder is null)
        {
            return 0;
        }

        for (var index = 0; index < gameOrder.Count; index++)
        {
            if (gameOrder[index] == game)
            {
                return index;
            }
        }

        return int.MaxValue;
    }
}

/// <summary>What each section is called on screen.</summary>
public static class AcquisitionNames
{
    /// <summary>The heading for a section.</summary>
    public static string Of(AcquisitionKind kind) => kind switch
    {
        AcquisitionKind.Gift => "Gifts and statics",
        AcquisitionKind.Wild => "In the wild",
        AcquisitionKind.Evolution => "By evolving",
        AcquisitionKind.Breeding => "From the day care",
        AcquisitionKind.Trade => "In-game trades",
        _ => kind.ToString(),
    };

    /// <summary>How an encounter is started, as a player would say it.</summary>
    public static string Of(EncounterMethod method) => method switch
    {
        EncounterMethod.Walk => "walking",
        EncounterMethod.Surf => "surfing",
        EncounterMethod.OldRod => "Old Rod",
        EncounterMethod.GoodRod => "Good Rod",
        EncounterMethod.SuperRod => "Super Rod",
        EncounterMethod.RockSmash => "Rock Smash",
        EncounterMethod.Headbutt => "headbutting trees",
        EncounterMethod.HoneyTree => "honey trees",
        EncounterMethod.Swarm => "a swarm",
        EncounterMethod.DarkGrass => "dark grass",
        EncounterMethod.RustlingGrass => "rustling grass",
        EncounterMethod.DustCloud => "dust clouds",
        EncounterMethod.RipplingWater => "rippling water",
        EncounterMethod.BridgeShadow => "shadows on a bridge",
        EncounterMethod.HiddenGrotto => "a Hidden Grotto",
        _ => "another way",
    };

    /// <summary>What sort of one-off a gift is.</summary>
    public static string Of(GiftKind kind) => kind switch
    {
        GiftKind.Starter => "Starter",
        GiftKind.Fossil => "Revived fossil",
        GiftKind.NpcGift => "Gift",
        GiftKind.Egg => "Egg",
        GiftKind.StaticEncounter => "Static encounter",
        _ => kind.ToString(),
    };
}
