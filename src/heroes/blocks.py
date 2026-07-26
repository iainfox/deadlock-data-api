import re

from utils.kv3_parser import extract_balanced

_HERO_HEADER_RE = re.compile(r'(hero_[a-zA-Z0-9_/]+|hero_base)\s*=\s*(\{?)')

_ABILITY_HEADER_RE = re.compile(r'((?:citadel_)?(?:ability|weapon)_[a-zA-Z0-9_/]+)\s*=\s*(\{?)')


def _read_stripping_bom(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    if content.startswith('\ufeff'):
        content = content[1:]
    return content


def _consume_block(lines, i, match, items, regex):
    name, opener_on_same_line = match.group(1), match.group(2)

    if opener_on_same_line == '{':
        obj_text, end_line = extract_balanced(lines, i)
        items[name] = obj_text
        return end_line + 1

    if i + 1 < len(lines) and lines[i + 1].strip() == '{':
        obj_text, end_line = extract_balanced(lines, i + 1)
        items[name] = obj_text
        return end_line + 1

    return i + 1


def _extract_blocks(filepath, regex):
    content = _read_stripping_bom(filepath)
    lines = content.split('\n')

    items = {}
    i = 0
    while i < len(lines):
        match = regex.match(lines[i].strip())
        if match:
            i = _consume_block(lines, i, match, items, regex)
        else:
            i += 1

    return items


def extract_hero_blocks(filepath):
    return _extract_blocks(filepath, _HERO_HEADER_RE)


def extract_ability_blocks(filepath):
    return _extract_blocks(filepath, _ABILITY_HEADER_RE)
