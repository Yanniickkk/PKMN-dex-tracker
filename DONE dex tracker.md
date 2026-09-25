# Living Dex Tracker — Completed Work

Companion to `TODO dex tracker.md`. Items move here when they are finished, so the
TODO stays a list of what is still open rather than a growing archive.

## How this file works

- **Move, don't copy.** When an item is done, cut it from the TODO and paste it here
  under the matching section. The TODO shrinks, this file grows.
- **Tick the box on the way over.** `- [ ]` becomes `- [x]`.
- **Date every move.** Append ` — YYYY-MM-DD` to the item. That is the day it was
  finished, not the day it was written.
- **Keep the nesting.** A Phase 2 game moves with its sub-steps intact, so the
  record shows what "done" actually covered for that game - including how many steps
  there were at the time.
- **Partial work stays in the TODO.** A game with four steps ticked is not done;
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

### 0.8 The shared forms table

Numbered 0.8 rather than 0.2, which is what it was called while it was open: Phase 0 had already
spent 0.2 through 0.7 by the time this was written, and two sections with one number is worse
than a gap in the sequence.

- [x] Fill `dataset/forms.json`, which had been written empty since Phase 1 - 2026-09-23
  - Noticed by Yannick: turning on functional forms in a collection added no entries. Not a bug
    in the app - `FormSelection`, `DexBuilder` and `ReferenceData` all worked, and functional
    forms are on by default. There was simply nothing in the table for them to expand.
  - `forms.json` holds 154 entries: 97 gender differences, 39 cosmetic and 18 functional. Nothing
    regional, because the earliest of those is Alolan and this dataset stops at Generation 5.
  - Read rather than listed. `forms.py` walks each species' varieties and then each variety's own
    faces, which is the two shapes PokeAPI uses, and works out the kind by measuring: a form
    whose typing, base stats or abilities differ from the species' is functional and one that
    differs in none of them is cosmetic. That is why Unown's letters come out cosmetic and
    Wormadam's cloaks functional without anybody deciding it twice - the letters are one Pokemon
    with 28 faces and the cloaks are three Pokemon. Which games a form is in comes from the
    version group it arrived in, so every Mega, Gigantamax and regional form falls outside this
    dataset by itself.
  - Two kinds are left out on purpose. Battle-only, which the source flags - Castform's weather,
    Darmanitan's Zen Mode, Meloetta's Pirouette - and held-item, which it does not: Arceus's
    seventeen plates and Genesect's four drives. Take the item off and it is the same Pokemon, so
    an entry each would ask a player to catch one Arceus eighteen times. Say so if you want them
    back.
  - Four entries the source gets wrong are written by hand in `ONLY_IN`: Deoxys changes into a
    different form in each of the three Generation 3 cartridges and PokeAPI can only name the
    version group, which pairs FireRed and LeafGreen; and the spiky-eared Pichu cannot leave
    HeartGold or SoulSilver.

### 0.9 What the forms table still could not say

- [x] A picture of its own for each form - 2026-09-23
  - 704 form sprites, and every form of every game has one bar a female Eevee in Generation 4,
    which the sheet never drew. The sheets file them two ways and both are tried: a variety is a
    Pokemon with a number of its own - Wash Rotom is 10009 - and a face of one Pokemon is filed
    under the species' number and the face's name, `585-summer.png`. Gender differences live in
    a `female/` folder beside the rest. `SpritePath` now takes the whole target, so a form falls
    back to its species before the species falls back to the shared set.
  - One thing the fetch had to learn: a sheet is fetched once however many games share it, and
    which games share it still matters. All four Generation 5 games are drawn from one sheet and
    only two of them have a Therian Landorus, so asking the first game alone left six forms
    without a picture.
- [x] How a form is obtained, for the twenty games already written - 2026-09-23
  - 1269 records, of which 187 are a sentence somebody wrote and the rest are a sex. Every form
    of every game has an answer except Unown in Ruby and Sapphire, where there is genuinely none:
    those two have the letters in their dex and no ruins to find one in.
  - A kind of its own, `formChange`, beside the other five. It is last in the popup's order for a
    reason the order already had: the sections run from the surest way to the least, and this is
    the only one that needs the Pokemon already - everything above it answers "how do I get one"
    and this answers "and then what".
  - The sentences live in the region that owns them, as gifts and trades do, and the same form
    gets a different one per region because the games do: Rotom's appliances are behind the
    Secret Key in Sinnoh, up a broken lift shaft in Johto, and in boxes in a shop basement in
    Unova. The Griseous Orb turns up in a different place in every pair since Platinum.
  - A sex needs no table anywhere. It is the one form that is not something done to a Pokemon
    already caught - you look for it while catching - and the answer is the same in every game
    that has the question, so it is written once in `formchanges.py`.
  - What is deliberately not written twice: Generation 5 has Burmy's cloaks and Shellos's seas in
    its dex and no way to make one, because neither species lives in Unova. The Sinnoh record
    carries over the transfer graph and shows as "Then to Black 2: the Poke Transfer", which is
    both true and the answer a player needs.

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

A game lands here only once every step is ticked and its validation run is green.

The twenty games below were written against a checklist of 8 steps. It is 9 now: alternate forms
went in between the events step and the validation one, and the games here did not have it. Their
forms were filled in afterwards in one pass, which Phase 0.8 and 0.9 describe - twenty games had
already been written by the time the shared table existed, and doing it per game would have meant
going back through all of them. From Generation 6 on it is part of writing a game.

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

### A correction that touched sixteen — 2026-09-23

An evolved form whose base a game cannot produce is as unfillable as the base, and sixteen games
said nothing about it. Omega Ruby records "evolve a Lombre" for its Ludicolo - the record is
true, a Lombre does become one - and no Omega Ruby will ever produce a Lotad. Ruby had the same
hole, and Red said nothing about Sandslash, and Gold and Silver nothing about twelve entries
each.

Found while writing Omega Ruby's step 5, by walking each game's own caught records forward
through its own evolutions and eggs and listing what never came up. Nothing in the TODO ever
asked for it: every exclusives table in the dataset was worked out from encounter tables, and
nobody went back through the evolutions afterwards.

`no-evolution-dead-ends` could not catch it. It asks whether the earlier stage is obtainable
*anywhere*, which is the right question for the dataset and the wrong one for a player holding
one cartridge.

- **`reach.py`** answers what one game can reach on its own: what it puts in a player's hands -
  caught, handed over, traded for - and then everything that evolves or hatches from that, as a
  fixed point rather than one pass. A wild slot that does not count is not a start: the Friend
  Safari answers no here for the same reason it answers no to "can I get one in X".
- `spread_unobtainable` gives an entry nothing here can reach the reason its own line already
  carries, and invents nothing where the line says nothing - `every-entry-has-a-method` is
  left to say that about the whole of it. It runs in the build, after a game is built, because
  the answer depends on records that are not finished until then.
- **`unreachable-entries-say-so`** is the eleventh rule, and asks the same question the other
  way round, so that a game which grows a new exclusive and forgets its evolutions is told.

**86 entries in 16 games**, every one of them inheriting a sentence that was already checked:
Blue learns that Gloom and Vileplume are Red's like the Oddish they come from; the three
Generation 2 games say what they had never said about Ivysaur, Venusaur and four more - "nobody
hands one over in Generation 2: Oak's lab is a visit rather than a choice" - and about Omastar
and Kabutops, which no Generation 2 scientist revives. Yellow says it about Beedrill and
Weezing, Diamond about Bastiodon, Emerald about Medicham, Ruby about Ludicolo.

And one the rule could not answer, found in the same pass and written by hand: **SoulSilver
cannot produce a Mantine**. It surfaces on Route 41 in HeartGold and nowhere here, and this
half's only other route to one is a Mantyke - which hatches from a Mantine. A circle nobody had
looked at, and the only entry in the dataset whose whole line was unreachable and unexplained.

The whole dataset rebuilt: 11 rules, 0 warnings, and nothing unreachable and unexplained
anywhere but Omega Ruby and Alpha Sapphire's Jirachi, which is their step 7.

### Generation 1

- [x] **Red** (`red`, gen 1, pair partner: Blue) - 2026-09-22
  - [x] 1 Entity + edges - 2026-09-22
  - [x] 2 Dex list - 2026-09-22
  - [x] 3 Wild - 2026-09-22
  - [x] 4 Gifts & statics - 2026-09-22
  - [x] 5 Trades & evolutions - 2026-09-22
  - [x] 6 Sprites - 2026-09-22
  - [x] 7 Events - 2026-09-22
  - [x] 8 Validate + smoke test - 2026-09-22
- [x] **Blue** (`blue`, gen 1, pair partner: Red) - 2026-09-22
  - [x] 1 Entity + edges - 2026-09-22
  - [x] 2 Dex list - 2026-09-22
  - [x] 3 Wild - 2026-09-22
  - [x] 4 Gifts & statics - 2026-09-22
  - [x] 5 Trades & evolutions - 2026-09-22
  - [x] 6 Sprites - 2026-09-22
  - [x] 7 Events - 2026-09-22
  - [x] 8 Validate + smoke test - 2026-09-22
  - **Virtual Console only, by decision.** Generations 1 and 2 are in this dataset as their 3DS
    releases and not as the cartridges: a Game Boy cartridge trades with another Game Boy
    cartridge and reaches nothing else, so what is caught on one can never join a living dex
    kept anywhere later. These can, through Poke Transporter into Bank. So there is no `red-vc`
    beside a `red` - there is one Red, it is the 3DS one, and the entity's release says so
    rather than its id.
  - 584 and 586 ways to get something, 144 of 151 full and 7 explained in each, validation green
    on all 9 rules.
  - Green is not in the dataset. Its Virtual Console release never left Japan, so listing it would
    claim a game most players cannot buy.
  - `vc.py` holds what every Virtual Console release shares - the release kind, and Poké
    Transporter into Bank. `gb.py` holds Generation 1: a dex of 151 with no National Dex behind
    it, the three releases that trade with each other, and the Time Capsule forward into
    Generation 2.
  - **The Time Capsule is the odd route.** Every other edge in this dataset either carries
    everything a game can hold or goes one way; this one goes both ways and refuses half of what
    the newer side can offer. Declared by the Generation 1 side, because the limit is a fact about
    it - the same reasoning that leaves Pal Park with the Generation 4 game that receives.
  - **The first games here with no National Dex.** `nationalDexThrough` is null and the dex source
    is the game's own list, which `DexBuilder` has always had a branch for and nothing had ever
    used. A living dex in Red is 151 entries.
  - `kanto.py` is now about the place rather than about one generation, the way `johto.py` is.
    Red and Blue are Kanto and so are FireRed and LeafGreen, and the two pairs share a dex - the
    same 151 entries in the same order, which PokéAPI confirms by listing both version groups
    under one name. That is the opposite of Johto, where the remake renumbered 150 entries.
    A test pins that the region module carries no generation number and no National Dex cap.
  - The dex is the 151-entry Kanto one, Bulbasaur #001 to Mew #151 - and `kanto.py` already had
    the function, because FireRed and LeafGreen show the same list in the same order. One dex for
    four games. The difference is what the list *is*: in FireRed it is the game's own Pokedex with
    a National Dex behind it, and in Red it is the whole thing. The app draws 151 tiles and drops
    the dex selector, which only appears for a game with two lists.
  - **Red caught a hole in `every-entry-has-a-method`.** Every one of its 151 entries is caught in
    some later game, so nothing was missing from the dataset and the rule said nothing - about a
    game that brought no encounters at all. Step 8 reads "validation green" as proof a game is
    finished, so a game with a dex and no way to fill any of it is now an error whatever else
    covers its species, and the message says which of the two gaps it is: "0 of its 151 dex
    entries have no source anywhere in the dataset, and the other 151 are only covered by other
    games". Two rule tests had been leaning on the old behaviour without meaning to; both now
    bring a method of their own.
  - 477 wild slots in Red and 479 in Blue, 86 species over 43 places, and **not one condition**.
    No time of day, no seasons, no swarms, no radio, no blocks: the whole apparatus
    `conditions.py` grew for Generation 4 has nothing to say about Generation 1, and the records
    are the barest in the dataset. Every condition PokeAPI does carry for these games is for a
    gift or a trade - what the Game Corner charges, which fossil, what an NPC wants - so they all
    belong to steps 4 and 5.
  - The version split comes out right on its own: Ekans, Oddish, Mankey, Growlithe, Scyther and
    Electabuzz in Red; Sandshrew, Bellsprout, Meowth, Vulpix, Pinsir and Magmar in Blue.
  - **PokeAPI files most of Generation 1's water as `walk`.** There are three surf rows in the
    whole of Red - Tentacool on the three sea routes - and Horsea, Staryu, Shellder, Psyduck,
    Slowpoke, Seel and Dewgong come out of the grass instead. That is the source's shape rather
    than the game's, and it costs nothing here: every water species still has a way in, and a
    player reading "walking" in the Seafoam Islands will not be led anywhere wrong.
  - `kanto.py`'s machinery is now generic over the two pairs, the way `johto.py`'s is: one
    `acquisition_methods` taking how far the National Dex reaches, with
    `gba_pair_acquisition_methods` and `gb_pair_acquisition_methods` filling it in. Red passes
    None, which is the `living_dex` branch for a game with no National Dex - written long ago and
    used for the first time here.
  - 26 gifts and statics over 24 species, and **Kanto's gifts are the part the remake left
    alone.** The same three in Oak's lab, the same scientist on Cinnabar reviving the same fossil,
    the same choice of one Hitmon in the same dojo, the same man in the Celadon Mansion with the
    same Eevee. So the table is the region's - `SHARED_GIFTS` - and each pair adds only what is
    its own: the Hypno that frightened Lostelle is the remake's, and one door opens differently.
    Cerulean Cave waits for the Elite Four in Red and for the Sevii Islands Network Machine in
    FireRed.
  - Red and Blue need no table for the Game Corner. PokeAPI carries what each window charges as a
    condition on the encounter - 180 coins for an Abra in Red and 120 in Blue, 9999 for a Porygon
    against 6500 - which it does not for the remake, so the remake keeps its hand-written prices
    and these two keep none.
  - 72 evolutions and 9 trades, and **no eggs at all** - not because nobody looked, but because
    Generation 1's day care raises a Pokemon and nothing else. Breeding arrives with Generation 2,
    and so do the babies that would need it.
  - **Nobody is named in a Generation 1 trade.** Every other game in the dataset records the
    trader as the original trainer of what they hand over, which is the name the table uses; these
    games store a hardcoded string that reads "TRAINER" in whatever language the cartridge is. So
    the `npc` field is empty for all nine, and that is the game rather than a gap. What they do
    give is a nickname - the Farfetch'd is DUX, the Mr. Mime is MARCEL, the Jynx is LOLA - and
    there is no field for it, so the nicknames are written into the table's comment rather than
    lost.
  - Four of the evolutions need a link cable: Kadabra, Machoke, Graveler and Haunter, which in
    this generation means a second Game Boy and a second player. Their records say "Trade" the
    same way every other generation's do; what has changed is how much that asks of you.
  - Coverage after this step: 144 of 151 full. What is left is the other half's six exclusives and
    Mew, which is step 7's.
  - Step 7 ran before step 6, which the checklist warns against and which cost nothing: its input
    is the list of entries nothing in the game produces, and a sprite sheet does not change that.
  - 151 sprites, one sheet for the pair and the oldest in the dataset - 374 KB for the lot, next
    to 10 MB for the four generations above it.
  - **The set is `generation-i/red-blue/transparent`, and the last word is not a detail.**
    Generation 1's default sheet is a 56x56 palette image with no alpha channel at all, so every
    sprite arrived in a white box, which looked exactly like a white box on a dark grid. The
    transparent set is the same drawings at 96x96 with the background cut out - what every other
    generation's sheet already gives. Noticed by Yannick, on the published exe.
  - The repository keeps a `gray` set as well, which is those same drawings in the Game Boy's own
    four shades. This is the coloured version, for the reason the entity gives: what is in the
    dataset is the 3DS release, and a 3DS shows these games in colour.
  - **This is where modelling the Virtual Console release rather than the cartridge pays.** Mew's
    reason is not the famous one. The Mews of the Nintendo tours, the shopping centres and the
    Toys "R" Us queues went onto Game Boy cartridges between 1996 and 2000, and a 3DS download is
    not one of those. Exactly two distributions were for these releases, both in 2016: the Game
    Freak Mew in Japan in the spring, and the Mew at Nintendo UK's Pokemon Festival that November.
    A cartridge entity would have carried a list of twenty events that never reached the thing a
    player actually owns.
  - Twelve species, twelve *In events* tables, and not one Virtual Console distribution among
    them. What the exclusives have is for Gold and Silver, for the Generation 3 games, or later
    still; Mankey has never been distributed at all. Only Mew ever got a Virtual Console event, so
    the emptiness here is structural rather than a gap somebody should go back and fill.
  - Sandslash is caught nowhere in Red either, and it is not on the list: it evolves from a
    Sandshrew that comes over the link. The same distinction that once put Banette on Ruby's.
  - **The first games in the dataset with nothing in the "a transfer away" column.** 144 full and
    7 explained, and that is all 151: their dex is their whole living dex, so there is no third
    place for an entry to sit.
  - Ten edges are waiting: Yellow, the three Generation 2 releases each of them opens a Time
    Capsule with, and Bank.
  - Smoke test on the published exe: a collection made through the wizard with Red as main game.
    Its linked-games step offers **one** game - Blue, via trading - because nothing else in the
    dataset can send anything into a Generation 1 game, and the graph says so without anyone
    coding a special case. Vulpix reads "Not in Red: Blue only in Generation 1; trade one in"
    and then three of Blue's routes, each with "Then to Red: trading". Mew carries its two 2016
    distributions and no ways at all. Marking Mewtwo caught in Red wrote the record with today's
    date and moved the counter to "1 of 151". The user's own settings were copied out first and
    restored afterwards.
- [x] **Yellow** (`yellow`, gen 1, standalone) - 2026-09-22
  - [x] 1 Entity + edges - 2026-09-22
  - [x] 2 Dex list - 2026-09-22
  - [x] 3 Wild - 2026-09-22
  - [x] 4 Gifts & statics - 2026-09-22
  - [x] 5 Trades & evolutions - 2026-09-22
  - [x] 6 Sprites - 2026-09-22
  - [x] 7 Events - 2026-09-22
  - [x] 8 Validate + smoke test - 2026-09-22
  - 554 ways to get something, 143 of 151 full and 8 explained, validation green on all 9 rules.
  - Yellow is a third version rather than half of a pair, so it names no partner, and its dex is
    the same 151 in the same order. What it does bring is a sprite sheet of its own
    (`generation-i/yellow`), its own version exclusives, and Pikachu following the player around,
    which is nothing this dataset has a field for.
  - Step 2 confirmed that: Yellow rearranged a great deal of what is *in* these games - the
    starter, what the rival takes, what half of Kanto's grass holds - and renumbered nothing. Five
    games now share one `kanto.dex_entries`, and the test that used to say "both pairs" says
    "every Kanto game".
  - The build now ends step 2 with one validation error rather than none, and that is the rule
    Red's step 8 added doing its job: Yellow has 151 entries and nothing at all that fills them,
    which is exactly "this game's encounters have not been gathered yet". It says so in those
    words, names the 151 as covered only by other games, and exits 3. Step 3 clears it. Every
    game from here on will fail its own step 2 this way, which is better than a build that calls
    a half-gathered game finished.
  - Step 3: 448 wild slots across 43 places, filling 85 of the 151. Red has 477 across its own
    grass, so the two are the same size and not the same list. No conditions anywhere - Generation
    1 has no time of day, no seasons and no swarms, so a slot is a place, a method and a rate.
  - Yellow's grass is genuinely a different game, which the diff against Red shows. Gone: the
    whole Weedle line, the Ekans line, the Koffing line, Meowth, Vulpix, Hypno, Electabuzz - and
    Pikachu, which has no wild slot anywhere at all, because the only Pikachu in this game is the
    one that will not stay in its ball. Arrived: Sandshrew, both Oddish *and* Bellsprout on Routes
    12 to 15, both Scyther *and* Pinsir in the Safari Zone, Farfetch'd on Routes 12 and 13,
    Lickitung in Cerulean Cave, and Dragonair on the Safari Zone's Super Rod. Yellow hands over
    what the pair kept from each other and takes back what the anime did not need.
  - So `gb_pair_acquisition_methods` is now a thin wrapper around `gb_acquisition_methods`, which
    is the one that fixes `through=None` for the generation and takes the tables as arguments.
    Red and Blue pass the pair's; Yellow passes none yet and will pass its own. Handing Yellow the
    pair's tables would have printed Red's Kanto and called it Yellow's, and a test now says so:
    a gift row in its encounter table is read as nothing at all until step 4 gathers its gifts.
  - Step 4: 27 gifts and statics, 475 ways to get something in all. Yellow's own table is four
    entries long and they are the four the game exists for. Oak's lab holds one Pikachu instead of
    a choice of three, and the three it replaced are scattered across Kanto in the hands of
    strangers - so a player of Yellow ends up with all four and trades for none of them, where a
    player of Red takes one and needs a second cartridge for the others.
  - Checked on Bulbapedia rather than guessed, because each of the three is asked for differently:
    the Bulbasaur is a girl's in a house in Cerulean City and she wants Pikachu's friendship at
    147 or higher first; the Charmander is a boy's past Nugget Bridge on Route 24, handed to a
    trainer he thinks will look after it better; the Squirtle is Officer Jenny's in Vermilion City
    and takes the Thunder Badge from the gym in the same town.
  - `GB_PAIR_GIFTS` is now `GB_GIFTS`. Mewtwo behind the Elite Four is a Generation 1 fact rather
    than a pair one - Yellow's Cerulean Cave opens on the same door - and the rename is what keeps
    Yellow from inheriting a table whose name says it is not its.
  - Yellow's Game Corner still needs no table, though it charges differently and stocks different
    species: Vulpix for 1000 coins, Wigglytuff for 2680, Abra for 230, Porygon for 9999, and both
    Scyther *and* Pinsir for 6500 where Red and Blue split them one each. The coins arrive as a
    condition on the encounter, so the wording is already written.
  - That corrects step 3's reading of the diff: Vulpix has no wild slot in Yellow but is not
    missing from it - it is in the Game Corner window. Which entries are genuinely out of reach is
    step 7's answer and needs the trades first.
  - Step 5: seven trades and 72 evolutions, 554 ways to get something in all. Not one of Yellow's
    trades is a trade the pair has. Red and Blue offer nine, Yellow offers seven, and the only
    species handed over in both is the Mr. Mime on Route 2 - which wants an Abra there and a
    Clefairy here. Checked against Bulbapedia's in-game trade table rather than assumed from the
    pair's. The nicknames are MILES, RICKY, GURIO, SPIKE, BUFFY, CEZANNE and STICKY; there is no
    field for them, so they are written into the table's comment rather than lost.
  - Yellow is its own version group in PokeAPI where Red and Blue share one, so it asks about
    `yellow` and not `red-blue`. Nothing evolves differently, and asking the pair's group would
    still have been asking about another game.
  - Step 7: eight entries no amount of playing Yellow will fill - Weedle, Ekans, Meowth, Koffing,
    Jynx, Electabuzz, Magmar and Mew. Not a version split: Yellow follows the anime, so what the
    anime had no use for left the game and came back nowhere. Each reason names which of the other
    two to trade from, and it is not always the same one: Ekans and Electabuzz are Red's, Meowth
    and Magmar are Blue's, and Weedle, Koffing and Jynx are in both. Every event is None, for the
    reason Red's table gives - only Mew was ever handed out for a Virtual Console release.
  - The sharpest case in the generation, and it stays *off* the list: Raichu. No grass in Yellow
    holds a Pikachu and the one Oak hands over refuses the Thunder Stone - but Bulbapedia is
    explicit that a traded Pikachu is unaffected, so a Pikachu that comes over the link evolves
    like any other. Reachable, not listed. The same reasoning keeps Kakuna, Beedrill, Arbok,
    Persian and Weezing off it, which is the Sandslash rule from Red.
  - Step 6: 151 sprites of Yellow's own, in `generation-i/yellow/transparent`. Not one of the 151
    is byte-for-byte the pair's: the whole sheet was redrawn for the same hardware, which is why
    this game gets a sprite set instead of pointing at Red and Blue's. The dataset is 4.013 files
    now, 151 more than before.
  - `transparent` again, and the check was the same as at Red's step 6: the default Yellow sheet
    is a 40x40 palette PNG with no alpha chunk at all, so every sprite would have arrived in a
    white box. The transparent set is 96x96 with a `tRNS` chunk. Worth re-checking per sheet
    rather than assuming - the pair's default was 56x56 and Yellow's is 40x40, so the sets are not
    built to one rule.
  - Jynx is the one that needed looking up rather than reasoning about: no grass in Red or Blue
    holds one either. What the pair has is an NPC in Cerulean City who swaps one for a Poliwhirl,
    and Yellow's traders swap other things - so a trade disappearing is what makes an entry
    unreachable, which no encounter table would have shown.
  - Its title carries the subtitle the box does: "Pokémon Yellow Version: Special Pikachu
    Edition". The picker wraps it over two lines and the row still reads, which is worth the
    game's real name.
  - The cartridge followed Red and Blue by two years; the Virtual Console release came out the
    same day as theirs, and it is the 2016 date the entity carries.
  - Step 1 cost almost nothing: the three modules were already there, and the only edit outside
    its own file was making `pair_partner` optional in Kanto's Generation 1 factory. Kanto has a
    third version again, which it had not had since FireRed and LeafGreen made the argument
    required.
  - Generation 1's triangle is closed: three link cables between the three releases. Twelve edges
    are still waiting - each release opens a Time Capsule with each of the three Generation 2
    ones, and each reaches Bank.
  - Smoke test on the published exe: a collection made through the wizard with Yellow as main
    game. Its linked-games step offers exactly two - Blue and Red, both "via trading" - because
    nothing else in the dataset can send anything into a Generation 1 game. Pikachu reads
    "Starter, Pallet Town, from Professor Oak, level 5, the only starter here", and underneath
    it Blue's Viridian Forest and Power Plant with "Then to Yellow: trading", which is the game
    saying it has no wild Pikachu of its own. Raichu carries the same borrowed wild slots and
    then "From Pikachu, Yellow, using a Thunder Stone" with no transfer line at all - reachable
    here, once a Pikachu comes over the link. Jynx reads "Not in Yellow: Red and Blue only in
    Generation 1; trade one in" and then the same NPC in Cerulean City twice, once per game,
    with no wild slot anywhere. Marking it caught elsewhere filled the tile in colour, moved the
    counter to "1 still to transfer" and wrote the record holding in Blue with today's date.
  - The user's own settings were copied out first and restored byte-for-byte afterwards; their
    data file was not opened at any point. Closing the app afterwards stopped every LivingDex
    process, not only the one this test started.

### Generation 2

- [x] **Gold** (`gold`, gen 2, pair partner: Silver) - 2026-09-22
  - [x] 1 Entity + edges - 2026-09-22
  - [x] 2 Dex list - 2026-09-22
  - [x] 3 Wild - 2026-09-22
  - [x] 4 Gifts & statics - 2026-09-22
  - [x] 5 Trades & evolutions - 2026-09-22
  - [x] 6 Sprites - 2026-09-22
  - [x] 7 Events - 2026-09-22
  - [x] 8 Validate + smoke test - 2026-09-22
- [x] **Silver** (`silver`, gen 2, pair partner: Gold) - 2026-09-22
  - [x] 1 Entity + edges - 2026-09-22
  - [x] 2 Dex list - 2026-09-22
  - [x] 3 Wild - 2026-09-22
  - [x] 4 Gifts & statics - 2026-09-22
  - [x] 5 Trades & evolutions - 2026-09-22
  - [x] 6 Sprites - 2026-09-22
  - [x] 7 Events - 2026-09-22
  - [x] 8 Validate + smoke test - 2026-09-22
  - Built as a pair. 1695 and 1683 ways to get something, 234 of 251 full and 17 explained in
    each, validation green on all 9 rules.
  - Step 1 for both, built as a pair. `gbc.py` is new and is Generation 2 the way `gb.py` is
    Generation 1: a dex of 251 with no National Dex behind it, three releases that trade with
    each other, Poke Transporter out to Bank. `johto.py` needed only a `gbc_release` and a
    `gbc_edges` beside its DS pair of factories - the region module was written for this and did
    not have to be rearranged to take it.
  - The Time Capsule is deliberately *not* in `gbc.py`. It goes both ways, so exactly one side
    may declare it, and that side is Generation 1: the limit on it - the first 151 in both
    directions - is a fact about the older games, which have nowhere to put a Chikorita. Same
    reasoning that leaves Pal Park with the Generation 4 game that receives. A test pins it: a
    Generation 2 release's edges are trades and Transporter, and nothing else.
  - Six Time Capsules lit up the moment these two registered - each of Red, Blue and Yellow to
    each of Gold and Silver - plus the link cable between the pair. The dataset is at 15 games
    and 55 routes. Ten are still waiting: Crystal, which both generations reach in their own way,
    and Bank.
  - The dates are the Virtual Console ones again: 22 September 2017, one day worldwide. The
    cartridge was Japan in 1999 and Europe not until April 2001, and neither is what this entity
    is.
  - Kanto is playable in all three of these and the entity still says Johto, exactly as HeartGold
    does. A second half of the map is not a second region.
  - Step 2 did not go where it looked like it would. Johto has a regional order - PokeAPI's
    `original-johto`, 251 entries starting at Chikorita - and these games do list in it: the
    Pokedex opens in New Pokedex Mode with the Johto first partners at the front. But Bulbapedia
    is explicit that the New Pokedex numbers are shown **nowhere** in the games. What is printed
    beside a Pokemon is the old number, so a Gold player reads Chikorita as #152 and Bulbasaur as
    #001.
  - So these are numbered nationally: the national list cut off at Celebi, Bulbasaur #001 through
    Mew #151 straight into Chikorita #152. A dex entry carries one number and it should be the one
    on the screen. The Johto order they happen to list in is not recorded at all - there is no
    field for "listed like this, numbered like that", and inventing one would buy nothing a player
    can see. `johto.ORIGINAL_DEX` stays in the file, named and unused, with the reason written
    next to it.
  - That makes these the only games in the dataset whose dex is built by cutting the national list
    short. Every other game either shows a regional dex of its own - Kanto's 151, Hoenn's 202, the
    updated Johto's 256 - or has a National Dex behind that regional one. These have a National
    Dex and nothing in front of it.
  - HeartGold is the other way round and the contrast is worth keeping: its regional numbers *are*
    what its player sees, so it carries `updated-johto` and its renumbering. Same region, two
    answers, and the entity is what decides.
  - The step 2 build fails validation as every step 2 now does, and this time it names one entry
    with no source anywhere in the dataset rather than none: Celebi. HeartGold and SoulSilver mark
    it unobtainable, so nothing in fifteen games produces one. Gold's own step 7 will say the same
    thing about it.
  - Step 3: 1526 wild slots in Gold and 1514 in Silver, over 81 places each, filling 135 of the
    251. The biggest step 3 in the dataset so far, and the reason is the map: Johto and Kanto are
    both in these games, so 81 places is two regions' worth.
  - These are the oldest games in the dataset that carry a time of day, and not one line had to be
    written for it. 756 of Gold's slots name one - 260 morning, 250 day, 246 night - and the other
    770 are the ones the clock does not touch. The condition vocabulary was filled in for
    HeartGold, which reads the same `time-night` off the same field, and Generation 2 is where the
    clock was introduced in the first place.
  - Nothing else needed wording either, which was the open question going in. Seven slots read
    "Only while it is swarming" and three read "After the beasts are disturbed in the Burned
    Tower" - Raikou, Entei *and* Suicune, all three roaming Johto, which is Gold and Silver's
    arrangement rather than Crystal's. Headbutt trees come through as a method (106 slots) and
    Rock Smash as another (6), both already spelled.
  - Step 4: 24 gifts and statics each, 1550 and 1538 ways to get something. The pair's table is
    one table with two entries picked out per version, and those two are not species.
  - **The version switch in these games is a wing.** Gold's Radio Tower Director hands over the
    Rainbow Wing once Team Rocket is beaten and Silver's hands over the Silver Wing, so Gold meets
    Ho-Oh at level 40 in the middle of its story and Silver meets Lugia there. The other wing
    belongs to an old man in Pewter City - Kanto, so after the Elite Four - and the other bird
    waits at level 70. The levels in PokeAPI's own rows say the same thing, which is how the
    switch was noticed before it was read up.
  - Checked on Bulbapedia, and two of them changed what I would have written: Mania lends the
    Shuckle rather than giving it, asks for it back on another day, and lets it stay at 150
    friendship or if you refuse him; and the Spearow from the gate north of Goldenrod is Kenya,
    handed over holding Mail for a man on Route 31. What happens to Kenya after the delivery is
    left unsaid on purpose - the sources disagree and no dex entry hangs on it, because Spearow is
    in the grass and in the headbutt trees on half of Johto's routes.
  - Eevee is the first gift in the dataset handed over in two places in one game: Bill's house in
    Goldenrod and Celadon's window at 6666 coins. The `where` field was built for exactly this at
    HeartGold's step 4, and one description names Bill while the other says nothing and lets the
    price stand.
  - Both Game Corners needed no rows at all. The coins arrive as conditions, so "Game Corner
    prize, 700 coins" writes itself - and that window is where the pair switch reaches a place no
    grass does: Ekans is Gold's prize and Sandshrew is Silver's, at the same price.
  - **The Bell Tower is the Tin Tower here, and that is fixed rather than noted.** PokeAPI keeps
    one name per location and it is the newest game's, so Ho-Oh's home came through under the
    remake's name - a Gold player being told the name of a game they are not playing.
    `LocationNames` now takes a `renamed` table, applied to the location before anything is
    written down, so a gift table's `where` and a validation message both read what the player
    reads. The sub-area is untouched: "Tin Tower, Roof".
  - The table lives in `gbc.py` and holds one entry, after reading all 83 places these two games
    use. It belongs with the generation and not with the region, which is the point: Johto did not
    rename anything, the games disagree about it, and all three Generation 2 releases say Tin
    Tower. So **Crystal gets this for nothing**, and anything found in its own 83 places goes in
    beside it. A test pins the placement by asserting `johto` has no table of its own.
  - Step 5: seven trades, 122 evolutions and six eggs each; 1695 and 1683 ways to get something.
    Generation 2 is the first in the dataset whose trades record *who* you traded with - a
    Generation 1 trade says TRAINER and nothing else - so the seven carry their trainers' names.
    Crystal adds an eighth (a Xatu for a Haunter, in the same house in Pewter that trades the
    Rapidash) and changes none of these.
  - The remake rearranged them, which is why the two tables are not one: Blackthorn hands over a
    Rhydon here and a Dodrio in HeartGold, for the same Dragonair.
  - Six eggs, and they are the first in the dataset that are not a remake's: Pichu, Cleffa,
    Igglybuff, Smoochum, Elekid and Magby, none of them in any grass. HeartGold's list is twice as
    long and every extra is a later generation reaching back - five incense babies that do not
    exist yet, and a Bonsly for a trade these games do not have. Its Elekid may also hatch from an
    Electivire; here the only parent is the Electabuzz that existed at the time, and a test says
    so.
  - **PokeAPI has nothing at all for the Bug-Catching Contest, and that is not a detail.** Scyther
    and Pinsir are in no grass in either game; Weedle is Silver's in the wild and Gold's only at
    the contest, and Caterpie is the other way round. Without it the dataset says a Gold player
    cannot catch a Scyther, and they can - in the National Park, on a Tuesday.
  - So `wild.py` grew a second source: `RecordedSlot` and `recorded_encounters`, for slots written
    down by hand and cited to whoever was read. Ten slots with their levels and rates, off
    Bulbapedia, carrying a bulbapedia citation instead of a PokeAPI url - which is what makes them
    tellable from every other slot in the dataset. It is meant to stay a last resort: a table like
    that cannot be re-fetched, cannot be checked against the game, and goes stale without saying
    so. Bulbapedia lists the contest identically for Crystal, so Crystal reads the same table.
  - What that leaves uncovered is 17 entries per game, and every one of them looks right for step
    7: the three Kanto first partners (Oak hands over nothing in these games), Omanyte and Kabuto
    (no fossil is revived in Generation 2), the three legendary birds and Mewtwo - all four of
    them Time Capsule cargo from Red, Blue and Yellow rather than anything in Kanto - Mew, Celebi,
    and each half's four version exclusives.
  - Worth recording because I had it wrong until Bulbapedia said otherwise: the legendary birds
    are **not** in Gold and Silver. Kanto is half of these games and the Seafoam Islands, the
    Power Plant and Mt. Silver hold none of them; the birds' own pages say "Time Capsule, Event"
    for all of Generation 2. PokeAPI's silence about them is correct, and it was the contest that
    was missing rather than the statics.
  - Step 6: 502 sprites, 251 per game, and **these are the first pair in the dataset that does
    not share a sheet**. Every pair before them was drawn once - Ruby and Sapphire, FireRed and
    LeafGreen, HeartGold and SoulSilver, Red and Blue - but Gold and Silver drew all 251 twice
    over, so a sheet here belongs to a game rather than to a pair. Crystal brings a third.
  - `transparent` again, and checked again rather than assumed, which was worth doing: the default
    Generation 2 sheet is 40x40 with no alpha chunk, and the transparent one is 56x56 with `tRNS`
    - not the 96x96 that Generation 1's transparent set gives. The sets are not built to one rule
    and every generation needs its own look.
  - Step 7: seventeen entries per game, and **eleven of them are the same eleven in both** -
    which no pair in this dataset has done before. A pair usually differs by six and agrees about
    everything else; these two also agree about what neither can produce, and all but one of the
    eleven is Kanto's. Half of their map is a region whose first partners nobody hands over, whose
    fossils nobody revives, and whose four legendaries are standing nowhere at all.
  - Each of those ten points at the same way in, and it is the route the Generation 1 side
    declared: the Time Capsule. A Bulbasaur in a Gold save came out of a Game Boy.
  - The eleventh is Celebi, and its exception is a game rather than an event. Ten distributions
    between 2000 and 2003, every one onto a cartridge - but **Crystal's Virtual Console release
    turns on the GS Ball event that was Japan's alone**, so one caught in Ilex Forest there can be
    traded across. That is the second time this generation that modelling the 3DS release rather
    than the cartridge changes an answer, and it is why the validator has stopped complaining:
    once these two marked Celebi, no entry in the dataset is left without either a source or a
    reason.
  - The six exclusives per half are all None again, for the reason Red's are: the only Generation
    2 distributions at all were the Celebis and the Mews, and those went onto cartridges.
  - Every earlier step took something off this list, which is why it is worked out last: Ekans is
    the Goldenrod Game Corner's in Gold and Sandshrew is Silver's, Weedle and Caterpie are both in
    the Bug-Catching Contest, and Ariados, Ursaring and Persian evolve from something that comes
    over the link.
  - The version exclusives came out of the encounter tables as expected and mirror each other:
    Gold has the Spinarak line, Growlithe, Mankey, Teddiursa, Gligar, Mantine, Sandshrew and the
    Caterpie line; Silver has the Ledyba line, Vulpix, Meowth, Phanpy, Delibird, Skarmory, Ekans
    and the Weedle line. Which of them are really unfillable is step 7's answer, after the trades.
  - Smoke test on the published exe: a collection made through the wizard with Gold as main
    game. Its linked-games step offers four in two groups and names the mechanism for each -
    Blue, Red and Yellow "via the Time Capsule", Silver "via trading" - which is the transfer
    graph read back out loud. Scyther's tile shows the National Park at levels 13-14, needing
    "the Bug-Catching Contest, held on Tuesdays, Thursdays and Saturdays", cited to bulbapedia,
    and directly underneath it Red's Safari Zone slots cited to pokeapi with "Then to Gold: the
    Time Capsule" - the two sources side by side and tellable apart, which is what the citation
    is for. Ho-Oh's tile shows the whole version switch in one card: Tin Tower Roof at level 40
    in Gold for the Radio Tower Director's Rainbow Wing, and the same roof at level 70 in Silver
    for the old man's in Pewter City. Marking it caught in Gold wrote the record with today's
    date and moved the counter to "1 of 251".
  - The user's own settings were copied out first and restored byte-for-byte afterwards, and
    only the instance this test started was stopped.
