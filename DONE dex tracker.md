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

`pipeline/src/livingdex_pipeline/`, with 47 tests. The pipeline now runs end to end against the
real PokeAPI.

- [x] PokeAPI client with on-disk cache - 2026-09-21
  - Species, National Dex numbers, types, evolution chains and sprites. Deliberately not asked
    for encounter data: per-game encounter detail is where PokeAPI is thinnest, and that is what
    the scrapers are for.
  - Verified against the live API: a five-species build made 11 requests, and the same build
    again made zero.
- [x] Scraper base with on-disk cache and polite rate limiting - 2026-09-21
  - Everything downloaded goes through one client, which caches with no expiry, rate limits per
    host, and reads `robots.txt` before requesting a page - refusing rather than working around
    a `Disallow`. The User-Agent names the project and links to the repository.
  - A scraper produces loose records naming things the way its source names them. It does not
    decide what is true and does not know about PokeAPI ids. Keeping that apart from the
    normaliser and the merger is what makes a disagreement visible instead of silently settled
    by whichever source ran last.
- [x] Normaliser: scraped records matched onto PokeAPI ids - 2026-09-21
  - Two bugs the tests caught: an apostrophe was becoming a separator, so Farfetch'd came out as
    `farfetch-d` instead of `farfetchd`; and the gender symbols were being stripped by the ASCII
    pass before they could be spelled out, collapsing Nidoran-female and Nidoran-male into one
    name.
  - A name nothing matches is reported, not guessed at. A form the dataset does not know falls
    back to the base species rather than inventing an id.
- [x] Merge step with precedence rules and a conflict log - 2026-09-21
  - Sources are ranked once, in the scraper registry, and that ranking settles everything.
    Registering a source is therefore also a statement about how far it is trusted.
  - The losing value is written to `conflicts.json` rather than dropped: that is how a wrong
    encounter rate gets found later, and how a real disagreement is told apart from a scraper
    bug. A source that simply says nothing about a field is not disagreeing.
- [x] Emit dataset + sprites, stamped with version and build date - 2026-09-21
  - Two-space indent, LF, sorted where order carries no meaning, nulls left out entirely. The
    dataset is committed, so a rebuild has to produce a readable diff.
  - One battle sprite per species, so the app never touches the network.
- [x] Validator with the checks listed in 0.7 - 2026-09-21
  - The harness landed here, the rules in 0.7 below. Every build validates what it just wrote by
    reading it back from disk rather than checking the objects still in memory, so a
    serialisation bug fails the run that caused it.
- [x] `build --game <id>` so a single game can be rebuilt without touching the rest - 2026-09-21
  - Rewrites that game's file and the index, reads the shared tables rather than rebuilding
    them, and refuses if the shared tables are not there yet. A game with no registered builder
    is named, along with the ones that are registered, instead of writing an empty file that
    looks finished.

The cross-language contract is now tested. `pipeline/tests/expected/sample-dataset/` is a
committed sample using every shape in the schema: the Python suite regenerates it and fails if
it drifted, and a C# test reads the same files and fails if they no longer deserialise. The two
halves share no code, so this file format is the only thing holding them together, and it is now
the thing that breaks a build when it changes.

### 0.7 Validation rules

`pipeline/src/livingdex_pipeline/rules.py`, with 17 tests in `pipeline/tests/test_rules.py`.
Each rule is shown firing on the thing it exists to catch, and passing on the case it should
allow.

One decision underpins most of this section. Acquisition methods are recorded per game, but a
living dex is filled by transferring as much as by catching: most of Platinum's National Dex has
no Sinnoh encounter at all. So an entry counts as accounted for when *some* game in the dataset
can produce it. Whether that is the game you are playing is the difference between `full` and
`partial` in the coverage report, not the difference between valid and invalid. Read the rule
the other way and it would flag several hundred legitimate entries per National Dex game.

- [x] Every dex entry has a method, or is explicitly flagged unobtainable - 2026-09-21
  - This needed the schema change 0.6 predicted: `DexEntry.unobtainableReason`. A reason rather
    than a bool, so the validator can tell "we checked, and it cannot be caught" from "we have
    nothing", and Phase 3 can say which. `IsUnobtainable` is derived from it, so a file cannot
    claim the flag without saying why.
- [x] Every evolution rule points at an entry that itself has a method - no dead ends - 2026-09-21
  - Checked one link at a time, which covers a whole chain transitively: Infernape is fine
    because Monferno is, and Monferno because Chimchar is a gift. A method pointing at a rule id
    that does not exist is reported separately, because that is a different mistake.
- [x] Every form referenced by a game's dex exists in the form table - 2026-09-21
  - Also checks the form is filed under the species the dex puts it under.
  - Added beyond the spec, as a warning rather than an error: a dex that numbers a form whose
    form-table entry does not list that game. The dex builder silently drops such a form, so the
    dex comes out short with nothing to show for it.
- [x] Every transfer edge connects two known games - 2026-09-21
  - "Known" means present in the dataset as a game file, which is why Bank and HOME need entities
    of their own. Writing one exposed a gap: `GameRelease` had only `cartridge` and
    `virtualConsole`, and HOME is neither. It now has `service`.
- [x] Per-game coverage report: full / partial / missing counts - 2026-09-21
  - The spec asks for the three counts without defining them. Given meanings here: `full` is
    obtainable in this very game, `partial` is obtainable elsewhere and therefore a transfer
    away, `missing` is nothing can produce it anywhere.
  - A fourth count, `unobtainable`, sits beside them rather than being folded into one: an entry
    someone has checked and stated a reason for is not the same as one nobody has looked at.

The committed sample dataset now passes its own validator. It did not at first - the rules found
five real problems in it, which is a fair advertisement for them, but a sample that fails its own
checks is a bad thing to commit. It gained acquisition methods for what its dex lists and game
files for the transfer endpoints it referenced, and is now a small but valid dataset as well as a
wire-format fixture.

---

## Phase 1 — First vertical slice

- [x] Collection setup wizard: name, main game, linked games, the form selection - 2026-09-21
  - Three steps, as asked: name and main game, linked games, forms. The rules live in
    `CollectionDraft` in Core rather than in the Razor file, so what counts as a valid collection
    is tested without a browser; 17 tests cover it.
  - A name is required and has to be unused, ignoring case: two collections called "Living dex"
    would be a coin toss every time the player picks one. Linking no games at all is a valid
    answer, and linking the main game to itself is refused. Every form combination is allowed,
    including none.
  - Going back never validates. A step you have broken is exactly the step you need to retreat
    from.
  - Saving appends and retries once against whatever is on disk, because appending cannot lose
    anyone else's work. A second failure says so rather than looping.
  - Walked through in the running app end to end: the empty form refuses with both reasons
    listed, the duplicate name is caught, and the collection lands in the data file with the
    form switches the player set.

- [x] Linked-game picker filtered by the transfer graph, disabled entries show the reason - 2026-09-21
  - The graph needed a question it could not answer: "could this game ever feed that one",
    with no species in mind. `RoutesBetween(from, to)` is that question. A game can be a
    perfectly good feeder while refusing some of what lives in it - Emerald feeds Platinum even
    though Turtwig cannot make the Pal Park hop - so the picker must not ask the species-aware
    version.
  - Games that cannot feed are listed and disabled rather than left out. A picker that quietly
    omits them leaves the player wondering whether the app forgot their game or transferring is
    simply impossible.
  - The graph explains itself with game ids, which is right for a log and wrong for a screen, so
    the page writes the sentence from the reason and the titles it has. Enabled entries say how
    the feed would happen, for example "via Pal Park" - the same data, and it answers why
    something *is* available.
  - Changing the main game drops links that the change makes impossible. Verified in the app:
    ticking Emerald under Platinum and then switching the main game to Emerald leaves nothing
    ticked, rather than carrying a link into a collection that cannot work.

- [x] Grid screen: virtualised, battle sprites, dex number, name - 2026-09-21
  - The dataset is real now: a full pipeline run fetched all 1025 species and their sprites,
    1.04 MB of PNG in total, and validation stayed clean. Platinum's dex builds straight out of
    `nationalDexThrough`, so its 493 entries need no per-game dex file.
  - Virtualising rows rather than tiles. `Virtualize` inserts spacer elements, and a CSS grid
    would lay those out as if they were cells; a row is a grid of its own, so the spacers sit
    between rows where they belong. The column count is fixed rather than measured, because
    virtualising needs a row height it can trust and a count that changed with the window would
    invalidate that on every resize.
  - Sprites are served to the WebView by a second embedded-resource provider mapped at
    `dataset/`, so `sprites/pikachu.png` finds the embedded file. They stay dataset output
    rather than being copied into `wwwroot`.
  - Checked in the running app: 493 tiles, scrolled to #493 Arceus with no drift, and the last
    partial row renders correctly.
  - `DatasetLoader` had no tests. It has seven now, running against the pipeline's own sample
    dataset embedded into the test assembly the same way the real one is embedded into the app.

Two risks found and closed while doing this:

- `/collections/new` and `/collections/{id}` both match the same URL. Blazor prefers the literal
  segment, so the wizard still wins - verified in the app rather than assumed, because the
  failure would have been the grid quietly appearing instead of the wizard.
- `.gitattributes` said `dataset/** text eol=lf`, which would have made git rewrite line endings
  inside all 1025 PNGs and corrupt every one of them on checkout. They are marked binary now.

Two things this item needed that the list does not mention:

- The app had no way to read a dataset. `DatasetLoader` reads it out of the assembly, embedded
  the same way the web assets are, for the same reason: the app is one file and half a delivery
  should not be possible. The MSBuild for it needs qualified metadata - a bare `%(Filename)`
  there batches over every `EmbeddedResource` already in the project and produces a cross
  product.
- There were no games to choose. Platinum and Emerald are now registered in the pipeline with
  their entities and the Pal Park edge between them, which is Phase 2 step 1 for those two. That
  exposed a real ordering bug: a full build wrote the transfer graph without building any games,
  so every edge pointed at a game that was not in the dataset. The validator caught it. A build
  with no `--game` now builds every registered game.

