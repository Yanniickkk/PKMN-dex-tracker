using System.IO;
using System.Text;
using System.Windows;
using Microsoft.Win32;

namespace LivingDex.Desktop;

/// <summary>
/// Asks where to put an exported file and writes it there.
/// </summary>
/// <remarks>
/// The dialog and the writing are together because they are one answer to one question: a
/// screen asks for a file to be saved, and either it was or the player changed their mind.
///
/// Static, and it holds nothing: there is one desktop and one save dialog, and an instance
/// would only be somewhere to put state that does not exist. The data file's own prompt is an
/// interface instead, because <see cref="LivingDex.Core.UserData.DataFileLocator"/> in Core
/// has to be testable without a desktop; nothing in Core asks for this one.
/// </remarks>
public static class WpfExportPrompt
{
    /// <summary>
    /// Offers a save dialog and writes <paramref name="contents"/> to whatever comes back.
    /// </summary>
    /// <param name="suggestedName">The file name to start with.</param>
    /// <param name="contents">The text to write.</param>
    /// <returns>The path written, or null when the player cancelled.</returns>
    /// <exception cref="IOException">The file could not be written.</exception>
    public static string? SaveCsv(string suggestedName, string contents)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(suggestedName);
        ArgumentNullException.ThrowIfNull(contents);

        var dialog = new SaveFileDialog
        {
            Title = "Export this dex",
            Filter = "Comma separated values (*.csv)|*.csv|All files (*.*)|*.*",
            DefaultExt = ".csv",
            FileName = suggestedName,
            AddExtension = true,
        };

        // An ownerless modal gets no taskbar button and can end up behind the window that
        // opened it, which looks exactly like the app hanging.
        var owner = Application.Current?.MainWindow;
        if ((owner is not null ? dialog.ShowDialog(owner) : dialog.ShowDialog()) != true)
        {
            return null;
        }

        // With a byte order mark, which is the opposite of what this app wants when it reads a
        // file and the right thing here: Excel reads a CSV as the machine's ANSI codepage
        // unless one is there, and half these names have an accent in them. Every other
        // program on this list copes with it.
        File.WriteAllText(dialog.FileName, contents, new UTF8Encoding(encoderShouldEmitUTF8Identifier: true));

        return dialog.FileName;
    }
}
