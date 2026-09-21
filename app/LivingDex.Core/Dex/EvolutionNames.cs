using LivingDex.Core.Reference;

namespace LivingDex.Core.Dex;

/// <summary>
/// How an evolution reads on screen.
/// </summary>
/// <remarks>
/// In Core with the other naming helpers: the detail popup prints it under the evolution
/// section, and the drill-down will print the same rule again on the way down a chain.
/// </remarks>
public static class EvolutionNames
{
    /// <summary>What sets the evolution off.</summary>
    public static string Of(EvolutionTrigger trigger) => trigger switch
    {
        EvolutionTrigger.LevelUp => "Level up",
        EvolutionTrigger.UseItem => "Use an item",
        EvolutionTrigger.Trade => "Trade",
        _ => "Some other way",
    };

    /// <summary>
    /// One extra requirement, as a fragment that follows the trigger: "Level up, <em>at night</em>".
    /// </summary>
    /// <param name="condition">The requirement.</param>
    /// <param name="nameOf">
    /// How to name a species. Passed in because Core's naming table lives in the dataset, which
    /// this file deliberately does not depend on.
    /// </param>
    public static string Of(EvolutionCondition condition, Func<SpeciesId, string>? nameOf = null)
    {
        ArgumentNullException.ThrowIfNull(condition);

        return condition switch
        {
            MinimumLevelCondition level => $"from level {level.Level}",
            HeldItemCondition held => $"holding {Article(held.Item)}",
            UsedItemCondition used => $"using {Article(used.Item)}",
            FriendshipCondition friendship => $"with friendship {friendship.Minimum} or higher",
            // "during the day" rather than "at day", which is how "at night" tempts you to write it.
            TimeOfDayCondition time => $"during the {time.TimeOfDay}",
            LocationCondition location => $"at {location.Location}",
            KnownMoveCondition move => $"knowing {move.Move}",
            GenderCondition gender => $"{gender.Gender} only",
            TradePartnerCondition partner => $"for {(nameOf is null ? partner.Species.Value : nameOf(partner.Species))}",
            OtherCondition other => other.Description,
            _ => "under some other condition",
        };
    }

    /// <summary>
    /// The whole rule as one line, for example <c>Level up, with friendship 220 or higher</c>.
    /// </summary>
    public static string Describe(EvolutionRule rule, Func<SpeciesId, string>? nameOf = null)
    {
        ArgumentNullException.ThrowIfNull(rule);

        var parts = new List<string> { Of(rule.Trigger) };
        parts.AddRange(rule.Conditions.Select(condition => Of(condition, nameOf)));

        return string.Join(", ", parts);
    }

    /// <summary>
    /// "a Fire Stone", "an Oval Stone". Crude on purpose: it covers the item names a dataset
    /// actually holds, and a wrong article reads better than none at all.
    /// </summary>
    private static string Article(string item) =>
        item.Length > 0 && "aeiouAEIOU".Contains(item[0], StringComparison.Ordinal)
            ? $"an {item}"
            : $"a {item}";
}
