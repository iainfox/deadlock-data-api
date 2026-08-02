import shutil
import subprocess
from pathlib import Path

from steam.settings import APP_ID, STEAM_USER, STEAM_PASS, STEAM_SHARED_SECRET, STEAMCMD_PATH, DOWNLOAD_DIR, log
from steam.totp import steam_guard_arg, wait_for_next_window


def _steamcmd_home() -> Path:
    return Path(STEAMCMD_PATH).parent


def download_depots(depot_manifests: dict[str, str]) -> dict[str, Path]:
    """Download all given depots in a single SteamCMD login.

    One login means one Steam Guard code: reusing the same 30s-window code
    across multiple logins makes Steam reject the later ones (error 88). We
    also wait for the next TOTP window so this code can't equal the one used
    by the manifest query earlier in the run.
    """
    if not depot_manifests:
        return {}

    content_root = _steamcmd_home() / "steamapps" / "content" / f"app_{APP_ID}"

    if STEAM_USER:
        if STEAM_SHARED_SECRET:
            wait_for_next_window()
        login = [STEAM_USER] + ([STEAM_PASS] if STEAM_PASS else []) + steam_guard_arg(STEAM_SHARED_SECRET)
        log.info("Downloading %d depot(s) as %s", len(depot_manifests), STEAM_USER)
    else:
        login = ["anonymous"]
        log.info("Downloading %d depot(s) anonymously", len(depot_manifests))

    cmd = [STEAMCMD_PATH, "+login", *login]
    for depot_id, manifest_id in depot_manifests.items():
        cmd += ["+download_depot", APP_ID, depot_id, manifest_id]
    cmd += ["+quit"]
    log.info("Running SteamCMD: %s", " ".join(cmd[:6]) + " ... +download_depot ...")

    result = subprocess.run(cmd, cwd=_steamcmd_home(), text=True)

    downloaded = {}
    for depot_id, manifest_id in depot_manifests.items():
        content_dir = content_root / f"depot_{depot_id}"
        if not content_dir.exists() or not any(content_dir.rglob("*")):
            log.error("SteamCMD produced no content for depot %s (exit code %d)", depot_id, result.returncode)
            continue
        out_dir = DOWNLOAD_DIR / depot_id
        out_dir.mkdir(parents=True, exist_ok=True)
        if out_dir.exists():
            shutil.rmtree(out_dir)
        shutil.move(str(content_dir), str(out_dir))
        downloaded[depot_id] = out_dir
        log.info("Depot %s downloaded successfully to %s", depot_id, out_dir)

    shutil.rmtree(content_root, ignore_errors=True)

    return downloaded
