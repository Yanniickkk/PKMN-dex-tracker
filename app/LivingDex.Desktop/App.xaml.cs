using System.IO;
using System.Windows;
using System.Windows.Threading;
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

        var services = new ServiceCollection();
        services.AddWpfBlazorWebView();
#if DEBUG
        services.AddBlazorWebViewDeveloperTools();
#endif

        // BlazorWebView resolves its Services property out of the application
        // resource dictionary, so the provider has to live there under this key.
        Resources.Add("services", services.BuildServiceProvider());
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