- [x] Tile status colours for the three states, plus a non-colour badge or icon - 2026-09-21
  - The states are not told apart by colour alone, because a good share of players cannot rely
    on it and a grid of a thousand tiles is exactly where that bites. Not caught is the only
    greyed-out sprite; the two caught states are the only ones with a badge, and those badges
    are different shapes - a tick for done, an arrow for still to transfer. Turn the colour off
    entirely and the grid still reads.
  - No badge at all on a missing entry, deliberately. A hollow marker on nine hundred tiles is
    noise, and the greyed sprite already says it.
  - Every tile also carries the state in words, in its tooltip and in text only a screen reader
    sees. The wording is `CaptureStatusNames` in Core, not in the page, because the detail popup
    and the filters have to say the same thing. It names the game - "In Emerald, still to
    transfer" - rather than the app's own word for the state.
  - `CaptureIndex` turns the file's flat record list into a lookup per collection. The grid asks
    a thousand times while it scrolls, and a list scan per tile would be a thousand scans of
    every record in the file. It also settles two things the file can contain but the app never
    writes: records belonging to another collection are skipped, and two records for one entry
    leave the later one standing rather than throwing halfway through a render.
  - An entry with no record at all is "not caught". A fresh collection has no records, and that
    has to mean an empty dex rather than a missing one.
  - Checked in the running app in both themes against a seeded file: twelve entries in the main
    game, eight held in Emerald, the rest untouched. 10 tests.

- [x] Progress counter, with a secondary "still to transfer" figure - 2026-09-21
  - "12 of 493 in Platinum, 2%", with "8 still to transfer" set apart at the other end of the
    line. The main figure counts only what is in the main game, because that is what finishing a
    living dex means; the secondary figure is the work the player can do without catching
    anything new.
  - A bar under it in the same two colours as the tiles, green for home and amber for still to
    transfer. It is decoration: every figure it shows is already in the sentence above it, so it
    is hidden from screen readers rather than duplicated.
  - Counted over the dex the collection shows, never over the records in the file. A file keeps
    records the current dex has no line for - a form switched off since, or one caught before
    the main game changed - and counting those would push the figure past the total.
  - The percentage never rounds up to 100 while something is missing, and never down to 0 once
    something is done. A dex of 1025 reporting "100%" with one Pokemon left is the most annoying
    thing a tracker can do; 1024 of 1025 reads as 99%.
  - A finished dex says "All 386 in Emerald" rather than "386 of 386, 100%".
  - The bar width is written with the invariant culture. On this Dutch machine the default would
    have produced "2,4%", which is not a length and would have silently done nothing.
  - 8 tests, and both ends checked in the running app: a part-done Platinum dex in dark, and a
    complete Emerald dex in light.

- [x] Filters: name search, still to catch, not yet transferred, available in game - 2026-09-21
  - The two status switches widen the result and everything else narrows it. An entry cannot be
    both still to catch and not yet transferred, so reading those two as "and" would always
    return nothing; ticking both means "everything not done". Ticking neither is not "show
    nothing", it is "do not ask about status at all".
  - "Available in Platinum" is the main game only. That is the question a player has while
    playing: combined with "still to catch" it answers "what can I go and get right now". The
    linked-game version of the same question is what the transfer route in the detail popup is
    for. One line to change if the other reading turns out to be the wanted one.
  - The switch is offered but disabled while the dataset has no encounter data for the game,
    with a title saying so. Enabled, it would answer "nothing is available here", which is a lie
    rather than an empty result. It lights up on its own once Phase 2 fills that game in.
  - The dataset carried acquisition methods in its files but threw them away on load:
    `ReferenceData` had nowhere to put them. It has `MethodsFor(game, target)` and
    `HasAcquisitionData(game)` now, which the detail popup needs next anyway.
  - The filter resets when you open another collection. Walking into a different dex with the
    previous one's search still in the box reads as a bug.
  - 14 tests on the filter rules and 3 on the new lookups. Checked in the app: "chu" finds four,
    "not yet transferred" finds exactly the eight the counter promises, both switches give 481
    of 493, and a search that matches nothing says so instead of showing an empty grid frame.

An accent-folding bug worth naming, because it would have bitten anywhere else too:

- The search folds accents so "flabebe" finds Flabébé. The obvious implementation - decompose to
  FormD and drop the combining marks - compiles, runs, and does nothing at all here: this app
  sets `InvariantGlobalization`, which keeps the single file small but makes `String.Normalize`
  return its input unchanged. The accents are mapped by hand now, with a test that pins the two
  tables to the same length so a later edit cannot silently shift every mapping. The search also
  matches the species id, which is already punctuation-free, so "farfetchd" finds Farfetch'd.

- [x] Detail popup: opens for caught and uncaught entries alike - 2026-09-21
  - Nothing in it depends on status. The entry you have not found yet is exactly the one you
    need to read about, so an uncaught entry opens the same popup as a caught one - and shows
    its sprite in full colour, where the grid greys it.
  - A real `<dialog>` opened with `showModal()`, not a div pretending to be one. That hands over
    focus trapping, Escape, the backdrop, and returning focus to the tile that opened it. All
    four verified in the app: Escape closes it, and Enter straight afterwards reopens the same
    entry, which is only true if focus went back where it came from.
  - The tile is a `<button>` now rather than an `<article>`. It opens something, so it says so to
    the keyboard and to a screen reader instead of being a div with a click handler.
  - Closing is handled on the dialog's own close event rather than in each thing that closes it.
    Escape and the backdrop do not go through any of our code, so the selection would otherwise
    outlive the popup that showed it.
  - What it shows for now: sprite, number, name, typing, where it is, and the catch date and
    note when there are any. The acquisition sections are the next items; while the dataset has
    no encounter data for the game it says so in place of them, rather than looking empty for no
    reason.
  - Which types an entry has moved into `ReferenceData.TypesOf`, with 4 tests. A form's types
    are stored only when they differ from the species, so null there means "the same as the
    species" and not "none" - Alolan Vulpix is Ice, an odd-looking Vivillon is still Vivillon.

- [x] Acquisition sections ordered gift → wild → evolution → trade - 2026-09-21
  - The order runs from the surest way to the least sure: a starter you are handed cannot be
    missed, a wild slot is a chance, an evolution needs something else first, and a trade needs
    something to trade away. Reading top to bottom, the player meets the option that always
    works first.
  - The order lives in one place, the `AcquisitionKind` enum, and the grouping sorts by its
    values. A second list of the same four names would be a second thing to keep in step.
  - A kind nobody has a method for is left out rather than shown as an empty heading.
  - The sections gather methods from the main game *and* the linked games, because "how do I get
    this" is a question about the whole collection. Which of those comes first inside a section
    is the next item; for now they keep the order the dataset gives.
  - An empty list says which kind of empty it is. "The dataset has no encounter data for
    Platinum yet" and "no recorded way to get this in your games" are different answers, and the
    second one is a real fact about the Pokemon rather than a gap in ours.
  - `ReferenceData` gained `NameOf(target)` and `FindEvolutionRule(id)`. `DexBuilder` now uses
    `NameOf` too, so "Vulpix (Alolan)" is spelled in exactly one place instead of two.
  - 6 tests on the grouping and the names. Seen in the app against a seeded dataset: five methods
    handed in backwards came out as gift, wild, wild, evolution, trade, with the Emerald wild
    slot listed under the same heading as the Platinum ones and named as Emerald. The seeded
    files were restored afterwards; the real dataset still has no acquisition data.

- [x] Main-game methods before linked-game methods within each section - 2026-09-21
  - Inside a section the methods are sorted by game: the main game first, then the linked games
    in the order the player linked them. Where the main game can supply something, that is the
    answer; a linked game means catching it there and then moving it.
  - The sort is stable, so two methods from one game keep the order the dataset gave them. The
    games move, nothing else does.
  - A method from a game the collection does not include sorts last rather than first. It should
    not happen, but a dataset can hold one, and the failure has to be "an odd line at the bottom"
    rather than "the main game pushed off the top".
  - The page gathers per game and would already hand them over in that order, so this is belt
    and braces - but the order is now decided in one place instead of falling out of how the
    caller happens to loop.
  - 5 tests. No fresh screenshot for this one: the machine was in use and the app window kept
    being minimised, so rather than keep stealing focus I left it at the unit tests and the
    screenshot from the previous item, which already shows a linked-game slot listed under the
    same heading as the main game's.

- [x] Per-method detail fields rendered per the spec table - 2026-09-21
  - **Read this if the fields look wrong.** The specification is not in the repository, so there
    was no table to render from. Rather than stop, the fields were taken from the schema itself,
    which is the same information written twice over: every field an `AcquisitionMethod` carries
    is shown, in a fixed order per kind, and anything the dataset does not know is left out
    instead of printed empty. If the real table differs, it is one list per kind to change, in
    `FieldsOf` in `CollectionGrid.razor`.
  - Gift: where, from whom, level, what has to be true first.
  - Wild: how it is started, the level range, the slot chance, and time of day, season or
    weather when the slot is restricted to one.
  - Evolution: the rule as one sentence, for example "Level up, with friendship 220 or higher,
    during the day".
  - Trade: where, with whom, what the game wants in return, and what has to be true first.
  - Every method also shows where the claim came from and when the pipeline read it. That is
    what the citation on each record is for: a disputed encounter rate can be traced without
    rerunning anything.
  - The evolution wording is `EvolutionNames` in Core, with 6 tests. Conditions read as
    fragments that follow the trigger, and each condition type has its own wording rather than a
    dump of the record - including the prose escape hatch, which is printed as written.
  - Seen in the app against a seeded dataset covering all four kinds, then restored. The same
    screenshot shows the previous item working: Emerald's Safari Zone slot sits under the two
    Platinum slots in the wild section.