- [x] **Crystal** (`crystal`, gen 2, standalone) - 2026-09-22
  - [x] 1 Entity + edges - 2026-09-22
  - [x] 2 Dex list - 2026-09-22
  - [x] 3 Wild - 2026-09-22
  - [x] 4 Gifts & statics - 2026-09-22
  - [x] 5 Trades & evolutions - 2026-09-22
  - [x] 6 Sprites - 2026-09-22
  - [x] 7 Events - 2026-09-22
  - [x] 8 Validate + smoke test - 2026-09-22
  - 1982 ways to get something, 236 of 251 full and 15 explained - the most fillable of the
    three, and the only game in the dataset that produces a Celebi. Validation green on all 9
    rules.
  - Crystal inherits four things from its pair without doing any work: the Tin Tower's name, the
    Bug-Catching Contest table, the renamed-places machinery and `gbc.py` itself. What is its own
    is a third sprite sheet, one more in-game trade (a Xatu for a Haunter, in the same house in
    Pewter that trades the Rapidash), a Suicune that does not roam, and the GS Ball.
  - **The GS Ball is the reason Crystal matters to this dataset.** Its Virtual Console release
    turns on the event that was Japan's alone, so Celebi is catchable in Ilex Forest - the only
    game in three generations that can produce one. Gold and Silver already point at it.
  - Step 1 cost one file and one line, which is what the two module splits were for: `crystal.py`
    names itself, its date and its box art, and everything else comes from `johto.gbc_release` and
    `johto.gbc_edges`. Nothing outside its own file changed except the registry - not even a
    `pair_partner` argument, which Johto's Generation 2 factory had already been given as optional
    when Gold and Silver went in.
  - **Generation 2's triangle is closed and every Time Capsule is lit.** Sixteen games, 60 routes:
    three link cables between the Generation 1 releases, three between the Generation 2 ones, and
    nine Time Capsules - each of Red, Blue and Yellow to each of Gold, Silver and Crystal. The
    last two generations of Game Boy are now one connected piece.
  - **Six edges are waiting, and for the first time they are all the same thing:** Poke
    Transporter into Bank, one from each Virtual Console release. Every held-back route in the
    dataset now waits on a node that is not a game, which is the next piece of work rather than
    the next game.
  - The date is 26 January 2018, worldwide on one day - five months after Gold and Silver's
    Virtual Console release, where the cartridge had followed theirs by a year.
  - Step 2 was a repeat rather than a decision, which is what a shared module is for: the same 251
    through `johto.gbc_dex_entries`, the national list cut off at Celebi, Chikorita at #152. The
    test that pinned the numbering for the pair now runs over all three.
  - The one thing that is not a repeat is the last entry. Celebi is #251 in all three games and in
    this one it is an entry a player can fill, which is step 4's business.
  - Step 3: 1819 wild slots over the same 81 places, filling 148 of the 251 - three hundred more
    slots than Gold, and thirteen more species. The contest's ten and the Tin Tower's name arrived
    without a line being written for them, which is what the two module splits were for.
  - Crystal's grass is its own. It adds Granbull, Parasect, Pupitar, Rhydon and Weezing, which the
    pair can only evolve or trade for, and it drops Mareep and Flaaffy, Girafarig, Mankey and
    Primeape, Remoraid and Vulpix - PokeAPI has no Crystal encounter for any of them. Whether that
    makes them unfillable is step 7's answer, after the trades.
  - Step 4: 26 gifts and statics, and **Celebi is one of them**. Three generations of games have
    had it in their dex and none could fill it; this one can, and only because the dataset models
    the 3DS release. PokeAPI marks the Ilex Forest encounter `other-virtual-console`, which is the
    rarest thing a source can do - say out loud that a re-release changed what is catchable - and
    that condition now has a wording of its own.
  - `GBC_PAIR_GIFTS` became `GBC_GIFTS`, because reading Crystal showed the table was never the
    pair's: it keeps every row - Elm's three, the Egg in Violet City, Bill, Mania, the trap floor
    under Mahogany Town - and brings four of its own.
  - Those four are the game: a Dratini from the Master of the Dragon Shrine for passing his
    five-question quiz (perfect first time and it knows ExtremeSpeed, which nothing else in
    Generation 2 or 4 can teach it); Suicune waiting on the Tin Tower's first floor behind the
    Clear Bell; Ho-Oh behind a Rainbow Wing a Sage only hands over once the Hall of Fame is
    entered *and* all three beasts are caught with your own trainer ID - the hardest condition in
    the dataset; and Lugia, which simply is not there unless the Silver Wing is in the Bag.
  - Where Crystal's Silver Wing comes from is deliberately left unsaid: two Bulbapedia pages
    disagree about whether it is the Radio Tower Director or the old man in Pewter City, and the
    sentence reads fine without it.
  - **PokeAPI files the day care's seven babies as gifts here and as nothing at all in Gold and
    Silver.** Route 34 is the day care, so what it is describing is breeding - in the one
    generation that invented it. They are excluded and left to the egg table, which names the
    parents a player has to leave there, and all three games now say the same thing about a Pichu.
    That is the second disagreement with PokeAPI worth recording, after the Sinnoh fossils.
  - Step 5: eight trades, 122 evolutions and six eggs; 1982 ways to get something. The eighth
    trade is the only one in Generation 2 that is not in all three releases - a Xatu for a
    Haunter, from a trainer the game records as PAUL, in the same house in Pewter City that trades
    the Rapidash. `GBC_PAIR_TRADES` and `GBC_PAIR_EGGS` lost their "pair" the way the gift table
    did: all three releases share them.
  - **PokeAPI is missing the Karate King's Tyrogue for this game.** It has the row for Gold and
    Silver and not for Crystal, and without it the game has no Tyrogue *and* no Hitmon: all three
    of those evolve from it and nothing here hatches one, so the gap closes a circle rather than
    leaving a hole. Bulbapedia is clear that he hands over a level 10 Tyrogue in all three.
  - So `gifts.py` got the same second source `wild.py` did: `RecordedGift` and `recorded_gifts`,
    for gifts written down by hand and cited. Two hand-written sources in one generation is more
    than any other has needed, and both are for things the games themselves are known for.
  - Step 6: 251 sprites of its own, and **Generation 2 drew all 251 three times over**. Not one
    of the 753 is byte-for-byte identical across all three sheets: Gold and Silver agree about
    five drawings, Gold and Crystal about eight, and no species is the same in all three. The
    dataset is at 4772 files.
  - Checking again rather than assuming paid off once more: Crystal's default sheet is 56x56 where
    Gold's and Silver's are 40x40, and it still carries no alpha chunk. Only the transparent sets
    have `tRNS` - in all three, at 56x56.
  - Step 7: fifteen entries, where each half of the pair has seventeen - and **the two it does
    not share are the whole point of this game.** Ten are the generation's: three Kanto first
    partners nobody hands over, two fossils nobody revives, four legendaries standing nowhere, and
    Mew. Celebi is the eleventh for the pair and is simply not on this list.
  - The other five are Crystal's own, and they are not a version switch: nothing here is held back
    for Gold or Silver to have instead. **A third version that drops five things**, where Yellow,
    Emerald and Platinum all add. Vulpix is Silver's, Mankey is Gold's, and Mareep, Girafarig and
    Remoraid are in both halves and in no grass here.
  - Read off each species' own game-locations table rather than from PokeAPI's silence, which is
    the lesson the legendary birds taught at Gold's step 7: every one of the five says "Trade" in
    its Crystal row. Remoraid is the only one Generation 2 ever distributed at all - twice, at
    Gotta Catch 'Em All Station! in the United States in 2002 - and both went onto cartridges,
    which a 3DS download is not.
  - `GBC_PAIR_UNOBTAINABLE` split into `GBC_UNOBTAINABLE` (the ten every release lacks) and the
    pair's eleven, which is the one place in the generation where the third version is not a
    superset of a half but the only way in.
  - **Suicune leaves the wild list entirely, and that is the version's own story.** Gold and
    Silver set all three beasts roaming Johto; here only Raikou and Entei do, and Suicune waits on
    the first floor of the Tin Tower at the end of a chase the game scripts. PokeAPI files it as a
    static, so it arrives with step 4 rather than here - the roamer count in the data, two against
    three, says the same thing without anyone writing it down.
  - Smoke test on the published exe: a collection made through the wizard with Crystal as main
    game. Its linked-games step offers five in two groups with the mechanism on each - Blue, Red
    and Yellow "via the Time Capsule", Gold and Silver "via trading". Celebi's tile reads "Ilex
    Forest, level 30, GS Ball taken to the shrine; on the Virtual Console release it is handed
    over at the Goldenrod Pokemon Center once the Hall of Fame is entered; the cartridge only
    ever gave it out in Japan". Suicune's shows both versions of its own story at once: Tin
    Tower 1F behind the Clear Bell here, and "Roaming Johto - after the beasts are disturbed in
    the Burned Tower" in Gold. Tyrogue's shows the point of the hand-written records - two gift
    cards with the same Karate King, the same floor and the same level, one cited to bulbapedia
    because it is this game's and PokeAPI has no row for it, the other cited to pokeapi because
    it is Gold's. Marking Celebi caught in Crystal wrote the record and moved the counter to
    "1 of 251".
  - The user's own settings were copied out first and restored byte-for-byte afterwards, and
    only the instance this test started was stopped.

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

- [x] **HeartGold** (`heartgold`, gen 4, pair partner: SoulSilver) - 2026-09-22
  - [x] 1 Entity + edges - 2026-09-22
  - [x] 2 Dex list - 2026-09-22
  - [x] 3 Wild - 2026-09-22
  - [x] 4 Gifts & statics - 2026-09-22
  - [x] 5 Trades & evolutions - 2026-09-22
  - [x] 6 Sprites - 2026-09-22
  - [x] 7 Events - 2026-09-22
  - [x] 8 Validate + smoke test - 2026-09-22
- [x] **SoulSilver** (`soulsilver`, gen 4, pair partner: HeartGold) - 2026-09-22
  - [x] 1 Entity + edges - 2026-09-22
  - [x] 2 Dex list - 2026-09-22
  - [x] 3 Wild - 2026-09-22
  - [x] 4 Gifts & statics - 2026-09-22
  - [x] 5 Trades & evolutions - 2026-09-22
  - [x] 6 Sprites - 2026-09-22
  - [x] 7 Events - 2026-09-22
  - [x] 8 Validate + smoke test - 2026-09-22
  - Built as a pair, the way both Generation 3 pairs and the Sinnoh pair were. 3025 and 3046
    ways to get something, 446 and 447 of 493 full, validation green on all 9 rules.
  - **Johto is the first region in this dataset that two generations are set in**, so `johto.py`
    is about the *place* rather than about the hardware - unlike `kanto.py`, whose first line
    says "the Generation 3 Kanto cartridges". Gold, Silver and Crystal read from it too when
    they arrive, and nothing in it should have to be edited for them.
  - What is true of Johto goes there; what is true of the generation stays with the generation,
    in `ds.py` now and in Generation 2's own module later. The two factories are named for the
    hardware for that reason - `ds_cartridge`, `ds_edges` - leaving room for the pair beside
    them, and a test pins that the region module carries no generation number and no National
    Dex cap. That is the mistake worth catching: a fact about the DS pair written down as a
    fact about the place.
  - A table that belongs to one pair rather than to the region says so in its name, the way
    Sinnoh's `PAIR_DEX` does. The two dexes will need it: Gold and Silver show the 251-entry
    Johto dex and HeartGold and SoulSilver the 256-entry one.
  - The six edges Diamond, Pearl and Platinum had been holding for the Johto half lit up on
    their own, without either side being edited. 45 routes now: ten link cables, ten wireless
    trades and twenty-five Pal Park trips.
  - Building one half alone is a red build, and rightly: `version-pairs-name-each-other` says
    HeartGold names a partner that is not in the dataset. It goes green when the other half
    arrives, which is what that rule is for.
  - The dex is the 256-entry Johto dex, `updated-johto`, Chikorita #001 to Celebi #256. Both
    halves show the same list in the same order, the way Diamond and Pearl share their 151.
  - The region names both its dexes rather than one. Gold, Silver and Crystal show
    `original-johto`, 251 entries, and the five the updated one adds are the Generation 4
    evolutions of Pokemon already in it - Yanmega, Ambipom, Lickilicky, Tangrowth, Mamoswine -
    each filed directly behind what it evolves from. So it is not the original with five at the
    back: everything from Yanmega on is renumbered, 150 entries of it. That is the opposite of
    Sinnoh, where Platinum's 210 keep Diamond's 151 numbers exactly, and it is why one constant
    called "the Johto dex" would have been a lie waiting to be believed.
  - Which entries the cartridge cannot produce is step 5's answer, not this one's. Reading the
    encounter tables alone cannot tell a version exclusive from something that evolves from one,
    which is what once put Banette on Ruby's list.
  - Both are red until step 3, and the message is the one the aggregate rule was written for:
    "this game's encounters have not been gathered yet". The single entry it counts as missing
    from the whole dataset is Celebi, which nothing anywhere produces - the other 255 are
    already obtainable in some other game here.
  - 2704 wild slots in HeartGold and 2725 in SoulSilver, 248 species over 92 places, both
    regions included - Kanto is half of these games and none of it is in their 256 entries,
    which is exactly why the build asks about the living dex instead.
  - Johto hangs more on its conditions than any region before it, and all of them are in
    `conditions.py`, which is shared, so Gold and Silver will find most of the sentences already
    written:
    - The Pokegear radio does what the Game Boy Advance slot does in Sinnoh - it puts another
      region's Pokemon in the grass - except it asks for nothing a player does not already own.
      211 slots on the Hoenn sound, 189 on the Sinnoh sound.
    - The Safari Zone's numbers are block **points**, not objects. An area holds thirty at a
      time and each one counts for more once the area has been active long enough, so "at least
      35 forest" is reachable; a player counting to thirty would have concluded it was not.
      185 slots hang on it.
    - Headbutt trees come in three groups and which tree is in which is fixed per save, so it is
      not "find the right tree" but "find out which of yours it is". 350 slots.
    - The Bug-Catching Contest replaces the National Park for a day, and the National Dex
      changes what is in it - one Butterfree slot reads "Only during the Bug-Catching Contest
      and after the National Dex opens and on a Tuesday", which is three conditions the game
      really does stack.
  - The two roamers were worth checking rather than guessing at: the beasts start moving when
    they are disturbed in the Burned Tower, and Latias or Latios when the player leaves the
    Vermilion City Pokemon Fan Club with the Copycat's doll. Both read off Bulbapedia's roaming
    page.
  - A test in `test_wild.py` used one of the Safari Zone conditions as its example of a
    condition nobody has worded yet. Somebody worded it, so the test now uses Generation 7's
    SOS chaining instead - which is the path working exactly as intended.
  - Coverage after this step: 248 of 493 full, 241 a transfer away, 4 produced nowhere at all -
    Celebi, Jirachi, Manaphy and Phione. Steps 4 and 5 are what turn the 241 into something
    smaller: these games hand over a great deal and evolve even more.
  - 53 gifts and statics over 50 species, one table for both halves. What they disagree about -
    which of two the Game Corner sells, which legendary sleeps in the Embedded Tower, what level
    a cover legendary is caught at - PokeAPI already files per version, so none of it needs a
    switch in the table.
  - **One species, two different gifts** is new here and needed a change to `gifts.py`. Bill
    hands over an Eevee in Goldenrod and the Celadon Game Corner sells one for 6,666 coins; the
    Master of the Dragon Shrine gives a Dratini for his quiz and Goldenrod sells one for 2,100.
    A table keyed by species alone would have printed "From: Bill" on a slot machine prize. A
    `GiftDetail` can now say `where` it applies, a species can carry several, and a set of
    descriptions that between them fit nowhere is logged rather than passing silently.
  - Three sets of first partners in one game, which nothing else in the dataset does: Elm's
    three in New Bark Town, Oak's three in Pallet Town after Red is beaten, and Steven's three
    Hoenn starters in Silph Co. once a Kanto one has been taken.
  - Four things were worth reading rather than guessing at, and all four came off Bulbapedia:
    - The Embedded Tower legendaries wait behind an **in-game** item, not an event. Mr. Pokemon
      hands over the Blue Orb (HeartGold) or Red Orb (SoulSilver) once Red is beaten and a Kanto
      first partner has been taken, and Professor Oak gives the Jade Orb for being shown a
      Kyogre and a Groudon **both caught in that tower** - so a Rayquaza needs the other version
      to have been played too.
    - Primo's three eggs take a password, which is a set of phrases picked in conversation. The
      codes were printed in magazines and are freely known; nothing about it needs an event.
    - The Togepi egg comes from Professor Elm's assistant after the Zephyr Badge.
    - The Dragon Shrine's Dratini is the reward for the Master's quiz, and a first-time perfect
      set of answers is what makes it know ExtremeSpeed. PokeAPI files that as two rows; one
      sentence collapses them into the one gift it is.
  - Manaphy is skipped with a word, the way Sinnoh's is: its egg is a Pokemon Ranger reward sent
    across, which is a fact about two games and a wireless link. It cannot be marked unobtainable
    here, though, because it is not in these games' own 256-entry dex and a reason lives on a dex
    entry. Same for Jirachi and Phione. Worth fixing where the coverage report counts, not here.
  - 22 species are handed over that the table says nothing about, and the build names them: the
    Rocket HQ's trap Voltorb, the Game Corner's cheaper prizes, the birds, the beasts. Each one
    still carries its place, its level and whatever its conditions said; what they lack is a
    sentence somebody has checked. That number is the size of the job, not a fault.
  - Coverage after this step: 282 of 493 full, 207 a transfer away, 4 produced nowhere. Step 5
    is the big one for these games - Johto is where breeding was invented.
  - Step 5 in three parts: 246 evolutions, 10 in-game trades, 12 babies from the day care on
    Route 34 - which is the same building Gold and Silver put there, so it is the region's and
    not the pair's.
  - **A trader who names no price.** Jasmine hands over a Steelix for whatever is in the party,
    and every other trader in the dataset asks for a species. Rather than invent a price she
    never asked for, `wants` became optional - in the pipeline's schema, in the app's model and
    in the sentence the popup prints, which now reads "Trade anything for it". Four of the ten
    traders are characters a player already knows: HeartGold gave its new trades to Brock,
    Jasmine, Lt. Surge and Steven rather than to invented strangers.
  - Two trades are only open at certain hours, which no other game in the dataset has done:
    Brock's Rhyhorn on Saturday evenings after he is beaten at the Pewter Gym, and Jasmine's
    Steelix between one and two in the afternoon after a rematch, on the second time she is
    spoken to. Both came off Bulbapedia's in-game trade table, along with the trainer names the
    games record as the original trainer.
  - **The incense is only for the babies Generation 4 invented.** A Pikachu has always simply
    laid a Pichu; a Marill lays another Marill unless a parent is holding a Sea Incense. The
    six older babies - Pichu, Cleffa, Igglybuff, Smoochum, Elekid, Magby - hatch from nothing
    but two parents, and the six newer ones each need their own item. Getting that backwards
    would send a player shopping for something they do not need.
  - Johto invented breeding and still needs a short table: Azurill, Budew and Chingling are in
    its own grass, so an egg is not the only way to one and they are not listed. Bonsly is,
    and it has to be - Brock will not hand over his Rhyhorn without one, and nothing else in
    these games produces a Bonsly.
  - Coverage after this step: 446 of 493 full in HeartGold and 447 in SoulSilver, 43 and 42 a
    transfer away, 4 produced nowhere. What is left to explain is Celebi, which is step 7's.
  - The pair redrew Generation 4's sprites rather than reusing Diamond and Pearl's or
    Platinum's, so they get a sheet of their own: 493 of them, the whole National Dex these
    games reach, and not one missing. Three sheets in Generation 4 now, one per release.
  - Step 7's input is the list of entries nothing in the game produces, and for these two it is
    eight and seven: the other half's exclusives, plus Mew and Celebi. **Validation is green** -
    9 rules, 0 errors, 0 warnings across all ten games.
  - The pair is not symmetrical. Six species are SoulSilver's and five are HeartGold's, which
    is worth saying out loud because every other pair in this dataset mirrors exactly.
  - What is *not* on those lists matters as much. Ledian is caught nowhere in HeartGold either,
    and it evolves from a Ledyba that comes over the link - the distinction that once put
    Banette on Ruby's list. Reading only the encounter tables cannot make it.
  - Eleven *In events* tables read, and one hit: not a Pokemon that was handed out, but a place
    to walk. The Sightseeing route for the Pokewalker holds a Meowth, and that route was itself
    an event download. Every other distribution those eleven have is for Generation 1 to 3 or
    for Black and White. An empty finding is still a finding.
  - Mew came over Wi-Fi rather than over a counter, which is what the generation changed: the
    Susumu Mew in Japan in 2009 and 2010, and the Fall 2010 Mew in five languages.
  - Celebi is more than a dex entry here. The Cinema Celebi of 2010 and the Winter 2011 Celebi
    are what put the GS Ball in the player's hands and Giovanni in Ilex Forest, so the
    distribution carried a piece of the game with it - and saying only "event only" would have
    left out half of what it does.
  - The Pokewalker was worth checking for another reason: PokeAPI has nothing about it, so a
    course holding something the cartridge does not could have made a whole list wrong. Only
    one of the eleven is on any route at all, and that route is an event.
  - Adding a game's edges needs a **full** build. A single-game build reads the shared tables
    rather than rewriting them - that is what makes adding a game cost nothing for the others -
    and the transfer graph is one of them. Roughly seven minutes from a warm cache.
  - Smoke test on the published exe: a collection made through the wizard with HeartGold as
    main game and Emerald and SoulSilver linked. Vulpix reads "Not in HeartGold: SoulSilver
    only in Generation 4; trade one in", then Emerald's Mt. Pyre by Pal Park and SoulSilver's
    Route 36 by trading - both routes in one popup, which no other game in the dataset has
    shown. Celebi carries its distributions and no ways at all. Marking Vulpix caught elsewhere
    wrote the record with today's date, and the counter moved to "1 still to transfer". The
    user's own settings were copied out first and restored afterwards; nothing touched their
    data file.

### Generation 5

- [x] **Black** (`black`, gen 5, pair partner: White) - 2026-09-23
  - [x] 1 Entity + edges - 2026-09-22
  - [x] 2 Dex list - 2026-09-22
  - [x] 3 Wild - 2026-09-22
  - [x] 4 Gifts & statics - 2026-09-22
  - [x] 5 Trades & evolutions - 2026-09-23
  - [x] 6 Sprites - 2026-09-23
  - [x] 7 Events - 2026-09-23
  - [x] 8 Validate + smoke test - 2026-09-23
  - 1168 ways to get something: 809 wild slots, 320 evolutions, 30 gifts and statics, 5 trades
    and 4 eggs. 455 of the 649 its living dex asks for are fully covered, 178 partly, 13
    explained. Validation green on all 9 rules, for the whole dataset.
- [x] **White** (`white`, gen 5, pair partner: Black) - 2026-09-23
  - [x] 1 Entity + edges - 2026-09-22
  - [x] 2 Dex list - 2026-09-22
  - [x] 3 Wild - 2026-09-22
  - [x] 4 Gifts & statics - 2026-09-22
  - [x] 5 Trades & evolutions - 2026-09-23
  - [x] 6 Sprites - 2026-09-23
  - [x] 7 Events - 2026-09-23
  - [x] 8 Validate + smoke test - 2026-09-23
  - The same counts as Black, entry for entry, which is what a version pair is.

  _What all four games share is in `unova.py`, which is also the region module: Generation 5 never
  left Unova, so the hardware-and-region split `ds.py` explains has nothing on either side of it.
  Black 2 and White 2 are not a third version but a second pair - own story, own half of the map,
  own Pokedex - so `unova.py` keeps the two pairs apart wherever they disagree._

  _Step 4 for both: 30 gifts and statics each. The fossils are the interesting half - nine of them,
  revived by the museum's machine in Nacrene City, and PokeAPI's condition is the bare item name.
  Where the item comes from is the part that is hard: seven are from earlier generations and a
  Worker in Twist Mountain hands out one a day, and only once Ghetsis is beaten; the two this
  generation brought are a choice a person in the Relic Castle offers, so one save fills one of
  them and the other waits for a trade. That looks exactly like a version exclusive and is not one._

  _The woman outside the Dreamyard hands over the monkey the player's own first partner beats -
  Pansage for a Tepig - and PokeAPI files all three with no condition at all, so without the table
  the dataset would have promised every player all three. All three are in the rustling grass as
  well, so the gift decides which one is free rather than which one is possible._

  _**Three entries turned out not to be answers**, and all three are really in the game: Victini
  behind the Liberty Pass, which went out over Nintendo Wi-Fi in 2011 and closed with the service in
  2014; Zorua behind the event Celebi; Zoroark behind one of the shiny event beasts, both of them
  Generation 4 giveaways carried across with the Relocator. They bring no record now and step 7
  writes their sentence._

  _Two more faults in the source, and one new piece of machinery for the second:_

  _- PokeAPI files the roaming Tornadus and Thundurus under **Team Flare Secret HQ**, which is in
  Kalos, two generations away. Corrected with the same rename table the Bell Tower needed._
  _- It has the Friday Musharna twice, once in the Dreamyard with the conditions and once in the
  basement without them, and Bulbapedia has one Musharna, in the basement. `excluded` can now name
  a place rather than a species, so one row is dropped and the species keeps its real one._

  _And two conditions nobody had words for: `defeated-ghetsis` ("After Ghetsis is beaten", which is
  this generation's Hall of Fame) and `special-encounter-couldnt-capture-before` ("Only if it got
  away the first time" - the cover legendary waiting at Dragonspiral Tower, and Landorus coming
  back to the Abundant Shrine)._

  _Step 5 for both: five traders, 320 evolutions and four eggs._

  _The five traders are small for a Unova game and every one of them is worth something. Two are
  the only way here to a Rotom and a Munchlax, neither of which is in this generation's dex at all,
  and the Munchlax is **only in summer** - the first door in this dataset that the calendar closes.
  The fifth is the pair's own switch written as a trade: Dye swaps Petilil for a Cottonee in Black
  and Cottonee for a Petilil in White, so **two of the six species that look like version
  exclusives are not**, and step 7 has to know that before it writes anyone off._

  _Four eggs, of fifteen babies that could have needed one. Unova's grass is full of grown-up
  Pokemon from earlier generations and empty of their babies - Clefable in the Giant Chasm's
  rustling grass, Wigglytuff on Route 14 - which is the exact opposite of Sinnoh, where the babies
  were in the grass and the day care was not needed at all. Cleffa, Igglybuff and Smoochum need
  nothing; Chingling needs a Chimecho holding a **Pure Incense**, which the Driftveil Market only
  sells once the National Pokedex is open. The other eleven are left out because nothing here
  produces a parent - there is no Pikachu in these games at all, so "hatch a Pichu" would be the
  lie the no-breeding-dead-ends rule watches for._

  _Validation is down to six errors each: Victini, Zorua, Keldeo, Meloetta, Genesect, and Zoroark
  for evolving from a Zorua nothing explains yet. All six are step 7's._

  _Step 7 for both: thirteen entries each, and **validation is green** - nine rules, no errors, no
  warnings, for the whole dataset._

  _Seven of the thirteen are the other half's, mirrored exactly, and the events there are the
  surprise. Generation 4's four exclusives had no distribution at all; here both of the legendaries
  each half is missing were handed out, and **every one of those giveaways was aimed at the half
  that could not catch it** - the Milos Island Thundurus for Black, which has the Tornadus, and
  Ash's Zekrom for Black, whose box has Reshiram on it. The ordinary five - the Solosis and Gothita
  lines, Rufflet and Vullaby - were never handed out anywhere._

  _Cottonee and Petilil are not on either list, which is step 5 paying off: they look exactly like
  two more exclusives, and Dye swaps each half the one its own grass is missing._

  _The other six are neither half's, and none of them is missing because the cartridge never held
  it - each is really in the game, behind a giveaway that has ended. That is the opposite of Mew in
  Kanto or Manaphy in Sinnoh. Two of the six needed the games column read carefully: **Zorua** is the
  only entry anywhere in the six that no distribution ever covered - what was handed out was the key
  rather than the Pokemon, an event Celebi for the Generation 4 games - and **Genesect** was handed
  out plenty, but in the West every one of those was for the sequels, so a player of Black in Europe
  or America was never offered one._

  _`handed_out` moved from `kanto.py` to `exclusives.py` on the way: step 7 asks the same question
  of every game, and the answer is the same shape in all of them._

  _Step 6 for both: `generation-v/black-white`, 649 sprites, not one of them missing. One sheet for
  the whole generation, which is new - every generation before this redrew itself either for its
  third version or for its remakes, and the Unova sequels reuse these exactly. No `transparent` on
  the end: unlike the Generation 1 and 2 sheets these are already cut out. The animated sheet beside
  it is what these games are actually famous for, and it stays unused - they are GIFs, the grid
  draws a still picture, and a folder of animations nobody plays is megabytes in the exe for
  nothing. 1.9 MB added._

  _Double-checked afterwards, and the four statics that were left without a sentence now have one.
  PokeAPI carries no condition on any of those rows, and two other sources - Pokemon Database and
  the species' own Bulbapedia pages - say only the place, the same place PokeAPI says. Three sources
  agreeing about where something stands is not three sources saying how to reach it. The answers are
  on the *Swords of Justice* page and on the two locations' own pages: Cobalion is in Mistralton
  Cave's Guidance Chamber behind Surf, and **Terrakion and Virizion do not exist until Cobalion has
  been met**; Volcarona waits on the Relic Castle's lowest floor once Ghetsis is beaten; and Kyurem
  is not postgame at all, which was the easy thing to assume - it is in the cave depths on the first
  visit, and what waits for the Hall of Fame is the second chance if it faints or is run from._

  _Validation is down to 39 errors each from 55. Thirty-three of them are evolutions and belong to
  step 5; the other six are the three above and the three mythicals, and they belong to step 7._

  _Step 3 for both: every wild slot in Unova, read per version. What it cost was five new
  encounter methods, because Unova hides a second table inside the first almost everywhere and the
  schema had nowhere to put it: `darkGrass`, `rustlingGrass`, `dustCloud`, `ripplingWater` and
  `bridgeShadow`, in `models.py`, the C# enum, the section labels and the icon set. 62 of the 214
  species a player of Black can catch are only in one of those, and 13 more only in the dark grass,
  which the dataset would otherwise have called plain walking. Fishing in a ripple is the one
  compound case: it stays a Super Rod slot and says "Cast into rippling water", because the rod is
  the half a player can be missing._

  _Unova is also the first region whose slots carry a **season** - 127 of Black's do. The field has
  been in the schema since Phase 0 and empty in all sixteen games before these two._

  _Two things in the shared machinery changed while this was written, and both touched games that
  were already finished:_

  _- A room PokeAPI has no name for is no longer printed as one. Unova's Victory Road is filed as a
  dozen `unknown-area-53`, and "Victory Road, Unknown Area 62" is the source admitting it does not
  know, written out as if it were a place. Whatever else the slug holds is kept, so `1f-unknown-room`
  is still 1F._
  _- Records a player cannot tell apart are now folded into one: same species, place, method and
  state of the world, differing only in levels and odds. That is what dropping the rooms needed -
  Boldore stood in three of them - and it also caught 21 groups each in Gold, Silver and Crystal,
  where a headbutt tree was listed twice at the same level with two different odds. The level range
  widens to cover both and the odds are the best of them rather than their sum: a player is in one
  room at a time._

  _Left for step 4, found while reading the tables: PokeAPI files the roaming Tornadus and Thundurus
  under **Team Flare Secret HQ**, which is a Kalos place and plainly wrong; `defeated-ghetsis` and
  `special-encounter-couldnt-capture-before` have no wording yet; and the fossils arrive as `item-`
  conditions on gift rows._

  _Step 2 for both: 156 entries each, `original-unova`, Victini #000 to Genesect #155. It is the
  first dex in this dataset that starts at zero, and the only one anywhere that holds nothing but
  its own generation - all 156 of the species Generation 5 added, 494 to 649, and no older Pokemon
  at all. So the gap between a game's dex and a living dex in it is widest here: 156 against 649.
  Validation is red until step 3, and says so in as many words - "this game's encounters have not
  been gathered yet"._

  _The sequels show `updated-unova`, which is a different list rather than a longer one: it keeps
  twelve of these numbers, Victini through Watchog, and renumbers everything after them. Both names
  are in `unova.py` so that neither can quietly become "the" dex._

  _Step 1 for both: 11 new routes. One trade between the halves, and ten one-way Poke Transfers -
  each of the five Generation 4 cartridges into each of them, capped at 493 because nothing above
  Arceus existed to send. Four more wait for the sequels and two for Bank._

  _Two things moved while these were written. `bank.py` now holds the Bank node and the Poke
  Transporter edge, which were in `vc.py`: Transporter shipped in 2013 for the Generation 5
  cartridges and was given the Virtual Console releases three years later, so it was never a
  Virtual Console fact. And `ds.poke_transfer_edges` sits beside `gba.pal_park_edges`, declared by
  the generation that sends and called by the game that receives._

  _Decided: the Dream Radar is in and the Dream World is out. Both hand Pokemon to these games and
  neither is a game, but only one of them can still hand anything over - the Dream World was a
  website and it closed in 2014, so nothing it gave is reachable by anyone starting today. The
  Radar is a 3DS app someone can still run. It only feeds Black 2 and White 2, and it is in Phase 3
  rather than in a game's step 4 because it needs a shape this dataset does not have yet._

  - [ ] **Black** (`black`, gen 5, pair partner: White)
    - [x] 1 Entity + edges - 2026-09-22
    - [x] 2 Dex list - 2026-09-22
    - [x] 3 Wild - 2026-09-22
    - [x] 4 Gifts & statics - 2026-09-22
    - [x] 5 Trades & evolutions - 2026-09-23
    - [x] 6 Sprites - 2026-09-23
    - [x] 7 Events - 2026-09-23
    - [ ] 8 Validate + smoke test
    - 809 wild slots, 214 species catchable, 158 of those slots in the dark grass alone, and 30
      things handed over or standing in one spot.
    - Black City stands where White Forest does and is not the same kind of place: no wild
      Pokemon at all in the city, and a dozen older species in the forest. **PokeAPI has neither
      area** - no `black-city`, no `white-forest` - so step 7 must not read its silence as "cannot
      be caught", the way Gold's legendary birds taught. Hand-written slots may be needed, as the
      Bug-Catching Contest needed them.
  - [ ] **White** (`white`, gen 5, pair partner: Black)
    - [x] 1 Entity + edges - 2026-09-22
    - [x] 2 Dex list - 2026-09-22
    - [x] 3 Wild - 2026-09-22
    - [x] 4 Gifts & statics - 2026-09-22
    - [x] 5 Trades & evolutions - 2026-09-23
    - [x] 6 Sprites - 2026-09-23
    - [x] 7 Events - 2026-09-23
    - [ ] 8 Validate + smoke test
    - 809 wild slots too, and the same 214 species. The same gap as well: White Forest's dozen
      depend on who has moved in, and PokeAPI carries none of it.
  - [ ] **Black 2** (`black-2`, gen 5, pair partner: White 2)
    - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
    - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Events
    - [ ] 8 Validate + smoke test
  - [ ] **White 2** (`white-2`, gen 5, pair partner: Black 2)
    - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
    - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Events
    - [ ] 8 Validate + smoke test

  - Smoke test on the published exe: a collection made through the wizard called "Black on the
    DS", with Black as main game and Platinum and White linked. The linked-games step is the
    whole transfer graph in one screen - eleven games in three groups, and each card says how it
    reaches Black: the five Generation 3 cartridges "via Pal Park, then the Poke Transfer",
    which is a two-hop route composed by the app; the five Generation 4 games "via the Poke
    Transfer"; White "via trading". Generations 1 and 2 are absent, correctly - their only way
    out is Bank, and Bank is not written yet.
  - The grid reads "0 of 649 in Black", drawn from the Generation 5 sprite sheet. Audino's
    popup is what step 3 was for: four slots, each "How: rustling grass", with levels and odds.
    Victini's says "Liberty Garden only opens with the Liberty Pass, which went out over
    Nintendo Wi-Fi in 2011; the service closed in 2014", then the two distributions that handed
    one out. Solosis shows all three layers at once - "White only in Generation 5; trade one
    in", then White's own slots including one in the dark grass, each ending "Then to Black:
    trading". Marking Audino caught moved the counter to "1 of 649".
  - Every citation in the app reads "read 22 Sep 2026" rather than the day of the build, which
    is the cache-dated citation working end to end.
  - The user's settings were copied out first and restored byte for byte, and their data file
    was untouched: same checksum and same timestamp afterwards as before. A second copy of the
    app - theirs - was running throughout, so the automation was pointed at one window by
    process id rather than by title, and only the instance this test started was stopped.

