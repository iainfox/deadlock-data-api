import subprocess
from pathlib import Path

from steam.settings import APP_ID, STEAM_USER, STEAM_PASS, DEPOTDOWNLOADER_DLL, DOWNLOAD_DIR, log


def download_depot(depot_id: str, manifest_id: str) -> Path:
    if not STEAM_USER or not STEAM_PASS:
        raise RuntimeError("STEAM_USER / STEAM_PASS environment variables are not set.")

    out_dir = DOWNLOAD_DIR / depot_id
    out_dir.mkdir(parents=True, exist_ok=True)

    log.info("Downloading depot %s @ manifest %s -> %s", depot_id, manifest_id, out_dir)

    depotdownloader_exe = Path(DEPOTDOWNLOADER_DLL)
    if depotdownloader_exe.suffix.lower() == ".exe":
        cmd = [str(depotdownloader_exe)]
    else:
        cmd = ["dotnet", str(depotdownloader_exe)]

    cmd += [
        "-app", APP_ID,
        "-depot", depot_id,
        "-manifest", manifest_id,
        "-username", STEAM_USER,
        "-password", STEAM_PASS,
        "-remember-password",
        "-dir", str(out_dir),
        "-validate",
    ]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        log.error("DepotDownloader failed for depot %s (exit code %d)", depot_id, result.returncode)
        raise RuntimeError(f"DepotDownloader exited with code {result.returncode}")

    log.info("Depot %s downloaded successfully.", depot_id)
    return out_dir
