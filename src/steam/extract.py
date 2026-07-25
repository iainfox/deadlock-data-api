import subprocess
from pathlib import Path

from steam.settings import VRF_CLI_PATH, VPK_EXTENSIONS, log


def find_vpks(depot_dir: Path) -> list[Path]:
    return sorted(depot_dir.rglob("*_dir.vpk"))


def extract_vpk(vpk_path: Path) -> Path:
    out_dir = Path(str(vpk_path).replace("_dir.vpk", "") + "/")
    out_dir.mkdir(parents=True, exist_ok=True)

    log.info("Extracting %s -> %s", vpk_path, out_dir)
    cmd = [
        VRF_CLI_PATH,
        "--input", str(vpk_path),
        "--output", str(out_dir),
        "--vpk_cache",
        "--vpk_decompile",
        "--vpk_extensions", VPK_EXTENSIONS,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.error("VRF extraction failed for %s:\n%s", vpk_path, result.stdout + result.stderr)
        raise RuntimeError(f"Source2Viewer-CLI exited with code {result.returncode}")

    log.info("Extraction complete: %s", out_dir)
    return out_dir


def extract_depot(depot_dir: Path) -> list[Path]:
    vpks = find_vpks(depot_dir)
    if not vpks:
        log.info("No VPKs found under %s (nothing to extract).", depot_dir)
        return []

    extracted = []
    for vpk_path in vpks:
        try:
            extracted.append(extract_vpk(vpk_path))
        except Exception:
            log.exception("Failed to extract %s -- continuing with other VPKs.", vpk_path)
    return extracted
