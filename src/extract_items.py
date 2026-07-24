"""Extracts item/ability data from abilities.vdata into items_data.json.

Pipeline:
    1. Load localization files (display names + descriptions).
    2. Pull raw `upgrade_*` KV3 blocks out of abilities.vdata (item_blocks).
    3. Parse each raw block into a Python dict (kv3_parser).
    4. Transform each parsed dict into the clean output schema (item_transform).
    5. Write the result to items_data.json and print a summary.
"""

import json
import os

from config import Paths, TIER_PRICES, find_repo_dir
from item_blocks import extract_item_blocks
from item_transform import build_item_record
from kv3_parser import parse_kv3_obj
from steam_localization import parse_steam_localization
from summary import summarize


def load_localization(paths):
    names = parse_steam_localization(paths.mod_names)
    descriptions = parse_steam_localization(paths.mod_descriptions)
    print(f"Names: {len(names)}, Descriptions: {len(descriptions)}")
    return names, descriptions


def load_parsed_items(paths):
    """Extract and parse every item block from abilities.vdata.

    Parse failures are logged and skipped rather than aborting the run.
    """
    raw_blocks = extract_item_blocks(paths.abilities)
    print(f"Found {len(raw_blocks)} items")

    items = {}
    for item_id, block_text in raw_blocks.items():
        try:
            items[item_id] = parse_kv3_obj(block_text)
        except Exception as e:
            print(f"  Fail: {item_id}: {e}")

    print(f"Parsed: {len(items)} items")
    return items


def build_output(items, names, descriptions):
    clean_items = {
        item_id: build_item_record(item_id, items[item_id], names, descriptions)
        for item_id in sorted(items.keys())
    }
    return {
        '_metadata': {
            'source': 'abilities.vdata',
            'count': len(clean_items),
            'pricing': TIER_PRICES,
        },
        'items': clean_items,
    }


def write_output(output, out_path):
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_dir = find_repo_dir(script_dir)
    paths = Paths(repo_dir)

    print(f"Loading: {paths.abilities}")

    names, descriptions = load_localization(paths)
    items = load_parsed_items(paths)
    output = build_output(items, names, descriptions)

    write_output(output, paths.output_json)
    print(f"\nOutput: {paths.output_json}")
    print(f"Items: {len(output['items'])}")

    tiers, slots, activations = summarize(output['items'])
    print(f"Tiers: {tiers}")
    print(f"Slots: {slots}")
    print(f"Activation: {activations}")


if __name__ == '__main__':
    main()