- [x] Evolution drill-down: click through to the previous stage, back control, breadcrumb - 2026-09-21
  - The evolution line in the popup is the way down: "From Pikachu" opens Pikachu in the same
    popup, with its own sections, so the question "and how do I get *that*" is answered without
    losing your place. Only evolutions lead anywhere; a wild slot or a gift is the end of the
    line and stays plain text.
  - The path is a `DexTrail` in Core with 8 tests, not a "currently showing" field. Back drops
    one step, a breadcrumb click drops everything after it, and going back to an entry already
    on the trail folds it rather than lengthening it - a chain that loops cannot grow the trail
    without end.
  - The breadcrumb only appears once you are drilled in. One entry needs no trail to explain
    itself.
  - A previous stage outside the collection's dex is shown anyway, built from the reference
    tables by `DexLines.For`, with 3 tests. A baby Pokemon the main game does not list, or a
    form the player switched off, is exactly where the chain is most worth reading, and refusing
    to draw it would break it there.
  - Walked in the app on seeded data: Raichu to Pikachu to Pichu, the breadcrumb growing to
    "Raichu > Pikachu > Pichu", then the Raichu crumb jumping straight back to the top with the
    breadcrumb disappearing again. The seeded files were restored afterwards.

- [x] Transfer route shown for non-main-game methods, alternatives collapsible - 2026-09-21
  - A method in a linked game now carries the rest of the answer: "Then to Platinum: Pal Park".
    Catching it there is only half the job, and the popup should not make the player go and look
    up the other half.
  - Nothing is shown for a method in the main game. There is nothing to move.
  - The shortest route is the line; everything else sits behind a "1 other way" disclosure. A
    native `<details>`, so it needs no state of ours and works from the keyboard.
  - When no route carries this particular Pokemon, the line says it cannot be moved and prints
    the engine's own explanation, which names the hop that refused and why - Pal Park only
    carrying National Dex 1 to 386, say. That branch is covered by the transfer engine's tests
    rather than by a screenshot; with the real dataset it needs a species Emerald can hold and
    Pal Park will not carry, which does not exist yet.
  - Routes are cached per game and entry while the popup is open. Several slots in one game
    would otherwise each pay for the same search.
  - New test: two edges between the same pair of games are two routes, not one. The alternatives
    list depends on it, and nothing had pinned it before.
  - Seen in the app on seeded data: the Emerald slot showing the route while the Platinum slot
    above it shows none, and the disclosure opening to reveal the second way. The seeded files
    are restored.

While seeding that, a foot-gun worth knowing: a hand-written transfer edge with no `filter`
carries nothing at all rather than everything, and says nothing about it. The pipeline always
writes one, so only hand edits can hit this - but the failure is silent, which is the worst kind.
Worth a validator rule if edges are ever written by hand.

- [x] Capture controls: three states, holding-game prompt, catch date, note - 2026-09-21
  - The first screen that writes to the data file. Three pills for the three states, a "held in"
    picker that appears only for "caught elsewhere", a catch date that appears only once
    something is caught, and a note that is always there.
  - The state and the holding game cannot contradict each other, because the state sets the
    game: the main game when it is home, the first linked game when it is elsewhere and none was
    recorded, nothing at all when it is not caught. Picking a game the other way round sets the
    state to match.
  - "Caught elsewhere" is offered disabled, with a reason, when the collection has no linked
    games. There is nowhere else for it to be.
  - The discrete choices save the moment they are made; the note is held while typing and written
    on blur, on stepping to another entry, and when the popup closes - Escape and the backdrop
    included, because those do not pass through any of our code. A save per keystroke would
    rewrite the whole file thirty times for one sentence.
  - Marking something caught stamps it with today's date, so the common case needs no typing.
    An existing date is never overwritten by it, and going back to "not caught" keeps the date
    rather than erasing it. Today is passed into the rule rather than read from the clock inside
    it, so it is decided once per action and can be tested.
  - A record that ends up saying nothing - not caught, no date, no note - is deleted rather than
    stored. Clicking a tile and unclicking it leaves the file exactly as it was. A record that
    still carries a note or a date is kept, so an accidental click cannot throw those away.
  - Saving retries once against what is on disk, like adding a collection, and then rebuilds the
    grid, the badges and the counter from what was written rather than patching them separately.
  - `CaptureEditing` in Core holds those rules with 7 tests: one record per entry, duplicates
    collapsing when written to, other collections untouched.
  - Walked in the app against a sandbox data file: Chimchar to "caught elsewhere" (the tile grew
    its arrow badge and the counter went from 8 to 9 still to transfer), then a catch date typed
    as 04/03/2026 landing in the file as 2026-03-04, then a note saved by pressing Escape. Piplup
    to "in Platinum" (counter 12 to 13, 2% to 3%) and back to "not caught", which removed the
    record and left the file exactly as long as before.

- [x] Quick toggle on the tile itself - 2026-09-21
  - The badge in the tile's corner is the control. Click it and the entry moves to the main game;
    click it again and it is not caught. From an entry sitting in a linked game it means "moved
    it", which is the step that was left to do.
  - Deliberately not a cycle through all three states. From the grid the useful move is always
    "it is home now" and the way back; choosing which linked game holds something is a decision,
    and decisions belong in the popup. The button's tooltip says which of the three it will do.
  - Marking it this way dates it today, the same as in the popup, because it goes through the
    same rule.
  - The tile stopped being a button and became a box with two buttons in it: one stretched over
    the whole tile that opens the detail, and the badge above it. A button inside a button is
    not markup a browser will accept, and the grid needed both.
  - A not-caught entry has no badge to show, but the control still has to be there to be
    clicked. It is a ring at a quarter strength that comes up to full on hover or focus: findable
    without speckling a grid of a thousand tiles. The three states still read without colour -
    grey sprite, arrow, tick.
  - Checked in the app: the toggle flipped Spearow to caught, the tile turned green, the counter
    went from 12 to 13 and 2% to 3%, the file gained a record with today's date - and clicking
    the tile itself still opened the detail rather than the toggle swallowing it.

- [x] Sprite caching, no runtime network calls - 2026-09-21
  - Already true by construction, so this item was mostly about proving it and keeping it true.
    All 1025 sprites are embedded resources in the exe - counted in the built assembly, not
    assumed - and served by the same provider that serves the web assets. The app has no
    `HttpClient`, and nothing it renders points at a server.
  - Two guards that read the repository rather than a library, because what they protect is a
    property of what ships:
    - every species in the dataset has a sprite file beside it;
    - no `src`, `href`, `url()`, `fetch` or `import` in the app's HTML, CSS, JavaScript or Razor
      names an http address. A URL in a comment is prose and is left alone.
  - The second guard was checked by breaking it on purpose: a Google Fonts stylesheet added to
    `index.html` failed the test, and was removed again. A guard that cannot fail is worth
    nothing.
  - The pipeline gained a matching rule, `every-species-has-a-sprite`, at warning level. The
    build already logged a failed sprite fetch and carried on, which is right - a hole in the
    grid is not worth throwing a build away for - but the hole now gets counted in
    `validation.json` instead of scrolling past in a log. A build run with `--no-sprites` says
    nothing rather than repeating itself 1025 times. 3 tests.
  - Caching itself needs nothing: the WebView asks for `sprites/x.png`, the provider hands back
    an embedded resource, and there is no round trip to make faster. The cost of a rebuilt
    dataset is a rebuilt exe, which is the trade this project already made.

- [x] End-to-end check: fresh collection -> catch Chimchar -> drill Infernape -> Monferno ->
      Chimchar - 2026-09-21
  - Walked from an empty data file with nothing skipped: "No collections yet", the wizard
    (name, Platinum, Emerald offered "via Pal Park" and ticked, forms), the collection written to
    the file and listed, the grid at "0 of 493, 0%".
  - Chimchar found by search, caught with the toggle on its tile: the tile went green, the
    counter went to "1 of 493, 1%", and the file gained one record - in the main game, dated
    today - and nothing else.
  - Infernape opened from the grid, then down the chain: "From Monferno" to Monferno, "From
    Chimchar" to Chimchar, with the breadcrumb reading Infernape > Monferno > Chimchar and each
    step showing its own evolution rule ("Level up, from level 36" and "from level 14").
  - The last screen is the point of the whole slice: Chimchar shown as in Platinum, caught on
    21/09/2026, with the starter it comes from - Route 201, Professor Rowan, level 5 - listed
    underneath. Everything the player needs about one entry, reached from a tile in two clicks.
  - The drill needed evolution rules and the starter gift, which the real dataset does not have
    yet: those are Phase 2 steps 4 and 5 for Platinum. They were seeded for the walk and removed
    again afterwards, so the check is honest about what exists today - the machine works, the
    data is what Phase 2 is for.

### Beyond the list

- [x] The game picker reads like a shelf: release order, no letterboxing, as many per row as
      fit - 2026-09-22
  - **A game now says when it came out**, and the picker sorts by it inside a generation: Ruby
    and Sapphire, then FireRed and LeafGreen, then Emerald. Alphabetical had Emerald first,
    which is not an order anyone thinks in. The date is the original Japanese release, because
    the order games came out in is one order and every region saw it shifted - Emerald reached
    Japan months before FireRed reached America. Mandatory in the pipeline, optional in the C#
    schema, which is the same shape `spriteSet` has: a dataset written before the field existed
    is still readable, and a dataset written now always carries it.
  - Title breaks a tie, which keeps the two halves of a pair - same day - together and in the
    same order every time.
  - **The covers had bars above and below them.** They sat in a fixed 3:4 frame, and no box art
    is 3:4: the Game Boy Advance boxes are square and Platinum's is wider than tall. The frame
    is gone for a game that has art - the image is the cover - and the height is what is fixed,
    so the names below still line up across a row. The drawn fallback keeps a frame, because it
    has no shape of its own to take.
  - **Two per row was a reading width applied to a grid.** `.step-body` capped the whole step at
    62ch, which is the right measure for a paragraph and the wrong one for a shelf of covers.
    The step is 940px now and what is prose inside it - the hints, the name field, the forms
    list - carries its own 62ch.
  - **The gap between cards only worked sideways.** A card stretches to its cell with
    `height: 100%`, and without `box-sizing: border-box` that meant 100% *plus* its own padding
    and border: 22px of overflow that ate the row gap while leaving the column gap alone. Found
    by measuring the screenshot rather than by eye, after the two directions disagreed.

