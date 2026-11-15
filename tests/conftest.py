"""Shared test helpers. Every test runs offline on the small fixtures."""
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
