import json
import os
from datetime import datetime, timezone
from pathlib import Path
from controls import for_storage

def _log_path() -> Path:
    base = Path(os.environ.get("PIILAB_DATA_DIR", "var"))
    base.mkdir(parents=True, exist_ok=True)
    return base / "audit.jsonl"

def write(session_id: str, kind: str, text: str) -> None:
    event = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "session": session_id,
        "kind": kind,
        "text": for_storage(text),
    }
    with _log_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")
