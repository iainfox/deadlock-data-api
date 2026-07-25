import os
from pathlib import Path

TIER_PRICES = [0, 800, 1600, 3200, 6400, 9999]

SLOT_DISPLAY_NAMES = {
    'EItemSlotType_Armor': 'Vitality',
    'EItemSlotType_WeaponMod': 'Weapon',
    'EItemSlotType_Tech': 'Spirit',
}

PROMOTED_STAT_KEYS = [
    'AbilityCooldown',
    'AbilityDuration',
    'AbilityCastRange',
    'AbilityCharges',
]


def _find_file(data_dir, *rel_path):
    """Look for a file under data_dir. Try exact path first, then recursive search."""
    exact = os.path.join(data_dir, *rel_path)
    if os.path.exists(exact):
        return exact
    matches = list(Path(data_dir).rglob(rel_path[-1]))
    if matches:
        return str(matches[0])
    return exact


class Paths:
    def __init__(self, data_dir, output_path=None):
        self.data_dir = data_dir
        self.abilities = _find_file(data_dir, 'pak01_dir', 'scripts', 'abilities.vdata')
        self.mod_names = _find_file(
            data_dir, 'resource', 'localization',
            'citadel_gc_mod_names', 'citadel_gc_mod_names_english.txt',
        )
        self.mod_descriptions = _find_file(
            data_dir, 'resource', 'localization',
            'citadel_mods', 'citadel_mods_english.txt',
        )
        self.output_json = output_path