- [x] **Black 2** (`black-2`, gen 5, pair partner: White 2) - 2026-09-23
  - [x] 1 Entity + edges - 2026-09-23
  - [x] 2 Dex list - 2026-09-23
  - [x] 3 Wild - 2026-09-23
  - [x] 4 Gifts & statics - 2026-09-23
  - [x] 5 Trades & evolutions - 2026-09-23
  - [x] 6 Sprites - 2026-09-23
  - [x] 7 Events - 2026-09-23
  - [x] 8 Validate + smoke test - 2026-09-23
  - 1688 ways to get something: 1288 wild slots, 320 evolutions, 47 gifts and statics, 27 eggs
    and 6 trades. 509 of the 649 its living dex asks for are fully covered, 117 partly, 20
    explained, 3 left over. Validation green on all 9 rules, for the whole dataset.
- [x] **White 2** (`white-2`, gen 5, pair partner: Black 2) - 2026-09-23
  - [x] 1 Entity + edges - 2026-09-23
  - [x] 2 Dex list - 2026-09-23
  - [x] 3 Wild - 2026-09-23
  - [x] 4 Gifts & statics - 2026-09-23
  - [x] 5 Trades & evolutions - 2026-09-23
  - [x] 6 Sprites - 2026-09-23
  - [x] 7 Events - 2026-09-23
  - [x] 8 Validate + smoke test - 2026-09-23
  - One more wild slot than Black 2 and one fewer fully covered entry, and otherwise the same
    counts entry for entry, which is what a version pair is.

  _Black 2 and White 2 are not a third version but a second pair - own story, own half of the map,
  own Pokedex - so `unova.py` keeps the two pairs apart wherever they disagree._

  _Their dex is 301 entries against the pair's 156, and it is not that list with more on the end:
  it keeps all 156 and adds 145 from older generations, and only the first twelve numbers survive
  the renumbering. So Black and White's regional dex, which held nothing a player had seen before,
  is the odd one out in the series and the sequels put it back - in the same region, two years
  later. Two lists that disagree about what nearly every number means, which is Johto's situation
  rather than Platinum's._

  _Registering them lit the four trades Black and White had been declaring into an empty space,
  and neither of those two files was edited to do it. Every route between two cartridges now has
  both of its ends: the ten still waiting all point at Bank._

  _Step 3 needed a second source. Twenty Hidden Grottoes are hidden around the sequels' Unova and
  PokeAPI has never heard of one: they are in no encounter table anywhere, and a dozen species are
  in nothing else. So `grottoes.py` reads the Bulbapedia page rather than asking an API - the first
  source in this dataset that is parsed instead of typed - and `hiddenGrotto` is a method in the
  schema beside the four spot types. The Funfest Mission grottoes at the foot of that page are
  deliberately not read: they were opened by a mission handed out over Wi-Fi and the service closed
  in 2014, so Glameow, Stunky and the Eevee line are step 7's business rather than step 3's._

  _Step 4 turned up the one case in this dataset of a species that is obtainable and still needs a
  second cartridge. Regirock, Regice and Registeel are in both halves and neither half can catch
  all three: catching Regirock is rewarded with the Iron Key in Black 2 and the Iceberg Key in
  White 2, and the other chamber only opens with the key the other game was given, sent over the
  Unova Link. That is not a trade and not a version exclusive, and it looks exactly like both._

  _Step 5's number is the day care's: twenty-seven babies against the first pair's four. It is one
  fact about Unova written large - the grass is full of grown-ups from older generations and almost
  none of their young, so Hariyama is on Route 23 with no Makuhita anywhere and Banette is in the
  Strange House with no Shuppet. Every parent named was checked to be reachable in that half
  without leaving it._

  _Step 6 had nothing to fetch, which is itself the finding. The sequels reuse the first pair's
  sprites exactly, so one set of 649 pictures answers for four games - and no generation before
  this one managed that: Platinum redrew Diamond and Pearl's, and HeartGold redrew Generation 4's
  again. Every one of the 649 a living dex here asks for is in the sheet, so nothing falls back._

  _Step 7 found Victini and Genesect swapping places between the two pairs. Black and White were
  never offered a Genesect outside Japan and South Korea; the sequels were offered one over Wi-Fi
  five weeks after they came out. And exactly one Victini distribution ever named the sequels - in
  Japanese, in Japan, for six weeks - where the first pair's went out worldwide._

  _It also grew the first pair's sentences. With four cartridges in one generation, "the other half
  has it" stopped being the whole answer: Black's Zekrom is in White and in Black 2, and Black did
  not have to be edited for that to be true, only for its reason to say so._

  - Smoke test on the published exe: a collection called "Black 2 on the DS", with Black 2 as
    main game and Ruby, Platinum and White 2 linked. The linked-games step shows the whole
    transfer graph in one screen, and the four edges step 1 lit up are in it: Generation 5
    offers Black, White and White 2, all "via trading", with Black 2 itself left out. The five
    Generation 3 cartridges read "via Pal Park, then the Poke Transfer" - a two-hop route the
    app composes - and the five Generation 4 games "via the Poke Transfer". Generations 1 and 2
    are absent, correctly: their only way out is Bank, and Bank is not written.
  - The grid reads "0 of 649 in Black 2", drawn from the Generation 5 sheet. Switching *Showing*
    to the Unova dex makes it "1 of 301" and renumbers every tile - Solosis moves from #577 to
    #139, which is step 2's whole point in one tile.
  - Four popups were read closely. Pachirisu shows "Route 3, Dark grass - How: a Hidden Grotto -
    55-59 - 15%", cited to "bulbapedia, read 23 Sep 2026", which is step 3's second source
    working end to end. Kecleon shows the Nature Preserve twice with the Permit sentence in
    full, and Ruby's two Devon Scope statics above it. Landorus says "Only at the Abundant
    Shrine, and only with Tornadus and Thundurus in the party - both of which the Pokemon Dream
    Radar is the only source of here". Solosis reads "White and White 2 only in Generation 5;
    trade one in", then White 2's own slots, each ending "Then to Black 2: trading".
  - Regice is the one that needed the whole step: three cards side by side, Black 2's saying the
    Iceberg Key is White 2's reward and has to be sent over the Unova Link, White 2's saying it
    is simply the reward, and Ruby's Braille puzzle with "Then to Black 2: Pal Park, then the
    Poke Transfer" under it. A player sees both halves of the asymmetry and the way round it at
    once.
  - Marking Solosis caught moved the counter to "1 of 649".
  - The user's settings were copied out first and restored byte for byte - same checksum as the
    backup - and their data file was untouched: same checksum, timestamp and size afterwards as
    before. The test ran against a data file in the scratchpad, and only the instance it started
    was stopped.

### Generation 6

- [x] **X** (`x`, gen 6, pair partner: Y) - 2026-09-23
  - [x] 1 Entity + edges - 2026-09-23
  - [x] 2 Dex list - 2026-09-23
  - [x] 3 Wild - 2026-09-23
  - [x] 4 Gifts & statics - 2026-09-23
  - [x] 5 Trades & evolutions - 2026-09-23
  - [x] 6 Sprites - 2026-09-23
  - [x] 7 Events - 2026-09-23
  - [x] 8 Alternate forms - 2026-09-23
  - [x] 9 Validate + smoke test - 2026-09-23
  - 1377 ways to get something: 797 wild slots, 355 evolutions, 168 form changes, 53 eggs, 20
    gifts and statics and nine trades. 562 of the 721 its living dex asks for are filled in the
    game itself, 133 are a transfer away, 19 are explained and seven are left over. Validation
    green on all 10 rules, for the whole dataset.
- [x] **Y** (`y`, gen 6, pair partner: X) - 2026-09-23
  - [x] 1 Entity + edges - 2026-09-23
  - [x] 2 Dex list - 2026-09-23
  - [x] 3 Wild - 2026-09-23
  - [x] 4 Gifts & statics - 2026-09-23
  - [x] 5 Trades & evolutions - 2026-09-23
  - [x] 6 Sprites - 2026-09-23
  - [x] 7 Events - 2026-09-23
  - [x] 8 Alternate forms - 2026-09-23
  - [x] 9 Validate + smoke test - 2026-09-23
  - The same counts entry for entry, bar the fishing rods: the two halves differ by eight Super
    Rod slots, eight Good Rod ones and three eggs. Sixteen exclusives each, which is what a
    version pair looks like.
  - Step 1 for both: released the same day everywhere, which no game before them was, and the
    first pair whose only route out of its generation is a service rather than a cartridge. They
    trade with each other and with the two Hoenn remakes, and they talk to Bank in both
    directions - where Generation 5 and the Virtual Console releases only ever push into it. Six
    of the eight routes they declare are waiting on a game or a node that is not written yet.
  - Step 2 made a decision no game before it had to: **X and Y show three Pokedexes**, Central
    (153), Coastal (153) and Mountain Kalos (151), sharing no species and each numbering from
    #001. The three are kept apart rather than run together into one list of 457, because a
    number spanning them is a number no game has ever shown. A dex entry now names which of its
    game's Pokedexes it is numbered in - null for the twenty games that show one list - and the
    switch in the app offers the three beside the National Dex. A tenth validation rule,
    `every-dex-number-means-one-thing`, guards it.
  - The three lists hold 457 and the games ask for 454: Diancie, Hoopa and Volcanion sit at the
    end of the Central list and are not counted towards completing it. They are the only entries
    in any dex here that the game itself excuses a player from, and step 7 is where that gets
    written down.
  - Step 3: 797 slots each, covering 338 of the 721 species X asks for and 337 of Y's. Four new
    methods, because Kalos stops hiding its second tables: **a horde** of five at once, **a
    flower patch** whose colour is a different table, **a berry tree** at the Berry Fields, and
    **an ambush** - which is one method rather than five, with what jumped written beside the
    slot: off a cave ceiling, out of the ground, out of the sky, out of a bush, out of a bin.
  - The **Friend Safari** needed more care than anything since the Hidden Grottoes. PokeAPI
    files it as eighteen ordinary areas with ordinary tables and it is none of those things: it
    is one room in Kiloude City that opens after the Hall of Fame, what lives in a Safari is
    decided by the friend code of somebody registered on the player's own 3DS, and the
    percentage on each row is how likely that Safari is to hold the species rather than how
    often it turns up. All three are said, once, as a gate on the place. The third slot is the
    only thing in this dataset that got *harder* after release: it opened when the friend
    appeared in the Player Search System, and that network closed in April 2024, so it now means
    playing side by side.
  - One find for step 7: every Friend Safari exclusive can be caught normally in Omega Ruby or
    Alpha Sapphire, which is worth knowing before anything is written off.
  - Step 4: 20 handed over or standing still in each half. **Six starters**, which no game had
    done since FireRed - three at the table in Aquacorde Town and three more from Professor
    Sycamore in his lab, so two of the three Kanto lines are in a Kalos living dex without a
    trade. Two fossils, one of which costs the other. Lucario, kept after the one-on-one battle
    atop the Tower of Mastery whether it is won or lost. Snorlax, woken with a Poke Flute
    borrowed at Parfum Palace.
  - **Which legendary bird a save gets is decided by the starter it began with**: Chespin brings
    Articuno, Fennekin Zapdos, Froakie Moltres. It roams from the Hall of Fame, flees every
    time, and waits at the Sea Spirit's Den once it has been met eleven times. So one
    playthrough reaches one of the three and the other two are a trade - checked against the
    wiki, because it is the kind of claim a source could easily have backwards.
  - Lapras is in the data with a place and a level and nothing else. Who hands it over was not
    established by anything read, and an invented NPC would be worse than a blank line.
  - Step 5: 355 evolutions, nine trades and 53 eggs. X covers 562 of the 721 its living dex asks
    for on its own, with 133 a transfer away and 16 left to the other half. Two of the six
    traders will take **anything in the party**, which no game had done before - both hand over a
    held item worth more than the Pokemon, the Gardevoirite and a Rare Candy.
  - **Shauna's trade is three trades.** She takes the first partner yours is strong against and
    gives it back in Vaniville Town at the end, so a save reaches two of the three Kalos
    starters and the third is in neither game by any means at all.
  - The egg table is **worked out rather than written down**, and that is new. Unova's is 27
    names typed by hand; X's is 53, and every one is the same three questions asked of PokeAPI -
    what does this grow into, can the game reach any of those, is it the bottom of its chain.
    The two things a hand-written table exists for turn out to be in the source as well: the
    incense is `baby_trigger_item` on the chain, and a Beldum needing a Ditto is a `gender_rate`
    of -1. Guarded by tests for the two ways it could lie - a Silcoon is not an egg, because
    breeding its Beautifly gives a Wurmple, and a Bayleef this game only knows how to evolve is
    not a parent anybody can put in the day care. Fifty-six of X's evolution records are that
    second case.
  - **PokeAPI has no Aerodactyl in Kalos at all**, which read as an entry neither half could
    fill - the only one in the region that is not a Mythical. It is simply missing: the Ambrette
    Town Fossil Lab revives an Old Amber, and the Old Amber is under a rock in the Glittering
    Cave. Written down by hand and cited, the way Johto's Bug-Catching Contest had to be.
  - **The Friend Safari is recorded and not counted**, which nothing in the dataset was before.
    Its rows are true - eighteen areas, real tables, 194 records - and a player cannot be sent to
    use them: a Safari holds what somebody else's friend code decided, there is no choosing
    which, and a third of every Safari has been shut since the 3DS network closed. So the records
    are kept and shown, with the reason on each, and they answer no to "can I get this here".
    A wild slot can now carry `doesNotCount`, the validator and the coverage report skip such
    rows, and the app's availability filter does too.
  - It showed up as a broken version pair. Counting the Safari left X with three exclusives and
    Y with ten, because a Safari pays no attention to which cartridge is asking and so dissolved
    one half's list and not the other's. Not counting it put the pair at **sixteen each**, which
    is what every pair before it looks like. The seven that a Safari really does hold say so in
    their reason rather than being silently written off.
  - What is left with no source anywhere is Diancie, Hoopa and Volcanion, which are step 7's.
  - Step 6: 919 files in `generation-vi/x-y`, one sheet for both halves - 721 species with not
    one gap, and 198 of the 199 forms. **The first generation with no sprites at all.** X and Y
    are in 3D; what stands in for a sheet is a shot of each model, and it shows: every sheet
    before this one is a grid of one size, and these are cropped to the Pokemon - 43x48 for a
    Bulbasaur, 121x129 for a Rayquaza.
  - Which needed the grid changed. Drawn sprites are scaled with nearest-neighbour, and doing
    that to a rendered model makes every edge ragged, so the grid now asks the main game which
    kind it has: `generation-vi` and later are smoothed, everything before it keeps its pixels.
    One prefix covers both 3D generations, because `generation-vi` is not a prefix of
    `generation-v/`.
  - The one form with no picture of its own is the female Eevee, whose file the sheet simply
    does not have - the Generation 5 sheet does. It falls back to the species picture, which is
    what the fallback is for.
  - Step 7 read the *In events* table on all 35 entries either half cannot fill. **Validation is
    green: ten rules, no errors, no warnings, for the whole dataset.** Each half now explains 19
    entries - the 16 the other keeps and the three Mythicals - and 562 of its 721 are filled in
    the game itself.
  - Diancie, Hoopa and Volcanion were only ever given away, which is the cleanest case this step
    ever meets: no cave to search and no version to trade with, only dates that have passed.
    Every one of their distributions went to X and Y alike.
  - Step 8: 199 forms each, and 168 of them now say how they are come by - 99 sexes, which need
    no table, and 69 written out. The step it was invented for: four of the families here are
    settled when the Pokemon is generated and cannot be changed afterwards at all, so what a
    player can act on is where to look and what to breed.
  - **Vivillon's pattern is a fact about the console**: the 3DS's own country and region decide
    it, before the Scatterbug even hatches, so one machine reaches one of the eighteen and the
    rest are a trade. **A Furfrou trim cannot be kept at all** - five days, and gone the moment
    it goes in a box - so no living dex can hold one, and in X and Y a trim is not a Pokedex
    entry of its own either. Both facts are in the data rather than left for a player to find.
  - All four items that change an older legendary are in Kalos, and every one is handed over for
    being shown the legendary itself, which no Kalos save can catch: the Reveal Glass in
    Reflection Cave, the DNA Splicers in Kiloude City, the Griseous Orb in Terminus Cave, the
    Gracidea at the Snowbelle City Pokemon Center. Each is a favour done for a Pokemon that came
    from somewhere else.
  - 31 forms are left without a record on purpose: the Eternal Flower Floette, which no game ever
    handed over, and Unown's letters, Basculin's stripe and Shellos's sea, which are settled
    where the Pokemon is caught and none of those is caught here.
  - The find is that **the 2014 Korean World Championship Series gave each half what it cannot
    catch**: a Heracross, a Manectric and a Tyranitar to X players, and an Aggron, a Houndoom
    and a Pinsir to Y players, on the same two days. A distribution covering a version exclusive
    is not new - Black and White's legendaries were the same - but one covering three at once,
    chosen for the half with no way to them, is deliberate work. Twelve of the 32 exclusives had
    no distribution at all.
  - Smoke test on the published exe: a collection called "X on the 3DS", with X as main game, Y
    linked and every kind of form ticked - 920 tiles, 721 species and 199 forms. The linked-games
    step offered **one** candidate, Y, "via trading", which is the transfer graph being right:
    everything older reaches X through Bank, and Bank is not written.
  - The *Showing* switch is the three-dex decision made visible. National dex reads "0 of 920";
    Central Kalos "0 of 229" and renumbers the grid to Chespin #001; Coastal Kalos "0 of 169"
    and starts at Drifloon #001. Vivillon's nineteen patterns all sit at #022, which is what a
    form taking its species' number looks like when there are nineteen of them.
  - Four popups were read closely. **Spritzee** is the one that matters: it says "not in X - Y
    only in Generation 6; trade one in. A Friend Safari can hold one, which takes somebody else's
    3DS and their friend code", and below it the Friend Safari row itself, with the gate under
    *Needs* and the reason it does not count under *But*, and Y's Route 7 slot with "Then to X:
    trading". Searching for it with *Available in X* ticked finds nothing; with *Available in Y*
    it is there. Recorded and not counted, end to end.
  - Skrelp shows three Y fishing slots and the trade across. Chespin shows the starter at the
    table in Aquacorde Town and Shauna's trade, requirement included: "only in a save that
    started with Fennekin: she picks the first partner yours is strong against". Diancie shows no
    method at all and the whole of what step 7 found. Furfrou (Dandy) shows the trim under
    *Changing its form*, with the five days and the box in the sentence.
  - Marking Chespin caught moved the counter to "1 of 920".
  - The user's settings were copied out first and restored byte for byte - same checksum as the
    backup - and their data file was untouched: same checksum and timestamp afterwards as
    before. The test ran against a data file in the scratchpad, and only the instance it started
    was stopped.

- [x] **Omega Ruby** (`omega-ruby`, gen 6, pair partner: Alpha Sapphire) - 2026-09-23
  - [x] 1 Entity + edges - 2026-09-23
  - [x] 2 Dex list - 2026-09-23
  - [x] 3 Wild - 2026-09-23
  - [x] 4 Gifts & statics - 2026-09-23
  - [x] 5 Trades & evolutions - 2026-09-23
  - [x] 6 Sprites - 2026-09-23
  - [x] 7 Events - 2026-09-23
  - [x] 8 Alternate forms - 2026-09-23
  - [x] 9 Validate + smoke test - 2026-09-23
  - 1724 ways to get something: 1150 wild slots, 355 evolutions, 132 form changes, 62 gifts and
    statics, 22 eggs and three trades. **203 of the 211 its own Pokedex asks for can be reached
    in the game itself**; the other eight say why not - seven are Alpha Sapphire's and the
    eighth is Jirachi. It records something about 596 of the 721 a living dex here wants, and
    the rest are a transfer away. Validation green on all 11 rules, for the whole dataset.
- [x] **Alpha Sapphire** (`alpha-sapphire`, gen 6, pair partner: Omega Ruby) - 2026-09-23
  - [x] 1 Entity + edges - 2026-09-23
  - [x] 2 Dex list - 2026-09-23
  - [x] 3 Wild - 2026-09-23
  - [x] 4 Gifts & statics - 2026-09-23
  - [x] 5 Trades & evolutions - 2026-09-23
  - [x] 6 Sprites - 2026-09-23
  - [x] 7 Events - 2026-09-23
  - [x] 8 Alternate forms - 2026-09-23
  - [x] 9 Validate + smoke test - 2026-09-23
  - 1727, which is the same but for one wild slot and two form records: the East Sea Shellos
    and its Gastrodon are this half's, and Omega Ruby has no way to make either. The same 203
    of 211 reachable, and seven exclusives each, which is what a version pair looks like.

  _The region and the generation are two modules again, after a generation that had nothing on
  either side of that line: `kalos.py` is the place and `gen6.py` is the hardware, the National Dex
  to Volcanion and the four cartridges that trade with each other. Omega Ruby and Alpha Sapphire
  will read `hoenn.py` and the same `gen6.py`._

  _The split matters more here than it looks. **Legends: Z-A is a Kalos game too** - Lumiose City on
  the Switch, three generations later - so `kalos.py` is the second region in this dataset, after
  Johto, whose games are not all from one generation. Its factories are named `gen6_cartridge` and
  `gen6_edges` for that reason: Z-A gets its own beside them rather than editing these, and nothing
  about Bank, a dex cap or a 3DS trade set may be written down as a fact about Kalos._

  - Step 1 for both: `hoenn.py` now holds two generations, the way `kanto.py` has since
    FireRed. Every Generation 3 name in it says so - `gba_cartridge`, `gba_edges`,
    `gba_dex_entries`, `GBA_DEX`, `GBA_PAIR_GIFTS` - beside `gen6_cartridge` and `gen6_edges`.
    What kept its plain name is `REGION` and the day care, which really is on Route 117 in all
    five games set here.
  - The four trades X and Y had been declaring into an empty space became real the moment these
    two registered, and neither of those files was touched. Nothing is left waiting on a game
    now - all 14 held-back edges are Bank's, which is Phase 3.
  - No route runs between a remake and the game it remakes. What a Ruby has to travel to reach
    an Omega Ruby is Pal Park, the Poke Transfer, Poke Transporter and Bank: five games, two
    services, and every step of it already in the graph.
  - Step 2: **211 entries, not the 202 Ruby shows.** The nine the remakes added - Gallade,
    Probopass, Magnezone, Budew, Roserade, Dusknoir, Chingling, Rhyperior, Froslass - are all
    Generation 4 relatives of families Hoenn already had, and each goes in beside its family
    rather than at the end. So from #032 on almost everything moves: 171 of the 202 entries
    have a number here that means a different species in Ruby, starting with #032, which is
    Surskit there and Gallade here. Pokemon Bank named the older list *Good Old Hoenn* to keep
    the two apart, which is the games agreeing that a regional dex is not one list for all time.
  - One Pokedex, so no entry names its list - unlike X and Y, which had to. The game asks for
    208 of the 211: Rayquaza, Jirachi and Deoxys are not counted towards completing it. That is
    the second dex here to excuse a player from anything, after Central Kalos, and not the same
    kind of excusing - two of these three are caught in the story after the story.
  - Validation is one error, which is the guard doing its job: `every-entry-has-a-method` folds
    a game with no encounters yet into a single finding rather than 211. The one entry nothing
    in the whole dataset can produce is **Jirachi**, which no game has ever handed over outside
    an event.
  - Step 3 found that **PokeAPI has no encounter tables for these two games**. Its rows for
    Omega Ruby and Alpha Sapphire are hordes, the Mirage spots, a little Rock Smash and the
    statics - no grass, no water, no fishing at all. Built from that source alone the games say
    a Tentacool cannot be caught in Hoenn. So the wild step reads **Bulbapedia's location
    pages** instead: `encountertables.py`, the second source in this dataset that is parsed
    rather than typed, after the Hidden Grottoes. Sixty-nine pages, one row per species, and
    the games a row belongs to written as a **colour** rather than as text - both cells say
    "OR" and "AS" either way, so a parser reading the letters would hand both halves every
    exclusive in Hoenn.
  - 1150 slots in Omega Ruby and 1151 in Alpha Sapphire, over 66 places, covering 205 species
    each - 108 of the 211 the regional dex asks for, before a single gift or evolution. 1043 of
    them are the wiki's and 107 are PokeAPI's: the Mirage spots, which the wiki keeps on pages
    that are not tables, so each source answers where the other is silent and a place both know
    is the wiki's. Otherwise every horde in Hoenn would be recorded twice.
  - Two new methods, and they are the two halves of Hoenn nobody could reach before: **Dive**,
    the table under the water a player is surfing on, and **Soaring**, the flocks met in mid-air
    on a Latios. Their icons are HM07, which is Dive in these games, and the Eon Flute, which is
    the whole of Soaring.
  - The **DexNav** is what 165 of those rows depend on and what the wiki explains in four words.
    It says "Exclusively as hidden Pokemon"; the dataset says a patch that rustles, named on the
    touch screen, crept up on rather than walked into - and, for most of them, only once Groudon
    or Kyogre has been dealt with.
  - Three things the pages said that a parser had to be taught. A heading opens a group and the
    next heading closes it, or the condition at the foot of a table would be read as true of the
    grass at the top of it. A heading that names a method outranks the Location column, which is
    twelve rows on Routes 118 and 121 where five Wingull walking up at once is a horde standing
    in long grass. And **Omega Ruby's Shellos is the West Sea one where Alpha Sapphire's is the
    East Sea one** - the only thing these two halves differ about by form rather than by species.
  - One correction outside Hoenn: a place name made out of a slug shouted its joining words, so
    the Mirage spots read "North Of Fallarbor" and Sinnoh's Spear Pillar "Between Pillars 1 And
    2". Fixed in `places.py` and the three Sinnoh games rebuilt. PokeAPI also files one Mirage
    Cave as west of *Rustburo*; the town has been Rustboro since 2002.
  - Step 4: 62 handed over or standing still in each half, and the shape of the list is unlike
    any game before it. **Twelve first partners** - Birch gives one of Hoenn's three on Route
    101, one of Johto's after the Hall of Fame, one of Unova's after the Delta Episode and one
    of Sinnoh's after the Hall of Fame a second time. Four choices of three, so a save keeps
    four and the other eight are a trade.
  - And **the legendaries of five generations**, which is what makes these two games a living
    dex in a way none before them were. The Mirage spots put Cobalion, Terrakion and Virizion on
    an island that only rises while three Pokemon in the party have maxed EVs; Uxie, Mesprit and
    Azelf in a cavern that wants three at maximum friendship; Raikou, Entei and Suicune in a
    forest that wants Ho-Oh or Lugia in the party, and which of the three is standing there is
    the minute of the hour. Dialga and Palkia are a gap in the sky that opens for the lake trio,
    Giratina a second gap behind them; Tornadus and Thundurus a black cloud that wants a
    Castform, Landorus the cloud behind that. Kyurem waits on Reshiram and Zekrom, who wait on a
    Pokemon at level 100.
  - A gift record can now carry a **gate** beside its conditions rather than instead of them,
    which is what those places needed: PokeAPI knows the day and the hour and cannot know that
    the island is not there at all.
  - The **fossils** are the second thing in this dataset written by hand, after Kalos's Old
    Amber: nine species that are an item carried to the Devon Corporation and no encounter
    anywhere. Route 111 still asks Hoenn's oldest question - the Root Fossil or the Claw Fossil,
    and the other is lost for good - and the remakes added seven more in rocks at the Mirage
    spots, split by version: Omega Ruby's hold the Dome, Armor and Plume Fossils, Alpha
    Sapphire's the Helix, Skull and Cover. The Old Amber is in both, and Kalos's two fossils in
    neither.
  - Which turned up an error in a game written two days ago: Ruby and Sapphire said their
    fossils came from the **Mirage Tower**, and that tower is Emerald's alone. Both corrected.
  - The **eon duo** swap places: each half meets one on Southern Island in its own story and the
    other waits on the same island for anybody holding an Eon Ticket. PokeAPI files each of them
    twice, as a gift and as a static; written as statics they fold into the one encounter they
    are.
  - Two things the source got wrong and one it could not know. Cobalion appears on three days
    and PokeAPI carries two of them, filing the Sunday with no condition at all. Giratina's gap
    is marked as a Sunday by PokeAPI and by nothing else, so the requirement says only what
    Bulbapedia says. And the Clear Bell and Tidal Bell, which Captain Stern swaps for the
    Scanner found on the same wreck, are what Ho-Oh and Lugia are waiting for - one each, Omega
    Ruby's and Alpha Sapphire's.
  - 126 of the 211 the dex asks for are now covered in the game itself. The 85 left over are
    evolutions, babies and version exclusives - step 5 - and Jirachi, which is step 7's.
  - Step 5: 355 evolutions, 22 eggs and three trades, which takes each half to 1592 records and
    **205 of the 211** its dex asks for. The egg table is worked out rather than typed, the way
    Kalos's is; the set that decides what counts as "already in your hands" moved to
    `breeding.py`, where the day care is, because it was never a fact about Kalos.
  - The three trades are the same three towns Ruby and Sapphire use and not the same trades.
    **Fortree wants a Spinda** where it wanted a Pikachu - a Hoenn Pokemon put where a Kanto one
    had been - and the two trainers whose names the game records swapped towns: Darrell is in
    Rustboro here and was in Fortree.
  - **Seven version exclusives each**, against Ruby and Sapphire's six, and the extra one is the
    same line's last stage: the remakes' Pokedex holds every stage of the Lotad and Seedot lines
    where Generation 3's stopped short. So Omega Ruby is missing Lotad, Lombre *and* Ludicolo,
    and Alpha Sapphire Seedot, Nuzleaf and Shiftry - plus Sableye, Seviper, Lunatone and Kyogre
    against Mawile, Zangoose, Solrock and Groudon.
  - Step 6: 926 files in `generation-vi/omegaruby-alphasapphire`, one sheet for both halves -
    **721 species with not one gap**, and 205 of the 206 forms. The second set in this dataset
    that is not a sprite sheet: these two are in 3D like X and Y, so what stands in for a sheet
    is a shot of each model, and the grid already knows to smooth `generation-vi` rather than
    scale it with nearest-neighbour.
  - The one form with no picture of its own is the **female Eevee** - the same one X and Y are
    missing, in a different sheet. It falls back to the species picture, which is what the
    fallback is for.
  - Step 7 read the *In events* table on all fifteen entries either half cannot fill, and found
    four. Both story legendaries went out in the same campaign - the **Dahara City Groudon and
    Kyogre**, Japan and South Korea over 2015 - a Mawile went to South Korea with XY&Z in 2016,
    and a Sableye went to Japan in the Mega Campaign of January 2016. The other eleven were
    never handed out at all, which is an answer too.
  - The joke in the Sableye row: Generation 6's *other* Sableye giveaway, Shigeki Morimoto's,
    went to **Alpha Sapphire alone** - the half that catches them in the wild.
  - **Jirachi has never been catchable in any game, in any generation.** Generation 3's answer
    was a disc that came in the box with another game; this generation's is nine distributions,
    of which the Pokemon 20th Anniversary Jirachi of April 2016 is the one most players outside
    Japan could have had. In between there was nothing at all.
  - **Validation is green: 11 rules, 0 errors, 0 warnings, for the whole dataset.** Step 8 is
    the forms, and step 9 the smoke test.
  - Step 8: 132 form records in Omega Ruby and 134 in Alpha Sapphire. The pair holds 110 forms
    and 75 of them get no record on purpose - Unown wants ruins that are in Johto, and Vivillon,
    Furfrou, Flabebe and Pumpkaboo all want Kalos, which is the other half of this generation
    and a different pair of games.
  - Every item that changes an older legendary is somewhere else than it is in X and Y, which is
    the whole reason a form's answer belongs to a region: the Reveal Glass is a woman selling
    mirrors on Mauville City 1F, the **DNA Splicers are hidden in the Gnarled Den - the Mirage
    spot Kyurem itself waits in**, the Griseous Orb is underwater off Route 130, and the
    Gracidea is handed over on Route 123 for showing somebody a Shaymin.
  - Three answers only these two games have. **Hoopa Unbound** is the second form here a living
    dex cannot hold, after Furfrou's trim: three days, and back in the bottle the moment it goes
    in a box. **The Cosplay Pikachu** is six costumes that cannot evolve, cannot breed and
    cannot be traded or put into Bank - they stay on the cartridge they were given on, which
    nothing else in the dataset does. And the **East Sea Shellos** is the only form whose answer
    is the version's: Alpha Sapphire catches them on Routes 103 and 110 where Omega Ruby catches
    the West Sea kind.
  - And step 8 found something in the shared table. **Deoxys's three formes were pinned to the
    three Generation 3 cartridges** that hold one each - right while the dataset stopped at
    Generation 3, wrong from Diamond on, where a meteorite cycles through all four. Thirteen
    games got them back, each with its own place: outside in Veilstone City, on Route 3 in
    Johto, in the Nacrene Museum, in Ambrette Town's Fossil Lab, and here in Professor Cozmo's
    house in Fallarbor - the same meteorite Ruby and Sapphire have a fetch quest about.

  - Smoke test on the published exe: a collection called "Omega Ruby on the 3DS", with Omega
    Ruby as main game, Alpha Sapphire linked and every kind of form ticked - **930 tiles**, 721
    species and 209 forms. The linked-games step offered exactly three, X, Y and Alpha Sapphire,
    all "via trading", which is the transfer graph being right: everything older reaches these
    two through Bank, and Bank is not written.
  - The *Showing* switch reads "National dex" at 930 and "Hoenn dex" at 261, renumbered from
    Treecko #001 - and it is the remakes' list rather than Ruby's: **#031 Gardevoir and #032
    Gallade stand side by side**, which is what the nine inserted entries do to the numbering.
  - Five popups were read closely. **Ludicolo** is the one that matters, because it is what the
    eleventh rule was written for: "Not in Omega Ruby - Alpha Sapphire only in Generation 6;
    trade one in", and under it the evolution from Lombre that this game can perform and never
    start. **Cobalion** shows the Pathless Plain, level 50, and one sentence carrying both the
    gate and the days: three Pokemon with maxed EVs, on a Wednesday, a Friday or a Sunday.
    **Deoxys** shows four tiles at #386 and the meteorite in Professor Cozmo's house. **Pikachu
    (Libre)** shows the Cosplay sentence in full, cited to Bulbapedia. **Treecko** shows Birch
    on Route 101.
  - The *Available in* filter was checked both ways round: Lotad with "Available in Omega Ruby"
    finds nothing and with "Available in Alpha Sapphire" finds one. Marking Treecko caught in
    Omega Ruby moved the counter to "1 of 930" and wrote the data file.
  - One blemish worth writing down rather than fixing here: the Cosplay Pikachu's record in the
    linked game still carries the app's generic footer, "Then to Omega Ruby: trading", under a
    sentence that says it cannot be traded. The sentence is right and the footer is the transfer
    graph talking about the game rather than about the form. A form that cannot leave its
    cartridge is new in this dataset and nothing above the graph knows it yet.
  - The user's settings were copied out first and restored byte for byte - same checksum as the
    backup - and their data file was untouched: same checksum and timestamp afterwards as
    before. The test ran against a data file in the scratchpad, and only the instance it started
    was stopped.
  - One thing went wrong and is worth the note: the first attempt wrote the settings file with
    single backslashes, which is not JSON, so the app fell back to its defaults, asked where to
    keep data, and rewrote the real settings with the default path and theme. The backup put it
    back, byte for byte, and the second attempt wrote the file through a JSON encoder instead.

### Generation 7

- [x] **Sun** (`sun`, gen 7, pair partner: Moon) - 2026-09-24
  - [x] 1 Entity + edges - 2026-09-23
  - [x] 2 Dex list - 2026-09-23
  - [x] 3 Wild - 2026-09-23
  - [x] 4 Gifts & statics - 2026-09-23
  - [x] 5 Trades & evolutions - 2026-09-23
  - [x] 6 Sprites - 2026-09-23
  - [x] 7 Events - 2026-09-24
  - [x] 8 Alternate forms - 2026-09-24
  - [x] 9 Validate + smoke test - 2026-09-24
