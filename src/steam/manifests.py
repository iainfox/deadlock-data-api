import re
import subprocess

from steam.settings import APP_ID, STEAMCMD_PATH, log


def get_current_manifests(known_depot_ids: list[str] | None = None) -> dict:
    log.info("Querying Steam for current app info...")
    cmd = [STEAMCMD_PATH, "+login", "anonymous", "+app_info_print", APP_ID, "+quit"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
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

    if not manifests:
        log.warning(
            "No manifests parsed from app_info_print output. "
            "Steam's VDF format can shift -- inspect raw output with "
            "`steamcmd +login anonymous +app_info_print %s +quit` and adjust the regex.",
            APP_ID,
        )

    if known_depot_ids:
        manifests = {d: m for d, m in manifests.items() if d in known_depot_ids}

    return manifests
