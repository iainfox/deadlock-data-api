"""Snapshot archiving for extracted game data.

Every extraction run stores a copy of items/heroes data under
``<archive>/<build_id>/items_data.json`` / ``heroes_data.json`` so past game
versions can be served later. An ``index.json`` keeps per-build metadata
(build_id, capture time, manifests, content hashes) for fast lookups.
"""

import copy
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

FILENAMES = {
    "items": "items_data.json",
    "heroes": "heroes_data.json",
}

_SAFE_BUILD_ID = re.compile(r"[^0-9A-Za-z_.-]")


def _current_manifests() -> dict:
    try:
        from steam.state import load_state
        return load_state().get("manifests", {})
    except Exception:
        return {}


def get_build_id() -> str:
    manifests = _current_manifests()
    if manifests:
        parts = [f"{depot}_{gid}" for depot, gid in sorted(manifests.items())]
        build_id = "_".join(parts)
    else:
        build_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return _SAFE_BUILD_ID.sub("_", build_id)


def resolve_archive_dir(output_path, archive_dir=None) -> Path:
    if archive_dir:
        return Path(archive_dir)
    env = os.environ.get("DEADLOCK_ARCHIVE_DIR")
    if env:
        return Path(env)
    return Path(output_path).resolve().parent / "archive"


def _load_index(archive_dir: Path) -> dict:
    path = archive_dir / "index.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"builds": {}}


def _save_index(archive_dir: Path, index: dict) -> None:
    archive_dir.mkdir(parents=True, exist_ok=True)
    (archive_dir / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _content_hash(data: dict) -> str:
    payload = json.dumps(
        {k: v for k, v in data.items() if k != "_metadata"},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def enrich_metadata(data: dict, build_id: str | None = None) -> dict:
    """Add provenance (build_id, capture time, manifests) to a data dict."""
    meta = data.setdefault("_metadata", {})
    meta.setdefault("build_id", build_id or get_build_id())
    meta.setdefault("captured_at", datetime.now(timezone.utc).isoformat())
    meta.setdefault("manifests", _current_manifests())
    return data


def _enrich(data: dict, build_id: str) -> dict:
    return enrich_metadata(copy.deepcopy(data), build_id)


def archive_data(output_path, data: dict, kind: str, archive_dir=None) -> Path:
    if kind not in FILENAMES:
        raise ValueError(f"Unknown snapshot kind: {kind!r} (expected {sorted(FILENAMES)})")

    out_dir = resolve_archive_dir(output_path, archive_dir)
    build_id = get_build_id()
    data_hash = _content_hash(data)

    index = _load_index(out_dir)
    entry = index["builds"].get(build_id)

    if entry and entry.get(f"{kind}_hash") == data_hash:
        print(f"Archive: {build_id} {kind} unchanged, skipping")
        _update_entry(entry, data, build_id, kind, data_hash)
        _save_index(out_dir, index)
        return out_dir / build_id / FILENAMES[kind]

    enriched = _enrich(data, build_id)
    snapshot_path = out_dir / build_id / FILENAMES[kind]
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(
        json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Archive: wrote {snapshot_path}")

    entry = index["builds"].setdefault(build_id, {"build_id": build_id})
    _update_entry(entry, enriched, build_id, kind, data_hash)
    _save_index(out_dir, index)

    return snapshot_path


def _update_entry(entry, data: dict, build_id: str, kind: str, data_hash: str) -> None:
    meta = data.get("_metadata", {})
    entry.setdefault("captured_at", meta.get("captured_at"))
    if "manifests" in meta:
        entry["manifests"] = meta["manifests"]
    entry[f"{kind}_count"] = meta.get("count")
    entry[f"{kind}_hash"] = data_hash