- [x] **Moon** (`moon`, gen 7, pair partner: Sun) - 2026-09-24
  - [x] 1 Entity + edges - 2026-09-23
  - [x] 2 Dex list - 2026-09-23
  - [x] 3 Wild - 2026-09-23
  - [x] 4 Gifts & statics - 2026-09-23
  - [x] 5 Trades & evolutions - 2026-09-23
  - [x] 6 Sprites - 2026-09-23
  - [x] 7 Events - 2026-09-24
  - [x] 8 Alternate forms - 2026-09-24
  - [x] 9 Validate + smoke test - 2026-09-24
  - Step 1 for Sun and Moon: 5 new routes, and the graph is at 116. One trade between the halves
    and four Bank edges, a deposit and a withdrawal each. Four more wait for Ultra Sun and Ultra
    Moon, which is the first thing held back since Bank was written.
  - `alola.py` is new and is the region module *and* the generation's, the way `unova.py` is -
    but for the opposite reason. Unova had one region and one console with nothing on either
    side of the seam; Alola has four cartridges on a 3DS and Let's Go has two games on a Switch,
    and those six share no trade set, no dex and no way out. A file called `gen7` would have to
    say "except in Let's Go" about every line in it. Let's Go belongs in `kanto.py`, which has
    served that region for two generations already.
  - **The Virtual Console releases finally have somewhere to go.** Bank refuses a Generation 6
    game anything that came out of a Virtual Console Red or Gold; these four it does not refuse.
    Six games that have had a node and no destination since Bank was built now reach one, which
    is the whole reason Generations 1 and 2 are in this dataset as their 3DS releases.
  - **A cable between the two pairs is capped at 802**, which is the Time Capsule's shape twenty
    years on: a both-ways route carrying everything one way and stopping short the other. The
    five species Ultra Sun and Ultra Moon introduced cannot be read by Sun or Moon, by cable or
    by Bank - so `bank_edges` now takes a species filter for the withdrawal beside the history
    window it already took. The cap is written once, in `alola.py`, because a filter is not part
    of what makes two declarations the same edge: two games declaring the same route differently
    would silently collapse into whichever was seen first.
  - Alola has a meteorite too, beside Sophocles in the Hokulani Observatory, and the shared form
    table did not know it - so Deoxys's three formes were missing from both games the moment
    they were registered. Same shape as the correction Omega Ruby found, caught this time before
    it was committed. `METEORITE` now runs from Diamond to Moon.
  - The shared form table gained 70 forms with these two: the Alolan forms, the Totem ones, and
    Ash-Greninja. 279 of the 280 it holds are in Sun; the one that is not is the spiky-eared
    Pichu, which never leaves HeartGold and SoulSilver.
  - Step 4 for Sun and Moon: 90 and 89 records - three starters, an Egg, two fossils each,
    twelve statics, and seventy Poke Pelago arrivals. The unexplained entries fell from 33 to 21,
    and the twenty-one left are the evolutions of step 5, the one in-game trade that fills
    Steenee, and the two events of step 7.
  - **The fossils are a version exclusive the source does not know.** Olivia's shop in Konikoni
    City stocks two of the four and which two is the cartridge's - the Skull and Cover Fossils in
    Sun, the Armor and Plume in Moon - and PokeAPI files all four under both halves, exactly as
    it does Sinnoh's two. Refused with a reason rather than quietly kept, which is what
    `excluded` is for.
  - **A gift can be a form now too**, which the wild step had already needed: what stands on
    Exeggutor Island is the Alolan Exeggutor and not the Kantonian one, and the 10% Zygarde comes
    off the same Reassembly Unit as the 50%. Both steps ask `forms.targets_of` the same question
    now, and a game that passes no forms reads exactly as it did.
  - The giver is the box art, so Cosmog cannot be one record for the pair: Solgaleo hands it over
    at the Lake of the Sunne and Lunala at the Lake of the Moone, and each of the two is a static
    in its own half and nowhere in the other.
  - Necrozma's two conditions had no wording and now have one. Both are halves of the same
    errand - Looker and Anabel hire the player to round up the Ultra Beasts that came through
    with Lusamine, and what waits at the end of it is the one that came through after them.
  - Step 5 for Sun and Moon: **1194 and 1193 ways to get something** - 708 wild slots, 386
    evolutions, 90 gifts and statics, six trades and four eggs. Two entries are left unexplained
    in each, Magearna and Marshadow, and both are step 7's.
  - **A trader can hand over a form now.** The one in Tapu Village wants a Haunter and gives an
    Alolan Graveler, which turns into an Alolan Golem the moment it arrives - and "Graveler"
    would name the wrong rock. What is recorded is what is handed over, as Sinnoh's
    Haunter-into-Gengar already was.
  - That is the third record kind this region has taught to carry a form, after the wild slots
    and the gifts. It also moved Unova's note on: Kyle's Basculin in Driftveil City is one stripe
    in Black and the other in White, and what was missing is no longer the schema but the fact -
    Bulbapedia lists both against the one trade and does not say which cartridge gets which.
  - The name on each trade is the original trainer the game stamps on what is handed over - Hila,
    Kihei, Momoe, Sill, Kumu, Anga - rather than the nickname, which all six come with and which
    a player can change.
  - Four eggs, which is few and right: the nursery is only asked for what nothing else in the
    game produces, and by this step almost nothing is left.
  - Step 9 for Sun and Moon: **validation green at 11 rules, 0 errors, 0 warnings**, over the
    whole dataset rather than these two - the evolution change of step 8 touched every game, so
    every game was rebuilt and every game was checked.
  - Coverage over the living dex: Sun **510 full, 267 partial, 10 missing, 15 unobtainable**;
    Moon 509, 268, 10, 15. The ten are the Mythicals no game in this dataset produces - Jirachi,
    Phione, Manaphy, Victini, Keldeo, Meloetta, Genesect, Diancie, Hoopa, Volcanion - and they
    are `missing` here rather than `unobtainable` for a structural reason worth writing down:
    **a reason lives on a dex entry, and these games have no dex entry to put one on.** The
    Alola Pokedex is 302 names and none of the ten is among them, so Sun has nowhere to say
    what Kalos says about Diancie. Every generation has some of these and the count grows as
    the Mythicals pile up - Omega Ruby has 9, X has 7, Black has 3 - so it is a shape rather
    than a Generation 7 fault.
  - Smoke test on a collection with **Sun as main game and Moon linked**, all four form kinds
    on. 1075 tiles in the National Dex view, 273 of them forms; 404 in the Alola Dex view, 102
    of them forms; 444 tiles available in Sun without anything transferred in.
  - The two tiles this pair's last three steps were about both read correctly. **Magearna is
    available**, with the QR Scanner sentence and the delivery man in Hau'oli City - step 7's
    finding, all the way through to the screen. **Marshadow is not**, with the Mount Tensei
    distributions and the February 2018 cut-off. Sandshrew, Oranguru and Shieldon each show
    their exclusive reason with the event that covered it, and Oranguru and Shieldon also show
    Moon's ways underneath with "then trade it over".
  - And the four kinds of form answer read the way step 8 meant them to: **Alolan Raichu** by
    evolving (`pikachu-to-raichu-alola`, which did not exist this morning), **Silvally (Fire)**
    from Gladion's memories at Aether Paradise, **Minior (Blue)** as a core settled when it
    appears on Mount Hokulani, **Giratina (Origin)** off the Griseous Orb sold at Antiquities of
    the Ages. **Gumshoos (Totem)** is not available and says nothing, which is right.
  - One thing the smoke test showed that is true and not obviously helpful: a Sun player reading
    Sandshrew's reason gets no "in Moon" trail under it, because what Moon has is the *Alolan*
    Sandshrew and the trail is looked up per species. The same goes for Vulpix the other way
    round. Nothing is wrong in the data - the Kantonian Sandshrew really is unobtainable in both
    halves - but a regional form is the first case where "the other half has one" and "the other
    half has this exact tile" come apart.
  - The published exe starts on the new dataset and stays up, with no crash log. The data file
    was copied before the test and is byte-identical after it; the two backups the app wrote
    during the run were removed, and the four that were there before it were left alone.
  - Step 8 for Sun and Moon: **273 forms each, 187 of them now with a record**, where 15 had
    one before. 148 form changes per game, and 12 more evolutions - and those twelve cost more
    work than the 148, because they were a hole in the pipeline rather than a table nobody had
    written.
  - **PokeAPI knew which Raichu a Thunder Stone makes in Alola, and this pipeline was throwing
    it away.** Every evolution detail can carry `required_pokemon_form` and `evolved_pokemon_form`,
    and `IGNORED_DETAILS` skipped both with a note saying the forms table did not carry them
    yet. It does now, and they turned out to be most of what makes Generation 7 different: it
    is `evolved_pokemon_form` that says a Thunder Stone here makes an *Alolan* Raichu, and
    `required_pokemon_form` that says only an Alolan Vulpix takes the Ice Stone.
  - Seven Alolan forms had no way to get them at all before this - Raichu, Ninetales, Sandslash,
    Persian, Golem, Muk and Marowak - because their evolution records named the species and the
    species' plain form is the Kantonian one, which is not in these games. Seven tiles in the
    Alola dex that nothing filled.
  - **A second bug underneath it, and this one was not Alola's.** `evolution_encounters` picked
    `max(usable, key=order)` - one variant per pair - which is right when a later generation
    replaces a way of evolving and wrong when several ways *start together*. Wormadam has worn
    three cloaks since Diamond and Pearl and only one was recorded; the same for Gastrodon's two
    seas, Deerling's four coats in Black and White, Flabebe's five colours and Pumpkaboo's four
    sizes in X and Y, Meowstic's two sexes, and Rockruff's two Lycanroc here. The newest version
    group still wins; what changed is that a tie at that version group is now several answers
    rather than one picked arbitrarily. **18 rules across the dataset became 30, and every game
    from Diamond on gained records it should always have had.**
  - **Telling a form from a spelling took two signals, not one, and the first attempt used only
    one of them.** PokeAPI's form fields point at a *form* resource, and it has one for a default
    as readily as for anything else: the ordinary Lycanroc is `lycanroc-midday`, the ordinary
    Gastrodon is `gastrodon-west`, the ordinary Burmy is `burmy-plant`. Asking "is this also one
    of the species' other Pokemon" sorts out Lycanroc and got Gastrodon wrong, because the East
    Sea is a form of the only Gastrodon there is. Asking "does this project record that form"
    sorts out Gastrodon and got Lycanroc wrong, because the Dusk one belongs to games not built
    yet and quietly became a plain Lycanroc - which would have told a Sun player to find a
    Rockruff with Own Tempo and wait for dusk, in a game that cannot do it. Both questions, and
    a third answer: the species, a form, or a fork this dataset refuses to guess at.
  - **Alola buys what Kalos had to earn.** The items that change an older legendary are all here,
    and not one of them asks to be shown anything: the Griseous Orb and the Gracidea are for sale
    in the Hau'oli City mall, the DNA Splicers and the Prison Bottle come from the same Aether
    Foundation employee in the same back room, and the Reveal Glass is Professor Burnet's reward
    for beating Olivia. In Kalos a Scientist wanted to see all three forces of nature first.
  - **Cosplay Pikachu never leaves Omega Ruby and Alpha Sapphire.** Bank refuses all six and so
    does a trade, so no Generation 7 box can hold one - and the version group said otherwise,
    which put six tiles in Sun's grid that nothing could ever fill. `forms.py` now says so, the
    way it already did for the spiky-eared Pichu. Sun's form table went from 279 to 273. It is a
    *kind* rather than a curiosity now: a form that cannot be transferred is stuck in its own
    generation however long the series runs.
  - **Omega Ruby's own smoke test saw this coming.** Its note reads: "A form that cannot leave
    its cartridge is new in this dataset and nothing above the graph knows it yet." Something
    does now - the form table itself - which is why no Generation 7 grid has a tile for one. The
    footer that note was actually complaining about is still there, because that is the transfer
    graph talking about the game rather than about the form, and it is Phase 3's to answer.
  - **The Totem Pokemon are Ultra Sun and Ultra Moon's, not these two.** A Totem at a trial site
    is a battle, not a catch. What can be kept is a Totem-*like* one, handed out by Samson Oak at
    Heahea Beach for Totem Stickers - in the second pair only. They trade back to Sun and Moon,
    which is why the form is theirs to hold and not theirs to produce.
  - Of the 86 forms still without a record in each half, the great majority are families simply
    not caught in Alola - Unown's letters, Vivillon's patterns, Furfrou's trims, Deerling's
    coats - which is the honest answer rather than a gap. Four are named in `ALOLA_NO_WAY_HERE`
    because a family sentence would otherwise have reached them: the Eternal Flower Floette,
    Basculin's blue stripe, the Original Color Magearna that belongs to HOME, and Ash-Greninja,
    which came out of the Special Demo Version and left with the eShop in March 2023.
  - **What step 8 did not finish: the pictures.** The third of its three parts is a sprite of
    each form from this game's own sheet, and Generation 7 has no sheet - which is the Phase 3
    item already queued. Every form here falls back to the Generation 6 drawing or to its
    species, and an Alolan Raichu currently shows a Kantonian one.
  - One more thing left alone deliberately: **PokeAPI files Alola's wild Gastrodon under the
    plain species**, and Bulbapedia is clear that the one in Alola's grass is the East Sea. The
    evolution now names both seas correctly; the *wild* record still says "Gastrodon". Saying
    which form a game's default wild catch really is needs a mechanism this dataset does not
    have yet, and it is the same shape for Alola's Shellos.
  - Step 7 for Sun and Moon: **eighteen version exclusives and one Mythical**, and the
    twentieth entry turned out not to belong on the list at all. Ten reasons written per half,
    fifteen in the file once `spread_unobtainable` has handed each line's reason down to the
    evolutions - the same shape Diamond's five produced eight of.
  - **Magearna is not an event, and step 7 is what found that out.** It was one of the two
    entries left unexplained after step 5, and it looked exactly like the other one. It is not:
    Bulbapedia files it under *Game locations* beside the grass and the fishing spots -
    "Hau'oli City (QR Scanner)" - and keeps the word *Event* for Marshadow one line below. The
    QR Code is a picture published for each region in 2016 and still published, the scanner is
    the 3DS's own camera, and there is nothing at the other end to switch off. Bulbapedia's
    distribution row has no closing date because there is nothing to close. So a Sun cartridge
    bought today can still fill that tile, and calling it unobtainable would have been a lie.
  - It is also the only record in either game that no source this pipeline reads has a row for.
    PokeAPI has no encounter for Magearna in any version - not a gift, not a static, not even
    the `event` method it does use for distributions it knows about - so `QR_MAGEARNA` is
    hand-written and cited to the QR Scanner page, the way Hoenn's mirage fossils are.
  - **One basket of Eggs covered all four exclusives nobody could trade for.** Six Eggs went
    out at Pokemon Centers in Japan over Easter 2017 and the same six in South Korea a month
    later: Goomy, Mareanie, and then Oranguru, Passimian, Turtonator and Drampa - two from each
    half, handed to *both* halves. It is the Kalos trick of covering a version exclusive on
    purpose, done tidily: one distribution, four gaps. Kalos took three at a Korean tournament.
  - Three of each half's seven non-fossil exclusives were covered and four never were. What was
    never covered is worth as much as what was: **all four Ultra Beasts of the pair have no
    distribution anywhere**, and neither do Unova's four - Rufflet, Vullaby, Cottonee, Petilil.
    Cottonee's only giveaway ever was Sword and Shield's Wild Area News, thirteen years later.
  - The four fossils are the one split that is **only** Sun and Moon's. Olivia stocks two of the
    four per cartridge; Ultra Sun and Ultra Moon sell all four in both halves. Their reasons
    take `fossil_only_on`, which moved from `sinnoh.py` into `exclusives.py` to be said twice -
    a fossil is an item, so it can cross the link held by a traded Pokemon and be revived here.
  - Not one of the four fossil Pokemon has ever been handed out for these games. Shieldon,
    Archen, Cranidos and Tirtouga have exactly one distribution between them in the whole
    series - the Pokemon Adventure Camp in Japan in 2012, for Black and White - which is the
    same emptiness Diamond and Pearl found and reported as a finding rather than a gap.
  - `only_on` here names the pair partner and nothing else, deliberately. Sixteen of the
    eighteen splits hold in Ultra Sun and Ultra Moon too and those two will belong in the
    sentence when they are built; the fossils are the two that will not, so the sentence cannot
    be written ahead of time. A game this dataset does not have is not a trade to send anyone
    after.
  - **The whole dataset is green for the first time since Generation 7 was started**: 11 rules,
    0 errors, 0 warnings, across 28 games.
  - **Step 6 for Sun and Moon: they have no sprite sheet, and nor does anything else in
    Generation 7.** Every generation from the first to the sixth has a folder of battle sprites
    in the sprite repository; the seventh has none, not for these two and not for Ultra Sun and
    Ultra Moon either. PokeAPI publishes a URL for the second of those and the repository does
    not have the file - the source promises a picture it cannot hand over, which is worth
    writing down because a build that trusted it would have fetched 404s in silence.
  - What Generation 7 does have there is a folder of box icons. They are a different kind of
    picture from the battle sprites every other game shows, so they are not used: the entities
    carry no sprite set and the app draws the shared one, as every sheetless game already does. That
    was a fallback rather than an answer, and it was answered on 2026-09-24: the four now draw
    from `generation-vii/alola`, off the Bulbagarden Archives. Phase 3 has what that found,
    including the two things this note could not have known - that Ultra Sun and Ultra Moon have
    no sheet of their own, and that the 800-pixel pictures which look like theirs are Let's Go's.
  - **That would have been a bad answer on its own, and the fix reaches the whole dataset.** A
    form used to have nothing but its species to fall back on, so in a region where most of the
    Kanto Pokemon *are* the regional form, an Alolan Rattata's tile drew a Kantonian one. The
    shared set now carries a picture per form as well as per species, and `SpritePath` tries
    four things instead of three: the sheet's form, the sheet's species, the shared form, the
    shared species.
  - The sheet still wins all the way down, so nothing already drawn changes: a Wash Rotom in
    Black keeps the Generation 5 Rotom it has always had, and gains a picture of the form only
    where its sheet had none.
  - Checked on the published exe: Generation 7 shows two covers in the picker, and a Sun
    collection's linked-game list holds **every other game in the dataset** - Generations 1 and
    2 "via Poke Transporter, then Pokemon Bank", Generation 3 with Pal Park and the Poke Transfer
    ahead of it, Generation 6 simply "via Pokemon Bank", which is one hop in and one hop out with
    no cable between the two generations at all.
  - Validation green on all 11 rules; 501 pipeline tests and 248 app tests.
  - Step 2 for Sun and Moon: 302 entries each, Rowlet to Marshadow, and the same list for both
    halves - a version pair has never disagreed about its own dex.
  - **No `dex` name on the entries.** X and Y needed one because they show three lists and a
    player picks between them; Alola shows one. The source has the four island dexes too -
    Melemele, Akala, Ula'ula, Poni, numbered from 1 - and they are deliberately not written:
    those numbers are the official guidebooks', and in the game a Pokemon keeps its overall
    Alola number wherever it is listed, so Pikipek is #010 on all four islands although it is
    first on three of them. Writing them would print numbers no player was ever shown. Thirty-
    nine entries are on no island at all, so the four are not even a partition of the list.
    `ISLAND_DEXES` names them so the next person knows they were looked at and left.
  - PokeAPI calls this one `original-alola`, as it does Unova's and Sinnoh's first lists. The
    other is `updated-alola`: 403 entries, first disagreeing at **#024 - Pichu here, Buneary
    there** - which is exactly what Bulbapedia says and what makes the two lists two lists.
  - Validation is red until step 3, on purpose and with a useful number in it: 81 of the 302
    have no source anywhere in the dataset, which is precisely the 81 species these games
    introduced, and the other 221 are covered by games already built.
  - Step 3 for Sun and Moon: **708 wild slots each**, and the unexplained entries fell from 302
    to 33. Unlike the Hoenn remakes, the source has these tables - places, methods, levels and
    slot chances, all of it - so no wiki had to be read for them.
  - **A wild slot can be a form now, and in Alola most of them are.** Encounters hang off a
    Pokemon and a species can be several: every Rattata on Route 1 is `rattata-alola`, every
    Diglett on Route 2, every Grimer in Hau'oli City, and the Kantonian ones are nowhere in the
    game. `wild_encounters` takes the game's own form table and asks the source for each
    species' whole set of Pokemon rather than only its default; a form this game does not have
    is skipped, so the source's Dusk Lycanroc does not become a tile Sun could never fill.
    59 of Sun's records target a form, over 14 of them - ten Alolan, Oricorio's three other
    styles, and Midnight Lycanroc.
  - **And six games built before this one gained the slots they had been missing.** Every game
    passes its forms now, not only the ones written after Alola: Blue-Striped Basculin has
    encounters in Black, White, Black 2, White 2, X and Y, and Pumpkaboo's Small, Large and Super
    sizes have them in X and Y, and none of the six had recorded one. 192 records in all.
  - That turned up a sentence that was wrong rather than merely thin. Basculin's form change said
    "the stripe follows the game", which reads as though a Black player cannot catch a blue one -
    and in Black the blue stripe is not absent, it is in the rippling water, 60% surfing and 40%
    on the Super Rod, exactly as the red one is in White's. Both games hold both stripes and the
    water tells them apart. Reworded. Pumpkaboo's said the sizes get rarer the bigger they are,
    which Route 16's own numbers do not bear out; reworded to what the slots now say themselves.
  - **Two new encounter methods**, which is what Alola has of its own. An SOS ally is the
    generation's signature - a wild Pokemon at low health calls for help - and whole species are
    in these games only as somebody else's ally, so it is a way of starting an encounter rather
    than a note on one: 133 slots in Sun, three species that have no other route. The compound
    the source gives beside it, an ally called by something met in a bubbling spot, stays an SOS
    slot and says where in its requirement, the way fishing in a ripple already did.
  - The other took reading the source twice. Its method 34 is called "Fishing at bubbling spots
    in the water" and it turns up in **Haina Desert**, which has no water at all. Bulbapedia
    settles it: the desert's table is *sand clouds* and Route 2's is *rustling grass*. It is
    Unova's four moving spots come back as one, and the source named the family after the only
    member of it that is wet. So the method here is `movingSpot`, named for what the three have
    in common, and which one a player is looking at follows from where the record puts them.
  - The version split the source does have: 21 records differ between the two halves - Cottonee
    and Petilil, Braviary and Mandibuzz, Buzzwole and Pheromosa - which is what step 4 will read.
  - **And the one thing it does not: when a slot is there.** Alola's wiki tables have two rate
    columns and they are Day and Night, not Sun and Moon - Yungoos stands in Route 2's grass by
    day and Alolan Rattata by night, in both games - and PokeAPI carries no time-of-day
    condition for a single Alola slot. `alolatables.py` reads it: 56 pages, one question, and
    **111 records a game now say which hour**, 56 by day and 55 by night.
  - It is a layer rather than a source. The places, the levels and the odds stay PokeAPI's; a
    page that cannot be fetched, a row whose Pokemon will not resolve and a slot the wiki files
    elsewhere each cost a condition and no record, which is why nothing in it raises. Two of the
    fifty-seven places needed a page named by hand: the wiki's Berry fields carry no region in
    their title, and every slot the source files under Royal Avenue is in the abandoned Thrifty
    Megamart, which has a page of its own and stands on another island.
  - The same rows answered the other half of the moving-spot question for free. Their **Location**
    column names the terrain - rustling grass, a rustling bush, a rustling tree, a cloud of sand,
    a cloud of dirt, a shadow on the water, water that splashes - and the heading above them
    names the seventh, a bubbling spot, because those rows are labelled "Fishing" like any other
    water. **77 of Sun's 81 moving-spot records now say which of the seven they are**, which is
    what the source flattened into one method and called after the wet one.
  - A blemish fixed while the names were being read: five places in the dataset were spelled with
    a curly apostrophe and everything else with a straight one - Hau'oli City one way and Hau'oli
    Cemetery the other, in the same game. Four were Alola's and one Kalos's. Normalised in
    `places.py`, where the English name is taken.

- [x] **Ultra Sun** (`ultra-sun`, gen 7, pair partner: Ultra Moon) - 2026-09-24
  - [x] 1 Entity + edges - 2026-09-24
  - [x] 2 Dex list - 2026-09-24
  - [x] 3 Wild - 2026-09-24
  - [x] 4 Gifts & statics - 2026-09-24
  - [x] 5 Trades & evolutions - 2026-09-24
  - [x] 6 Sprites - 2026-09-24
  - [x] 7 Events - 2026-09-24
  - [x] 8 Alternate forms - 2026-09-24
  - [x] 9 Validate + smoke test - 2026-09-24
- [x] **Ultra Moon** (`ultra-moon`, gen 7, pair partner: Ultra Sun) - 2026-09-24
  - [x] 1 Entity + edges - 2026-09-24
  - [x] 2 Dex list - 2026-09-24
  - [x] 3 Wild - 2026-09-24
  - [x] 4 Gifts & statics - 2026-09-24
  - [x] 5 Trades & evolutions - 2026-09-24
  - [x] 6 Sprites - 2026-09-24
  - [x] 7 Events - 2026-09-24
  - [x] 8 Alternate forms - 2026-09-24
  - [x] 9 Validate + smoke test - 2026-09-24
  - Step 9 for Ultra Sun and Ultra Moon: **validation at 11 rules, 0 errors**, and the two
    warnings about the Own Tempo Rockruff that step 7 explained. `ValidationReport.ok` is
    `not self.errors`, so that is green by the build's own definition.
  - Coverage: **613 full, 165 partial, 10 missing, 19 unobtainable** per half, out of 807. The
    613 is the highest any game in this dataset reaches by itself.
  - Smoke test on a collection with Ultra Sun as main game and Ultra Moon linked, all four form
    kinds on: 1089 tiles in the National Dex view, 546 in the Alola Dex view. Everything the
    last six steps were about read correctly - **Ho-Oh available off a wormhole**, Lugia not and
    "in ultra-moon: 1 way, then trade it over" under it, Poipole from Soliera, Naganadel by
    evolving it, both Necrozma fusions with Colress's items, the Partner Cap Pikachu off its QR
    Code, a Totem Gumshoos from Samson Oak, Zeraora and Marshadow unobtainable with their
    distributions named.
  - **And it found a real bug, which is what a smoke test is for.** Deoxys (Attack) said
    *available in Ultra Sun*. It is not: Ultra Sun knows how to touch the meteorite beside
    Sophocles and has no way at all of producing a Deoxys to touch it with. `Availability`
    checked an evolution's earlier stage and a breeding parent and let a **form change** through
    unasked - the same bug Yannick reported about Ivysaur in Platinum, one record kind further
    on and missed when that one was fixed.
  - A form is not caught, it is changed into, so what it is changed *from* has to be gettable.
    Fixed, with three tests. **It moves 64 tiles in Ultra Sun alone** - 618 available became 554
    - and much more elsewhere: Emerald went from 28 available form tiles to 1, Ruby and Sapphire
    from 27 to 0, because neither catches an Unown or a Deoxys. And it keeps the half of the
    rule that makes it useful: bring a Deoxys in and its three formes become available, which is
    the whole point of an item that changes something.
  - One thing it still cannot see, written into the class rather than left to be rediscovered: a
    form change carries what it needs as a sentence - "fuse it with Lunala using the
    N-Lunarizer" - and nothing in the schema says the Lunala is a second Pokemon to be had
    first. So Ultra Sun counts Dawn Wings Necrozma, whose Necrozma it can catch and whose Lunala
    it cannot.
  - The published exe starts on the new dataset and stays up, no crash log. The data file was
    copied before the test and is byte-identical after it; every backup the app wrote during the
    run was removed and the four that were there before were left alone.
  - Step 8 for Ultra Sun and Ultra Moon: **282 forms each, 196 with a record**, and 151 form
    changes against the first pair's 148. The three that are new are the three these games are
    about.
  - **Necrozma is the reason this pair exists.** Colress hands over both fusion items on Mount
    Lanakila once Necrozma is caught, and which one a cartridge can use is decided by the box it
    came in: Dusk Mane needs a Solgaleo and Dawn Wings needs a Lunala, so each half can make one
    of them and has to trade for the other. Ultra Necrozma is not here and should not be - it
    lasts until the battle ends, and `is_battle_only` has kept that kind out since the table was
    written.
  - **The Partner Cap Pikachu is the second QR Code these games shipped with**, and it is
    Magearna's shape exactly: a picture published for each region, scanned on the 3DS's own
    camera, nothing at the other end to switch off. It is the only one of Ash's seven caps
    anybody can still get - the other six were serial codes in 2017 and are over.
  - The rest of the table is the first pair's, because the items did not move: the Griseous Orb
    and the Gracidea are still sold in the Hau'oli City mall, the DNA Splicers and the Prison
    Bottle still come from the same employee in Secret Lab A, Rotom's appliances are still in
    Kukui's basement. Only Silvally's memories moved, with Gladion: Wicke hands over all
    seventeen at Ancient Poni Path.
  - **Forty forms were removed from the dataset, and none of them should ever have been there.**
    Scatterbug and Spewpa each carry twenty patterns and Mothim carries three cloaks, and
    Bulbapedia settles all three in its own words: Scatterbug and Spewpa "each have 20 visually
    indistinct forms" whose only job is to decide which Vivillon they become, and a Mothim keeps
    the cloak of the Burmy it evolved from "though this is only shown in its internal data". A
    player with all twenty Scatterbug in a box could not tell them apart, and every one of them
    was a tile asking to be filled. `forms.py` now leaves out a third kind on purpose, beside
    the battle-only and held-item ones: **invisible**.
  - They were easy to miss because they arrived the day these two were registered - that is the
    version group the source stamps them with - so they looked like something the new games
    brought. The form table went from 329 to 289.
  - **The meteorite was missing for the third time.** `METEORITE` in `forms.py` is written out
    by hand because a version group cannot say it, and every pair since Omega Ruby has found it
    short: Omega Ruby, then Sun and Moon, now these two. Deoxys's three formes were absent from
    both halves. It is one meteorite, beside Sophocles in the Hokulani Observatory, and all four
    Alola cartridges walk past it.
  - Step 7 for Ultra Sun and Ultra Moon: **thirteen reasons per half - eleven exclusives and
    two nobody can produce** - and nineteen entries once `spread_unobtainable` has handed each
    line's reason down. Validation is at **0 errors**.
  - **Only three of the twenty-four were ever handed out, and that is the finding.** It is the
    exact opposite of what the first pair found. Sun and Moon's eighteen exclusives were covered
    six times over - a basket of Easter Eggs at Pokemon Centers, a Korean giveaway a month
    later, Lillie's own Alolan Vulpix, Kiawe's Turtonator - and **every one of those
    distributions says "S M" in its games column and means it**. By the time these two shipped a
    year on, the giveaways had moved on: a Drampa or an Alolan Sandshrew missing here stays
    missing. The one exception is a Pokemon Bank Hidden Ability giveaway in 2019 that covered
    all four cartridges, and it is why Oranguru and Passimian have a sentence and nine others do
    not.
  - The split itself is not the first pair's either. **The fossils are not on this list at all** -
    all four are revived at the Restoration Center on Route 8 in both halves, where Olivia
    stocked two per cartridge - and three pairs are exclusives these two invented: Electrike and
    Houndour, Baltoy and Golett, Skrelp and Clauncher.
  - **Marshadow and Zeraora were both given away to these two specifically.** Sun and Moon's
    Marshadow codes ran out in February 2018 and these two got their own, starting on the day
    they came out; Zeraora was **never offered to any other game at all** until Pokemon HOME
    handed out a Shiny one for a million victories, two generations later. The Fula City Zeraora
    is the only distribution in this dataset whose games column names one pair and nothing else.
  - **Two warnings are left, and they are the honest kind.** Dusk Lycanroc can only be got from
    a Rockruff with Own Tempo, and that Rockruff was a serial code handed to buyers between the
    launch day and 10 January 2018. The distribution is over, so there is no record to write -
    and **a form has nowhere to say so**: an `unobtainable_reason` lives on a dex entry, dex
    entries are species, and the form table has no field for one.
  - So the rule was taught to tell the two cases apart rather than to go quiet. It used to say
    "the generation they come from has not been built", which was written for a species from an
    unbuilt generation and was a plain lie about a form - a form is never in any dex, so it can
    never be "listed", and it fell into that bucket by accident. Ultra Sun was reporting that
    Generation 7 had not been built. It now says what is true: *only obtainable by evolving a
    form nothing in the dataset produces, and a form has no dex entry to carry a reason on*.
    Giving the form table that field is Phase 3's to weigh.
  - Coverage: **613 full, 165 partial, 10 missing, 19 unobtainable** per half.
  - Step 6 for Ultra Sun and Ultra Moon: **there is no sheet, and this time the source names
    these two by name.** `versions/generation-vii/ultra-sun-ultra-moon/25.png` is the url
    PokeAPI publishes for a Generation 7 Pikachu and it is still a 404; there is no `sun-moon`
    folder to 404 on at all. So both entities carry `sprite_set=None` explicitly rather than by
    omission, and the app draws the shared set - the documented fallback, as for the first pair.
  - Scraping the Archives instead turned out to be a bigger and stranger job than the Phase 3
    item guessed, so it now has one of its own: *Scrape Generation 7's sprites from the
    Bulbagarden Archives*.
  - Step 5 for Ultra Sun and Ultra Moon: **1471 ways to get something and 1470** - 868 wild
    slots, 407 evolutions, 166 gifts and statics, seven trades and 23 eggs. Coverage went from
    331 full to **618 of 807**, which is the most any game in this dataset fills by itself:
    Sun manages 510 of 802 and Omega Ruby 575 of 721.
  - **Not one of the traders is offering what they offered before.** Hila still stands on Route 2
    and still wants a Spearow, and hands over a Hawlucha where it was a Machop; Kihei still wants
    a Lillipup on Route 5 and gives a Noibat rather than a Bounsweet. Two of the first pair's
    places have no trader and three new ones do, and there are seven trades against six - which
    is why the four cartridges cannot share one table however alike the names look.
  - Two are worth reading twice. **Sill's Phantump becomes a Trevenant the moment it arrives**,
    which is what a traded Phantump does - recorded as what is handed over, the way Sinnoh's
    Haunter-into-Gengar and this region's own Alolan Graveler-into-Golem already were. And
    **Kumu's Shellos is the West Sea one**, where everything in Alola's water is East Sea: that
    trade is not a shortcut to something in the grass, it is the only West Sea Shellos these
    games have. It is the far side of a finding step 8 made about Sun and Moon and could not act
    on.
  - `USUM_VERSION_GROUP` is its own constant beside `ALOLA_VERSION_GROUP`, because a rule is
    stamped with the group it started in and a game is only allowed the groups at or before its
    own. Handing these two Sun and Moon's group would have quietly refused them every rule that
    arrived with their own - which is two: Poipole into Naganadel, and Rockruff into a Dusk
    Lycanroc.
  - **Naganadel dropped off the error list on its own**, which is what step 5 was for: Poipole
    is Soliera's or Dulse's gift and Naganadel is what it becomes. Marshadow and Zeraora are
    all that is left, and both are step 7's.
  - **One new warning, and it is right**: Dusk Lycanroc can only be got from a Rockruff with Own
    Tempo, and nothing in the dataset produces one. That Rockruff was a serial code handed to
    early buyers over the winter of 2017, so it is step 7's answer - though the warning's own
    wording does not fit the case, since it says "the generation they come from has not been
    built" and the generation is built. Worth revisiting when step 7 writes the reason.
  - Step 4 for Ultra Sun and Ultra Moon: **166 gifts and statics each**, against the first
    pair's 90. Nineteen of Ultra Sun's and twenty of Ultra Moon's are the other half's, which is
    a version exclusive on a scale nothing in this dataset has tried before - **nine of them are
    pairs of legendaries**: Ho-Oh and Lugia, Dialga and Palkia, Groudon and Kyogre, Reshiram and
    Zekrom, Xerneas and Yveltal, Raikou and Entei, Latios and Latias, Tornadus and Thundurus,
    Heatran and Regigigas.
  - **The Ultra Warp Ride is the single largest thing any game here does for a living dex.**
    Ride Solgaleo or Lunala through Ultra Space and dive into a warp hole: there are four tiers
    of them, the farthest flights find the rarest, and one with a flower-shaped aura is
    guaranteed to hold a legendary. Nearly every legendary of the six generations before Alola
    is at the end of one, and most of them had been reachable only by carrying one across five
    transfers from the cartridge it was caught on.
  - Five of them want company first - Giratina wants Dialga and Palkia in the party, Rayquaza
    wants Groudon and Kyogre, Suicune wants Raikou and Entei, Kyurem wants Reshiram and Zekrom,
    Landorus wants Tornadus and Thundurus - which is the oldest habit in the series, the one the
    Regis had in Hoenn, turned into the shape of a whole postgame.
  - **The source files the Ultra Space Wilds twice and the two copies are not equal.** Once as
    their own place, holding the legendaries *and* the twenty ordinary species that live there,
    with no conditions; and once under Ultra Space, holding only the legendaries but carrying
    the in-party conditions. Keeping either one alone loses something, so the fuller place is
    kept and those five conditions are written out by hand. It is Unova's Friday Musharna again,
    in the Dreamyard and in the Dreamyard basement.
  - **A gift can name a form now**, and Samson Oak is why. He hands out Totem-sized Pokemon on
    Heahea Beach for Totem Stickers, and the source files every one of them under the ordinary
    species - which is the one thing a Totem-sized Gumshoos is not, since a plain one is caught
    in the grass on Route 1. `GiftDetail` gained a `form`, and the six per half land on
    `gumshoos-totem`, `raticate-totem-alola` and the rest.
  - That also answers something step 8 for Sun and Moon had to leave open. Those two have Totem
    Pokemon at their trial sites, a Totem is a battle rather than a catch, and all seven of
    their Totem forms were left with no way at all. **This is where they come from**, and the
    first pair can only be handed one over the link. Mimikyu is in both halves here, the sole
    exception among the twelve.
  - Nearly every ordinary gift moved. Kukui hands the starters over on Route 1 where Hala did it
    at the festival in Iki Town; Wicke hands over the Type: Null at Ancient Poni Path because
    Gladion has left Alola for the whole of this story; the fossils are revived at a Restoration
    Center on Route 8 instead of bought from Olivia, **and all four are in both halves**, which
    is the one place these two are kinder than the first pair. Necrozma waits in Mount
    Lanakila's crater rather than in Ten Carat Hill. Poipole is handed over in the Ultra
    Megalopolis by Soliera in one half and Dulse in the other.
  - Six conditions had no wording and have one now: the three in-party trios, Olivia's grand
    trial, and the Magearna QR Code - which **the source has a row for in these two and had none
    at all for Sun and Moon**, where it had to be written by hand at step 7. Its phrase is
    worded as a state rather than an instruction, because it is never the only condition on the
    row and "After entering the Hall of Fame and scan the QR Code" is two sentences colliding.
  - Validation is down to six errors from eight: Naganadel, which is step 5's, and Marshadow and
    Zeraora, which are step 7's. Poipole dropped off on its own. Coverage is 331 full, 463
    partial, 13 missing for each half.
  - Step 3 for Ultra Sun and Ultra Moon: **868 wild slots and 866**, against the first pair's
    708. These are not Sun and Moon's tables with a few rows added - Route 2 alone has eighteen
    rows for the older pair and thirty-one for this one - and SOS calls went from 133 to 197,
    which is the generation's own mechanic being leaned on harder the second time round.
  - **Three places the first pair's grass never had**: Dividing Peak Tunnel, Sandy Cave and
    Ula'ula Beach. 59 places against Sun's 59, but not the same 59.
  - **Blacephalon in Ultra Sun and Stakataka in Ultra Moon**, both standing in Poni Grove at
    level 60 - a version exclusive, and the first Ultra Beasts in this dataset that are walked
    into rather than hunted. Sun and Moon's four were statics on Looker's errand.
  - 94 records carry an hour, 47 by day and 47 by night, and 103 of the 117 ambushes say which
    of the seven terrains they are. Both come from `alolatables.py`, which needed one change:
    **both pairs' tables are on the same page and a two-letter column is all that separates
    them.** It read `("S", "M")` and now takes which pair to read - worked out from the
    cartridge rather than passed in, because there is exactly one right answer per game and
    reading the wrong one would quietly give a game the other pair's hours.
  - `alola.acquisition_methods` became `sinnoh.acquisition_methods`'s shape: the four cartridges
    share every piece of machinery and not one of the tables behind it, so a game brings what it
    knows and **a table left out is a step that has not been gathered yet**. That is what lets
    these two arrive with encounters and nothing else, the way the first pair did. `reach` is a
    required argument rather than a constant now, because this is the first region whose two
    pairs disagree about how far a living dex goes: 802 against 807.
  - Sun and Moon came out of that refactor byte-identical - 1362 records and 1361, the same
    counts entry for entry - which was checked rather than assumed.
  - **Validation is at eight errors, four per half, and every one of them is named**: Poipole
    and Naganadel, which are step 4's and step 5's, and Marshadow and Zeraora, which are step
    7's. The blanket "encounters have not been gathered yet" is gone, which is the thing step 3
    was for. Stakataka and Blacephalon dropped off the list on their own, because each half
    covers the other's.
  - Step 2 for Ultra Sun and Ultra Moon: **403 entries each, Rowlet to Zeraora**, and the same
    list for both halves as every pair in this dataset shows.
  - **Only 23 of Sun and Moon's 302 numbers still mean the same thing.** The hundred and one new
    entries were not added to the end, they were slotted in where they belong and nothing was
    taken away, so the two lists part company at #024 - Pichu in the older, Buneary in this one
    - and 279 of the older numbers point at something else here. That is Johto's situation
    rather than Platinum's, which kept Diamond's 151 and put four after them so every shared
    number went on meaning what it always had. It is why `SM_DEX` and `USUM_DEX` have always
    been separate constants and why neither is ever called "the Alola dex".
  - The five the sequels introduced sit at Alola #261 and #262 for Poipole and Naganadel, #392
    and #393 for Stakataka and Blacephalon, and #403 for Zeraora - scattered through, not piled
    at the end, which is the same fact seen from the other side.
  - **Validation is red on purpose after this step, and clears at step 3.** A game with a dex
    and no way to fill any of it now trips `every-entry-has-a-method`, which is exactly what
    that rule was written for: its docstring says a game like that "is unfinished whatever else
    covers its species, and step 9 reads validation green as proof that it is finished". Step 1
    did not trip it because a game with no dex has nothing to fail; step 2 gives it 403 entries
    and no encounters, which is the state the rule names. Two errors, one per half, and nothing
    else.
  - Step 1 for Ultra Sun and Ultra Moon: **the transfer graph is closed again.** 125 routes and
    nothing held back - the four Sun and Moon spent a whole pair's worth of steps declaring into
    an empty space are real, and neither of those two files was edited to light them. It has
    been true once before, when Bank and HOME arrived, and it stopped being true the moment
    Generation 7 opened. Let's Go will break it again.
  - Fourteen new routes: six trades between the four Alola cartridges where there had been one,
    and eight Bank edges where there had been four. **Four of the six carry 1 to 802 and two
    carry everything**, which is the cap `carried_between` was written for a pair ago: a cable
    that crosses between the pairs cannot hand over the five species the second pair introduced,
    and it refuses them in both directions because the older side holds none of them anyway.
  - **These two are the first second pair in the series to move the National Dex on.** A third
    version has never done it and nor have sequels: Emerald added nothing to Ruby and Sapphire's
    386, Platinum nothing to Diamond and Pearl's 493, Black 2 and White 2 nothing to Black and
    White's 649. Poipole, Naganadel, Stakataka, Blacephalon and Zeraora make this 807 against
    Sun and Moon's 802, and that gap is the whole reason the cap above exists.
  - **And the first release in the series that was one day everywhere.** X and Y managed one day
    in four regions, which this dataset called the end of the months a game used to spend out in
    Japan alone - and then Sun and Moon slipped back, with Europe five days behind. These two
    went out in eight regions on 17 November 2017, mainland China, Hong Kong and Taiwan among
    them, which none of the twenty-eight games before them here can say: Generation 7 is where
    the series gained Chinese at all. It is the first entity in this dataset with no "the
    Japanese date" to prefer.
  - Both entities carry an empty dex and no ways of getting anything, which is what step 1 is:
    coverage reads 0 full, 791 partial, 16 missing for each. The sixteen are the ten Mythicals
    nothing in this dataset produces, Marshadow, and the five these two introduced - and every
    one of the five is waiting for step 3 or step 4 rather than being a hole.
  - `alola.py` needed no changes at all. It was written for four cartridges when only two
    existed - `CARTRIDGES`, `ULTRA`, `carried_between`, `bank_carries` - and this step is the
    first test of whether that was foresight or decoration. Nothing in it had to move.

