import subprocess
from pathlib import Path

from steam.settings import APP_ID, STEAM_USER, STEAM_PASS, DEPOTDOWNLOADER_DLL, DOWNLOAD_DIR, log


def download_depot(depot_id: str, manifest_id: str) -> Path:
    out_dir = DOWNLOAD_DIR / depot_id
    out_dir.mkdir(parents=True, exist_ok=True)

    depotdownloader_exe = Path(DEPOTDOWNLOADER_DLL)
    if depotdownloader_exe.suffix.lower() == ".exe":
        cmd = [str(depotdownloader_exe)]
    else:
        cmd = ["dotnet", str(depotdownloader_exe)]

    cmd += ["-app", APP_ID, "-depot", depot_id, "-manifest", manifest_id]

    if STEAM_USER:
        cmd += ["-username", STEAM_USER]
        if STEAM_PASS:
            cmd += ["-password", STEAM_PASS]
        cmd += ["-remember-password"]
        log.info("Downloading depot %s @ manifest %s as %s", depot_id, manifest_id, STEAM_USER)
    else:
        log.info("Downloading depot %s @ manifest %s anonymously", depot_id, manifest_id)

    cmd += ["-dir", str(out_dir), "-validate"]
    log.info("Output -> %s", out_dir)

    result = subprocess.run(cmd)
    if result.returncode != 0:
        log.error("DepotDownloader failed for depot %s (exit code %d)", depot_id, result.returncode)
        raise RuntimeError(f"DepotDownloader exited with code {result.returncode}")

    log.info("Depot %s downloaded successfully.", depot_id)
    return out_dir
