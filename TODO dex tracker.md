# Living Dex Tracker — Implementation TODO

Companion to the specification. Work top to bottom: Phase 0 and 1 build the machine,
Phase 2 feeds it one game at a time.

## How this file works

- **Every version is its own game entity.** Red and Blue are two entities, not one
  "Red/Blue" row. Same for Gold/Silver, Sword/Shield, Scarlet/Violet, and every other pair.
  Version exclusives are the whole reason this matters.
- **Phase 2 is the repeating part.** Each game has the same 9-step checklist. A game is
  "done" when all 9 are ticked and its validation run is green.
- **Games are independent.** Adding Emerald must not require touching Platinum's data.
  Anything shared belongs in Phase 0, not in a game's data file.
- Tick boxes as you go. Add notes inline under a step when something is unusual.
- **Finished items move out.** When an item is done, cut it from this file and paste it
  into `DONE dex tracker.md` under the matching section, ticked and dated. That file
  explains the exact shape. Partial work stays here until every sub-step is done.

---

## Phase 0 — Foundations (no game data yet)

### 0.1 Project setup
- [ ] Windows build target: installer or portable exe, verified to run on a clean machine
  - `publish/LivingDex.exe` is a single self-contained file, verified to run from an empty
    folder with nothing beside it. Still open: a Windows install without the WebView2
    Runtime, and a Windows 10 box.

---

## Phase 1 — First vertical slice

_Done. The slice works end to end; what it is short of is game data, which is Phase 2._

Build the whole app against two games before scaling the data out.
Target: **Platinum** as main game, **Emerald** linked.


---

## Phase 2 — Games, one at a time

### The per-game checklist

Every game below repeats these 9 steps:

1. **Entity + edges** — register the game, its metadata, and its transfer edges in both directions
2. **Dex list** — which species and forms it contains, and their numbering in this game
3. **Wild** — every encounter slot: location, sub-area, method, level range, rate, time, season, weather
4. **Gifts & statics** — starters, fossils, revives, NPC gifts, eggs, legendary statics
5. **Trades & evolutions** — in-game NPC trades, which evolution triggers are actually
   possible here, and the babies only the day care produces
6. **Sprites** — battle sprites for this generation, or the documented fallback
7. **Events** — for every entry still marked unobtainable, find out whether a distribution event
   ever handed one out, and say so in its reason
8. **Alternate forms** — which of this game's forms it actually has, how each one is come by,
   and a picture of each from this game's own sheet
9. **Validate + smoke test** — validation green, then create a collection with this game as main game

Step 7 can only run once steps 1 to 6 are done: its input is the list of entries nothing in the
game produces, and that is not known before. It does not change what is obtainable — an event you
had to attend in 2006 is not a way to fill a dex today — it changes the answer a player gets, from
"nothing can produce this" to "nothing you can play can produce this, and here is what once did".
The place to look is the species' own *In events* section on Bulbapedia, which lists the games
each distribution was for.

Step 8 is new, and the first five generations did not have it: their forms were filled in one
pass afterwards, as Phase 0.8 and 0.9 in `DONE dex tracker.md` describe, because twenty games had
already been written by the time the table existed. From Generation 6 on it is part of writing a
game, and it has to be, because that is where forms stop being a curiosity — Mega Evolution, then
the regional forms, then Gigantamax. Three things belong to it:

- **Which forms this game has.** `forms.py` works most of it out from the version group a form
  arrived in, and what it cannot know is a form that arrived and went no further, or one that is
  in the generation and not in this half of it.
- **How each one is come by.** A form is not caught, handed over, hatched, traded or evolved: it
  is changed into, and the answer is one sentence — use the Reveal Glass, fuse it with the DNA
  Splicers, hold a Mega Stone. That is a table in the game's own module, like its gifts.
- **A picture of each.** The sprite step fetches these, and a form the sheet never drew falls
  back to its species.

Validating and smoke testing stay last, because they are the step that says the game is finished:
they should be looking at the final data, reasons included, rather than at a version of it that is
about to be edited.

Order to work in: start with Gen 3 and Gen 4 (already partly done in Phase 1),
then Gen 1–2, then forward through Gen 5 onward.

### Generation 1

_Done: all three. Red, Blue and Yellow are Kanto on the 3DS._

