"""Tiny JSON cache: one file per source, each stamped with fetched_at (UTC ISO)."""
import json
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def save(source: str, payload) -> dict:
    doc = {"fetched_at": datetime.now(timezone.utc).isoformat(), "data": payload}
    (DATA_DIR / f"{source}.json").write_text(json.dumps(doc), encoding="utf-8")
    return doc


def load(source: str):
    p = DATA_DIR / f"{source}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))
