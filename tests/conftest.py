"""Shared test helpers. Every test runs offline: no internet, no API keys, no Ollama.

Step 2 adds:
  engine_db  points Emolé's engine at the small fixture database
  real_db    the REAL table, rebuilt from the committed snapshot (data/processed), used only
             to prove the prompt's worked examples run; no test depends on its values
  stand_in   a pretend model: it returns SQL and sentences written by the test, so every
             step of the engine can be tested without a real model
"""
from pathlib import Path

import pytest

from emole import config
from emole.data.build import run

FIXTURES = Path(__file__).parent / "fixtures"
RAW = FIXTURES / "raw"
SOURCES = FIXTURES / "sources_test.yaml"


@pytest.fixture(scope="session")
def built(tmp_path_factory):
    """Run the whole build once on the fixtures (offline) into a temp folder."""
    out = tmp_path_factory.mktemp("build")
    result = run(offline=True, sources_file=SOURCES, raw_dir=RAW, ref_dir=config.REFERENCE_DIR,
                 out_dir=out / "processed", db_path=out / "emole.duckdb",
                 year_min=1970, year_max=2026)
    result["out"] = out
    return result


@pytest.fixture(scope="session")
def real_db_path(tmp_path_factory):
    out = tmp_path_factory.mktemp("real")
    run(from_snapshot=True, out_dir=config.PROCESSED_DIR, db_path=out / "emole.duckdb")
    return out / "emole.duckdb"


def _use_db(monkeypatch, path):
    from emole.pipeline import catalog, llm
    monkeypatch.setattr(config, "DB_PATH", path)
    monkeypatch.setattr(config, "LOG_QUERIES", False)
    catalog._cache.update(mtime=None, facts=None)
    llm.reset_cooldowns()


@pytest.fixture
def engine_db(built, monkeypatch):
    path = built["out"] / "emole.duckdb"
    _use_db(monkeypatch, path)
    yield path
    from emole.pipeline import catalog
    catalog._cache.update(mtime=None, facts=None)


@pytest.fixture
def real_db(real_db_path, monkeypatch):
    _use_db(monkeypatch, real_db_path)
    yield real_db_path
    from emole.pipeline import catalog
    catalog._cache.update(mtime=None, facts=None)


class StandIn:
    """A pretend model. Fill .sql (question -> SQL), .repairs (list of SQL for repair calls),
    .followups (message -> rewritten question) and .answers (list of sentences)."""

    def __init__(self):
        self.sql, self.repairs, self.followups, self.answers = {}, [], {}, []
        self.calls = []                                  # (kind, temperature)

    def __call__(self, link, messages, temperature, max_tokens, stop):
        last = messages[-1]["content"]
        usage = {"prompt_tokens": sum(len(m["content"]) for m in messages) // 4, "reply_tokens": 10}
        if last.startswith("QUESTION: "):
            self.calls.append(("sql", temperature))
            return self.sql[last.split("\n")[0][len("QUESTION: "):]], usage
        if last.startswith("That SQL has a problem"):
            self.calls.append(("repair", temperature))
            return self.repairs.pop(0), usage
        if last.startswith("EARLIER QUESTIONS"):
            self.calls.append(("followup", temperature))
            msg = last.split("LATEST MESSAGE:\n")[1]
            return self.followups.get(msg, msg), usage
        self.calls.append(("answer", temperature))
        return (self.answers.pop(0) if self.answers else "Here are the figures from the data."), usage


@pytest.fixture
def stand_in(monkeypatch):
    from emole.pipeline import llm
    s = StandIn()
    monkeypatch.setitem(config.PROVIDERS, "standin", {"kind": "standin"})
    monkeypatch.setitem(llm.SENDERS, "standin", s)
    monkeypatch.setattr(config, "PROVIDER_CHAIN", ["standin:scripted"])
    return s
