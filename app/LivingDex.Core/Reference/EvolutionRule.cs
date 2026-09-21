using System.Text.Json.Serialization;

namespace LivingDex.Core.Reference;

/// <summary>What sets an evolution off.</summary>
public enum EvolutionTrigger
{
    LevelUp,
    UseItem,
    Trade,
    Other,
}

/// <summary>
/// An extra requirement on top of the trigger. Modelled as separate types rather than a bag of
/// nullable fields so that a rule cannot express something meaningless, and so the UI can render
/// each requirement without a switch over nulls.
/// </summary>
[JsonPolymorphic(TypeDiscriminatorPropertyName = "condition")]
[JsonDerivedType(typeof(MinimumLevelCondition), "minimumLevel")]
[JsonDerivedType(typeof(HeldItemCondition), "heldItem")]
[JsonDerivedType(typeof(UsedItemCondition), "usedItem")]
[JsonDerivedType(typeof(FriendshipCondition), "friendship")]
[JsonDerivedType(typeof(TimeOfDayCondition), "timeOfDay")]
[JsonDerivedType(typeof(LocationCondition), "location")]
[JsonDerivedType(typeof(KnownMoveCondition), "knownMove")]
[JsonDerivedType(typeof(GenderCondition), "gender")]
[JsonDerivedType(typeof(TradePartnerCondition), "tradePartner")]
[JsonDerivedType(typeof(OtherCondition), "other")]
public abstract record EvolutionCondition;

/// <summary>Evolves at or above this level.</summary>
public sealed record MinimumLevelCondition(int Level) : EvolutionCondition;

/// <summary>Must be holding this item, for example a Metal Coat.</summary>
public sealed record HeldItemCondition(string Item) : EvolutionCondition;

/// <summary>An item used on it, for example a Fire Stone.</summary>
public sealed record UsedItemCondition(string Item) : EvolutionCondition;

/// <summary>Friendship at or above this value.</summary>
public sealed record FriendshipCondition(int Minimum) : EvolutionCondition;

/// <summary>Only during this part of the day, for example <c>night</c>.</summary>
public sealed record TimeOfDayCondition(string TimeOfDay) : EvolutionCondition;

/// <summary>Only in this place, for example Mt. Coronet.</summary>
public sealed record LocationCondition(string Location) : EvolutionCondition;

/// <summary>Must know this move, for example Ancient Power.</summary>
public sealed record KnownMoveCondition(string Move) : EvolutionCondition;

/// <summary>Only this gender, for example Combee to Vespiquen.</summary>
public sealed record GenderCondition(string Gender) : EvolutionCondition;

/// <summary>Trade for this specific species, for example Shelmet and Karrablast.</summary>
public sealed record TradePartnerCondition(SpeciesId Species) : EvolutionCondition;

/// <summary>
/// Anything not worth its own type yet. Carries prose so a game can be finished without first
/// extending this file; promote it to a real condition once a second game needs the same thing.
/// </summary>
public sealed record OtherCondition(string Description) : EvolutionCondition;

/// <summary>
/// How one target becomes another. Rules are shared across games; whether a rule is usable in a
/// given game is expressed by that game having an <see cref="EvolutionAcquisition"/> for it.
/// </summary>
/// <param name="Id">Stable id, for example <c>chimchar-to-monferno</c>.</param>
/// <param name="From">What evolves.</param>
/// <param name="To">What it becomes.</param>
/// <param name="Trigger">What sets it off.</param>
/// <param name="Conditions">Extra requirements, all of which must hold.</param>
public sealed record EvolutionRule(
    EvolutionRuleId Id,
    DexTarget From,
    DexTarget To,
    EvolutionTrigger Trigger,
    IReadOnlyList<EvolutionCondition> Conditions);
