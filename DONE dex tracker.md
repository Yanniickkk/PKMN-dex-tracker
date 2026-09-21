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

All eight items landed together; the entities only make sense as one set. They live in
`app/LivingDex.Core/Reference/`, with the on-disk shape in `app/LivingDex.Core/Dataset/`
and 20 round-trip tests in `app/LivingDex.Core.Tests/Reference/`.

- [x] `Game` - id, title, version, generation, region, release (`cartridge` /
      `virtual-console`), `hasNationalDex`, dex source rules - 2026-09-21
  - Dex source rules became a `DexSource` enum (`nationalDex` / `gameDex`) next to
    `nationalDexThrough`, plus an optional `pairPartner` so Red knows about Blue.
  - `hasNationalDex` started as a bool and became `nationalDexThrough` (a number) in 0.5, once
    the dex builder needed to know where the National Dex stops rather than whether there is
    one. `HasNationalDex` is now derived from it.
- [x] `TransferEdge` - from, to, mechanism, direction, species filter rule - 2026-09-21
  - The filter is a small type hierarchy rather than flags: `all`, `nationalDexRange`
    (Time Capsule 1-251, Pal Park 1-386) and `presentInTargetDex`, which is the rule that
    makes HOME refuse a deposit into a Gen 8/9 game with no entry for the species.
- [x] `Species` - national dex number, name, types, evolution chain id - 2026-09-21
- [x] `Form` - species id, form name, form kind (`regional` / `functional` / `cosmetic` /
      `gender`), games it exists in - 2026-09-21
  - Added an optional `types` override beyond the listed fields. Every regional form has a
    different typing from its species, so without it the schema is wrong for exactly the
    case this project exists for.
- [x] `DexEntry` - game id, species or form id, that game's dex number - 2026-09-21
  - "Species or form" is a `DexTarget` carrying both, so a form entry never needs a lookup
    to find its species. The same type is reused as an acquisition method's target.
- [x] `AcquisitionMethod` - game id, target, kind (`gift` / `wild` / `evolution` / `trade`),
      method-specific fields, source citation - 2026-09-21
  - Four separate types behind one JSON `kind` discriminator, rather than one record with
    mostly-null columns. The spec table of per-method fields is not in this repo, so the
    fields were inferred from the Phase 2 checklist (step 3 for wild, step 4 for gifts and
    statics, step 5 for trades). Worth a review against the real table.
  - Every method carries a `SourceCitation`, so a disputed encounter rate can be traced
    without rerunning the pipeline.
- [x] `EvolutionRule` - from, to, trigger, conditions - 2026-09-21
  - Conditions are typed (`minimumLevel`, `heldItem`, `usedItem`, `friendship`, `timeOfDay`,
    `location`, `knownMove`, `gender`, `tradePartner`), with an `other` escape hatch holding
    prose so a game can be finished without first extending the schema.
  - Rules are global; a game being able to use one is expressed by that game having an
    `evolution` acquisition method pointing at it. That is also what makes the Phase 0.7
    "no evolution dead ends" check possible.
- [x] Decide the on-disk shape: one file per game plus shared species tables - 2026-09-21
  - `index.json`, `species.json`, `forms.json`, `evolution-rules.json`, `transfers.json`,
    and `games/<id>.json`. Documented with real serialiser output in `dataset/README.md`.
  - Written indented, camelCase, LF: the dataset is committed, so a rebuild has to produce a
    reviewable diff rather than one enormous line.
  - Ids are distinct types in code (`GameId`, `SpeciesId`, ...) and plain strings on disk.

Two things found while testing that the next phases need to know:

- An `AcquisitionMethod.Kind` property cannot be serialised alongside a `kind` discriminator;
  it is `[JsonIgnore]`d on the base *and* on each override, because System.Text.Json does not
  inherit the attribute.
- Records holding a collection compare that collection by reference, so `==` on `EvolutionRule`
  or `GameData` is not value equality. Compare the parts.

### 0.3 User data schema and storage

Model and storage in `app/LivingDex.Core/UserData/`, the WPF picker in
`app/LivingDex.Desktop/`, with 17 tests in `app/LivingDex.Core.Tests/UserData/`.

