using LivingDex.Core.UserData;

namespace LivingDex.Desktop;

/// <summary>
/// Hands out the <see cref="UserDataStore"/> once the app knows where the data file is.
/// </summary>
/// <remarks>
/// Working out that location can put a picker on screen, and a modal with no owner window has
/// no taskbar button and can hide behind another app. So the question is asked from the main
/// window rather than during startup, and anything that needs the store waits for the answer
/// instead of racing it.
/// </remarks>
public sealed class UserDataStoreProvider
{
    private readonly TaskCompletionSource<UserDataStore> _ready =
        new(TaskCreationOptions.RunContinuationsAsynchronously);

    private readonly DataFileLocator _locator;

    public UserDataStoreProvider(DataFileLocator locator)
    {
        ArgumentNullException.ThrowIfNull(locator);
        _locator = locator;
    }

    /// <summary>Completes once the data file location is known.</summary>
    public Task<UserDataStore> GetAsync() => _ready.Task;

    /// <summary>
    /// Resolves the location, asking the player if this is a first run. Called on the UI thread
    /// once a window exists to own the picker. Safe to call more than once.
    /// </summary>
    public void Initialize()
    {
        if (_ready.Task.IsCompleted)
        {
            return;
        }

        try
        {
            _ready.TrySetResult(new UserDataStore(_locator.Resolve()));
        }
        catch (Exception exception)
        {
            // Whoever is waiting gets the failure rather than waiting forever.
            _ready.TrySetException(exception);
            throw;
        }
    }
}
