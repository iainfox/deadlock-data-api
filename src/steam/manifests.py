import re
import subprocess
from pathlib import Path

from steam.settings import APP_ID, STEAMCMD_PATH, STEAM_USER, STEAM_PASS, STEAM_SHARED_SECRET, log
from steam.totp import steam_guard_arg


def get_current_manifests(known_depot_ids: list[str] | None = None) -> dict:
    log.info("Querying Steam for current app info...")
    manifests = _query_manifests(["anonymous"])
    if not manifests and STEAM_USER:
        log.info("Anonymous app info incomplete for app %s, retrying with account login...", APP_ID)
        manifests = _query_manifests([STEAM_USER] + ([STEAM_PASS] if STEAM_PASS else []) + steam_guard_arg(STEAM_SHARED_SECRET))

    if not manifests:
        log.warning(
            "No manifests parsed from app_info_print output. "
            "Steam's VDF format can shift or anonymous access may be denied "
            "for app %s -- inspect the raw output and adjust the regex/login.",
            APP_ID,
        )

    if known_depot_ids:
        manifests = {d: m for d, m in manifests.items() if d in known_depot_ids}

    return manifests


def _query_manifests(login: list[str]) -> dict:
    cmd = [STEAMCMD_PATH, "+login", *login, "+app_info_print", APP_ID, "+quit"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=Path(STEAMCMD_PATH).parent)
    output = result.stdout + result.stderr

    manifests = {}
    depot_block_re = re.compile(r'"(\d{5,})"\s*\n\s*\{')
    for match in depot_block_re.finditer(output):
        depot_id = match.group(1)
        start = match.end()
        window = output[start:start + 2000]
        gid_match = re.search(r'"public"\s*\n\s*\{\s*\n\s*"gid"\s*"(\d+)"', window)
        if gid_match:
            manifests[depot_id] = gid_match.group(1)

    return manifests
