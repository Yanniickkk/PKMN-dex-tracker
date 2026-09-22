using System.Text.RegularExpressions;

namespace LivingDex.Core.Tests.Dataset;

/// <summary>
/// The app runs with no network at all: every sprite is shipped inside the exe and nothing in
/// the UI points at a server.
/// </summary>
/// <remarks>
/// These read the repository rather than a library, because what they guard is a property of
/// what gets shipped. A stylesheet that starts pulling a font from a CDN, or a dataset that
/// loses a sprite, would otherwise only show up on a machine with no internet - which is exactly
/// the machine this app is meant for.
/// </remarks>
public class OfflineTests
{
    private static readonly string Repository = FindRepository();

    private static string FindRepository()
    {
        var directory = new DirectoryInfo(AppContext.BaseDirectory);

        while (directory is not null && !File.Exists(Path.Combine(directory.FullName, "LivingDex.slnx")))
        {
            directory = directory.Parent;
        }

        Assert.NotNull(directory);
        return directory.FullName;
    }

    [Fact]
    public void Every_species_in_the_dataset_has_a_sprite_beside_it()
    {
        var species = Path.Combine(Repository, "dataset", "species.json");
        var sprites = Path.Combine(Repository, "dataset", "sprites");

        Assert.True(File.Exists(species), "the dataset has not been built");

        var ids = Regex.Matches(File.ReadAllText(species), "\"id\": \"(?<id>[^\"]+)\"")
            .Select(match => match.Groups["id"].Value)
            .ToList();

        Assert.NotEmpty(ids);

        var missing = ids
            .Where(id => !File.Exists(Path.Combine(sprites, $"{id}.png")))
            .ToList();

        Assert.True(missing.Count == 0, $"no sprite for: {string.Join(", ", missing.Take(10))}");
    }

    [Fact]
    public void The_app_embeds_every_sprite_directory_rather_than_only_the_top_one()
    {
        // The check that was missing when per-game sprites arrived. The csproj globbed
        // dataset/sprites/*.png, which is not recursive, so every per-game directory was written
        // to disk, committed, and then silently left out of the exe - and the app fell back to
        // the shared set while looking exactly as though it had not.
        //
        // This asserts the rule rather than the exe: the test project does not reference the app,
        // so it cannot read the app's resources. It fails the moment someone flattens the glob.
        var csproj = File.ReadAllText(
            Path.Combine(Repository, "app", "LivingDex.Desktop", "LivingDex.Desktop.csproj"));

        var include = Regex.Match(csproj, @"<_DatasetSprite Include=""(?<path>[^""]+)""");
        Assert.True(include.Success, "the sprite glob has been renamed");
        Assert.Contains("**", include.Groups["path"].Value, StringComparison.Ordinal);

        // And the path a sprite is embedded under has to keep the directory it came from, or
        // every set would collapse onto the shared names.
        var logical = Regex.Match(
            csproj,
            @"<LogicalName>dataset/sprites/(?<name>[^<]+)</LogicalName>");
        Assert.True(logical.Success, "the sprite logical name has been renamed");
        Assert.Contains("RecursiveDir", logical.Groups["name"].Value, StringComparison.Ordinal);
    }

    [Theory]
    [InlineData("wwwroot")]
    [InlineData("Components")]
    public void Nothing_the_app_renders_points_at_a_server(string folder)
    {
        var root = Path.Combine(Repository, "app", "LivingDex.Desktop", folder);
        Assert.True(Directory.Exists(root), $"{root} is missing");

        var offenders = new List<string>();

        foreach (var file in Directory.EnumerateFiles(root, "*", SearchOption.AllDirectories)
                     .Where(path => path.EndsWith(".html", StringComparison.OrdinalIgnoreCase)
                         || path.EndsWith(".css", StringComparison.OrdinalIgnoreCase)
                         || path.EndsWith(".js", StringComparison.OrdinalIgnoreCase)
                         || path.EndsWith(".razor", StringComparison.OrdinalIgnoreCase)))
        {
            foreach (var (line, number) in File.ReadLines(file).Select((line, index) => (line, index + 1)))
            {
                // Anything that would be fetched: a src, an href, a CSS url(), an import. A URL
                // inside a comment is prose and cannot be requested.
                if (Regex.IsMatch(line, @"(src|href)\s*=\s*[""']https?://", RegexOptions.IgnoreCase)
                    || Regex.IsMatch(line, @"url\(\s*[""']?https?://", RegexOptions.IgnoreCase)
                    || Regex.IsMatch(line, @"(fetch|import)\s*\(\s*[""']https?://", RegexOptions.IgnoreCase))
                {
                    offenders.Add($"{Path.GetRelativePath(Repository, file)}:{number}");
                }
            }
        }

        Assert.True(offenders.Count == 0, $"these would be fetched at runtime: {string.Join(", ", offenders)}");
    }
}
