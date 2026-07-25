"""
Minimal parser for Valve's KV3 (KeyValues3) text format.

KV3 looks like a relaxed JSON/HOCON hybrid:

    m_iItemTier = 2
    m_vecTags = [
        "tag_a"
        "tag_b"
    ]
    m_mapAbilityProperties =
    {
        SomeProp = { m_strValue = "10" }
    }

This module only implements the subset of KV3 needed to read ability/item
definitions: scalars, nested objects, arrays, and the "value on the next
line" style shown above. It does not attempt to be a general-purpose KV3
parser (no comments-as-data, no multiline strings, no resource references).
"""

import re

_KEY_VALUE_RE = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.*?)(?:\s*//.*)?$')


def parse_simple_value(raw):
    if not isinstance(raw, str):
        return raw

    value = raw.strip().strip(',')

    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]

    try:
        return int(value)
    except ValueError:
        pass

    try:
        as_float = float(value)
        return int(as_float) if as_float == int(as_float) else as_float
    except ValueError:
        pass

    return value


def extract_balanced(lines, start_idx):
    first_line = lines[start_idx].strip()
    if first_line.startswith('{'):
        open_char, close_char = '{', '}'
    elif first_line.startswith('['):
        open_char, close_char = '[', ']'
    else:
        return '', start_idx

    depth = 0
    started = False
    collected_lines = []
    line_idx = start_idx

    while line_idx < len(lines):
        stripped = lines[line_idx].strip()
        in_string = False
        escape_next = False
        line_out = []

        for ch in stripped:
            if escape_next:
                escape_next = False
                line_out.append(ch)
                continue
            if ch == '\\':
                escape_next = True
                line_out.append(ch)
                continue
            if ch == '"':
                in_string = not in_string
                line_out.append(ch)
                continue

            if not in_string:
                if ch == open_char:
                    depth += 1
                    if not started:
                        started = True
                        continue
                elif ch == close_char:
                    depth -= 1
                    if depth == 0:
                        if line_out:
                            collected_lines.append(''.join(line_out))
                        return '\n'.join(collected_lines), line_idx

            line_out.append(ch)

        if started and depth > 0:
            collected_lines.append(''.join(line_out))

        line_idx += 1

    return '\n'.join(collected_lines), line_idx - 1


def parse_kv3_obj(text):
    if not text or not text.strip():
        return {}

    lines = text.split('\n')
    result = {}
    i = 0

    while i < len(lines):
        stripped = lines[i].strip()

        if not stripped or stripped.startswith('<!--'):
            i += 1
            continue

        match = _KEY_VALUE_RE.match(stripped)
        if not match:
            i += 1
            continue

        key, rest = match.group(1), match.group(2).strip()

        if rest.startswith('{'):
            obj_text, end_line = extract_balanced(lines, i)
            result[key] = parse_kv3_obj(obj_text)
            i = end_line + 1
        elif rest.startswith('['):
            arr_text, end_line = extract_balanced(lines, i)
            result[key] = parse_kv3_arr(arr_text)
            i = end_line + 1
        elif rest == '':
            i = _parse_value_on_next_line(lines, i, key, result)
        else:
            result[key] = parse_simple_value(rest)
            i += 1

    return result


def _parse_value_on_next_line(lines, i, key, result):
    if i + 1 >= len(lines):
        return i + 1

    next_stripped = lines[i + 1].strip()
    if next_stripped.startswith('{'):
        obj_text, end_line = extract_balanced(lines, i + 1)
        result[key] = parse_kv3_obj(obj_text)
        return end_line + 1
    if next_stripped.startswith('['):
        arr_text, end_line = extract_balanced(lines, i + 1)
        result[key] = parse_kv3_arr(arr_text)
        return end_line + 1
    return i + 1


def parse_kv3_arr(text):
    if not text or not text.strip():
        return []

    lines = text.split('\n')
    result = []
    i = 0

    while i < len(lines):
        stripped = lines[i].strip().rstrip(',')

        if not stripped or stripped.startswith('<!--'):
            i += 1
            continue

        if stripped.startswith('{'):
            obj_text, end_line = extract_balanced(lines, i)
            result.append(parse_kv3_obj(obj_text))
            i = end_line + 1
        elif stripped.startswith('['):
            arr_text, end_line = extract_balanced(lines, i)
            result.append(parse_kv3_arr(arr_text))
            i = end_line + 1
        elif stripped.startswith('subclass:'):
            i = _parse_subclass_entry(lines, i, stripped, result)
        elif stripped.startswith('"') and stripped.endswith('"'):
            result.append(parse_simple_value(stripped))
            i += 1
        else:
            value = parse_simple_value(stripped)
            if value != '':
                result.append(value)
            i += 1

    return result


def _parse_subclass_entry(lines, i, stripped, result):
    rest = stripped[len('subclass:'):].strip()

    if rest.startswith('{'):
        obj_text, end_line = extract_balanced(lines, i)
        result.append(parse_kv3_obj(obj_text))
        return end_line + 1

    if rest == '' and i + 1 < len(lines) and lines[i + 1].strip().startswith('{'):
        obj_text, end_line = extract_balanced(lines, i + 1)
        result.append(parse_kv3_obj(obj_text))
        return end_line + 1

    return i + 1
