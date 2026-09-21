using System.IO;
using System.Reflection;
using Microsoft.Extensions.FileProviders;
using Microsoft.Extensions.Primitives;

namespace LivingDex.Desktop;

/// <summary>
/// Serves files that the build baked into this assembly, so the published exe carries its own
/// host page, CSS, <c>blazor.webview.js</c> and sprites instead of needing folders beside it.
/// </summary>
/// <remarks>
/// Only file lookups are implemented. BlazorWebView asks for one asset at a time by path and
/// never enumerates directories or watches for changes.
/// </remarks>
internal sealed class EmbeddedResourceFileProvider : IFileProvider
{
    private readonly Assembly _assembly;
    private readonly string _resourcePrefix;
    private readonly HashSet<string> _resourceNames;
    private readonly DateTimeOffset _lastModified;

    /// <param name="assembly">Where the resources were embedded.</param>
    /// <param name="resourcePrefix">
    /// What a requested path is prefixed with to get a resource name, for example
    /// <c>wwwroot/</c>. This is what keeps one provider from serving another one's files.
    /// </param>
    public EmbeddedResourceFileProvider(Assembly assembly, string resourcePrefix)
    {
        _assembly = assembly;
        _resourcePrefix = resourcePrefix;
        _resourceNames = new HashSet<string>(assembly.GetManifestResourceNames(), StringComparer.Ordinal);

        // Assembly.Location is empty in a single-file build, so date the assets by the exe.
        var exe = Environment.ProcessPath;
        _lastModified = exe is not null && File.Exists(exe)
            ? new DateTimeOffset(File.GetLastWriteTimeUtc(exe), TimeSpan.Zero)
            : DateTimeOffset.UnixEpoch;
    }

    public IFileInfo GetFileInfo(string subpath)
    {
        var resourceName = _resourcePrefix + subpath.Replace(Path.DirectorySeparatorChar, '/').TrimStart('/');
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
