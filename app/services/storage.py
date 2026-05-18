# app/services/storage.py
import json
import os
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Optional

from app.models.snapshot import MarketSnapshot

logger = logging.getLogger(__name__)

SNAPSHOTS_DIR = Path("data/snapshots")
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def _atomic_write(path: Path, content: str) -> None:
    """
    Write content to path atomically via temp-file + rename.
    Prevents MCP server from reading a half-written file during concurrent refreshes.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.stem}_", suffix=".tmp")
    try:
        tmp_path = Path(tmp)
        tmp_path.write_text(content, encoding="utf-8")
        os.close(fd)
        tmp_path.replace(path)          # atomic on POSIX; best-effort on Windows
    except Exception:
        Path(tmp).unlink(missing_ok=True)
        raise


def save_snapshot(snap: MarketSnapshot) -> None:
    """
    Persist snapshot to two locations:
      - {ticker}_latest.json  → always overwritten; primary MCP read target
      - {snapshot_id}.json    → immutable archive entry
    Uses model_dump_json() (Pydantic v2 native) — no default=str hack needed.
    """
    payload = snap.model_dump_json(indent=2)

    latest_path = SNAPSHOTS_DIR / f"{snap.ticker}_latest.json"
    archive_path = SNAPSHOTS_DIR / f"{snap.snapshot_id}.json"

    _atomic_write(latest_path, payload)

    # Archive is write-once — skip if already exists (re-signal on same snapshot)
    if not archive_path.exists():
        _atomic_write(archive_path, payload)

    logger.info(f"Saved snapshot {snap.snapshot_id} ({len(snap.news)} news items)")


def load_latest_snapshot(ticker: str) -> Optional[MarketSnapshot]:
    path = SNAPSHOTS_DIR / f"{ticker}_latest.json"
    if not path.exists():
        logger.warning(f"No latest snapshot for {ticker}")
        return None
    try:
        return MarketSnapshot.model_validate_json(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"Corrupt snapshot for {ticker}: {e}")
        return None


def load_history(ticker: str, limit: int = 20) -> list[dict]:
    files = sorted(
        SNAPSHOTS_DIR.glob(f"{ticker}_2*.json"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )[:limit]

    history = []
    for f in files:
        try:
            history.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception as e:
            logger.warning(f"Skipping corrupt archive file {f.name}: {e}")

    return history
