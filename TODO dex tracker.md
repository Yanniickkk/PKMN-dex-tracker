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

_**Done: forty entities, and every one of them has all nine steps ticked.** Thirty-eight games
and two nodes; 143 routes became 148 when the last pair arrived, and every route any entry
declares has both of its ends in the dataset. What is left of this project is Phase 3._

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

### The last six games, read before any of them is written — 2026-09-25

_A reading rather than a step. The six games left share four questions, and answering them once
is cheaper than meeting each of them six times: the answers change each other, and two of them
change which game should go first. Nothing here is code._

**Every one of these games needs a source for step 3 that is not PokeAPI.** Measured rather than
assumed: `sprigatito` and `lechonk` have no encounters at all, `bidoof` has seven versions and
none of them is `brilliant-diamond`. The bare fact is that the source stops at Sword and Shield.
That is not new - `encountertables.py` exists because Omega Ruby and Alpha Sapphire had the same
hole - but from here it is the rule instead of the exception.

- **Brilliant Diamond and Shining Pearl need no new reader at all.** Sinnoh Route 201 carries a
  second table under its own heading, shaped `Pokemon | Games | Location | Levels | Rate` with
  **BD** and **SP** in the games column - which is exactly what `table_encounters` already
  parses, and exactly what `column=` is for. Swarms are a heading inside it, the way tides and
  floors already are elsewhere.
  - _**Half right, and the half it got wrong is worth carrying to the other three.** The page
    shape was the one the reader already parses. Two things in the reader were not: the pair of
    letters in the Games column was written in as `("OR", "AS")`, and a Generation 8 grass table
    splits its rate column three ways under a morning, a day and a night icon with no text at
    all - which only the header row shows. Both are fixed and both are general, so whoever
    writes Scarlet and Violet should look at the header before trusting a row._
- **Legends: Arceus and Legends: Z-A share one new reader, and it is a small one.** Neither has
  a rate and neither has a games column, because neither has a second half: an Arceus
  sublocation page - Horseshoe Plains, not Obsidian Fieldlands, which only lists names and says
  to go a level deeper - gives `Pokemon | Levels | Alpha Levels | Time of day | Weather`, and a
  Z-A Wild Zone page gives the same minus the alphas. Ticks rather than percentages. The time of
  day and the weather are conditions this dataset already words.
  - _**Right, and Z-A's step 0 proved it by running the reader rather than reading the page:
    260 rows off twenty pages with nothing in `encountertables.py` changed.** Two details were
    wrong and neither costs anything. The page is `Wild_zone` with a small z, and `Wild_Zone`
    is a 404. And the alphas are not missing - they are a heading inside the table, "Fixed alpha
    Pokemon spawns", where Hisui made them a column. `alpha_levels` is a `.get`, so the reader
    never noticed._
- **Scarlet and Violet are the only real question, and it is about the record rather than the
  parser.** South Province (Area One) gives `Pokemon | Games | Terrain | Levels | Probability
  Weight | Group Rate | Group Pokemon`, grouped under biome headings like "Prairie", with five
  terrain ticks. **There is no percentage per row** - there is a weight of 60 or 80 or 1, and a
  group rate on the row that leads a group. `wild.py` records a rate, so either the weight is
  turned into one or the model grows a second way of saying how likely something is. Decide that
  before writing the reader, not during. The fixed and special encounters on the same page are
  in the familiar shape and need none of this.
- So: **two new readers, not one, and not six.** Whichever is written first should be the Legends
  one, because it is the simplest and it proves the shape.

**The sprite sheets exist, and the naming rule changed twice.** Probing `Spr_8b_001`, `Spr_8a_001`
and `Spr_9s_001` gave three 404s, which looked like "no sheets" and was wrong both times - this
is the Generation 7 lesson again, and reading the Archives' own categories settled it in minutes:

- **Legends: Arceus has its own sheet**: `Spr_8a_NNN[_m|_f].png`, 367 files. `Spr_8a_001` is a
  404 because Bulbasaur is not in Hisui - the sheet only draws its own 242.
- **Generation 9 numbers to four digits.** `Spr_9s_0726.png` answers where `Spr_9s_001.png` does
  not. But the Scarlet and Violet category holds **two files**, so there is no sheet there to
  speak of.
- **Legends: Z-A has 35 files and all of them are Megas**: `Spr_9z_0121M.png`. That is Ultra Sun
  and Ultra Moon's shape - a layer over another sheet rather than a sheet.
