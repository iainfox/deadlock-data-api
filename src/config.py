"""Paths and constants used when building items_data.json."""

import os

# Soul cost by item tier (index = tier).
TIER_PRICES = [0, 800, 1600, 3200, 6400, 9999]

# Maps the raw engine slot enum to the display category used in output.
SLOT_DISPLAY_NAMES = {
    'EItemSlotType_Armor': 'Vitality',
    'EItemSlotType_WeaponMod': 'Weapon',
    'EItemSlotType_Tech': 'Spirit',
}

# Stat keys that get promoted to top-level fields on each item (with the
# leading "Ability" stripped and lowercased, e.g. AbilityCooldown -> cooldown).
PROMOTED_STAT_KEYS = [
    'AbilityCooldown',
    'AbilityDuration',
    'AbilityCastRange',
    'AbilityCharges',
]


def find_repo_dir(start_dir, marker=('data', 'game', 'citadel'), max_levels_up=4):
    """Walk upward from start_dir looking for a directory containing `marker`.

    start_dir is the extract_items.py script's own directory (src/), so the
    repo root is at least one level above it. Falls back to the highest
    directory reached if the marker is never found.
    """
    repo_dir = start_dir
    for _ in range(max_levels_up):
        if os.path.exists(os.path.join(repo_dir, *marker)):
            break
        repo_dir = os.path.dirname(repo_dir)
    return repo_dir


class Paths:
    """Resolved input/output file paths, relative to the repo root.

    Game data lives under <repo_dir>/data/game/citadel/...; output is
    written to <repo_dir>/items_data.json.
    """

    def __init__(self, repo_dir):
        self.repo_dir = repo_dir
        game_dir = os.path.join(repo_dir, 'data', 'game', 'citadel')

        self.abilities = os.path.join(
            game_dir, 'pak01_dir', 'scripts', 'abilities.vdata'
        )
        self.mod_names = os.path.join(
            game_dir, 'resource', 'localization',
            'citadel_gc_mod_names', 'citadel_gc_mod_names_english.txt',
        )
        self.mod_descriptions = os.path.join(
            game_dir, 'resource', 'localization',
            'citadel_mods', 'citadel_mods_english.txt',
        )
        self.output_json = os.path.join(repo_dir, 'items_data.json')
