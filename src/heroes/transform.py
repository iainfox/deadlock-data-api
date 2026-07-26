import re

from config import PROMOTED_STAT_KEYS
from utils.kv3_parser import parse_simple_value


_SLOT_TO_KEY = {
    'ESlot_Signature_1': 1,
    'ESlot_Signature_2': 2,
    'ESlot_Signature_3': 3,
    'ESlot_Signature_4': 4,
}


def get_str_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [value]
    return []


def extract_stats(item):
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


def build_clean_stats(stats):
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


def extract_upgrades(item):
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


def determine_ability_activation(item):
    return item.get('m_eAbilityActivation', '')


def determine_available(item):
    disabled = str(item.get('m_bDisabled', '')).lower() in ('true', '1')
    not_pickable = item.get('_not_pickable', 0)
    in_dev = str(item.get('m_bInDevelopment', '')).lower() in ('true', '1')

    if disabled or not_pickable or in_dev:
        return 'in_dev'
    return 'main_game'


def _resolve_localization(ability_id, loc_names):
    key = ability_id
    if key in loc_names:
        return loc_names[key]
    citadel_key = f'citadel_{ability_id}'
    if citadel_key in loc_names:
        return loc_names[citadel_key]
    return ability_id


def _resolve_localization_desc(ability_id, loc_descriptions):
    key = f'{ability_id}_desc'
    if key in loc_descriptions:
        return loc_descriptions[key]
    citadel_key = f'citadel_{ability_id}_desc'
    if citadel_key in loc_descriptions:
        return loc_descriptions[citadel_key]
    return ''


def build_ability_record(ability_id, ability, loc_names, loc_descriptions):
    stats = extract_stats(ability)

    upgrades = extract_upgrades(ability)

    record = {
        'id': ability_id,
        'display_name': _resolve_localization(ability_id, loc_names),
        'description': _resolve_localization_desc(ability_id, loc_descriptions),
        'activation': determine_ability_activation(ability),
        'stats': build_clean_stats(stats),
    }

    for key in PROMOTED_STAT_KEYS:
        if key in stats:
            field_name = key.replace('Ability', '').lower()
            record[field_name] = parse_simple_value(stats[key].get('value', ''))

    if upgrades:
        record['upgrades'] = upgrades

    tooltip_descriptions = extract_tooltip_descriptions(ability, loc_descriptions)
    if tooltip_descriptions:
        record['tooltip_descriptions'] = tooltip_descriptions

    return record


def _extract_weapon_ability(hero_item, abilities_dict, loc_names, loc_descriptions):
    bound = hero_item.get('m_mapBoundAbilities', {})
    if not isinstance(bound, dict):
        return None
    weapon_id = bound.get('ESlot_Weapon_Primary', '')
    if not weapon_id or weapon_id not in abilities_dict:
        return None
    return build_ability_record(weapon_id, abilities_dict[weapon_id], loc_names, loc_descriptions)


def build_hero_record(hero_id, hero_item, abilities_dict, loc_names, loc_descriptions, hero_names):
    bound = hero_item.get('m_mapBoundAbilities', {})
    if not isinstance(bound, dict):
        bound = {}

    starting_stats = hero_item.get('m_mapStartingStats', {})
    if not isinstance(starting_stats, dict):
        starting_stats = {}

    standard_level_up = hero_item.get('m_mapStandardLevelUpUpgrades', {})
    if not isinstance(standard_level_up, dict):
        standard_level_up = {}

    scaling_stats = hero_item.get('m_mapScalingStats', {})
    if not isinstance(scaling_stats, dict):
        scaling_stats = {}

    raw_tags = hero_item.get('m_vecHeroTags', [])
    if isinstance(raw_tags, str):
        raw_tags = [raw_tags]

    tags = []
    for tag in raw_tags if isinstance(raw_tags, list) else []:
        if isinstance(tag, str) and tag.startswith('#'):
            loc_key = tag[1:]
            tags.append(loc_descriptions.get(loc_key, tag))
        else:
            tags.append(str(tag))

    name_key = f'{hero_id}:n'
    display_name = hero_names.get(name_key, hero_id).strip()

    desc_key = f'{hero_id}_desc'
    description = loc_descriptions.get(desc_key, '')

    record = {
        'id': hero_id,
        'display_name': display_name.strip(),
        'description': description,
        'hero_id': hero_item.get('m_HeroID', 0),
        'complexity': hero_item.get('m_nComplexity', 0),
        'available_in': determine_available(hero_item),
        'stats': {k: parse_simple_value(v) for k, v in starting_stats.items()},
        'stat_scaling': {k: parse_simple_value(v) for k, v in standard_level_up.items()},
        'tags': tags,
    }

    if scaling_stats:
        record['scaling_stats'] = {k: parse_simple_value(v) for k, v in scaling_stats.items()}

    weapon = _extract_weapon_ability(hero_item, abilities_dict, loc_descriptions, loc_descriptions)
    if weapon:
        record['weapon'] = weapon

    abilities = {}
    for slot, key in sorted(_SLOT_TO_KEY.items(), key=lambda x: x[1]):
        ability_id = bound.get(slot, '')
        if ability_id and ability_id in abilities_dict:
            abilities[str(key)] = build_ability_record(
                ability_id, abilities_dict[ability_id], loc_descriptions, loc_descriptions
            )

    if abilities:
        record['abilities'] = abilities

    return record