**Virtual Console only.** Generations 1 and 2 are in this dataset as their 3DS Virtual Console
releases and not as the cartridges. A Game Boy cartridge trades with another Game Boy cartridge
and reaches nothing else, so what is caught on one can never join a living dex kept anywhere
later; the Virtual Console releases can, through Poké Transporter into Bank, and that route is
the whole reason they are here. The same decision governs Generation 2 below.

_What Kanto shares is in `kanto.py`, what Generation 1 shares is in `gb.py`, and what every
Virtual Console release shares is in `vc.py`. Twelve edges are waiting: each of the three opens
a Time Capsule with each of Gold, Silver and Crystal, and each reaches Bank._

### Generation 2

_Done: all three. Gold, Silver and Crystal are Johto on the 3DS, and everything they reach is in
`DONE dex tracker.md`._

_What Johto shares is in `johto.py`, what Generation 2 shares is in `gbc.py`, and what every
Virtual Console release shares is in `vc.py`. **Every Time Capsule is lit and every trade is
made: the six waiting edges all point at Bank.**_

### Generation 3

_Done: Ruby, Sapphire, Emerald, FireRed and LeafGreen. All five are in `DONE dex tracker.md`._

### Generation 4

_Done: all five. Diamond, Pearl and Platinum are Sinnoh; HeartGold and SoulSilver are Johto._

_What the Sinnoh games share is in `sinnoh.py` and what the Johto ones share is in `johto.py`;
what every Generation 4 cartridge shares - the wireless trading between all five, the National
Dex to 493, Pal Park out of the slot underneath - is in `ds.py`._

### Generation 5

_Done: all four. Black and White are the pair, Black 2 and White 2 the sequels, and everything
they reach is in `DONE dex tracker.md`._

_What all four share is in `unova.py`, which is also the region module: Generation 5 never left
Unova, so the hardware-and-region split `ds.py` explains has nothing on either side of it. **The
whole cartridge chain is closed: every route between two games in this dataset now has both of
its ends, and the ten edges still waiting all point at Bank.**_

### Generation 6

_Done: all four. X and Y are Kalos, Omega Ruby and Alpha Sapphire are Hoenn again, and
everything they reach is in `DONE dex tracker.md`._

_What Kalos shares is in `kalos.py` and what Hoenn shares is in `hoenn.py`; what every
Generation 6 cartridge shares - the trades between all four, the National Dex to Volcanion, and
Pokemon Bank where the Poke Transfer used to be - is in `gen6.py`. **The four edges X and Y
declared into an empty space are lit; the fourteen still waiting all point at Bank.**_

### Generation 7

**These four have no National Pokedex** — the first games since Generation 2 without one, and
Bulbapedia counts it as the first since it was introduced at all. The Rotom Dex shows Alola's
302 and nothing else; the National list a player used to read in the game moved to Pokemon Bank.
Decided anyway, by Yannick: a living dex here is everything the boxes can hold, so the entities
carry 802 and Ultra Sun and Ultra Moon carry 807. The Alola list is step 2's, as the game's own
dex, and the grid can be switched to it.

**Two dexes, and the second is not the first with more at the end.** Alola is 302 entries in Sun
and Moon and 403 in Ultra Sun and Ultra Moon, and the 101 added are scattered through the list
rather than appended: the numbering parts company at #024 and most of what follows disagrees.
`alola.py` keeps `SM_DEX` and `USUM_DEX` apart so neither can quietly become "the" dex.

_Done: Sun, Moon, Ultra Sun and Ultra Moon - all four Alola cartridges, and everything they
reach is in `DONE dex tracker.md`. The two Let's Go games are what is left of this generation._

_What Alola shares is in `alola.py`, which is the region module and the generation's both - for
the reason that file gives about Let's Go. **Every route the four cartridges declare now has
both of its ends**, and the graph is closed until Let's Go opens it again._

- [ ] **Let's Go, Pikachu!** (`lets-go-pikachu`, gen 7, pair partner: Let's Go, Eevee!)
  - [x] 1 Entity + edges  - [x] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Events
  - [ ] 8 Alternate forms  - [ ] 9 Validate + smoke test
