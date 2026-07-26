#!/usr/bin/env python3
"""Combined entrypoint for tracking Deadlock updates and extracting data."""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Deadlock Data Extractor")
    sub = parser.add_subparsers(dest="command", required=True)

    track = sub.add_parser("track", help="Check for and download Deadlock depot updates")
    track.add_argument("--depots", nargs="*", help="Limit to specific depot IDs")
    track.add_argument("--force", action="store_true", help="Download even if manifest unchanged")
    track.add_argument("--skip-extract", action="store_true", help="Download only, skip VPK extraction")
    track.add_argument("--extract-items", action="store_true", help="Run item extraction after update")
    track.add_argument("--items-output", help="Path for items_data.json output")

    extract = sub.add_parser("extract-items", help="Extract item data from game files")
    extract.add_argument("--data-dir", help="Path to extracted game data directory")
    extract.add_argument("--output", help="Path to write items_data.json")

    extract_heroes = sub.add_parser("extract-heroes", help="Extract hero data from game files")
    extract_heroes.add_argument("--data-dir", help="Path to extracted game data directory")
    extract_heroes.add_argument("--output", help="Path to write heroes_data.json")

    all_parser = sub.add_parser("all", help="Check for updates, download, extract, and build data")
    all_parser.add_argument("--force", action="store_true", help="Download even if manifest unchanged")

    args = parser.parse_args()

    if args.command == "track":
        _run_tracker(args)
    elif args.command == "extract-items":
        _run_item_extraction(args)
    elif args.command == "extract-heroes":
        _run_hero_extraction(args)
    elif args.command == "all":
        _run_all(args)


def _run_tracker(args):
    from steam.tracker import main as tracker_main
    sys.argv = [sys.argv[0]]
    if args.depots:
        sys.argv += ["--depots"] + args.depots
    if args.force:
        sys.argv.append("--force")
    if args.skip_extract:
        sys.argv.append("--skip-extract")
    if args.extract_items:
        sys.argv.append("--extract-items")
    if args.items_output:
        sys.argv += ["--items-output", args.items_output]
    tracker_main()


def _run_item_extraction(args):
    from items.extract import main as extract_main
    sys.argv = [sys.argv[0]]
    if args.data_dir:
        sys.argv += ["--data-dir", args.data_dir]
    if args.output:
        sys.argv += ["--output", args.output]
    extract_main()


def _run_hero_extraction(args):
    from heroes.extract import main as hero_extract_main
    sys.argv = [sys.argv[0]]
    if args.data_dir:
        sys.argv += ["--data-dir", args.data_dir]
    if args.output:
        sys.argv += ["--output", args.output]
    hero_extract_main()


def _run_all(args):
    from steam.tracker import main as tracker_main
    from items.extract import run as extract_items
    from heroes.extract import run as extract_heroes
    from steam.settings import DOWNLOAD_DIR

    sys.argv = [sys.argv[0]]
    if args.force:
        sys.argv.append("--force")
    tracker_main()

    data_dirs = _find_game_data_dirs(DOWNLOAD_DIR)
    if not data_dirs:
        print("No game data directories found. Run with --force to download even if unchanged.")
        return

    for data_dir in data_dirs:
        print(f"\nExtracting items from: {data_dir}")
        extract_items(str(data_dir), args.items_output)
        print(f"\nExtracting heroes from: {data_dir}")
        extract_heroes(str(data_dir), args.heroes_output)


def _find_game_data_dirs(download_base):
    if not download_base.exists():
        return []
    dirs = set()
    for path in Path(download_base).rglob("abilities.vdata"):
        try:
            depot_dir_name = path.relative_to(download_base).parts[0]
            dirs.add(str(download_base / depot_dir_name))
        except ValueError:
            pass
    return sorted(dirs)

if __name__ == "__main__":
    main()
