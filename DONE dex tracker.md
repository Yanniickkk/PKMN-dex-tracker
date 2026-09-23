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

_Nothing yet._

### Generation 8

_Nothing yet._

### Generation 9

_Nothing yet._

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
