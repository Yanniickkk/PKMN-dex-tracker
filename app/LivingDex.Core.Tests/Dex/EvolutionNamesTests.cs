using LivingDex.Core.Dex;
using LivingDex.Core.Reference;

namespace LivingDex.Core.Tests.Dex;

public class EvolutionNamesTests
{
    private static EvolutionRule Rule(EvolutionTrigger trigger, params EvolutionCondition[] conditions) =>
        new(
            new EvolutionRuleId("test"),
            DexTarget.ForSpecies(new SpeciesId("chimchar")),
            DexTarget.ForSpecies(new SpeciesId("monferno")),
            trigger,
            conditions);

    [Fact]
    public void A_plain_level_up_needs_no_conditions_to_read_as_a_sentence()
    {
        Assert.Equal("Level up", EvolutionNames.Describe(Rule(EvolutionTrigger.LevelUp)));
    }

    [Fact]
    public void Conditions_follow_the_trigger_in_the_order_they_are_given()
    {
        var rule = Rule(
            EvolutionTrigger.LevelUp,
            new MinimumLevelCondition(16),
            new TimeOfDayCondition("night"));

        Assert.Equal("Level up, from level 16, during the night", EvolutionNames.Describe(rule));
    }

    [Fact]
    public void An_item_gets_an_article_that_fits_it()
    {
        Assert.Equal("using a Fire Stone", EvolutionNames.Of(new UsedItemCondition("Fire Stone")));
        Assert.Equal("holding an Oval Stone", EvolutionNames.Of(new HeldItemCondition("Oval Stone")));
    }

    [Fact]
    public void A_trade_partner_is_named_when_a_namer_is_given()
    {
        var condition = new TradePartnerCondition(new SpeciesId("karrablast"));

        Assert.Equal("for karrablast", EvolutionNames.Of(condition));
        Assert.Equal("for Karrablast", EvolutionNames.Of(condition, _ => "Karrablast"));
    }

    [Fact]
    public void Prose_that_has_no_type_of_its_own_is_printed_as_written()
    {
        Assert.Equal(
            "after walking 1000 steps",
            EvolutionNames.Of(new OtherCondition("after walking 1000 steps")));
    }

    [Fact]
    public void Every_trigger_and_condition_kind_says_something()
    {
        Assert.DoesNotContain(
            Enum.GetValues<EvolutionTrigger>().Select(EvolutionNames.Of),
            text => string.IsNullOrWhiteSpace(text));

        EvolutionCondition[] all =
        [
            new MinimumLevelCondition(5),
            new HeldItemCondition("Metal Coat"),
            new UsedItemCondition("Fire Stone"),
            new FriendshipCondition(220),
            new TimeOfDayCondition("night"),
            new LocationCondition("Mt. Coronet"),
            new KnownMoveCondition("Ancient Power"),
            new GenderCondition("female"),
            new TradePartnerCondition(new SpeciesId("shelmet")),
            new OtherCondition("something else"),
        ];

        Assert.DoesNotContain(
            all.Select(condition => EvolutionNames.Of(condition)),
            text => string.IsNullOrWhiteSpace(text));
    }
}
