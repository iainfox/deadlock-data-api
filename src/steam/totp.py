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


def wait_for_next_window(buffer: float = 2.0) -> None:
    """Sleep until the next 30s TOTP window starts (plus a small buffer).

    Steam Guard codes are single-use per window, so a code generated after
    this call is guaranteed to differ from any code generated before it.
    """
    now = time.time()
    delay = (int(now) // 30 + 1) * 30 + buffer - now
    if delay > 0:
        time.sleep(delay)


def steam_guard_arg(shared_secret: str | None) -> list[str]:
    if not shared_secret:
        return []
    return [generate_code(shared_secret)]
