# deadlock-data-extractor

Tools for extracting structured data out of Source 2 (Citadel) game files
and turning it into clean JSON. The game stores most of its data in
Valve's KV3 (KeyValues3) text format, spread across resource scripts and
localization files — this repo pulls that apart into something easier to
work with (websites, tools, spreadsheets, whatever).

Item/ability extraction is the first extractor. More will be added over
time (e.g. heroes, maps, patch data) following the same pattern.

## Requirements

Python 3.8+. No third-party dependencies — standard library only.

## Project layout

```
deadlock-data-extractor/
├── src/
│   ├── kv3_parser.py           # shared: KV3 text -> dict/list parser
│   ├── steam_localization.py   # shared: localization .txt parser
│   │
│   ├── extract_items.py        # entrypoint for item/ability extraction
│   ├── config.py                #   paths, pricing table, slot names
│   ├── item_blocks.py           #   finds upgrade_* blocks in abilities.vdata
│   ├── item_transform.py        #   raw parsed item -> clean output record
│   └── summary.py               #   tier/slot/activation counts
│
├── data/
│   └── game/
│       └── citadel/            # mirrors the game's own directory structure
│           ├── pak01_dir/scripts/abilities.vdata
│           └── resource/localization/
│               ├── citadel_gc_mod_names/citadel_gc_mod_names_english.txt
│               └── citadel_mods/citadel_mods_english.txt
│
├── items_data.json             # generated output of extract_items.py
└── README.md
```

`kv3_parser.py` and `steam_localization.py` are generic — they don't know
anything about items specifically — so future extractors (heroes, maps,
etc.) can reuse them rather than reimplementing KV3/localization parsing
from scratch. Extractor-specific files are prefixed accordingly
(`item_*.py` for items) so it's clear what belongs to what as more get
added.

## Extractors

### Items (`extract_items.py`)

Extracts item/ability data from `abilities.vdata`, resolves display names
and descriptions from the localization files, and writes a single clean
`items_data.json`.

**Usage:**

```bash
cd src
python3 extract_items.py
```

This writes `items_data.json` to the repo root (one level above `src/`)
and prints a short summary:

```
Loading: /path/to/repo/data/game/citadel/pak01_dir/scripts/abilities.vdata
Names: 412, Descriptions: 398
Found 410 items
Parsed: 410 items

Output: /path/to/repo/items_data.json
Items: 410
Tiers: {0: 12, 1: 98, 2: 110, 3: 105, 4: 60, 5: 25}
Slots: {'Weapon': 140, 'Vitality': 135, 'Spirit': 135}
Activation: {'Active': 210, 'Passive': 200}
```

**Output format:**

```jsonc
{
  "_metadata": {
    "source": "abilities.vdata",
    "count": 410,
    "pricing": [0, 800, 1600, 3200, 6400, 9999]  // soul cost by tier
  },
  "items": {
    "upgrade_example_item": {
      "id": "upgrade_example_item",
      "display_name": "Example Item",
      "description": "What the item does.",
      "tier": 2,
      "soul_cost": 1600,
      "slot": "Weapon",              // Weapon | Vitality | Spirit
      "activation": "Active",        // Active | Passive
      "available_in": "main_game",   // main_game | street_brawl | in_dev
      "stats": {
        "SomeStatName": { "value": 10, "usage": "..." }
      },
      "passive": { "...": "..." },   // stats auto-applied passively
      "active": { "...": "..." },    // stats applied via the active buff
      "cooldown": 12,                // present if the item has one
      "duration": 5,                 // present if the item has one
      "components": ["upgrade_basic_magazine"],   // if it's a combined item
      "upgrades": [ { "SomeStat": 1.5 } ],         // per-tier bonuses
      "tooltip_descriptions": [ { "section": "...", "description": "..." } ]
    }
  }
}
```

Fields like `components`, `upgrades`, and `tooltip_descriptions` are only
present when the item actually has them.

**Known quirks:**

- If an `upgrade_*` block's opening `{` appears on the same line as a
  field the parser doesn't expect immediately after it, the block may be
  extracted as empty. This mirrors how the source data is laid out in
  practice and hasn't caused missed items so far, but if you see an item
  in `abilities.vdata` missing from the output, check the raw formatting
  of that block first.
- Parse failures on individual items are logged to stdout
  (`Fail: <item_id>: <error>`) and skipped rather than aborting the whole
  run.

## How paths are resolved

Each extractor's `config.find_repo_dir()` starts at the script's own
directory (`src/`) and walks upward until it finds `data/game/citadel/`,
up to a few levels up. This means a script can be run without needing to
`cd` into `src/` first — as long as `data/` lives somewhere above it in
the tree, it'll be found.

## Adding a new extractor

To add a new extractor (e.g. heroes):

1. Reuse `kv3_parser.py` and `steam_localization.py` for parsing — don't
   duplicate that logic.
2. Add extractor-specific modules prefixed with the extractor's name
   (e.g. `hero_blocks.py`, `hero_transform.py`), following the same
   split as the item extractor: block extraction, transform, config,
   entrypoint.
3. Add a section under **Extractors** above documenting what it does,
   how to run it, and its output format.