using LivingDex.Core.Dataset;
using LivingDex.Core.Reference;
using LivingDex.Core.UserData;

namespace LivingDex.Core.Dex;

/// <summary>
/// Whether one entry can actually be got in one game.
/// </summary>
/// <remarks>
/// Not the same question as "does the dataset record a way", which is what this replaced and
/// what made it wrong. Platinum knows how to turn a Bulbasaur into an Ivysaur and has no way at
/// all of producing a Bulbasaur, so "available in Platinum" listed an Ivysaur that no Platinum
/// player can ever have. An evolution is only an answer if the thing you evolve can be had, and
/// the same goes for an egg and its parents. The validator has said so since Phase 0.7; the
/// filter beside the grid did not.
///
/// What a player already owns counts. Once a Bulbasaur has been transferred into Platinum, the
/// Ivysaur it becomes really is available there, so this reads the collection's records as well
/// as the dataset - which is why it belongs to a screen and is rebuilt when the records change.
/// Owning the Bulbasaur does not make Bulbasaur itself available: you cannot obtain one in
/// Platinum, you brought it.
/// </remarks>
public sealed class Availability
{
    private readonly ReferenceData _reference;
    private readonly CaptureIndex _captures;
    private readonly Dictionary<(GameId Game, DexTarget Target), bool> _known = [];

    public Availability(ReferenceData reference, CaptureIndex captures)
    {
        ArgumentNullException.ThrowIfNull(reference);
        ArgumentNullException.ThrowIfNull(captures);

        _reference = reference;
        _captures = captures;
    }

    /// <summary>Whether this game has a way to produce this entry that a player could follow.</summary>
    public bool In(GameId game, DexTarget target) => Resolve(game, target, []);

    private bool Resolve(GameId game, DexTarget target, HashSet<(GameId, DexTarget)> visiting)
    {
        var key = (game, target);

        if (_known.TryGetValue(key, out var answer))
        {
            return answer;
        }

        // Evolution chains do not loop, so this only fires on data that is already wrong. It
        // answers no rather than recursing forever, and the answer is cached like any other.
        if (!visiting.Add(key))
        {
            return false;
        }

        answer = _reference.MethodsFor(game, target).Any(method => Follows(game, method, visiting));

        visiting.Remove(key);
        _known[key] = answer;

        return answer;
    }

    /// <summary>Whether one method is a way a player could actually follow in this game.</summary>
    private bool Follows(
        GameId game,
        AcquisitionMethod method,
        HashSet<(GameId, DexTarget)> visiting) => method switch
    {
        // A rule the dataset does not have is not a way to get anything. The validator reports
        // it separately; here it simply does not count.
        EvolutionAcquisition evolution =>
            _reference.FindEvolutionRule(evolution.Rule) is { } rule
            && CanBeHad(game, rule.From, visiting),

        // Any one parent at the day care lays the egg.
        BreedingAcquisition breeding =>
            breeding.Parents.Any(parent => CanBeHad(game, parent, visiting)),

        // Caught, handed over or traded for: the game produces it outright.
        _ => true,
    };

    private bool CanBeHad(GameId game, DexTarget target, HashSet<(GameId, DexTarget)> visiting) =>
        _captures.IsIn(game, target) || Resolve(game, target, visiting);
}
