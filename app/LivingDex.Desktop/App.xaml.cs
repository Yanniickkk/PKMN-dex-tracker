using System.IO;
using System.Windows;
using System.Windows.Threading;
using LivingDex.Core.Dataset;
using LivingDex.Core.Transfers;
using LivingDex.Core.UserData;
using Microsoft.Extensions.DependencyInjection;

namespace LivingDex.Desktop;

/// <summary>
/// Interaction logic for App.xaml
/// </summary>
public partial class App : Application
{
    private static readonly string CrashLogPath = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "LivingDexTracker",
        "crash.log");

    public App()
    {
        // A WinExe that dies before its window appears leaves nothing behind but a
        // Windows Error Reporting bucket, which says only "a .NET exception happened".
        AppDomain.CurrentDomain.UnhandledException += (_, e) =>
            WriteCrashLog(e.ExceptionObject as Exception);
        DispatcherUnhandledException += OnDispatcherUnhandledException;
    }

    protected override void OnStartup(StartupEventArgs e)
    {
        var settings = new AppSettingsStore(AppSettingsStore.DefaultPath);
        var locator = new DataFileLocator(settings, new WpfDataFileLocationPrompt());

        var services = new ServiceCollection();
        services.AddWpfBlazorWebView();
#if DEBUG
        services.AddBlazorWebViewDeveloperTools();
#endif
        services.AddSingleton(settings);
        services.AddSingleton(locator);

        // Read once at startup: it is embedded in this assembly and never changes while
        // the app is running.
        var dataset = DatasetLoader.Load(typeof(App).Assembly);
        services.AddSingleton(dataset);

        // The graph is data, so it is built here rather than anywhere it is used.
        services.AddSingleton(new TransferGraph(
            dataset.Reference.TransferEdges,
            new ReferenceFilterContext(
                dataset.Reference.Species,
                dataset.Reference.DexEntries,
                dataset.Reference.Games)));

        // Registered, not resolved: on a first run this puts a picker on screen, and that has
        // to wait until there is a window to own it. MainWindow sets it going.
        services.AddSingleton(new UserDataStoreProvider(locator));

        // BlazorWebView resolves its Services property out of the application
        // resource dictionary, so the provider has to live there under this key.
        Resources.Add("services", services.BuildServiceProvider());

        base.OnStartup(e);
    }

    private void OnDispatcherUnhandledException(object sender, DispatcherUnhandledExceptionEventArgs e)
    {
        WriteCrashLog(e.Exception);
        MessageBox.Show(
            $"Living Dex Tracker hit an unexpected error and has to close.\n\n" +
            $"{e.Exception.GetType().Name}: {e.Exception.Message}\n\n" +
            $"Details written to:\n{CrashLogPath}",
            "Living Dex Tracker",
            MessageBoxButton.OK,
            MessageBoxImage.Error);
        e.Handled = true;
        Shutdown(1);
    }

    private static void WriteCrashLog(Exception? exception)
    {
        if (exception is null)
        {
            return;
        }

        try
        {
            Directory.CreateDirectory(Path.GetDirectoryName(CrashLogPath)!);
            File.AppendAllText(
                CrashLogPath,
                $"""

                ===== {DateTimeOffset.Now:yyyy-MM-dd HH:mm:ss zzz} =====
                {exception}

                """);
        }
        catch (IOException)
        {
            // Nothing useful left to do if even the crash log cannot be written.
        }
        catch (UnauthorizedAccessException)
        {
        }
    }
}
