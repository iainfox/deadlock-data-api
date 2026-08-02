import base64
import hashlib
import hmac
import struct
import time


def generate_code(shared_secret: str) -> str:
    key = base64.b64decode(shared_secret)
    message = struct.pack(">Q", int(time.time()) // 30)
    digest = hmac.new(key, message, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % 100000
    return f"{code:05d}"


def steam_guard_arg(shared_secret: str | None) -> list[str]:
    if not shared_secret:
        return []
    return [generate_code(shared_secret)]