- [ ] **Let's Go, Eevee!** (`lets-go-eevee`, gen 7, pair partner: Let's Go, Pikachu!)
  - [x] 1 Entity + edges  - [x] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Events
  - [ ] 8 Alternate forms  - [ ] 9 Validate + smoke test
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

### Generation 8

No National Dex either, and unlike Generation 7 these games cannot hold what is not in their own
list — step 2 uses the game's own dex, DLC included, and `nationalDexThrough` stays empty.

- [ ] **Sword** (`sword`, gen 8, pair partner: Shield) — base + Isle of Armor + Crown Tundra
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Events
  - [ ] 8 Alternate forms  - [ ] 9 Validate + smoke test
- [ ] **Shield** (`shield`, gen 8, pair partner: Sword) — base + Isle of Armor + Crown Tundra
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Events
  - [ ] 8 Alternate forms  - [ ] 9 Validate + smoke test
- [ ] **Brilliant Diamond** (`brilliant-diamond`, gen 8, pair partner: Shining Pearl)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Events
  - [ ] 8 Alternate forms  - [ ] 9 Validate + smoke test
- [ ] **Shining Pearl** (`shining-pearl`, gen 8, pair partner: Brilliant Diamond)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Events
  - [ ] 8 Alternate forms  - [ ] 9 Validate + smoke test
- [ ] **Legends: Arceus** (`legends-arceus`, gen 8, standalone)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Events
  - [ ] 8 Alternate forms  - [ ] 9 Validate + smoke test

### Generation 9

- [ ] **Scarlet** (`scarlet`, gen 9, pair partner: Violet) — base + Teal Mask + Indigo Disk
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Events
  - [ ] 8 Alternate forms  - [ ] 9 Validate + smoke test
- [ ] **Violet** (`violet`, gen 9, pair partner: Scarlet) — base + Teal Mask + Indigo Disk
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Events
  - [ ] 8 Alternate forms  - [ ] 9 Validate + smoke test
- [ ] **Legends: Z-A** (`legends-z-a`, gen 9, standalone)
  - [ ] 0 **Verify against a live source first** — dex contents and HOME compatibility
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Events
  - [ ] 8 Alternate forms  - [ ] 9 Validate + smoke test

### Transfer-only nodes

_Both are built. Nothing is held back: for the first time since this dataset held one game,
every route any entry declares has both of its ends in it._

_What the two of them left for the games above, so it is read before those games are written:
`bank.bank_edges` and `home.home_edges` each give a deposit and a withdrawal as two one-way
edges, because in both cases the service hands back less than it takes. Three Switch pairs do
**not** get `home_edges` and each needs its own answer - Let's Go only takes back what started
there, Legends: Z-A gives nothing back to anything older, and Pokemon GO and the Switch FireRed
and LeafGreen send one way into HOME and are not games this dataset holds._

_The Virtual Console releases used to be a separate job at the end of this list. They are not:
they **are** Generations 1 and 2 here, built in their place above, and the cartridges are not in
the dataset at all._

---

## Phase 3 — Polish

### Build time — 2026-09-24

_Done. A full build went from the best part of an hour to **45 seconds**, and a single-game
build from minutes to six seconds._

_The cache was never the problem: of the 8415 sprite requests a build makes, 8410 were already
on disk. What cost the time was touching the same files over and over. A build asked for the
same document dozens of times - five separate readers want `pokemon-species/shellos` while one
game is being written, and all 28 games want it again - and each of those was a file read and a
JSON parse. Over three games, 12484 reads were 2644 distinct documents._

_An LRU was simulated before it was written, which changed the design: the re-reads are not
close together in time, so holding 256 entries saved 1% and only holding the whole working set
saved 79%. So `MemoryCache` is sized in bytes rather than entries - a location is a few hundred
bytes and a Pokemon with its moveset is forty kilobytes - with a 192 MB budget against a 375 MB
cache. A full build now reads each URL off disk exactly once: 15518 disk reads against 15543
distinct urls, and 81462 reads served from memory._

_Two smaller things. A 404 is now remembered, because a sheet only draws what its generation
drew and `_first_picture` finds a form by asking for several names until one answers - so a
build asks for pictures that are not there, and used to ask again every time. Only 404 and 410:
a 500 or a timeout is about the moment rather than the url, and writing one down as "no" would
put a permanent hole in the dataset over a blip. And a sprite is compared before it is written,
so a rebuild that changes nothing leaves 8211 files and their timestamps alone - the summary
says "wrote 92 file(s), 8211 already current" rather than claiming credit for all of them._

