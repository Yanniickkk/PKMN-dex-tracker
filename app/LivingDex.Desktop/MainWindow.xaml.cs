using System.Windows;
using Microsoft.Extensions.DependencyInjection;

namespace LivingDex.Desktop;

/// <summary>
/// Interaction logic for MainWindow.xaml
/// </summary>
public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
        Loaded += OnLoaded;
    }

    private void OnLoaded(object sender, RoutedEventArgs e)
    {
        Loaded -= OnLoaded;

        // First run asks where to keep the data. Done here rather than at startup so the picker
        // has this window as its owner.
        // Application.Resources, not this window's own dictionary: the indexer does not walk up.
        var services = (IServiceProvider)Application.Current.Resources["services"]!;
        services.GetRequiredService<UserDataStoreProvider>().Initialize();
    }
}
