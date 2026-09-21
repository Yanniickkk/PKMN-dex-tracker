using System.Globalization;
using System.Security.Cryptography;
using System.Text.Json;
using LivingDex.Core.Dataset;

namespace LivingDex.Core.UserData;

/// <summary>
/// Identifies the exact bytes on disk. A content hash rather than a timestamp: cloud sync
/// clients rewrite modification times freely, and two machines can disagree about the clock.
/// </summary>
/// <param name="Hash">Lowercase hex SHA-256 of the file, or empty when there is no file.</param>
public readonly record struct FileRevision(string Hash)
{
    /// <summary>No file on disk yet.</summary>
    public static FileRevision None { get; } = new(string.Empty);

    /// <summary>True when there is no file.</summary>
    public bool IsMissing => Hash.Length == 0;

    public override string ToString() => IsMissing ? "(none)" : Hash[..Math.Min(12, Hash.Length)];
}

/// <summary>What was read, and which revision it was read from.</summary>
/// <param name="Document">The data.</param>
/// <param name="Revision">The revision it came from, to be handed back to the next save.</param>
public sealed record UserDataSnapshot(UserDataDocument Document, FileRevision Revision);

/// <summary>Why a save did or did not happen.</summary>
public enum SaveStatus
{
    /// <summary>The file now holds what was passed in.</summary>
    Saved,

    /// <summary>
    /// Someone else wrote the file since it was read. Nothing was overwritten.
    /// </summary>
    Conflict,
}

/// <summary>The result of a save attempt.</summary>
/// <param name="Status">Whether the write happened.</param>
/// <param name="Revision">
/// The revision now on disk: the newly written one after a save, or the other machine's one
/// after a conflict.
/// </param>
/// <param name="OnDisk">
/// What is on disk instead, set only on a conflict so the caller can show it or reload without
/// a second read.
/// </param>
public sealed record SaveResult(SaveStatus Status, FileRevision Revision, UserDataDocument? OnDisk);

/// <summary>Thrown when the data file exists but cannot be read as user data.</summary>
public sealed class UserDataCorruptException : Exception
{
    public UserDataCorruptException()
    {
    }

    public UserDataCorruptException(string message)
        : base(message)
    {
    }

    public UserDataCorruptException(string message, Exception innerException)
        : base(message, innerException)
    {
    }

    /// <summary>The file that could not be read, when the failure was about a specific one.</summary>
    public string? Path { get; private init; }

    /// <summary>Names the offending file in both the message and <see cref="Path"/>.</summary>
    public static UserDataCorruptException ForFile(string path, Exception inner) =>
        new($"The data file at {path} could not be read.", inner) { Path = path };
}

/// <summary>
/// Reads and writes the player's data file.
/// </summary>
/// <remarks>
/// <para>
/// Three things protect the file, and they cover different failures:
/// </para>
/// <list type="bullet">
/// <item>
/// Writes go to a temporary file in the same directory and are then swapped in, so a crash or a
/// pulled power cable leaves either the old file or the new one, never half of either.
/// </item>
/// <item>
/// A lock file serialises two processes on the same machine for the whole check-then-swap.
/// </item>
/// <item>
/// A save states which revision it believes is on disk. If the file moved on, the save is
/// refused rather than applied. This is the only defence that works across machines, because no
/// file lock survives a cloud sync client.
/// </item>
/// </list>
/// <para>
/// The revision check still has a window: a sync client can land a file between the check and
/// the swap. The swap itself is atomic, so the worst case is the other machine's write being
/// replaced, and the previous content is in the backup directory.
/// </para>
/// </remarks>
public sealed class UserDataStore
{
    private static readonly TimeSpan LockTimeout = TimeSpan.FromSeconds(5);
    private static readonly TimeSpan LockRetryDelay = TimeSpan.FromMilliseconds(50);

    private readonly string _path;
    private readonly int _backupsToKeep;

