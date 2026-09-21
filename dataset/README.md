# dataset/

Build output of `pipeline/`, committed on purpose: the app must run with no network access,
and a checked-in dataset is what makes a build reproducible from a git tag.

Nothing is generated yet. Phase 0.6 fills this directory; do not hand-edit it.

The shape below is defined by `LivingDex.Core.Dataset.DatasetLayout` and written with
`LivingDex.Core.Dataset.DatasetJson.Options`. The pipeline and the app share that one
configuration, so the two cannot drift.

## Layout

```
dataset/
  index.json             version stamp and the list of games present
  species.json           every species, shared
  forms.json             every form, shared
  evolution-rules.json   every evolution rule, shared
  transfers.json         the transfer graph
  games/
    platinum.json        one file per game: the game, its dex, its acquisition methods
    emerald.json
  sprites/               battle sprites
```

One file per game plus shared tables. Adding Emerald means adding `games/emerald.json` and
appending to the shared tables — it never means editing `games/platinum.json`.

JSON is written indented with camelCase names and `\n` line endings. That is deliberate: the
dataset is committed, so a rebuild has to produce a reviewable diff rather than one enormous
line.

## Game file

Everything specific to one game. The `kind` discriminator decides which fields an acquisition
method carries, so there are no mostly-null columns.

`nationalDexThrough` is the highest National Dex number this game's National Dex covers, or
absent for a game without one. The dex builder needs the number rather than a yes or no:
"has a National Dex" does not say where it stops.

```json
{
  "game": {
    "id": "platinum",
    "title": "Pokemon Platinum Version",
    "version": "Platinum",
    "generation": 4,
    "region": "Sinnoh",
    "release": "cartridge",
    "nationalDexThrough": 493,
    "dexSource": "nationalDex"
  },
  "dexEntries": [
    { "game": "platinum", "target": { "species": "chimchar" }, "number": 4 }
  ],
  "acquisitionMethods": [
    {
      "kind": "gift",
      "game": "platinum",
      "target": { "species": "chimchar" },
      "giftKind": "starter",
      "location": "Route 201",
      "npc": "Professor Rowan",
      "level": 5,
      "source": {
        "source": "bulbapedia",
        "url": "https://bulbapedia.bulbagarden.net/wiki/Route_201",
        "retrievedOn": "2026-09-21"
      }
    },
    {
      "kind": "wild",
      "game": "platinum",
      "target": { "species": "starly" },
      "location": "Route 202",
      "method": "walk",
      "levels": { "minimum": 3, "maximum": 4 },
      "ratePercent": 55,
      "source": { "source": "bulbapedia", "retrievedOn": "2026-09-21" }
    },
    {
      "kind": "evolution",
      "game": "platinum",
      "target": { "species": "monferno" },
      "rule": "chimchar-to-monferno",
      "source": { "source": "bulbapedia", "retrievedOn": "2026-09-21" }
    }
  ]
}
```

A form entry names both, so nothing has to be looked up:
`"target": { "species": "vulpix", "form": "vulpix-alola" }`.

## Shared tables

`evolution-rules.json` holds rules once, for every game. Whether a game can use one is
expressed by that game having an `evolution` acquisition method pointing at it — which is also
what makes the Phase 0.7 check "no evolution dead ends" possible.

```json
[
  {
    "id": "chimchar-to-monferno",
    "from": { "species": "chimchar" },
    "to": { "species": "monferno" },
    "trigger": "levelUp",
    "conditions": [{ "condition": "minimumLevel", "level": 14 }]
  }
]
```

`transfers.json` holds the graph. Edges are data so that adding a game never means changing the
engine. `filter` says which species an edge will carry.

```json
[
  {
    "from": "emerald",
    "to": "platinum",
    "mechanism": "palPark",
    "direction": "oneWay",
    "filter": { "filter": "nationalDexRange", "from": 1, "to": 386 }
  },
  {
    "from": "home",
    "to": "sword",
    "mechanism": "home",
    "direction": "bothWays",
    "filter": { "filter": "presentInTargetDex" }
  }
]
```

`presentInTargetDex` is the rule that makes HOME refuse a deposit into a Generation 8 or 9 game
that has no entry for the species.