- [x] `Collection` - id, name, main game, linked games, `formsIncluded`,
      `genderDifferencesIncluded` - 2026-09-21
  - Named `DexCollection` in code. A domain type called exactly `Collection` reads badly next
    to `System.Collections`, and the analyser refuses any name ending in that word without an
    explicit exception, which `.editorconfig` now grants with a reason.
  - The two form booleans became a `FormSelection` in 0.5, at the user's request: one switch per
    `FormKind` (regional, functional, cosmetic, gender differences) rather than one blanket
    switch plus gender.
- [x] `CaptureRecord` - collection id, dex entry id, status, holding game, catch date,
      note - 2026-09-21
  - Keyed by `DexTarget`, not by a dex entry id. A dex entry id belongs to one game's
    numbering, so it would break the moment the forms setting is flipped or the main game
    changes - and 0.5 requires that toggling either setting preserves records.
  - `CaughtIn` derives the status from whether the holding game is the main game, so the two
    cannot contradict each other. `IsInconsistentFor` reports files where they already do.
  - A record survives going back to `notCaught`, so an accidental click does not throw away a
    note or a catch date.
- [x] JSON read/write with atomic writes (temp file, then rename) - 2026-09-21
  - Written through to the device before the swap, so the swap cannot promote a file whose
    contents are still in a write cache.
- [x] File location picker on first run, remembered - 2026-09-21
  - Shown from the main window's `Loaded`, not from startup. An ownerless modal gets no
    taskbar button and can sit behind another window, which on a first run is indistinguishable
    from the app hanging. Confirmed by inspection: the dialog now reports the main window as its
    owner, and the app has a taskbar button while it is up.
  - Cancelling falls back to Documents and remembers that, so the app always has somewhere to
    save and the question is asked exactly once.
- [x] Rolling timestamped backups next to the data file - 2026-09-21
  - `File.Replace` provides them in the same atomic operation that swaps the new file in: the
    old file is moved aside rather than deleted. Kept in a `.backups` directory beside the data
    file, pruned to the ten most recent.
- [x] External-change detection: warn before overwriting, reload when the file is newer - 2026-09-21
  - At the storage level: a save states the revision it believes is on disk, and is refused
    rather than applied if the file moved on. The refusal hands back what is on disk, so the
    caller can reload or merge without a second read. `ReadRevisionAsync` spots an outside edit
    while the app sits idle.
  - The visible warning and the reload prompt are Phase 1 work; there is no screen to show them
    on yet.
- [x] Test: two "machines" writing the same file, no silent data loss - 2026-09-21
  - Two stores on one file: both read the same revision, A saves, B is refused rather than
    erasing A's change, B merges what it was handed and saves. Plus a ten-way concurrent save
    where exactly one wins and the file still parses.

What protects the file, and what each part actually covers:

- The temp-file swap covers a crash mid-write.
- A lock file covers two processes on this machine, for the whole check-then-swap.
- The revision check is the only thing that covers a second machine, because no file lock
  survives a cloud sync client. It still has a window: a sync client can land a file between the
  check and the swap. The swap is atomic, so the worst case is the other machine's write being
  replaced, and that content is in the backup directory.

### 0.4 Transfer graph engine

`app/LivingDex.Core/Transfers/`, with 13 tests in `app/LivingDex.Core.Tests/Transfers/`.

- [x] Load the graph from data, never hardcode edges - 2026-09-21
  - The engine knows nothing about Pal Park, the Time Capsule or HOME by name. An empty edge
    list gives an empty graph; there is a test for that.
  - A `bothWays` edge becomes two directed edges at construction, so the search only ever deals
    with one-way hops.
- [x] `reachableFrom(game)` - which games can send into a given main game - 2026-09-21
  - Species filters are deliberately not applied: this answers "could this game ever feed that
    one", which is what the linked-game picker needs. Whether one species survives the trip is
    `routesBetween`.
- [x] `routesBetween(from, to, species)` - ordered chains, species filter applied per hop - 2026-09-21
  - Takes a `DexTarget`, so a form can be asked about, with a `SpeciesId` overload.
  - Filters are checked at every hop, not only the first. A Generation 4 species travelling from
    Ruby to Black is stopped at the Pal Park hop in the middle, and the test names that hop.
