using System.IO;
using System.Windows;
using LivingDex.Core.UserData;
using Microsoft.Win32;

namespace LivingDex.Desktop;

/// <summary>
/// Asks where to keep the data file with the standard Windows save dialog.
/// </summary>
/// <remarks>
/// A save dialog rather than an open dialog: on a first run the file does not exist yet, but a
/// player moving to a second machine needs to point at one that does. A save dialog does both,
/// with the overwrite warning turned off because picking an existing data file is the normal
/// way to join an existing collection rather than a mistake.
/// </remarks>
public sealed class WpfDataFileLocationPrompt : IDataFileLocationPrompt
{
    public string? AskWhereToKeepData(string suggestedPath)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(suggestedPath);

        var directory = Path.GetDirectoryName(suggestedPath);
        if (!string.IsNullOrEmpty(directory))
        {
            Directory.CreateDirectory(directory);
        }

        var dialog = new SaveFileDialog
        {
            Title = "Where should Living Dex Tracker keep your data?",
            Filter = "Living Dex data (*.json)|*.json|All files (*.*)|*.*",
            DefaultExt = ".json",
            FileName = Path.GetFileName(suggestedPath),
            InitialDirectory = directory,
            OverwritePrompt = false,
            AddExtension = true,
        };

        // An ownerless modal gets no taskbar button and can end up behind another window, which
        // on a first run looks exactly like the app hanging. The owner also puts it on the same
        // screen as the app rather than the primary one.
        var owner = Application.Current?.MainWindow;
        var answer = owner is not null ? dialog.ShowDialog(owner) : dialog.ShowDialog();

        return answer == true ? dialog.FileName : null;
    }
}
