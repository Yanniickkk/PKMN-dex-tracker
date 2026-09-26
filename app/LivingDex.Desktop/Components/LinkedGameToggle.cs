using LivingDex.Core.Reference;

namespace LivingDex.Desktop.Components;

/// <summary>A game being ticked or unticked in the linked-games picker.</summary>
/// <param name="Game">Which game.</param>
/// <param name="Linked">True when it was ticked, false when it was unticked.</param>
public readonly record struct LinkedGameToggle(GameId Game, bool Linked);
