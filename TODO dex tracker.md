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

### 0.2 The shared forms table

_Done. `forms.json` holds 154 entries: 97 gender differences, 39 cosmetic and 18 functional.
Nothing regional, because the earliest of those is Alolan and this dataset stops at Generation 5._

_Read rather than listed. `forms.py` walks each species' varieties and then each variety's own
faces, which is the two shapes PokeAPI uses, and works out the kind by measuring: a form whose
typing, base stats or abilities differ from the species' is functional and one that differs in
none of them is cosmetic. That is why Unown's letters come out cosmetic and Wormadam's cloaks
functional without anybody deciding it twice - the letters are one Pokemon with 28 faces and the
cloaks are three Pokemon. Which games a form is in comes from the version group it arrived in,
so every Mega, Gigantamax and regional form falls outside this dataset by itself._

_Two kinds are left out on purpose. Battle-only, which the source flags - Castform's weather,
Darmanitan's Zen Mode, Meloetta's Pirouette - and held-item, which it does not: Arceus's
seventeen plates and Genesect's four drives. Take the item off and it is the same Pokemon, so an
entry each would ask a player to catch one Arceus eighteen times. Say so if you want them back._

_Four entries the source gets wrong are written by hand in `ONLY_IN`: Deoxys changes into a
different form in each of the three Generation 3 cartridges and PokeAPI can only name the
version group, which pairs FireRed and LeafGreen; and the spiky-eared Pichu cannot leave
HeartGold or SoulSilver._

### 0.3 What the forms table still cannot say
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
pass afterwards, as Phase 0.2 and 0.3 describe, because twenty games had already been written by
the time the table existed. From Generation 6 on it is part of writing a game, and it has to be,
because that is where forms stop being a curiosity — Mega Evolution, then the regional forms, then
Gigantamax. Three things belong to it:

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

- [ ] **X** (`x`, gen 6, pair partner: Y)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Events
  - [ ] 8 Alternate forms  - [ ] 9 Validate + smoke test
- [ ] **Y** (`y`, gen 6, pair partner: X)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Events
  - [ ] 8 Alternate forms  - [ ] 9 Validate + smoke test
- [ ] **Omega Ruby** (`omega-ruby`, gen 6, pair partner: Alpha Sapphire)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Events
  - [ ] 8 Alternate forms  - [ ] 9 Validate + smoke test
- [ ] **Alpha Sapphire** (`alpha-sapphire`, gen 6, pair partner: Omega Ruby)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Events
  - [ ] 8 Alternate forms  - [ ] 9 Validate + smoke test

### Generation 7

- [ ] **Sun** (`sun`, gen 7, pair partner: Moon)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Events
  - [ ] 8 Alternate forms  - [ ] 9 Validate + smoke test
- [ ] **Moon** (`moon`, gen 7, pair partner: Sun)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Events
  - [ ] 8 Alternate forms  - [ ] 9 Validate + smoke test
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

First games without a National Dex — step 2 uses the game's own dex, DLC included.

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

Not playable main games, but they must exist as nodes for routes to work.

- [ ] **Pokémon Bank** (`bank`) — edges from Gen 5 and VC, both ways with Gen 6 and 7, one-way to HOME
      — two edges are already waiting for this node, and there will be six once Generations 1
      and 2 are built
- [ ] **Pokémon HOME** (`home`) — one-way in from Bank and Let's Go, both ways with Gen 8 and 9,
      per-species dex filter on deposit

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

- [ ] Multiple collections: list, switch, rename, delete
- [ ] Editing a collection's settings after creation, records preserved
- [ ] Dataset version and build date shown somewhere in the UI
- [ ] Unobtainable entries handled per the decision in the spec's open questions
- [ ] Keyboard navigation through the grid and popup
- [ ] Empty and error states: no dataset, corrupt data file, cloud file locked
- [ ] Export a collection to CSV
- [ ] Collections list can be filtered on main game, name
- [ ] The Pokemon Dream Radar as a source for Black 2 and White 2
  - A 3DS app rather than a game: no dex of its own, nothing caught in it, and it sends one way
    into those two and nowhere else. So it is neither a transfer edge nor an NPC with a gift,
    and it needs a shape of its own - a source that is not a game, which nothing in the dataset
    is yet. What it is worth is that some of what it sends has no other way in.
  - Not the Dream World, and not by oversight: that was a website, it closed in 2014, and a
    player starting today cannot reach any of it. The Radar is still runnable by whoever has it.
  - Worth saying in the reason a player reads: the eShop it came from shut in 2023, so it is
    ownable rather than buyable. That is a different answer from "this cannot be done".