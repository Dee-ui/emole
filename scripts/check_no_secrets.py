"""check_no_secrets.py: stop a commit that contains something shaped like a secret.

It runs automatically before every commit (see .pre-commit-config.yaml), and you can
run it by hand on any files:
    python scripts/check_no_secrets.py README.md src/emole/config.py
    python scripts/check_no_secrets.py --all        (every file Git tracks)

Why: API keys belong ONLY in .env (git-ignored) and in Render's secret settings
(decision D-59 in the IEEE-CIS project, E-49 here). Remembering is not enough;
a check that blocks the commit is.

What it looks for (shapes, not real values):
  Groq keys            gsk_ followed by 40+ letters/digits
  Google API keys      AIza followed by 35 characters
  OpenRouter keys      sk-or-v1- followed by 64 hex characters
  OpenAI-style keys    sk- followed by 32+ characters
  Hugging Face tokens  hf_ followed by 30+ letters
  GitHub tokens        ghp_ / gho_ / github_pat_ ...
  AWS access keys      AKIA followed by 16 capitals/digits
  Private key blocks   -----BEGIN ... PRIVATE KEY-----
  Assignments          api_key = "...", secret: '...', token="..." with a long value

A line that must contain such a shape on purpose (rare) can end with the marker
    secrets-check: allow
and is then skipped. Use it sparingly and never for a real key.
"""
import re
import subprocess
import sys
from pathlib import Path

PATTERNS = [
    ("Groq API key", re.compile(r"\bgsk_[A-Za-z0-9]{40,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}")),
    ("OpenRouter API key", re.compile(r"\bsk-or-v1-[0-9a-f]{64}")),
    ("OpenAI-style secret key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_\-]{32,}")),
    ("Hugging Face token", re.compile(r"\bhf_[A-Za-z0-9]{30,}")),
    ("GitHub token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}"
                                r"|\bgithub_pat_[A-Za-z0-9_]{50,}")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Private key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("Secret assigned in code", re.compile(
        r"(?i)\b(?:api[_-]?key|secret(?:[_-]?key)?|access[_-]?token|auth[_-]?token|password|passwd)"
        r"\b\s*[:=]\s*['\"][^'\"\s]{16,}['\"]")),
]
ALLOW = "secrets-check: allow"
SKIP_SUFFIXES = {".parquet", ".duckdb", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".zip",
                 ".wav", ".mp3", ".mp4", ".onnx", ".bin", ".pdf", ".xlsx", ".pyc"}
MAX_BYTES = 2_000_000


def scan_text(text: str):
    """Yield (line number, kind) for every secret-shaped thing in the text."""
    for n, line in enumerate(text.splitlines(), 1):
        if ALLOW in line:
            continue
        for kind, rx in PATTERNS:
            if rx.search(line):
                yield n, kind
                break


def scan_file(path: Path):
    path = Path(path)
    if path.suffix.lower() in SKIP_SUFFIXES or not path.is_file():
        return []
    if path.stat().st_size > MAX_BYTES:
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    return [(path, n, kind) for n, kind in scan_text(text)]


def tracked_files() -> list:
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True)
    return [Path(p) for p in out.stdout.splitlines() if p]


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    files = tracked_files() if args == ["--all"] else [Path(a) for a in args]
    hits = [h for f in files for h in scan_file(f)]
    for path, n, kind in hits:
        # Never print the matching text itself: the point is to keep it out of logs too.
        print(f"BLOCKED: {path}:{n} looks like a {kind}.")
    if hits:
        print("\nMove secrets to .env (it is git-ignored) and read them with os.environ.")
        print("If this is a false alarm, end that line with:  # " + ALLOW)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
