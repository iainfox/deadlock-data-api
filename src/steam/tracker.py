import argparse
import sys
from pathlib import Path

import sys as _sys
from pathlib import Path as _Path
if __name__ == '__main__' and not __package__:
    _sys.path.insert(0, str(_Path(__file__).parent.parent))

from steam.settings import KNOWN_DEPOT_IDS, DOWNLOAD_DIR, log
from steam.state import load_state, save_state
from steam.manifests import get_current_manifests
from steam.download import download_depots
from steam.extract import extract_depot


def find_data_dirs(download_base=DOWNLOAD_DIR):
    if not download_base.exists():
        return []
    dirs = []
    for depot_dir in sorted(download_base.iterdir()):
        if not depot_dir.is_dir():
            continue
        for child in depot_dir.iterdir():
            if child.is_dir() and (child / "scripts" / "abilities.vdata").exists():
                dirs.append(child.parent)
    return dirs


def main():
    parser = argparse.ArgumentParser(description="Track Deadlock depot updates.")
    parser.add_argument("--depots", nargs="*", help="Limit to specific depot IDs")
    parser.add_argument("--force", action="store_true", help="Download even if manifest unchanged")
    parser.add_argument("--skip-extract", action="store_true", help="Download only, skip VPK decompiling")
    parser.add_argument("--extract-items", action="store_true", help="Run item extraction after update")
    parser.add_argument("--items-output", help="Path for items_data.json output")
    args = parser.parse_args()

    depot_ids = args.depots or KNOWN_DEPOT_IDS

    state = load_state()
    current = get_current_manifests(known_depot_ids=depot_ids)

    if not current:
        log.error("Could not retrieve any manifest info. Aborting this run.")
        sys.exit(1)

    changed = {}
    for depot_id, manifest_id in current.items():
        previous = state["manifests"].get(depot_id)
        if args.force or previous != manifest_id:
            changed[depot_id] = manifest_id
            log.info("Depot %s: %s -> %s", depot_id, previous, manifest_id)
        else:
            log.info("Depot %s: unchanged (%s)", depot_id, manifest_id)

    if not changed:
        log.info("No changes detected. Nothing to do.")
        save_state(state)
        return

    downloaded_paths = []
    extracted_paths = []
    try:
        downloaded = download_depots(changed)
    except Exception:
        log.exception("Failed to download depots -- leaving state unchanged for all.")
        save_state(state)
        return

    for depot_id, out_dir in downloaded.items():
        downloaded_paths.append(str(out_dir))
        state["manifests"][depot_id] = changed[depot_id]

        try:
            if not args.skip_extract:
                extracted_paths.extend(extract_depot(out_dir))
        except Exception:
            log.exception("Failed to extract depot %s -- manifest already recorded.", depot_id)

    save_state(state)

    if downloaded_paths:
        log.info("Update run complete. New depot snapshots:\n%s", "\n".join(downloaded_paths))
    if extracted_paths:
        log.info("Extracted data ready for parsing:\n%s", "\n".join(str(p) for p in extracted_paths))

    if args.extract_items and extracted_paths:
        _run_item_extraction(extracted_paths, args.items_output)


def _run_item_extraction(extracted_paths, output_path):
    try:
        from items.extract import run as extract_items
    except ImportError:
        log.error("Could not import items.extract -- skipping item extraction.")
        return

    for data_dir in extracted_paths:
        if not data_dir.is_dir():
            continue
        abilities = data_dir / "scripts" / "abilities.vdata"
        if abilities.exists():
            log.info("Running item extraction from %s", data_dir)
            extract_items(str(data_dir.parent), output_path)
            return

    log.warning("No abilities.vdata found in any extracted directory.")


if __name__ == "__main__":
    main()
