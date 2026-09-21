using LivingDex.Core.Dataset;

namespace LivingDex.Core.Tests.Dataset;

public class DatasetStampTests
{
    [Fact]
    public void ToString_reads_as_version_then_build_date()
    {
        var stamp = new DatasetStamp("1.4.0", new DateOnly(2026, 9, 21));

        Assert.Equal("1.4.0 (2026-09-21)", stamp.ToString());
    }

    [Fact]
    public void Formats_the_date_the_same_way_regardless_of_the_machine_locale()
    {
        // InvariantGlobalization is on, so a machine in a different locale must not
        // reorder the date in a bug report.
        var stamp = new DatasetStamp("1.4.0", new DateOnly(2026, 1, 2));

        Assert.EndsWith("(2026-01-02)", stamp.ToString(), StringComparison.Ordinal);
    }
}
