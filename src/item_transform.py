"""Turns a raw parsed ability/item dict (from kv3_parser) into the clean,
JSON-serializable item record used in items_data.json.
"""

import re

from config import PROMOTED_STAT_KEYS, SLOT_DISPLAY_NAMES, TIER_PRICES
from kv3_parser import parse_simple_value

_TIER_DIGIT_RE = re.compile(r'(\d+)')


def get_str_list(value):
    """Normalize a KV3 value that may be a single string or a list of strings."""
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [value]
    return []


def extract_stats(item):
    """Return {stat_name: {'value': ..., 'usage': ...}} from an item's
    m_mapAbilityProperties map."""
    props = item.get('m_mapAbilityProperties', {})
    if not isinstance(props, dict):
        return {}

    stats = {}
    for name, definition in props.items():
        if isinstance(definition, dict):
            stats[name] = {
                'value': definition.get('m_strValue', '0'),
                'usage': definition.get('m_eStatsUsageFlags', ''),
            }
    return stats


def parse_tier(item):
    """Extract the numeric tier from m_iItemTier (e.g. 'EItemTier_2' -> 2)."""
    tier_match = _TIER_DIGIT_RE.search(str(item.get('m_iItemTier', '')))
    return int(tier_match.group(1)) if tier_match else 0


def determine_activation(item):
    return 'Passive' if 'PASSIVE' in str(item.get('m_eAbilityActivation', '')) else 'Active'


def determine_slot(item):
    raw_slot = str(item.get('m_eItemSlotType', ''))
    return SLOT_DISPLAY_NAMES.get(raw_slot, raw_slot)


def determine_availability(item):
    """Classify an item as main_game / street_brawl / in_dev."""
    disabled = str(item.get('m_bDisabled', '')).lower() in ('true', '1')
    not_pickable = item.get('_not_pickable', 0)
    is_street_brawl = 'ERequirementStreetBrawl' in str(item.get('m_eAbilityRequirements', ''))

    if disabled or not_pickable:
        return 'in_dev'
    if is_street_brawl:
        return 'street_brawl'
    return 'main_game'


def extract_passive_property_names(item):
    """Property names auto-registered by the item's intrinsic modifiers."""
    intrinsics = item.get('m_AutoIntrinsicModifiers', [])
    if isinstance(intrinsics, dict):
        intrinsics = [intrinsics]

    names = set()
    for modifier in intrinsics if isinstance(intrinsics, list) else []:
        if isinstance(modifier, dict):
            names.update(get_str_list(
                modifier.get('m_vecAutoRegisterModifierValueFromAbilityPropertyName', [])
            ))
    return names


def extract_active_property_names(item):
    """Property names auto-registered by the item's active buff/caster modifier."""
    modifier = item.get('m_BuffModifier') or item.get('m_CasterModifier')
    if not isinstance(modifier, dict):
        return set()
    return set(get_str_list(
        modifier.get('m_vecAutoRegisterModifierValueFromAbilityPropertyName', [])
    ))


def extract_upgrades(item):
    """Return a list of {property_name: bonus_value} dicts, one per upgrade tier."""
    upgrades = item.get('m_vecAbilityUpgrades', [])
    if isinstance(upgrades, dict):
        upgrades = [upgrades]

    parsed = []
    for entry in upgrades if isinstance(upgrades, list) else []:
        if not isinstance(entry, dict):
            continue
        property_upgrades = entry.get('m_vecPropertyUpgrades', [])
        if isinstance(property_upgrades, dict):
            property_upgrades = [property_upgrades]

        upgrade_dict = {}
        for prop in property_upgrades if isinstance(property_upgrades, list) else []:
            if isinstance(prop, dict):
                name = prop.get('m_strPropertyName', '')
                bonus = prop.get('m_strBonus', '')
                if name:
                    upgrade_dict[name] = parse_simple_value(bonus)

        if upgrade_dict:
            parsed.append(upgrade_dict)

    return parsed


def extract_tooltip_descriptions(item, descriptions):
    """Resolve tooltip section attributes (#loc_key references) against
    the localization dict, returning [{'section': ..., 'description': ...}]."""
    sections = item.get('m_vecTooltipSectionInfo', [])
    if isinstance(sections, dict):
        sections = [sections]

    results = []
    for section in sections if isinstance(sections, list) else []:
        if not isinstance(section, dict):
            continue

        attributes = section.get('m_vecSectionAttributes', [])
        if isinstance(attributes, dict):
            attributes = [attributes]

        for attribute in attributes if isinstance(attributes, list) else []:
            if not isinstance(attribute, dict):
                continue
            loc_string = attribute.get('m_strLocString', '')
            if isinstance(loc_string, str) and loc_string.startswith('#'):
                loc_key = loc_string[1:]
                if loc_key in descriptions:
                    results.append({
                        'section': section.get('m_eAbilitySectionType', ''),
                        'description': descriptions[loc_key],
                    })

    return results


def build_clean_stats(stats):
    """Convert extract_stats() output into the clean per-item 'stats' field."""
    clean_stats = {}
    for name, definition in stats.items():
        if not isinstance(definition, dict):
            continue
        entry = {'value': parse_simple_value(definition.get('value', ''))}
        usage = definition.get('usage', '')
        if usage and usage not in ('', 'IntrinsicallyProvidedInAbility'):
            entry['usage'] = usage
        clean_stats[name] = entry
    return clean_stats


def build_item_record(item_id, item, names, descriptions):
    """Build the full clean output record for a single item."""
    tier = parse_tier(item)
    stats = extract_stats(item)

    passive_props = extract_passive_property_names(item)
    active_props = extract_active_property_names(item)

    components = item.get('m_vecComponentItems', [])
    if isinstance(components, str):
        components = [components]

    record = {
        'id': item_id,
        'display_name': names.get(item_id, item_id).strip(),
        'description': descriptions.get(f"{item_id}_desc", ''),
        'tier': tier,
        'soul_cost': TIER_PRICES[tier] if 0 <= tier < len(TIER_PRICES) else 0,
        'slot': determine_slot(item),
        'activation': determine_activation(item),
        'available_in': determine_availability(item),
        'stats': build_clean_stats(stats),
        'passive': {
            name: parse_simple_value(stats[name].get('value', ''))
            for name in passive_props if name in stats
        },
        'active': {
            name: parse_simple_value(stats[name].get('value', ''))
            for name in active_props if name in stats
        },
    }

    for key in PROMOTED_STAT_KEYS:
        if key in stats:
            field_name = key.replace('Ability', '').lower()
            record[field_name] = parse_simple_value(stats[key].get('value', ''))

    if components:
        record['components'] = components

    upgrades = extract_upgrades(item)
    if upgrades:
        record['upgrades'] = upgrades

    tooltip_descriptions = extract_tooltip_descriptions(item, descriptions)
    if tooltip_descriptions:
        record['tooltip_descriptions'] = tooltip_descriptions

    return record
