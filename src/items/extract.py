import argparse
import json
import os
import sys as _sys
from pathlib import Path

if __name__ == '__main__' and not __package__:
    _sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Paths, TIER_PRICES
from items.blocks import extract_item_blocks
from items.transform import build_item_record
from items.summary import summarize
from utils.kv3_parser import parse_kv3_obj
from utils.localization import parse_steam_localization


def load_localization(paths):
    names = parse_steam_localization(paths.mod_names)
    descriptions = parse_steam_localization(paths.mod_descriptions)
    print(f"Names: {len(names)}, Descriptions: {len(descriptions)}")
    return names, descriptions


def load_parsed_items(paths):
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


def run(data_dir, output_path=None):
    if output_path is None:
        output_path = os.path.join(os.getcwd(), 'items_data.json')

    paths = Paths(data_dir, output_path)

    print(f"Abilities: {paths.abilities}")
    print(f"Names: {paths.mod_names}")
    print(f"Descriptions: {paths.mod_descriptions}")

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

    return output


def main():
    parser = argparse.ArgumentParser(description="Extract item data from Deadlock game files.")
    parser.add_argument("--data-dir", help="Path to extracted game data directory (depot download dir)")
    parser.add_argument("--output", help="Path to write items_data.json")
    args = parser.parse_args()

    data_dir = args.data_dir
    if not data_dir:
        tracker_dir = os.environ.get("DEADLOCK_TRACKER_DIR")
        if tracker_dir:
            depots_dir = Path(tracker_dir) / "depots"
            if depots_dir.exists():
                data_dir = str(depots_dir)
    if not data_dir:
        data_dir = os.getcwd()

    run(data_dir, args.output)


if __name__ == '__main__':
    main()