- [x] Shortest route first, alternatives available - 2026-09-21
  - Iterative deepening, so the cap on how many routes to return can never drop a shorter route
    in favour of a longer one already collected. `Shortest` and `Alternatives` are separate
    properties, ready for the collapsible list in Phase 1.
- [x] Return a reason when no route exists, for display in the UI - 2026-09-21
  - `NoRouteReason` distinguishes same game, unknown game, not connected at all, connected but
    not for this species, and a route longer than the search allows. The first two are user
    error, the third is permanent, the fourth is about this one Pokemon - the UI wants to say
    different things about each.
  - The explanation names the hop that refused and why, for example that Pal Park only carries
    National Dex 1 to 386. It is written with game ids; the UI has the names and can reword.
- [x] Unit tests: Platinum accepts Gen 3-4 only; Gen 2 cannot reach Gen 3; HOME rejects species
      missing from a Gen 8/9 dex - 2026-09-21
  - All three, plus one-way edges not being usable in reverse, both-ways edges working in both
    directions, and hop chains being continuous.

Performance was measured rather than assumed. On a graph the size and shape of the real one
(35 games, 186 edges, every game in a generation trading with every other), enumerating simple
paths across those near-complete cliques took 446 ms for a red-to-scarlet lookup. A reverse-BFS
distance map now prunes any branch that cannot reach the destination inside the remaining hop
budget; that lookup is 5 ms. The map ignores filters, so it never over-estimates and never prunes
a real route. Cost: the map is rebuilt per call, which took 500 short lookups from 22 ms to
36 ms. Worth caching per destination if that ever matters.

### 0.5 Dex builder

`app/LivingDex.Core/Dex/`, with `ReferenceData` in `app/LivingDex.Core/Dataset/` and 15 tests
in `app/LivingDex.Core.Tests/Dex/`.

- [x] Given a main game, produce the entry list (national dex vs that game's own dex) - 2026-09-21
  - This is what forced a schema change: see the note below.
  - Both sources are reduced to one species-to-number map before forms are considered, which
    keeps them on the same footing and stops a form appearing twice when the game numbers it and
    the form table lists it.
- [x] Apply the form settings: expand or collapse form entries - 2026-09-21
  - Shipped first as the specified single `formsIncluded` switch, then changed at the user's
    request to one switch per kind: regional, functional, cosmetic, gender differences. The
    kinds are worth very different amounts of work, and one blanket switch meant a Generation 8
    or 9 collection pulled in every Vivillon pattern along with the Alolan forms.
  - Only forms that exist in the main game, whatever the switches say. Alolan Vulpix shows up
    for a Sword collection and not for a Platinum one; Rotom's appliance forms the other way
    round.
  - There is no separate "include forms at all" field: it would be a second place to say what
    the four switches already say, and the two could disagree. `FormSelection.Any` is derived
    for a master checkbox to bind to, with `All`, `None` and `Default` to set it. `Default` is
    regional and functional on, cosmetic and gender off - the forms that are a different Pokemon
    to catch rather than the same one in a different colour.
- [x] Toggling either setting preserves existing capture records - 2026-09-21
  - The builder only reads reference data; it never touches records. Turning forms off removes
    the line from the grid and leaves the record, note and catch date alone, and turning it back
    on lines the record up with its entry again.
  - This is the payoff for keying `CaptureRecord` by `DexTarget` in 0.3 rather than by a dex
    entry id. A record also survives the main game changing, because Pikachu is the same entry
    whether it is numbered 25 or 194.
- [x] Ordering: dex number, base form first, then its forms - 2026-09-21
  - Forms under a species are ordered by form id so the list is stable between runs, and the
    outer sort is stable so that order survives it.

Schema change this section forced: `Game.hasNationalDex` was a bool, which says whether a game
has a National Dex but not where it ends - and the builder needs the number. It is now
`nationalDexThrough` (a number, absent for games without one), with `HasNationalDex` derived
from it. Same reasoning as `DexTarget.IsForm` and `CaptureRecord.Status`: do not store something
a file could then contradict. The 0.2 entry above records this too, `dataset/README.md` shows
the new field, and there is no migration cost because no dataset exists yet.

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
