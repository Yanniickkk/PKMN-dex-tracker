# Living Dex Tracker — Completed Work

Companion to `TODO dex tracker.md`. Items move here when they are finished, so the
TODO stays a list of what is still open rather than a growing archive.

## How this file works

- **Move, don't copy.** When an item is done, cut it from the TODO and paste it here
  under the matching section. The TODO shrinks, this file grows.
- **Tick the box on the way over.** `- [ ]` becomes `- [x]`.
- **Date every move.** Append ` — YYYY-MM-DD` to the item. That is the day it was
  finished, not the day it was written.
- **Keep the nesting.** A Phase 2 game moves with its 7 sub-steps intact, so the
  record shows what "done" actually covered for that game.
- **Partial work stays in the TODO.** A game with 4 of 7 steps ticked is not done;
  leave it where it is. Only whole items cross over.
- **Add a note when it is worth knowing.** Indent one line under the item for
  decisions taken, surprises found, or things deliberately left out.

Entry shape:

```
- [x] Item text, verbatim from the TODO — 2026-09-21
  - Note: what was decided, or what was skipped and why.
```

---

## Phase 0 — Foundations

### 0.1 Project setup

- [x] Pick the stack, note the choice and reason in `README.md` — 2026-09-21
  - .NET 10 + WPF hosting Blazor Hybrid (`BlazorWebView`) for the app, Python for the
    pipeline, self-contained single-file portable exe for distribution. Reasoning is in
    `README.md`.
  - The desktop project targets `net10.0-windows10.0.19041.0`, not `net10.0-windows`:
    `WebView2CompositionControl` needs the Windows SDK projections, and without them the
    app builds and then throws `FileNotFoundException: Microsoft.Windows.SDK.NET` on
    first layout.
- [x] Repository layout: `app/` and `pipeline/` separated, dataset output committed — 2026-09-21
  - `app/` holds `LivingDex.Desktop`, `LivingDex.Core` and `LivingDex.Core.Tests`;
    `pipeline/` is a standalone Python package. They share no code — the dataset format is
    the whole contract.
  - `dataset/` is tracked rather than ignored. It is empty until Phase 0.6 emits into it.
- [x] Linting, formatting, and a test runner wired up — 2026-09-21
  - .NET: `.editorconfig` + analyzers at `latest-recommended`, warnings as errors,
    `dotnet format --verify-no-changes`, xUnit via `dotnet test`.
  - Python: ruff for both lint and format, pytest. Both configured in `pipeline/pyproject.toml`.

### 0.2 Reference data schema

_Nothing yet._

### 0.3 User data schema and storage

_Nothing yet._

### 0.4 Transfer graph engine

_Nothing yet._

### 0.5 Dex builder

_Nothing yet._

### 0.6 Pipeline skeleton

_Nothing yet._

### 0.7 Validation rules

_Nothing yet._

---

## Phase 1 — First vertical slice

_Nothing yet._

---

## Phase 2 — Games

A game lands here only once all 7 steps are ticked and its validation run is green.

### Generation 1

_Nothing yet._

### Generation 2

_Nothing yet._

### Generation 3

_Nothing yet._

### Generation 4

_Nothing yet._

### Generation 5

_Nothing yet._

### Generation 6

_Nothing yet._

### Generation 7

_Nothing yet._

### Generation 8

_Nothing yet._

### Generation 9

_Nothing yet._

### Transfer-only nodes

_Nothing yet._

### Virtual Console releases

_Nothing yet._

---

## Phase 3 — Polish

_Nothing yet._
