import argparse
import json
import os
import sys as _sys
from pathlib import Path

if __name__ == '__main__' and not __package__:
    _sys.path.insert(0, str(Path(__file__).parent.parent))

from archive import archive_data, enrich_metadata
from config import Paths
from heroes.blocks import extract_hero_blocks, extract_ability_blocks
from heroes.transform import build_hero_record
from heroes.summary import summarize
from utils.kv3_parser import parse_kv3_obj
from utils.localization import parse_steam_localization


def load_localization(paths):
    hero_names = parse_steam_localization(paths.hero_names)
    hero_descriptions = parse_steam_localization(paths.hero_abilities)
    print(f"Hero names: {len(hero_names)}, Ability descriptions: {len(hero_descriptions)}")
    return hero_names, hero_descriptions


def load_parsed_heroes(paths):
    raw_blocks = extract_hero_blocks(paths.heroes)
    print(f"Found {len(raw_blocks)} hero entries")

    heroes = {}
    for hero_id, block_text in raw_blocks.items():
        if hero_id == 'hero_base':
            continue
        try:
            heroes[hero_id] = parse_kv3_obj(block_text)
        except Exception as e:
            print(f"  Fail: {hero_id}: {e}")

    print(f"Parsed: {len(heroes)} heroes")
    return heroes


def load_parsed_abilities(paths):
    raw_blocks = extract_ability_blocks(paths.abilities)
    print(f"Found {len(raw_blocks)} ability entries")

    abilities = {}
    for ability_id, block_text in raw_blocks.items():
        try:
            abilities[ability_id] = parse_kv3_obj(block_text)
        except Exception as e:
            print(f"  Fail: {ability_id}: {e}")

    print(f"Parsed: {len(abilities)} abilities")
    return abilities


def build_output(heroes, abilities, hero_names, hero_descriptions):
    clean_heroes = {}
    for hero_id in sorted(heroes.keys()):
        try:
            clean_heroes[hero_id] = build_hero_record(
                hero_id, heroes[hero_id], abilities, hero_names, hero_descriptions, hero_names
            )
        except Exception as e:
            print(f"  Error building {hero_id}: {e}")

    return {
        '_metadata': {
            'source': 'heroes.vdata',
            'count': len(clean_heroes),
        },
        'heroes': clean_heroes,
    }


def write_output(output, out_path):
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def run(data_dir, output_path=None, archive_dir=None):
    if output_path is None:
        output_path = os.path.join(os.getcwd(), 'heroes_data.json')

    paths = Paths(data_dir, output_path)

    print(f"Heroes: {paths.heroes}")
    print(f"Abilities: {paths.abilities}")
    print(f"Hero names: {paths.hero_names}")
    print(f"Hero abilities: {paths.hero_abilities}")

    hero_names, hero_descriptions = load_localization(paths)
    heroes = load_parsed_heroes(paths)
    abilities = load_parsed_abilities(paths)
    output = build_output(heroes, abilities, hero_names, hero_descriptions)
    enrich_metadata(output)
    write_output(output, paths.hero_output_json)

    print(f"\nOutput: {paths.hero_output_json}")
    print(f"Heroes: {len(output['heroes'])}")

    avail, total_abilities = summarize(output['heroes'])
    print(f"Availability: {avail}")
    print(f"Total abilities extracted: {total_abilities}")

    try:
        archive_data(paths.hero_output_json, output, "heroes", archive_dir)
    except Exception as e:
        print(f"  Archive failed: {e}")

    return output


def main():
    parser = argparse.ArgumentParser(description="Extract hero data from Deadlock game files.")
    parser.add_argument("--data-dir", help="Path to extracted game data directory (depot download dir)")
    parser.add_argument("--output", help="Path to write heroes_data.json")
    parser.add_argument("--archive-dir", help="Directory for versioned snapshots (default: <output dir>/archive)")
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

    run(data_dir, args.output, args.archive_dir)


if __name__ == '__main__':
    main()