- **Brilliant Diamond and Shining Pearl have nothing.** The only category with their name in it
  is trainer select-screen models.
- **What actually draws the modern games is HOME artwork**: `HOME0906.png`, `HOME0003_f.png`,
  3,143 files, and it resolves under the same md5 path rule as everything else. So four of the
  six games draw from one shared set rather than from a sheet of their own, and step 6's words -
  "a picture of each from this game's own sheet" - need to admit that. It is the honest answer:
  these games have no battle sprite, and a HOME render is what a player of them actually sees in
  a box.
- The renders are **512 by 512 with the drawing padded inside**, exactly like Generation 7's 240
  pixel frames. The Pillow crop `archives.py` already does for those applies unchanged.

**Every one of the six will need its forms written by hand.** `forms.py` says so itself and has
since Sword and Shield: the version-group rule is switched off for a game whose boxes do not hold
the generation, and "from here on it stays broken". `REGIONAL` already knows `hisui` and `paldea`.
So step 8 is a `GALAR_FORMS` for each, and budgeting it as a measurement rather than a switch is
the difference between half a day and a whole step.

**The dex shapes, from the source:**

- Brilliant Diamond and Shining Pearl: `original-sinnoh`, 151. **But these games do get a
  National Dex after the Sinnoh one is seen, and PokeAPI does not model that** - it lists only
  the 151. Step 2 has a decision to make that Galar did not: `nationalDexThrough` is empty for
  Sword and Shield because those games genuinely have no National Dex, and these do.
- Legends: Arceus: `hisui`, 242.
- Scarlet and Violet: `paldea` 400, `kitakami` 200, `blueberry` 243 - **the same three-lists
  shape as Galar**, and the same trap. Read `galar.FOREIGN_TO_EVERY_DEX` first.
- Legends: Z-A: `lumiose-city` 232 and `hyperspace` 132, the second being the expansion's.

**And the source knows two things this file does not list.** `mega-dimension` is Z-A's expansion
and `champions` is a game of its own with a 231-entry dex. Neither has a line in Phase 2. That is
a scope decision rather than a finding, and it belongs with Z-A rather than before it.

### Generation 8

_Done: all five. Sword and Shield in Galar, Brilliant Diamond and Shining Pearl in Sinnoh, and
Legends: Arceus in Hisui. What each pair shares is in a module of its own - `galar.py` and
`bdsp.py` - the standalone one is `legends_arceus.py`, and what all five have in common is
Pokemon HOME, which `home.py` has held since before any of them existed. **There is nothing left
for a `gen8.py` to say and now there never will be**: three modules are three answers to every
question this generation asks._

_**Every route these five declare has both of its ends**, and they declared them into a graph
that was already waiting: HOME is the only door Generation 8 has, so nothing older had to be
touched to let a Pokemon caught in Red reach Galar, Sinnoh or Hisui._

**The generation is not one answer about Pokedexes, it is three.** Sword and Shield have no
National Dex and cannot hold what is not in their own list - three lists kept apart and eighty
species left out of all of them, with `nationalDexThrough` empty. Brilliant Diamond and Shining
Pearl remade the generation that invented the National Dex and kept it: 493, `dexSource` national,
and a regional list of 151 that is only a page in the game. So the field that Galar left blank
was filled in for the first time in Generation 8 by a game released two years later.

_And Legends: Arceus is the third: no National Dex either, but unlike Galar **no leftover beside
the list** - only Pokemon in its 242 may be transferred in at all, with two exceptions the game
itself contains. `legends_arceus.HELD_WITHOUT_BEING_LISTED` has two entries where
`galar.FOREIGN_TO_EVERY_DEX` has eighty._

_Whichever game comes next should read three things: `galar.FOREIGN_TO_EVERY_DEX` before
assuming its own dex is the whole of what its boxes hold, `bdsp.EVOLUTION_GROUP` before assuming
a remake evolves things its own generation's way, and `evolutions.NOT_IN_THE_SOURCE` before
assuming PokeAPI has every way a Pokemon can change - it stopped having them at Hisui._

### Generation 9

_Done: all three, and with them **Phase 2**. Scarlet and Violet are Paldea and Legends: Z-A is
Lumiose City, and the two halves of this generation have nothing in common but Pokemon HOME -
so there is no `gen9.py` and now there never will be._

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