### Generation 8

_Done: all five. Sword and Shield in Galar, Brilliant Diamond and Shining Pearl in Sinnoh, and
Legends: Arceus in Hisui - which is the same ground as Sinnoh under an older name and shares
nothing else with it._

_The generation has no module of its own and now never will: `galar.py`, `bdsp.py` and
`legends_arceus.py` are three answers to every question, and the one thing all five have in
common is Pokemon HOME, which `home.py` has held since before any of them existed._

### Generation 9

_One of three. Legends: Z-A is Lumiose City on the Switch, and Scarlet and Violet are still to
come._

### Transfer-only nodes

- [x] **Pokémon Bank** (`bank`) - 2026-09-23
  - The first thing in this registry nobody plays: an entity with an empty dex, a release of
    `service`, no National Dex and no region at all, so that the routes through it have
    something to point at. `transfer-edges-connect-known-games` counts a node as known only when
    there is a game file for it, which is why a node needs an entity rather than a mention.
  - **Fourteen edges lit up and no game file was touched.** Ten Poké Transporter trips - one
    from each Virtual Console release and each Generation 5 cartridge - and the four Generation 6
    cartridges talking to Bank themselves. Every one of them had been declared at that game's
    step 1 and held back by the registry since, which is what holding them back was for. The
    graph went from 92 routes to 110.
  - **Bank hands back less than it takes, and that needed a shape the schema did not have.**
    Bulbapedia is plain about it: anything that has ever been in a Generation 7 game, or that
    came from a Generation 1 or 2 game, cannot be moved to the Generation 6 games. Both halves
    are the same fact from either end - X and Omega Ruby cannot read what those games write -
    and neither half is about a species. The same Charizard is taken or refused depending on
    which cartridge it was caught on three transfers ago.
  - So an edge now carries a `history` window beside its filter: the generations every game on
    the route so far must fall inside. Bank's withdrawals into Generation 6 carry 3 to 6. It is
    the first thing in this dataset that no record about a Pokémon could ever answer, and it is
    read against the route rather than against the tile.
  - Which made the deposit and the withdrawal two one-way edges rather than one both-ways edge.
    A both-ways edge says one thing about both directions and these two do not agree: Bank takes
    anything X holds and gives back only some of it.
  - **What it costs is the point.** Without the window the dataset would say a Pokémon caught in
    a Virtual Console Red reaches X in two moves. It does not, and that is exactly the route a
    player would try. With it, the six Virtual Console releases gain a node and no new
    destination at all - they are waiting for Generation 7, which is the only thing Bank will
    hand them to.
  - The window is checked even when no species was named. The linked-game picker deliberately
    ignores species filters, because a game can be a good feeder and still refuse some of what
    lives in it; this is not that kind of no. `ReachableFrom` had to become a forward search from
    each candidate for the same reason - where a route has been is only knowable going forwards -
    and the search state is two numbers, the earliest and latest generation behind it, which
    keeps it small enough to walk exhaustively.
  - A node of unknown generation is refused by a window rather than waved through, which is the
    stance `nationalDexRange` already takes towards a species it cannot number.
  - **Not in either picker.** Bank is not a main game - there is nothing to fill in it - and not
    a linked one either: a linked game is somewhere a player can get something, and nothing was
    ever caught in Bank. `NewCollection` lists games and leaves the services out. It still does
    all its work, in the routes the games it hides are offered by: X's linked-game list now holds
    every Generation 3, 4 and 5 game, "via Pal Park, then the Poké Transfer, then Poké
    Transporter, then Pokémon Bank" and shorter.
  - Two checks were taught what a node is rather than left to report an empty game. A node has no
    cover to be missing, and four zeroes in the coverage report read like a game nobody has
    started.
  - The registry now knows which of its entries are not games, because it has to answer before
    any of them is built: the shared forms table asks PokéAPI about every id it holds, and
    PokéAPI has a version group for Omega Ruby and has never heard of Pokémon Bank. The first
    full build after registering Bank failed exactly there.
  - **One thing was wrong and is now fixed.** `form_table` handed its forms back in National Dex
    order and `write_forms` wrote them sorted by id, so the table a full build held in memory and
    the table a single-game build read off disk were the same list in two different orders - and
    a game writes its form records in the order it is given them. Sixteen of the twenty-four game
    files had form records at all, and which order each one was in recorded nothing but which
    command had last been run on it. The table is sorted at the source now, to match what is
    written, and the sixteen were normalised to it while HOME was built: 4018 lines moved and not
    one changed.
  - The way out is declared here and waiting: `bank -> home`, one way, and the last held-back
    edge in the dataset. It is also the last door out of every 3DS game here - the service was
    given an end date of 26 February 2027, announced in August 2026, and after that nothing moves
    at all.
  - Validation green on all 11 rules for the whole dataset.
  - **Smoke test on the published exe**, on a collection called "Bank smoke" with X as the main
    game. The main-game picker shows 24 cards over six generations and no Bank, which is the
    dataset's 25 entries minus the node.
  - The linked-game list is the thing to look at. It used to hold three cards, "via trading", and
    it now holds seventeen and **begins at Generation 3**: five Generation 3 cartridges "via Pal
    Park, then the Poké Transfer, then Poké Transporter, then Pokémon Bank", five Generation 4
    "via the Poké Transfer, then Poké Transporter, then Pokémon Bank", four Generation 5 "via
    Poké Transporter, then Pokémon Bank", and the three other Generation 6 games "via trading".
    Generations 1 and 2 are not on it at all, which is the window doing exactly the work it was
    written for: those six releases reach Bank and stop there.
  - Two popups read closely, with Ruby and Black linked. **Reshiram** shows N's Castle at level
    50 "During the last battle of the story" and under it "Then to X: Poké Transporter, then
    Pokémon Bank", with three other ways that are that route with a trade on one end or both.
    **Groudon** shows the Cave of Origin at level 45 and "Then to X: Pal Park, then the Poké
    Transfer, then Poké Transporter, then Pokémon Bank" - four mechanisms, five games and a
    service, twelve years of hardware, and none of it written anywhere but in the edges.
  - Marking Groudon caught in X moved the counter to "1 of 746" and wrote the data file. The
    user's settings were copied out first and restored byte for byte - same checksum as the
    backup - and their data file was untouched: same checksum, timestamp and length afterwards as
    before. The test ran against a data file in the scratchpad and only the instance it started
    was stopped.

- [x] **Pokémon HOME** (`home`) - 2026-09-23
  - The second node and the last one, and the smallest entry in this file for the amount it
    settles: the same shape Bank has - empty dex, `service`, no region - and registering it lit
    `bank -> home`, which Bank declared at its own step and which had been the last held-back
    route in the dataset. **Nothing is waiting now.** Every route any of the twenty-six entries
    declares has both of its ends here, which has not been true since the dataset held one game.
  - Released everywhere on one day, 12 February 2020, on phones and on the Switch at once. This
    dataset keeps Japanese dates because nearly everything in it reached Japan months early;
    HOME had no such date to be first.
  - It declares no route of its own, because nothing leaves HOME that is not a game's own
    business - the same division Bank uses, where the Generation 6 cartridges declare their side
    and Bank only declares its way out. What it leaves for those games is `home_edges`: a deposit
    that takes anything the game can hold, and a withdrawal that hands back only what that game's
    own Pokedex lists.
  - **And there the split into two one-way edges stopped being a preference and became the only
    thing that works.** A both-ways edge carries one filter in both directions, and
    `presentInTargetDex` asks whether the game being transferred *into* lists the species. Read
    backwards it asks HOME, whose dex is empty by definition, so a single both-ways edge would
    have refused every deposit ever made. Both fixtures in the repo had that edge as both-ways,
    and the C# one hid it by giving HOME a dex of three species. Both are two edges now and a
    test names the trap rather than leaving the next person to find it.
  - **Three Switch pairs deliberately do not get `home_edges`**, written into the module so
    nobody reaches for it out of habit. Let's Go only takes back a Pokemon that started in Let's
    Go - and anything that came in from Bank or from GO was converted to Sword and Shield's
    format on the way and can never enter it at all, which is a set no filter here can name, not
    a species and not a generation. Legends: Z-A takes Pokemon in and returns nothing to anything
    older. And Pokemon GO and the Switch releases of FireRed and LeafGreen send one way into HOME
    and are not games this dataset holds; both now have a line in Phase 3.
  - Pokemon Champions is not an edge at all. A Pokemon *visiting* Champions never leaves HOME -
    it is greyed out in the boxes and cannot be moved, traded or released while it is away - so
    there is nothing to draw.
  - **What the two nodes mean together**, which is the sentence this phase existed for: Bank is
    where the cartridge era ends and HOME is where it becomes unreachable. A Pokemon goes into
    HOME from Bank one way, and Bank itself shuts on 26 February 2027. After that a living dex
    kept on a Switch and a living dex kept on a 3DS are two collections with nothing between
    them, and this graph says so without anyone writing the sentence into it.
  - Validation green on all 11 rules for the whole dataset; 111 routes, 0 held back. 495
    pipeline tests and 248 app tests.
  - Checked on the published exe: the main-game picker still ends at Generation 6 with four
    cards and 24 in all, so both nodes stay out of it although the dataset now holds 26 entries.
    Settings restored byte for byte and the user's data file untouched, same as before.

- [x] **Let's Go, Pikachu!** (`lets-go-pikachu`, gen 7, pair partner: Let's Go, Eevee!) - 2026-09-24
  - [x] 1 Entity + edges - 2026-09-24
  - [x] 2 Dex list - 2026-09-24
  - [x] 3 Wild - 2026-09-24
  - [x] 4 Gifts & statics - 2026-09-24
  - [x] 5 Trades & evolutions - 2026-09-24
  - [x] 6 Sprites - 2026-09-24
  - [x] 7 Events - 2026-09-24
  - [x] 8 Alternate forms - 2026-09-24
  - [x] 9 Validate + smoke test - 2026-09-24
- [x] **Let's Go, Eevee!** (`lets-go-eevee`, gen 7, pair partner: Let's Go, Pikachu!) - 2026-09-24
  - [x] 1 Entity + edges - 2026-09-24
  - [x] 2 Dex list - 2026-09-24
  - [x] 3 Wild - 2026-09-24
  - [x] 4 Gifts & statics - 2026-09-24
  - [x] 5 Trades & evolutions - 2026-09-24
  - [x] 6 Sprites - 2026-09-24
  - [x] 7 Events - 2026-09-24
  - [x] 8 Alternate forms - 2026-09-24
  - [x] 9 Validate + smoke test - 2026-09-24
  - Step 9 for both: **validation green on all 11 rules, and a collection made through the
    wizard on the published exe.** 139 full, 0 partial, 0 missing and 14 explained per half; the
    two warnings left in the report are Ultra Sun's and Ultra Moon's Own Tempo Rockruff, which
    belong to the four cartridges rather than to these two. 593 pipeline tests and 257 app tests.
  - **"Kanto on the Switch": Let's Go, Pikachu! as main game, and the linked-games step offered
    exactly one card - Let's Go, Eevee!, "via trading".** That is the graph answering for itself:
    no Bank, no Alola cartridge, nothing that reaches HOME can send into these two, and step 1's
    three routes are visible to a player as one choice.
  - The grid draws **0 of 191** with regional, functional and gender forms switched on: 153
    species, 14 Alolan forms, 23 female halves and the partner, every tile off
    `generation-vii/lets-go` and not one of them falling back to another generation's picture.
    The tiles read `#019 Rattata`, `#019 Rattata (Alola)`, `#019 Rattata (Female)`, and `#025
    Pikachu (Partner)` sits beside the ordinary one.
  - Detail popups: the Alolan Rattata shows **Dark / Normal** - the form's own typing - and two
    in-game trades, Tatianna in the Cerulean City Pokemon Center in each half, the Eevee one
    followed by "Then to Let's Go, Pikachu!: trading". Meltan shows no ways at all and the GO
    Park reason underneath, ending in the Chinese distribution step 7 found.
  - The write path was exercised: marking the Alolan Rattata caught greened the tile and moved
    the counter to **1 of 191**, and the record landed in the data file with today's date. The
    user's settings were copied out first and restored byte for byte - same sha256 - and their
    own data file was never opened: the test pointed the app at a scratch file, which is where
    the collection and the record are.
  - Run twice over, once per half, through the app's own wizard, dex builder, sprite chain and
    store rather than only through the window: both halves build the same 191 lines and offer
    each other and nothing else.
  - Step 8 for both: **38 forms each, written out by hand, and the eight traders step 5 had to
    leave.** 23 gender forms, 14 Alolan and one partner per half; 42 more pictures off the same
    `7p` sheet, which takes that folder to 195 files and 13 MB.
  - **The fourteen Alolan forms each half has are the eight traders' doing**, and the four that
    differ are the two traders who ask for a different Pokemon per cartridge - the Camper in
    Celadon City and the Punk Guy on Cinnabar Island. What those eight hand over, and whatever
    it evolves into, is the whole of what either half can produce. Everything else Alolan comes
    through the GO Park or from another player, and a form has no dex entry to carry a reason
    on, so it is left out: a form the table leaves out is a tile that is not drawn, and a form
    it invents is a tile nobody can fill.
  - **Mega Evolution is not step 8's problem, and that was already decided.** These games have
    it, and in their own way: thirteen of the 153 Mega Evolve into fifteen Megas, and because
    there are no held items here the player only needs the stone in the bag. No Mega is in this
    dataset at all - `forms.py` refuses `is_mega` and `is_battle_only` along with it, because a
    Mega reverts when the battle ends and a living dex is about what a box can hold. The same
    sentence `gen7sprites.py` writes about Ultra Necrozma.
  - **Two ways that start from different forms are two ways**, which is the reader's rule that
    was missing and the sharpest thing in the step. Generation 7 added a second Rattata rather
    than changing the first, and the source says so: the newer detail *requires*
    `rattata-alola` and produces `raticate-alola`, where the older requires nothing. Reading
    every Alolan detail as a replacement left the Let's Go pair unable to evolve a Kantonian
    Graveler into a Kantonian Golem - a hole that only appeared once this pair had the Alolan
    forms to be confused by. Fixed in `evolution_encounters`, which now groups ways by what goes
    in as well as what comes out, and **the same fix gave Sun, Moon, Ultra Sun and Ultra Moon
    seven records each they never had**: a Kantonian Rattata sent in through Bank has always
    become a Kantonian Raticate in Alola, and the dataset said it became an Alolan one.
  - **And three evolutions that depend on where you are standing**, named by hand because
    nothing in the data can say it: a Pikachu, a Cubone and an Exeggcute are one Pokemon each,
    their details require no Alolan form, and what the Thunder Stone, the level and the Leaf
    Stone make of them is decided by the region. In Kanto that is the Kantonian Raichu, Marowak
    and Exeggutor; the Alolan three are Psytrice's, Genmar's and Exemann's to trade. Bulbapedia
    agrees entry for entry - all three read "Trade" in their Alolan row for these games.
  - **The partner is a form now**, which it always was: PokeAPI calls them `pikachu-starter` and
    `eevee-starter`, stamps both with this pair's version group, and nothing in the dataset is
    newer - so the ordinary rule gave them no games at all and dropped them. The starter gift
    points at the form rather than at the species, because the wild Pikachu of Viridian Forest
    and the wild Eevee of Route 17 are ordinary ones and this is not. The table measures it as
    *functional* rather than cosmetic without being told to: a partner has higher base stats.
  - Eevee is drawn once on the Let's Go sheet and once on Alola's, so its female form falls back
    to the shared set in both - the same disagreement with PokeAPI that the Generation 7 scrape
    turned up, arriving a second time. The other twenty-two are drawn twice.
  - Step 7 for both: **three distributions in seven years, and not one of them was for these
    cartridges.** Every unobtainable entry in either half was checked against its own *In
    events* table - 22 version exclusives, Mew, Meltan and Melmetal - and exactly four rows came
    back marked `PE`.
  - **The international Let's Go games have had one Mystery Gift in their life, and it is not a
    distribution.** The Poke Ball Plus Mew: a serial code in an accessory, redeemable once per
    accessory ever manufactured, open since the day the games went on sale and never closed.
    Every other pair in this dataset has a list of events behind its unobtainable entries; these
    two have none at all. Step 7 usually turns "nothing can produce this" into "nothing you can
    play can, and here is what once did" - here it turned it into "and nothing ever did".
  - **The three that do exist belong to the mainland Chinese release**, which came out in
    September 2024 on the Tencent Switch, six years after these cartridges: the Chinese Release
    Commemoration Meltan, the Pokemon Day Melmetal, and - the odd one - a **Shiny Arbok for the
    Year of the Snake**, level 50 with an eight in every IV, handed out over a fortnight in
    January 2025. All three were passwords rather than serial codes, all three are once per save
    file, and all three are refused unless the save's origin language is Simplified Chinese.
  - **The Arbok is the only entry in either half whose reason is not its line's.** A reason
    normally spreads down an evolution line from the base that carries it, which is how Ekans
    answers for Arbok, Weepinbell and Victreebel. Here the distribution is for the Arbok and
    there has never been one for the Ekans, so the Arbok is written out and the spread leaves it
    alone - the first time in the dataset that step 7 has found an event for something other
    than the base of its line.
  - **And a correction to step 1, made by the same page.** `lets_go.py` said the mainland
    Chinese release "trades only with itself". It does not: Bulbapedia notes that an event
    Pokemon from those games shows its real met location once it is traded locally to an
    international copy, which describes a trade between the two releases in passing. That is
    what keeps these three reasons from being useless - there is a way across, and it runs
    through somebody else's Switch.
  - One more thing that release is worth: the Poke Ball Plus Mew stopped being redeemable there
    on 15 May 2026, when Nintendo Switch online services in mainland China shut down. On the
    cartridges this dataset holds it is still open, which is the difference the reason turns on.
  - Step 6 for both: **153 pictures, 9.1 MB, `generation-vii/lets-go`, and not one miss.** Off
    the Bulbagarden Archives' `7p` sheet in fourteen minutes, cropped at build time like Alola's.
    The app needed no change and the second half's build fetched nothing: the two share the
    folder, so Eevee's came free.
  - **PokeAPI does have a Let's Go folder, and it is the reason to look before assuming.** It
    holds animated GIFs of the models - 384 pixels square, thirty to seventy-five frames, three
    quarters of a megabyte to two megabytes each - and they are named `.gif` where every other
    set in that repository is `.png`, so the ordinary fetcher would have taken 153 404s and
    called the generation undrawn. A quarter of a gigabyte for a picture shown at 56 pixels.
    Taking frame 0 of each would work and would still be a pose out of an idle animation rather
    than the front-facing render the wiki keeps, so the Archives won the same argument twice.
  - **The third sheet stopped being a warning and became a folder.** `gen7sprites.py` has
    carried `7p` since the Alola scrape - written down only so nobody would mistake it for `7u`
    - and the whole of step 6 was letting a sheet be named instead of worked out from the
    number. One namer, two folders, and `ARCHIVES_SHEETS` says which sheet fills which: Alola's
    four cartridges split across two sheets at 802, and these two are one sheet from Bulbasaur
    to Melmetal - which matters, because Melmetal is 809 and the number rule would have asked
    Ultra Sun's sheet for it.
  - **Fourteen species answered only to `_m`** - Venusaur, Butterfree, Rattata, Raticate,
    Raichu, Zubat, Golbat, Gloom, Vileplume, Kadabra, Alakazam, Doduo, Dodrio and Hypno, the
    ones the sheet draws twice. The form table for these two deliberately says they have no
    forms until step 8, so nothing could say in advance which spelling to try; offering both
    turned that into fourteen wasted requests rather than fourteen holes. That is the design
    from the Alola scrape paying for itself in the case it was written for.
  - **These are the largest pictures in the dataset and they are still a tenth of what arrived.**
    The 800 pixel frame is nearly all air: cropped, a Meltan is 148 by 192 and a Moltres - the
    biggest of the 153 - is 730 across. Capping them at 256 pixels was measured and dropped: it
    saves a fifth of the folder and resamples every picture to do it, and PNG size here is
    detail rather than dimensions.
  - No change in the app, and the reason is a line written for Generation 6: the grid asks
    whether the main game's set starts with `generation-vi` to decide between nearest-neighbour
    and smooth scaling, and `generation-vii` starts with it too. A render of a model gets
    smoothed, which is what it wants.
  - Found while searching and left for step 8: the partner Pikachu is `Spr_7p_025P`, and `P` on
    the `7u` sheet is the Partner Cap Pikachu. The same code, two sheets, two different Pokemon.
  - Step 5 for both: **72 evolutions each, six version-exclusive lines apiece, and not one
    trade.** Coverage is **139 full, 0 partial, 0 missing, 14 explained** per half: every entry
    in this Pokedex is now either fillable here or carries a reason, which is the state step 9
    asks for.
  - **The newest way to evolve something is the newest way *this game* has**, and finding that
    out is most of the step. `evolution_encounters` took the newest version group a game is old
    enough for and stopped. That is right for Alola - a Thunder Stone there makes an Alolan
    Raichu and no longer a Kantonian one - and these two came out a year *after* Alola and are
    Kanto. So the pair was handed Alola's rule, the rule names a form their table has not got,
    the form reader refused it, and the answer was nothing at all: **no Raichu, Ninetales,
    Persian, Sandslash, Dugtrio, Raticate, Golem, Muk, Marowak or Exeggutor**, which is exactly
    the list of species Alola drew a second time. The reader now steps down an order whenever a
    whole one is refused for wanting a form the game lacks. Nothing else in the dataset moves:
    every game old enough to be refused a form's rule is already too old to be offered it, and
    fourteen games rebuilt to check said so.
  - **A game whose boxes hold a list can evolve something into what it cannot hold.** Every game
    before this pair holds everything up to its own National Dex number, so whatever a species
    in the living dex evolves into was in the living dex too. These two hold 153 and nothing
    else, and their Eevee was quietly recorded as producing an Espeon - along with nineteen more
    that no box here can take, Crobat and Blissey and Magnezone among them. Twenty records that
    the rest of the dataset would have read as "obtainable somewhere".
  - **And one the chain says and the game cannot do**: Meltan becomes Melmetal on 400 Meltan
    Candy, and that happens in Pokemon GO. Named and refused in the game's own file, the way a
    gift the source files under the wrong version is. Nothing was broken by it, which is the
    part worth keeping: Meltan is unobtainable here, so the Melmetal that evolved from it was
    unreachable and `no-evolution-dead-ends` had nothing to say. A record can be wrong without
    failing anything.
  - **Six lines each way, which is the smallest split a Kanto pair has had** - Red and Blue
    divide eleven. Sandshrew, Oddish, Mankey, Growlithe, Grimer and Scyther are Pikachu's;
    Ekans, Vulpix, Meowth, Bellsprout, Koffing and Pinsir are Eevee's. Eleven species apiece
    once the evolutions are counted, and only the six bases are written down: the pipeline
    already spreads a reason down a line.
  - The reason is this pair's own rather than `exclusives.only_on`, which would have said "only
    in Generation 7" twice wrongly: Ekans is in Alola as well, and no Alola cartridge can reach
    these two anyway. **The cable between the halves is the whole of what a player can be told
    to do** - which is the same sentence `lets_go.py` has been making about the graph since step
    1, arriving now on 132 dex entries.
  - **The step-1 guess about what "no mutually exclusive Pokemon" meant was wrong, and the real
    answer is better.** That note said it was because every version exclusive can be had from an
    NPC in the other half. It cannot - the traders hand over Alolan forms and nothing else.
    Bulbapedia's mutually-exclusive list simply has no Let's Go section, and what earns that is
    two things these games undid: **both Hitmons walk around on Victory Road as rare spawns**
    (step 3) and **both fossils are hidden in Cerulean Cave** (step 4). Mutually exclusive is
    about one save file, not about two cartridges. Version exclusives are alive and well here;
    the choices are what went.
  - **Not one trade, and that is step 5's answer rather than a table not gathered yet.** There
    are eight traders - seven Pokemon Centers and the Pokemon League lobby - and every one of
    them hands over an Alolan form; Bulbapedia calls them the only way to an Alolan form outside
    the GO Park or another player. A record whose target is a form cannot be written before the
    form table says which forms this game has, and `FORMS_NAMED_BY_THE_GAME` deliberately says
    these two have none until step 8 writes it out. So the eight are listed in `lets_go.py` and
    wait there. The cost is nothing a player can see: all eight targets are species this half
    already fills another way, making these the first in-game trades in the dataset that add no
    species to a living dex at all. They are also the first that can be repeated forever.
  - Step 4 for both: **20 gifts and statics each, one table for the two of them, and three
    entries neither half can produce.** Validation is green for the first time since this pair
    was written, and coverage is **117 full, 33 partial, 0 missing, 3 explained** per half - the
    33 are step 5's evolutions and trades.
  - **Kanto's three starters are not starters here**, which is the sharpest thing in the table.
    Bulbasaur, Charmander and Squirtle are not lined up in Oak's laboratory to be chosen
    between: they are three separate presents from three strangers in three towns, and what
    each one asks is how many species have been caught - 30, 50 and 60. All three can be had in
    one save, so the choice Red made in 1996 is gone along with the grass. Every other Kanto in
    this dataset marks them `STARTER` and says "pick one of the three; the other two take a
    trade". The partner is the starter here, and it is the one Pokemon in either half that
    leaves by no route at all.
  - **One gift table for both halves, which no pair before them could have had.** The only two
    rows that are not in both are the Persian and the Arcanine, and those are one errand
    outside one building with a different animal at the end of it: catch five Growlithe in
    Pikachu, five Meowth in Eevee. That is what "the first core games with no mutually exclusive
    Pokemon" turns out to mean once it reaches the data, and the same answer came back for the
    unobtainable table - three entries, shared, and not a version exclusive among them.
  - **Four levels are the games' word against the source's, which is a first.** PokeAPI puts
    the Persian and the Arcanine at 32, the Porygon at 36 and the fake-item-ball Electrode at
    43; Bulbapedia's list of these games' event Pokemon and Serebii's gift page agree with each
    other against it at 16, 16, 34 and 42. The Electrode says where those numbers likely came
    from: 43 is what the Electrode in the same room of the same Power Plant was in Red and Blue,
    and Bulbapedia's Power Plant page prints the two side by side. A game's own table has always
    been able to correct the wording of a row; `GiftDetail.level` is new, and nothing else in
    the dataset sets it.
  - **The Lapras PokeAPI has no row for**, in either half: the Silph Co. employee has handed one
    over in that room since Red, and PokeAPI's tables simply stop at this version. Written down
    and cited like Crystal's Tyrogue. It closes no hole - step 3 found Lapras swimming off two
    sea routes - and leaving it out would have said this Kanto stopped doing something it has
    done for twenty-two years.
  - **The first Kanto where the fossil turned down is not lost for good.** Red, Blue, Yellow,
    FireRed and LeafGreen all keep the one left behind at the end of Mt. Moon; this pair hides
    more of both, and more Old Amber, in Cerulean Cave as ordinary ground items. Both halves of
    a choice that was permanent for twenty-two years now fill a living dex.
  - **The GO Park is a reason rather than a record, which is the opposite of what step 1
    guessed.** `lets_go.py` said the park would be "the same shape as an egg from an NPC"
    because Pokemon GO is not a game in this dataset. It is not that shape: it is the Pokemon
    Dream Radar's problem - a source that is not a game, sending one way into two cartridges and
    nowhere else - and Black 2 and White 2 state that as a reason on the entry while the Phase 3
    item below works out what shape such a thing should have. That item asks in as many words
    for GO and the Radar to be decided together rather than one at a time, and a GO Park shaped
    acquisition invented here would have decided it alone, for two species, in a schema the app
    draws pictures from. So Meltan and Melmetal carry a reason that says exactly what to do, and
    nothing in the dataset claims Kanto contains a Meltan.
  - **And a third entry nothing here produces: Mew, which is behind hardware rather than behind
    a date.** The only one in these games is the Mystery Gift redeemed with the serial code
    inside a Poke Ball Plus - one per accessory ever manufactured, still sold, open since the
    day the games went on sale. Not a distribution that ended, which is the distinction step 7
    exists to draw, so step 7 looks at this wording again beside the rest of the events.
  - No eggs, and that is one of the five things step 4 goes looking for answered with nothing:
    these are the first core games since Gold and Silver with no breeding at all, so there is no
    egg table to leave out and nothing in this Pokedex hatches.
  - Step 3 for both: **666 wild slots each, 112 species, 35 places, and not one of them is
    grass.** These two have no encounter table to walk into and no random battle at all: every
    wild Pokemon is standing, swimming or flying where the player can see it, and an encounter
    starts by touching that one. The whole vocabulary the twenty-eight games before them share
    - tall grass, a rod, a Repel, a roll when the battle starts - is gone.
  - So `EncounterMethod` gains three, and three rather than one because they are three places
    to look: **`overworld`, `overworldWater` and `overworldFlying`**. The sky is not a rarer
    kind of ground - a Charizard passes overhead and is gone, and it is the only place a wild
    Charizard or Dragonite exists at all. Mapping these onto `walk` and `surf` would have said
    a player pushes into grass and hopes, which is the one thing these games never ask.
  - **Rarity is not a method, and here it could not be a number either.** The source keeps a
    second table beside each of the three for what turns up far less often - Chansey on
    seventeen routes, Lapras on two sea routes, Snorlax in Cerulean Cave - and every slot in
    these games is listed at 100%, because what a player meets is decided when the overworld is
    populated rather than when a battle starts. So the chance column cannot carry it and the
    requirement does: 174 of the 666 say "a rare spawn". Kalos's flower patches got the same
    call.
  - **The only place in this dataset where catching a Legendary Pokemon puts it back in the
    wild.** Each of the three birds has one static - the source puts Articuno on Seafoam
    Islands B4F, Zapdos in the Power Plant and Moltres on Victory Road 2F, which is not where
    FireRed kept them - and once that one is caught the same bird starts flying over twenty-four
    routes as a rare spawn. That is how a player gets a second; every other game in the series
    has exactly one. Three new condition wordings for it.
  - **Not one slot in either game carries a time of day**, and that is right rather than
    missing: Bulbapedia lists these as the first core games without a day-and-night cycle since
    Diamond and Pearl re-introduced it. 111 of Sun's 708 slots carry one.
  - The halves split 11 species each way in their grass - Oddish, Growlithe, Sandshrew, Scyther
    and seven more against Bellsprout, Vulpix, Meowth, Pinsir and seven more - which is the
    ordinary shape and is about to stop being it: step 5 has to check whether every one of them
    is also handed over by an NPC in the other half, which is what "the first core games with no
    mutually exclusive Pokemon" would mean.
  - Fixed while here: a method's sentence and a condition's were joined with a bare "and", so
    Kalos has been reading "Out of a bin and In a bin, on a Thursday" since it was built. They
    go through the same joiner a list of conditions does now, which lowers the second one in.
    Ten lines in X and ten in Y.
  - Coverage is **112 full, 39 partial, 2 missing** per half, and validation is down to the two
    errors that are the point: Meltan and Melmetal are in the dex at #152 and #153 and no game
    in this dataset can produce either. That is step 4's GO Park to answer.
  - One thing left open by the site rather than by the work: Bulbapedia started returning 403 to
    this pipeline partway through the step, so the wording of the rare-spawn sentence and the
    birds' was written from PokeAPI's own tables and the place names in them. Worth a second
    look when the wiki lets us in again.
  - Step 2 for both: **153 entries each, and the first 151 of them are Kanto's, unchanged.**
    Bulbasaur #001 to Mew #151 in the order they have been in since 1996, with Meltan at #152
    and Melmetal at #153. Platinum's situation rather than Johto's - every number these games
    share with Red or FireRed means exactly what it always meant - and the opposite of what
    Ultra Sun did to Sun, which parted company at #024.
  - **The two at the end are the strangest entries in the dataset so far.** Meltan is the only
    species a Generation 7 game introduced that is in no Alola dex, and it sits in a Pokedex
    that is otherwise Generation 1 from end to end. Neither of the two can be caught in Kanto:
    Meltan comes out of a Mystery Box in Pokemon GO and arrives through the GO Park, and
    Melmetal is what 400 Meltan Candy makes of one - in GO, not here. Step 4 has to answer
    what that means for these two lines.
  - And the validator noticed before anybody asked it to: **2 of the 153 have no source
    anywhere in the dataset**, which has not been true of any entry since Red was written. The
    other 151 are all covered by other games, so the coverage reads 0 full, 151 partial, 2
    missing per half - the 0 being step 3, which has not run.
  - Validation is **2 errors on purpose**, one per half: `every-entry-has-a-method` reports that
    a game with a dex and no encounters has not been worked on yet rather than that it has
    gaps. That rule was written for exactly this state - see what it says about Red - and the
    errors go away when step 3 does.
  - No forms on any entry, which is an answer rather than a gap: the Pokedex here has 153 lines
    and an Alolan Rattata does not get one of its own, exactly as in Sun and Moon. Which forms
    these two actually hold is step 8's, and until then `FORMS_NAMED_BY_THE_GAME` keeps the
    table quiet about them.
  - Step 1 for both, built as a pair: **five routes, and that is every route these two have.**
    The cable between the halves, and for each half a deposit into HOME and a withdrawal back
    out. No Bank, no cartridge, not even the generation they belong to - Bulbapedia calls them
    the first core games "to not be compatible with previous core series titles in any way
    since Pokemon Ruby and Sapphire, and as such, the first to be unable to trade with other
    core series games in their generation". The dataset is at 32 games and 130 routes, and
    nothing is held back.
  - `lets_go.py` is new and is the pair's module. Not `kanto.py`, which holds what is true of
    the place across the generations that have visited it - the overlap is real and steps 2 and
    3 will find it, and whatever turns out to be about Kanto moves there named `switch_`, the
    way FireRed's is named `gba_`. And not a `switch.py` either: Sword and Shield are on the
    same console and share none of this, so it would have to say "except in Let's Go" about
    every line, which is the sentence a `gen7.py` would have had to say about Alola.
  - **The withdrawal out of HOME is the first edge in this dataset that asks where a Pokemon
    started.** `home.py` wrote this down when it was built, before either game existed: only a
    Pokemon originally from Let's Go may be moved into Let's Go, and anything that reached HOME
    from Bank or the GO Transporter was converted to Sword and Shield's format on the way in
    and can never enter them. No filter could name that set - not a species, not a generation -
    so `OriginRequirement` is new beside `SpeciesFilter` and `HistoryWindow`, in the pipeline
    and in the app, with the pair as one origin: a Pokemon caught in Eevee may be withdrawn
    into Pikachu.
  - `TransferGraph` honours it, which is the half that matters. Without it, Red -> Bank -> HOME
    -> Let's Go would have been a real route and every tile in a Let's Go grid would have said
    "obtainable elsewhere, transfer it in". A route that begins at HOME is refused, because a
    Pokemon in a HOME box started somewhere and nothing here records where - the same answer a
    history window gives when it cannot see the whole route. Four tests.
  - **And registering two games put 578 wrong lines into the form table.** `from_group_on` has
    one rule - a form is in the games of the version group it arrived in and in every game
    after them - and it has held for twenty-eight games because all of them hold everything up
    to their own National Dex number. These two came out after Ultra Sun and hold 153 species,
    so every Deerling season, every Totem Pokemon and a Therian Landorus were listed as theirs.
    The rule is switched off for the pair, and step 8 will name their forms by hand: the table
    now says they have none, which is also untrue - an Alolan Rattata out of the GO Park is the
    point of the park - but it is the harmless direction, because a form left out is a tile
    that is not drawn and a form invented is a tile nobody can fill.
  - Two things found while reading that belong to later steps, written down so they are not
    found twice. **These are the first core games with no mutually exclusive Pokemon**: every
    version exclusive can also be had from an NPC in the other half, over and over, which is
    step 4's and step 5's to confirm and may leave `only_on` empty for the first time. And
    **there is no breeding at all** - the first core games since Gold and Silver without it -
    so step 5 has no day care to ask about.
  - The GO Park is deliberately not an edge. Pokemon GO sends Kanto's 151, their Alolan forms
    and Meltan one way into twenty parks where the Safari Zone used to be, and it is the only
    way anybody gets a Meltan; but GO is not a game this dataset holds, for the reasons
    `home.py` already gives, so what arrives through the park is step 4's answer about *these*
    games rather than a route between two entities - the same shape as an egg from an NPC.
  - The partner Pikachu and Eevee cannot be traded or put into HOME, which no starter before
    them could say. It is a fact about a form, so it waits for step 8 and is written down in
    both places that would otherwise have to rediscover it.