- [x] Games are picked by clicking their box art, both the main game and the linked ones -
      2026-09-21
  - The dropdown and the checkbox list are gone. Both steps of the wizard now show a grid of
    covers; the main game is a set of radios, the linked games a set of checkboxes, with the art
    as the label. Real inputs, visually hidden, so the keyboard and a screen reader still get
    radios and checkboxes and the card only has to draw what they say.
  - A linked game that cannot feed the main game is still shown and still disabled, with its
    reason under the cover, and the "via Pal Park" line that says why an available one is
    available.
  - A game with no image still gets a drawn cover - its version name on a colour chosen by
    generation - which reads as a deliberate cover rather than as a broken image, and which is
    what a game whose art could not be fetched falls back to.
  - Two things this shook out. `LoadedDataset` had no way to answer "is there an image for this
    game", which is why it now carries the set. And a hand-built `RenderFragment` for the cover
    produced mis-nested markup - Blazor's sequence numbers are positions in the source, not a
    counter to increment - so it is an ordinary component now.
  - One CSS trap worth writing down: `.field label { display: block }` beat `.game-card` on
    specificity, which quietly flattened the card layout. The card rule is two classes deep now.

- [x] Box art is fetched by the pipeline rather than drawn - 2026-09-21
  - The covers come from the Bulbagarden Archives, which is where Bulbapedia's own game pages
    take theirs. Their `robots.txt` allows the file description page and the media itself while
    disallowing the API, so the pipeline reads the page for the image's address and follows it.
    Nothing touches `/w/`, and no URL is guessed at: the path carries a hash of the file name
    that is the wiki's business, not ours.
  - Each game names its own file in `gamedefs` - `Emerald EN boxart.jpg`, `Platinum EN
    boxart.png` - because the names follow no pattern across the series, not even the extension.
    Guessing one would break on the first game that spells it differently.
  - The page offers a preview beside the original, and the preview is what gets downloaded: a
    cover is drawn at 92 pixels in the app, and a 1500 pixel scan would put megabytes into the
    exe for nothing. Platinum is 617 KB and Emerald 103 KB as shipped.
  - `PoliteClient` now honours a site's declared `Crawl-delay` whenever it is the slower of the
    two. The Archives ask for five seconds and get five seconds; our own interval is a floor,
    never a licence to go faster than a site asked. 1 test.
  - `--no-box-art` skips the download, matching `--no-sprites`, and a build that skipped it says
    nothing rather than warning once per game. A game that has no cover after a real run is a
    warning, `every-game-has-box-art`, beside the sprite rule.
  - `.gitattributes` would have corrupted the JPEG: `dataset/** text eol=lf` was excepted only
    for `*.png`, so `emerald.jpg` came back as `text: set` from `git check-attr`. JPEG is marked
    binary now, verified the same way the sprites were.
  - The app keeps a file name per game rather than a flag, because the two covers are not the
    same kind of file. The picker asks the dataset what to load and serves whatever it is
    handed.
  - Both real covers seen in the running picker, whole rather than cropped: `object-fit:
    contain`, because a Game Boy box is square and a DS box is not, and cropping the top off a
    box is the one thing a box art picker must not do.
  - These are copyrighted covers, shipped inside a personal tool the same way the 1025 sprites
    already are. Worth knowing before this goes anywhere public.

- [x] The window opens maximised - 2026-09-21
  - `WindowState="Maximized"` on the main window. The 1280x800 size stays as what it restores
    down to, and the minimum size stays what it was, so nothing about resizing changes - only
    where it starts.

- [x] Every way of getting a Pokemon shows the games' own icon for it - 2026-09-21
  - Drawn glyphs were tried first and failed at the size they are shown: a tuft of grass came out
    as a letter Y, two footprints as punctuation. A 17-pixel box has room for one shape, not a
    scene, and the games already have a picture for nearly all of this.
  - The icons are item sprites from the same source as the battle sprites, so they sit in the
    popup as if they belong there: the three rods are three different rods, Surf and Rock Smash
    are their HM discs, a fossil is a fossil, an egg is an egg, a swarm is the Poke Radar.
  - Walking has no item of its own, so the ball you throw stands for a plain wild encounter. In-
    game trading has none either - Link Cable and Linking Cord have no sprite in the set - and
    that one stays drawn rather than borrowing a picture that means something else.
  - The mapping is data in the pipeline, one item name per method key, so a game that wants a
    different picture changes one line. The app asks the dataset whether an icon was shipped
    before drawing it, the same as it does for box art, so a build run with `--no-icons` shows
    nothing rather than a broken image.
  - 3 tests on the mapping and on a fetch that fails: a missing icon is skipped, not a stopped
    build.

---

## Phase 2 — Games

A game lands here only once all 8 steps are ticked and its validation run is green.

### A correction that touched all eight — 2026-09-22

Every game gathered its encounters for its **regional** dex and nothing else. The grid a player
sees is the **living** dex - `DexBuilder` builds it from `NationalDexThrough` for every game
that has a National Dex, which is all of them - so Diamond showed 493 tiles and could only ever
carry a method on 151 of them.

Noticed by Yannick, asking whether the pipeline only reads the regional dex. It did: one line,
`species = [entry.target.species for entry in entries]`, repeated in all four region modules.
Nothing in the TODO ever asked for that; step 3 is written as "**every** encounter slot".

- `BuildContext.living_dex` answers "every species this game asks a player to fill", and the
  build hands every builder the species table so it can. A game with no National Dex - none yet
  - falls back to its own dex, which for it is the same list.
- The coverage report counts the living dex too. It used to say Diamond was 146 of 151, which
  was true and answered a question nobody asked.
- `gift_encounters` logs the species it hands over that a game's gift table says nothing about.
  Widening the net catches gifts nobody has written up, and the number is the size of that job.
- `no-evolution-dead-ends` and `no-breeding-dead-ends` learned the difference between a hole and
  a generation nobody has built. Ruby knows how to finish a Bayleef; before Emerald was rebuilt,
  nothing in the dataset made a Chikorita, and seventeen errors said so one chain at a time. A
  dead end that leads out of every dex in the dataset is now one aggregated warning.
- Seven condition values surfaced that had never been asked about, and all seven are for
  species no regional dex lists: the legendary beast FireRed and LeafGreen pick by your starter,
  the birds Platinum sets loose after Professor Oak turns up in Eterna City, Cresselia after the
  Canalave nightmares, Regigigas with the three Regis in the party, the Water Labyrinth Togepi.

What it was worth, in species a game demonstrably produces:

| game | before | after |
| --- | --- | --- |
| Diamond, Pearl | 146 | 440 |
| Platinum | 205 | 450 |
| Emerald | 197 | 309 |
| Ruby, Sapphire | 197 | 281 |
| FireRed, LeafGreen | 154 | 280 |

Diamond hands over Bebe's Eevee, the Rotom in the Old Chateau, Heatran in its chamber under
Stark Mountain and the Cresselia that roams after the nightmares are cured. It said nothing
about any of them.

All eight rebuilt, validation green: 0 errors and 0 warnings. Three species in the whole dataset
are produced by nothing and explained by nothing - Celebi, Jirachi and Phione - and they are
visible now where before they were not even asked about.

### Generation 1

_Nothing yet._

### Generation 2

_Nothing yet._

### Generation 3

- [x] **Ruby** (`ruby`, gen 3, pair partner: Sapphire) - 2026-09-22
  - [x] 1 Entity + edges - 2026-09-22
  - [x] 2 Dex list - 2026-09-22
  - [x] 3 Wild - 2026-09-22
  - [x] 4 Gifts & statics - 2026-09-22
  - [x] 5 Trades & evolutions - 2026-09-22
  - [x] 6 Sprites - 2026-09-22
  - [x] 7 Events - 2026-09-22
  - [x] 8 Validate + smoke test - 2026-09-22
