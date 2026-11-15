"""config.py: one place for paths and settings. Every other file reads from here.

Paths are worked out from where this file sits, so the project runs the same way
from any folder name (your folder is "Project Emole", the repo is "emole"), inside
Docker later, and on a CI machine. Set the EMOLE_ROOT environment variable only if
you ever need to point the code at a different copy of the project.
"""

import datetime as dt
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# PROJECT FOLDERS
# ---------------------------------------------------------------------------
# src/emole/config.py -> parents[0] = src/emole, [1] = src, [2] = project root
PROJECT_ROOT = Path(os.environ.get("EMOLE_ROOT", Path(__file__).resolve().parents[2]))

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"                    # downloaded files (git-ignored)
PROCESSED_DIR = DATA_DIR / "processed"        # the committed snapshot
REFERENCE_DIR = DATA_DIR / "reference"        # region and bloc lists (committed)
SOURCES_FILE = DATA_DIR / "sources.yaml"      # the list of all 17 columns and where they come from
DOCS_DIR = PROJECT_ROOT / "docs"
LOGS_DIR = PROJECT_ROOT / "logs"              # git-ignored

DB_PATH = DATA_DIR / "emole.duckdb"           # the database Emolé reads (git-ignored, rebuilt)

# The committed snapshot (decision E-45): rebuilding the database from these files
# needs no internet, so Docker builds and test gold answers stay reproducible.
SNAPSHOT_TABLE = PROCESSED_DIR / "country_year.parquet"
SNAPSHOT_META = PROCESSED_DIR / "column_meta.csv"
SNAPSHOT_INFO = PROCESSED_DIR / "build_info.json"
REMOVED_ROWS = PROCESSED_DIR / "removed_rows.csv"
COVERAGE_REPORT = DOCS_DIR / "coverage_report.md"

# ---------------------------------------------------------------------------
# BUILD SETTINGS
# ---------------------------------------------------------------------------
# Bump this whenever the cleaning or joining code changes, so everyone can tell
# which rules built a given snapshot. It is saved inside the database and snapshot.
#   1: first build (Step 1)
BUILD_VERSION = 1

# Years kept in country_year (decision E-43). 1970 is where the aviation series
# start. Nothing after the current year is kept, so projections can never slip in.
YEAR_MIN = 1970
YEAR_MAX = dt.date.today().year

# A polite name for our downloads, so data publishers can see who is asking.
# It names the project, never a person or an email address.
USER_AGENT = "EmoleDataBuild/0.1 (+https://github.com/Dee-ui/emole)"
HTTP_TIMEOUT_SEC = 60
HTTP_RETRIES = 3

# Where the data comes from (decision E-03 and E-37).
OWID_CSV_URL = "https://ourworldindata.org/grapher/{slug}.csv?csvType=full&useColumnShortNames=true"
OWID_PAGE_URL = "https://ourworldindata.org/grapher/{slug}"
WB_INDICATOR_URL = ("https://api.worldbank.org/v2/country/all/indicator/{code}"
                    "?format=json&per_page=20000&date={start}:{end}&page={page}")
WB_COUNTRIES_URL = "https://api.worldbank.org/v2/country?format=json&per_page=400&page={page}"
WB_PAGE_URL = "https://data.worldbank.org/indicator/{code}"

# OWID marks its own entities with codes that start with OWID_. Most are groups
# ("World", "Africa") or countries that no longer exist (USSR, Yugoslavia).
# Kosovo is the one real country among them: we keep it, under the World Bank's
# code XKX, so World Bank columns join to the same row (decision E-38).
OWID_CODE_RENAMES = {"OWID_KOS": "XKX"}

# ---------------------------------------------------------------------------
# COVERAGE CHECKS (Step 1 coverage report)
# ---------------------------------------------------------------------------
# Nigeria first, then the African peers, then global comparisons (Context 4.2).
PEER_COUNTRIES = {
    "NGA": "Nigeria", "GHA": "Ghana", "KEN": "Kenya", "ZAF": "South Africa",
    "EGY": "Egypt", "ETH": "Ethiopia", "CIV": "Cote d'Ivoire", "SEN": "Senegal",
    "MAR": "Morocco",
    "USA": "United States", "GBR": "United Kingdom", "IND": "India", "BRA": "Brazil",
    "IDN": "Indonesia", "CHN": "China", "DEU": "Germany", "ARE": "United Arab Emirates",
}
# A column is FLAGGED (not dropped) for review when one of these is true. The rule
# was written before the first real build, so the result cannot bend it (as in the
# IEEE-CIS project): Nigeria misses it in its latest 5 years, fewer than this share
# of countries have it in its broad-coverage year, or a peer misses more than this
# many of the latest 5 years.
FLAG_MIN_COUNTRY_SHARE = 0.60
FLAG_MAX_PEER_GAPS = 3
RECENT_YEARS = 5

# "Latest year with broad coverage": the newest year in which at least this share
# of the column's usual number of countries (its best year in the last 10) report.
# Example: Ember's 2025 electricity data covers far fewer countries than 2024, so
# for rankings and group answers 2024 is the fairer "latest".
BROAD_COVERAGE_SHARE = 0.80
