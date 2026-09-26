using LivingDex.Core.Dex;
using LivingDex.Core.Reference;
using LivingDex.Core.UserData;

namespace LivingDex.Core.Tests.Dex;

public class CollectionCsvTests
{
    private static readonly DexCollectionId Mine = DexCollectionId.New();
    private static readonly GameId Platinum = new("platinum");
    private static readonly GameId Emerald = new("emerald");

    private static DexLine Line(string species, int number, string? name = null, FormKind? kind = null) =>
        new(DexTarget.ForSpecies(new SpeciesId(species)), number, name ?? species, kind);

    private static readonly DexLine Turtwig = Line("turtwig", 387, "Turtwig");
    private static readonly DexLine Chimchar = Line("chimchar", 390, "Chimchar");
    private static readonly DexLine Piplup = Line("piplup", 393, "Piplup");

    private static string Name(GameId game) => game == Platinum ? "Pokémon Platinum" : "Pokémon Emerald";

    private static string[] Rows(string csv) =>
        csv.Split("\r\n", StringSplitOptions.RemoveEmptyEntries);

    [Fact]
    public void An_empty_dex_is_still_a_file_with_a_header()
    {
        var csv = CollectionCsv.Of([], CaptureIndex.Empty, "Pokémon Platinum");

        Assert.Equal("Number,Name,Form,Status,Held in,Caught on,Out of reach,Note\r\n", csv);
    }

    [Fact]
    public void Every_line_gets_a_row_in_the_order_it_was_given()
    {
        var csv = CollectionCsv.Of([Turtwig, Chimchar, Piplup], CaptureIndex.Empty, "Pokémon Platinum");
        var rows = Rows(csv);

        Assert.Equal(4, rows.Length);
        Assert.Equal("387,Turtwig,,Not caught,,,,", rows[1]);
        Assert.Equal("390,Chimchar,,Not caught,,,,", rows[2]);
    }

    [Fact]
    public void What_is_recorded_is_what_is_written()
    {
        var captures = CaptureIndex.For(
            Mine,
            [
                CaptureRecord.CaughtIn(Mine, Turtwig.Target, Platinum, Platinum, new DateOnly(2026, 9, 21)),
                CaptureRecord.CaughtIn(Mine, Chimchar.Target, Emerald, Platinum),
            ]);

        var rows = Rows(CollectionCsv.Of(
            [Turtwig, Chimchar, Piplup],
            captures,
            "Pokémon Platinum",
            Name));

        Assert.Equal("387,Turtwig,,In Pokémon Platinum,Pokémon Platinum,2026-09-21,,", rows[1]);
        Assert.Equal(
            "390,Chimchar,,\"In Pokémon Emerald, still to transfer\",Pokémon Emerald,,,",
            rows[2]);
        Assert.Equal("393,Piplup,,Not caught,,,,", rows[3]);
    }

    [Fact]
    public void A_note_with_a_comma_a_quote_or_a_line_break_survives()
    {
        // All three really happen: it is free text a player typed into a box.
        var captures = CaptureIndex.For(
            Mine,
            [
                CaptureRecord.NotCaught(Mine, Turtwig.Target) with
                {
                    Note = "in the \"spare\" box, second row\nnear the top",
                },
            ]);

        var rows = Rows(CollectionCsv.Of([Turtwig], captures, "Pokémon Platinum"));

        // One row, not two: the line break the player typed stays inside the quoted field, and
        // the quotes around their word are doubled rather than ending it.
        Assert.Equal(2, rows.Length);
        Assert.EndsWith(
            "\"in the \"\"spare\"\" box, second row\nnear the top\"",
            rows[1],
            StringComparison.Ordinal);
    }

    [Fact]
    public void A_form_says_which_kind_it_is()
    {
        var wooper = Line("wooper", 53, "Wooper (Paldea)", FormKind.Regional);

        var rows = Rows(CollectionCsv.Of([wooper], CaptureIndex.Empty, "Pokémon Scarlet"));

        Assert.Equal("53,Wooper (Paldea),Regional,Not caught,,,,", rows[1]);
    }

    [Fact]
    public void Out_of_reach_is_left_empty_when_nothing_was_asked_and_answered_when_it_was()
    {
        var asked = Rows(CollectionCsv.Of(
            [Turtwig, Piplup],
            CaptureIndex.Empty,
            "Pokémon Platinum",
            isReachable: target => target != Piplup.Target));

        Assert.EndsWith("Not caught,,,no,", asked[1], StringComparison.Ordinal);
        Assert.EndsWith("Not caught,,,yes,", asked[2], StringComparison.Ordinal);

        var unasked = Rows(CollectionCsv.Of([Turtwig], CaptureIndex.Empty, "Pokémon Platinum"));
        Assert.EndsWith("Not caught,,,,", unasked[1], StringComparison.Ordinal);
    }

    [Fact]
    public void A_game_with_no_name_to_hand_is_written_as_its_id_rather_than_left_out()
    {
        var captures = CaptureIndex.For(
            Mine,
            [CaptureRecord.CaughtIn(Mine, Turtwig.Target, Emerald, Platinum)]);

        var rows = Rows(CollectionCsv.Of([Turtwig], captures, "Pokémon Platinum"));

        Assert.Contains("emerald", rows[1], StringComparison.Ordinal);
    }

    [Fact]
    public void The_suggested_name_is_the_collection_and_the_day()
    {
        var today = new DateOnly(2026, 9, 26);

        Assert.Equal("Platinum-living-dex-2026-09-26.csv", CollectionCsv.FileNameFor("Platinum living dex", today));
        Assert.Equal("Yannick-s-dex-2026-09-26.csv", CollectionCsv.FileNameFor("Yannick's dex", today));
        Assert.Equal("living-dex-2026-09-26.csv", CollectionCsv.FileNameFor("///", today));
        Assert.Equal("living-dex-2026-09-26.csv", CollectionCsv.FileNameFor("", today));
    }
}
