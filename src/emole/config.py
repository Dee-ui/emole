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
#   2: the database also holds the group-maths macros pop_avg() and gdp_avg() (Step 2)
BUILD_VERSION = 2

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


# ===========================================================================
# STEP 2: THE ENGINE
# ===========================================================================
# Keys and personal settings live in .env (git-ignored). This reads it once, here,
# so every part of Emolé sees the same values. A key is NEVER printed or logged:
# code only ever says whether a key is present.
def _load_env_file() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:                           # the data build does not need it
        return
    load_dotenv(PROJECT_ROOT / ".env", override=False)


_load_env_file()

# ---------------------------------------------------------------------------
# MODE (Context 6.2): local = your laptop, team = inside an organisation,
# public = the free demo on the internet. Set EMOLE_MODE in .env.
# ---------------------------------------------------------------------------
MODES = ("local", "team", "public")
EMOLE_MODE = os.environ.get("EMOLE_MODE", "local").strip().lower() or "local"

# ---------------------------------------------------------------------------
# MODEL PROVIDERS
# ---------------------------------------------------------------------------
# One entry per provider. "openai" kind = called through the OpenAI-compatible format,
# so a provider is just a web address, a key and a model name.
#   temperature: False for Gemini. Google's Gemini 3 guidance is to leave temperature at
#   its default, and from Gemini 3.5 Flash-Lite on the API ignores it (decision E-63).
PROVIDERS = {
    "ollama": {"kind": "ollama", "host": os.environ.get("OLLAMA_HOST") or "http://127.0.0.1:11434"},
    "groq": {"kind": "openai", "base_url": "https://api.groq.com/openai/v1",
             "key_env": "GROQ_API_KEY", "temperature": True},
    "gemini": {"kind": "openai", "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
               "key_env": "GEMINI_API_KEY", "temperature": False},
    "openrouter": {"kind": "openai", "base_url": "https://openrouter.ai/api/v1",
                   "key_env": "OPENROUTER_API_KEY", "temperature": True},
}

OLLAMA_MODEL = "qwen2.5:7b-instruct"

# The chain: tried in order; a provider that is busy, out of quota, too slow or broken
# is skipped for a while and the next one answers. Format "provider:model".
# Override it in .env, for example:
#   EMOLE_PROVIDER_CHAIN=groq:openai/gpt-oss-120b,gemini:gemini-3.5-flash-lite
# Step 3's evaluation decides the final order (accuracy first, then speed; E-12).
DEFAULT_CHAINS = {
    "local": [f"ollama:{OLLAMA_MODEL}"],
    "team": [f"ollama:{OLLAMA_MODEL}"],
    "public": ["groq:openai/gpt-oss-120b",
               "gemini:gemini-3.5-flash-lite",
               "gemini:gemini-3.1-flash-lite"],
}
PROVIDER_CHAIN = [p.strip() for p in os.environ.get("EMOLE_PROVIDER_CHAIN", "").split(",") if p.strip()]

LLM_TIMEOUT_SEC = 180         # Ollama on a laptop CPU can be slow on the first call
HOSTED_TIMEOUT_SEC = 30       # a hosted provider slower than this is skipped for the next one
MAX_SQL_TOKENS = 400          # cap on SQL length (a model can never ramble forever)
MAX_ANSWER_TOKENS = 150       # cap on the answer sentence
# Hosted "thinking" models (Gemini 3.x) spend part of the output budget thinking before
# they answer, and that thinking cannot be switched off. Their caps are raised to this,
# so the SQL is never cut off half-way. The answer is still checked as usual.
HOSTED_MIN_TOKENS = 2048
RATE_LIMIT_COOLDOWN_SEC = 60  # skip a provider this long after "too many requests" or a timeout
ERROR_COOLDOWN_SEC = 600      # ... and this long after a broken key or a wrong model name
SQL_REPAIR_ATTEMPTS = 1       # if the SQL fails a check or errors, the model may fix it once

# ---------------------------------------------------------------------------
# SPEED (kept from the earlier build; they apply to Ollama)
# ---------------------------------------------------------------------------
# Every Ollama call asks for the SAME context size. Too small and Ollama silently cuts
# the middle out of a long prompt; a different size on each call makes it reload the
# model. Emolé's SQL prompt is measured in the guide (decision E-13: measured, not cut).
LLM_NUM_CTX = 12288
LLM_KEEP_ALIVE = "60m"        # keep the model loaded between questions
LLM_NUM_THREAD = 0            # 0 = Ollama decides
LLM_WARM_UP = True            # load the model and read the SQL prompt once at start
QUICK_ANSWERS = True          # one-number answers get a fixed sentence, no model call
ANSWER_CACHE_SIZE = 200       # used by the website (Step 4)
SPEED_LOG = True              # print a "[speed]" line after every question

# ---------------------------------------------------------------------------
# ANSWERS, LOGS AND CHARTS
# ---------------------------------------------------------------------------
MAX_ROWS = 5000               # never pull more rows than this into memory
RANKING_LIMIT = 10            # "top countries" without a number means the top 10
MAX_HISTORY_TURNS = 3         # earlier questions remembered for follow-ups
SHOW_SQL = True               # show the SQL in the terminal chat
LOG_QUERIES = True            # save question, SQL, timing and provider (never result rows)
CHART_DIR = PROJECT_ROOT / "charts"          # git-ignored
LABEL_UNIT_MODE = "per_value"                # chart labels: 950, 54.3k, 1.2M ...
LABEL_DECIMALS = 1
