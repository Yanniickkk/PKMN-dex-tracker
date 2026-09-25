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

_Done: all six. Sun, Moon, Ultra Sun and Ultra Moon are the four Alola cartridges; Let's Go,
Pikachu! and Let's Go, Eevee! are Kanto on a home console, and everything the six reach is in
`DONE dex tracker.md`._

_What Alola shares is in `alola.py`, which is the region module and the generation's both - for
the reason that file gives about Let's Go. What the two Let's Go games share is in `lets_go.py`,
which is neither: they are Kanto without being `kanto.py`'s, and a Switch module would have been
a file those two sat in alone. **Every route this generation declares now has both of its
ends**, and Generation 8 is what opens the graph again._

### Generation 8

_Done: Sword and Shield, which are Galar and the first Pokedex in the series that does not have
room for everything. What they share is in `galar.py`, which is the region module and the pair's
both: Generation 8 is those two in Galar, Brilliant Diamond and Shining Pearl in Sinnoh and
Legends: Arceus in Hisui, and what the five have in common is Pokemon HOME, which `home.py` has
held since before any of them existed. There is nothing left for a `gen8.py` to say._

_**Every route this pair declares has both of its ends**, and it declared them into a graph that
was already waiting: HOME is the only door Generation 8 has, so nothing older had to be touched
to let a Pokemon caught in Red reach Galar._

No National Dex either, and unlike Generation 7 these games cannot hold what is not in their own
list — step 2 uses the game's own dex, DLC included, and `nationalDexThrough` stays empty. Sword
and Shield answered that with three lists kept apart and eighty species left out of all of them;
whichever of the three remaining pairs comes next should read `galar.FOREIGN_TO_EVERY_DEX` before
assuming its own dex is the whole of what its boxes hold.

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



### Generation 7's pictures - 2026-09-24

_Done, and it cost a quarter of what the two items it replaces budgeted. The four Alola
cartridges draw from `generation-vii/alola`: **927 pictures, 8.4 MB, 240 pixels square**, off
the Bulbagarden Archives._

_**The plan was wrong about which sheet was which, and reading the source first is what caught
it.** Both items said `7p` was Ultra Sun and Ultra Moon. It is not: the description page for
`Spr_7p_019A.png` files it under *Let's Go, Pikachu! and Let's Go, Eevee! models*, and that is
where the 800-pixel, 52-kilobyte pictures came from. Ultra Sun and Ultra Moon are `7u`. A
scrape that had trusted the number would have given Alola a sheet drawn from the wrong games,
ten times the size, and nothing about the result would have looked wrong._

_**Ultra Sun and Ultra Moon have no sheet of their own**, which is the other half of why four
hours became one. Their category holds 409 files against Sun and Moon's 1949, and what is in it
is what those two added: Dusk Mane, Dawn Wings and Ultra Necrozma, Dusk Form Lycanroc, the
Partner Cap Pikachu. Everything else in Ultra Sun is the picture Sun already had. So `7u` is
laid over `7s` in one folder rather than standing beside it as a second sheet, and four games
share what is nearly one._

_**A name is a rule, not a list, for all but a hundred and thirty of them.** The number is three
digits; a species drawn differently by sex has `_m` and `_f` and no plain name, and one drawn
once has nothing else. Which of those two to ask for first is not a guess - a species drawn
twice is exactly one this dataset already holds a `-female` form for. Every one of the 802
answered on the first name tried. Unown's letters, Vivillon's patterns and Arceus's types have
codes that follow nothing and would each have to be read; those keep the shared set's picture of
the form, which is the right Pokemon in another generation's style._

_Two things the fetching found rather than the planning. **The five past 802** - Poipole,
Naganadel, Stakataka, Blacephalon and Zeraora - answered to nothing until they were asked for
under `7u`, which is right: Sun and Moon never drew them. And **Eevee has a female in PokeAPI
and one picture on this sheet**, so offering both spellings turned a disagreement between two
sources into one wasted request instead of a hole._

_**Totem forms and Own Tempo Rockruff have no file at all**, checked rather than assumed._

_**And they arrived padded, which is the one thing that had to be undone.** These are the only
sprites in the dataset that come in a fixed frame: every Generation 7 Pokemon is centred in 240
pixels at its true size against the others, so a Wailord fills three fifths of it and a Pikachu a
quarter. The drawing inside is the same 60 pixels across as the Generation 6 Pikachu, which comes
with no padding at all - so in a 56 pixel tile, `object-fit: contain` drew Alola's Pikachu at
fourteen pixels beside Kalos's at fifty-six, and the whole generation looked shrunken. The
relative sizing is real information and no other sheet here carries it, so it comes off at build
time: Pillow, one call, cropped to what is drawn. The sheet went from 8.4 MB to 6.8, and every
picture now fills its own frame the way the other twenty-eight sheets do._

_The md5 path rule holds, so no description page is read and the fetching is halved. The
category pages are not the shortcut they look like: their next 200 is a `/w/` url, which the
Archives' robots.txt disallows. 77 minutes of fetching, paid once - a build that already has the
pictures opens no client at all, and the app needed no change, because the dataset cannot tell
where a folder of pictures came from._


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
  - And a third case, met by step 4 of the Let's Go pair: the **GO Park** is the same question
    inside one pair of games rather than at the hub. It is the only source of Meltan and
    Melmetal anywhere in the dataset, and those two carry a reason saying so - which is the
    holding answer the Radar's three already have. Three cases now wait on one decision.
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