- [x] **Sapphire** (`sapphire`, gen 3, pair partner: Ruby) - 2026-09-22
  - [x] 1 Entity + edges - 2026-09-22
  - [x] 2 Dex list - 2026-09-22
  - [x] 3 Wild - 2026-09-22
  - [x] 4 Gifts & statics - 2026-09-22
  - [x] 5 Trades & evolutions - 2026-09-22
  - [x] 6 Sprites - 2026-09-22
  - [x] 7 Events - 2026-09-22
  - [x] 8 Validate + smoke test - 2026-09-22
  - The pair is built together, because a pair is the one case where two games really are one
    dataset with a switch in it. What they share is in `gamedefs/hoenn.py` - region, National
    Dex reach, the name of the Hoenn dex, the link cable - and each game file holds only what is
    true about itself. Emerald reads from the same module now, so the cartridge list and the
    edge factory exist once rather than three times.
  - They are still two entities, and the picker proves it: two cards, two covers, and Ruby can
    be linked to an Emerald collection without Sapphire coming with it.
  - Their own sprites are step 6. Declaring the set at step 1 would have pulled 386 files into
    every build for a game with no dex yet.
  - **Two things the pair broke on arrival, both worth having found now.**
  - A both-ways route declared from both ends was two rows in the graph. Nothing noticed while
    only Emerald declared GBA trades; the moment Ruby named Emerald and Emerald named Ruby, the
    transfer file held the same route twice - and the app expands a both-ways edge into both
    directions itself, so it would have drawn four. The registry now keys a both-ways route on
    its unordered ends. A one-way route keeps its order: Pal Park into Platinum is not the same
    claim backwards.
  - `pair_partner` had been in the schema since Phase 0 with nothing ever reading it. Ruby and
    Sapphire are the first pair the dataset has held, so `version-pairs-name-each-other` now
    checks that both halves are present and name each other. It found two dangling partners in
    the committed sample on its first run - sword named a shield that was not there, diamond a
    pearl - which is a fair advertisement for it.
  - Step 2 was one function, not two. The three cartridges share these 202 entries *and their
    numbering*, so `hoenn.dex_entries` answers for all of them and each game passes only its own
    table of what it cannot hold. Emerald reads it too now, so its own copy is gone.
  - Neither of the pair brings an unobtainable table yet. Which entries a cartridge's own grass
    never holds is a fact about its encounters, and those are step 3; writing it down first
    would be a guess with a citation on it.
  - So the build is red, 6 errors per game, and they name exactly the six nobody can produce
    yet: Surskit, Meditite, Roselia, Zangoose, Lunatone and Jirachi. Emerald was red the same
    way from its step 2 until its step 5. Coverage reads 0 full, 196 partial, 6 missing for
    each of the pair, which is the true picture: everything they list is a transfer away.
  - Deoxys is still the one form question, and still waiting for the forms table. It takes a
    different forme in each of the three cartridges, which is exactly the case the table exists
    for, and none of the three can say so until it is filled.
  - Step 3 cost five seconds and no requests. PokeAPI answers `/pokemon/<name>/encounters` with
    every version at once, so Emerald's run had already fetched everything the pair needed; the
    version is a filter over a response that was on disk.
  - Ruby: 691 slots over 114 species and 59 places. Sapphire: 692, 114, 59. Emerald: 706, 115,
    63 - the third version widened the Safari Zone, which is where most of the difference is.
  - The version exclusives come out right, which is the check that the switch is doing real work
    rather than building the same data twice. Ruby alone has Seedot, Nuzleaf, Zangoose, Solrock,
    Mawile, Dusclops and Latios; Sapphire alone has Lotad, Lombre, Seviper, Lunatone, Sableye,
    Banette and Latias. Two tests pin it: one that each half reads its own version of a shared
    encounter table, and one that a species only the other half has brings no slot at all rather
    than an empty one.
  - Doing the pair together paid for itself here. Twelve errors became two: Zangoose is on Ruby
    and Lunatone on Sapphire, so each half accounts for the other's exclusive the moment both
    exist. Surskit, Meditite and Roselia are now produced by the pair, which is what Emerald's
    unobtainable reasons said would happen - and it means Medicham and Masquerain have a real
    source in the dataset rather than only a stated one.
  - Only Jirachi is left, in both, and it is the same event-only distribution Emerald marks.
    That is step 4.
  - 88 dex entries have no wild slot in either half, against Emerald's 87. Those are the gifts,
    statics, trades and evolutions of steps 4 and 5.
  - Step 4: 19 gift and static records each, and one table for the two of them. They agree about
    every species they both have, so `hoenn.PAIR_GIFTS` is written once; where they differ they
    differ by *which* species turns up at all - Groudon in one Cave of Origin and Kyogre in the
    other - and a key the other half never sees simply never matches. Emerald keeps its own
    table, which reads the same in places and must not be merged: its legendary hides in a cave
    that moves and its Rayquaza waits on a fight only it has.
  - Southern Island is the nice inversion. Ruby's island holds Latias and Sapphire's holds
    Latios, each the opposite of the one roaming its own Hoenn - and the wild step had already
    produced exactly that mirror, from the other direction.
  - The version exclusives are seven a side and mirror exactly, which is a test now: a species in
    both lists would mean one of the two tables is wrong. Ruby cannot hold Lotad, Lombre,
    Sableye, Seviper, Lunatone, Banette or Kyogre; Sapphire cannot hold Seedot, Nuzleaf, Mawile,
    Zangoose, Solrock, Dusclops or Groudon.
  - **Validation went green at step 4**, where Emerald stayed red until step 5. The pair covers
    each other: everything one half keeps, the other can produce, so nothing is unaccounted.
    Coverage is 127 full, 67 partial, 0 missing, 8 unobtainable for each.
  - **A shipped Emerald record turned out to be wrong, and building the pair is what caught it.**
    Emerald said of each fossil "only one of the two can be taken", which is the opposite of the
    truth: the Desert Underpass exists only in Emerald, and the fossil left behind at the Mirage
    Tower waits at the end of it once the Elite Four are done. Ruby and Sapphire are the games
    where the choice really is final. Both wordings corrected.
  - The 67 still unexplained are evolutions, which is step 5. Deoxys is among them: the Aurora
    Ticket that reaches Birth Island never came to these two, so it is likely a step 7 answer
    rather than a step 5 one.
  - Step 5 closed all 67 but one. Each half now carries 97 evolutions, 3 in-game trades and the
    same 3 babies, for 813 and 814 methods. Coverage: 193 full, 1 partial, 0 missing, 8
    unobtainable.
  - Three trades, shared, where Emerald swapped them for four of its own: a Makuhita for a
    Slakoth in Rustboro, a Skitty for a Pikachu in Fortree, and a Corsola for a Bellossom in
    Pacifidlog. The last one is the only trade in either generation that asks for something you
    have to build first - a Bellossom takes a Sun Stone on a Gloom - so it says so.
  - The version group is the pair's own, `ruby-sapphire`, where Emerald is its own group. Both
    are Generation 3 and the difference is the point: the arithmetic is an ordering, not a
    generation.
  - Ruby evolves Lombre into Ludicolo although it can never catch a Lotad. That is right, and it
    only reads as right because of the change that came with Emerald's validation step: a stated
    reason counts as an answer, and Lombre carries one - "Sapphire only; trade one in". Trade a
    Lombre in and Ruby will evolve it.
  - The shared tables are module-level in `hoenn` now rather than passed in. Two copies of the
    same three trades is how one of them gets edited and the other does not.
  - **Only Deoxys is left**, in both, which is exactly what step 4 predicted. The Aurora Ticket
    that reaches Birth Island was never handed out for these two, so this is a step 7 answer
    rather than anything step 5 can give - the first time the new step has had a question waiting
    for it before it ran.
  - Step 6 cost one fetch for two games. They name the same directory, `generation-iii/ruby-
    sapphire`, and the build already collapsed a set to one download however many games declare
    it - so the log reads "ruby sprites: 386 species" and says nothing at all about Sapphire.
    386 files, about 1 MB, beside Emerald's own.
  - Worth checking that the two sheets are actually different, or the whole exercise is
    ceremony: 335 of the 386 are byte-identical and **51 were redrawn for Emerald**, Blaziken and
    Butterfree among them. A game does get its own look out of this.
  - And the check that mattered more: **nothing had ever been embedded**. Emerald's step 6 shipped
    a csproj glob of `dataset/sprites/*.png`, which is neither recursive nor path-preserving, so
    every per-game directory reached the repository and none of them reached the exe. The app had
    been falling back to the shared set since that step, while a screenshot of it was read as
    proof that it was not. The glob is `**` now, the logical name keeps `RecursiveDir`, and the
    assembly carries 772 nested sprites where it carried 0.
  - The guard for it asserts the build rule rather than the exe, because the test project does
    not reference the app. It was verified the only way such a test is worth anything: by
    flattening the glob again and watching it fail.
  - Step 7 answered Deoxys, the question step 5 left open. It was never catchable in either
    half: two 2006 distributions handed the Pokemon itself over, the Space Center Deoxys in the
    United States and the Doel Deoxys in the Netherlands - where Emerald's Aurora Ticket instead
    opened the island it waits on. Marked unobtainable in both, with that as the reason.
  - Ten of the twelve remaining entries had an event. Most share the 2006 Japanese campaign that
    already covered Emerald's; Sableye, Seviper, Mawile and Zangoose were also given away in
    English at the Pokemon Center in New York in the summer of 2004, and those carts were Ruby
    and Sapphire specifically. Kyogre and Groudon had no Generation 3 giveaway at all, so their
    reasons say nothing extra rather than reaching for one.
  - Lombre and Nuzleaf have no event of their own and did not need one: a Lotad and a Seedot from
    that same campaign evolve into them, and the reason says so.
  - **Step 7 caught a mistake from step 4 before writing anything.** Banette was marked "Sapphire
    only" on Ruby and Dusclops "Ruby only" on Sapphire - and each cartridge catches the stage
    below and evolves it. The exclusives were worked out from encounter tables at step 4, before
    step 5 added the evolutions, and nobody went back. Both removed; the lists are six a side.
  - `unobtainable-entries-really-are` now guards it: a game that can reach an entry on its own -
    something it catches or is handed, and then whatever those evolve or hatch into - must not
    also claim it cannot. It fired on exactly those two and on nothing else. Emerald evolving a
    Medicham from a Meditite it cannot catch is not reachable on its own and is left alone, which
    is the distinction that makes the rule usable.
  - Emerald's own reasons now read from the shared wording rather than a second copy of it. The
    2006 campaign covered all three cartridges, so the sentence lives in one place.
  - Validation green at 9 rules, 0 errors, 0 warnings. Coverage is identical for the two of
    them: 194 full, 0 partial, 0 missing, 8 unobtainable.
  - Smoke test on a collection with Ruby as main game and Sapphire linked, which is the pair's
    own route and the thing worth looking at. Seviper reads the whole chain in one popup: **Not
    in Ruby** with the reason and the two events that handed one out, then Sapphire's Route 114
    slot, then "Then to Ruby: trading". Deoxys shows its reason and no ways at all, which is
    right - neither half can produce one.
  - The collection was created, read and deleted again; the data file is byte-identical to what
    it was before, and the backup the app wrote during the test was removed with it.
  - The catch toggle was not exercised here. It is the same code Emerald's smoke test already
    went through, and running it again would only have written more to a file that had to be put
    back.
  - One thing the test caught that had nothing to do with the data: the reason on screen was a
    sentence short, because the Debug build still had the dataset from before step 7. The exe
    bakes the dataset in at build time, so a stale build shows stale data and looks entirely
    healthy doing it.
