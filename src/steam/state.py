import json
from datetime import datetime, timezone

from steam.settings import STATE_FILE


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"manifests": {}, "last_checked": None}


def save_state(state: dict) -> None:
    state["last_checked"] = datetime.now(timezone.utc).isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2))
