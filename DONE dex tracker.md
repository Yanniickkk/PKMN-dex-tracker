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