- [x] **Sword** (`sword`, gen 8, pair partner: Shield) — base + Isle of Armor + Crown Tundra - 2026-09-25
  - [x] 1 Entity + edges - 2026-09-25
  - [x] 2 Dex list - 2026-09-25
  - [x] 3 Wild - 2026-09-25
  - [x] 4 Gifts & statics - 2026-09-25
  - [x] 5 Trades & evolutions - 2026-09-25
  - [x] 6 Sprites - 2026-09-25
  - [x] 7 Events - 2026-09-25
  - [x] 8 Alternate forms - 2026-09-25
  - [x] 9 Validate + smoke test - 2026-09-25
- [x] **Shield** (`shield`, gen 8, pair partner: Sword) — base + Isle of Armor + Crown Tundra - 2026-09-25
  - [x] 1 Entity + edges - 2026-09-25
  - [x] 2 Dex list - 2026-09-25
  - [x] 3 Wild - 2026-09-25
  - [x] 4 Gifts & statics - 2026-09-25
  - [x] 5 Trades & evolutions - 2026-09-25
  - [x] 6 Sprites - 2026-09-25
  - [x] 7 Events - 2026-09-25
  - [x] 8 Alternate forms - 2026-09-25
  - [x] 9 Validate + smoke test - 2026-09-25
  - Step 9 for both: **validation green on all 11 rules with nothing at all to report**, and a
    collection made through the wizard on the published exe. Coverage is **768 full, 0 partial, 0
    missing and 53 explained** per half. 629 pipeline tests and 257 app tests.
  - **Zero findings for the whole dataset**, which has not happened before. Every report since
    Ultra Sun and Ultra Moon has carried the two Own Tempo Rockruff warnings, and step 8 answered
    them by accident: Galar puts one in a Max Raid den, so the thing those two games could only
    evolve is now produced somewhere.
  - **"Galar on a Switch": Sword as main game, and the linked-games step offered every playable
    game with the route it takes** - "via Poke Transporter, then Pokemon HOME" for Generation 5,
    "via Pokemon Bank, then Pokemon HOME" for Generations 6 and 7, "via Pokemon HOME" for Let's
    Go, and Shield "via trading". That is step 1's finding on screen: HOME is the only door
    Generation 8 has, and it is a door rather than a wall.
  - The grid draws **0 of 489** with regional, functional and gender forms switched on - 400
    species and 89 forms - and **553 of 553 with cosmetic ones on too**, which is the headless
    run. Every tile off `generation-viii/sword-shield` and not one falling back to another
    generation's picture. The tiles read `#031 Zigzagoon`, `#031 Zigzagoon (Galar)`, `#015
    Butterfree (Female)`, `#032 Linoone (Galar)`.
  - Detail popup on the Galarian Zigzagoon: **Dark / Normal** - the form's own typing - and four
    wild rows off Route 2, Route 3 and Bridge Field twice, at 2%, 38% and 35%, with "Before
    entering the Hall of Fame" on one Bridge Field row and "After" on the other. Every part of
    step 3 is legible there: the overworld method, the level band, the odds and the gate.
  - The write path was exercised: marking it caught greened the tile and moved the counter to **1
    of 489**, and the record landed in the data file as `zigzagoon` / `zigzagoon-galar`, status
    `inMainGame`, dated today. The user's settings were copied out first and restored byte for
    byte - same sha256, same 106 bytes - and their own data file was provably untouched: same
    sha256, same size, last written three quarters of an hour before the test began.
  - Run headless too, once per half, through the app's own wizard, dex builder, sprite chain and
    store: both halves build the same 553 lines, Gible is obtainable in Shield and explained in
    Sword, Sirfetch'd shows its raid *and* its evolution, and Galarian Slowking shows the
    evolution and the Galarica Wreath beside it.
  - One thing that is mine rather than the app's, written down so nobody chases it: **the GUI
    driver stopped landing clicks partway through**, so the last few steps were done by keyboard
    and the detail popup would not close at the end. Every input that did land was answered
    correctly and the write reached disk; it is the PowerShell harness losing the WebView, not
    the window.
  - Step 8 for both: **189 forms each - 29 regional, 59 sexes, 37 functional and 64 cosmetic -
    151 form-change records, and 87 more pictures off the same `8s` sheet**, which takes that
    folder to 670 files. `forms.json` goes from 291 to 379. 629 pipeline tests and 257 app tests,
    and validation is **11 rules, 0 errors, 0 warnings**.
  - **Before this step there was not one Galarian form in the dataset.** The version-group rule
    is off for this pair, so a form whose only games would be Sword and Shield came out with an
    empty list and was dropped from the table altogether. Step 8 had to write those rows, not
    switch them on - the same job `LETS_GO_FORMS` did for the partner Pikachu.
  - **Nothing in the table was remembered; each of the three parts was measured**, and the parts
    answer different kinds of form:
    - **what the games place, they place.** A form is a Pokemon in the source and a Pokemon has
      encounters, so asking each candidate for its own settles every form that is *met*: 45 of
      them, including Rotom's five appliances, both Basculin stripes, three of Pumpkaboo's four
      sizes, and the four Galarian forms the halves split.
    - **the sexes are the Generation 4 rule**, not the sheet. That was the correction: the sheet
      draws 54 of them apart and five it does not, and Croagunk has had a different throat since
      Diamond whatever the wiki got round to uploading. A sprite sheet is a witness about
      drawing.
    - **and the rest are written by hand because they are changed into**: two Galarica items,
      Type: Null's seventeen memories, Kubfu's second tower, the Reins of Unity's two riders,
      the Rotom Catalog from a house in Wyndon, Sinistea's mark under the base, and Alcremie's
      sixty-two faces, which are one spin with a different sweet in hand.
  - **No Gigantamax form is here and none had to be refused by hand.** The source marks them
    battle-only and `forms.py` refuses those wherever they come from - the same sentence that
    keeps every Mega out. A Gigantamax Pokemon reverts when the battle ends.
  - **The trap step 5 warned about was real and is shut.** Handing Galar its regional forms gains
    seven evolutions and loses three, so `raichu-alola`, `marowak-alola` and `exeggutor-alola`
    are refused by name: a Thunder Stone in Galar makes the Kantonian Raichu, and the Alolan one
    is what the Diglett Trainer hands over for forty of his hidden Diglett. **The same three
    Let's Go had to name**, which makes it a shape rather than an accident. Nothing else Alolan
    is refused - those lines name their own form at both ends, so an Alolan Meowth becomes an
    Alolan Persian here and a Kantonian one a Kantonian Persian.
  - **Sirfetch'd and Cursola have their evolutions back**, which is what the forms were blocking:
    the way in wants a Galarian Farfetch'd or Corsola and now the game has one. Checked rather
    than assumed, and the check found a third: **the Alolan Ninetales was missing from the table
    entirely.** Alolan Vulpix is a Diglett Trainer reward and so has a row of its own; the
    Ninetales is only ever evolved into, so nothing placed it anywhere and the "what do the games
    place" measurement could not see it. Five sexes and both Antique teacups were missing the
    same way.
  - **Two warnings that have been in every report since Ultra Sun and Ultra Moon are gone**, and
    nothing was done to them. `no-evolution-dead-ends` said Own Tempo Rockruff exists in those
    two only to become a Dusk Lycanroc and that nothing in the dataset produced one. Galar puts
    one in a den. The oldest complaint in the report was answered by a game that arrived six
    years later.
  - Seven evolution rules lost a version group from their name - `koffing-to-weezing-red-blue` is
    `koffing-to-weezing` now - because the Galarian variant is told apart by its form instead. It
    reaches thirty other game files and is the naming rule working as written: a suffix is for a
    pair that has nothing else to tell it apart by.
  - Two condition families needed wording, and both arrived with the forms: the Diglett
    Trainer's thresholds, which are a number and are read as one, and the Crown Tundra's three
    birds, which have to be seen fighting over the Dyna Tree before any of them can be met.
  - Left out on purpose and worth writing down: **East Sea Shellos and Gastrodon.** The source
    has no Pokemon for them to hang an encounter on and the wiki's page did not settle whether
    Galar has that sea, so they are not in the table. A form the table leaves out is a tile that
    is not drawn; a form it invents is a tile nobody can fill.
  - Step 7 for both: **71 species asked, 15 of the 53 explained entries now name a
    distribution, and validation is green** - 11 rules, 0 errors, and the only two warnings left
    are Ultra Sun's and Ultra Moon's Own Tempo Rockruff. Coverage is **768 full, 0 partial, 0
    missing and 53 explained** per half. 624 pipeline tests and 257 app tests.
  - Read the way the checklist says to: each species' own *In events* section, which is the only
    place that names the games a distribution was for. Two things had to be got right to trust
    it - the section also carries move tables, so only a table with "Distribution period" in its
    header counts, and a row only counts when its Games column names the half that *lacks* the
    species. A Sword-only raid does not answer a Shield player.
  - **Wild Area News is a way of distributing a Pokemon that only these games have**, and it is
    the strangest thing the step found. A den table is pushed to a Switch over the internet for a
    few days and then taken away; what is in the den while it lasts is in the game neither before
    nor after. Step 3 had already met its leftovers without knowing what they were - the
    `max-den-rarity-special` condition on a handful of Rolling Fields spawns.
  - **Four of those raids ran in the half that cannot catch the Pokemon at all, and they are
    exactly the four Regina's trades are split by.** A Shield player could raid a Galarian
    Farfetch'd and a Galarian Darumaka in the week of 19 to 25 March 2020; a Sword player a
    Galarian Ponyta and a Rapidash in the same week. Covered once each, for seven days, six years
    ago.
  - **Neither box legendary is strictly one cartridge's after all.** Lancer's Shiny Zacian ran in
    *Shield* and Arthur's Shiny Zamazenta ran in *Sword*, from October 2021, so each half was
    once handed the other's hero. Nothing else in this dataset has a version exclusive covered by
    a distribution aimed at the half that lacks it.
  - **Zarude closes the last hole.** The Isle of Armor's Mythical Pokemon is not in the grass,
    not in a den, not in the Max Lair and not handed over - the one entry of 821 that neither
    half produces - and it was given away six times between August 2020 and March 2022, twice
    over in three regions, once as itself and once as the Dada Zarude the film is about.
  - **Twenty-nine of the thirty-eight exclusives were never covered by anything**, which is the
    sparsest showing since Ultra Sun and Ultra Moon. A Sword player who wants a Gible, a Goomy or
    an Eiscue has one answer and it is the cable.
  - Four lines keep their own dates rather than inheriting the first stage's, because
    `reach.spread_unobtainable` would otherwise give a Zweilous Deino's week: Zweilous and
    Hydreigon had a raid of their own in October 2020, Pupitar and Tyranitar one in April and
    May 2020, and Rapidash two.
  - Step 6 for both: **583 of 584 species drawn, 44.6 MB, off the Bulbagarden Archives' `8s`
    sheet.** The pair shares one folder, `generation-viii/sword-shield`, which is the first
    Generation 8 set in the dataset. 620 pipeline tests and 257 app tests; the dataset is 120.7
    MB and the exe 287 MB.
  - **Looked before assuming, and PokeAPI has nothing again.** Its sprite repository stops having
    battle sprites after Generation 6; what it holds for Generation 8 is a folder of box icons
    and an empty entry for Brilliant Diamond. Same answer as Alola and Let's Go, for the same
    reason: these games have no battle sprite to hold.
  - **The sheet was read rather than guessed at**, which is the whole lesson of the `7p`/`7u`
    mix-up. `Spr_8s_810.png` has a description page and it says "Game model of #810 Grookey from
    Pokemon Sword and Shield", categorised under *Sword and Shield models*. That is the sheet.
  - **And not Pokemon HOME's artwork**, which the same wiki keeps beside it as `HOME0810.png`
    and which is a render of the same model. HOME is a service and these are the games; a
    picture filed under the games is the one a Galar tile should show, which is the argument
    `archives.py` already makes about Let's Go.
  - **`gen7sprites.py` is now `archives.py`.** The name was true while Alola and Let's Go were
    its only tenants. Sword and Shield are Generation 8 and read *exactly* the same rules -
    three digits, the same form codes, the same `_m` and `_f` - so the name was the only thing
    that had to change. The four sheets it knows are `7s`, `7u`, `7p` and `8s`.
  - What looked like holes were the sexed spellings: Magikarp and Eevee have no plain name on
    this sheet and both have `_m` and `_f`. **Eevee is drawn twice here where the Let's Go sheet
    drew it once**, so Galar's female Eevee will get a picture of its own at step 8 where Let's
    Go's had to fall back. 623 requests, 53 of them a 404, and every 404 was a species drawn
    twice rather than one drawn nowhere.
  - **One real hole, and the fallback is what it is for: Pinsir.** The wiki has no `8s` model for
    it under any spelling - checked all three - so its tile shows today's artwork instead. It is
    in the Isle of Armor list rather than the Galar one, so a collection opening on Galar's 400
    never sees it. That is the "documented fallback" the checklist asks for, doing its job.
  - The frame is 1080 pixels square where Let's Go's was 800, and the drawing inside runs from
    240 to 770 - the largest thing in this dataset. `cropped` takes the air off and the result
    averages **78 KB against Let's Go's 67**, so this is the same treatment at three times the
    species rather than a heavier one.
  - The app needed one line changed and it was a comment. The grid picks smooth scaling over
    nearest-neighbour on the prefix `generation-vi`, which is a prefix of `generation-vii/` and
    of `generation-viii/` and not of `generation-v/`. A trick written for Kalos took Alola and
    Let's Go for free and has now taken Galar the same way; only the sentence saying "both 3D
    generations" had to become three.
  - Step 5 for both: **18 trades and 291 evolutions each, and coverage closes to 768 full, 0
    partial, 52 explained and 1 missing** of 821. The one left is Zarude, which is step 7's
    question rather than this step's. 619 pipeline tests and 257 app tests.
  - **Twenty in-game traders, which is more than any game in this dataset has had.** Nine in the
    base game - two of them handing over a different Pokemon per cartridge - and eleven from
    Regina in the caves of the Isle of Armor.
  - **Regina's eleven are one idea, and it is an idea only Galar could have had:** she swaps a
    regional form for the original. Hand her the Galarian Meowth that Galar's grass is full of
    and she gives back the Kantonian one; the same for Ponyta, Farfetch'd, Corsola, Zigzagoon,
    Darumaka, Stunfisk, Weezing, Mr. Mime and Yamask, and for Exeggutor and Marowak it is the
    Alolan form that goes the other way. **She is the only way any of those eleven originals
    exists in these games.** `InGameTrade` carries what is wanted as a species, so which face of
    it is said in the requirement - the same place Unova's Basculin would have been answered if
    anybody had written down which stripe Kyle hands over.
  - **And four of her eleven are a version exclusive arriving through a trade counter**, which
    nothing before this pair has done. Galarian Farfetch'd and Darumaka are Sword's and Galarian
    Ponyta and Corsola are Shield's, so the half without the form can neither make the trade nor
    hold what it would have handed back.
  - **Kubfu evolves by a rule the source files under `the-isle-of-armor`, not `sword-shield`.**
    The expansions are version groups of their own and they carry real rules, so
    `evolution_encounters` takes several names now and reads every way up to the newest of them.
    Asking only about `sword-shield` left the one Pokemon the whole island is built around with
    no way to exist. Nothing from Legends: Arceus or Scarlet and Violet leaks in: those sit above
    the Crown Tundra in the source's own order and are refused by the same comparison.
  - **Nineteen exclusives each, which is the evenest split in the series**, and the table is
    written here rather than earlier because it is the answer to a question only the finished
    steps can be asked: which of the 584 does this half produce that the other does not. Grass,
    raids, gifts, statics, trades and evolutions all count. `reach.spread_unobtainable` then
    carries each reason down its line without being asked, so 19 species become **35 species over
    52 entries** - Lotad's reason reaching Lombre and Ludicolo, Gible's reaching Garchomp.
  - Four of the thirty-eight are somebody else's doing: **Sirfetch'd is Sword's because Galarian
    Farfetch'd is, and Cursola is Shield's because Galarian Corsola is.** Neither is split by
    anything in its own right.
  - The nursery produced **no eggs at all**, and that is the right answer rather than a gap: a
    day care is only asked for what nothing else in the game produces, and after 507 species of
    grass, 45 gifts and 18 trades there is nothing left for it to be asked about.
  - Two evolutions are waiting on step 8 and the build says so by name: **Sirfetch'd and Cursola
    have no evolution record**, because the way in needs a Galarian Farfetch'd or Corsola. Both
    are still reachable - they turn up in Max Raid dens - so nothing is missing from the grid,
    only from the reason underneath it.
  - **And step 8 will have to invent those two forms rather than switch them on**, which was
    worth measuring before assuming. `forms.json` holds 18 regional forms and **all 18 are
    Alolan: there is not one Galarian form in the table**. Switching the version-group rule off
    for this pair means a form whose only games would be Sword and Shield comes out with an
    empty list and is dropped from the table altogether, so `farfetchd-galar` and `corsola-galar`
    do not exist anywhere yet. Step 8 has to write them, the way `LETS_GO_FORMS` had to write
    `pikachu-starter`.
  - **A warning for that step, found the same way: handing Galar the Alolan forms is a trap.**
    Run the evolution reader over Sword with the eleven Alolan forms whose species it lists and
    it gains seven records - the Alolan Raichu, Ninetales, Persian, Sandslash, Dugtrio, Marowak
    and Exeggutor - **and loses three**, because a Thunder Stone, a level and a Leaf Stone stop
    making the Kantonian Raichu, Marowak and Exeggutor. That is exactly the regression Let's Go's
    step 8 hit, and the fix is the same shape: those three are region-dependent and Galar is not
    Alola. Six of the seven are real - the Diglett Trainer hands them over - so the forms are
    wanted and the three evolutions have to be refused by name.
  - One thing the day's date turned up rather than the step: **a full build now re-dates 3,014
    hand-written citations** because they carry `date.today()`. That is the Phase 3 item about a
    citation carrying the day a human read the page, arriving on schedule. The re-dating was
    kept out of this step's diff by hand.
  - Step 4 for both: **45 records each - 3 first partners, 4 fossils, 10 presents and 28 things
    standing in one spot.** Coverage is **745 full, 68 partial and 8 missing** of Sword's 821
    entries, up from 723/78/20. 614 pipeline tests and 257 app tests. One table for the pair,
    because the two halves hand over the same things apart from which hero is on the box.
  - **Galar's fossils are the first in the series made of two halves**, and it is the sharpest
    thing in the step. Every fossil from the Helix to the Sail is one item revived into one
    Pokemon; Cara Liss on Route 6 takes two out of a set of four - a bird, a fish, a drake and a
    dino - and which two go in decides which of the four comes out. The source says so without
    being asked: two `item-fossilized-` conditions on one row, which no row in this dataset has
    ever carried.
  - **A Let's Go save file on the same console is a way of getting a Pokemon**, and it is the
    only one of its kind here. Two people at the Wild Area Station look at what else is on the
    Switch and hand over the Gigantamax Pikachu or Eevee accordingly. Nothing is transferred and
    no edge exists: `home.py` and `lets_go.py` both say those two games reach these two through
    nothing at all, and this does not change it.
  - **The Crown Tundra's giants ask for things the source has never heard of.** PokeAPI carries
    no condition at all on Regirock, Regice and Registeel - what opens each temple is an
    Everstone in the party, a Cryogonal walking behind the player, and a whistle at the door -
    so those three sentences are read off the wiki. Without them a player is sent to a door that
    will not open.
  - **Four Pokemon in these games cost another Pokemon**, which is a shape the dataset has seen
    once before in a fossil shop: the dots lit in the Split-Decision Ruins bring Regieleki *or*
    Regidrago, and the carrot grown in Freezington calls Glastrier *or* Spectrier. Each one's
    sentence names the one it costs, so a player reads the price before paying it.
  - Two conditions joined the shared table rather than a game's: Mustard's first trial and all
    three of them, which between them gate Bulbasaur, Squirtle, Kubfu and Porygon. The rest are
    written in Galar's own table because they are about one game - fifty footprints, ten hidden
    Alolan Diglett, thirty-two players talked to at a tombstone.
  - Thirteen statics are left undescribed on purpose and the build says so: Chewtle on Route 2,
    the Lapras in its lake, the Obstagoon by the road. A place and a level is the whole of what
    there is to say about them, and the table is for what the source cannot say.
  - **The 8 left are exactly steps 5 and 7's**, the same in both halves: the six that only
    evolve - Thwackey, Rillaboom, Raboot, Cinderace, Drizzile, Inteleon - plus Urshifu, which
    Kubfu becomes at one of two towers, and Zarude, which no copy of these games has ever
    produced.
  - One ordering note for step 8, found here rather than there: **the Diglett Trainer's seven
    rewards are six Alolan forms and a Kantonian Slowpoke**, and only the Slowpoke is visible
    now. A form has to be in the game's form table before the gift reader will ask about it, and
    these two have no forms until step 8 - so six gifts, the Galarian birds and the Slowpoke at
    Wedgehurst Station are all waiting on that step rather than missing from this one.
  - Step 3 for both: **12,363 slots in Sword and 12,264 in Shield, over 358 places**, covering
    507 of the 584 species each half lists. The biggest wild step in the dataset by some way -
    SoulSilver held the record at 2,725 - and the two game files are 6.5 MB apiece. Coverage is
    **723 full, 78 partial, 20 missing** of Sword's 821 entries. 609 pipeline tests and 257 app
    tests.
  - **PokeAPI has all of it, which was worth checking before assuming a scrape.** 45,381 rows
    across six version names, structured and conditioned the same way every generation before
    has been. What it needed was reading properly, and that is the step: **three PokeAPI versions
    per half.** The source files each expansion as a version group of its own - a Sword player's
    grass is `sword`, `the-isle-of-armor-sword` and `the-crown-tundra-sword` - so reading the one
    name the way every game before this did would have quietly dropped two thirds of the game.
    `wild_encounters` takes a name or several now, and nothing else had to change.
  - **The weather field is filled in for the first time since it was written.** Nine states of
    the Wild Area's sky, each its own table, and 5,517 of Sword's slots carry one. The other side
    of that is the fold: a species standing there in every sky the place has is not
    weather-dependent, and nine records differing in one word tell a player nothing. What counts
    as "every sky" is measured per place from what the game lists there rather than assumed to be
    nine, because a place the sun never leaves has no snow table.
  - **Two ways of getting a Pokemon that are not a place at all**, and they are the first in the
    dataset: a **Max Raid** - a beam of light over a den, four trainers against one Dynamax
    Pokemon and a single throw at the end - and a **Dynamax Adventure**, the Crown Tundra's run
    through the Max Lair. 5,336 raid records over 276 dens in Sword, and 212 species in the Max
    Lair. Neither could be `other`, which is where a method goes to stop being an answer.
  - **A den's star rating is a number, so it is read as one.** The source writes a row per star,
    which would have put five records under every species in every den; folded into a range they
    read "In a den under a strong purple beam of light and at 2 to 3 stars". 22,461 raid rows
    became 5,336 records that way.
  - Four more overworld methods where Let's Go had three, and all four land on the existing
    three with a sentence beside them: what **wanders a fixed patch**, what **comes up out of the
    ground or the swamp**, and what **gives chase the moment the water is entered**. Three places
    to look is a method; how the thing behaves once it is looked at is a sentence - the same call
    Let's Go's rare spawns and Kalos' flower patches got.
  - **The 20 entries still missing are exactly steps 4 and 5's list**, and the same 20 in both
    halves: the three starter lines, Zacian, Zamazenta, Eternatus, Kubfu and Urshifu, Zarude,
    Regieleki and Regidrago, and Calyrex with Glastrier and Spectrier. Their conditions are
    already visible in the source and were left alone on purpose - the fossils, the Master Dojo's
    two trials, the Regis' fifty footprints, the two carrots, and the Pokemon a Let's Go save on
    the same console hands over.
  - **Step 2's decision showed up exactly where it was predicted to.** Most of the legendaries a
    Dynamax Adventure produces - Mewtwo, the Kanto birds, the Tapus - are among the eighty these
    games hold without listing, so the dataset never asks about them and the Max Lair records
    them for the 212 species that do have an entry. Nothing is wrong; the grid is 584 species and
    this is what that costs.
  - Step 2 for both: **821 entries each across three lists, and 584 species under them.** Galar
    #001 Grookey to #400 Eternatus, the Isle of Armor #001 Slowpoke to #211 Zarude, the Crown
    Tundra #001 Snom to #210 Calyrex. Both halves show the same three with the same numbers,
    which is what a version pair has always meant: they split what can be caught, never what is
    listed. 603 pipeline tests and 257 app tests.
  - **The three overlap, which Kalos' three did not, and that is the whole difference.** X and
    Y's 153 + 153 + 151 add up to the 457 the games ask for; 400 + 211 + 210 here is 821 entries
    and 584 species, because 101 species are in both Galar's list and the Isle of Armor's, 135
    in Galar's and the Crown Tundra's, 13 on both islands and 12 in all three. **Magikarp is
    #144, #42 and #62 in one save file** - one Pokemon wearing three numbers, which no game
    before this pair has done.
  - **Decision: the three are kept apart and there is no combined list.** That is X and Y's
    ruling applied to a harder case, and `every-dex-number-means-one-thing` is the rule that has
    been guarding it since: a number spanning the three is a number no player has been shown,
    and the only one available - the National Dex number - would make the grid say #129 where
    the game says #144. **What it costs is written down rather than left to be found:** a
    collection built on Sword opens on Galar's 400 of the 584 these games hold, and the other
    184 are behind the dex switch. Seeing everything one of these games holds in one grid is not
    something this dataset can express, and that is not a gap in Galar - it is the first time a
    game's Pokedex and a game's boxes have been different lists.
  - **And the eighty get no entry at all.** Bulbapedia counts eighty species Sword and Shield can
    hold while naming them in none of their three Pokedexes - Mewtwo, Celebi, the three Alola
    starters, every Ultra Beast - and twenty-six of those have a Sword and Shield Pokedex entry
    that can only be read in Pokemon HOME. A dex entry is a number in a list and there is no
    number to give them. So the dataset says these games hold 584 where the truth is 664, in the
    safe direction: a tile the grid does not draw asks nothing of a player, while a tile it
    invents asks for something they may not be able to get.
  - **That found a sentence in `home.py` that was wrong.** It named Decidueye as the Pokemon
    Sword has no entry for and HOME will not put there. Decidueye is one of the eighty: the
    example was true about this dataset and false about the game. Changed to Chikorita, which is
    in neither list, and the real consequence is now written down where the filter lives - the
    withdrawal out of HOME is **eighty species stricter than the service it describes**, and no
    tile turns on any of them.
  - **146 of the 821 entries have no source anywhere in the dataset, and they are exactly the 89
    species these games invented.** Not one older species in the three lists is unaccounted for:
    every one of the other 495 is already produced by something written months ago. That is the
    graph checking its own work, and step 3 is what closes it.
  - Validation is **2 errors on purpose**, one per half, which is the same state Let's Go's step
    2 left behind: `every-entry-has-a-method` reports a game with a dex and no encounters as not
    worked on yet rather than as full of holes. They go away when step 3 does.
  - Checked through the app's own dex builder: Sword builds **400 tiles** by default - the Galar
    list - with no forms, since step 8 has not named any yet, and every picture falling back to
    the shared set because step 6 has not run. No tile points at a file that is not there.
  - Step 1 for both: **five routes, which is every route these two have** - the cable between
    the halves, and for each half a deposit into HOME and a withdrawal back out. The dataset is
    at 34 games and 135 routes, nothing held back. 600 pipeline tests and 257 app tests, and
    validation green on all 11 rules with the same two Rockruff warnings as before.
  - **Registering them lights nothing that was waiting, and that is the finding rather than a
    gap.** Every pair since Generation 5 has arrived to find routes already pointing at it,
    declared by files written years earlier; these arrive to find none, because HOME is the only
    door Generation 8 has and every older game that can reach them was already reaching HOME. A
    Pokemon caught in Red still gets to Galar - Poke Transporter, Bank, HOME, Sword - and not one
    edge on that route had to be told these games exist. Checked through the app's own graph with
    Sword as main game: the linked-games step offers all thirty-one other playable games, where
    Let's Go offered one.
  - **The withdrawal out of HOME is the edge `home.home_edges` was written for**, back when the
    node was built and before either of these games was registered, and this is the first time
    that function has had anything to describe: Bank and the four Generation 6 cartridges got their own pair, Let's Go got a
    withdrawal that asks where a Pokemon started, and these get the ordinary one that reads the
    target's own Pokedex. `home.py` even named the example - Sword has no entry for Decidueye and
    HOME will not put one there - and step 1 did not have to invent a thing.
  - `galar.py` is the pair's module and the region's both, which is the `kalos.py` shape rather
    than `alola.py`'s. **There is nothing for a `gen8.py` to hold**: Generation 8 is these two in
    Galar, Brilliant Diamond and Shining Pearl in Sinnoh and Legends: Arceus in Hisui, and what
    those five share is Pokemon HOME, which `home.py` has held since before any of them existed.
  - **Dexit, measured.** The three Pokedexes PokeAPI counts 400, 211 and 210 in overlap heavily:
    584 distinct species, plus the eighty Bulbapedia lists as compatible with these games while
    being in none of the three, is 664 out of the 898 that existed when the Crown Tundra shipped.
    Twenty-six of those eighty have a Sword and Shield Pokedex entry that can only be read in
    HOME. **Whether the eighty belong in the list is step 2's, not this step's** - they are
    written down in `galar.FOREIGN_TO_EVERY_DEX` so that step does not have to find them again -
    and the filter on the way out of HOME is right either way the question goes, because an entry
    no list holds is a tile nobody is shown.
  - **And the same trap Let's Go sprang, this time for good.** `from_group_on` gives a form every
    game from its own version group onward, which holds only while a game can hold everything up
    to its own National Dex number. Left alone it hands this pair **373 forms across 746 lines,
    92 of them rows the table does not hold at all** - every Vivillon pattern, every Unown letter,
    every Burmy cloak. Switched off for them as it is for Let's Go, and `forms.json` stayed at
    291 to prove it. Nineteen Alolan forms are in that 373 and are the part step 8 will have to
    look at hardest: Bulbapedia says a regional form of a species these games are compatible with
    is compatible too, and Raichu, Vulpix, Meowth, Marowak and Sandshrew are all in a Galar list.
  - Three Pokedexes means `DexEntry.dex` gets its second user after X and Y, and not the same
    shape: Kalos' three are one region cut in thirds and share nothing, while the Isle of Armor's
    and the Crown Tundra's each start at #001 and each repeat much of the Galar list. Step 2's.
  - **These games changed after they shipped**, which nothing in the series had done - 400 entries
    on 15 November 2019, the Isle of Armor's 211 with version 1.2.0 on 16 June 2020 and the Crown
    Tundra's 210 with 1.3.0 on 22 October 2020, and both times for every player rather than only
    for the ones who bought the pass. So the dataset holds version 1.3.x, the game as it can be
    bought and played today, while `released` stays the day it first went on sale. Same decision
    the Virtual Console releases got, in a different shape.
  - One thing left standing on purpose at the time: **the picker offered Sword and Shield and a
    collection made with either was an empty grid.** That is what a game between step 1 and step
    2 looks like, and the validator was quiet about it by design - `every-entry-has-a-method`
    reports a game with a dex and no encounters, and a game with neither has not been claimed
    about yet. Step 2 filled it.

- [x] **Brilliant Diamond** (`brilliant-diamond`, gen 8, pair partner: Shining Pearl) - 2026-09-25
  - [x] 1 Entity + edges - 2026-09-25
  - [x] 2 Dex list - 2026-09-25
  - [x] 3 Wild - 2026-09-25
  - [x] 4 Gifts & statics - 2026-09-25
  - [x] 5 Trades & evolutions - 2026-09-25
  - [x] 6 Sprites - 2026-09-25
  - [x] 7 Events - 2026-09-25
  - [x] 8 Alternate forms - 2026-09-25
  - [x] 9 Validate + smoke test - 2026-09-25