_The build now prints its own timings, which is how any of this was found: every phase turned
out to be seconds with a warm cache and minutes with a cold one, which is a different problem
from the one it looked like._



- [ ] A hand-written table's citation should carry the day a human read the page
  - The fetched half is done: a PokeAPI citation now takes its date from the cache entry the
    answer came out of, so a rebuild from unchanged pages no longer re-dates 27,000 records
    with the build day. What is left is the 209 records whose source was read by a person and
    typed in - the in-game trades, the day care, the Bug-Catching Contest, the Karate King -
    because there is no fetch to take a date from.
  - Two ways to do it. Either each game module declares when its tables were read
    (`READ_ON = date(...)`, passed to `bulbapedia(...)`), or the build actually fetches the page
    it cites and lets the cache answer, which is honest but makes the build depend on a page it
    does not read. The first is simpler and does not pretend.
  - A third way turned up at Black 2's step 3 and is worth weighing before the other two:
    `grottoes.py` reads its page instead of citing it from memory, and its dates come out of the
    cache for free. That only works where the page is uniform enough to parse, which is not most
    of the 209 - but a table that is worth parsing never joins the queue in the first place.

- [ ] Generation 7's pictures from a source that has them
  - Step 6 for Sun and Moon found that PokeAPI's sprite repository has a folder of battle
    sprites for every generation from the first to the sixth and none for the seventh - not for
    these two and not for Ultra Sun and Ultra Moon, whose URL it publishes and whose file it does
    not have. So all four carry no `sprite_set` and draw the shared set. That is the right
    fallback and a poor ending: they would be the only games in the dataset never shown in a
    picture of their own.
  - Three candidates, and the cheapest is already refused. The same repository has
    `versions/generation-vii/icons`, which is box icons - a different kind of picture from the
    battle sprites every other game shows, and one grid holding both would look like a fault.
  - The second is `other/home`, in that same repository and so needing no new host, no robots.txt
    and no politeness budget: renders of the very models Generation 7 used, one per species and
    per form, Alolan Rattata included. Two honest costs. They are Pokemon HOME's renders rather
    than these games' own, so a sheet built from them would be a *style* that suits Generation 7
    rather than a picture Sun took; and they are 512x512 and 80-90 KB each against the 96x96 and
    under a kilobyte of everything the dataset holds now, so roughly 800 of them is some 70 MB
    against today's 1311 files. Whether they go in the repository at that size, or are scaled on
    the way in, is the first thing to settle.
  - The third is Bulbapedia's Archives, which the pipeline can already read politely and which
    has the games' own artwork. At five seconds a request that is over an hour for one sheet,
    and it is the only one of the three that would actually be Sun and Moon's picture.
  - Whatever is picked, nothing about how a picture is chosen has to change: `SpritePath` already
    tries a sheet's form, a sheet's species, the shared form and the shared species in that
    order, so a Generation 7 sheet is a constant in `alola.py` and a fetch, and the tiles follow.

