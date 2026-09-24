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

_Done: Sun and Moon, and everything they reach is in `DONE dex tracker.md`. Ultra Sun, Ultra
Moon and the two Let's Go games are still to come._

_What Alola shares is in `alola.py`, which is the region module and the generation's both - for
the reason that file gives about Let's Go. **The four edges Sun and Moon declared into an empty
space all point at Ultra Sun and Ultra Moon**, and they light up the moment those two exist._

- [ ] **Ultra Sun** (`ultra-sun`, gen 7, pair partner: Ultra Moon)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Events
  - [ ] 8 Alternate forms  - [ ] 9 Validate + smoke test
- [ ] **Ultra Moon** (`ultra-moon`, gen 7, pair partner: Ultra Sun)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Events
  - [ ] 8 Alternate forms  - [ ] 9 Validate + smoke test
- [ ] **Let's Go, Pikachu!** (`lets-go-pikachu`, gen 7, pair partner: Let's Go, Eevee!)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Events
  - [ ] 8 Alternate forms  - [ ] 9 Validate + smoke test
- [ ] **Let's Go, Eevee!** (`lets-go-eevee`, gen 7, pair partner: Let's Go, Pikachu!)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Events
  - [ ] 8 Alternate forms  - [ ] 9 Validate + smoke test

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