- [x] **Shining Pearl** (`shining-pearl`, gen 8, pair partner: Brilliant Diamond) - 2026-09-25
  - [x] 1 Entity + edges - 2026-09-25
  - [x] 2 Dex list - 2026-09-25
  - [x] 3 Wild - 2026-09-25
  - [x] 4 Gifts & statics - 2026-09-25
  - [x] 5 Trades & evolutions - 2026-09-25
  - [x] 6 Sprites - 2026-09-25
  - [x] 7 Events - 2026-09-25
  - [x] 8 Alternate forms - 2026-09-25
  - [x] 9 Validate + smoke test - 2026-09-25
  - Step 1 for both: **`bdsp.py` is new, five new routes, and the dataset is at 36 games and
    140.** The pair module is the arrangement `lets_go.py` made with `kanto.py`: `sinnoh.py`
    holds what is true of the place across the generations and is written for Generation 4 -
    its `cartridge` and its `edges` both hand the question to `ds.py`, which answers with four
    link cables and Pal Park. Neither sentence is true here.
  - **The remake is a second entity beside the cartridge, not a newer date on it.** Same region,
    same 493, different studio, different generation, different way out. Two Sinnohs in one
    dataset with nothing between them: no route this pair brings goes anywhere near Diamond.
  - **The National Dex decision went the other way from Galar's**, which is what makes it worth
    writing down. Sword and Shield were the first games whose boxes hold a list, so their entity
    carries no number at all. These remake the generation that invented the National Dex, they
    kept it, and `nationalDexThrough` is 493 - the same field, filled in for the first time in
    Generation 8.
  - Three routes each, the same count Galar has: the cable between the halves and HOME both
    ways. HOME arrived six months after the games did, in May 2022, so for half a year these
    were the only core games on the console with no way out - which is a fact about a service's
    release rather than a property of a game, and the dataset grows no field for it.
  - **Registering them showed that `forms.py`'s rule breaks here too, for a third reason - and
    it is the reason that shows the rule was never about Dexit.** These hold everything up to a
    number, so the sentence that explains Galar does not apply and the rule should have been
    right. It handed them **373 forms** anyway: the same count as Galar and nearly the same
    list, every Alcremie sweet, an Eternamax Eternatus, thirty-six regional forms. All the rule
    reads is *when* a form arrived, and these came out after Sword and Shield, so everything is
    old enough. Bulbapedia states the real limit in one line: only Pokemon that exist in the
    game data, the first four generations, **regional forms excluded**.
  - So the rule is off for these two as well and step 8 writes the table. A remake is the
    clearest case there is: what a game holds is a fact about the game, and a date is no
    substitute for it.
  - Three limits on the HOME routes, read rather than assumed, and **none of them changes what a
    living dex here can hold**: Spinda cannot be transferred either way at all, a Nincada from
    another game cannot be deposited in, and certain Legendaries may leave a save file only once
    each. The first two are entries a player fills in the game instead, and the third is a limit
    on how often a route may be used rather than on where it goes. Step 3 says whether any of
    them needs more than a docstring.
  - The withdrawal filter needed no special case: `PresentInTargetDexFilter` asks the target's
    own list, which is the wiki's own sentence about these games. An Alolan Vulpix is refused
    because step 2 and step 8 will not put it in the list, not because anything here names it.
  - 639 pipeline tests, 257 app tests, validation 11 rules with 0 findings. The two game files
    are an entity and two empty lists, which is what step 1 means.
  - Step 2 for both: **the 151 Diamond showed, in Diamond's order, and not Platinum's 210.**
    That is the one place a remake could quietly have grown and did not. The third version of
    2008 added 59 species to the regional list; these went back past it - Bulbapedia calls it
    "the Sinnoh Pokedex's return to the original Diamond and Pearl numbering" - so Eevee's
    family, Togepi's, Rotom and Scyther are National Dex work here the way they were in 2007.
  - The list is asked of `sinnoh.py` rather than copied, because a Pokedex is a fact about the
    region and this is the same list: PokeAPI files `original-sinnoh` under both version groups,
    and four games in two generations now put Turtwig at #001 and Manaphy at #151. Its function
    was called `pair_dex_entries` and is `original_dex_entries` now - named for the list rather
    than for a pair, since there are two pairs.
  - **Two lists doing two jobs, which Galar did not have.** The Pokedex on screen is the
    region's 151 and what a living dex here aims at is the National Dex the entity carries: 493
    tiles in the grid, 151 of them named on a page in the game. Every entry's `dex` is empty,
    because one list needs no label - Galar's three were the exception, not this.
  - Validation is **2 errors and they are the right two**: `every-entry-has-a-method` against
    each half, saying their encounters have not been gathered. That is the state the rule was
    written for. It also says something worth keeping for step 7: of the 151, exactly one -
    **Manaphy** - is produced by nothing anywhere in the dataset, and the other 150 are all
    produced by some older game. Diamond and Pearl reach Manaphy through Pokemon Ranger, which
    these two have no version of.
  - 642 pipeline tests, 257 app tests.
  - Step 3 for both: **2,060 wild records for Brilliant Diamond and 2,065 for Shining Pearl,
    across 82 places, covering 257 and 261 species.** Read off Bulbapedia, because PokeAPI has
    no encounter for these games at all - not a thin table, none - which is what the reading
    before Generation 8's remaining games found and is true of all six of them.
  - **The prediction that this pair needed no new reader was half right, and the half it got
    wrong is the interesting half.** The page shape is the one `encountertables.py` already
    parses. Two things in it were not: the pair of letters in the Games column was written into
    the reader as `("OR", "AS")`, and **a Generation 8 grass table splits its rate column three
    ways**, under a morning, a day and a night icon with no text.
  - So a row is up to three slots now. On Sinnoh's thirty route pages **all ninety-two rows that
    carry three rates carry three different ones**, so folding them into one would have thrown
    away the whole of what they say - and **0% appears 112 times**, which is the page saying the
    species is not out at that hour. Those become no slot at all: the difference between a tile
    a player fills after dark and one they could stand in the grass all morning for and never
    fill. Three rates that agree say nothing and the hour is dropped, the way a heading that
    repeats the method column already was.
  - **The Grand Underground is eighteen caves with a page each**, and it is the reason a
    remake's encounter list is not its original's: it holds species Sinnoh above ground has
    none of. Eleven are reached from the tunnels and seven open after the National Pokedex does.
    Named "Grand Underground, Grassland Cave" and so on, because that is what a player would
    say; the pages' own split into Visible Encounters and Rare Spawns arrives as the sub-area
    without anything naming it.
  - Fifty-six route and town pages plus the eighteen caves, **and not one warning**: every page
    yielded rows and every species name the wiki writes matched something. The four aliases are
    Shellos's and Gastrodon's two seas, which is the answer Hoenn gives too.
  - Version exclusives came out of the tables rather than a list: **20 species only Brilliant
    Diamond catches and 24 only Shining Pearl does** - Murkrow, Stunky, Scyther, Seel here;
    Misdreavus, Glameow, Pinsir, Slowpoke there.
  - Validation is **2 errors and they have changed for the better**: not "this game's encounters
    have not been gathered" any more, but **Manaphy**, which is in the dex at #151 and which
    nothing in the dataset produces. Diamond and Pearl reach it through Pokemon Ranger and these
    two have no version of that. It is step 4's to place or step 7's to explain.
  - 648 pipeline tests, 257 app tests.
  - Step 4 for both: **41 gifts and statics each - 3 starters, 6 fossils, 3 handed over, 2 eggs
    and 27 standing in one spot.** 2,116 records for Brilliant Diamond, covering 295 species.
    Written out by hand, because there is nothing to write it *onto*: every game before Let's Go
    had PokeAPI rows for a `GiftDetail` to add a sentence to, and these have none.
  - **Ramanas Park is the remake's answer to a question Diamond never had to ask.** A Generation
    4 cartridge got the older legendaries by trading with a Generation 3 cartridge through Pal
    Park; a Switch game has no cartridge slot to trade with. So these two grow a building, and
    **seventeen legendaries that used to be somebody else's become theirs** - the birds, the
    beasts, the tower duo, the giants, the eon duo, the three super-ancient and Mewtwo - each
    called up by a slate dug out of the Grand Underground. It splits the way a pair always
    splits: Johto's three and Ho-Oh in Brilliant Diamond, Kanto's three and Lugia in Shining
    Pearl, the rest in both.
  - The Distortion Slate is deliberately not recorded. It calls up a second Giratina and
    Turnback Cave already has the first: a living dex counts what a box can hold, not how many
    ways there are to fill one page.
  - **The two Mythical Pokemon in Floaroma Town are the strangest rows in the table, and they
    are in it because a player can still get them today**: an old woman hands over a Mew if the
    console has Let's Go save data and an old man a Jirachi if it has Sword or Shield save data.
    That is a condition on hardware rather than an event that closed. Compare the three below
    them that really are shut - Oak's Letter and the Member Card were handed out over the
    internet in 2022 and never since, and the Azure Flute wants a finished Legends: Arceus on
    the same console. Those three are step 7's clearest cases.
  - **Step 3 was missing the honey trees and now is not.** They are not on any location page:
    the wiki keeps one table for all twenty-one trees, so this dataset can say what a slathered
    tree gives and not which tree - where Diamond, whose slots came from PokeAPI one place at a
    time, names Valley Windworks and the rest. 15 rows, Munchlax and Heracross among them, and
    the four trees each save file picks are a requirement rather than a place.
  - Manaphy is still the only error, and step 4 is where it became certain rather than likely:
    **the wiki's list of this pair's event Pokemon does not have it.** Diamond and Pearl hatch
    it from an egg Pokemon Ranger sends over, and there is no Ranger to send it. It is step 7's.
  - 651 pipeline tests, 257 app tests.
  - Step 5 for both: **4 traders, 246 evolutions and 9 babies the day care alone produces.**
    2,375 records for Brilliant Diamond, covering 468 of the 493 a living dex here aims at.
  - **The one place where treating a remake as a Generation 8 game gives the wrong answer**, and
    it was measured before it was decided. Asked as `brilliant-diamond-shining-pearl` the
    evolution reader returns the same 246 records - but seven of them by the newest route, so
    Eevee would take an Ice Stone and a Leaf Stone, Magneton and Nosepass a Thunder Stone and
    Feebas a Prism Scale. **Not one of those items is in these games.** Bulbapedia states it
    outright: the Ice Stone is not obtainable in Brilliant Diamond and Shining Pearl, so Eevee
    can only evolve into Glaceon with the Ice Rock.
  - So `EVOLUTION_GROUP` is `diamond-pearl` - the original's, not the remake's - and the rule
    ids that come out are Diamond's. **`evolution-rules.json` did not change by one byte**,
    which is the answer being right rather than merely chosen: a Magnezone made at Mt. Coronet
    in 2007 and one made there in 2021 were made the same way.
  - Nothing is lost by looking backwards, and that was checked too: both readings give 246
    records with the same targets. No evolution arrived after Diamond and Pearl for a species
    this dex holds.
  - The four traders are the originals' four, read off the wiki rather than assumed - Hilary's
    Abra for a Machop, Norton's Chatot for a Buizel, Mindy's Haunter for a Medicham, Meister's
    foreign Magikarp for a Finneon. Same people, same rooms, same wants, so the table stays in
    `sinnoh.py` and this pair asks for it.
  - Of the Sinnoh 151, **146 are produced in Brilliant Diamond**: Glameow, Misdreavus, Palkia
    and Shieldon are the other half's, and Manaphy is nobody's.
  - 652 pipeline tests, 257 app tests.
  - Step 6 for both: **493 pictures, 44 MB, from Pokemon HOME rather than from a sheet** -
    because these games have no sheet. The Archives' only category carrying their name holds
    trainer select-screen models, and the two files under Scarlet and Violet's are not a sheet
    either. What the wiki draws the modern games with is HOME's renders, 3,143 of them.
  - **That is the honest answer as well as the available one.** These games have no battle
    sprite to photograph: a HOME render is the picture a player sees when they open a box.
  - **The first set here that is not a generation's.** It is called `home`, not
    `generation-viii/home`, because four games in two generations will share it - these two,
    Scarlet and Violet, and whatever Legends: Z-A's thirty-five Mega files do not cover.
  - HOME spells a name its own way and more simply: four digits, no sheet code, no prefix but
    its own - `HOME0001.png`. A sheet draws a species with visible sexes as `_m` and `_f` and
    gives it no plain name at all; HOME marks only the female, so the plain name is always right
    and there is no second spelling to try. **All 493 answered on the first name asked**, which
    is the first set in this dataset where nothing had to be guessed at twice.
  - They arrive padded in a 512 pixel frame, exactly like Generation 7's 240 - so `cropped`
    applies unchanged and the folder is 44 MB rather than what the frames claimed. 91 KB a
    picture, which is Galar's 81 with four more years of polygons.
  - **And it broke an assumption in the app, which is the part worth keeping.** The scaling rule
    read the generation out of the set name: `generation-vi` as a prefix covered every 3D
    generation in one stroke. A set called `home` is not a generation. So the question is asked
    the other way round now - the five hand-drawn generations are named and everything else is a
    render - which is the safer of the two defaults: a set nobody has told the app about is far
    likelier to be a render than a hand-drawn grid, and it is what a game with no set of its own
    already fell back to.
  - 41 minutes of fetching, paid once. 654 pipeline tests, 257 app tests.
  - Step 7 for both: **nine entries the two halves cannot fill between them, and exactly one
    distribution ever covered any of them.** Checked species by species against the wiki's own
    events table rather than assumed. Validation is back to **11 rules, 0 errors, 0 warnings**
    for the whole dataset.
  - Eight of the nine are the other half's version exclusives, and **not one of them has ever
    been handed out in any distribution in the series** - no Misdreavus, no Glameow, no Palkia,
    no Shieldon, no Murkrow, no Stunky, no Cranidos, no Dialga. That emptiness is the finding
    rather than a gap: a version exclusive is filled by the link to the other half, which is
    what the transfer graph is for.
  - The ninth is **Manaphy, and the reason is the one place a remake is poorer than the game it
    remakes.** Diamond and Pearl hatch it from an egg Pokemon Ranger sends across; Ranger is a
    Nintendo DS game with no version of itself on this console. So these two inherited the hole
    and not the way out of it.
  - What covered it is generous and narrow at once: the Manaphy Egg was handed out over the
    internet **from 19 November 2021, the day the games came out, until 21 February 2022**. A
    player who bought them at release can fill that entry; one who bought them in March cannot.
  - Five reasons per half became **eight entries with reasons**, because `spread_unobtainable`
    pushed them down the evolution lines: Bastiodon behind Shieldon, Mismagius behind
    Misdreavus, Purugly behind Glameow. Nothing was typed twice.
  - 656 pipeline tests, 257 app tests.
  - Step 8 for both: **137 forms each - 94 sexes, 31 cosmetic, 12 functional - 137 form-change
    records, and 93 more pictures.** `forms.json` goes from 379 to 379, because these are the
    same forms the Generation 4 cartridges already hold; what changed is which games claim them.
  - **The shape of the answer is the finding: this is Diamond's 130 plus the seven Platinum
    added.** Not the generation's list, not the console's - the third version's. Each of the
    seven was checked on the wiki rather than carried over: Rotom's five appliances are in
    Rotom's Room in the Team Galactic Eterna Building, Giratina's Origin Forme is the Griseous
    Orb ("from Platinum to Brilliant Diamond and Shining Pearl, it transforms into its Origin
    Forme while holding a Griseous Orb"), and Shaymin's Sky Forme is the Gracidea, which the
    wiki files under Generation VIII key items for these games.
  - **Two of them are better here than in Platinum, and for a living dex that is not a detail.**
    The Secret Key was the first of four items Platinum handed out at events; here the player
    gets it the moment the Rotom in the Old Chateau is caught. And Platinum let only one Rotom
    possess each appliance at a time and would not let the forms be traded - these will, and
    they add the Rotom Catalog. **In Platinum a living dex of Rotom's six forms was impossible;
    here it is not.**
  - One thing is worse, and it gets its own sentence: there is no Distortion World, so the
    Griseous Orb is the whole of how Giratina takes its second shape rather than one of two ways.
  - **What is not here is not a judgement call.** No regional form of anything, no Mega, no
    Gigantamax, nothing above 493 - Bulbapedia states the limit outright, and `forms.py` had the
    rule switched off for this pair since step 1 precisely so this step could write the answer
    instead of inheriting 373 wrong ones.
  - The meteorites were checked rather than carried over too: the wiki has a "Meteorites in
    Pokemon Brilliant Diamond and Shining Pearl" section saying four stand on the east side of
    Veilstone City and a Deoxys in the party changes form when they are inspected. So Diamond
    and Pearl's own table serves unchanged for everything except those three.
  - **HOME drew 93 of the 94 sexes and not the ninety-fourth**: there is no female Torchic
    render. It falls back to the shared set's picture, which is the right Pokemon in another
    generation's style rather than a hole - the documented answer, working.
  - 658 pipeline tests, 257 app tests, validation 11 rules with 0 findings.
  - Step 9 for both: **validation green on all 11 rules with nothing to report**, and a
    collection made through the wizard on the published exe. Coverage is **465 full, 19 partial,
    1 missing and 8 explained** per half, against Diamond's 437 full and 47 partial - the
    remake covers twenty-eight more species in the game itself, and that is the Grand
    Underground.
  - **The one missing is Phione, and it is Diamond's too.** It hatches from a Manaphy and
    nothing in the dataset produces a Manaphy, so the hole the originals have was inherited
    rather than introduced. Diamond reports the same 1.
  - **"Sinnoh on a Switch": Brilliant Diamond as main game, and the linked-games step offered
    every playable game with the route it takes** - "via Poke Transporter, then Pokemon HOME"
    for Generation 5, "via Pokemon Bank, then Pokemon HOME" for Generations 6 and 7, "via
    Pokemon HOME" for Let's Go and for Sword and Shield, and Shining Pearl **"via trading"**.
    Step 1's finding on screen: HOME is the only door, and the pair's own cable is the one
    exception.
  - The grid draws **0 of 599** with regional, functional and gender forms on - 493 species and
    106 forms - and the headless run makes 630 with cosmetic ones too. Every tile off `home`
    and not one falling back to another set.
  - **Searching "rotom" gives six tiles at #479** - Rotom, Fan, Frost, Heat, Mow, Wash - which
    is step 8's whole point standing on the screen: that row is a living dex Platinum could not
    hold.
  - The Wash Rotom popup reads **Electric / Water**, the form's own typing, and carries the
    form-change sentence for both halves with "Eterna City, Team Galactic Eterna Building"
    under it and "Then to Brilliant Diamond: trading" on the other half's. Its citation line
    says **"bulbapedia, read 25 Sep 2026"** - which is the Phase 3 citation item visible in the
    interface rather than only in a file.
  - The write path was exercised: marking it caught greened the tile, moved the counter to **1
    of 599**, filled in "Caught on 25/09/2026", and the record landed in the data file as
    `rotom` / `rotom-wash`, status `inMainGame`, held in `brilliant-diamond`. The user's
    settings were copied out first and restored byte for byte - same sha256, same 106 bytes -
    and their own data file was provably untouched: same sha256, same 4,167 bytes, last written
    two hours before the test began.
  - Run headless too, once per half, through the app's own dataset loader, dex builder,
    availability rule, sprite chain and capture store: both halves build the same 630 lines with
    every form on, every one of them draws, and 584 of 630 are available in Brilliant Diamond
    alone against 579 in Shining Pearl.
  - One thing found rather than fixed, written down for Phase 3: **a form with no picture of its
    own falls back to its species' picture on the same sheet before it falls back to the shared
    set's picture of the form.** That is right for a Wash Rotom in Black, which should keep the
    Generation 5 Rotom the game drew - and wrong for the one gender form HOME does not draw, the
    female Torchic, which now shows the male render instead of the shared female one. One tile
    in 630, and the rule that makes it is deliberate, so it is a note rather than a change.

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

- [x] A hand-written table's citation should carry the day a human read the page — 2026-09-25
  - The last of the build-day dates. A fetched citation has taken its date from the cache entry
    the answer came out of since the build-time work; what was left were the tables a person
    read off a wiki and typed in, which have no fetch to take a date from and were taking
    `date.today()` instead. That said a reader had been on Bulbapedia this morning, and said
    something different tomorrow about a table nobody had touched.
  - **The measurement was wrong twice before it was right, and both corrections made the item
    bigger.** The TODO said 209 records; it was 209 when it was written and Galar has since
    added 641. Then the first count of what carried today's date turned up 793 - and 491 of
    those were not hand-written at all but PokeAPI's. Most were honest, because Galar's
    encounters really were fetched today; 152 were not, and they were in the half that was
    supposed to be finished.
  - **Two defects, not one.** The hand-written tables are 31 call sites across eleven modules.
    The other is four citations that name `pokeapi.co/api/v2/evolution-chain` - the collection
    rather than one chain in it - because the fact they stand for was read chain by chain.
    Nothing ever fetches a collection url, so asking the cache about it got nothing and fell
    through to today: those citations moved every day while what was behind them had not been
    read in a week.
  - `ReadByHand` in `sources.py` is the answer to the first: a module states the pages its
    tables were typed from and the day each was read, and cites through it. What matters is
    what it does with a page it does not know, which is raise - a new table cannot quietly
    inherit a date nobody chose for it. Six games are still to be written and each brings
    tables of its own, which is why this went first rather than last.
  - The dates are the commit that first carried each table, which is the best evidence there
    is once the reading is over. They are not all one day per module and that is the point:
    Hoenn's trades were read on the 22nd and its fossils on the 23rd, and a single date per
    file would have been a smaller lie rather than none.
  - Crystal's Suicune has a page of its own - Mt. Mortar - and `johto.py` has no date for it,
    because it is Crystal's table rather than Johto's. So the two parameters that used to take
    a page name now take a citation, and the game that read the page dates it.
  - `DiskCache.newest_under` answers the second: the newest thing read under a url, for a fact
    made of a whole collection. It scans one host's metadata once, dates each entry by the same
    rule a single url is dated by - timestamp fallback included, because most chains in a cache
    this old were written before the date was recorded - and costs 1.8 seconds on a 17,732-file
    cache. A build still takes 74 seconds.
  - **Proved rather than argued: the build was run again with the clock moved to 2 October, and
    the two datasets are byte-identical apart from `builtOn`**, which is the one field that is
    supposed to say when the build ran. Before this, that experiment moved 2,395 lines.
  - 641 citations still say 2026-09-25 and every one of them is true: Galar's tables were
    written today and its encounters fetched today. A date being today is not the bug; a date
    being today *because* the build ran today is.
  - Three tests in `test_sources.py`, three in `test_http.py`, and one of them is a guard rather
    than a check - no module under `gamedefs/` may contain the string `date.today()`. The habit
    is one line long and comes back easily.
  - 635 pipeline tests, 257 app tests, validation 11 rules with 0 findings.

- [x] **Legends: Arceus** (`legends-arceus`, gen 8, standalone) - 2026-09-25
  - [x] 1 Entity + edges - 2026-09-25  - [x] 2 Dex list - 2026-09-25
  - [x] 3 Wild - 2026-09-25  - [x] 4 Gifts & statics - 2026-09-25
  - [x] 5 Trades & evolutions - 2026-09-25  - [x] 6 Sprites - 2026-09-25
  - [x] 7 Events - 2026-09-25  - [x] 8 Alternate forms - 2026-09-25
  - [x] 9 Validate + smoke test - 2026-09-25
  - Step 1: **37 games, 142 routes, and the two smallest numbers in the dataset.** This is the
    first playable entry here that is not half of anything - no pair partner, no third version
    beside it - so it brings a deposit into HOME and a withdrawal back, and nothing else. Every
    other game carries a cable. It trades only with other copies of itself, which is a route
    from a game to itself and one a graph of games has nowhere to draw.
  - No shared module, and the three it does not read from are named in `legends_arceus.py`
    rather than left to be rediscovered: not `sinnoh.py`, because Hisui shares ground with
    Sinnoh and nothing a living dex cares about; not a `gen8.py`, which still has nothing to
    say; and not a `legends.py` shared with Z-A, because the one thing those two share is a
    table reader and that belongs in `encountertables.py`.
  - **Galar's Pokedex answer, reached by a different road.** No National Dex,
    `nationalDexThrough` empty, `dexSource` gameDex. `galar.FOREIGN_TO_EVERY_DEX` was read
    first, as the reading before these six games says to.
    - _Step 1 concluded from it that the dex here **is** the boxes, and step 2 found two entries
      that make that not quite true. Corrected in place rather than left standing: the leftover
      is `HELD_WITHOUT_BEING_LISTED`, and it has two entries where Galar's has eighty._
  - **Registering it changed 34 game files, and not one of them beyond a rule's name** -
    measured by stripping the rule ids and comparing, rather than by reading the diff. What
    happened is worth keeping: the 16 Hisuian forms were in no game's list, so `evolutions.py`
    could not name them, and the rules that make them were told apart by version group with a
    condition reading "in Hisui". They are now told apart by what they produce.
    `bergmite-to-avalugg-legends-arceus` is `bergmite-to-avalugg-hisui`, and
    `growlithe-to-arcanine-red-blue` goes back to being `growlithe-to-arcanine` because nothing
    needs telling apart from it any more. 576 rules before and after; 17 renamed, 14 rewritten.
  - **The form rule spoke for this game and handed it 393 forms**, which is more than it gave
    any other Generation 8 game, for a game whose boxes hold 242 species and nothing else: every
    Alcremie sweet, 19 Alolan forms, 18 Galarian ones. So `FORMS_NAMED_BY_THE_GAME` gains a
    seventh game at step 8 and the table is written by hand, as the reading before these six
    games budgeted. The rule is not wrong about dates; it is that a date is not what a game
    holds.
  - It also put **24 forms into the dataset that had never been in it** - the 16 Hisuian ones,
    White-Striped Basculin and female Basculegion, Origin Dialga and Palkia, Therian Enamorus,
    and three Generation 8 leftovers Sword and Shield's own hand-written table had dropped:
    Eternamax Eternatus, World Cap Pikachu and Dada Zarude. Those three are step 8's to drop
    again. No other game gained or lost a single form.
  - Left for the steps that can answer them: the withdrawal filter asks whether the target lists
    the species, and the wiki's sentence is stricter - non-Hisuian regional forms of a listed
    species are refused. The app's `DexContains` lets a form through whenever the target lists
    its species, so the same gap Brilliant Diamond left open is open here; it reaches a tile
    only once there is a form list, which is step 8.
  - `sprite_set` is deliberately left out. This is the only one of the six with a sheet of its
    own - `Spr_8a_NNN`, 367 files - and step 6 fills it in, so that a guess made at step 1
    cannot quietly become a folder of pictures.
  - 663 pipeline tests, 257 app tests, validation 11 rules with 0 findings. The game file is an
    entity and two empty lists, which is what step 1 means.
  - Step 2: **the Hisui Pokedex, 242 entries, Rowlet #001 to Darkrai #242.** One list, so no
    entry says which dex it is numbered in - the rule every game before X and Y followed, and
    the opposite of Galar's three - and it is the whole of what a living dex here aims at, since
    `dexSource` gameDex means there is no National Dex above it.
  - **Checked against the wiki row by row rather than trusted.** PokeAPI's `hisui` and
    Bulbapedia's list agree on all 242 entries, in the same order, with the same numbers. The
    two texts differ in exactly one way, on 32 rows: the wiki names a form where the source
    names a species - "DecidueyeHisuian Form" against `decidueye`.
  - **And that difference is most of the game.** Sixteen of the 242 species exist here only as
    their Hisuian form, so a grid drawn with forms switched off will put a Kantonian Growlithe
    on a tile that a player of this game can only fill with the Hisuian one. Sinnoh had Burmy's
    three cloaks and Shellos's two seas; here it is a quarter of what the game is about, and it
    all waits on step 8. Nothing in the dex list carries a form, for the reason Galar's gives.
  - **The finding that corrects step 1: #168 and #169 are the *Kantonian* Vulpix and Ninetales**
    - the snow of the Alabaster Icelands is full of the Vulpix that is not the icy one - so the
    Alolan pair the transfer rule excepts is a genuine exception rather than the wiki naming
    this game's own entries. A box in Hisui can hold two kinds of Vulpix while the Pokedex has a
    page for one. Written down as `HELD_WITHOUT_BEING_LISTED` and used nowhere: a form is not a
    dex entry, and Galar's eighty had to be acted on where these two do not.
  - Validation is **1 error and it is the right one**: `every-entry-has-a-method`, saying the
    encounters have not been gathered. It carries a number worth keeping for steps 4, 5 and 7 -
    **nine of the 242 are produced by nothing anywhere in the dataset**, and seven of those nine
    are the Pokemon this game invented: Wyrdeer, Kleavor, Overqwil, Ursaluna, Basculegion,
    Sneasler and Enamorus. The other two are Phione and Manaphy, which is the same hole
    Brilliant Diamond has and this game fills.
  - 667 pipeline tests, 257 app tests.
  - Step 3: **1,720 wild records across 81 places, covering 216 of the 242.** The second table
    reader the reading before these six games budgeted for, and the prediction about it was
    wrong in almost every particular except the one that mattered - it is small.
  - **The tables are a level below the place a player would name**, which the plan did get
    right: the Obsidian Fieldlands' own article has an empty Pokemon section and nineteen
    sublocations under it. So 81 pages rather than five, and a record reads "Obsidian Fieldlands,
    Horseshoe Plains" the way the Grand Underground's say which cave. The other 22 parts of
    Hisui are written down as `NO_WILD_TABLE` rather than dropped: eleven base camps, four
    arenas where a noble is fought, and seven places the story owns.
  - **The plan said `Pokemon | Levels | Alpha Levels | Time of day | Weather` with ticks. The
    ticks are there; everything about how they are laid out is not.** Time of day and Weather
    are not columns but *blocks* - four columns and six - named only by icons, in a second
    header row, and a row ticked in all of one block writes a single cell spanning it. So the
    reader expands colspans and reads the header's own icons rather than counting columns.
  - **And the weather block is a different width in every area**, which is what makes reading
    the header a requirement rather than good manners: six in the Obsidian Fieldlands and the
    Crimson Mirelands, seven in the Coronet Highlands, five on the Cobalt Coastlands, four in
    the Alabaster Icelands - where it never rains and it can blizzard. A reader that had counted
    on six would have put every tick in three of the five areas one column out and reported
    nothing wrong. This is the Brilliant Diamond lesson - *look at the header before trusting a
    row* - paying for itself one game later.
  - **A page can hold both kinds of table.** Lake Verity is a sublocation of the Obsidian
    Fieldlands and a Sinnoh lake, so its article carries forty-one: Diamond's, Platinum's,
    HeartGold's, Brilliant Diamond's, and one of these. Wayward Cave carries two Generation 4
    tables whose Games column spans six letters and whose Rate column spans three - so "a header
    with a block in it" would have read them as Hisui rows and named six games as six weathers.
    Each reader insists on its own header: this one on a block called "Time of day", the older
    one on two particular letters in a Games column.
  - **There is no Location column at all**: the way a player meets something is a heading over a
    group of rows, and the rows under no heading are the ordinary ones - so `""` is a real key
    in `METHODS` and it is the commonest. Three of Let's Go's words do most of the work, because
    these games ask the same thing of a player: no grass, no rod, nothing rolled when they walk.
  - **Two new methods, and both were measured before they were named.** A space-time distortion
    holds 69 species and **30 of them are in nothing else in the game** - every Johto and Unova
    starter, the whole Eevee family, Porygon's line, Gengar, Scizor - which is the Max Raid
    argument exactly: `other` would tell a player that a third of what this game holds has no
    answer. And a shaking tree, a shaking ore deposit and the wooden boxes in the Celestica
    ruins are **one** method with the furniture said beside it, which is the call Kalos's five
    ambushes got. It is Johto's headbutt trees three hundred years earlier, and it is not
    `headbutt`: there is no move and two of the three are not trees.
  - A fixed alpha stayed `overworld`. Fourteen species are only ever one - Garchomp, Torterra,
    Gallade, Machamp - so the rows cannot be folded away, but walking up to a Pokemon that is
    standing there is not a new way of meeting one. Which one it is goes in the sentence.
  - **The finding the ticks themselves gave: they carry almost nothing.** Of 1,720 records only
    264 have a time of day and **three** have a weather. And the time is binary - every single
    restricted row is either "night" (190) or "morning, day and evening" (74), and there is no
    third phrase. A grid of ten columns per row turns out to say "is it nocturnal", and once for
    a Ponyta that dislikes rain.
  - Validation is **8 errors and they are the right eight**: seven of the Pokemon this game
    invented - Wyrdeer, Kleavor, Overqwil, Ursaluna, Basculegion, Sneasler, Enamorus - plus
    Manaphy. Every one of them is step 4's or step 5's. Phione came off that list, because the
    water tables have one.
  - 681 pipeline tests, 259 app tests.
  - Step 4: **23 records - three starters, nineteen statics and one gift - and the dataset's
    first game where every entry behind one of them is behind a numbered quest.** There is no
    cave here a player can walk into and find a deity in: 19 of the 23 name a mission or a
    request, and the list of those is one page while the place each one stands is on twenty-one
    others.
  - So a hand-written gift may now **cite its own page**. `RecordedGift` grew an optional
    `source`, because citing the quest list for "Enamorus is in the Scarlet Bog" would be a
    footnote pointing at a paragraph that does not say it. Every table before this one was read
    off a single page and needed nothing of the kind.
  - **All three starters are gettable in one save file**, which is true of no other game in the
    dataset. Laventon offers the three he has just chased across the Fieldlands, and after
    Mission 18 he hands over the two that were not picked - where every other starter anywhere
    here needs a trade or a second cartridge.
  - **Two records turn on another game's save file being on the console**, and they are the only
    two of their kind: Shaymin's request appears if there is Sword or Shield save data, Darkrai's
    if there is Brilliant Diamond or Shining Pearl save data. That is the Azure Flute looking
    back - Brilliant Diamond gets its Arceus because *this* game has been played. A save file is
    not a route between two games and no edge is drawn for it; it is a condition on one record.
  - **The weather is the whole answer exactly twice.** Of 1,720 wild rows only three tick a
    weather at all, and then two of the four Forces of Nature turn out not to appear unless the
    sky is doing one particular thing: Tornadus in a blizzard at Bonechill Wastes, Thundurus in
    a thunderstorm between Sand's Reach and Lunker's Lair.
  - **And the Alolan Vulpix closes the question step 1 opened.** Step 1 read HOME's rule -
    non-Hisuian regional forms are refused, "with the exception of Alolan Vulpix and Alolan
    Ninetales" - and could not say why. Step 2 found that the Hisui Pokedex's #168 is the
    *Kantonian* Vulpix. This is the rest: Request 83 has a Security Corps member from Alola
    called Keaka whose Vulpix are hiding in Whiteout Valley, so there is a second Vulpix in the
    game that the Pokedex has no page for. HOME excepts those two because the game contains them.
  - **No levels on any of the 23**, which is a gap rather than a decision and is written down as
    one: every other game takes its gifts from PokeAPI, which carries the level, and the pages
    that say where each of these stands do not say what level it is at.
  - Validation is **6 errors, down from 8**, and all six are step 5's: Wyrdeer, Kleavor,
    Overqwil, Ursaluna, Basculegion and Sneasler, every one of them an evolution this game
    invented. 233 of the 242 now have a record in this game; the nine left are those six plus
    Hisuian Arcanine, Electrode and Lilligant, which are stones.
  - 687 pipeline tests, 259 app tests.
  - Step 5: **143 evolutions to 131 species, no trades and no eggs - and validation went green.**
    All 242 entries now have a record in this game, and the two empty halves of this step are
    the interesting half.
  - **There is no in-game trade here, and the wiki says so outright**: "Pokemon Legends: Arceus
    is the only core series game to not feature in-game trades." And no eggs either - the game's
    own article lists what was removed: abilities, held items, breeding, Eggs and Pokerus. So
    there is no `trade_encounters` call and no `breeding_encounters` call, the second game in
    the dataset with neither after the Let's Go pair. Both are absences stated rather than lines
    quietly not written, and a test asserts the module has no table for either.
  - **And then the defect those two absences caused.** PokeAPI has **no Legends: Arceus detail
    for a single one of the classic trade evolutions** - `kadabra` still carries exactly one
    detail, `red-blue` and `trade` - so a build that trusted the source told a player of the one
    core series game without in-game trades to go and trade a Kadabra. Thirteen records said it.
  - So `evolutions.py` grew `NOT_IN_THE_SOURCE`: **twelve ways of evolving written by hand**,
    the same last resort as the hand-written wild slots in `wild.py` and the hand-written gifts
    in `gifts.py` - and it took until the twenty-ninth game for one to be needed, because until
    Hisui the source had every way a Pokemon could change. Four use the Linking Cord, which that
    item's page names all four of; the other eight use the item that used to be held, and each
    of those eight pages says it in its own words: "due to the absence of held items, the Metal
    Coat simply needs to be used on Onix or Scyther". Read one at a time rather than generalised
    from the first.
  - Each of the twelve **cites the item page it was read from** rather than a chain url, because
    citing the chain would point at a document that does not say it. A variant carries a page
    name rather than a citation so that it stays hashable - it is a dict key twice over.
  - Measured rather than assumed: **no leakage.** The twelve are version group `legends-arceus`,
    so Sword, Platinum and Brilliant Diamond all still trade their Kadabra, and the shared rules
    file went from 576 to 588 with 29 renames and no rule losing its meaning. 34 game files
    changed; ten of them beyond a rule's name, and every one of those ten is the
    `evolution-chain` collection citation moving to today because the chains were read today.
  - **One `trade` record survives and it is step 8's**: `graveler -> golem` by the Alolan rule,
    which is here only because the form rule still hands this game every Alolan form. When step
    8 writes the real list it goes, and that is the check - after step 8 this game should have no
    trade record at all.
  - Validation: **0 errors**, and one warning that is the same story. Seven evolutions here start
    from a form nothing in the dataset produces - `growlithe-hisui`, `qwilfish-hisui`,
    `basculin-white-striped` and four more - because step 3's records name species and sixteen of
    the 242 exist here only as their Hisuian form. Step 2 predicted it and the validator found it
    on its own. Closing it is a change to the table reader, not only to a form list.
  - 693 pipeline tests, 259 app tests.
  - Step 6: **318 pictures, 25 MB, and all 242 species drawn - nothing falls back.** `8a`, off
    the Bulbagarden Archives, into `generation-viii/legends-arceus`. 33 minutes of fetching,
    paid once.
  - **The only one of the last five games in the series with a sheet.** Sword and Shield have
    `8s`; after them Brilliant Diamond, Shining Pearl, Scarlet and Violet all draw Pokemon
    HOME's renders because the Archives have nothing for any of them. The reading before these
    six games got this right, and the two details it did not have are the interesting part.
  - **This is the first sheet here that is not a whole National Dex.** `Spr_8a_001.png` is a 404
    because Bulbasaur is not in Hisui - the Generation 7 sheets draw everything up to their own
    number whether the game holds it or not. So a miss is ordinary here in a way it has never
    been before, and 142 of them were needed to place 318 pictures.
  - **And a species name on this sheet can be a form code**, which is new. Fifteen species are
    in this game only as their Hisuian form, so the sheet draws no plain one at all:
    `Spr_8a_058.png` does not exist and `Spr_8a_058H.png` is the Growlithe this game has.
    Falling back for those fifteen would have put a *Kantonian* Growlithe on a Hisui tile, which
    is a different Pokemon rather than another generation's drawing of the same one. The coded
    names are asked for last, so Vulpix - which is drawn both ways - still gets the Kantonian
    one its Pokedex lists.
  - Two species needed a second look, and both were found by the count rather than guessed at:
    **Basculin** has no plain 550 and spells its form `W` rather than `H`, because White-Striped
    is a form of the same shape and not a regional one; and **Floatzel is drawn exactly once, as
    a female**, with no plain name and no `_m`, which is an upload the wiki is short of rather
    than a Floatzel the game is short of. That one is asked for last of all.
  - **The sheet answered a step 8 question on its own.** The form rule still hands this game 393
    forms, 37 of them Alolan or Galarian - and of those 37 the Archives drew exactly **two**:
    `vulpix-alola` and `ninetales-alola`. Which is the pair Request 83 hands over and the pair
    HOME excepts. Three sources now agree about those two and about nothing else Alolan.
  - The crop `archives.py` has done since Generation 7 worked unchanged: these arrive square and
    padded like Galar's and come out 106 to 454 pixels wide, against Galar's 140 to 895.
  - 697 pipeline tests, 259 app tests, validation 11 rules with 0 errors and the one step 8
    warning.
  - Step 7: **nothing to write, because there is nothing unobtainable here** - and that is the
    finding rather than a skipped step. Measured across the whole dataset: of the thirty-five
    games with a Pokedex, **this is the only one that produces every entry of its own**. Sword
    leaves 17 of its 821 to another game, Gold 17 of 251, Pearl 4 of 151, and every one of those
    is where step 7 does its work - turning "nothing can produce this" into "nothing you can
    play can produce this, and here is what once did". There was nothing here to turn.
  - Two things keep that from being a boast, and both are written into the module rather than
    left as a nice number:
    - **Two of the 242 need another game on the console.** Shaymin's request only appears with
      Sword or Shield save data, Darkrai's only with Brilliant Diamond or Shining Pearl save
      data. Both are a gift with a requirement rather than an unobtainable entry - the call
      Brilliant Diamond's Arceus got for the same reason in reverse - because it is a condition
      a player can still meet, unlike a distribution that closed in 2006.
    - **Three of the 242 stand on a chain step 8 has not finished.** Basculegion, Overqwil and
      Sneasler are produced by nothing here but an evolution, and each starts from a form -
      White-Striped Basculin, Hisuian Qwilfish, Hisuian Sneasel - that no record in this game
      yet names, because step 3's records name species. That is the `no-evolution-dead-ends`
      warning, found by the validator rather than by reading.
  - 698 pipeline tests, 259 app tests.
  - Step 8: **117 forms where the rule said 393, twelve sentences, and validation clean for the
    first time - 0 errors and 0 warnings.** The widest margin any game has had: 276 forms the
    rule handed over that this game does not have.
  - **The list was read off the sheet rather than argued about, and the way in was something the
    reading before these six games had written off.** That reading said the Archives' category
    pages are not a shortcut because their "next 200" is a `/w/` url the robots.txt disallows.
    True - and the same link works as a query on the `/wiki/` path the robots.txt allows. So the
    whole category came back in two requests: 367 files, one per thing this game draws, every
    number one of the Hisui Pokedex's 242 and every letter code a form.
  - What it gives: **eighteen regional forms** (the sixteen Hisuian ones plus Alolan Vulpix and
    Ninetales, and *nothing else Alolan or Galarian at all*), **eleven functional** - three
    Origin Formes, four Therian Formes, Sky Shaymin, the White-Striped Basculin and Wormadam's
    two other cloaks - twenty-seven Unown, four cosmetic, and fifty-seven sexes.
  - **One thing is deliberately left out and it is the only real judgement call in this step:
    Rotom's five appliances.** The models are in the category under this game's name, each has a
    Pokedex entry written for this game - a cauldron, a bureau, a cupboard instead of a
    microwave and a washing machine - and Bulbapedia says the forms were documented in the Hisui
    Pokedex by Professor Laventon. What nothing found says is **how a player changes one**, and
    there is no Rotom Room in Hisui. A form whose sentence cannot be written is a tile nobody
    can fill, which is the call `lets_go.py` already made. One line to add them the day somebody
    reads the mechanism, and the evidence for both sides is in the table's own comment.
  - **Twelve sentences, and eight of them are the same sentence**: this game has no held items,
    so the Griseous Orb Giratina carried in Platinum is a Griseous *Core* here and is used on it
    out of the satchel. Three for the deities, four for the Forces of Nature with Cogita's
    Reveal Glass, and the Gracidea for Sky Shaymin - which only arrives with the Sword or Shield
    save data bonus, the same bonus that makes the Shaymin request appear at all.
  - **And the reader had to change, which step 5 predicted and step 7 confirmed.** These pages
    run a form's name onto the species name - the cell reads "SneaselHisuian Form" - and step 3
    read only the link title, so sixteen species were recorded as the species and every Hisuian
    evolution started from a form nothing produced. `legends_encounters` now reads the phrase
    and a `FORM_PHRASES` table says what each one means; a phrase that maps to nothing leaves
    the record about the species, because "Plant Cloak" and "West Sea" name a default.
  - **The first table was written from the dex list page and got three phrases wrong**, and the
    reader's own warning found all three rather than a person re-reading: the location pages
    write "Trash Cloak" where the dex page writes "Plant Cloak", and they write White-Striped
    with a **non-breaking hyphen** - U+2011 - sometimes with the sex in brackets. It is spelled
    as an escape in the module so that it is visible rather than a character that looks exactly
    like the ordinary one, and ruff flagged the literal, which is how it stayed visible.
  - Two smaller things this needed. `RecordedGift` can now name a **form**: Request 83 hands
    over an *Alolan* Vulpix, and without saying so the Alolan Ninetales it evolves into starts
    from a form nothing in the game produces. It is the only gift in the dataset that names one.
    And three forms left the dataset altogether - Eternamax Eternatus, World Cap Pikachu and
    Dada Zarude - which step 1 said would happen: they were only ever here because this game's
    wrong list picked up what Sword and Shield's hand-written one had dropped.
  - **The check step 5 set passed exactly.** That step said this game should have no trade
    record left once the real form list existed, because the one survivor was the Alolan
    Graveler's rule. It has none: 140 evolutions, 102 by levelling, 34 by an item, 4 by
    something else, and not one by trading - in the only core series game with no in-game trade.
  - 1,952 records now: 1,720 wild, 140 evolutions, 69 form changes, 23 gifts. 90 of them name a
    form, and every form an evolution here starts from is one this game produces.
  - 705 pipeline tests, 259 app tests, validation 11 rules with **0 errors and 0 warnings**.
  - Step 9: **validation 11 rules with 0 errors and 0 warnings, and a collection made in the
    app with this game as its main game.** The picker offers it under Generation 8, which now
    says five games, with its box art and "Gen 8 · Hisui" under it.
  - The headless half first, against the published dataset: 242 tiles with forms off and **359
    with them all on, every one of them drawn from this game's own set and not one falling back
    to another**. 316 of the 359 are available in this game alone; nothing is explained as
    unobtainable, because nothing needs to be.
  - The linked-games step is worth a line of its own. Every older game in the dataset offers
    itself, and each one says how it would get here: "via Poke Transporter, then Pokemon HOME"
    for the Generation 5 cartridges, "via Pokemon Bank, then Pokemon HOME" for Generations 6 and
    7, "via Pokemon HOME" for the Switch games. One door, and the graph draws every route
    through it without this game naming any of them.
  - Two tiles read end to end. **Growlithe (Hisui), Fire / Rock**, with the `Spr_8a_058H` render
    and three wild records - Windbreak Stand at 41-44 and Veilstone Cape at 29-32 by walking up
    to it, and Veilstone Cape again as a swarm with "Only while an outbreak of it is running".
    And **Vulpix (Alola), Ice**, with one record: a static at Whiteout Valley reading "Request
    83, and it is the Alolan Vulpix rather than the Kantonian one the Hisui Pokedex lists".
    That one tile is the whole finding of this game.
  - Smoke test discipline kept, and checked rather than asserted. The settings file was hashed
    and backed up (D912EEA4..., 106 bytes), pointed at a scratch data file for the duration and
    **restored byte for byte** - same hash, same size. The user's own data file was hashed
    before and after: 2E5BEF75..., 4167 bytes, mtime 12:23:13, unchanged, and the collection the
    test made went to the scratch file instead. Zero instances were running before, one was
    started, and only that one was stopped.
  - 705 pipeline tests, 259 app tests.

- [x] **Legends: Z-A** (`legends-z-a`, gen 9, standalone) - 2026-09-25
  - [x] 0 **Verify against a live source first** — dex contents and HOME compatibility - 2026-09-25
  - [x] 1 Entity + edges - 2026-09-25  - [x] 2 Dex list - 2026-09-25
  - [x] 3 Wild - 2026-09-25  - [x] 4 Gifts & statics - 2026-09-25
  - [x] 5 Trades & evolutions - 2026-09-25  - [x] 6 Sprites - 2026-09-25
  - [x] 7 Events - 2026-09-25  - [x] 8 Alternate forms - 2026-09-25
  - [x] 9 Validate + smoke test - 2026-09-25
  - Step 0: **the source is there, both halves of it, and the one thing this game needed a
    verification step for turned out to be the thing the reading got right.** Nothing written.
  - **The version group is `legends-za`, not `legends-z-a`.** Order 30, generation IX, one
    version, two dexes - and `regions` is *empty*. Five of the source's thirty-two version
    groups have no region and the other four are Colosseum, XD, this game's expansion and
    Champions, none of which this dataset holds - so this is **the first game in the dataset
    whose region has to be written by hand**. The game id in this file stays as it is; only the
    source's spelling changes.
  - **Both sources agree on both dexes, to the entry.** `lumiose-city` 232, Chikorita to Mewtwo;
    `hyperspace` 132, Mankey to Zeraora - and Bulbapedia's two list pages count exactly 232 and
    132 rows. That is the first time a dex has been checked against two sources before it was
    written rather than after.
  - **The hole is total, as predicted.** Six species spread over the Lumiose dex, 11 to 33
    versions of encounter data each, and not one row for any Generation 9 version. Measured, not
    assumed.
  - **The reader Hisui forced parses this game unchanged**, and that was proved by running it:
    `legends_encounters` over the real pages gives **260 rows off twenty `Wild_Zone_N` pages,
    172 distinct species**, with nothing changed. The shape is `Pokemon | Levels | Time of day
    x2 | Weather x5`.
  - **Two times where Hisui had four, five weathers where Hisui had four to seven.** The
    header-first design was written because the weather block varies between Hisui's own areas;
    a second game now varies the *time* block too, which nothing in Hisui did. A hard-coded
    width would have been wrong here in a way no test would have caught.
  - The headings inside the tables are methods and conditions, exactly as in Hisui: nothing at
    all for the ordinary rows, `Fixed alpha Pokemon spawns`, and `Only during Main Mission 40` /
    `Only during Side Mission 017`, which are `METHOD_REQUIREMENTS` rather than methods.
  - **Forms are run onto the species name again** - `Female`, `Male`, `Meadow Pattern`, `Medium
    Variety`, `Red Flower`, `Alolan Marowak` - so `FORM_PHRASES` is needed from step 3 rather
    than discovered in step 8 the way Hisui's was. **And the phrase is sometimes the whole name
    rather than a suffix**, which Hisui never wrote: "Alolan Marowak", not "MarowakAlolan Form".
  - **172 of the 232 come out of the wild zones**, so sixty entries are steps 4 and 5's problem.
    Worth knowing before step 4 rather than at the end of it.
  - **Mega Dimension folds in, Galar-style, and that is the scope decision made rather than
    deferred.** `hyperspace` is the expansion's dex - Hyperspace Lumiose's own infobox says
    "Introduction: Legends: Z-A (Mega Dimension)" - and the source gives it a version group of
    its own, `mega-dimension`, order 31, sharing that dex. Sword and Shield already answered
    this: one entity, three dexes, three version groups. Here it is one entity and two.
  - The expansion's encounters are **eighteen pages organised by type**,
    `List_of_<Type>-type_hyperspace_wild_zones`, in the same table shape - **but the single-cell
    heading row is the zone number rather than the method**, so it names a place where every
    other Legends page names a method. That is the one reader change this game needs, and it is
    for the expansion rather than the base game.
  - **The pictures are a layer, not a sheet**: 35 files in `Category:Legends:_Z-A_models`, every
    one of them a Mega, codes M, MC, MD, MO, MS and MZ, and **not one plain number**. That is
    Ultra Sun's shape exactly - a layer over another set - and the set underneath is HOME's,
    which Brilliant Diamond already draws from. They are 670 square where HOME's are 512.
  - **And the source knows every one of them, which makes step 8 a selection rather than an
    invention**: thirty species with a new `-mega` variety, plus `absol-mega-z` and
    `garchomp-mega-z`. That is what `MZ` means - **a second, different Mega for a species that
    already had one**, which nothing in this dataset has yet.
  - **HOME: compatible since 2 April 2026, version 4.0.0, and it is a one-way door.** Only the
    Lumiose and Hyperspace dexes can be transferred in, and *nothing caught or transferred into
    this game can be sent back to any previous game*. So it is a sink: a withdrawal edge in and
    no deposit edge that leads anywhere older. The transfer-only note above predicted this in one
    line; it now has a date and a citation.
  - **`champions` is out, and for a reason rather than by omission.** The source carries it as a
    Generation IX version group with a 231-entry dex, which is what made it look like a game.
    The article says what it is: side series, battle simulation, and **Pokemon originally
    obtained there cannot be deposited in HOME at all**. Nothing is caught in it and nothing
    leaves it. That is the call Pokemon GO already gets as a game, for the same reason.
  - Step 1: **the 38th game, and the first in the dataset with a way in and no way out.** One
    edge where every Switch game before it brings two, and `legends_z_a.py` is the module.
  - **The missing half is the finding.** `home.home_edges` draws a deposit and a withdrawal
    because HOME moves Pokemon both ways with every core series game on the Switch. Not this
    one: both the game's article and HOME's own say, in the same words, that nothing transferred
    into it and nothing obtained in it goes back to a previous game. So this game does not call
    that function at all - the first that does not.
  - **And the deposit is left undrawn on purpose rather than by omission**, which is the part
    worth being careful about. A player really can put a Pokemon from this game into HOME and
    take it out again into this game; that is how two save files on one console swap anything.
    What they cannot do is take it out anywhere else - so every path the deposit opens leads
    back here, and `legends_arceus.py` already wrote the rule for that case in another context:
    a route from a game to itself is one a graph of games has nowhere to draw. Drawing it would
    not be harmless: this graph answers which games can supply an entry, so the edge would tell
    a player of Sword that a Pokemon caught here fills a tile there. The docstring says where to
    start the day a game after this one is added, because then the deposit is what connects them.
  - **`kalos.py` was written for this game three generations early, and the promise held.** That
    module's own docstring says Legends: Z-A will read from it and that nothing in it should
    have to be edited to let that happen. Step 1 asked for one thing - the region's name - and
    it was there, unedited. Hisui is written as its own region because nobody in that game has
    heard the word Sinnoh; here the name has not changed and neither has the era, so this is
    **Kalos**, the same region X and Y are set in. The city is not the region.
  - **The first game in the dataset whose id is not the source's name for it**, and the check
    that caught it was written to catch exactly this. `forms.VersionGroupGames` said in its
    docstring that a game id and PokeAPI's version name are the same string for every game here,
    and checked it rather than assuming - so the build **stopped** instead of quietly giving
    this game no forms at all. `pokeapi.VERSION_NAMES` is where the one difference now lives:
    `legends-z-a` here, `legends-za` there. Thirty-seven games and a table with one row.
  - Mega Dimension folds in as `EXPANSION`, Galar-style. The pictures are HOME's set with a
    layer of 35 Megas to come in step 6. Released 16 October 2025, everywhere on one day.
  - Step 2: **two lists, 364 entries, 364 species - and the two share nothing at all.** That is
    Galar's shape without Galar's arithmetic, and it is the first game in the dataset with more
    than one Pokedex whose lists do not overlap. Sword and Shield number a Magikarp once in
    Galar and again on the Isle of Armor, so their 821 entries are 584 species; the three Kalos
    lists overlap too. Here 232 + 132 is 364 either way you count it.
  - **The source and the wiki agree on all 364, in order, with nothing to reconcile.** Both
    numbers line up and both names do. That is a better result than Hisui's, which disagreed on
    32 rows - and the 26 rows here whose text is longer than a species name are every one of
    them the wiki naming a *default*: an Icy Snow Vivillon, a Male Meowstic, a Shield Forme
    Aegislash, an Ordinary Keldeo. The one row that looked like a real exception was Zygarde,
    and the page is showing all three formes under one number rather than choosing one.
  - **There is no leftover, and that was checked by contrast rather than by not finding one** -
    which is the only way a missing sentence can be checked. Legends: Arceus has the same
    transfer rule and a clause after it: non-Hisuian regional forms of a listed species cannot
    come in either, "with the exception of Alolan Vulpix and Alolan Ninetales". That clause is
    what `HELD_WITHOUT_BEING_LISTED` is. This game's article has the rule and stops. So Galar's
    leftover is eighty, Hisui's is two, and **this one's is nothing** - the first game with no
    National Dex whose Pokedexes really are the whole of what its boxes hold.
  - **What each list is made of, which being disjoint makes worth knowing.** The base game is
    Kalos: seventy of its 232 are Generation VI species, and there are seventy-two of those in
    the series - the missing pair being **Hoopa and Volcanion**, which are in the expansion's
    list instead. So the wiki's own line that all of Generation VI is in the base game is off by
    exactly its two Mythicals. **And exactly two of the 232 are newer than Kalos**: Drampa from
    Alola and Falinks from Galar, both of which are in the 35 Mega files step 0 read - so both
    are there because this game gives them a Mega. Nothing from Generation IX is in the base
    game's list at all, and 32 of the expansion's 132 are.
  - **Validation is one error and it is the designed one.** `every-entry-has-a-method` reports a
    game that brought no methods *once* rather than 364 times, and its own comment says why:
    that is a game that has not been worked on yet rather than one with gaps. It also counts the
    interesting number - **42 of the 364 have no source anywhere in the dataset** - and 40 of
    those are species. The two that are not are **Hoopa and Keldeo**, which every other game
    produces only as a form target, so a bare species entry for them is uncovered. Worth
    remembering at step 8 rather than rediscovering.
  - 721 pipeline tests, 259 app tests. The sprite step drew 216 new HOME renders for this game.
  - Step 3: **2,582 wild records off thirty-eight pages, and they cover 350 of the 364.** What
    is left is fourteen, and every one of them is steps 4, 5 and 7's: ten Mythicals and
    legendaries, and four that only evolve.
  - **The reader needed one change and step 0 had already named it.** On every other Legends
    page a one-cell row inside a table says *how* the rows under it are met - "Mass outbreak",
    "Fixed alpha Pokemon spawns". On the expansion's eighteen pages it says *where* they are.
    So `legends_encounters` takes a `places` table now: a heading in it names a place, a heading
    in `METHODS` names a method, and a heading in neither is passed over with a warning - which
    is what stops the footnote at the foot of each of those tables being read as an 11th zone.
  - **And it needed a second change nobody had predicted**, which the data found rather than a
    person: those pages cut themselves into sections by star rating and **number their zones
    from one again inside every section**, so Fire-type 2* Wild Zone 1 and Fire-type 5* Wild
    Zone 1 are different places with different Pokemon. The reader now reads a page in document
    order and remembers the heading above each table. Hisui's pages have exactly one heading -
    the word "Pokemon" - and nothing there uses it.
  - _A smaller trap inside that one, worth writing down because it looked right and was not: a
    css selector for several tags hands back all of one tag and then all of the next, not
    document order. The first version put every row on a page under that page's **last**
    heading, and it looked plausible until the counts were printed._
  - **Thirty-eight pages in two shapes.** Twenty `Wild_Zone_N` pages for the base game, which is
    Hisui's shape - and a location that says which district, because the whole game is one city
    and Lumiose's six districts are what Hisui's five areas were. Wild Zone 20 is not in a
    district at all: it is Centrico Plaza, the roundabout the city is built around, and it is
    the last to open. Then eighteen pages for the expansion, one per type.
  - **Four headings where Hisui needed thirteen.** No fishing, nothing shaken out of a tree, no
    space-time distortions: a Pokemon here is standing in the street and the only question is
    which street. The other three are a fixed alpha and two missions, and those are
    requirements rather than methods.
  - **Forty-eight form phrases against Hisui's sixteen, and a kind of phrase Hisui never wrote.**
    These pages sometimes write a suffix - "Red Flower", "Amped Form" - and sometimes the whole
    name over again: "Alolan Marowak", "Galarian Mr. Mime", "Heat Rotom". Most map to nothing,
    because they name a *default*; what is left is twenty-odd real forms and **nineteen of those
    belong to another region**. This game introduces no regional form of its own - the wiki says
    so and step 8 will check it - and holds more of other people's than anything since Galar.
  - **Rotom's five appliances are here, in the grass.** `legends_arceus.py` found the models
    under that game's name and a Pokedex entry for each, found nothing saying how a player
    changed one, and left them out with the evidence for both sides in a comment. This game
    puts a Heat Rotom in an Electric-type distortion at level 54.
  - **Two phrases this dataset cannot say, and they are written down rather than quietly zero.**
    A cell reading "all forms" or "All Flowers" means every one of them is there, and a record
    names one target - so those 21 rows leave the record about the species. True, and less than
    the page says. It is Flabebe's line, Vivillon and Furfrou, and **step 8 is where it bites**:
    those forms will have a tile and nothing here fills it.
  - 2,582 records, 332 species, 129 of them naming a form, over **520 distinct places** - which
    is more places than any game in this dataset has ever had. 731 pipeline tests, 259 app tests.
  - Step 4: **sixty-eight entries over sixty-seven species, which is more than any game in this
    dataset has ever needed** - and it takes the fourteen uncovered entries down to four. The
    four left only evolve, which is step 5's.
  - **A static outnumbers a gift two to one**: forty-seven standing in a spot against twenty-one
    handed over. That is this game being what it is - a city where things wait on a street
    corner rather than a region where somebody meets you at a gate.
  - **Two pages, and neither is cited for something it does not say.** One article lists every
    Pokemon this game hands over or leaves standing with its level and its place; the gift page
    is where the *condition* lives - which side mission, which NPC - and it covers only the
    gifts. So a static cites the list and a gift cites the gift page, which is the shape Hisui's
    two kinds of citation already had.
  - **The three this game starts a player with are Chikorita, Tepig and Totodile** - three
    regions and no Kalos, in a game set in Kalos. The Kalos three are here, and they are three
    separate side missions rather than a choice; so are the Kanto three, as a choice of one from
    Mable. **Four sets of first partners in one game**, which nothing else here has.
  - **Two gifts name a form**, where Hisui needed that field once: Terri's Stunfisk is the
    Galarian one and the Floette is the Eternal Flower, which is the only one there is.
  - **Nothing hatches, because nothing breeds.** The article says it in a single line -
    abilities, breeding and Eggs are not featured - so this is the third game in the dataset
    with no day care after the Let's Go pair and Legends: Arceus, and the second Legends game
    running. Written down rather than left as a `breeding_encounters` call quietly not made.
  - Two smaller things worth keeping. **Melmetal is handed over during Side Mission #193**,
    which makes this the only game in the dataset that produces one without Pokemon GO - and GO
    is still an open Phase 3 item for exactly that reason. And the **Old Amber Aerodactyl** is
    the only thing here the Stone Emporium will not sell until an earlier fossil has been
    revived, so it is a fossil behind a fossil.
  - 737 pipeline tests, 259 app tests. 2,650 records: 2,582 wild and 68 handed over or standing.
  - Step 5: **five traders, 202 evolutions, validation clean for the first time - and a bug in
    the shared evolution reader that only this game could have found.**
  - **Five NPC trades, where the other Legends game has none.** `legends_arceus.py` had to write
    down that not one NPC in Hisui will swap anything; this game puts four on the street and a
    fifth in the expansion, and **one of them is not optional** - the Pikachu for Heracross is
    part of Side Mission 002, inside Main Mission 5. Two of the five hand back the species they
    were given, a Slowpoke for a Slowpoke and a Raichu for a Raichu, which nothing else here
    does; they are in the table because leaving them out would make it a list of *useful* trades.
    And the fifth is a trade evolution a player can do alone: the Porygon comes back holding an
    Up-Grade, so what they end up with is a Porygon2.
  - **The source has exactly one evolution rule stamped with this game's name**, which was
    measured rather than guessed: of the 540 chains PokeAPI holds, one detail says `legends-za`
    and none says `mega-dimension`. It is Hisuian Qwilfish into Overqwil by using Barb Barrage
    twenty times - a Hisui evolution this game brought back, for a form its own wild tables hold.
  - **And the fallback that fills the other 201 was handing this game seven instructions a
    player here cannot follow.** The reader takes the newest way at or before a game's order, so
    Legends: Z-A - being newer than Legends: Arceus - was told to evolve Kadabra, Machoke and
    Haunter with a **Linking Cord**, and Onix, Scyther, Porygon and Porygon2 by *using* the item
    they are normally traded holding. Every one of those is Hisui's own change, and the sources
    say so in as many words: the Linking Cord's page lists Legends: Arceus as the only game it
    can be obtained in, and Kadabra's evolution chart marks it **"LA only"**.
  - **The fix is one sentence and it is about where a fact comes from.** A rule PokeAPI carries
    is the source saying "this is how it works from here", and carrying it forward is right. A
    rule in `evolutions.NOT_IN_THE_SOURCE` was typed in by a person from **one item's page in
    one game** - so it now stays in the version group it was read from. `MissingVariant`'s
    docstring said the opposite in so many words, and that sentence is now the correction.
    Seven records changed from "use a Linking Cord" to "trade it", which is what the series does
    and what this game does: Milotic's own page lists **Trade** as a Legends: Z-A game location,
    so trading here is a thing a player can do.
  - _Nothing else in the dataset moved, and that was checked rather than assumed: Legends: Z-A
    is the only game in it newer than Legends: Arceus, so it is the only one the old rule could
    ever have reached._
  - **Four rules are still another game's and are left alone on purpose**, because fixing them
    would be guessing rather than reading. `feebas-to-milotic` uses ORAS's Beauty condition,
    `mime-jr-to-mr-mime` carries a literal "in Galar", and Slowpoke's two Galarian evolutions
    want a Galarica Cuff and Wreath. All four come from PokeAPI rather than from this project's
    own table, so the sentence above does not touch them, and **all four name a species this
    game's wild tables already produce** - Milotic in the expansion, Galarian Mr. Mime, Slowbro
    and Slowking in the hyperspace zones - so no tile turns on them. Worth a reading of its own
    the day Scarlet and Violet are written, because they will meet the same four.
  - 202 evolutions: 148 by levelling, 33 by an item, 15 by trading, 6 by something else. 22 of
    them name a form.
  - 744 pipeline tests, 259 app tests, **validation 11 rules with 0 errors and 0 warnings** -
    all 364 entries covered, at step 5 rather than at step 8.
  - Step 7: **nothing to do, and the working is the point rather than the answer.** Every one
    of the 364 entries is produced by **this game** - not one is covered only by another game in
    the dataset, and not one carries an unobtainable reason. So there was nothing to turn from
    "nothing can produce this" into "nothing you can play can produce this, and here is what
    once did", and no species' *In events* section had to be opened at all.
  - **The second game in the dataset of which that is true, after Legends: Arceus - and this one
    gets there more comfortably.** Hisui had two caveats and this game has neither: Shaymin's
    request there appears only with Sword or Shield save data on the console and Darkrai's only
    with Brilliant Diamond or Shining Pearl. Searching every requirement in this game for
    another game's name, for a date, or for the word distribution turns up **nothing**. All
    twenty-four legendaries and Mythicals, Mewtwo to Zeraora, are standing in a spot or handed
    over by somebody in the game.
  - **How the 364 break down by what reaches them**: 162 by a wild slot and an evolution, 123 by
    a wild slot alone, 29 by a wild slot and a gift, 24 by a gift or a static alone - which is
    exactly that set of legendaries - 13 by all three, 7 only by evolving, and 5 involving a
    trade.
  - **And the one thing this step leaves open, stated rather than glossed over.** The checklist
    puts step 7 after step 6 because its input is the list of entries nothing produces. Step 6
    cannot change that list - a picture is not a way of obtaining anything - so running it early
    costs nothing. **Step 8 can.** Two of the seven entries reachable only by evolving start
    from a *form*: Runerigus from a Galarian Yamask and Sirfetch'd from a Galarian Farfetch'd,
    with no wild slot, gift or trade of their own. Both forms are in the wild tables today, so
    both chains stand - and `legends_z_a.STANDS_ON_A_FORM` is where that is written down, so
    step 8 knows what it must not take away.
  - 747 pipeline tests, 259 app tests, validation still **11 rules with 0 errors and 0
    warnings**. Nothing was written to the dataset, which is the right outcome for this step.
  - Step 8: **the rule gave this game 420 forms and it has 90** - a margin of 330, where
    Hisui's was 276. The fifth game running the rule is wrong about, and by now the rule being
    wrong is the expected answer rather than the finding.
  - **Most of that margin is not a judgement at all, and measuring it first is what made this
    step small.** Of the 420, only **135 are even forms of a species this game lists** - the
    other 285 belong to species in neither Pokedex, and only Pokemon in those two lists can be
    here at all. So the real question was 135 wide over 73 species, which is a list a person can
    read in one sitting.
  - **There is no sheet to read it off, which is the difference from Hisui.** The Archives keep
    367 files for Legends: Arceus, one per thing it draws; they keep **35** for this game and
    every one is a Mega. So the list is assembled from what the game's own sources say: its wild
    tables, its gifts, its evolutions, and the Game locations row on each species' article.
  - What it comes to: **sixteen regional forms, sixteen functional, seventeen cosmetic and
    forty-one sexes.** And every one of the sixteen regional forms belongs to somebody else -
    four Hisuian, four Alolan, eight Galarian. **This game introduces none of its own**, which
    the wiki states as a fact about it: the first non-remake core series game since Generation
    VII not to add a regional form.
  - **Rotom's five appliances are in this one.** `HISUI_FORMS` leaves them out because nothing
    there said how a player changes one; here nobody has to change anything - a Heat Rotom is
    standing in an Electric-type distortion at level 54 and the game's own table says so. The
    two tables now sit beside each other making opposite calls about the same five forms, each
    for a reason written down.
  - **Four things are left out and all four are the same call as Hisui's Rotom.** Hoopa Unbound,
    Resolute Keldeo, Original Color Magearna and Furfrou's nine trims each have a Pokedex entry
    written for this game - and a Pokedex entry is exactly what Hisui's Rotom had. What none has
    is a sentence saying how a player gets one: no Prison Bottle, no Secret Sword, no groomer,
    and the Game locations row for each names no form. **Seventeen of Vivillon's nineteen
    patterns are out for the same reason**, and the two that are in are in because the game
    produces them - a Garden Pattern in the wild tables and the Marine Pattern the museum's
    Spewpa evolves into.
  - **And two are out because the game removed the mechanism rather than because nobody read
    it**: abilities are not featured here, so a Battle Bond Greninja and Zygarde's two Power
    Construct formes cannot be what they are.
  - **`FORM_CHANGES` is empty, and that is the finding rather than an omission.** Legends:
    Arceus needed twelve sentences for 117 forms, eight of them an item used out of the satchel.
    Every one of this game's ninety is caught, handed over or evolved into. The table is kept
    empty rather than deleted, because "nothing here is changed into" is a claim about the game
    worth being able to point at.
  - **What this adds to the dataset is six forms**, not ninety: the table went from 400 before
    this game existed to 406, and the six are ones no other game here holds - a Roaming
    Gimmighoul, three Squawkabilly plumages and two Tatsugiri.
  - _And it tidied up after step 1. The window in which the rule gave this game every Generation
    9 form had it fetch fourteen pictures for forms nothing now holds - Paldean Tauros, the
    Ogerpon masks, Bloodmoon Ursaluna. They name nothing in the dataset and are deleted rather
    than committed._
  - **Step 7's one open question is closed**: both forms `STANDS_ON_A_FORM` names survived, so
    Runerigus and Sirfetch'd are still produced and nothing became unobtainable.
  - 754 pipeline tests, 259 app tests, full build **11 rules with 0 errors and 0 warnings**.
  - Step 6: **364 species and 89 of the 90 forms drawn from Pokemon HOME's own set** - and the
    work was not fetching anything. Every picture was already on disk from steps 1 and 2. The
    work was teaching the namer how HOME spells a form.
  - **The comment that had to be deleted had been waiting since Brilliant Diamond.**
    `archives.form_names` returned a name for a female and nothing at all for any other form of
    the HOME set, with a comment saying that HOME's way of spelling a form was not read yet and
    that nothing wanted it. True for as long as the games drawing from this set named no forms
    between them. **This game names ninety.**
  - **Read off the category rather than guessed at, on a category nine times Hisui's.** HOME's
    artwork is 3,126 files and every code in it belongs to one kind of form. Three of the codes
    are the sheets' own letters a fourth time - `A` Alola, `G` Galar, `H` Hisui - and the rest
    are HOME's, including three that are two letters where a sheet uses one: `La`, `Sm` and `Su`
    for a Gourgeist's size. Twenty-six codes cover all ninety.
  - **Every code was checked against the file's own description page, and Rotom is where that
    paid.** Its five appliances are `F`, `L`, `O`, `R` and `W`, and only the pages say that `O`
    is the oven and `L` is the lawnmower. **Guessing alphabetically would have put a washing
    machine on the microwave's tile** - which is the Generation 7 `7p` lesson applied before it
    could cost anything instead of four hours afterwards.
  - _And the same letter means two things, which is why the table is keyed by a form's name and
    not by a letter: `L` is the lawnmower on a Rotom and Low Key on a Toxtricity, and `W` is the
    washing machine, the White Flower and the White Plumage._
  - **The category was wrong once, and the build is what caught it.** Reading it said
    `HOME0710Sm.png` was missing and that the Small Size Pumpkaboo would fall back - and asking
    for it returned a picture. The file is there; the category does not list it. **A category is
    a good index and not a complete one**, which is worth knowing before the next game trusts
    one. So `HOME_HAS_NO_PICTURE` holds what a build found rather than what the category said,
    and it holds one thing: Torchic's female, whose `HOME0255_f.png` does not answer.
  - **And the 35 Mega models are not used at all, which is not a gap.** `Spr_9z` draws Mega
    Starmie, Mega Clefable and 33 others - and a Mega is not a form in this dataset, because
    `forms._form` refuses anything the source marks `is_mega`, the same sentence that keeps
    every Gigantamax out. A Mega reverts when the battle ends and a living dex is about what a
    box can hold. **So the game about Mega Evolution contributes no tile that a Mega goes on**,
    by a rule written three generations before it for exactly this reason.
  - 757 pipeline tests, 259 app tests, full build **11 rules with 0 errors and 0 warnings**.
  - **And registering it moved `forms.json` before this game has a single Pokedex entry, which
    is expected rather than a fault.** Until step 8 switches the version-group rule off, that
    rule hands this game every form that arrived in Generation 9 or earlier: **420 of the 430 in
    the table**, and it pulled in a set of Generation 9 sprites nothing had asked for yet -
    Paldean Wooper, Ogerpon's masks, Squawkabilly's plumages. This is the same rhythm Legends:
    Arceus ran through with 393, and the number is here so step 8 can be checked against it.
  - 715 pipeline tests, 259 app tests, full build **11 rules with 0 errors and 0 warnings**,
    and 143 routes where there were 142 - one where every Switch game before it added two.
  - Step 9: **validation 11 rules with 0 errors and 0 warnings, and a collection made in the
    app with this game as its main game.** The picker offers it under Generation 9, which says
    one game, with its box art and "Gen 9 - Kalos" under it.
  - The headless half first, against the published dataset: **232 tiles with forms off and 290
    with all four kinds on, every one of them drawn from this game's own set and not one falling
    back to another.** Nothing is explained as unobtainable, because nothing needs to be.
  - **256 of the 290 are available in this game alone, and the 34 that are not are all forms and
    not one is a species** - which is the whole of step 7 restated by the app's own availability
    rule rather than by the validator.
  - **The routes read the way step 1 drew them: one edge in, none out.** The linked-games step
    offers every older game in the dataset and each one says how it would get here - "via Poke
    Transporter, then Pokemon HOME" for the Generation 5 cartridges, "via Pokemon Bank, then
    Pokemon HOME" for Generations 6 and 7, "via Pokemon HOME" for the Switch games. One door,
    and nothing offers a way back.
  - **One tile read end to end, and it is the one that proves steps 3, 6 and 8 at once.**
    Vivillon (Garden), Bug / Flying, with its own HOME render, and five wild records reading
    "Hyperspace Lumiose, Bug-type, 1* Wild Zone 2", "walking up to it", levels 15-17, cited to
    bulbapedia read 25 September 2026. The three-part place the expansion needed reads as a
    sentence in the popup rather than as a string with commas in it.
  - Marking it caught moved the counter to **1 of 290** and wrote one record naming
    `vivillon-garden` with `holdingGame: legends-z-a`.
  - **And the smoke test found something that is not this game's fault, which is what a smoke
    test is for.** The grid shows **the first of a game's Pokedexes and offers no way to the
    others unless the game also has a National Dex**: `CollectionGrid.BothDexesExist` requires
    `HasNationalDex: true` before it renders the switch at all. This game has no National Dex
    and two lists, so **132 of its 364 entries - the whole Hyperspace Pokedex - cannot be shown
    in the app**. Sword and Shield have the same shape and lose 184 of 584 the same way, which
    `galar.DEXES` describes as being "behind the switch" - and the switch is not there. The
    dataset is right and the app cannot show all of it. It is a Phase 3 item now.
  - Smoke test discipline kept, and checked rather than asserted. The settings file was hashed
    and backed up (D912EEA4..., 106 bytes), pointed at a scratch data file for the duration and
    **restored byte for byte** - same hash, same size. The user's own data file was hashed
    before and after: 2E5BEF75..., 4167 bytes, mtime 12:23:13, unchanged, and the collection the
    test made went to the scratch file instead. Zero instances were running before, one was
    started, and only that one was stopped.
  - 757 pipeline tests, 259 app tests.

### A game with several Pokedexes and no National Dex could only show the first of them - 2026-09-25

_Found by Legends: Z-A's step 9 rather than by Galar's, although Galar has had it since Galar.
`CollectionGrid` asked whether the game had a National Dex before it drew the dex switch at all,
which is the right question for Diamond - 493 entries and a Sinnoh Pokedex of 151 - and the
wrong one for a game whose several lists have no National Dex above them. Those games got no
switch, so the grid showed the first of their lists and offered no way to the others._

_**What it cost, which is the part that was invisible: 132 of Legends: Z-A's 364 entries - the
whole Hyperspace Pokedex - and 184 of Sword and Shield's 584.** `galar.DEXES` describes those
184 as being "behind the switch". The switch was not there._

_The question moved out of the page and into the dataset, where it can be tested:
`ReferenceData.DexChoiceCount` counts the lists a player can choose between - the game's own,
plus the National Dex when it has one - and the grid draws the switch when that is more than
one and offers the National Dex option only when there is one. A game that names no list still
has one, which is the twenty games written before a dex needed a name._

_One smaller thing fixed with it: the switch started on nothing. `ChosenView` read the chosen
list, which is empty until a player chooses, where the builder reads "the first this game
names". Now they agree, so the select opens on the list that is actually on screen._

_Checked in the app on the published exe: the switch reads **Lumiose dex** and **Hyperspace
dex** with no National Dex option, and switching to the second draws **164 tiles** that could
not be reached before - Mankey to Rotom, with Meowth's two regional forms and Rotom's five
appliances among them, every one with its picture. 757 pipeline tests, 261 app tests._
