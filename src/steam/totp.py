import base64
import hashlib
import hmac
import struct
import time

_CHARSET = "23456789BCDFGHJKMNPQRTVWXY"


def generate_code(shared_secret: str) -> str:
    key = base64.b64decode(shared_secret)
    message = struct.pack(">Q", int(time.time()) // 30)
    digest = hmac.new(key, message, hashlib.sha1).digest()
    start = digest[19] & 0x0F
    codeint = struct.unpack(">I", digest[start:start + 4])[0] & 0x7FFFFFFF

    code = ""
    for _ in range(5):
        codeint, i = divmod(codeint, len(_CHARSET))
        code += _CHARSET[i]
    return code


def steam_guard_arg(shared_secret: str | None) -> list[str]:
    if not shared_secret:
        return []
    return [generate_code(shared_secret)]
