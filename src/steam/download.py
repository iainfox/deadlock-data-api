import shutil
import subprocess
from pathlib import Path

from steam.settings import APP_ID, STEAM_USER, STEAM_PASS, STEAMCMD_PATH, DOWNLOAD_DIR, log


def _steamcmd_home() -> Path:
    return Path(STEAMCMD_PATH).parent


def download_depot(depot_id: str, manifest_id: str) -> Path:
    out_dir = DOWNLOAD_DIR / depot_id
    out_dir.mkdir(parents=True, exist_ok=True)

    if STEAM_USER:
        login = [STEAM_USER] + ([STEAM_PASS] if STEAM_PASS else [])
        log.info("Downloading depot %s @ manifest %s as %s", depot_id, manifest_id, STEAM_USER)
    else:
        login = ["anonymous"]
        log.info("Downloading depot %s @ manifest %s anonymously", depot_id, manifest_id)

    cmd = [
        STEAMCMD_PATH,
        "+login", *login,
        "+download_depot", APP_ID, depot_id, manifest_id,
        "+quit",
    ]
    log.info("Running SteamCMD: %s", " ".join(cmd[:6]) + " ... +download_depot ...")
    result = subprocess.run(cmd, cwd=_steamcmd_home(), text=True)
    if result.returncode != 0:
        log.error("SteamCMD download failed for depot %s (exit code %d)", depot_id, result.returncode)
        raise RuntimeError(f"SteamCMD exited with code {result.returncode}")

    content_dir = _steamcmd_home() / "steamapps" / "content" / f"app_{APP_ID}" / f"depot_{depot_id}"
    if not content_dir.exists():
        log.error("SteamCMD did not produce content at %s", content_dir)
        raise RuntimeError(f"SteamCMD produced no content for depot {depot_id}")

    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.move(str(content_dir), str(out_dir))
    shutil.rmtree(_steamcmd_home() / "steamapps" / "content" / f"app_{APP_ID}", ignore_errors=True)

    log.info("Depot %s downloaded successfully to %s", depot_id, out_dir)
    return out_dir
