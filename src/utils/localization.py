"""Reader for Steam/Source engine localization files.

These files look like:

    "lang"
    {
        "Language" "english"
        "Tokens"
        {
            "some_key"    "Some Value"
            "another_key" "Another Value"
        }
    }

We only care about the flat "key" "value" pairs inside the "Tokens" block.
"""

import re

_TOKENS_BLOCK_RE = re.compile(r'"Tokens"\s*\n\s*\{')
_TOKEN_PAIR_RE = re.compile(r'"((?:\\.|[^"\\])*)"\s+"((?:\\.|[^"\\])*)"')

_ESCAPE_SEQUENCES = {
    '\\"': '"',
    '\\\\': '\\',
    '\\n': '\n',
    '\\t': '\t',
}
_ESCAPE_RE = re.compile(r'\\.')


def _unescape(text):
    return _ESCAPE_RE.sub(lambda m: _ESCAPE_SEQUENCES.get(m.group(0), m.group(0)), text)


def parse_steam_localization(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    tokens_text = _extract_tokens_block(content)
    if tokens_text is None:
        return {}

    return {
        _unescape(key): _unescape(value)
        for key, value in _TOKEN_PAIR_RE.findall(tokens_text)
    }


def _extract_tokens_block(content):
    match = _TOKENS_BLOCK_RE.search(content)
    if not match:
        return None

    pos = match.end()
    depth = 1
    chars = []

    while pos < len(content) and depth > 0:
        ch = content[pos]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                break
        chars.append(ch)
        pos += 1

    return ''.join(chars)
