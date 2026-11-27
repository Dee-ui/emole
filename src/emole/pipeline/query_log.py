"""query_log.py: a simple diary of questions, to improve Emolé later.

Saved: the question, the SQL, the answer type, which checks fired, timing, which
provider answered and how many tokens it used, and any /good or /bad feedback.
NEVER saved: result rows, API keys, or anything from .env.
"""
import json
from datetime import datetime

from emole import config

LOG_FILE = config.LOGS_DIR / "queries.jsonl"


def write(entry: dict) -> None:
    if not config.LOG_QUERIES:
        return
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    entry = {"ts": datetime.now().isoformat(timespec="seconds"), **entry}
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")


def read_all() -> list:
    if not LOG_FILE.exists():
        return []
    return [json.loads(line) for line in LOG_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
