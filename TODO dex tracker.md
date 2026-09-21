# Living Dex Tracker — Implementation TODO

Companion to the specification. Work top to bottom: Phase 0 and 1 build the machine,
Phase 2 feeds it one game at a time.

## How this file works

- **Every version is its own game entity.** Red and Blue are two entities, not one
  "Red/Blue" row. Same for Gold/Silver, Sword/Shield, Scarlet/Violet, and every other pair.
  Version exclusives are the whole reason this matters.
- **Phase 2 is the repeating part.** Each game has the same 7-step checklist. A game is
  "done" when all 7 are ticked and its validation run is green.
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

Every game below repeats these 7 steps:

1. **Entity + edges** — register the game, its metadata, and its transfer edges in both directions
2. **Dex list** — which species and forms it contains, and their numbering in this game
3. **Wild** — every encounter slot: location, sub-area, method, level range, rate, time, season, weather
4. **Gifts & statics** — starters, fossils, revives, NPC gifts, eggs, legendary statics
5. **Trades & evolutions** — in-game NPC trades, plus which evolution triggers are actually possible here
6. **Sprites** — battle sprites for this generation, or the documented fallback
7. **Validate + smoke test** — validation green, then create a collection with this game as main game

Order to work in: start with Gen 3 and Gen 4 (already partly done in Phase 1),
then Gen 1–2, then forward through Gen 5 onward.

### Generation 1

- [ ] **Red** (`red`, gen 1, pair partner: Blue)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **Blue** (`blue`, gen 1, pair partner: Red)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **Yellow** (`yellow`, gen 1, standalone)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test

### Generation 2

- [ ] **Gold** (`gold`, gen 2, pair partner: Silver)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **Silver** (`silver`, gen 2, pair partner: Gold)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **Crystal** (`crystal`, gen 2, standalone)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test

### Generation 3

- [ ] **Ruby** (`ruby`, gen 3, pair partner: Sapphire)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **Sapphire** (`sapphire`, gen 3, pair partner: Ruby)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **Emerald** (`emerald`, gen 3, standalone)
  - [x] 1 Entity + edges - 2026-09-21
  - [x] 2 Dex list - 2026-09-21
  - [x] 3 Wild - 2026-09-21
  - [x] 4 Gifts & statics - 2026-09-21
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
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
- [ ] **FireRed** (`firered`, gen 3, pair partner: LeafGreen)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **LeafGreen** (`leafgreen`, gen 3, pair partner: FireRed)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test

### Generation 4

- [ ] **Diamond** (`diamond`, gen 4, pair partner: Pearl)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **Pearl** (`pearl`, gen 4, pair partner: Diamond)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **Platinum** (`platinum`, gen 4, standalone) — *partly done in Phase 1*
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **HeartGold** (`heartgold`, gen 4, pair partner: SoulSilver)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **SoulSilver** (`soulsilver`, gen 4, pair partner: HeartGold)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test

### Generation 5

- [ ] **Black** (`black`, gen 5, pair partner: White)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **White** (`white`, gen 5, pair partner: Black)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **Black 2** (`black-2`, gen 5, pair partner: White 2)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **White 2** (`white-2`, gen 5, pair partner: Black 2)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test

### Generation 6

- [ ] **X** (`x`, gen 6, pair partner: Y)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **Y** (`y`, gen 6, pair partner: X)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **Omega Ruby** (`omega-ruby`, gen 6, pair partner: Alpha Sapphire)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **Alpha Sapphire** (`alpha-sapphire`, gen 6, pair partner: Omega Ruby)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test

### Generation 7

- [ ] **Sun** (`sun`, gen 7, pair partner: Moon)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **Moon** (`moon`, gen 7, pair partner: Sun)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **Ultra Sun** (`ultra-sun`, gen 7, pair partner: Ultra Moon)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **Ultra Moon** (`ultra-moon`, gen 7, pair partner: Ultra Sun)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **Let's Go, Pikachu!** (`lets-go-pikachu`, gen 7, pair partner: Let's Go, Eevee!)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **Let's Go, Eevee!** (`lets-go-eevee`, gen 7, pair partner: Let's Go, Pikachu!)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test

### Generation 8

First games without a National Dex — step 2 uses the game's own dex, DLC included.

- [ ] **Sword** (`sword`, gen 8, pair partner: Shield) — base + Isle of Armor + Crown Tundra
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **Shield** (`shield`, gen 8, pair partner: Sword) — base + Isle of Armor + Crown Tundra
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **Brilliant Diamond** (`brilliant-diamond`, gen 8, pair partner: Shining Pearl)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **Shining Pearl** (`shining-pearl`, gen 8, pair partner: Brilliant Diamond)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **Legends: Arceus** (`legends-arceus`, gen 8, standalone)
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test

### Generation 9

- [ ] **Scarlet** (`scarlet`, gen 9, pair partner: Violet) — base + Teal Mask + Indigo Disk
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **Violet** (`violet`, gen 9, pair partner: Scarlet) — base + Teal Mask + Indigo Disk
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
- [ ] **Legends: Z-A** (`legends-z-a`, gen 9, standalone)
  - [ ] 0 **Verify against a live source first** — dex contents and HOME compatibility
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test

### Transfer-only nodes

Not playable main games, but they must exist as nodes for routes to work.

- [ ] **Pokémon Bank** (`bank`) — edges from Gen 5 and VC, both ways with Gen 6 and 7, one-way to HOME
- [ ] **Pokémon HOME** (`home`) — one-way in from Bank and Let's Go, both ways with Gen 8 and 9,
      per-species dex filter on deposit

### Virtual Console releases (optional, later)

Separate entities from the cartridges, because only these reach Bank.

- [ ] `red-vc`, `blue-vc`, `yellow-vc` — edges to Bank via Poké Transporter
- [ ] `gold-vc`, `silver-vc`, `crystal-vc` — edges to Bank via Poké Transporter

---

## Phase 3 — Polish

- [ ] Multiple collections: list, switch, rename, delete
- [ ] Editing a collection's settings after creation, records preserved
- [ ] Dataset version and build date shown somewhere in the UI
- [ ] Unobtainable entries handled per the decision in the spec's open questions
- [ ] Keyboard navigation through the grid and popup
- [ ] Empty and error states: no dataset, corrupt data file, cloud file locked
- [ ] Export a collection to CSV
- [ ] Filter national dex or regional dex
