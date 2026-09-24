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

No National Dex either, and unlike Generation 7 these games cannot hold what is not in their own
list — step 2 uses the game's own dex, DLC included, and `nationalDexThrough` stays empty.

- [ ] **Sword** (`sword`, gen 8, pair partner: Shield) — base + Isle of Armor + Crown Tundra
  - [x] 1 Entity + edges  - [x] 2 Dex list  - [x] 3 Wild  - [x] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Events
  - [ ] 8 Alternate forms  - [ ] 9 Validate + smoke test
- [ ] **Shield** (`shield`, gen 8, pair partner: Sword) — base + Isle of Armor + Crown Tundra
  - [x] 1 Entity + edges  - [x] 2 Dex list  - [x] 3 Wild  - [x] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Events
  - [ ] 8 Alternate forms  - [ ] 9 Validate + smoke test
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