using System.IO;
using System.Reflection;
using Microsoft.Extensions.FileProviders;
using Microsoft.Extensions.Primitives;

namespace LivingDex.Desktop;

/// <summary>
/// Serves the static web assets that the <c>EmbedStaticWebAssets</c> target in the csproj baked
/// into this assembly, so the published exe carries its own host page, CSS and
/// <c>blazor.webview.js</c> instead of needing a <c>wwwroot</c> folder beside it.
/// </summary>
/// <remarks>
/// Only file lookups are implemented. BlazorWebView asks for one asset at a time by path and
/// never enumerates directories or watches for changes.
/// </remarks>
internal sealed class EmbeddedStaticWebAssetFileProvider : IFileProvider
{
    private const string ResourcePrefix = "wwwroot/";

    private readonly Assembly _assembly;
    private readonly HashSet<string> _resourceNames;
    private readonly DateTimeOffset _lastModified;

    public EmbeddedStaticWebAssetFileProvider(Assembly assembly)
    {
        _assembly = assembly;
        _resourceNames = new HashSet<string>(assembly.GetManifestResourceNames(), StringComparer.Ordinal);

        // Assembly.Location is empty in a single-file build, so date the assets by the exe.
        var exe = Environment.ProcessPath;
        _lastModified = exe is not null && File.Exists(exe)
            ? new DateTimeOffset(File.GetLastWriteTimeUtc(exe), TimeSpan.Zero)
            : DateTimeOffset.UnixEpoch;
    }

    public IFileInfo GetFileInfo(string subpath)
    {
        var resourceName = ResourcePrefix + subpath.Replace(Path.DirectorySeparatorChar, '/').TrimStart('/');
        if (!_resourceNames.Contains(resourceName))
        {
            return new NotFoundFileInfo(subpath);
        }

        using var stream = _assembly.GetManifestResourceStream(resourceName);
        if (stream is null)
        {
            return new NotFoundFileInfo(subpath);
        }

        return new EmbeddedFile(_assembly, resourceName, Path.GetFileName(resourceName), stream.Length, _lastModified);
    }

    public IDirectoryContents GetDirectoryContents(string subpath) => NotFoundDirectoryContents.Singleton;

    public IChangeToken Watch(string filter) => NullChangeToken.Singleton;

    private sealed class EmbeddedFile(
        Assembly assembly,
        string resourceName,
        string name,
        long length,
        DateTimeOffset lastModified) : IFileInfo
    {
        public bool Exists => true;

        public bool IsDirectory => false;

        public DateTimeOffset LastModified => lastModified;

        public long Length => length;

        public string Name => name;

        public string? PhysicalPath => null;

        public Stream CreateReadStream() => assembly.GetManifestResourceStream(resourceName)!;
    }
}