- [ ] Scrape Generation 7's sprites from the Bulbagarden Archives
  - The work the item above leaves open, now that the source has been read properly rather than
    estimated. Three things came out of it and two of them change the plan.
  - **The file names are not a rule.** The guess was `Spr_7s_<number>.png`, and that is not what
    is there: a Generation 7 sprite carries a sex suffix, so Pikachu is `Spr_7s_025_m.png` and
    `Spr_7s_025_f.png` and there is no plain `Spr_7s_025.png` to fetch. Alolan forms take a
    letter instead - `Spr_7s_019A.png` for Alolan Rattata - shinies take `_s`, back sprites take
    a `Spr_b_` prefix, and the Partner Cap Pikachu is `Spr_7p_025P_m.png`. Guessing a name costs
    five seconds per miss, so the names have to be **read** rather than constructed: each
    species' own page lists every sprite it has, for both sheets and all forms, in one request.
  - **There are two sheets and they are not the same pictures.** `7s` is Sun and Moon, `7p` is
    Ultra Sun and Ultra Moon, and the same Pokemon differs by a factor of ten in size:
    `Spr_7s_019A.png` is 5 KB and `Spr_7p_019A.png` is 52 KB. So "one Generation 7 sheet" is not
    on offer, and which of the two to use - or whether to take both - is the first decision.
  - **What it would cost**, at the five seconds a request the Archives ask for:
    - ~800 species pages to read the names from: about 70 minutes.
    - 1075 pictures for the first pair's sheet and 1126 for the second: about 90 minutes each.
    - So roughly **four hours for both sheets**, or two and a half for one.
    - On disk: the `7s` sheet is about 5 MB and the `7p` sheet about **60 MB**, against the 11 MB
      the whole sprite set weighs today. The cheap sheet is the one for the games that came
      first.
  - The MD5 path rule holds and saves the other half of the fetching: a file at
    `/media/upload/<md5[0]>/<md5[0:2]>/<name>` needs no description page read first. Verified on
    four names.
  - Yannick asked for this to be a separate item, and it should be run as a background job that
    only warms the HTTP cache and writes nothing into `dataset/` - which makes it restartable,
    keeps it off the dataset's writer, and lets the sheet be wired in afterwards with one
    ordinary build. It must not run while a build that touches the Archives is running: the
    five-second budget is per process, so two of them would halve the interval the site asked
    for.
  - **The four hours are paid once, by whoever runs it, and never again by anybody.** Yannick
    asked how often this would have to happen, and the honest first answer was "once, unless
    someone builds on a machine with a cold cache" - because the pipeline asked the source for
    every picture on every build and it was the HTTP cache under `pipeline/.cache` that made
    that free. That cache is gitignored and 559 MB; `dataset/sprites` is committed and 11 MB.
    The cheap one was the one that did not travel.
  - Fixed before the scrape rather than after it, because it is the scrape that makes it matter:
    a build now skips the fetch entirely when the picture is already in the dataset, and
    `--refresh` is the only thing that overrides it. A full build reports **8248 pictures
    already in the dataset and never asked for**, its sprite phase takes a second and its box
    art phase none, and the dataset comes out byte-identical. So a fresh clone costs nothing for
    pictures, and the Generation 7 sheet costs four hours exactly once.

- [ ] Multiple collections: list, switch, rename, delete
- [ ] Editing a collection's settings after creation, records preserved
- [ ] Dataset version and build date shown somewhere in the UI
- [ ] Unobtainable entries handled per the decision in the spec's open questions
- [ ] Keyboard navigation through the grid and popup
- [ ] Empty and error states: no dataset, corrupt data file, cloud file locked
- [ ] Export a collection to CSV
- [ ] Collections list can be filtered on main game, name
- [ ] Pokemon GO as a one-way source into HOME
  - Turned up while HOME was being written, and it is the Dream Radar's problem again with a
    bigger source: GO sends into HOME one way, some of what it sends has no other route, and it
    is not a game in the sense used here - no Pokedex to fill, and nothing is caught in it the
    way this tracker means. So it is neither an edge between two games nor an NPC with a gift.
  - Whatever shape the Radar gets should fit this too, which is a reason to decide the two
    together rather than one at a time.
- [ ] Decide what the Switch releases of FireRed and LeafGreen are
  - They send one way into HOME from October 2026, which makes them the first things since the
    3DS Virtual Console releases that can reach a living dex kept anywhere later.
  - The same decision Generation 1 needed: this dataset holds one `firered`, the Game Boy
    Advance cartridge, and it reaches Pal Park and stops. A Switch FireRed would be a third
    entity beside it and the 3DS release - or the two would be one entry with two ways out, which
    is what the Virtual Console decision refused to do.
- [ ] The Pokemon Dream Radar as a source for Black 2 and White 2
  - A 3DS app rather than a game: no dex of its own, nothing caught in it, and it sends one way
    into those two and nowhere else. So it is neither a transfer edge nor an NPC with a gift,
    and it needs a shape of its own - a source that is not a game, which nothing in the dataset
    is yet. What it is worth is that some of what it sends has no other way in.
  - Not the Dream World, and not by oversight: that was a website, it closed in 2014, and a
    player starting today cannot reach any of it. The Radar is still runnable by whoever has it.
  - Worth saying in the reason a player reads: the eShop it came from shut in 2023, so it is
    ownable rather than buyable. That is a different answer from "this cannot be done".