    /// <param name="path">The data file. Its directory is created on first save.</param>
    /// <param name="backupsToKeep">How many timestamped backups to keep.</param>
    public UserDataStore(string path, int backupsToKeep = 10)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(path);
        ArgumentOutOfRangeException.ThrowIfNegative(backupsToKeep);

        _path = System.IO.Path.GetFullPath(path);
        _backupsToKeep = backupsToKeep;
    }

    /// <summary>The data file this store reads and writes.</summary>
    public string Path => _path;

    /// <summary>Where rolling backups are kept, beside the data file.</summary>
    public string BackupDirectory =>
        System.IO.Path.Combine(
            System.IO.Path.GetDirectoryName(_path) ?? ".",
            System.IO.Path.GetFileNameWithoutExtension(_path) + ".backups");

    private string LockPath => _path + ".lock";

    /// <summary>
    /// Reads the file. A file that is not there yet is not an error: it reads as an empty
    /// document at <see cref="FileRevision.None"/>, which is what a first run sees.
    /// </summary>
    /// <exception cref="UserDataCorruptException">The file exists but is not readable as user data.</exception>
    public async Task<UserDataSnapshot> LoadAsync(CancellationToken cancellationToken = default)
    {
        if (!File.Exists(_path))
        {
            return new UserDataSnapshot(UserDataDocument.Empty, FileRevision.None);
        }

        byte[] bytes;
        try
        {
            bytes = await File.ReadAllBytesAsync(_path, cancellationToken).ConfigureAwait(false);
        }
        catch (IOException exception)
        {
            throw UserDataCorruptException.ForFile(_path, exception);
        }

        return new UserDataSnapshot(Deserialize(bytes), Revision(bytes));
    }

    /// <summary>
    /// What is on disk right now, without reading the whole document. Used to notice that
    /// another machine has written the file while this one sat idle.
    /// </summary>
    public async Task<FileRevision> ReadRevisionAsync(CancellationToken cancellationToken = default)
    {
        if (!File.Exists(_path))
        {
            return FileRevision.None;
        }

        await using var stream = new FileStream(
            _path,
            FileMode.Open,
            FileAccess.Read,
            FileShare.ReadWrite,
            bufferSize: 4096,
            useAsync: true);

        var hash = await SHA256.HashDataAsync(stream, cancellationToken).ConfigureAwait(false);
        return new FileRevision(Convert.ToHexStringLower(hash));
    }

    /// <summary>
    /// Writes the document, but only if the file still holds <paramref name="expected"/>.
    /// </summary>
    /// <param name="document">What to write.</param>
    /// <param name="expected">
    /// The revision the caller last read or wrote. Pass <see cref="FileRevision.None"/> to mean
    /// "there should be no file yet".
    /// </param>
    /// <param name="cancellationToken">Cancels the save.</param>
    /// <returns>
    /// <see cref="SaveStatus.Saved"/> with the new revision, or <see cref="SaveStatus.Conflict"/>
    /// with what is on disk instead. A conflict never overwrites anything.
    /// </returns>
    public async Task<SaveResult> SaveAsync(
        UserDataDocument document,
        FileRevision expected,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(document);

        Directory.CreateDirectory(System.IO.Path.GetDirectoryName(_path)!);

        using var fileLock = await AcquireLockAsync(cancellationToken).ConfigureAwait(false);

        var current = await ReadRevisionAsync(cancellationToken).ConfigureAwait(false);
        if (current != expected)
        {
            var onDisk = current.IsMissing
                ? UserDataDocument.Empty
                : Deserialize(await File.ReadAllBytesAsync(_path, cancellationToken).ConfigureAwait(false));

            return new SaveResult(SaveStatus.Conflict, current, onDisk);
        }

        var bytes = JsonSerializer.SerializeToUtf8Bytes(document, DatasetJson.Options);
        var temporaryPath = _path + ".tmp-" + Guid.NewGuid().ToString("n");

        try
        {
            await WriteThroughAsync(temporaryPath, bytes, cancellationToken).ConfigureAwait(false);
            SwapIn(temporaryPath);
        }
        catch
        {
            TryDelete(temporaryPath);
            throw;
        }

        PruneBackups();
        return new SaveResult(SaveStatus.Saved, Revision(bytes), OnDisk: null);
    }

    private static UserDataDocument Deserialize(byte[] bytes)
    {
        try
        {
            return JsonSerializer.Deserialize<UserDataDocument>(bytes, DatasetJson.Options)
                ?? throw new UserDataCorruptException("The data file contains a bare null.");
        }
        catch (JsonException exception)
        {
            throw new UserDataCorruptException("The data file is not valid user data.", exception);
        }
    }

    private static FileRevision Revision(byte[] bytes) =>
        new(Convert.ToHexStringLower(SHA256.HashData(bytes)));

    /// <summary>
    /// Writes and flushes all the way to the device, so the swap cannot promote a file whose
    /// contents are still sitting in a write cache.
    /// </summary>
    private static async Task WriteThroughAsync(string path, byte[] bytes, CancellationToken cancellationToken)
    {
        await using var stream = new FileStream(
            path,
            FileMode.CreateNew,
            FileAccess.Write,
            FileShare.None,
            bufferSize: 4096,
            FileOptions.Asynchronous | FileOptions.WriteThrough);

        await stream.WriteAsync(bytes, cancellationToken).ConfigureAwait(false);
        await stream.FlushAsync(cancellationToken).ConfigureAwait(false);
    }

    private void SwapIn(string temporaryPath)
    {
        if (!File.Exists(_path))
        {
            File.Move(temporaryPath, _path);
            return;
        }

        Directory.CreateDirectory(BackupDirectory);

        // File.Replace hands us the rolling backup for free: the file being replaced is moved
        // aside rather than deleted, in the same atomic operation.
        File.Replace(temporaryPath, _path, BackupPathForNow(), ignoreMetadataErrors: true);
    }

    private string BackupPathForNow()
    {
        var stamp = DateTime.Now.ToString("yyyyMMdd-HHmmss-fff", CultureInfo.InvariantCulture);
        var name = System.IO.Path.GetFileNameWithoutExtension(_path);
        var extension = System.IO.Path.GetExtension(_path);

        return System.IO.Path.Combine(BackupDirectory, $"{name}-{stamp}{extension}");
    }

    private void PruneBackups()
    {
        if (!Directory.Exists(BackupDirectory))
        {
            return;
        }

        var name = System.IO.Path.GetFileNameWithoutExtension(_path);
        var extension = System.IO.Path.GetExtension(_path);

        // The stamp sorts the same way as the clock, so ordering by name needs no file metadata.
        var backups = Directory.GetFiles(BackupDirectory, $"{name}-*{extension}")
            .OrderByDescending(path => path, StringComparer.Ordinal)
            .Skip(_backupsToKeep);

        foreach (var backup in backups)
        {
            TryDelete(backup);
        }
    }

    private static void TryDelete(string path)
    {
        try
        {
            File.Delete(path);
        }
        catch (IOException)
        {
            // A backup that cannot be pruned is not worth failing a save over.
        }
        catch (UnauthorizedAccessException)
        {
        }
    }

    /// <summary>
    /// Holds a lock file for the whole check-then-swap. This serialises two processes on this
    /// machine. It does nothing about another machine writing through a cloud sync client, which
    /// is what the revision check is for.
    /// </summary>
    private async Task<FileStream> AcquireLockAsync(CancellationToken cancellationToken)
    {
        var deadline = DateTime.UtcNow + LockTimeout;

        while (true)
        {
            cancellationToken.ThrowIfCancellationRequested();

            try
            {
                return new FileStream(LockPath, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
            }
            catch (IOException) when (DateTime.UtcNow < deadline)
            {
                await Task.Delay(LockRetryDelay, cancellationToken).ConfigureAwait(false);
            }
        }
    }
}
