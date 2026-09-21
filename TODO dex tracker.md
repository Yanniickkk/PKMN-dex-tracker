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

### 0.6 Pipeline skeleton
- [ ] Validator with the checks listed in 0.7
  - The harness is built and wired into every build: what a rule is, what it reports, and
    a report written beside the dataset. No rules yet, and a build with none says "no rules
    ran, so nothing was checked" rather than looking clean. The rules are 0.7 below.
  - Note for 0.7: the first rule on that list needs dex entries to be markable as
    deliberately unobtainable, and nothing in the schema says that yet.

### 0.7 Validation rules
- [ ] Every dex entry has a method, or is explicitly flagged unobtainable
- [ ] Every evolution rule points at an entry that itself has a method — no dead ends
- [ ] Every form referenced by a game's dex exists in the form table
- [ ] Every transfer edge connects two known games
- [ ] Per-game coverage report: full / partial / missing counts

---

## Phase 1 — First vertical slice

Build the whole app against two games before scaling the data out.
Target: **Platinum** as main game, **Emerald** linked.

- [ ] Collection setup wizard: name, main game, linked games, both toggles
- [ ] Linked-game picker filtered by the transfer graph, disabled entries show the reason
- [ ] Grid screen: virtualised, battle sprites, dex number, name
- [ ] Tile status colours for the three states, plus a non-colour badge or icon
- [ ] Progress counter, with a secondary "still to transfer" figure
- [ ] Filters: name search, still to catch, not yet transferred, available in game
- [ ] Detail popup: opens for caught and uncaught entries alike
- [ ] Acquisition sections ordered gift → wild → evolution → trade
- [ ] Main-game methods before linked-game methods within each section
- [ ] Per-method detail fields rendered per the spec table
- [ ] Evolution drill-down: click through to the previous stage, back control, breadcrumb
- [ ] Transfer route shown for non-main-game methods, alternatives collapsible
- [ ] Capture controls: three states, holding-game prompt, catch date, note
- [ ] Quick toggle on the tile itself
- [ ] Sprite caching, no runtime network calls
- [ ] End-to-end check: fresh collection → catch Chimchar → drill Infernape → Monferno → Chimchar

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
- [ ] **Emerald** (`emerald`, gen 3, standalone) — *partly done in Phase 1*
  - [ ] 1 Entity + edges  - [ ] 2 Dex list  - [ ] 3 Wild  - [ ] 4 Gifts & statics
  - [ ] 5 Trades & evolutions  - [ ] 6 Sprites  - [ ] 7 Validate + smoke test
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