- [x] **Emerald** (`emerald`, gen 3, standalone) - 2026-09-22
  - [x] 1 Entity + edges - 2026-09-21
  - [x] 2 Dex list - 2026-09-21
  - [x] 3 Wild - 2026-09-21
  - [x] 4 Gifts & statics - 2026-09-21
  - [x] 5 Trades & evolutions - 2026-09-22
  - [x] 6 Sprites - 2026-09-22
  - [x] 7 Events - 2026-09-22
  - [x] 8 Validate + smoke test - 2026-09-22
  - Validation went green by fixing the rule rather than the game. `no-evolution-dead-ends`
    called Medicham a dead end because nothing in the dataset produces a Meditite - which is
    true, and which the dex already answered in as many words: "Ruby and Sapphire only in
    Generation 3; trade one in". `every-entry-has-a-method` had always accepted a stated reason
    as an answer; the two dead-end rules now do the same, and a previous stage nobody has
    written anything about is still an error.
  - 7 rules, 0 errors, 0 warnings. Coverage: 196 full, 0 partial, 0 missing, 6 unobtainable.
  - Smoke test on a collection with Emerald as its main game. The grid draws 386 entries in
    Emerald's own sprites; "Available in Emerald" shows 197 of them, which is the 196 the
    coverage report counts plus Meowth - obtainable here through the Battle Frontier trade and
    not in the Hoenn dex, so the report never counted it. Two numbers from two sides of the
    wire agreeing is the check.
  - Detail popups read correctly for every kind: wild slots with levels and chance, the day
    care with both parents as links, in-game trades with who wants what, and evolutions with
    Generation 3's own rule. Drilling from Pichu to Pikachu and back keeps the trail.
  - The write path was exercised and put back: marking Pikachu caught moved the counter to
    1 of 386, greened the tile and wrote a record with today's date. Setting it back to not
    caught leaves the record with its date, which is deliberate - "an accidental click must not
    erase it" - so the file is not byte-identical afterwards by design.
  - Events arrived as a step after this game was already finished, so it was done
    retroactively - and at the time it was numbered 8, after validating. The two were swapped
    afterwards, so the numbers above read 7 and 8 while Emerald did them the other way round.
    Nothing turns on it here: the events changed no reason that the validation run depended on.
  - All six
    of the entries Emerald cannot produce turned out to have been distributed at an event, and
    five of them at the same one: a Japanese campaign that ran for three weeks in 2006 and
    covered Ruby, Sapphire, Emerald, FireRed and LeafGreen alike. Surskit had a second, the
    PokePark Egg of 2005. Jirachi is the only one whose reason *is* the event.
  - The place to look is the species' own "In events" section on Bulbapedia, which says which
    games each distribution was for - the part that matters, since a Generation 4 giveaway is no
    use to a Hoenn cartridge.
  - Nothing about what is obtainable changed, and the validation run did not move: an event that
    closed twenty years ago is not a way to fill a dex. What changed is the answer a player gets
    when they ask where one comes from at all.
  - The app did not show any of this until now. `UnobtainableReason` had been carried through the
    schema, the loader and `ReferenceData` since Phase 0.7 with no screen reading it, so a player
    looking at Zangoose in an Emerald collection saw "No recorded way to get this in your games" -
    true of Emerald, and unhelpful, because the dataset knew it was a Ruby Pokemon and said so.
    The detail popup now has a **Not in <game>** section carrying the reason, and it is shown even
    when there are ways listed: those ways are all in other games, and the reason is the sentence
    that explains why. `ReferenceData.FindDexEntry` is the lookup behind it.
  - A game now declares every route it has, including ones to games that are not written yet.
    Emerald claims a both-ways trade with Ruby, Sapphire, FireRed and LeafGreen; the registry
    holds each of those back until the other end exists and the build says which are waiting.
    Adding Ruby will light its edge up without anyone editing Emerald, and either side may
    declare a shared edge because duplicates collapse.
  - Pal Park stays with the Generation 4 game that receives, where its National Dex limit is a
    fact about the receiver rather than about Emerald.
  - The dex list is the 202-entry Hoenn dex with Emerald's own numbering, Treecko #001 to Deoxys
    #202, from PokeAPI's `hoenn` - not `updated-hoenn`, which is Omega Ruby and Alpha Sapphire's
    211. Ruby and Sapphire share it, so their step 2 can ask for the same thing.
  - That list is the game's own Pokedex, not what a living dex here is aiming at. The target is
    the National Dex through 386, which the entity already carries; this one is what the
    coverage report measures encounters against.
  - Deoxys is the one form question in this game - it takes its Speed Forme in Emerald - and it
    waits for the shared forms table, which is still empty. Nothing else in Hoenn has a form.
  - Building a game needed the PokeAPI client, which a builder had no way to reach. `BuildContext`
    carries it now, and one client is opened for the whole run rather than one per step.
  - Wild slots come from PokeAPI, not from a scraper. The note in `pokeapi.py` said encounter
    detail was a scraper's job; that was written before anyone looked. PokeAPI carries the games'
    own encounter tables - area, method, level range, slot chance, per version - already
    structured and citable, and a wiki would have been slower, more fragile and no more true.
    706 slots, 115 species, 63 places.
  - PokeAPI lists one row per level, so they are added back up: one record per place, method and
    condition, carrying the whole level range and the chance of meeting it at all. Poochyena on
    Route 101 is "levels 2 to 3, 45%", not four rows.
  - Place names come from the parent location, not the area: PokeAPI generates area names and
    calls Route 101 "Road 101". Whatever is left of the area slug becomes the sub-area, so Cave
    of Origin keeps its B1F.
  - Two of PokeAPI's methods can land on one of ours - a roamer is listed once for grass and once
    for water - and two records a player cannot tell apart are dropped to one. Their chances are
    not added: those are two ways of meeting one Pokemon, not two slots in a table.
  - Gifts, statics and trades are skipped here rather than bent into wild slots. That is what the
    87 entries still unaccounted for are, and they are steps 4 and 5.
  - Encounters hang off a Pokemon rather than a species, and for anything with forms the two are
    spelled differently - the species is `deoxys`, the Pokemon is `deoxys-normal`. The default
    form is resolved first; asking by species name is a 404.
  - **Emerald's validation is red until step 5.** A dex with nothing behind it is exactly what
    step 1 produces, and the build said so in one line rather than two hundred: "none of its 202
    dex entries has a way to be obtained". It stays an error, so the build keeps failing until
    the encounters are there. Step 3 left 87 entries named one line each, step 4 leaves 70, and
    every one of those is an evolution waiting for step 5.
  - Gifts and statics come from the same encounter tables as the wild slots, with the other
    methods taken out: `gift`, `gift-egg`, `static`, and the item-in-hand ones like `devon-scope`
    that are one Pokemon standing in one place. 23 records, 20 species.
  - What PokeAPI cannot say is who hands a Pokemon over, what you had to do first, and whether a
    "gift" is a starter, a fossil or a present - it is one word for all three. That half is a
    table in `emerald.py`, and the module only joins the two: the general kind is the default and
    a game says when it is something more particular.
  - A gift record has one line for where it happens, so the sub-area is read into it rather than
    dropped: "Route 119, Weather Institute", "Sky Pillar, Apex".
  - An encounter's conditions name the item it depends on, so a fossil's requirement can be read
    off the data. The game's own sentence beats it when there is one: "Claw Fossil" is true but
    thin next to where the fossil comes from and that taking one means not taking the other.
  - Distribution events are not a way to fill a dex. `colosseum-bonus-disc-jpn` is skipped with a
    line in the log, and Jirachi - which has no other source - is marked unobtainable with the
    reason, which is what keeps it out of the list of things the data is missing.
  - The two tickets are the other half of that: Latias, Latios and Deoxys are in the game and the
    boat ride to them was only ever handed out at events, so they keep their records and say so
    in the requirement.
  - Zangoose and Lunatone are in the Hoenn dex and not in Emerald - it kept Seviper and Solrock
    and left the other half of each pair on Ruby and Sapphire. Marked unobtainable here, naming
    the cartridge that has them; the transfer graph is how they get filled, which is the whole
    reason a route from Ruby exists.
  - Step 5 turned 70 unexplained entries into 67 evolutions, 3 babies and 4 trades, and three
    entries that were never holes at all.
  - PokeAPI stamps every evolution detail with the version group it *started* in, so "which
    evolution triggers are actually possible here" is arithmetic rather than a hand-written
    list: take the newest variant at or before the game being built. Emerald gets Feebas's
    Beauty and not Black and White's Prism Scale, and no Gallade, Froslass, Roserade or
    Probopass, without anyone writing any of those five facts down.
  - Rules are global and the table holds every variant, so an id is `<from>-to-<to>` only while
    there is one way to do it. A pair with more than one names the version group each started
    in - `feebas-to-milotic-ruby-sapphire` beside `feebas-to-milotic-black-white` - rather than
    one of them holding the plain id and the rest looking like afterthoughts.
  - The shared table is built from chains rather than species: 1025 species are a few hundred
    chains, and everything in one chain shares it.
  - In-game trades are a table in the game's own file, because no API carries them. Four of
    them, and not one is the only way to get what it gives - Meowth is not even in the Hoenn
    dex. They are recorded because they are true.
  - **Breeding became a fifth acquisition kind**, on both sides of the wire. Pichu, Igglybuff
    and Azurill hatch from the day care and do nothing else, and filing them under `gift` would
    have said an NPC hands them over. A record lists every parent that works, because any one
    of them is enough: a Pichu comes from a Pikachu *or* a Raichu.
  - `no-breeding-dead-ends` came with it and guards the same lie its evolution twin does. It is
    not in the spec's list of checks; a kind that can claim "hatch a Pichu" to someone with no
    way to get a Pikachu needs one.
  - Three entries step 3 left unexplained turned out to be the game rather than the data.
    Roselia and Meditite are in Ruby and Sapphire's grass and not in Emerald's. Surskit is in
    Emerald, but only as a swarm, and an Emerald swarm only offers it after records have been
    mixed with a Ruby or Sapphire cartridge - a second cartridge, the same as the other two.
    All three are marked unobtainable with the reason.
  - Surskit is the one place the schema is visibly short. `WildAcquisition` has no
    `requirement`, so a swarm record would have read "Route 102, walking" and sent a player to
    wait for something that never comes. Worth a nullable field the next time a game needs one.
  - Step 6 made sprites a per-game choice rather than one set for everybody. A game names the
    directory its own sprites live in - Emerald's is `generation-iii/emerald` - and the grid
    draws the main game's set, so an Emerald collection looks like Emerald rather than like
    2026. 386 files, about 250 KB, because a Generation 3 sprite is 64x64.
  - The shared set stays and is still built for all 1025 species. It is the documented fallback
    the checklist asks for: a set only covers what its generation drew, so a Turtwig transferred
    into a Hoenn collection is drawn in today's artwork rather than not at all. The app decides
    per species, by asking whether the file shipped, which is the same question it already asks
    about a method icon.
  - The linked games get no say. A grid is one dex and one look, and the main game is whose dex
    it is.
  - The CSS needed nothing: the tiles were already fixed boxes with `object-fit: contain` and
    `image-rendering: pixelated`, so a 64x64 sprite upscales cleanly instead of blurring.
  - `spriteSet` is an init property on the C# `Game` rather than a tenth constructor parameter.
    Every game built before this step is still a valid game without one, and the positional
    record has nine parameters already.
  - Form sprites are still not here. `SpriteFor` used to promise them for this step; the forms
    table is empty, so there is nothing to draw them for yet, and the comment now says so
    instead of pointing at a step that has been done.
  - **This step shipped broken and was reported as working.** The csproj globbed
    `dataset/sprites/*.png`, which is not recursive and which flattens what it does match, so the
    386 Emerald sprites were written to disk, committed, embedded nowhere, and silently fallen
    back on. The app drew the shared set the whole time. It was checked by eye against a
    screenshot and the shared Charizard was mistaken for the Generation 3 one - a sprite that
    looks right at a glance is exactly what a fallback is for, which is why looking was not a
    check.
  - Fixed while building Ruby and Sapphire, whose set had the same problem: the glob is `**` now
    and the logical name keeps `RecursiveDir`, so a sprite is embedded under the directory it
    came from. 772 nested resources where there were 0.
  - `The_app_embeds_every_sprite_directory_rather_than_only_the_top_one` guards it. It asserts
    the build rule rather than the exe, because the test project does not reference the app - and
    it was proved by flattening the glob again and watching it fail.
