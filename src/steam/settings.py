import logging
import os
import sys
from pathlib import Path

import dotenv

dotenv.load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

APP_ID = "1422450"

BASE_DIR = Path(os.environ.get("DEADLOCK_TRACKER_DIR", Path(__file__).parent.parent.parent / "data" / "tracker"))
STATE_FILE = BASE_DIR / "state.json"
DOWNLOAD_DIR = BASE_DIR / "depots"
LOG_FILE = BASE_DIR / "tracker.log"

STEAMCMD_PATH = os.environ.get("STEAMCMD_PATH", "steamcmd")
DEPOTDOWNLOADER_DLL = os.environ.get("DEPOTDOWNLOADER_DLL", str(Path.home() / "DepotDownloader" / "DepotDownloader.dll"))

VRF_CLI_PATH = os.environ.get("VRF_CLI_PATH", str(Path.home() / "ValveResourceFormat" / "Source2Viewer-CLI"))

VPK_EXTENSIONS = "txt,lua,kv3,db,gameevents,vcss_c,vjs_c,vts_c,vxml_c,vsndevts_c,vsndstck_c,vpulse_c,vdata_c"

STEAM_USER = os.environ.get("STEAM_USER")
STEAM_PASS = os.environ.get("STEAM_PASS")
STEAM_SHARED_SECRET = os.environ.get("STEAM_SHARED_SECRET")

KNOWN_DEPOT_IDS = ["1422451", "1422452", "1422456"]

BASE_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("deadlock_tracker")
