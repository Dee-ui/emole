"""sources.py: read and check data/sources.yaml and data/reference/blocs.yaml.

Checking the lists before any download means a typo (a missing unit, an unknown
aggregation rule, a bloc list with 11 codes where 12 were promised) stops the build
at once with a clear message, instead of producing a quietly wrong table.
"""
import re
from pathlib import Path

import yaml

from emole import config

AGGREGATIONS = {"sum", "pop_weighted", "gdp_weighted", "median"}
LETTERS = {"M", "O", "L", "E"}
REQUIRED = ("column", "letter", "description", "unit", "aggregation", "weight_note",
            "source", "producer", "licence")
NAME_OK = re.compile(r"^[a-z][a-z0-9_]*$")
ISO3 = re.compile(r"^[A-Z]{3}$")


class SourceListError(ValueError):
    """Raised when sources.yaml or blocs.yaml is not valid."""


def load_sources(path: Path = None) -> list:
    """Return the list of column entries from sources.yaml, checked."""
    path = Path(path or config.SOURCES_FILE)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    cols = data.get("columns") or []
    if not cols:
        raise SourceListError(f"{path} has no columns.")
    seen = set()
    for c in cols:
        name = c.get("column", "?")
        missing = [k for k in REQUIRED if not c.get(k)]
        if missing:
            raise SourceListError(f"{name}: missing {', '.join(missing)} in {path.name}")
        if not NAME_OK.match(name):
            raise SourceListError(f"{name}: column names must be lower_case_with_underscores")
        if name in seen:
            raise SourceListError(f"{name}: listed twice")
        seen.add(name)
        if c["letter"] not in LETTERS:
            raise SourceListError(f"{name}: letter must be one of M, O, L, E")
        if c["aggregation"] not in AGGREGATIONS:
            raise SourceListError(f"{name}: aggregation must be one of {sorted(AGGREGATIONS)}")
        if c["source"] == "owid" and not c.get("slug"):
            raise SourceListError(f"{name}: an OWID column needs a slug")
        if c["source"] == "worldbank" and not c.get("code"):
            raise SourceListError(f"{name}: a World Bank column needs a code")
        if c["source"] not in ("owid", "worldbank"):
            raise SourceListError(f"{name}: source must be owid or worldbank")
    names = {c["column"] for c in cols}
    if "population" not in names:
        raise SourceListError("population is required: it is the weight for group averages")
    if any(c["aggregation"] == "gdp_weighted" for c in cols) and "gdp_per_capita_ppp" not in names:
        raise SourceListError("gdp_weighted needs the gdp_per_capita_ppp column")
    return cols


def source_url(c: dict) -> str:
    """The page a person can open to see this source."""
    if c["source"] == "owid":
        return config.OWID_PAGE_URL.format(slug=c["slug"])
    return config.WB_PAGE_URL.format(code=c["code"])


def source_id(c: dict) -> str:
    return c.get("slug") or c.get("code")


def load_blocs(path: Path = None) -> dict:
    """Return the bloc lists from blocs.yaml, checked (counts, codes, duplicates)."""
    path = Path(path or config.REFERENCE_DIR / "blocs.yaml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    for key, b in data.items():
        members = b.get("members") or []
        bad = [m for m in members if not ISO3.match(str(m))]
        if bad:
            raise SourceListError(f"{key}: not ISO 3-letter codes: {bad}")
        if len(set(members)) != len(members):
            raise SourceListError(f"{key}: a code is listed twice")
        if b.get("count") != len(members):
            raise SourceListError(f"{key}: says {b.get('count')} members but lists {len(members)}")
        if not str(b.get("column", "")).startswith("is_"):
            raise SourceListError(f"{key}: column must start with is_")
        if not b.get("as_of"):
            raise SourceListError(f"{key}: needs an as_of date")
    return data