- [x] **FireRed** (`firered`, gen 3, pair partner: LeafGreen) - 2026-09-22
  - [x] 1 Entity + edges - 2026-09-22
  - [x] 2 Dex list - 2026-09-22
  - [x] 3 Wild - 2026-09-22
  - [x] 4 Gifts & statics - 2026-09-22
  - [x] 5 Trades & evolutions - 2026-09-22
  - [x] 6 Sprites - 2026-09-22
  - [x] 7 Events - 2026-09-22
  - [x] 8 Validate + smoke test - 2026-09-22
- [x] **LeafGreen** (`leafgreen`, gen 3, pair partner: FireRed) - 2026-09-22
  - [x] 1 Entity + edges - 2026-09-22
  - [x] 2 Dex list - 2026-09-22
  - [x] 3 Wild - 2026-09-22
  - [x] 4 Gifts & statics - 2026-09-22
  - [x] 5 Trades & evolutions - 2026-09-22
  - [x] 6 Sprites - 2026-09-22
  - [x] 7 Events - 2026-09-22
  - [x] 8 Validate + smoke test - 2026-09-22
  - Built as a pair, the way Ruby and Sapphire were, and the shared half is `gamedefs/kanto.py`.
  - **A third module came out of it.** `hoenn.py` was holding facts that are not about Hoenn at
    all: the link cable between the five Generation 3 cartridges, the generation itself, the
    National Dex stopping at 386. Kanto would have had to copy them, which is the exact failure
    a shared module exists to prevent, so they moved to `gba.py` and both regions read from it.
    `hoenn.py` is the region now; `gba.py` is the hardware.
  - **Platinum's Pal Park edges were wrong and this is what exposed it.** It named Emerald alone,
    correct in Phase 1 when Emerald was the only Generation 3 game in the dataset, never widened
    when Ruby and Sapphire arrived. So those two reached Generation 4 only the long way round -
    the picker said "via trading, then Pal Park" and that was the truth about the data, not about
    the games. Pal Park takes any Game Pak in the slot; all five cartridges declare the route now.
    4 edges became 15, and nothing is held back any more.
  - The dex is PokeAPI's `kanto`, the same 151 Red and Blue show, in the same order - the
    resource lists `firered-leafgreen` among its version groups, which is the check that it is
    the right list. The National Dex the games also get after the Elite Four is the entity's
    reach, not the game's own Pokedex.
  - **A validation rule had to be loosened, and the Kanto dex is what broke it.**
    `every-entry-has-a-method` collapses an unfinished game into one finding instead of hundreds,
    but it asked that *nothing* in the game's dex be explainable anywhere. That held for Emerald,
    the first game to meet it, because nothing else produced a Hoenn species. A third of the 151
    are caught in Hoenn too, so the pair fell past the guard and reported 103 separate faults each
    for the one fact that their encounters were not gathered yet. The test is now "this game
    brings no methods of its own", which is the question that was meant all along.
  - Step 3: 902 wild slots for FireRed, 903 for LeafGreen. Ekans and Growlithe on FireRed,
    Sandshrew and Vulpix on LeafGreen, Oddish against Bellsprout - the exclusives split exactly as
    they should, which is the best evidence the version filter is not merging the two tables.
  - Mankey and Meowth are in *both* halves here, although they were exclusives in Red and Blue.
    Checked on Bulbapedia rather than assumed: FireRed and LeafGreen share one row for them.
  - Step 4: 25 gift and static records each. The Game Corner is the one table the halves really
    disagree about - not only which Pokemon stands in the window (Scyther on FireRed, Pinsir on
    LeafGreen) but what the same one costs: Abra is 180 coins against 120, Porygon 9999 against
    6500. So the prizes are keyed by version and folded into the shared table.
  - The fossil left at Mt. Moon is gone for good, unlike Emerald's. Bulbapedia lists Mt. Moon as
    the only source of either, and it is a choice between them. The Old Amber is nobody's rival:
    its own item, out of the Pewter Museum of Science.
  - Mewtwo waits on the Sevii Islands, not on the Elite Four: Cerulean Cave opens when the
    Network Machine in the Pokemon Network Center works.
  - Step 5: 83 evolutions and 9 in-game trades each. Three of the trades differ by version, and
    one of them in a way worth writing down: the man on Route 18 hands over the same Lickitung in
    both games but wants a Golduck on FireRed and a Slowbro on LeafGreen. It is not in any plain
    text on the page - it had to be read off the background colour of the FR and LG columns - and
    it is coherent with the rest: FireRed has no Slowpoke and LeafGreen no Psyduck, so each half
    asks for something you can actually raise there.
  - The Four Island day care is deliberately absent. It exists, but a Kanto dex is 151 entries and
    every baby Pokemon is Generation 2 or later, so nothing these games hatch is anything this dex
    asks for. Ruby and Sapphire hatch three because their dex has three to hatch.
  - **The exclusives were derived after step 5 rather than at step 4, on purpose.** Ruby's list was
    worked out from encounter tables before evolutions existed and wrongly held Banette; Sapphire's
    held Dusclops. Both are caught nowhere and evolve from something the cartridge has, and reading
    only the grass cannot tell the difference. Waiting until trades and evolutions were in gave
    seven a side, mirrored exactly, first time.
  - Step 6: 386 sprites in `generation-iii/firered-leafgreen`, one sheet for the two of them.
    Checked three ways after what happened with Emerald: the files on disk, 386 resource names per
    set inside `LivingDex.dll`, and the same tile cut out of a FireRed grid and an Emerald grid in
    the running app and enlarged side by side. Different Charizards.
  - Step 7: thirteen of the fourteen exclusives had a distribution. The Pokemon Trade and Battle
    Day, one day in American shops in September 2004, covers nine of them; the Gather More
    Pokemon! Third Campaign covers most of the rest. Note the *Third*, not the Fifth the Hoenn
    cartridges name - different months, different species. Mew has three that reached these
    cartridges: the Hadou Mew, the Mystery Mew and the Aura Mew.
  - **Pinsir is the exception**, and it is a fact rather than a gap: nothing ever distributed one
    for these games. Its reason ends at "trade one in", and a test pins that it has no event
    sentence.
  - Bulbapedia's *Game locations* "Event" marker is not reliable for this. Slowpoke's row says
    only "Trade", while its *In events* table lists a 2004 FRLG distribution. All sixteen reasons
    were taken from *In events*.
  - Coverage: 143 full, 0 partial, 0 missing, 8 unobtainable for each - 151 either way.
  - Smoke test: a FireRed collection with LeafGreen linked, in the published exe. The filter row
    offers both games; Vulpix shows "Not in FireRed" with the LeafGreen sentence and the 2004
    event underneath, and its LeafGreen routes with "Then to FireRed: trading"; Farfetch'd shows
    the Vermilion City trade with Elyssa on both cartridges. The user's own data file was copied
    out first and restored byte for byte afterwards.


### Generation 4

- [x] **Diamond** (`diamond`, gen 4, pair partner: Pearl) - 2026-09-22
  - [x] 1 Entity + edges - 2026-09-22
  - [x] 2 Dex list - 2026-09-22
  - [x] 3 Wild - 2026-09-22
  - [x] 4 Gifts & statics - 2026-09-22
  - [x] 5 Trades & evolutions - 2026-09-22
  - [x] 6 Sprites - 2026-09-22
  - [x] 7 Events - 2026-09-22
  - [x] 8 Validate + smoke test - 2026-09-22
