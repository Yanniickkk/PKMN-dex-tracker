# Living Dex Tracker

A Windows desktop app for tracking a living Pokédex across every mainline game, and the
data pipeline that feeds it. Work is tracked in [`TODO dex tracker.md`](TODO%20dex%20tracker.md);
finished items move to [`DONE dex tracker.md`](DONE%20dex%20tracker.md).

Current state: **Phase 0 skeleton**. The app shell runs and both toolchains are wired up.
There is no dataset and no dex UI yet.

## Stack

| Part | Choice |
| --- | --- |
| App shell | .NET 10 (LTS) + WPF, targeting `net10.0-windows10.0.19041.0` |
| App UI | Blazor Hybrid via `BlazorWebView` (WebView2) |
| Domain logic | `LivingDex.Core`, a plain `net10.0` class library |
| Pipeline | Python 3.12+ |
| Distribution | Self-contained single-file portable `.exe` |

### Why

**Blazor Hybrid in a WPF host, not MAUI.** The target is Windows only. MAUI's Windows head
pushes you towards MSIX packaging, which fights the "copy a folder and run it" distribution
this app wants. A WPF window hosting a `BlazorWebView` gives the same Razor component model
with a plain `dotnet publish` to a portable exe.

The project targets `net10.0-windows10.0.19041.0` rather than `net10.0-windows`, because
`BlazorWebView` renders through `WebView2CompositionControl`, which needs the Windows SDK
projections. On the plain Windows TFM the app builds fine and then throws
`FileNotFoundException: Microsoft.Windows.SDK.NET` the moment the window is measured.

**Blazor for the UI.** The grid is a few hundred to a few thousand sprite tiles with
filtering and a detail popup — a layout problem that CSS grid and `<Virtualize>` solve
directly, and that WPF's `ItemsControl` templating solves laboriously.

**Python for the pipeline.** The pipeline scrapes and reconciles encounter data from several
sources. Python's scraping and data-wrangling libraries are a clear step up from the .NET
equivalents, and the coupling to the app is a committed JSON dataset, not a call — so the
language choice on one side is invisible to the other.

**Self-contained publish, one file.** No .NET install on the target machine, and nothing
beside the exe. The cost is a ~150 MB exe. Trimming stays off: WPF, XAML and Blazor all
resolve types by reflection.

`PublishSingleFile` bundles the runtime but *not* static web assets, so `wwwroot` would
normally have to travel next to the exe -- and an exe sent on its own opens a window showing
WebView2's "There is no content at /" rather than failing loudly. The `EmbedStaticWebAssets`
target in the desktop csproj therefore bakes every static web asset into the assembly, and
`LivingDexWebView` serves them through an embedded `IFileProvider`. `PublishExeOnly` then
deletes the loose copies from the publish folder, so the drop cannot be split in half.

### Requirement on the target machine

The app needs the **WebView2 Runtime**. It ships with Windows 11 and with current Windows 10,
but a stripped or older Windows 10 install may need the
[Evergreen bootstrapper](https://developer.microsoft.com/microsoft-edge/webview2/).
Everything else, including the .NET runtime, is inside the exe.

## Layout

```
app/
  LivingDex.Desktop/        WPF host + Blazor components (the shipped exe)
  LivingDex.Core/           Domain: schemas, transfer graph, dex builder
  LivingDex.Core.Tests/     xUnit
pipeline/                   Python: PokeAPI client, scrapers, normaliser, validator
dataset/                    Pipeline output, committed on purpose
```

`app/` and `pipeline/` share no code. The dataset file format is the entire contract
between them.

## Working on it

### App

```bash
dotnet build LivingDex.slnx
```

```bash
dotnet test LivingDex.slnx
```

```bash
dotnet format LivingDex.slnx --verify-no-changes
```

Publish the portable exe. The result is `publish/LivingDex.exe` and nothing else --
a single file you can copy anywhere and run:

```bash
dotnet publish app/LivingDex.Desktop -c Release -o publish
```

### Pipeline

One-time setup:

```bash
python -m venv .venv && ./.venv/Scripts/python.exe -m pip install -e "pipeline[dev]"
```

Then, from `pipeline/`:

```bash
../.venv/Scripts/ruff.exe check . && ../.venv/Scripts/ruff.exe format --check . && ../.venv/Scripts/python.exe -m pytest
```

Build the dataset (not implemented yet — see Phase 0.6):

```bash
./.venv/Scripts/livingdex-pipeline.exe build --game platinum
```

## Notes for later

- `wwwroot/index.html` must **not** put `autostart="false"` on the `blazor.webview.js`
  script tag. That script only boots itself when the attribute is absent, and nothing in a
  Blazor Hybrid host calls `Blazor.start()`. With it, the window opens, the page loads, and
  the app silently never renders.
- Static web assets are embedded, but during development `wwwroot` on disk wins, so editing
  `index.html` or `app.css` takes effect on the next run without a rebuild.
- Unhandled exceptions are appended to `%LOCALAPPDATA%\LivingDexTracker\crash.log`. A WinExe
  that dies before its window appears otherwise leaves nothing but a Windows Error Reporting
  bucket saying "a .NET exception happened".
