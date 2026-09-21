using System.IO;
using Microsoft.AspNetCore.Components.WebView.Wpf;
using Microsoft.Extensions.FileProviders;
using Microsoft.Extensions.Primitives;

namespace LivingDex.Desktop;

/// <summary>
/// A <see cref="BlazorWebView"/> that can fall back to static web assets embedded in the
/// assembly, so the app also runs as a single exe with no <c>wwwroot</c> folder next to it.
/// </summary>
public sealed class LivingDexWebView : BlazorWebView
{
    public override IFileProvider CreateFileProvider(string contentRootDir)
    {
        var assembly = typeof(LivingDexWebView).Assembly;
        var web = new EmbeddedResourceFileProvider(assembly, "wwwroot/");

        // Sprites are embedded under dataset/, so a request for sprites/chimchar.png finds
        // dataset/sprites/chimchar.png. Kept as a second provider rather than copied into
        // wwwroot: they are dataset output, and the pipeline owns them.
        var data = new EmbeddedResourceFileProvider(assembly, "dataset/");
        var embedded = new FallbackFileProvider(web, data);

        // During development wwwroot sits next to the build output; preferring it means an
        // edit to index.html or app.css shows up on restart without a rebuild.
        return Directory.Exists(contentRootDir)
            ? new FallbackFileProvider(base.CreateFileProvider(contentRootDir), embedded)
            : embedded;
    }

    /// <summary>Serves from <paramref name="primary"/>, falling back per file.</summary>
    private sealed class FallbackFileProvider(IFileProvider primary, IFileProvider fallback) : IFileProvider
    {
        public IFileInfo GetFileInfo(string subpath)
        {
            var file = primary.GetFileInfo(subpath);
            return file.Exists ? file : fallback.GetFileInfo(subpath);
        }

        public IDirectoryContents GetDirectoryContents(string subpath)
        {
            var contents = primary.GetDirectoryContents(subpath);
            return contents.Exists ? contents : fallback.GetDirectoryContents(subpath);
        }

        public IChangeToken Watch(string filter) => primary.Watch(filter);
    }
}