- [x] **Pearl** (`pearl`, gen 4, pair partner: Diamond) - 2026-09-22
  - [x] 1 Entity + edges - 2026-09-22
  - [x] 2 Dex list - 2026-09-22
  - [x] 3 Wild - 2026-09-22
  - [x] 4 Gifts & statics - 2026-09-22
  - [x] 5 Trades & evolutions - 2026-09-22
  - [x] 6 Sprites - 2026-09-22
  - [x] 7 Events - 2026-09-22
  - [x] 8 Validate + smoke test - 2026-09-22
  - Built as a pair, the way both Generation 3 pairs were. The shared half is
    `gamedefs/sinnoh.py`; what every Generation 4 cartridge shares - the wireless trading
    between all five, the National Dex to 493, Pal Park out of the slot underneath - is
    `gamedefs/ds.py`, which Platinum now reads from as well.
  - 146 full and 5 unobtainable per game, validation green on all 9 rules.
  - **The three Sinnoh games do not share a dex.** Ruby, Sapphire and Emerald all show the same
    202 entries, so `hoenn.py` names one. Platinum widened the regional list from 151 to 210,
    and PokeAPI keeps the two apart: `original-sinnoh` belongs to version group `diamond-pearl`,
    `extended-sinnoh` to `platinum`. The constant is `PAIR_DEX` for that reason, and Platinum
    will name its own.
  - **Generation 4 conditions were being dropped, and some of them were the whole answer.**
    Its encounter tables mark every row with the state of the world it is filled in. Generation 3
    has three such rows in the entire dataset; Sinnoh has over a thousand, and Gengar is in the
    Old Chateau *only* while a Generation 3 cartridge is in the Game Boy Advance slot. The old
    wild step logged them and threw them away, which would have printed a route and hidden the
    hardware. `WildAcquisition` gained a `requirement`, in the pipeline and in C#, and the detail
    popup shows it as "Needs". 416 slots per game carry one.
  - The phrasing lives in `conditions.py`, shared with the gift step, because both read the same
    tables. That closed a second hole: gifts only ever read *item* conditions, so Drifloon said
    nothing at all. It now reads "On a Friday, once Team Galactic is beaten at the Valley
    Windworks" - one sentence out of two bare facts.
  - Rows marking the ordinary state of the world - "no swarm", "no Poke Radar", "nothing in the
    slot underneath" - are one slot, not four, and their chances add up. A conditional row is
    dropped where the same place already holds the species unconditionally: Stunky stands on
    Route 206 whatever is in the slot, and five rows naming cartridges help nobody.
  - **That rule ate a true condition on its first outing.** PokeAPI writes a roamer down twice,
    once for grass and once for water, and hangs the condition on only one of the two. Latias in
    Emerald: both rows level 40 at 25%, and only one says she is not loose until the Elite Four
    are beaten. Two rows alike in place, level and chance are one encounter written twice, and
    the fuller one wins. Generation 3's only three conditioned slots are exactly this, so Ruby,
    Sapphire and Emerald gained four true sentences they had never carried.
  - **PokeAPI is wrong about the fossils.** It files both under both halves. Bulbapedia is clear
    - Skull Fossil in Diamond's Underground, Armor Fossil in Pearl's, and the Cranidos page says
    "Trade" for Pearl outright. `gift_encounters` gained an `excluded` table that names the
    species *and the reason*, so the disagreement is recorded rather than quietly tidied away.
  - **`only_on` said "Generation 3" in a string.** Diamond would have told a player to trade a
    Shieldon in from a Generation 3 game. The sentence moved to `gamedefs/exclusives.py` with
    the generation as a parameter, and both hardware modules wrap it.
  - A fossil is an item, so it can cross the link held by a traded Pokemon and be revived here.
    That is a second way over, and the fossil exclusives say so where the plain ones do not.
  - **No breeding table, and that is a finding.** Ruby and Sapphire hatch three babies because
    their dex has three with no other source. Generation 4 brought most of the baby Pokemon
    there are and then put them in Sinnoh's own grass - Cleffa and Chingling in Mt. Coronet,
    Pichu and Mime Jr. in the Trophy Garden, Azurill in the Great Marsh, Budew in Eterna Forest,
    Mantyke on the water, Munchlax on the honey trees. Happiny and Riolu are handed over as
    eggs. A test pins it, because "we forgot" and "there is nothing to forget" look the same.
  - Mismagius is deliberately *not* on the unobtainable list. It is caught nowhere in Diamond
    either, but it evolves from a Misdreavus that comes over the link. Marking it would be the
    mistake that once put Banette on Ruby's list.
  - Manaphy is nobody's exclusive: its egg is a reward in Pokemon Ranger and is sent across.
  - **Step 7 came up empty, which is the opposite of Kanto.** One day in a shop in 2004 covered
    most of the fourteen Kanto exclusives. Not one distribution was ever for Diamond or Pearl:
    Glameow and Stunky have no events at all, and what Misdreavus, Murkrow, Cranidos and
    Shieldon do have is for Gold and Silver, for the Generation 3 games, or for Black and White.
    Dialga and Palkia have been handed out dozens of times, never for the games they come from.
    Manaphy is the exception - nine distributions between 2006 and 2011, on three continents.
  - Sprites are `generation-iv/diamond-pearl`, one sheet for the two of them, all 493 present at
    80x80. Platinum redrew them, so the constant is named for the pair.
  - Smoke test on the published exe against the collection with Diamond as main game and Pearl
    linked: the grid fills with the Sinnoh sprites, Gengar's popup names the cartridge each of
    its five Old Chateau rows needs, Shieldon shows "Pearl only in Generation 4", Pearl's
    revived fossil underneath it and "Then to Diamond: trading", and Manaphy shows its reason
    with no way to get one anywhere.

- [x] **Platinum** (`platinum`, gen 4, standalone) - 2026-09-22
  - [x] 1 Entity + edges - 2026-09-22
  - [x] 2 Dex list - 2026-09-22
  - [x] 3 Wild - 2026-09-22
  - [x] 4 Gifts & statics - 2026-09-22
  - [x] 5 Trades & evolutions - 2026-09-22
  - [x] 6 Sprites - 2026-09-22
  - [x] 7 Events - 2026-09-22
  - [x] 8 Validate + smoke test - 2026-09-22
  - Step 1 was already done twice over before this stretch started: its Pal Park edges were
    widened while FireRed and LeafGreen were being added, and the file was moved onto
    `sinnoh.cartridge` and `sinnoh.edges` during the pair's own step 1. 450 full and 5
    unobtainable, validation green.
  - **A third version is not a third version in every respect.** Emerald shows the same 202
    entries the Hoenn pair does; Platinum widened Sinnoh's list from 151 to 210. The first 151
    keep their numbers exactly - Manaphy is still #151, Rotom is #152, Giratina is last at #210 -
    so `sinnoh.py` names both lists and each game says which is its own.
  - **And it kept all four of the pair's version exclusives out.** Emerald took most of Ruby and
    Sapphire's in, so this was the expectation to check rather than assume: Murkrow, Stunky,
    Misdreavus and Glameow all read "Trade" on Bulbapedia. Two are Diamond's and two are
    Pearl's, so the reason names the half that has them.
  - It shares exactly one table with the pair: the four in-game trades, same NPCs, same houses.
    `PAIR_TRADES` became `TRADES` for that reason. Everything else is its own - the starters
    moved to Route 201, Porygon became a gift from a man in Veilstone, and both cover
    legendaries wait at level 70 after the Hall of Fame for a player carrying the right Orb.
  - **Both fossils are here and a save file still gets one.** The Underground gives the Skull
    Fossil to a Trainer ID ending odd and the Armor Fossil to one ending even. The only
    requirement in this dataset that turns on a number the player never chose.
  - Giratina is deliberately absent from the gift table. It stands in two places on different
    terms - the Distortion World, and Turnback Cave if it was not caught there - and that table
    has one line per species, so any sentence would be wrong about one of the two. The
    conditions on the rows say it properly, and the smoke test confirmed both read correctly.
  - **The only Sinnoh game with anything to hatch,** and not because its grass is poorer: its dex
    is 59 entries longer, and Elekid and Magby are among the 59. Electabuzz is on the Valley
    Windworks and Magmar in Stark Mountain; what hatches from them is nowhere.
  - Its sprites are `generation-iv/platinum`, and not one of the 493 files matches the pair's
    byte for byte. It redrew every one.
  - Step 7 found nothing for the four exclusives - Stunky and Glameow have never been
    distributed in any game, Murkrow and Misdreavus only for Gold and Silver in 2002 and the
    Generation 3 games in 2006 - and **caught a mistake of mine about Manaphy.** Its reason was
    shared between all three Sinnoh games and named nine distributions. Seven of those nine had
    come and gone before Platinum was released, so it was telling a Platinum player to have been
    at a Toys "R" Us in 2007 for a game that did not exist until 2008. The pair keeps the nine;
    Platinum names the two that reached it.
  - Smoke test on the published exe: 0 of 493 with the Sinnoh sprites, the dex switch reading
    "0 of 210" on its own list, Manaphy showing the two distributions that were its own, and
    Giratina's two rows on their own terms.

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

- [x] "Available in this game" counted evolutions it could never reach — 2026-09-22
  - Noticed by Yannick: Platinum offered Ivysaur and Venusaur under "Available in Platinum" and
    no Platinum player can get a Bulbasaur. The filter asked whether the dataset recorded *a*
    method, and an evolution is not a way to get something when the thing it evolves from cannot
    be had. The validator has said exactly that since Phase 0.7 - `no-evolution-dead-ends` - and
    the filter beside the grid had never been told.
  - Not caused by widening the gathering to the living dex, but made much worse by it: before
    that, Platinum recorded no Bulbasaur chain at all, and it was Emerald offering a Medicham
    with no Meditite. Afterwards it was 26 species in Platinum and 82 in FireRed.
  - `Availability` in Core resolves it properly: a method counts when it is a catch, a gift or a
    trade; an evolution counts when what it evolves from can be had here; an egg counts when one
    parent can. Memoised, and guarded against a chain that loops, which only malformed data
    could produce.
  - And the other half of the rule, which is what makes it useful: what the player already owns
    counts. Transfer a Bulbasaur into Platinum and Ivysaur becomes available, and Venusaur
    behind it. Owning the Bulbasaur does not make Bulbasaur available - you cannot get one
    there, you carried it in - and that asymmetry is deliberate.
  - So the answer depends on the collection's records, not only on the dataset. The index is
    rebuilt whenever the records change, and `CaptureIndex.IsIn` answers which game is holding
    something.
  - What it drops, per game: Platinum 26, Diamond 29, Emerald 70, FireRed 82. Ivysaur,
    Charizard, Meganium, Mismagius, Purugly - every line whose base the game cannot produce.
  - Checked in the running app, both ways round, and the collection file restored byte for byte
    afterwards.

- [x] Filter national dex or regional dex — 2026-09-22
  - A switch rather than a filter, which is what made it worth doing: picking the regional dex
    rebuilds the grid from the game's own Pokedex, with the game's own numbering and order.
    Diamond is 493 tiles starting at Bulbasaur #001, or 151 starting at Turtwig #001, and the
    progress figure follows - "0 of 493" or "0 of 151".
  - `DexBuilder.Build` takes which of the two lists to build; null still means whichever the
    game names for itself. The branch that numbers from a game's own dex was already there, for
    games with no National Dex - this gave it a second caller.
  - The main game's dex, not a linked game's. A collection is built around its main game and
    Diamond with Pearl linked would otherwise offer the same 151 twice.
  - Not saved to the data file. It is a way of looking at a collection rather than part of what
    the collection is, the same as the filters beside it, and saving it would mean a user-data
    schema change for a dropdown.
  - Safe because capture records are keyed by target and never by number: Turtwig is 387 in one
    list and 1 in the other, and it is the same tick either way. A test pins that.
  - Only offered when the game really has both lists.
