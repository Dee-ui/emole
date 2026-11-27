"""The secrets check blocks key-shaped strings and lets normal text through.

The fake keys are GLUED TOGETHER at run time ("gsk" + "_" + ...), so this test file
itself never contains a key-shaped string and does not trip the commit hook."""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import check_no_secrets as cns  # noqa: E402

FAKES = {
    "Groq API key": "gsk" + "_" + "A1b2C3d4" * 7,
    "Google API key": "AI" + "za" + "SyA1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q",
    "Hugging Face token": "hf" + "_" + "AbCdEfGhIj" * 4,
    "GitHub token": "gh" + "p_" + "A1b2C3d4E5" * 4,
    "AWS access key": "AK" + "IA" + "ABCDEFGHIJKLMNOP",
}


# ids= keeps the fake keys out of test names (pytest saves names in .pytest_cache)
@pytest.mark.parametrize("kind,fake", list(FAKES.items()), ids=list(FAKES))
def test_fake_keys_are_blocked(tmp_path, kind, fake):
    f = tmp_path / "leak.py"
    f.write_text(f'KEY = "{fake}"\n', encoding="utf-8")
    hits = cns.scan_file(f)
    assert hits and hits[0][2] in (kind, "Secret assigned in code")
    assert cns.main([str(f)]) == 1


def test_secret_assignment_is_blocked(tmp_path):
    f = tmp_path / "settings.py"
    f.write_text('api_key = "' + "x9" * 12 + '"\n', encoding="utf-8")
    assert cns.main([str(f)]) == 1


def test_normal_text_and_empty_env_template_pass(tmp_path):
    f = tmp_path / "ok.md"
    f.write_text("GROQ_API_KEY=\nThe gsk_ prefix marks Groq keys.\napi_key = os.environ['X']\n",
                 encoding="utf-8")
    assert cns.main([str(f)]) == 0


def test_allow_marker_skips_a_line(tmp_path):
    f = tmp_path / "doc.py"
    f.write_text(f'EXAMPLE = "{FAKES["Groq API key"]}"  # secrets-check: allow\n', encoding="utf-8")
    assert cns.main([str(f)]) == 0


IGNORED = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".ruff_cache", "raw", ".env"}


def test_the_repository_itself_is_clean():
    """Every file that Git would track (ignored caches and downloads are skipped)."""
    files = [p for p in ROOT.rglob("*") if p.is_file() and not IGNORED & set(p.parts)]
    hits = [h for p in files for h in cns.scan_file(p)]
    assert hits == [], hits


def test_script_runs_from_the_command_line(tmp_path):
    f = tmp_path / "leak.txt"
    f.write_text(FAKES["Groq API key"], encoding="utf-8")
    res = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_no_secrets.py"), str(f)],
                         capture_output=True, text=True)
    assert res.returncode == 1 and "BLOCKED" in res.stdout
    assert FAKES["Groq API key"] not in res.stdout          # never echoes the secret
