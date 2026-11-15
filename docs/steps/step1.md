# Emolé, Step 1 of 6: foundations and data

**Date:** 8 November 2026. **Branch:** `step-01-foundations-data`. **Tag after merge:** `v0.1.0-step1`.

Sir, this guide takes you from an empty folder to a GitHub repo with a working data
pipeline. Read Part 0 and Part 1 first; Part 3 is the hands-on walkthrough.

---

## Part 0. This step in one minute

**What you get**

- A clean, installable project (`src/emole/`) with pinned requirements, an MIT licence (to confirm), Git rules, an env template and a light CI.
- `data/sources.yaml`: all 17 columns, each checked by hand on 8 November 2026 (exact chart or code, unit, producer, licence, years).
- `python scripts/build_data.py`: one command downloads the sources politely, removes every group row ("World", "Africa", World Bank aggregates), joins everything into `country_year`, adds continent, subregion, World Bank region, income group and five bloc columns, and writes the database plus a committed snapshot.
- `python scripts/coverage_report.py`: writes `docs/coverage_report.md` (per column, per peer country, per region and bloc) and flags columns to review using a rule written before any real data was seen.
- `src/emole/groupmath.py`: the group maths (sum, population-weighted, GDP-weighted, median) with coverage notes, in Python AND as SQL, proven to agree. Step 2 uses it.
- `docs/DATA.md` (data dictionary), `docs/PROJECT_STATE.md` (rewritten in full), `docs/POST_LOG.md` (13 entries), this guide.
- A secrets check that blocks API-key-shaped strings before any commit.

**What I tested (Linux, Python 3.11, the same library versions you will install)**

- 51 offline tests pass; `ruff` is clean.
- The whole build ran end to end on small test files shaped exactly like the real OWID and World Bank downloads.
- In a real Git repository, a clean commit passed and a commit holding a fake Groq-shaped key was **blocked**.

**What I could NOT test, said plainly**

- **The real downloads.** My workspace cannot reach ourworldindata.org or api.worldbank.org (every request was refused by its network proxy). So the first real build, its summary and the real coverage report happen on your laptop (Part 3, steps 6 and 7), and I need the output back (Part 5).

---

## Part 1. Your two questions, answered

### 1.1 Folder and repo
- **Folder:** `C:\Users\Dauda Agbonoga\Documents\Projects\Project Emole` (your choice). It is outside OneDrive, which matters: OneDrive sync can corrupt `.git` and DuckDB files. The space in the name is fine.
- **Repo:** `Dee-ui/emole`, public (you said it is good to go).
- **Folder name vs repo name:** they do not need to match. The code finds its files from its own location, so it runs the same in "Project Emole", in a clone called "emole", in Docker and in CI (decision E-30).

### 1.2 Code layout: `src/emole/` (a proper package). Recommended and used.
- **What it means:** the code lives in `src/emole/`, and `pip install -r requirements.txt` installs it (the last line, `-e .`, does this). After that, every script, test and (later) the website says `from emole import config`.
- **Why it beats your earlier build's flat `src/`:** those scripts had to edit `sys.path` at the top of every file to find each other. That breaks easily (run from another folder, inside Docker, in CI). An installed package always imports the same way, and the tests check the code you actually ship (decision E-31).
- **The cost:** one extra small file (`pyproject.toml`). That is all.

### 1.3 Licence
MIT for the code (simple, permissive, normal for portfolios and client work). The data keeps its own licences, listed in `docs/DATA.md`. **Please confirm MIT** (Part 5).

---

## Part 2. What was decided, and why

### 2.1 The sources (checked by hand before any download code was written, rule D-72)

| Letter | Column | Comes from | Why |
|---|---|---|---|
| M | air_passengers | OWID `air-passengers-carried` | |
| M | air_departures | **World Bank** IS.AIR.DPRT | OWID has no chart for it |
| M | air_freight_mtkm | OWID `air-transport-freight-ton-km` | planning expected the World Bank; OWID has it |
| M | internet_users_pct | OWID `share-of-individuals-using-the-internet` | |
| M | mobile_subs_per_100 | OWID `mobile-cellular-subscriptions-per-100-people` | |
| O | gdp_per_capita_ppp | OWID `gdp-per-capita-worldbank` | |
| O | gdp_growth_pct | **World Bank** NY.GDP.MKTP.KD.ZG | OWID's chart is the UN SDG series, 2000 to 2023 only |
| O | inflation_cpi_pct | OWID `inflation-of-consumer-prices` | |
| O | unemployment_pct | OWID `unemployment-rate` | |
| L | life_expectancy_years | OWID `life-expectancy` | |
| L | under5_deaths_per_1000 | **World Bank** SH.DYN.MORT | OWID gives a %, and lists the source under a UNICEF copyright notice; the World Bank gives per 1,000 under CC BY 4.0 |
| L | health_spend_per_capita_ppp | OWID `annual-healthcare-expenditure-per-capita` | |
| L | population | **World Bank** SP.POP.TOTL | OWID switches to UN projections after 2023 (explained below) |
| L | urban_pop_pct | OWID `share-of-population-urban` | |
| E | electricity_access_pct | OWID `share-of-the-population-with-access-to-electricity` | |
| E | renewables_share_elec_pct | OWID `share-electricity-renewables` | share of **electricity** (decision E-36) |
| E | co2_per_capita_t | OWID `co-emissions-per-capita` | |

Every licence is open: CC BY 4.0 for all World Bank series and OWID's processing, CC BY 3.0 IGO for UN population estimates inside life expectancy, CC BY 4.0 for Ember, and "free with attribution" for the Energy Institute.

**Why population moved to the World Bank (please agree, Part 5).** Population is the weight for every group average. Example: "the average internet share in ECOWAS in 2025" needs each country's 2025 population. OWID's population after 2023 is a UN *projection* (a forecast), while the World Bank's is an *estimate* up to 2025. Weighting real 2025 internet figures with forecast populations would mix data with guesses. Decision E-03 says "World Bank only where OWID lacks the column", so these four fallbacks need your nod.

**Two choices the plan asked me to make:**
- **GDP per person:** PPP in constant 2021 international dollars. "PPP" adjusts for living costs (a dollar buys more in Lagos than in London), and "constant" removes inflation, so both countries and years compare fairly. A naira devaluation will not look like an economic collapse (E-35).
- **Renewables:** share of electricity, not of all energy. Ember reports electricity for over 200 countries up to 2025 (Nigeria included), and "renewable power" is what most people mean (E-36).

### 2.2 Removing group rows: one rule was not enough (PL-002)
OWID writes "World" as `OWID_WRL` and continents with a blank code, so "keep only 3-letter codes" removes them. But the World Bank's groups use 3-letter codes too: `WLD` (World), `SSF` (Sub-Saharan Africa), `EUU` (European Union). The same rule would have let them all in, and "World" would top every ranking. So World Bank rows are checked against the World Bank's own list, which marks groups as "Aggregates". Every removed row is listed in `data/processed/removed_rows.csv`. Kosovo is the one `OWID_` code that is a real country: it is kept as `XKX`.

### 2.3 Regions and blocs
- **continent, subregion:** UN M49 (Nigeria: Africa, Western Africa). Taiwan and Kosovo are not in M49, so they were added by hand with a written reason.
- **wb_region, income_group:** the World Bank's CURRENT list (FY2027, effective 1 July 2026), applied to every year. Emolé will say "current income group".
- **Blocs:** ECOWAS has **12** members now (Burkina Faso, Mali and Niger left, effective 29 January 2025); AU 55; EU 27; G20's 19 countries. Current membership applies to every year in version 1 (so "ECOWAS in 2010" uses today's 12); Emolé will say "current members".
- **Middle East:** 16 countries (list and exclusions in `DATA.md` 4.4). Please agree (Part 5).

### 2.4 Group maths (please agree the two exceptions)
- Totals (passengers, departures, freight, population) are **summed**.
- Rates and per-person figures use a **population-weighted average**.
- **Exception 1: GDP growth is weighted by economy size** (GDP = GDP per person x population). Why: Nigeria has about 6.6 times Ghana's population but its economy is not 6.6 times bigger in the same proportion; growth rates should be weighted by how big each economy is. The World Bank does the same.
- **Exception 2: inflation uses the median** (the middle country). Why: one hyperinflation would wreck an average for a whole region. The World Bank uses the median for this indicator too.
- **Coverage note:** every group figure says how many members had data, for example "Based on 11 of 12 ECOWAS countries with data for 2023". A country counts only if it has the value AND its weight.

### 2.5 "Latest" is two numbers (PL-010)
Each column stores `latest_year` (newest year with any data) and `latest_broad_year` (newest year where at least 80% of its usual countries report). Ember's 2025 electricity data has only 91 countries, so a 2025 ranking would compare 91 countries, not the world. Rankings and group answers will use the broad year.

### 2.6 Years, snapshot, flags
- **Years:** 1970 (where aviation starts) to the current year; nothing in the future can slip in.
- **Snapshot:** the built table is committed as `data/processed/country_year.parquet` (+ metadata). `--from-snapshot` rebuilds the database offline in seconds, so Docker and the test answers never depend on a website being up.
- **Flags (rule fixed before seeing data):** a column is flagged if under 60% of countries have it in its broad year, or Nigeria has nothing in its latest 5 years, or a peer misses more than 3 of those years. A flag means "look", not "drop". We agree any drop together.

---

## Part 3. Do it on your laptop, step by step

Open **PowerShell** (or the VS Code terminal). Each step says what to type, what you should see, and why.

### Step 1. Put the files in place
1. Download `emole_step1.zip`.
2. Right-click it, **Extract All**, and choose `C:\Users\Dauda Agbonoga\Documents\Projects`. The zip holds one folder, `Project Emole`, so the files land in `...\Projects\Project Emole\`.
3. Check:
   ```powershell
   cd "C:\Users\Dauda Agbonoga\Documents\Projects\Project Emole"
   dir
   ```
   You should see `data`, `docs`, `scripts`, `src`, `tests`, `README.md`, `requirements.txt` and others. If the two bundle `.md` files from planning are in this folder, move them out (for example to `Documents\Emole planning\`), so they are never committed.

### Step 2. Create the empty repo on GitHub
1. Go to github.com, click **New repository**.
2. Name: `emole`. Visibility: **Public**.
3. **Leave every box unticked** (no README, no .gitignore, no licence). Why: the files already exist locally; a README made on GitHub would clash with yours.
4. Click **Create repository**. Leave the page open.

### Step 3. Create the virtual environment and install
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```
You should see `(.venv)` at the start of the prompt, and the install end with "Successfully installed ... emole-0.1.0 ...". Why: every library is pinned, so your laptop, CI and Docker build the same thing.
If PowerShell refuses to run `Activate.ps1`, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then activate again.

### Step 4. Start Git and switch on the commit checks
```powershell
git init -b main
pre-commit install
```
You should see "pre-commit installed at .git\hooks\pre-commit". From now on, every `git commit` first runs the secrets check and `ruff`. Keep the `.venv` active when you commit.

### Step 5. Run the tests (offline)
```powershell
pytest
```
Expected: `51 passed`. These use only the small files in `tests/fixtures/`, so they need no internet.

### Step 6. Build the real database
```powershell
python scripts/build_data.py
```
What happens: it checks `sources.yaml`, then downloads 18 files (13 OWID charts, 4 World Bank indicators, the World Bank country list) into `data\raw\`, cleans and joins them, and prints a summary like this (your real numbers will appear):
```
==============================================================================
Emole data build  |  BUILD_VERSION 1  |  built 2026-11-..
==============================================================================
country_year: N rows | N countries and territories | years 1970-2026

  letter column                          latest  broad  countries(broad)  aggregation
  M      air_passengers                   ....   ....               ...  sum
  ...
Rows removed (full list in data/processed/removed_rows.csv):
  ...
Grouping gaps (countries with no value for a grouping column):
  ...
```
It should take a minute or two. A second run reuses the saved files and makes no downloads; `--refresh` downloads fresh copies.

**If it stops** with `BUILD STOPPED: ...`, copy that whole line and send it to me. Two likely causes: a download refused (the message names the link; open it in your browser), or an OWID file with more than one value column (the message lists the columns; I will add the right `value_column` line).

**Copy the whole terminal output** from `[1/4]` to the end: I need it (Part 5), and it goes into `PROJECT_STATE.md` section 5.4.

### Step 7. Write and read the coverage report
```powershell
python scripts/coverage_report.py
code docs\coverage_report.md
```
It prints how many columns are flagged. In the report, read section 2 (flags) and section 3 (Nigeria and peers). Do not drop anything yet: send me the report and we agree drops together.

### Step 8. Check one number by eye (two minutes, worth it)
Open https://ourworldindata.org/grapher/share-of-individuals-using-the-internet?country=~NGA and note Nigeria's latest value. Then:
```powershell
python -c "import duckdb; con = duckdb.connect('data/emole.duckdb', read_only=True); print(con.execute('SELECT year, internet_users_pct FROM country_year WHERE iso3 = ? AND internet_users_pct IS NOT NULL ORDER BY year DESC LIMIT 3', ['NGA']).fetchall())"
```
The newest year and value should match the chart. If they do, the download and the cleaning are right end to end.

### Step 9. Save it to GitHub: first commit on main, then the step branch
Why two parts: a pull request needs a `main` branch to merge into. So `main` gets a tiny first commit, and the step's work goes on its own branch.

```powershell
git add README.md LICENSE .gitignore .gitattributes .pre-commit-config.yaml
git commit -m "chore: start the emole repository"
git remote add origin https://github.com/Dee-ui/emole.git
git push -u origin main
```
The hook config (`.pre-commit-config.yaml`) goes in this first commit on purpose: pre-commit refuses to run while its own config file is not committed or staged. You should see the two checks print `Passed` or `(no files to check)Skipped` before the commit. Then:

```powershell
git switch -c step-01-foundations-data
git add pyproject.toml requirements.txt .env.example .github src scripts data/sources.yaml data/reference data/raw/.gitkeep
git commit -m "feat: data pipeline, sources and reference lists"
git add tests
git commit -m "test: offline tests and fixtures"
git add data/processed
git commit -m "feat: first data snapshot (build 1)"
git add docs
git commit -m "docs: data dictionary, coverage report, project state, post log, step 1 guide"
git status
git push -u origin step-01-foundations-data
```
`git status` should say "nothing to commit, working tree clean". Check that `data\raw\` files and `data\emole.duckdb` were NOT added (they are git-ignored on purpose).

Then on GitHub:
1. Click **Compare & pull request**. Title: `Step 1: foundations and data`. Create it.
2. Wait for the **ci** check to turn green (about a minute). If it is red, open it, copy the error and send it to me.
3. Click **Squash and merge**, then **Confirm**.
4. Back in PowerShell, tag the merged result:
```powershell
git switch main
git pull
git tag -a v0.1.0-step1 -m "Step 1: foundations and data"
git push origin v0.1.0-step1
```

### Step 10. Prove the secrets check (and take a screenshot for the post log)
```powershell
python -c "open('leak_test.py', 'w').write('KEY = ' + chr(39) + 'gsk' + '_' + 'Z9y8X7w6V5' * 5 + chr(39) + chr(10))"
git add leak_test.py
git commit -m "test: this must be blocked"
```
Expected: `BLOCKED: leak_test.py:1 looks like a Groq API key.` and NO commit. Take a screenshot (evidence for PL-011). Then clean up:
```powershell
git restore --staged leak_test.py
Remove-Item leak_test.py
```
(The Python line builds the fake key from pieces, so this guide itself never contains a key-shaped string. `chr(39)` is a quote mark and `chr(10)` a new line; they avoid quote problems in PowerShell.)

---

## Part 4. Run order (short version)

1. Extract the zip into `...\Documents\Projects\`
2. Create the empty GitHub repo `emole` (public, nothing ticked)
3. `py -3.11 -m venv .venv` then `.\.venv\Scripts\Activate.ps1` then `pip install -r requirements.txt`
4. `git init -b main` then `pre-commit install`
5. `pytest` (51 passed)
6. `python scripts/build_data.py` (copy the output)
7. `python scripts/coverage_report.py`
8. Check one Nigeria number against OWID
9. Commit on `main`, push; branch, commits, push; PR; CI green; squash-merge; tag `v0.1.0-step1`
10. Secrets test and screenshot

Every later day: `cd` into the folder, `.\.venv\Scripts\Activate.ps1`, work.

---

## Part 5. What I need from you

1. **The full output of `python scripts/build_data.py`** (or the `BUILD STOPPED` line if it stopped).
2. **`docs/coverage_report.md`** and **`data/processed/removed_rows.csv`** (attach them; or attach a zip of the repo).
3. **Your answers:**
   - MIT licence for the code? (Q-01)
   - The 4 World Bank columns (departures, GDP growth, under-five mortality, population), with the reasons in Part 2.1? (Q-02)
   - The 2 group-maths exceptions (GDP growth weighted by economy size; inflation as a median)? (Q-03)
   - The 16-country Middle East list? (Q-04)
   - The peer list (Nigeria, Ghana, Kenya, South Africa, Egypt, Ethiopia, Cote d'Ivoire, Senegal, Morocco, United States, United Kingdom, India, Brazil, Indonesia, China, Germany, UAE)? (Q-05)
4. After you read the report: any flagged column you want dropped (we decide together).
5. Confirmation that the repo is pushed, the PR merged with CI green, and the tag pushed (a screenshot of the green check is enough), plus the secrets-test screenshot.

With these I will update `DATA.md`, `PROJECT_STATE.md` (section 5.4, flags, answers) and the post log (real counts for PL-002, PL-010 and PL-012). Then Step 2 can start: it needs `01_CONTEXT.md`, the Step 2 prompt, and the merged repo (or its zip).

---

## Part 6. Files in this step

Every file is new in this step.

| File | What it is for |
|---|---|
| `README.md` | Placeholder front page: name, one-line description, "work in progress", credits |
| `LICENSE` | MIT for the code (data keeps its own licences) |
| `pyproject.toml` | Makes `src/emole` an installable package; test and ruff settings |
| `requirements.txt` | Pinned versions for Step 1, plus `-e .` |
| `.gitignore` | Keeps `.venv`, `.env`, raw downloads, the database, logs, models and OS files out of Git |
| `.gitattributes` | LF line endings in Git |
| `.env.example` | Template for `.env` (no keys needed in Step 1) |
| `.pre-commit-config.yaml` | Runs the secrets check and ruff before every commit |
| `.github/workflows/ci.yml` | CI: secrets scan, ruff, offline tests |
| `data/sources.yaml` | The 17 columns and where each comes from |
| `data/reference/un_m49.csv` | UN M49 continents and subregions (248 rows, generated) |
| `data/reference/manual_regions.csv` | Taiwan and Kosovo |
| `data/reference/blocs.yaml` | ECOWAS, AU, EU, G20 and Middle East lists |
| `data/raw/.gitkeep`, `data/processed/.gitkeep` | Keep the empty folders in Git |
| `src/emole/__init__.py` | Package marker and version |
| `src/emole/config.py` | Paths and settings |
| `src/emole/groupmath.py` | Group rules in Python and SQL, with coverage notes |
| `src/emole/data/__init__.py` | Sub-package marker |
| `src/emole/data/sources.py` | Reads and checks the source and bloc lists |
| `src/emole/data/fetch.py` | Polite downloads, dated raw files, offline mode |
| `src/emole/data/parse.py` | Cleaning and group-row removal |
| `src/emole/data/groups.py` | Grouping columns |
| `src/emole/data/build.py` | The build (and `--from-snapshot`) |
| `src/emole/data/coverage.py` | The coverage report |
| `scripts/build_data.py` | One command to build |
| `scripts/coverage_report.py` | One command to write the report |
| `scripts/check_no_secrets.py` | The secrets check |
| `scripts/make_m49_reference.py` | Rebuilds `un_m49.csv` (rarely needed) |
| `tests/...` | 51 offline tests and their fixtures |
| `docs/DATA.md`, `docs/PROJECT_STATE.md`, `docs/POST_LOG.md`, `docs/steps/step1.md` | The documents |

---

## Part 7. Full contents of every file

Generated from the exact files in the zip, so they match byte for byte.

The two empty marker files `data/raw/.gitkeep` and `data/processed/.gitkeep` are not shown.

### `README.md`

```markdown
# Emolé

**"I'm Emolé, an expert on Movement, Output, Life and Energy."**

Emolé answers plain-English questions about countries (economy, energy, internet and
phones, aviation and health, over time and across regions) with exact figures,
labelled charts and a spoken reply. She is **deterministic**: the language model only
writes one read-only SQL query, the database computes every number, and code checks
every number in her answer against the database result.

> **Work in progress.** Step 1 of 6 (foundations and data) is being built.
> The live demo, the video and the full write-up come in later steps.

## What is here so far

- A reproducible data pipeline that builds one table, `country_year`, from public data
  (Our World in Data and the World Bank): 17 columns across Movement, Output, Life and
  Energy, plus continent, region, income group and bloc columns.
- One command rebuilds it: `python scripts/build_data.py`
- A coverage report: `python scripts/coverage_report.py` writes `docs/coverage_report.md`
- The data dictionary, sources and licences: [`docs/DATA.md`](docs/DATA.md)

## Data credits

Data from [Our World in Data](https://ourworldindata.org) (CC BY 4.0) and the
[World Bank World Development Indicators](https://data.worldbank.org) (CC BY 4.0),
which republish data from ICAO, ITU, ILO, IMF, WHO, UN IGME, the UN Population
Division, Ember, the Energy Institute and the Global Carbon Project. Regions follow the
UN M49 standard. Full credits per column: [`docs/DATA.md`](docs/DATA.md).

## The name

Emolé is inspired by ìmọ́lẹ̀, the Yoruba word for light: she brings light to the
numbers. Say it "ee-maw-leh".

## Author

Dauda Agbonoga ([GitHub](https://github.com/Dee-ui) ·
[LinkedIn](https://www.linkedin.com/in/dauda-agbonoga/) · X: @iam_the_Dee_ui)

Code: MIT licence. Data: the original licences listed in `docs/DATA.md`.
```

### `LICENSE`

```text
MIT License

Copyright (c) 2026 Dauda Agbonoga

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

This licence covers the code only. The data in data/processed/ and the reference
lists in data/reference/ stay under their original licences; see docs/DATA.md.
```

### `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=69"]
build-backend = "setuptools.build_meta"

[project]
name = "emole"
version = "0.1.0"
description = "Emolé: a deterministic data assistant, an expert on Movement, Output, Life and Energy"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
authors = [{ name = "Dauda Agbonoga" }]
# Exact versions live in requirements.txt (one place to pin them).
dependencies = []

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"

[tool.ruff]
line-length = 110
target-version = "py311"
src = ["src", "scripts", "tests"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "B"]
```

### `requirements.txt`

```text
# Emolé requirements for Step 1: the data pipeline, tests and code checks.
# Exact versions, so every machine (your laptop, CI, Docker later) builds the same thing.
# Heavier libraries (model clients, Whisper, Kokoro, MLflow, FastAPI) are added in the
# steps that need them, never before.

# --- Data pipeline ---
duckdb==1.4.5          # version already proven with the planned read-only settings; 2.0 is a new major release (revisit later)
pandas==2.3.3
numpy==2.4.6
pyarrow==26.0.1        # Parquet files (the committed snapshot)
requests==2.34.2
PyYAML==6.0.3          # reads data/sources.yaml and data/reference/blocs.yaml

# --- Tests and code checks ---
pytest==9.2.0
ruff==0.17.4
pre-commit==4.7.0

# --- This project, installed so "import emole" works everywhere ---
-e .
```

### `.gitignore`

```text
# --- Python ---
.venv/
venv/
__pycache__/
*.py[cod]
*.egg-info/
.pytest_cache/
.ruff_cache/
.ipynb_checkpoints/
build/
dist/

# --- Secrets (NEVER commit) ---
.env
.env.*
!.env.example
secrets/

# --- Data: raw downloads are re-downloadable, so they stay out of Git ---
data/raw/*
!data/raw/.gitkeep
# The database is rebuilt in seconds from the committed snapshot in data/processed/
*.duckdb
*.duckdb.tmp
*.duckdb.wal

# --- Website chats (from Step 4; contain answers) ---
data/app.sqlite
data/app.sqlite-*

# --- Voice (from Step 4): downloaded models, recordings, previews ---
models/
voice/
web/static/vendor/

# --- Generated outputs ---
charts/
mlruns/
mlflow.db
logs/
*.log

# --- Operating system and editor files ---
.DS_Store
Thumbs.db
desktop.ini
.vscode/*
!.vscode/settings.json
.idea/
```

### `.gitattributes`

```text
# Store text files with LF line endings in Git, whatever the computer.
# Without this, Windows (CRLF) and Linux (LF) copies make every line look "changed".
* text=auto eol=lf

# Binary files: never touch them.
*.parquet binary
*.duckdb binary
*.png binary
*.jpg binary
*.wav binary
*.zip binary
```

### `.env.example`

```text
# .env.example: a template. Copy it to .env and fill in YOUR values there.
#   PowerShell:  Copy-Item .env.example .env
# .env is git-ignored, so keys never reach GitHub. Never paste a key into a chat.
#
# Step 1 needs NO keys. The lines below are used from Step 2 onwards.

# local | team | public   (Context 6.2)
EMOLE_MODE=local

# Free hosted models (Step 2). Create keys in the Groq console and Google AI Studio.
GROQ_API_KEY=
GEMINI_API_KEY=
OPENROUTER_API_KEY=

# Signs the website's cookies (Step 4). Make one with:
#   python -c "import secrets; print(secrets.token_hex(32))"
SESSION_SECRET=
```

### `.pre-commit-config.yaml`

```yaml
# Checks that run automatically before every "git commit".
# Install once (with the virtual environment active):   pre-commit install
# Run on every file by hand:                            pre-commit run --all-files
#
# "language: system" means the hooks use the Python and ruff from your active .venv,
# so activate it before committing (.\.venv\Scripts\Activate.ps1).
repos:
  - repo: local
    hooks:
      - id: no-secrets
        name: block token-shaped secrets (API keys, tokens, private keys)
        entry: python scripts/check_no_secrets.py
        language: system
        types: [text]
      - id: ruff
        name: ruff (code checks)
        entry: ruff check
        language: system
        types: [python]
```

### `.github/workflows/ci.yml`

```yaml
# ci.yml: automatic checks on a clean machine, on every push and pull request.
# Step 1 version: secrets scan, code checks and the offline tests.
# Step 3 adds the security suite; Step 5 adds the Docker build and health check.
# No API keys are used here, and none are needed.
name: ci

on:
  push:
  pull_request:

jobs:
  quality:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
      - name: Install
        run: pip install -r requirements.txt
      - name: Secrets scan (every tracked file)
        run: python scripts/check_no_secrets.py --all
      - name: Code checks
        run: ruff check .
      - name: Tests (offline, small fixtures)
        run: pytest
```

### `data/sources.yaml`

```yaml
# sources.yaml: where every column of country_year comes from.
#
# One entry = one column. To add a column later, add one entry and run:
#     python scripts/build_data.py
#
# Fields
#   column        name in the database (units in the name)
#   letter        M (Movement), O (Output), L (Life), E (Energy)
#   description   plain meaning, used in docs and (Step 2) in the model's schema text
#   unit          unit of every value
#   aggregation   how a group (region, bloc) figure is made from its countries:
#                   sum           add the countries up (totals)
#                   pop_weighted  average where each country counts in proportion to its population
#                   gdp_weighted  average where each country counts in proportion to its economy size
#                   median        the middle country's value
#   weight_note   why the rule is exact, or how it is imperfect
#   source        owid (Our World in Data chart) or worldbank (World Bank data service)
#   slug / code   the OWID chart name, or the World Bank indicator code
#   original_id   the World Bank code behind an OWID chart, when there is one
#   producer      who made the data originally (credit them)
#   licence       licence of the original data
#   caveat        aviation = add the "registered airlines, not airports" note in answers
#   why_source    why this source was picked (for World Bank fallbacks and choices)
#   checked       what the source page showed when checked by hand on 8 November 2026
#                 (the build measures the real years from the data every time)
#   value_column  optional: the CSV column to use if a file holds more than one value column

version: 1
checked_on: 2026-11-08

columns:

  # ======================= M: MOVEMENT =======================
  - column: air_passengers
    letter: M
    description: Passengers carried by airlines registered in the country, on domestic and international flights
    unit: passengers
    aggregation: sum
    weight_note: A total, so group figures are a plain sum.
    source: owid
    slug: air-passengers-carried
    original_id: IS.AIR.PSGR
    producer: International Civil Aviation Organization (ICAO), via World Bank
    licence: CC BY 4.0
    caveat: aviation
    checked: {range: "1970-2023", next_update: "January 2027"}

  - column: air_departures
    letter: M
    description: Take-offs by airlines registered in the country, at home and abroad
    unit: departures
    aggregation: sum
    weight_note: A total, so group figures are a plain sum.
    source: worldbank
    code: IS.AIR.DPRT
    producer: International Civil Aviation Organization (ICAO), via World Bank
    licence: CC BY 4.0
    caveat: aviation
    why_source: OWID has no chart for this series, so the World Bank data service is used (decision E-03).
    checked: {range: "1970-2023"}

  - column: air_freight_mtkm
    letter: M
    description: Air freight carried by airlines registered in the country, in million tonne-kilometres (one tonne flown one kilometre)
    unit: million tonne-km
    aggregation: sum
    weight_note: A total, so group figures are a plain sum.
    source: owid
    slug: air-transport-freight-ton-km
    original_id: IS.AIR.GOOD.MT.K1
    producer: International Civil Aviation Organization (ICAO), via World Bank
    licence: CC BY 4.0
    caveat: aviation
    checked: {range: "1970-2023"}

  - column: internet_users_pct
    letter: M
    description: Share of the population who used the internet in the last three months
    unit: "% of population"
    aggregation: pop_weighted
    weight_note: Exact. The share is of the population, so weighting by population gives the true group share.
    source: owid
    slug: share-of-individuals-using-the-internet
    original_id: IT.NET.USER.ZS
    producer: International Telecommunication Union (ITU), via World Bank
    licence: CC BY 4.0
    checked: {range: "1990-2025"}

  - column: mobile_subs_per_100
    letter: M
    description: Mobile phone subscriptions per 100 people (can pass 100 when people hold more than one)
    unit: subscriptions per 100 people
    aggregation: pop_weighted
    weight_note: Exact. The rate is per person, so weighting by population gives the true group rate.
    source: owid
    slug: mobile-cellular-subscriptions-per-100-people
    original_id: IT.CEL.SETS.P2
    producer: International Telecommunication Union (ITU), via World Bank
    licence: CC BY 4.0
    checked: {range: "1960-2025"}

  # ======================= O: OUTPUT =======================
  - column: gdp_per_capita_ppp
    letter: O
    description: Average economic output per person, adjusted for inflation and for living costs between countries (PPP)
    unit: international-$ (2021 prices)
    aggregation: pop_weighted
    weight_note: Exact. Weighting GDP per person by population gives the group's GDP divided by its people.
    source: owid
    slug: gdp-per-capita-worldbank
    original_id: NY.GDP.PCAP.PP.KD
    producer: World Bank (International Comparison Program), Eurostat, OECD, IMF
    licence: CC BY 4.0
    why_source: PPP in constant 2021 international dollars compares fairly across countries and across years (decision E-35).
    checked: {range: "1990-2024"}

  - column: gdp_growth_pct
    letter: O
    description: Yearly growth of the economy (real GDP, at constant prices)
    unit: "% per year"
    aggregation: gdp_weighted
    weight_note: Bigger economies count more, using GDP (PPP) = gdp_per_capita_ppp x population as the weight, the way the IMF builds regional growth. A population weight would let a large poor country swamp a region's growth rate.
    source: worldbank
    code: NY.GDP.MKTP.KD.ZG
    producer: World Bank and OECD national accounts data
    licence: CC BY 4.0
    why_source: OWID's own GDP growth chart comes from the UN SDG database and only covers 2000-2023; the World Bank series runs from 1961 (decision E-37). The World Bank also builds its own regional growth as a GDP-weighted average.
    checked: {range: "1961-2024 (February 2026 edition)"}

  - column: inflation_cpi_pct
    letter: O
    description: Yearly change in consumer prices (CPI inflation)
    unit: "% per year"
    aggregation: median
    weight_note: The middle country's value, the same method the World Bank uses for this indicator. An average would let one hyperinflation (hundreds or thousands of percent in a year) swamp a whole region.
    source: owid
    slug: inflation-of-consumer-prices
    original_id: FP.CPI.TOTL.ZG
    producer: International Monetary Fund (IMF) International Financial Statistics, via World Bank
    licence: CC BY 4.0
    checked: {range: "1960-2025"}

  - column: unemployment_pct
    letter: O
    description: Share of the labour force without work but available and looking for work (ILO modelled estimates)
    unit: "% of labour force"
    aggregation: pop_weighted
    weight_note: Approximate. The true weight is the labour force, which this table does not hold; population is the closest weight available. Many values are ILO model estimates, not survey results.
    source: owid
    slug: unemployment-rate
    original_id: SL.UEM.TOTL.ZS
    producer: International Labour Organization (ILO) modelled estimates, via World Bank
    licence: CC BY 4.0
    checked: {range: "1991-2025"}

  # ======================= L: LIFE =======================
  - column: life_expectancy_years
    letter: L
    description: Period life expectancy at birth (how long a baby would live at that year's death rates)
    unit: years
    aggregation: pop_weighted
    weight_note: Approximate but standard. The exact group figure needs life tables; a population-weighted average is close.
    source: owid
    slug: life-expectancy
    producer: UN World Population Prospects 2024 (from 1950; OWID uses older historical sources only before 1950)
    licence: CC BY 3.0 IGO (UN WPP); OWID processing CC BY 4.0
    checked: {range: "1543-2023", next_update: "October 2026"}

  - column: under5_deaths_per_1000
    letter: L
    description: Deaths before age five per 1,000 live births (under-five mortality rate)
    unit: deaths per 1,000 live births
    aggregation: pop_weighted
    weight_note: Approximate. The true weight is the number of births; population is the closest weight available.
    source: worldbank
    code: SH.DYN.MORT
    producer: UN Inter-agency Group for Child Mortality Estimation (UNICEF, WHO, World Bank, UN DESA), via World Bank
    licence: CC BY 4.0
    why_source: OWID's child mortality charts give a share in %, and list the UN IGME source under a UNICEF copyright notice. The World Bank publishes the same estimates per 1,000 births under CC BY 4.0 (decision E-37).
    checked: {range: "1960-2024"}

  - column: health_spend_per_capita_ppp
    letter: L
    description: Current health spending per person (public and private), in PPP international dollars at current prices
    unit: current international-$
    aggregation: pop_weighted
    weight_note: Exact. Weighting spending per person by population gives the group's spending divided by its people.
    source: owid
    slug: annual-healthcare-expenditure-per-capita
    original_id: SH.XPD.CHEX.PP.CD
    producer: WHO Global Health Expenditure Database, via World Bank
    licence: CC BY 4.0
    checked: {range: "2000-2024"}

  - column: population
    letter: L
    description: Number of people living in the country (mid-year estimate)
    unit: people
    aggregation: sum
    weight_note: A total, so group figures are a plain sum. Also the weight for every population-weighted average.
    source: worldbank
    code: SP.POP.TOTL
    producer: World Bank estimates (based on UN World Population Prospects and national sources)
    licence: CC BY 4.0
    why_source: OWID's long-run population series switches to UN projections after 2023, but group averages need real estimates as weights for 2024 and 2025. The World Bank series gives estimates up to 2025 (decision E-37).
    checked: {range: "1960-2025 (July 2026 edition)"}

  - column: urban_pop_pct
    letter: L
    description: Share of people living in urban areas, as each country defines urban
    unit: "% of population"
    aggregation: pop_weighted
    weight_note: Exact. The share is of the population, so weighting by population gives the true group share.
    source: owid
    slug: share-of-population-urban
    original_id: SP.URB.TOTL.IN.ZS
    producer: UN World Urbanization Prospects, via World Bank
    licence: CC BY 4.0
    checked: {range: "1960-2024"}

  # ======================= E: ENERGY =======================
  - column: electricity_access_pct
    letter: E
    description: Share of the population with access to electricity
    unit: "% of population"
    aggregation: pop_weighted
    weight_note: Exact. The share is of the population, so weighting by population gives the true group share.
    source: owid
    slug: share-of-the-population-with-access-to-electricity
    original_id: EG.ELC.ACCS.ZS
    producer: World Bank (Sustainable Energy for All database)
    licence: CC BY 4.0
    checked: {range: "1990-2024 (newest edition seen)"}

  - column: renewables_share_elec_pct
    letter: E
    description: Share of the country's electricity generated from renewables (hydro, solar, wind, bioenergy, geothermal, wave, tidal)
    unit: "% of electricity generation"
    aggregation: pop_weighted
    weight_note: Approximate. The true weight is each country's electricity generation, which this table does not hold; population is used instead.
    source: owid
    slug: share-electricity-renewables
    producer: Ember (from 2000) and Energy Institute Statistical Review of World Energy (earlier years)
    licence: "Ember: CC BY 4.0; Energy Institute: free to use with attribution"
    why_source: Electricity, not primary energy (decision E-36). Ember reports electricity for over 200 countries up to 2025, which suits Nigeria and the peers.
    checked: {range: "1985-2025"}

  - column: co2_per_capita_t
    letter: E
    description: Carbon dioxide (CO2) from fossil fuels and industry per person (land-use change not included)
    unit: tonnes per person
    aggregation: pop_weighted
    weight_note: Exact. Weighting emissions per person by population gives the group's emissions divided by its people.
    source: owid
    slug: co-emissions-per-capita
    producer: Global Carbon Project (Global Carbon Budget), population from OWID
    licence: CC BY 4.0
    checked: {range: "1750-2024", next_update: "November 2026"}
```

### `data/reference/blocs.yaml`

```yaml
# blocs.yaml: membership lists for the true/false bloc columns in country_year.
#
# Rule for version 1 (decision E-41): CURRENT membership is applied to every year.
# So "ECOWAS in 2010" uses today's 12 members, not the 15 of 2010. Emolé must say
# "current members" in bloc answers. Historical membership could be added later.
# Membership is counted, not suspension or attendance.
#
# Each list: ISO 3-letter codes, the date the list was checked, and where it came from.

ecowas:
  column: is_ecowas
  name: Economic Community of West African States (ECOWAS)
  as_of: 2026-11-08
  count: 12
  members: [BEN, CPV, CIV, GMB, GHA, GIN, GNB, LBR, NGA, SEN, SLE, TGO]
  notes: >-
    Burkina Faso (BFA), Mali (MLI) and Niger (NER) announced their exit in January 2024;
    ECOWAS confirmed the withdrawal took effect on 29 January 2025 (with a six-month
    transition period). Mauritania left in 2000. All four are NOT counted.
  sources:
    - https://www.myjoyonline.com/west-africa-bloc-ecowas-announces-formal-exit-of-three-junta-led-states/
    - https://von.gov.ng/?p=386362

african_union:
  column: is_african_union
  name: African Union (AU)
  as_of: 2026-11-08
  count: 55
  members: [DZA, AGO, BEN, BWA, BFA, BDI, CPV, CMR, CAF, TCD, COM, COG, COD, CIV, DJI, EGY,
            GNQ, ERI, SWZ, ETH, GAB, GMB, GHA, GIN, GNB, KEN, LSO, LBR, LBY, MDG, MWI, MLI,
            MRT, MUS, MAR, MOZ, NAM, NER, NGA, RWA, ESH, STP, SEN, SYC, SLE, SOM, ZAF, SSD,
            SDN, TZA, TGO, TUN, UGA, ZMB, ZWE]
  notes: >-
    55 members: every widely recognised African country plus the Sahrawi Arab Democratic
    Republic (Western Sahara, ESH). Some members have been suspended at times (for example
    after military takeovers); a suspension does not end membership, so they are counted.
  sources:
    - https://gna.org.gh/?p=305583
    - https://ntlinternational.com/press/group-of-twenty-g20/

eu:
  column: is_eu
  name: European Union (EU)
  as_of: 2026-11-08
  count: 27
  members: [AUT, BEL, BGR, HRV, CYP, CZE, DNK, EST, FIN, FRA, DEU, GRC, HUN, IRL, ITA, LVA,
            LTU, LUX, MLT, NLD, POL, PRT, ROU, SVK, SVN, ESP, SWE]
  notes: >-
    27 members since the United Kingdom left in 2020. No country has joined since Croatia
    in 2013; Montenegro is the next expected member (accession treaty possibly in 2027).
  sources:
    - https://www.bluewin.ch/en/news/international/european-commission-montenegro-could-become-the-next-eu-member-state-li.3661303

g20:
  column: is_g20
  name: Group of Twenty (G20), country members
  as_of: 2026-11-08
  count: 19
  members: [ARG, AUS, BRA, CAN, CHN, FRA, DEU, IND, IDN, ITA, JPN, KOR, MEX, RUS, SAU, ZAF,
            TUR, GBR, USA]
  notes: >-
    The G20 has 21 members: these 19 countries plus the European Union and the African
    Union (a full member since 2023). The two unions are not countries, so they are not
    rows here; ask about them through is_eu and is_african_union.
  sources:
    - https://ntlinternational.com/press/group-of-twenty-g20/
    - https://geographyworlds.com/blog/g20-countries-list/

middle_east:
  column: is_middle_east
  name: Middle East (Emolé's own definition)
  as_of: 2026-11-08
  count: 16
  members: [BHR, EGY, IRN, IRQ, ISR, JOR, KWT, LBN, OMN, PSE, QAT, SAU, SYR, TUR, ARE, YEM]
  notes: >-
    No single official list exists (decision E-07). Emolé's list is the common core used
    by most news and reference works: the Arabian Peninsula, the Levant, Iraq, Iran,
    Turkiye and Egypt. Left out on purpose: Cyprus (an EU member, usually grouped with
    Europe), Armenia, Azerbaijan and Georgia (UN "Western Asia" but usually called the
    South Caucasus), and the Maghreb (Morocco, Algeria, Tunisia, Libya), which belong to
    "Middle East and North Africa" but not to the Middle East itself. For other
    definitions, ask for subregion = 'Western Asia' (UN) or the World Bank region in
    wb_region (its exact current name is listed in DATA FACTS from Step 2).
  sources:
    - Emolé project decision E-07 (documented in docs/DATA.md)
```

### `data/reference/manual_regions.csv`

```text
iso3,name,continent,subregion,reason
TWN,Taiwan,Asia,Eastern Asia,"Not listed separately in UN M49; placed in its geographic subregion, Eastern Asia"
XKX,Kosovo,Europe,Southern Europe,"Not in UN M49; placed with its neighbours in Southern Europe (OWID code OWID_KOS, World Bank code XKX)"
```

### `src/emole/__init__.py`

```python
"""Emolé: an expert on Movement, Output, Life and Energy.

A deterministic data assistant: a language model writes one read-only SQL query,
the database computes every number, and code checks the numbers in every answer.
The display name is Emolé (inspired by ìmọ́lẹ̀, the Yoruba word for light);
every technical name uses plain "emole".
"""

__version__ = "0.1.0"
```

### `src/emole/config.py`

```python
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
```

### `src/emole/groupmath.py`

```python
"""groupmath.py: the one correct way to turn country values into a group value.

Emolé never lets the model invent group maths. Every group figure (a region, a bloc,
an income group, "the world") is made from its member countries by ONE of four rules,
read from column_meta (decision E-06 and E-44):

  sum           add up the countries                  (air passengers, population ...)
  pop_weighted  average, each country counted by its population
                (internet %, GDP per person, life expectancy ...)
  gdp_weighted  average, each country counted by the size of its economy
                (GDP growth: weight = gdp_per_capita_ppp x population)
  median        the middle country's value            (inflation)

Why not a plain average? With a plain average, Cape Verde (about half a million
people) would count as much as Nigeria (over 200 million).

Every result also says how many members had data, so answers can add a note such as
"based on 11 of 12 ECOWAS countries with data for 2023". A country counts as
"with data" only if it has the value AND its weight (population, or GDP) that year,
because without the weight it cannot be included in a weighted average.

Two ways to use it:
  group_value(...)      in Python (tests, coverage report, checks)
  sql_expression(...)   the same maths as a DuckDB SQL expression (Step 2's SQL rules
                        and instant fixes). The tests prove both give the same number.
"""
from dataclasses import dataclass, field

import pandas as pd

RULES = ("sum", "pop_weighted", "gdp_weighted", "median")


@dataclass
class GroupResult:
    value: float
    rule: str
    year: int
    n_with_data: int
    n_members: int
    missing: list = field(default_factory=list)

    def note(self, group_name: str = "", world: bool = False) -> str:
        """The plain-English coverage note added by CODE, never by the model."""
        if world:
            return (f"This is the total of countries with data ({self.n_with_data} of "
                    f"{self.n_members}) for {self.year}, so it can differ slightly from "
                    "official world figures.")
        who = f"{group_name} countries" if group_name else "countries"
        return f"Based on {self.n_with_data} of {self.n_members} {who} with data for {self.year}."


def _usable(rows: pd.DataFrame, column: str, rule: str) -> pd.Series:
    ok = rows[column].notna()
    if rule == "pop_weighted":
        ok &= rows["population"].notna() & (rows["population"] > 0)
    elif rule == "gdp_weighted":
        ok &= (rows["population"].notna() & (rows["population"] > 0)
               & rows["gdp_per_capita_ppp"].notna() & (rows["gdp_per_capita_ppp"] > 0))
    return ok


def group_value(df: pd.DataFrame, column: str, rule: str, year: int, members=None) -> GroupResult:
    """Compute a group value for one column and one year.

    df       rows of country_year (any years; this function picks `year`)
    members  iso3 codes in the group; None = every country in df ("the world")
    """
    if rule not in RULES:
        raise ValueError(f"Unknown rule {rule!r}; use one of {RULES}")
    members = sorted(set(df["iso3"]) if members is None else set(members))
    rows = df[(df["year"] == year) & (df["iso3"].isin(members))]
    ok = _usable(rows, column, rule)
    use = rows[ok]
    have = set(use["iso3"])
    missing = [m for m in members if m not in have]
    if use.empty:
        value = None
    elif rule == "sum":
        value = float(use[column].sum())
    elif rule == "median":
        value = float(use[column].median())
    else:
        w = use["population"] if rule == "pop_weighted" else use["population"] * use["gdp_per_capita_ppp"]
        value = float((use[column] * w).sum() / w.sum())
    return GroupResult(value=value, rule=rule, year=year, n_with_data=len(have),
                       n_members=len(members), missing=missing)


def sql_expression(column: str, rule: str) -> str:
    """The same maths as one DuckDB aggregate expression, to use inside
    SELECT ... FROM country_year WHERE <group filter> AND year = <year>.
    The FILTER clauses make sure the value and its weight come from the SAME rows."""
    c = column
    if rule == "sum":
        return f"SUM({c})"
    if rule == "median":
        return f"MEDIAN({c})"
    if rule == "pop_weighted":
        return (f"SUM({c} * population) FILTER (WHERE {c} IS NOT NULL AND population > 0) / "
                f"SUM(population) FILTER (WHERE {c} IS NOT NULL AND population > 0)")
    if rule == "gdp_weighted":
        cond = f"{c} IS NOT NULL AND population > 0 AND gdp_per_capita_ppp > 0"
        return (f"SUM({c} * population * gdp_per_capita_ppp) FILTER (WHERE {cond}) / "
                f"SUM(population * gdp_per_capita_ppp) FILTER (WHERE {cond})")
    raise ValueError(f"Unknown rule {rule!r}; use one of {RULES}")


def sql_coverage(column: str, rule: str) -> str:
    """How many countries were used (to fill 'based on N of M countries')."""
    if rule == "pop_weighted":
        return f"COUNT(*) FILTER (WHERE {column} IS NOT NULL AND population > 0)"
    if rule == "gdp_weighted":
        return (f"COUNT(*) FILTER (WHERE {column} IS NOT NULL AND population > 0 "
                "AND gdp_per_capita_ppp > 0)")
    return f"COUNT({column})"
```

### `src/emole/data/__init__.py`

```python
"""emole.data: download, clean and combine the public data into country_year."""
```

### `src/emole/data/sources.py`

```python
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
```

### `src/emole/data/fetch.py`

```python
"""fetch.py: download the source files politely and keep dated copies in data/raw/.

File names carry the download date, for example
    data/raw/owid_air-passengers-carried__2026-11-08.csv
    data/raw/wb_IS.AIR.DPRT__2026-11-08.json
    data/raw/wb_countries__2026-11-08.json
A file that is already there is reused, so a second build makes no downloads.
Pass --refresh to the build script to download fresh copies (old ones are kept,
the newest one is used).
"""
import datetime as dt
import json
import re
import time
from pathlib import Path

import requests

from emole import config

_DATE = re.compile(r"__(\d{4}-\d{2}-\d{2})\.(csv|json)$")


class DownloadError(RuntimeError):
    """A source could not be downloaded after several tries."""


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": config.USER_AGENT})
    return s


def get(url: str, session: requests.Session = None) -> requests.Response:
    """GET with a few retries and a pause between them. Raises DownloadError with a
    plain message (including the HTTP status) if it never works."""
    session = session or _session()
    last = ""
    for attempt in range(1, config.HTTP_RETRIES + 1):
        try:
            resp = session.get(url, timeout=config.HTTP_TIMEOUT_SEC)
            if resp.status_code == 200:
                return resp
            last = f"HTTP {resp.status_code}"
            if resp.status_code in (400, 401, 403, 404):
                break                                   # retrying will not help
        except requests.RequestException as e:
            last = type(e).__name__
        time.sleep(2 * attempt)
    raise DownloadError(f"Could not download {url} ({last}). Check your internet connection "
                        "and open the link in a browser to see whether the source moved.")


def raw_path(name: str, ext: str, day: dt.date = None, raw_dir: Path = None) -> Path:
    raw_dir = Path(raw_dir or config.RAW_DIR)
    return raw_dir / f"{name}__{(day or dt.date.today()).isoformat()}.{ext}"


def latest_raw(name: str, ext: str, raw_dir: Path = None):
    """The newest downloaded copy of a source, or None."""
    raw_dir = Path(raw_dir or config.RAW_DIR)
    found = []
    for p in raw_dir.glob(f"{name}__*.{ext}"):
        m = _DATE.search(p.name)
        if m and p.name[: -len(m.group(0))] == name:
            found.append((m.group(1), p))
    return max(found)[1] if found else None


def download_date(path: Path) -> str:
    m = _DATE.search(Path(path).name)
    return m.group(1) if m else ""


def owid_name(slug: str) -> str:
    return f"owid_{slug}"


def wb_name(code: str) -> str:
    return f"wb_{code}"


def fetch_owid(slug: str, refresh: bool = False, offline: bool = False, raw_dir: Path = None) -> Path:
    name = owid_name(slug)
    existing = latest_raw(name, "csv", raw_dir)
    if existing and not refresh:
        return existing
    if offline:
        if existing:
            return existing
        raise DownloadError(f"No saved copy of OWID chart '{slug}' in data/raw and --offline was given.")
    resp = get(config.OWID_CSV_URL.format(slug=slug))
    if not resp.text.lstrip().startswith("Entity,Code,Year"):
        raise DownloadError(f"OWID chart '{slug}' did not return the expected CSV "
                            f"(first characters: {resp.text[:60]!r}).")
    path = raw_path(name, "csv", raw_dir=raw_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(resp.content)
    return path


def fetch_wb_indicator(code: str, refresh: bool = False, offline: bool = False,
                       raw_dir: Path = None) -> Path:
    """Every page of a World Bank indicator, saved as one JSON file:
    {"meta": {...first page's header...}, "records": [...all rows...]}"""
    name = wb_name(code)
    existing = latest_raw(name, "json", raw_dir)
    if existing and not refresh:
        return existing
    if offline:
        if existing:
            return existing
        raise DownloadError(f"No saved copy of World Bank indicator {code} and --offline was given.")
    session, records, meta, page, pages = _session(), [], None, 1, 1
    while page <= pages:
        url = config.WB_INDICATOR_URL.format(code=code, start=config.YEAR_MIN,
                                             end=config.YEAR_MAX, page=page)
        body = get(url, session).json()
        if not isinstance(body, list) or len(body) < 2 or body[1] is None:
            raise DownloadError(f"World Bank indicator {code} returned no data: {str(body)[:200]}")
        meta = meta or body[0]
        pages = int(body[0].get("pages", 1))
        records += body[1]
        page += 1
    path = raw_path(name, "json", raw_dir=raw_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"meta": meta, "records": records}), encoding="utf-8")
    return path


def fetch_wb_countries(refresh: bool = False, offline: bool = False, raw_dir: Path = None) -> Path:
    """The World Bank's list of economies AND aggregates, with region and income group.
    Used twice: to name each country's region and income group, and to recognise the
    World Bank's own group rows (which use 3-letter codes too, like WLD and SSF)."""
    name = "wb_countries"
    existing = latest_raw(name, "json", raw_dir)
    if existing and not refresh:
        return existing
    if offline:
        if existing:
            return existing
        raise DownloadError("No saved copy of the World Bank country list and --offline was given.")
    session, records, meta, page, pages = _session(), [], None, 1, 1
    while page <= pages:
        body = get(config.WB_COUNTRIES_URL.format(page=page), session).json()
        if not isinstance(body, list) or len(body) < 2 or body[1] is None:
            raise DownloadError(f"World Bank country list looks wrong: {str(body)[:200]}")
        meta = meta or body[0]
        pages = int(body[0].get("pages", 1))
        records += body[1]
        page += 1
    path = raw_path(name, "json", raw_dir=raw_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"meta": meta, "records": records}), encoding="utf-8")
    return path
```

### `src/emole/data/parse.py`

```python
"""parse.py: turn each downloaded file into a tidy list of (iso3, year, value) rows,
keeping ONLY real countries and territories, and recording everything removed.

Why removal needs two different rules (decision E-38)
  OWID files: group rows ("World", "Africa", "High-income countries", "European Union
  (27)") have a blank Code or a code starting with OWID_ (World is OWID_WRL).
  So "keep rows whose Code is 3 capital letters" removes them all.

  World Bank files: group rows use 3-letter codes too (WLD = World, SSF = Sub-Saharan
  Africa, EUU = European Union, HIC = High income ...). The 3-letter rule would let
  every one of them in, and "World" would top every country ranking. So World Bank
  rows are checked against the World Bank's own country list, which marks each
  group as an "Aggregate".
"""
import json
import re
from pathlib import Path

import pandas as pd

from emole import config

ISO3 = re.compile(r"^[A-Z]{3}$")
KEYS = ("Entity", "Code", "Year")


class ParseError(ValueError):
    """A downloaded file does not have the shape we expect."""


def _removed(df: pd.DataFrame, reason: str, column: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["column", "code", "entity", "rows", "reason"])
    out = (df.groupby(["code", "entity"], dropna=False).size().reset_index(name="rows"))
    out["reason"] = reason
    out["column"] = column
    return out[["column", "code", "entity", "rows", "reason"]]


def pick_value_column(df: pd.DataFrame, wanted: str = None, label: str = "") -> str:
    """OWID files have Entity, Code, Year and usually ONE value column. If there are
    several, sources.yaml must name the right one in value_column."""
    others = [c for c in df.columns if c not in KEYS]
    if wanted:
        if wanted not in df.columns:
            raise ParseError(f"{label}: value_column '{wanted}' not found. Columns are: {others}")
        return wanted
    numeric = [c for c in others if pd.api.types.is_numeric_dtype(df[c])]
    if len(numeric) == 1:
        return numeric[0]
    raise ParseError(f"{label}: expected one numeric value column, found {numeric or others}. "
                     "Add value_column: <name> to this entry in data/sources.yaml.")


def parse_owid(path: Path, column: str, value_column: str = None):
    """Returns (rows, removed, info). rows has iso3, year, value, entity."""
    df = pd.read_csv(path, encoding="utf-8")
    missing = [k for k in KEYS if k not in df.columns]
    if missing:
        raise ParseError(f"{Path(path).name}: missing {missing}. Columns: {list(df.columns)}")
    vcol = pick_value_column(df, value_column, Path(path).name)
    df = df.rename(columns={"Entity": "entity", "Code": "code", "Year": "year", vcol: "value"})
    df["code"] = df["code"].fillna("").astype(str).str.strip()
    renamed = df["code"].isin(config.OWID_CODE_RENAMES)
    df.loc[renamed, "code"] = df.loc[renamed, "code"].map(config.OWID_CODE_RENAMES)

    blank = df["code"] == ""
    owid_code = df["code"].str.startswith("OWID_")
    other_bad = ~blank & ~owid_code & ~df["code"].str.match(ISO3)
    removed = pd.concat([
        _removed(df[blank], "blank code: an OWID group row (region, income group, union)", column),
        _removed(df[owid_code], "OWID_ code: OWID group or former country (World, USSR ...)", column),
        _removed(df[other_bad], "code is not 3 capital letters", column),
    ], ignore_index=True)
    keep = df[~(blank | owid_code | other_bad)].copy()
    keep["value"] = pd.to_numeric(keep["value"], errors="coerce")
    keep = keep.dropna(subset=["value"])
    keep["year"] = keep["year"].astype(int)
    _no_duplicates(keep, Path(path).name)
    info = {"value_column": vcol, "file": Path(path).name}
    return keep.rename(columns={"code": "iso3"})[["iso3", "year", "value", "entity"]], removed, info


def parse_wb_countries(path: Path) -> pd.DataFrame:
    """The World Bank country list: one row per code, with region, income group and
    whether it is an aggregate (a group row)."""
    body = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = []
    for r in body["records"]:
        region = (r.get("region") or {}).get("value", "").strip()     # values can carry trailing spaces
        income = (r.get("incomeLevel") or {}).get("value", "").strip()
        rows.append({"iso3": r["id"].strip(), "wb_name": r.get("name", "").strip(),
                     "wb_region": region, "wb_income": income,
                     "is_aggregate": region == "Aggregates"})
    df = pd.DataFrame(rows)
    if df.empty or df["is_aggregate"].all():
        raise ParseError(f"{Path(path).name}: no countries found in the World Bank list")
    return df


INCOME_GROUPS = {
    "Low income": "low",
    "Lower middle income": "lower-middle",
    "Upper middle income": "upper-middle",
    "High income": "high",
}


def parse_wb_indicator(path: Path, column: str, aggregates: set):
    """Returns (rows, removed, info) for one World Bank indicator file."""
    body = json.loads(Path(path).read_text(encoding="utf-8"))
    recs = body.get("records") or []
    df = pd.DataFrame({
        "code": [str(r.get("countryiso3code") or "").strip() for r in recs],
        "entity": [(r.get("country") or {}).get("value", "") for r in recs],
        "year": [r.get("date") for r in recs],
        "value": [r.get("value") for r in recs],
    })
    if df.empty:
        raise ParseError(f"{Path(path).name}: no records")
    blank = df["code"] == ""
    agg = df["code"].isin(aggregates)
    other_bad = ~blank & ~agg & ~df["code"].str.match(ISO3)
    removed = pd.concat([
        _removed(df[blank], "blank code in World Bank file", column),
        _removed(df[agg], "World Bank aggregate (a group row with a 3-letter code)", column),
        _removed(df[other_bad], "code is not 3 capital letters", column),
    ], ignore_index=True)
    keep = df[~(blank | agg | other_bad)].copy()
    keep["value"] = pd.to_numeric(keep["value"], errors="coerce")
    keep["year"] = pd.to_numeric(keep["year"], errors="coerce")
    keep = keep.dropna(subset=["value", "year"])
    keep["year"] = keep["year"].astype(int)
    _no_duplicates(keep, Path(path).name)
    info = {"file": Path(path).name, "lastupdated": (body.get("meta") or {}).get("lastupdated")}
    return keep.rename(columns={"code": "iso3"})[["iso3", "year", "value", "entity"]], removed, info


def _no_duplicates(df: pd.DataFrame, label: str) -> None:
    dup = df.duplicated(["code", "year"]) if "code" in df.columns else df.duplicated(["iso3", "year"])
    if dup.any():
        sample = df[dup].head(3).to_dict("records")
        raise ParseError(f"{label}: the same country and year appears twice, e.g. {sample}")
```

### `src/emole/data/groups.py`

```python
"""groups.py: the grouping columns of country_year.

  continent, subregion   UN M49 (data/reference/un_m49.csv), plus Taiwan and Kosovo
                         from data/reference/manual_regions.csv (they are not in M49)
  wb_region              World Bank region, from the World Bank country list
  income_group           World Bank income group: low, lower-middle, upper-middle, high.
                         It is the CURRENT classification (FY2027, effective 1 July 2026)
                         applied to every year, and Emolé must say so.
  is_ecowas ... is_middle_east   true/false, from data/reference/blocs.yaml

Every country in the table gets every column filled where a source exists; countries
with no match are listed (never silently left blank).
"""
from pathlib import Path

import pandas as pd

from emole import config
from emole.data.parse import INCOME_GROUPS
from emole.data.sources import load_blocs

GROUP_COLUMNS = ["continent", "subregion", "wb_region", "income_group"]


def load_regions(ref_dir: Path = None) -> pd.DataFrame:
    ref_dir = Path(ref_dir or config.REFERENCE_DIR)
    m49 = pd.read_csv(ref_dir / "un_m49.csv", dtype=str, keep_default_na=False)
    manual = pd.read_csv(ref_dir / "manual_regions.csv", dtype=str, keep_default_na=False)
    clash = set(m49["iso3"]) & set(manual["iso3"])
    if clash:
        raise ValueError(f"manual_regions.csv repeats codes already in UN M49: {sorted(clash)}")
    both = pd.concat([m49[["iso3", "name", "continent", "subregion"]],
                      manual[["iso3", "name", "continent", "subregion"]]], ignore_index=True)
    return both.replace({"": None})


def build_groups(iso3_list, wb_countries: pd.DataFrame, ref_dir: Path = None):
    """Returns (groups, unmatched).
    groups: one row per iso3 with every grouping column.
    unmatched: {"continent": [...codes...], "wb_region": [...], ...} for the report."""
    ref_dir = Path(ref_dir or config.REFERENCE_DIR)
    base = pd.DataFrame({"iso3": sorted(set(iso3_list))})
    regions = load_regions(ref_dir)
    g = base.merge(regions[["iso3", "continent", "subregion"]], on="iso3", how="left")

    wb = wb_countries[~wb_countries["is_aggregate"]][["iso3", "wb_region", "wb_income"]]
    g = g.merge(wb, on="iso3", how="left")
    g["income_group"] = g["wb_income"].map(INCOME_GROUPS)     # "Not classified" -> empty
    g = g.drop(columns=["wb_income"])
    g["wb_region"] = g["wb_region"].replace({"": None})

    blocs = load_blocs(ref_dir / "blocs.yaml")
    for b in blocs.values():
        g[b["column"]] = g["iso3"].isin(b["members"])

    unmatched = {col: g.loc[g[col].isna(), "iso3"].tolist() for col in GROUP_COLUMNS}
    present = set(g["iso3"])
    unmatched["bloc members missing from the table"] = sorted(
        {m for b in blocs.values() for m in b["members"] if m not in present})
    return g, unmatched


def bloc_columns(ref_dir: Path = None) -> list:
    blocs = load_blocs(Path(ref_dir or config.REFERENCE_DIR) / "blocs.yaml")
    return [b["column"] for b in blocs.values()]
```

### `src/emole/data/build.py`

```python
"""build.py: build data/emole.duckdb (and the committed snapshot) from the sources.

The steps, in order:
  1. Read and check data/sources.yaml (17 columns) and the reference lists.
  2. Download each source once (or reuse the saved copy in data/raw/).
  3. Clean each file to (iso3, year, value): real countries only, every removed row recorded.
  4. Join all columns on iso3 + year into one wide table, years YEAR_MIN to YEAR_MAX.
  5. Add the country name and the grouping columns (continent ... is_middle_east).
  6. Measure each column: first year, latest year, latest year with broad coverage.
  7. Write the snapshot (data/processed/) and the database (built in a temporary file,
     then swapped in, so there is never a half-built database).

Run through the script:  python scripts/build_data.py   (see that file for options)
"""
import argparse
import datetime as dt
import json
import os
import platform
import sys
from pathlib import Path

import duckdb
import pandas as pd

from emole import config
from emole.data import fetch
from emole.data.groups import build_groups, load_regions
from emole.data.parse import ParseError, parse_owid, parse_wb_countries, parse_wb_indicator
from emole.data.sources import SourceListError, load_sources, source_id, source_url

ID_COLUMNS = ["country", "iso3", "year"]


# ---------------------------------------------------------------------------
# 2. DOWNLOAD (or reuse)
# ---------------------------------------------------------------------------
def collect_files(sources: list, raw_dir: Path, refresh: bool, offline: bool) -> dict:
    files = {"_wb_countries": fetch.fetch_wb_countries(refresh, offline, raw_dir)}
    for c in sources:
        print(f"   {c['column']:<28} ", end="", flush=True)
        if c["source"] == "owid":
            files[c["column"]] = fetch.fetch_owid(c["slug"], refresh, offline, raw_dir)
        else:
            files[c["column"]] = fetch.fetch_wb_indicator(c["code"], refresh, offline, raw_dir)
        print(files[c["column"]].name)
    return files


# ---------------------------------------------------------------------------
# 3-5. CLEAN, JOIN, ADD GROUPS
# ---------------------------------------------------------------------------
def build_table(sources: list, files: dict, ref_dir: Path = None,
                year_min: int = None, year_max: int = None):
    """Returns (wide, removed, infos, unmatched). Pure: no downloads, no writing."""
    year_min = config.YEAR_MIN if year_min is None else year_min
    year_max = config.YEAR_MAX if year_max is None else year_max
    wb_countries = parse_wb_countries(files["_wb_countries"])
    aggregates = set(wb_countries.loc[wb_countries["is_aggregate"], "iso3"])

    longs, removed, infos, names = [], [], {}, []
    for c in sources:
        col = c["column"]
        if c["source"] == "owid":
            rows, rem, info = parse_owid(files[col], col, c.get("value_column"))
            names.append(rows[["iso3", "entity"]].assign(src="owid"))
        else:
            rows, rem, info = parse_wb_indicator(files[col], col, aggregates)
            names.append(rows[["iso3", "entity"]].assign(src="wb"))
        in_range = rows["year"].between(year_min, year_max)
        info.update(rows_kept=int(in_range.sum()), rows_outside_years=int((~in_range).sum()),
                    download_date=fetch.download_date(files[col]))
        infos[col] = info
        longs.append(rows.loc[in_range, ["iso3", "year", "value"]].assign(column=col))
        removed.append(rem)

    long = pd.concat(longs, ignore_index=True)
    wide = long.pivot(index=["iso3", "year"], columns="column", values="value").reset_index()
    wide.columns.name = None
    metric_cols = [c["column"] for c in sources]
    for col in metric_cols:                         # a column with no rows at all still exists
        if col not in wide.columns:
            wide[col] = pd.NA
    # Totals that are whole numbers (passengers, people) are stored as whole numbers.
    for c in sources:
        s = wide[c["column"]]
        if c["aggregation"] == "sum" and s.notna().any() and (s.dropna() % 1 == 0).all():
            wide[c["column"]] = s.round().astype("Int64")

    wide["country"] = wide["iso3"].map(_country_names(pd.concat(names), wb_countries, ref_dir))
    groups, unmatched = build_groups(wide["iso3"].unique(), wb_countries, ref_dir)
    wide = wide.merge(groups, on="iso3", how="left")
    group_cols = [c for c in groups.columns if c != "iso3"]
    for col in ["country"] + [c for c in group_cols if not c.startswith("is_")]:
        # One kind of "empty" (None) everywhere, the same as after a round trip through Parquet.
        wide[col] = wide[col].astype(object).where(wide[col].notna(), None)
    wide = wide[ID_COLUMNS + group_cols + metric_cols].sort_values(["iso3", "year"])
    wide = wide.reset_index(drop=True)
    removed = pd.concat(removed, ignore_index=True).sort_values(["column", "reason", "entity"])
    return wide, removed.reset_index(drop=True), infos, unmatched


def _country_names(names: pd.DataFrame, wb_countries: pd.DataFrame, ref_dir) -> dict:
    """OWID's standard country names first (they are clean: 'Egypt', not 'Egypt, Arab
    Rep.'), then the World Bank's, then the UN M49 name."""
    out = {}
    m49 = load_regions(ref_dir).set_index("iso3")["name"].to_dict()
    wb = wb_countries.set_index("iso3")["wb_name"].to_dict()
    owid = names[names["src"] == "owid"]
    if not owid.empty:
        out.update(owid.groupby("iso3")["entity"].agg(lambda s: s.value_counts().index[0]).to_dict())
    for code in set(names["iso3"]):
        out.setdefault(code, wb.get(code) or m49.get(code) or code)
    return out


# ---------------------------------------------------------------------------
# 6. MEASURE EACH COLUMN
# ---------------------------------------------------------------------------
def broad_year(counts: pd.Series, latest: int) -> int:
    """Newest year whose country count is at least BROAD_COVERAGE_SHARE of the best
    count in the 10 years up to the latest year."""
    window = counts[(counts.index > latest - 10) & (counts.index <= latest)]
    peak = window.max()
    good = window[window >= config.BROAD_COVERAGE_SHARE * peak]
    return int(good.index.max())


def column_meta(wide: pd.DataFrame, sources: list, infos: dict) -> pd.DataFrame:
    rows = []
    for c in sources:
        col = c["column"]
        have = wide[wide[col].notna()]
        if have.empty:
            first = latest = broad = None
            n_latest = n_broad = 0
        else:
            counts = have.groupby("year")["iso3"].nunique()
            first, latest = int(counts.index.min()), int(counts.index.max())
            broad = broad_year(counts, latest)
            n_latest, n_broad = int(counts[latest]), int(counts[broad])
        info = infos.get(col, {})
        rows.append({
            "column": col, "letter": c["letter"], "description": c["description"],
            "unit": c["unit"], "aggregation": c["aggregation"], "weight_note": c["weight_note"],
            "caveat": c.get("caveat") or "", "source": c["source"], "source_id": source_id(c),
            "original_id": c.get("original_id") or c.get("code") or "",
            "source_url": source_url(c), "producer": c["producer"], "licence": c["licence"],
            "why_source": c.get("why_source") or "",
            "first_year": first, "latest_year": latest, "latest_broad_year": broad,
            "countries_latest": n_latest, "countries_broad": n_broad,
            "raw_file": info.get("file", ""), "download_date": info.get("download_date", ""),
        })
    meta = pd.DataFrame(rows)
    for k in ("first_year", "latest_year", "latest_broad_year"):
        meta[k] = meta[k].astype("Int64")
    return meta


# ---------------------------------------------------------------------------
# 7. WRITE
# ---------------------------------------------------------------------------
def build_info(wide: pd.DataFrame, infos: dict, year_min: int, year_max: int) -> dict:
    return {
        "build_version": config.BUILD_VERSION,
        "built_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "year_min": year_min, "year_max": year_max,
        "rows": int(len(wide)), "countries": int(wide["iso3"].nunique()),
        "first_year_in_table": int(wide["year"].min()), "last_year_in_table": int(wide["year"].max()),
        "python": platform.python_version(), "pandas": pd.__version__, "duckdb": duckdb.__version__,
        "sources": infos,
    }


def write_snapshot(wide, meta, info, removed, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    wide.to_parquet(out_dir / config.SNAPSHOT_TABLE.name, index=False)
    meta.to_csv(out_dir / config.SNAPSHOT_META.name, index=False, encoding="utf-8", lineterminator="\n")
    (out_dir / config.SNAPSHOT_INFO.name).write_text(json.dumps(info, indent=2), encoding="utf-8")
    removed.to_csv(out_dir / config.REMOVED_ROWS.name, index=False, encoding="utf-8", lineterminator="\n")


def write_database(wide, meta, info, db_path: Path) -> Path:
    """Build in a temporary file, then swap it in."""
    db_path = Path(db_path)
    tmp = db_path.with_suffix(".duckdb.tmp")
    if tmp.exists():
        tmp.unlink()
    con = duckdb.connect(str(tmp))
    try:
        con.register("wide_df", wide)
        con.register("meta_df", meta)
        con.execute("CREATE TABLE country_year AS SELECT * FROM wide_df")
        con.execute("CREATE TABLE column_meta AS SELECT * FROM meta_df")
        flat = [(k, json.dumps(v) if isinstance(v, (dict, list)) else str(v)) for k, v in info.items()]
        con.execute("CREATE TABLE build_info (key VARCHAR, value VARCHAR)")
        con.executemany("INSERT INTO build_info VALUES (?, ?)", flat)
    finally:
        con.close()
    try:
        os.replace(tmp, db_path)
    except PermissionError:
        sys.exit(f"\nCould not replace {db_path.name}: it is open somewhere (a notebook, the "
                 "chatbot or a database viewer). Close it and run the build again.")
    return db_path


def read_snapshot(out_dir: Path):
    wide = pd.read_parquet(out_dir / config.SNAPSHOT_TABLE.name)
    meta = pd.read_csv(out_dir / config.SNAPSHOT_META.name, keep_default_na=False,
                       na_values={"first_year": [""], "latest_year": [""], "latest_broad_year": [""]})
    for k in ("first_year", "latest_year", "latest_broad_year"):
        meta[k] = meta[k].astype("Int64")
    info = json.loads((out_dir / config.SNAPSHOT_INFO.name).read_text(encoding="utf-8"))
    return wide, meta, info


# ---------------------------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------------------------
def _plural(n: int, word: str) -> str:
    return f"{n:,} {word}" + ("" if n == 1 else "s")


def summary(wide, meta, info, removed=None, unmatched=None) -> str:
    lines = [
        "=" * 78,
        f"Emole data build  |  BUILD_VERSION {info['build_version']}  |  built {info['built_at_utc']}",
        "=" * 78,
        f"country_year: {info['rows']:,} rows | {info['countries']} countries and territories | "
        f"years {info['first_year_in_table']}-{info['last_year_in_table']}",
        "",
        "  letter column                          latest  broad  countries(broad)  aggregation",
    ]
    for _, m in meta.iterrows():
        lines.append(f"  {m['letter']:<6} {m['column']:<30} {str(m['latest_year']):>6} "
                     f"{str(m['latest_broad_year']):>6} {m['countries_broad']:>17}  {m['aggregation']}")
    if removed is not None and len(removed):
        lines.append("")
        lines.append("Rows removed (full list in data/processed/removed_rows.csv):")
        for reason, part in removed.groupby("reason"):
            ents = sorted(set(part["entity"].astype(str)))
            shown = ", ".join(ents[:8]) + (f" ... (+{len(ents) - 8} more)" if len(ents) > 8 else "")
            n_rows = int(part["rows"].sum())
            lines.append(f"  - {reason}: {_plural(len(ents), 'name')}, {_plural(n_rows, 'row')}. {shown}")
    if unmatched:
        lines.append("")
        lines.append("Grouping gaps (countries with no value for a grouping column):")
        for k, v in unmatched.items():
            lines.append(f"  - {k}: {len(v)}" + (f" -> {', '.join(v[:15])}" if v else ""))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def run(refresh: bool = False, offline: bool = False, from_snapshot: bool = False,
        sources_file: Path = None, raw_dir: Path = None, ref_dir: Path = None,
        out_dir: Path = None, db_path: Path = None, year_min: int = None, year_max: int = None) -> dict:
    out_dir = Path(out_dir or config.PROCESSED_DIR)
    db_path = Path(db_path or config.DB_PATH)
    if from_snapshot:
        print("\n[1/2] Reading the committed snapshot (no internet needed)")
        wide, meta, info = read_snapshot(out_dir)
        print("[2/2] Writing the database")
        write_database(wide, meta, info, db_path)
        print(summary(wide, meta, info))
        return {"wide": wide, "meta": meta, "info": info}

    year_min = config.YEAR_MIN if year_min is None else year_min
    year_max = config.YEAR_MAX if year_max is None else year_max
    print("\n[1/4] Checking data/sources.yaml and the reference lists")
    sources = load_sources(sources_file)
    print(f"   {len(sources)} columns listed")
    print("\n[2/4] Downloading (or reusing saved copies in data/raw/)")
    files = collect_files(sources, raw_dir or config.RAW_DIR, refresh, offline)
    print("\n[3/4] Cleaning and joining")
    wide, removed, infos, unmatched = build_table(sources, files, ref_dir, year_min, year_max)
    meta = column_meta(wide, sources, infos)
    info = build_info(wide, infos, year_min, year_max)
    print("\n[4/4] Writing the snapshot and the database")
    write_snapshot(wide, meta, info, removed, out_dir)
    write_database(wide, meta, info, db_path)
    print(summary(wide, meta, info, removed, unmatched))
    print(f"\nWritten: {db_path}\n         {out_dir}")
    return {"wide": wide, "meta": meta, "info": info, "removed": removed, "unmatched": unmatched}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Build Emole's country_year database.")
    ap.add_argument("--refresh", action="store_true", help="download fresh copies of every source")
    ap.add_argument("--offline", action="store_true", help="never download; use saved copies only")
    ap.add_argument("--from-snapshot", action="store_true",
                    help="rebuild the database from data/processed/ (no downloads, no cleaning)")
    args = ap.parse_args(argv)
    if args.refresh and (args.offline or args.from_snapshot):
        ap.error("--refresh cannot be combined with --offline or --from-snapshot")
    if args.from_snapshot and not config.SNAPSHOT_TABLE.exists():
        sys.exit(f"\nNo snapshot yet at {config.SNAPSHOT_TABLE}. Run the full build once "
                 "(python scripts/build_data.py), or pull the latest repo.")
    try:
        run(refresh=args.refresh, offline=args.offline, from_snapshot=args.from_snapshot)
    except (fetch.DownloadError, ParseError, SourceListError, ValueError) as e:
        # Expected problems get one clear sentence, not a page of Python traceback.
        sys.exit(f"\nBUILD STOPPED: {e}")
```

### `src/emole/data/coverage.py`

```python
"""coverage.py: write docs/coverage_report.md, a health check of what is REALLY in
the database (in the spirit of the earlier build's data audit script).

It answers four questions:
  1. For every column: first year, latest year, latest year with broad coverage,
     and how many countries have data.
  2. For Nigeria and each peer: which of the latest 5 years are missing, per column.
  3. For each region, income group and bloc: how many members have data in each
     column's broad-coverage year.
  4. Which columns are FLAGGED by the rule written before the first real build
     (see config.FLAG_*). A flag means "look at this", never "drop it": drops are
     agreed with the owner.
"""
import datetime as dt
from pathlib import Path

import duckdb
import pandas as pd

from emole import config


def load(db_path: Path = None):
    con = duckdb.connect(str(db_path or config.DB_PATH), read_only=True)
    try:
        wide = con.execute("SELECT * FROM country_year").fetchdf()
        meta = con.execute("SELECT * FROM column_meta").fetchdf()
    finally:
        con.close()
    return wide, meta


def peer_gaps(wide: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    """One row per peer, one column per data column: 'ok' or the missing years."""
    rows = []
    for iso, name in config.PEER_COUNTRIES.items():
        row = {"country": f"{name} ({iso})"}
        mine = wide[wide["iso3"] == iso]
        for _, m in meta.iterrows():
            col, latest = m["column"], m["latest_year"]
            if pd.isna(latest):
                row[col] = "no data"
                continue
            years = range(int(latest) - config.RECENT_YEARS + 1, int(latest) + 1)
            have = set(mine.loc[mine[col].notna(), "year"])
            gaps = [y for y in years if y not in have]
            row[col] = "ok" if not gaps else ("none" if len(gaps) == len(years)
                                              else "miss " + ",".join(str(y)[2:] for y in gaps))
        rows.append(row)
    return pd.DataFrame(rows)


def group_coverage(wide: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    """'members with data / members' in each column's broad-coverage year."""
    groups = []
    for col in ("continent", "subregion", "wb_region", "income_group"):
        for val in sorted(wide[col].dropna().unique()):
            groups.append((f"{col} = {val}", wide.loc[wide[col] == val, "iso3"].unique()))
    for col in [c for c in wide.columns if c.startswith("is_")]:
        groups.append((col, wide.loc[wide[col].fillna(False).astype(bool), "iso3"].unique()))
    rows = []
    for label, members in groups:
        row = {"group": label, "members": len(members)}
        part = wide[wide["iso3"].isin(members)]
        for _, m in meta.iterrows():
            year = m["latest_broad_year"]
            if pd.isna(year):
                row[m["column"]] = "-"
                continue
            n = part.loc[(part["year"] == int(year)) & part[m["column"]].notna(), "iso3"].nunique()
            row[m["column"]] = f"{n}/{len(members)}"
        rows.append(row)
    return pd.DataFrame(rows)


def flags(wide: pd.DataFrame, meta: pd.DataFrame, peers: pd.DataFrame) -> list:
    """Apply the pre-registered rule. Returns [(column, reason), ...]."""
    out = []
    for _, m in meta.iterrows():
        col, year = m["column"], m["latest_broad_year"]
        if pd.isna(year):
            out.append((col, "no data at all"))
            continue
        base = wide.loc[(wide["year"] == int(year)) & wide["population"].notna(), "iso3"].nunique()
        n = wide.loc[(wide["year"] == int(year)) & wide[col].notna(), "iso3"].nunique()
        if base and n / base < config.FLAG_MIN_COUNTRY_SHARE:
            out.append((col, f"only {n} of {base} countries with a population figure have it in {int(year)}"))
        ng = peers.loc[peers["country"].str.contains("(NGA)", regex=False), col]
        if len(ng) and ng.iloc[0] in ("none", "no data"):
            out.append((col, "Nigeria has no value in the latest 5 years"))
        bad = []
        for _, p in peers.iterrows():
            v = p[col]
            if v in ("none", "no data"):
                bad.append(p["country"])
            elif v.startswith("miss ") and len(v[5:].split(",")) > config.FLAG_MAX_PEER_GAPS:
                bad.append(p["country"])
        if bad:
            out.append((col, f"peers missing more than {config.FLAG_MAX_PEER_GAPS} of the latest "
                             f"{config.RECENT_YEARS} years: {', '.join(bad)}"))
    return out


def _md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join("" if pd.isna(v) else str(v) for v in r) + " |")
    return "\n".join(lines)


def report(db_path: Path = None, out: Path = None, removed_csv: Path = None) -> str:
    wide, meta = load(db_path)
    peers = peer_gaps(wide, meta)
    groups = group_coverage(wide, meta)
    flagged = flags(wide, meta, peers)
    removed_csv = Path(removed_csv or config.REMOVED_ROWS)

    cols = meta[["letter", "column", "unit", "first_year", "latest_year", "latest_broad_year",
                 "countries_latest", "countries_broad", "aggregation", "source", "source_id"]]
    parts = [
        "# Emolé coverage report",
        "",
        f"Generated {dt.date.today().isoformat()} by `python scripts/coverage_report.py` from "
        f"`data/emole.duckdb` ({len(wide):,} rows, {wide['iso3'].nunique()} countries and territories, "
        f"years {int(wide['year'].min())}-{int(wide['year'].max())}).",
        "",
        "**How to read it.** `latest` is the newest year with any data. `broad` is the newest year "
        f"in which at least {int(config.BROAD_COVERAGE_SHARE * 100)}% of the column's usual countries "
        "report: use it for rankings and group answers. A country's own latest year can be newer.",
        "",
        "## 1. Columns",
        "",
        _md_table(cols),
        "",
        "## 2. Flags (rule written before the first real build)",
        "",
        f"A column is flagged when: fewer than {int(config.FLAG_MIN_COUNTRY_SHARE * 100)}% of countries "
        "with a population figure have it in its broad year; or Nigeria has no value in its latest "
        f"{config.RECENT_YEARS} years; or a peer misses more than {config.FLAG_MAX_PEER_GAPS} "
        "of those years. A flag means review, not drop. Drops are agreed with the owner "
        "and recorded in docs/DATA.md.",
        "",
    ]
    parts += [f"- **{c}**: {r}" for c, r in flagged] or ["- No column is flagged."]
    parts += [
        "",
        f"## 3. Nigeria and peers: gaps in each column's latest {config.RECENT_YEARS} years",
        "",
        "`ok` = all years present. `miss 21,23` = 2021 and 2023 missing. `none` = no value in those years.",
        "",
        _md_table(peers),
        "",
        "## 4. Regions, income groups and blocs: members with data in each column's broad year",
        "",
        "Membership and income groups are the CURRENT ones, applied to every year.",
        "",
        _md_table(groups),
        "",
    ]
    if removed_csv.exists():
        rem = pd.read_csv(removed_csv, keep_default_na=False)
        summ = (rem.groupby("reason").agg(names=("entity", "nunique"), rows=("rows", "sum"))
                .reset_index())
        parts += ["## 5. Rows removed during the build", "",
                  "Full list: `data/processed/removed_rows.csv`.", "", _md_table(summ), ""]
    text = "\n".join(parts)
    out = Path(out or config.COVERAGE_REPORT)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"Coverage report written to {out}")
    print(f"Flagged columns: {len(flagged)}")
    for c, r in flagged:
        print(f"  - {c}: {r}")
    return text
```

### `scripts/build_data.py`

```python
"""build_data.py: build Emole's database from public data, in one command.

    python scripts/build_data.py                  download what is missing, then build
    python scripts/build_data.py --refresh        download fresh copies of every source
    python scripts/build_data.py --offline        never download; use saved copies in data/raw/
    python scripts/build_data.py --from-snapshot  rebuild data/emole.duckdb from the committed
                                                  snapshot in data/processed/ (no internet)

It writes:
    data/emole.duckdb                      the database Emole reads (git-ignored)
    data/processed/country_year.parquet    the committed snapshot of the table
    data/processed/column_meta.csv         one row per column: unit, rule, source, years
    data/processed/build_info.json         when and how it was built
    data/processed/removed_rows.csv        every group row that was removed, and why
Then run:  python scripts/coverage_report.py
"""
from emole.data.build import main

if __name__ == "__main__":
    main()
```

### `scripts/coverage_report.py`

```python
"""coverage_report.py: write docs/coverage_report.md from data/emole.duckdb.

    python scripts/coverage_report.py

Run it after every build. It shows what data really exists (by column, for Nigeria
and the peer countries, and for every region and bloc) and flags columns to review.
"""
from emole.data.coverage import report

if __name__ == "__main__":
    report()
```

### `scripts/check_no_secrets.py`

```python
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
```

### `scripts/make_m49_reference.py`

```python
"""make_m49_reference.py: turn the UN M49 region list into data/reference/un_m49.csv.

You do NOT need to run this for a normal build. Its output (un_m49.csv) is committed,
so the build works offline. Run it only if the UN changes its regions and you want
to refresh the file.

Where the data comes from
  The UN Statistics Division publishes the M49 standard (which country sits in which
  region) at https://unstats.un.org/unsd/methodology/m49/ but offers no stable file
  link, because its download buttons are made by JavaScript. The open-source package
  "un-m49" (MIT licence, by Titus Wormer) holds the same list as code, so we read that.

What it writes (one row per country or area that has an ISO code)
  iso3, m49_code, name, continent, m49_subregion, intermediate_region, subregion
  "subregion" is the most specific level: the intermediate region when M49 has one
  (Nigeria -> Western Africa), otherwise the M49 subregion (Egypt -> Northern Africa).

Run:  python scripts/make_m49_reference.py
      python scripts/make_m49_reference.py --file path/to/index.js   (use a saved copy)
"""
import argparse
import csv
import hashlib
import re
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "reference" / "un_m49.csv"
URL = "https://raw.githubusercontent.com/wooorm/un-m49/main/index.js"
# A name is written in 'single quotes', or in "double quotes" when it holds an
# apostrophe ("Lao People's Democratic Republic"). Both forms must match, or those
# countries silently go missing (this happened on the first run: North Korea and Laos).
ENTRY = re.compile(r"\{\s*type:\s*(\d),\s*name:\s*(?:'((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\"),"
                   r"\s*code:\s*'(\d{3})'"
                   r"(?:,\s*iso3166:\s*'([A-Z]{3})')?(?:,\s*parent:\s*'(\d{3})')?\s*\}")


def parse(text: str) -> list:
    rows = []
    for m in ENTRY.finditer(text):
        name = (m[2] if m[2] is not None else m[3]).replace("\\'", "'")
        rows.append({"type": int(m[1]), "name": name, "code": m[4], "iso3": m[5], "parent": m[6]})
    expected = len(re.findall(r"\btype:\s*\d", text))
    if len(rows) != expected:
        sys.exit(f"Parsed {len(rows)} entries but the file has {expected}: check the pattern.")
    return rows


def build(rows: list) -> list:
    by_code = {r["code"]: r for r in rows}
    out = []
    for r in rows:
        if r["type"] != 4 or not r["iso3"]:
            continue
        level = {1: "", 2: "", 3: ""}
        parent = r["parent"]
        while parent and parent in by_code:
            p = by_code[parent]
            if p["type"] in level:
                level[p["type"]] = p["name"]
            parent = p["parent"]
        out.append({"iso3": r["iso3"], "m49_code": r["code"], "name": r["name"],
                    "continent": level[1], "m49_subregion": level[2],
                    "intermediate_region": level[3],
                    "subregion": level[3] or level[2]})
    return sorted(out, key=lambda x: x["iso3"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="read a saved copy of un-m49's index.js instead of downloading")
    args = ap.parse_args()
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    else:
        resp = requests.get(URL, timeout=60, headers={"User-Agent": "EmoleDataBuild/0.1"})
        resp.raise_for_status()
        text = resp.text
    rows = build(parse(text))
    if len(rows) < 240:
        sys.exit(f"Only {len(rows)} countries parsed: the package format may have changed.")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    print(f"Wrote {len(rows)} countries and areas to {OUT}")
    print(f"Source fingerprint (sha256, first 16): {digest}  (record it in docs/DATA.md)")


if __name__ == "__main__":
    main()
```

### `tests/__init__.py`

```python

```

### `tests/conftest.py`

```python
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
```

### `tests/test_sources.py`

```python
"""The real source list and bloc lists are complete and consistent."""
import pandas as pd
import pytest

from emole import config
from emole.data.sources import SourceListError, load_blocs, load_sources


def test_real_sources_have_all_17_columns():
    cols = load_sources()
    assert len(cols) == 17
    assert {c["letter"] for c in cols} == {"M", "O", "L", "E"}
    names = [c["column"] for c in cols]
    assert len(names) == len(set(names))


def test_totals_are_summed_and_rates_are_weighted():
    rules = {c["column"]: c["aggregation"] for c in load_sources()}
    for total in ("air_passengers", "air_departures", "air_freight_mtkm", "population"):
        assert rules[total] == "sum"
    assert rules["internet_users_pct"] == "pop_weighted"
    assert rules["gdp_per_capita_ppp"] == "pop_weighted"
    assert rules["gdp_growth_pct"] == "gdp_weighted"
    assert rules["inflation_cpi_pct"] == "median"


def test_every_aviation_column_carries_the_caveat():
    for c in load_sources():
        if c["column"].startswith("air_"):
            assert c.get("caveat") == "aviation", c["column"]


def test_units_appear_in_column_names_where_promised():
    names = {c["column"] for c in load_sources()}
    assert {"internet_users_pct", "co2_per_capita_t", "under5_deaths_per_1000"} <= names


def test_bloc_lists_match_the_checked_memberships():
    b = load_blocs()
    eco = set(b["ecowas"]["members"])
    assert len(eco) == 12 and "NGA" in eco
    assert not eco & {"BFA", "MLI", "NER", "MRT"}          # left ECOWAS
    assert len(b["african_union"]["members"]) == 55 and "ESH" in b["african_union"]["members"]
    assert len(b["eu"]["members"]) == 27 and "GBR" not in b["eu"]["members"]
    assert len(b["g20"]["members"]) == 19
    assert len(b["middle_east"]["members"]) == 16 and "CYP" not in b["middle_east"]["members"]


def test_ecowas_members_are_all_au_members():
    b = load_blocs()
    assert set(b["ecowas"]["members"]) <= set(b["african_union"]["members"])


def test_m49_reference_is_complete():
    m49 = pd.read_csv(config.REFERENCE_DIR / "un_m49.csv", keep_default_na=False)
    assert len(m49) == 248 and m49["iso3"].is_unique
    row = m49.set_index("iso3")
    assert row.loc["NGA", "subregion"] == "Western Africa"
    assert row.loc["EGY", "subregion"] == "Northern Africa"
    assert row.loc["LAO", "continent"] == "Asia"          # name with an apostrophe (was missed once)
    assert "TWN" not in row.index and "XKX" not in row.index


def test_bad_source_list_is_rejected(tmp_path):
    bad = tmp_path / "s.yaml"
    bad.write_text("columns:\n  - column: x\n    letter: M\n", encoding="utf-8")
    with pytest.raises(SourceListError, match="missing"):
        load_sources(bad)


def test_bloc_count_mismatch_is_rejected(tmp_path):
    bad = tmp_path / "blocs.yaml"
    bad.write_text("x:\n  column: is_x\n  as_of: 2026-01-01\n  count: 3\n  members: [NGA, GHA]\n",
                   encoding="utf-8")
    with pytest.raises(SourceListError, match="says 3 members"):
        load_blocs(bad)
```

### `tests/test_parse.py`

```python
"""Cleaning keeps real countries only, and records everything it removes."""
import pytest

from emole.data import fetch
from emole.data.parse import ParseError, parse_owid, parse_wb_countries, parse_wb_indicator

from .conftest import RAW


def test_owid_group_rows_are_removed_and_listed():
    rows, removed, _ = parse_owid(RAW / "owid_test-air__2026-01-01.csv", "air_passengers")
    assert set(rows["iso3"]) == {"NGA", "GHA", "XKX", "TWN"}
    gone = set(removed["entity"])
    assert {"Africa", "World", "High-income countries", "European Union (27)", "USSR"} <= gone
    assert "Kosovo" not in gone


def test_kosovo_gets_the_world_bank_code():
    rows, _, _ = parse_owid(RAW / "owid_test-air__2026-01-01.csv", "air_passengers")
    assert rows.loc[rows["entity"] == "Kosovo", "iso3"].tolist() == ["XKX"]


def test_empty_values_are_dropped():
    rows, _, _ = parse_owid(RAW / "owid_test-air__2026-01-01.csv", "air_passengers")
    assert not ((rows["iso3"] == "GHA") & (rows["year"] == 2023)).any()


def test_two_value_columns_need_value_column():
    path = RAW / "owid_test-multi__2026-01-01.csv"
    with pytest.raises(ParseError, match="value_column"):
        parse_owid(path, "x")
    rows, _, info = parse_owid(path, "x", value_column="value_b")
    assert rows["value"].tolist() == [2] and info["value_column"] == "value_b"


def test_world_bank_aggregates_are_removed_even_with_3_letter_codes():
    countries = parse_wb_countries(RAW / "wb_countries__2026-01-01.json")
    aggregates = set(countries.loc[countries["is_aggregate"], "iso3"])
    assert aggregates == {"WLD", "SSF"}
    rows, removed, info = parse_wb_indicator(RAW / "wb_SP.POP.TOTL__2026-01-01.json",
                                             "population", aggregates)
    assert set(rows["iso3"]) == {"NGA", "GHA", "XKX"}
    assert {"World", "Sub-Saharan Africa", "Not classified"} <= set(removed["entity"])
    assert info["lastupdated"] == "2026-07-14"


def test_world_bank_region_names_lose_trailing_spaces():
    countries = parse_wb_countries(RAW / "wb_countries__2026-01-01.json").set_index("iso3")
    assert countries.loc["NGA", "wb_region"] == "Sub-Saharan Africa"


def test_newest_saved_copy_is_used():
    assert fetch.latest_raw("owid_test-air", "csv", RAW).name == "owid_test-air__2026-01-01.csv"
    assert fetch.download_date(RAW / "owid_test-air__2026-01-01.csv") == "2026-01-01"


def test_offline_without_a_saved_copy_fails_clearly(tmp_path):
    with pytest.raises(fetch.DownloadError, match="offline"):
        fetch.fetch_owid("not-downloaded-yet", offline=True, raw_dir=tmp_path)
```

### `tests/test_build.py`

```python
"""The whole build on the fixtures: right rows, right values, groups filled, files written."""
import duckdb
import pandas as pd

from emole.data.build import read_snapshot, run

from .conftest import RAW, SOURCES

EXPECTED_ROWS = {("NGA", 2022), ("NGA", 2023), ("GHA", 2022), ("GHA", 2023),
                 ("XKX", 2022), ("XKX", 2023), ("TWN", 2023)}


def test_only_real_countries_survive(built):
    wide = built["wide"]
    assert set(wide["iso3"]) == {"NGA", "GHA", "XKX", "TWN"}
    assert not wide["iso3"].isin(["WLD", "SSF", "OWID_WRL", "OWID_USS"]).any()
    assert not wide["country"].isin(["World", "Africa", "Sub-Saharan Africa"]).any()


def test_join_keeps_every_country_year_exactly_once(built):
    wide = built["wide"]
    keys = set(zip(wide["iso3"], wide["year"], strict=True))
    assert keys == EXPECTED_ROWS
    assert not wide.duplicated(["iso3", "year"]).any()


def test_values_land_in_the_right_cells(built):
    w = built["wide"].set_index(["iso3", "year"])
    assert w.loc[("NGA", 2023), "air_passengers"] == 110
    assert w.loc[("NGA", 2023), "internet_users_pct"] == 45
    assert w.loc[("NGA", 2023), "population"] == 205_000_000
    assert w.loc[("XKX", 2022), "air_passengers"] == 10          # from OWID_KOS
    assert w.loc[("XKX", 2023), "population"] == 1_800_000       # from the World Bank, same row
    assert pd.isna(w.loc[("GHA", 2023), "air_passengers"])       # empty in the source
    assert w.loc[("GHA", 2023), "gdp_growth_pct"] == 5.0


def test_years_outside_the_range_are_dropped(built):
    assert built["wide"]["year"].min() >= 1970
    assert built["info"]["sources"]["air_passengers"]["rows_outside_years"] == 1


def test_names_and_column_order(built):
    wide = built["wide"]
    assert list(wide.columns[:3]) == ["country", "iso3", "year"]
    names = dict(zip(wide["iso3"], wide["country"], strict=True))
    assert names["NGA"] == "Nigeria" and names["XKX"] == "Kosovo" and names["TWN"] == "Taiwan"
    assert wide.columns.get_loc("population") > wide.columns.get_loc("is_middle_east")


def test_totals_are_stored_as_whole_numbers(built):
    wide = built["wide"]
    assert str(wide["air_passengers"].dtype) == "Int64"
    assert str(wide["population"].dtype) == "Int64"
    assert wide["internet_users_pct"].dtype == float


def test_grouping_columns_are_filled_or_listed(built):
    g = built["wide"].drop_duplicates("iso3").set_index("iso3")
    assert g.loc["NGA", "continent"] == "Africa" and g.loc["NGA", "subregion"] == "Western Africa"
    assert g.loc["NGA", "wb_region"] == "Sub-Saharan Africa"
    assert g.loc["NGA", "income_group"] == "lower-middle"
    assert bool(g.loc["NGA", "is_ecowas"]) and bool(g.loc["NGA", "is_african_union"])
    assert not bool(g.loc["NGA", "is_g20"])
    assert g.loc["XKX", "subregion"] == "Southern Europe"           # manual entry
    assert g.loc["TWN", "continent"] == "Asia"                      # manual entry
    assert "TWN" in built["unmatched"]["wb_region"]                  # listed, not hidden
    for col in ("continent", "subregion"):
        assert built["unmatched"][col] == []


def test_removed_rows_are_recorded(built):
    rem = built["removed"]
    assert {"Africa", "World", "Western Africa (WB)", "Sub-Saharan Africa"} <= set(rem["entity"])
    assert (rem["rows"] > 0).all()


def test_column_meta_measures_years(built):
    meta = built["meta"].set_index("column")
    assert meta.loc["air_passengers", "latest_year"] == 2023
    # 2023 has only 2 of the usual 3 countries (below 80%), so the broad year is 2022
    assert meta.loc["air_passengers", "latest_broad_year"] == 2022
    assert meta.loc["internet_users_pct", "latest_broad_year"] == 2023
    assert meta.loc["gdp_growth_pct", "aggregation"] == "gdp_weighted"
    assert meta.loc["population", "source_url"].endswith("SP.POP.TOTL")


def test_database_is_written_and_readable(built):
    db = built["out"] / "emole.duckdb"
    con = duckdb.connect(str(db), read_only=True)
    try:
        tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        assert {"country_year", "column_meta", "build_info"} <= tables
        n = con.execute("SELECT COUNT(*) FROM country_year").fetchone()[0]
        version = con.execute("SELECT value FROM build_info WHERE key = 'build_version'").fetchone()[0]
    finally:
        con.close()
    assert n == len(EXPECTED_ROWS) and version == "1"


def test_snapshot_rebuild_gives_the_same_table(built, tmp_path):
    out = built["out"] / "processed"
    wide, meta, info = read_snapshot(out)
    pd.testing.assert_frame_equal(wide, built["wide"], check_dtype=False)
    again = run(from_snapshot=True, out_dir=out, db_path=tmp_path / "again.duckdb")
    assert len(again["wide"]) == len(built["wide"])


def test_build_is_repeatable(built, tmp_path):
    second = run(offline=True, sources_file=SOURCES, raw_dir=RAW, out_dir=tmp_path / "p",
                 db_path=tmp_path / "e.duckdb", year_min=1970, year_max=2026)
    pd.testing.assert_frame_equal(second["wide"], built["wide"])
```

### `tests/test_groupmath.py`

```python
"""Group maths: sums, weighted averages, medians and coverage, checked by hand,
and the SQL version must give exactly the same numbers as the Python version."""
import duckdb
import pytest

from emole.groupmath import group_value, sql_coverage, sql_expression

ECOWAS_PAIR = ["NGA", "GHA"]


def test_sum_with_coverage(built):
    r = group_value(built["wide"], "air_passengers", "sum", 2023, ECOWAS_PAIR)
    assert r.value == 110                       # Ghana has no 2023 value
    assert (r.n_with_data, r.n_members, r.missing) == (1, 2, ["GHA"])
    assert r.note("ECOWAS") == "Based on 1 of 2 ECOWAS countries with data for 2023."


def test_population_weighted_average(built):
    r = group_value(built["wide"], "internet_users_pct", "pop_weighted", 2023, ECOWAS_PAIR)
    # (45 x 205m + 65 x 31m) / (205m + 31m)
    assert r.value == pytest.approx((45 * 205 + 65 * 31) / 236)
    assert r.value != pytest.approx((45 + 65) / 2)    # NOT the plain average


def test_gdp_weighted_average(built):
    r = group_value(built["wide"], "gdp_growth_pct", "gdp_weighted", 2023, ECOWAS_PAIR)
    w_ng, w_gh = 6000 * 205e6, 7000 * 31e6
    assert r.value == pytest.approx((3.0 * w_ng + 5.0 * w_gh) / (w_ng + w_gh))


def test_median(built):
    r = group_value(built["wide"], "gdp_growth_pct", "median", 2023, ECOWAS_PAIR)
    assert r.value == 4.0


def test_country_without_a_weight_is_left_out_and_counted(built):
    # Taiwan has an internet value but no population figure: it cannot be weighted.
    r = group_value(built["wide"], "internet_users_pct", "pop_weighted", 2023)
    assert r.n_members == 4 and r.n_with_data == 3 and r.missing == ["TWN"]
    assert r.value == pytest.approx((45 * 205 + 65 * 31 + 80 * 1.8) / (205 + 31 + 1.8))
    assert "total of countries with data" in r.note(world=True)


def test_no_data_gives_none(built):
    r = group_value(built["wide"], "air_passengers", "sum", 1999, ECOWAS_PAIR)
    assert r.value is None and r.n_with_data == 0


def test_unknown_rule_is_rejected(built):
    with pytest.raises(ValueError):
        group_value(built["wide"], "population", "average", 2023)


@pytest.mark.parametrize("column,rule", [
    ("air_passengers", "sum"),
    ("internet_users_pct", "pop_weighted"),
    ("gdp_growth_pct", "gdp_weighted"),
    ("gdp_growth_pct", "median"),
])
def test_sql_gives_the_same_number_as_python(built, column, rule):
    con = duckdb.connect()
    con.register("country_year", built["wide"])
    sql = (f"SELECT {sql_expression(column, rule)} AS v, {sql_coverage(column, rule)} AS n "
           "FROM country_year WHERE year = 2023 AND iso3 IN ('NGA', 'GHA')")
    v, n = con.execute(sql).fetchone()
    py = group_value(built["wide"], column, rule, 2023, ECOWAS_PAIR)
    assert float(v) == pytest.approx(py.value) and n == py.n_with_data
```

### `tests/test_secrets.py`

```python
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


IGNORED = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".ruff_cache", "raw"}


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
```

### `tests/test_coverage.py`

```python
"""The coverage report runs on a built database and writes every section."""
from emole.data.coverage import report


def test_report_has_every_section(built, tmp_path):
    out = tmp_path / "coverage_report.md"
    text = report(db_path=built["out"] / "emole.duckdb", out=out,
                  removed_csv=built["out"] / "processed" / "removed_rows.csv")
    assert out.exists()
    for heading in ("## 1. Columns", "## 2. Flags", "## 3. Nigeria and peers",
                    "## 4. Regions, income groups and blocs", "## 5. Rows removed"):
        assert heading in text
    assert "Nigeria (NGA)" in text
    assert "is_ecowas" in text
    assert "\u2014" not in text                  # no em dashes anywhere (owner's rule)
```

### `tests/fixtures/README.md`

```markdown
# Test fixtures (test-only values)

These tiny files copy the exact SHAPE of the real downloads (Our World in Data chart
CSVs and World Bank API JSON), so the build can be tested without internet, in CI.

**The numbers in them are made up for the tests and are never used by Emolé.** Emolé's
real data comes only from the downloads described in `docs/DATA.md`. The values are
round on purpose (Nigeria population 205,000,000; internet 45%) so the expected answers
in the tests can be checked by hand.

What each file exercises:

| File | What it tests |
|---|---|
| `owid_test-air__2026-01-01.csv` | group rows with a blank code (Africa), `OWID_` codes (World, USSR), Kosovo renamed from `OWID_KOS` to `XKX`, a year before 1970, an empty value, Taiwan |
| `owid_test-air__2025-06-01.csv` | an OLDER copy of the same chart: the build must use the newest file |
| `owid_test-internet__2026-01-01.csv` | a rate column (population-weighted) |
| `owid_test-gdp__2026-01-01.csv` | GDP per person (the weight for GDP growth) |
| `owid_test-multi__2026-01-01.csv` | a file with two value columns (must ask for `value_column`) |
| `wb_SP.POP.TOTL__2026-01-01.json` | World Bank aggregates WLD and SSF that use 3-letter codes, a blank code, an empty value |
| `wb_NY.GDP.MKTP.KD.ZG__2026-01-01.json` | a GDP-weighted column |
| `wb_countries__2026-01-01.json` | region names with trailing spaces, "Not classified" income, aggregates |
| `../sources_test.yaml` | a five-column version of `data/sources.yaml` pointing at these files |
```

### `tests/fixtures/sources_test.yaml`

```yaml
# A small sources list for the tests. Same format as data/sources.yaml.
version: 1
columns:
  - column: air_passengers
    letter: M
    description: test air passengers
    unit: passengers
    aggregation: sum
    weight_note: total
    source: owid
    slug: test-air
    producer: test fixture
    licence: test only
    caveat: aviation
  - column: internet_users_pct
    letter: M
    description: test internet share
    unit: "% of population"
    aggregation: pop_weighted
    weight_note: exact
    source: owid
    slug: test-internet
    producer: test fixture
    licence: test only
  - column: gdp_per_capita_ppp
    letter: O
    description: test GDP per person
    unit: international-$
    aggregation: pop_weighted
    weight_note: exact
    source: owid
    slug: test-gdp
    producer: test fixture
    licence: test only
  - column: gdp_growth_pct
    letter: O
    description: test GDP growth
    unit: "% per year"
    aggregation: gdp_weighted
    weight_note: gdp weights
    source: worldbank
    code: NY.GDP.MKTP.KD.ZG
    producer: test fixture
    licence: test only
  - column: population
    letter: L
    description: test population
    unit: people
    aggregation: sum
    weight_note: total
    source: worldbank
    code: SP.POP.TOTL
    producer: test fixture
    licence: test only
```

### `tests/fixtures/raw/owid_test-air__2025-06-01.csv`

```text
Entity,Code,Year,is_air_psgr
Nigeria,NGA,2022,1
```

### `tests/fixtures/raw/owid_test-air__2026-01-01.csv`

```text
Entity,Code,Year,is_air_psgr
Africa,,2022,1000
World,OWID_WRL,2022,5000
High-income countries,,2022,3000
European Union (27),,2023,4000
Kosovo,OWID_KOS,2022,10
USSR,OWID_USS,1980,999
Nigeria,NGA,1969,1
Nigeria,NGA,2022,100
Nigeria,NGA,2023,110
Ghana,GHA,2022,50
Ghana,GHA,2023,
Taiwan,TWN,2023,70
```

### `tests/fixtures/raw/owid_test-gdp__2026-01-01.csv`

```text
Entity,Code,Year,ny_gdp_pcap_pp_kd
World,OWID_WRL,2023,20000
Nigeria,NGA,2023,6000
Ghana,GHA,2023,7000
Kosovo,OWID_KOS,2023,14000
```

### `tests/fixtures/raw/owid_test-internet__2026-01-01.csv`

```text
Entity,Code,Year,it_net_user_zs
Western Africa (WB),,2023,30
Lower-middle-income countries,,2023,40
Nigeria,NGA,2022,40
Nigeria,NGA,2023,45
Ghana,GHA,2022,60
Ghana,GHA,2023,65
Kosovo,OWID_KOS,2023,80
Taiwan,TWN,2023,90
```

### `tests/fixtures/raw/owid_test-multi__2026-01-01.csv`

```text
Entity,Code,Year,value_a,value_b
Nigeria,NGA,2023,1,2
```

### `tests/fixtures/raw/wb_NY.GDP.MKTP.KD.ZG__2026-01-01.json`

```json
{"meta": {"page": 1, "pages": 1, "per_page": 20000, "total": 3, "lastupdated": "2026-07-14"}, "records": [{"indicator": {"id": "NY.GDP.MKTP.KD.ZG", "value": "NY.GDP.MKTP.KD.ZG"}, "country": {"id": "NG", "value": "Nigeria"}, "countryiso3code": "NGA", "date": "2023", "value": 3.0, "unit": "", "obs_status": "", "decimal": 0}, {"indicator": {"id": "NY.GDP.MKTP.KD.ZG", "value": "NY.GDP.MKTP.KD.ZG"}, "country": {"id": "GH", "value": "Ghana"}, "countryiso3code": "GHA", "date": "2023", "value": 5.0, "unit": "", "obs_status": "", "decimal": 0}, {"indicator": {"id": "NY.GDP.MKTP.KD.ZG", "value": "NY.GDP.MKTP.KD.ZG"}, "country": {"id": "1W", "value": "World"}, "countryiso3code": "WLD", "date": "2023", "value": 2.7, "unit": "", "obs_status": "", "decimal": 0}]}
```

### `tests/fixtures/raw/wb_SP.POP.TOTL__2026-01-01.json`

```json
{"meta": {"page": 1, "pages": 1, "per_page": 20000, "total": 9, "lastupdated": "2026-07-14"}, "records": [{"indicator": {"id": "SP.POP.TOTL", "value": "SP.POP.TOTL"}, "country": {"id": "NG", "value": "Nigeria"}, "countryiso3code": "NGA", "date": "2022", "value": 200000000, "unit": "", "obs_status": "", "decimal": 0}, {"indicator": {"id": "SP.POP.TOTL", "value": "SP.POP.TOTL"}, "country": {"id": "NG", "value": "Nigeria"}, "countryiso3code": "NGA", "date": "2023", "value": 205000000, "unit": "", "obs_status": "", "decimal": 0}, {"indicator": {"id": "SP.POP.TOTL", "value": "SP.POP.TOTL"}, "country": {"id": "GH", "value": "Ghana"}, "countryiso3code": "GHA", "date": "2022", "value": 30000000, "unit": "", "obs_status": "", "decimal": 0}, {"indicator": {"id": "SP.POP.TOTL", "value": "SP.POP.TOTL"}, "country": {"id": "GH", "value": "Ghana"}, "countryiso3code": "GHA", "date": "2023", "value": 31000000, "unit": "", "obs_status": "", "decimal": 0}, {"indicator": {"id": "SP.POP.TOTL", "value": "SP.POP.TOTL"}, "country": {"id": "XK", "value": "Kosovo"}, "countryiso3code": "XKX", "date": "2023", "value": 1800000, "unit": "", "obs_status": "", "decimal": 0}, {"indicator": {"id": "SP.POP.TOTL", "value": "SP.POP.TOTL"}, "country": {"id": "1W", "value": "World"}, "countryiso3code": "WLD", "date": "2023", "value": 8000000000, "unit": "", "obs_status": "", "decimal": 0}, {"indicator": {"id": "SP.POP.TOTL", "value": "SP.POP.TOTL"}, "country": {"id": "ZG", "value": "Sub-Saharan Africa"}, "countryiso3code": "SSF", "date": "2023", "value": 1200000000, "unit": "", "obs_status": "", "decimal": 0}, {"indicator": {"id": "SP.POP.TOTL", "value": "SP.POP.TOTL"}, "country": {"id": "XY", "value": "Not classified"}, "countryiso3code": "", "date": "2023", "value": 5, "unit": "", "obs_status": "", "decimal": 0}, {"indicator": {"id": "SP.POP.TOTL", "value": "SP.POP.TOTL"}, "country": {"id": "NG", "value": "Nigeria"}, "countryiso3code": "NGA", "date": "2024", "value": null, "unit": "", "obs_status": "", "decimal": 0}]}
```

### `tests/fixtures/raw/wb_countries__2026-01-01.json`

```json
{"meta": {"page": 1, "pages": 1}, "records": [{"id": "NGA", "iso2Code": "NG", "name": "Nigeria", "region": {"id": "X", "iso2code": "X", "value": "Sub-Saharan Africa "}, "incomeLevel": {"id": "X", "iso2code": "X", "value": "Lower middle income"}}, {"id": "GHA", "iso2Code": "GH", "name": "Ghana", "region": {"id": "X", "iso2code": "X", "value": "Sub-Saharan Africa "}, "incomeLevel": {"id": "X", "iso2code": "X", "value": "Lower middle income"}}, {"id": "XKX", "iso2Code": "XK", "name": "Kosovo", "region": {"id": "X", "iso2code": "X", "value": "Europe & Central Asia"}, "incomeLevel": {"id": "X", "iso2code": "X", "value": "Upper middle income"}}, {"id": "VEN", "iso2Code": "VE", "name": "Venezuela, RB", "region": {"id": "X", "iso2code": "X", "value": "Latin America & Caribbean "}, "incomeLevel": {"id": "X", "iso2code": "X", "value": "Not classified"}}, {"id": "WLD", "iso2Code": "WL", "name": "World", "region": {"id": "X", "iso2code": "X", "value": "Aggregates"}, "incomeLevel": {"id": "X", "iso2code": "X", "value": "Aggregates"}}, {"id": "SSF", "iso2Code": "SS", "name": "Sub-Saharan Africa", "region": {"id": "X", "iso2code": "X", "value": "Aggregates"}, "incomeLevel": {"id": "X", "iso2code": "X", "value": "Aggregates"}}]}
```

### `docs/DATA.md`

```markdown
# Emolé data dictionary

Everything Emolé knows lives in ONE table, `country_year`, in `data/emole.duckdb`.
This file explains every column in plain words: what it means, its unit, where it
comes from, its licence, its years and its quirks. It also explains the regions, the
blocs, the group maths and what was left out.

**Sources checked by hand:** 8 November 2026. **Built by:** `python scripts/build_data.py`
(BUILD_VERSION 1). The years below marked "as checked" are what each source page showed
on that date. The build measures the real years every time and stores them in the
`column_meta` table and in `docs/coverage_report.md`; those measured years win.

---

## 1. The table at a glance

One row = one country (or territory) in one year. Every column describes the same
country in the same year, so all the industries sit side by side and cross-industry
questions need no joins.

| Kind | Columns |
|---|---|
| Identity | `country` (name), `iso3` (ISO 3-letter code), `year` |
| Groupings | `continent`, `subregion`, `wb_region`, `income_group`, `is_ecowas`, `is_african_union`, `is_eu`, `is_g20`, `is_middle_east` |
| **M**ovement | `air_passengers`, `air_departures`, `air_freight_mtkm`, `internet_users_pct`, `mobile_subs_per_100` |
| **O**utput | `gdp_per_capita_ppp`, `gdp_growth_pct`, `inflation_cpi_pct`, `unemployment_pct` |
| **L**ife | `life_expectancy_years`, `under5_deaths_per_1000`, `health_spend_per_capita_ppp`, `population`, `urban_pop_pct` |
| **E**nergy | `electricity_access_pct`, `renewables_share_elec_pct`, `co2_per_capita_t` |

Years kept: **1970 to the current year** (decision E-43). 1970 is where the aviation
series start; earlier years would add rows where most columns are empty. Nothing after
the current year is kept, so no projection can slip in.

Two code-only tables sit next to it (the model never queries them; the code reads them):

- `column_meta`: one row per column with its description, unit, group rule, source,
  licence, first year, latest year and latest year with broad coverage.
- `build_info`: when and how the database was built (BUILD_VERSION, versions, dates).

## 2. Two rules every answer must follow

**Rule 1: each column ends in a different year.** Air data ends in 2023 while internet
and inflation run to 2025. "Latest" always means the latest year of the column being
asked about. If someone asks for air passengers in 2025, Emolé says the latest is 2023.

`column_meta` holds two "latest" years per column:

- `latest_year`: the newest year with ANY data.
- `latest_broad_year`: the newest year in which at least 80% of the column's usual
  countries report (its best year in the last ten). Example: Ember's 2025 electricity
  data covers 91 countries, far fewer than earlier years, so for rankings and region
  answers the fair "latest" is 2024. Recommendation for Step 2: rankings and group
  answers use `latest_broad_year`; a single country's "latest" is that country's own
  newest year with a value.

**Rule 2: groupings are current.** Income groups and bloc memberships are TODAY's,
applied to every year (decision E-40, E-41). "ECOWAS in 2010" means today's 12 members.
Emolé must say "current members" or "current income group" in such answers.

---

## 3. The 17 columns

Licence short names: **CC BY 4.0** = Creative Commons Attribution 4.0 (free to use,
share and adapt, including commercially, with credit). **CC BY 3.0 IGO** = the same idea
for intergovernmental organisations. "via World Bank" = published in the World Bank's
World Development Indicators (WDI); "OWID" = Our World in Data, which republishes the
data in one clean file shape.

### M: Movement

#### `air_passengers`
- **Meaning:** passengers carried by airlines **registered in the country**, on domestic and international flights.
- **Unit:** passengers. **Group rule:** sum.
- **Source:** OWID chart [`air-passengers-carried`](https://ourworldindata.org/grapher/air-passengers-carried) (World Bank code IS.AIR.PSGR). **Producer:** International Civil Aviation Organization (ICAO), via World Bank. **Licence:** CC BY 4.0.
- **Years (as checked):** 1970 to 2023. Next OWID update expected January 2027.
- **Quirks:**
  - **Registered airlines, not airports (decision E-09).** Nigeria's figure counts Nigerian airlines only, not foreign airlines flying into Lagos. Every answer that uses an aviation column must say so (code adds the note, not the model).
  - In a country with one or two airlines, one airline starting or stopping can swing the figure sharply.
  - ICAO estimates the traffic of carriers that do not report.
  - 2020 and 2021 show the COVID-19 collapse in travel.

#### `air_departures`
- **Meaning:** take-offs by airlines registered in the country, at home and abroad.
- **Unit:** departures. **Group rule:** sum.
- **Source:** World Bank indicator [IS.AIR.DPRT](https://data.worldbank.org/indicator/IS.AIR.DPRT). **Producer:** ICAO, via World Bank. **Licence:** CC BY 4.0.
- **Why the World Bank:** OWID has no chart for this series (decision E-03).
- **Years (as checked):** 1970 to 2023.
- **Quirks:** same registered-airlines caveat as above.

#### `air_freight_mtkm`
- **Meaning:** freight (including express and diplomatic bags, not passenger baggage) carried by airlines registered in the country, in million tonne-kilometres. One tonne flown one kilometre is one tonne-kilometre.
- **Unit:** million tonne-km. **Group rule:** sum.
- **Source:** OWID chart [`air-transport-freight-ton-km`](https://ourworldindata.org/grapher/air-transport-freight-ton-km) (IS.AIR.GOOD.MT.K1). **Producer:** ICAO, via World Bank. **Licence:** CC BY 4.0.
- **Years (as checked):** 1970 to 2023.
- **Quirks:** registered-airlines caveat. The figure grows with distance, so a country whose airlines fly long routes shows more tonne-km for the same cargo weight.

#### `internet_users_pct`
- **Meaning:** share of the population who used the internet (from any device or place) in the last three months.
- **Unit:** % of population. **Group rule:** population-weighted average (exact).
- **Source:** OWID chart [`share-of-individuals-using-the-internet`](https://ourworldindata.org/grapher/share-of-individuals-using-the-internet) (IT.NET.USER.ZS). **Producer:** International Telecommunication Union (ITU), via World Bank. **Licence:** CC BY 4.0.
- **Years (as checked):** 1990 to 2025.
- **Quirks:** many countries' values are ITU estimates rather than household survey results.

#### `mobile_subs_per_100`
- **Meaning:** mobile phone subscriptions per 100 people.
- **Unit:** subscriptions per 100 people. **Group rule:** population-weighted average (exact).
- **Source:** OWID chart [`mobile-cellular-subscriptions-per-100-people`](https://ourworldindata.org/grapher/mobile-cellular-subscriptions-per-100-people) (IT.CEL.SETS.P2). **Producer:** ITU, via World Bank. **Licence:** CC BY 4.0.
- **Years (as checked):** 1960 to 2025 (kept from 1970).
- **Quirks:** it can pass 100, because many people hold more than one SIM. It counts subscriptions, not people.

### O: Output

#### `gdp_per_capita_ppp`
- **Meaning:** average economic output per person, adjusted for inflation and for differences in living costs between countries.
- **Unit:** international-$ at 2021 prices (PPP). **Group rule:** population-weighted average (exact: it gives the group's GDP divided by its people).
- **Source:** OWID chart [`gdp-per-capita-worldbank`](https://ourworldindata.org/grapher/gdp-per-capita-worldbank) (NY.GDP.PCAP.PP.KD). **Producer:** World Bank (International Comparison Program), Eurostat, OECD, IMF. **Licence:** CC BY 4.0.
- **Why this measure (decision E-35):** PPP in constant international dollars is the fairest way to compare living standards across countries and across years. Market-exchange-rate dollars swing with currency moves (a naira devaluation would look like a collapse in output).
- **Years (as checked):** 1990 to 2024. It starts in 1990, so earlier years are empty.

#### `gdp_growth_pct`
- **Meaning:** yearly growth of the economy, after removing inflation (real GDP growth, constant local prices).
- **Unit:** % per year. **Group rule:** **GDP-weighted** average (decision E-44): bigger economies count more, using GDP (PPP) = `gdp_per_capita_ppp` x `population` as the weight. The World Bank builds its regional growth rates as GDP-weighted averages too. A population weight would let a large but poorer economy swamp a region's growth rate.
- **Source:** World Bank indicator [NY.GDP.MKTP.KD.ZG](https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG). **Producer:** World Bank and OECD national accounts data. **Licence:** CC BY 4.0.
- **Why the World Bank (decision E-37):** OWID's own GDP growth chart comes from the UN SDG database and covers only 2000 to 2023.
- **Years (as checked):** 1961 to 2024 (February 2026 edition).
- **Quirks:** when a country re-bases its national accounts (updates the base year), its growth series can show a break.

#### `inflation_cpi_pct`
- **Meaning:** yearly change in consumer prices (CPI inflation).
- **Unit:** % per year. **Group rule:** **median** (decision E-44): the middle country's value. The World Bank uses the median for this indicator too, because one hyperinflation (hundreds or thousands of percent in a year) would swamp any average.
- **Source:** OWID chart [`inflation-of-consumer-prices`](https://ourworldindata.org/grapher/inflation-of-consumer-prices) (FP.CPI.TOTL.ZG). **Producer:** IMF International Financial Statistics, via World Bank. **Licence:** CC BY 4.0.
- **Years (as checked):** 1960 to 2025 (kept from 1970).

#### `unemployment_pct`
- **Meaning:** share of the labour force without work but available and looking for work.
- **Unit:** % of labour force. **Group rule:** population-weighted average (approximate: the true weight is the labour force, which this table does not hold).
- **Source:** OWID chart [`unemployment-rate`](https://ourworldindata.org/grapher/unemployment-rate) (SL.UEM.TOTL.ZS). **Producer:** International Labour Organization (ILO) modelled estimates, via World Bank. **Licence:** CC BY 4.0.
- **Years (as checked):** 1991 to 2025.
- **Quirks:** these are ILO **modelled** estimates, harmonised across countries; they can differ from a country's own national statistics office figure. Where a country has little survey data, the value is imputed by the ILO's model.

### L: Life

#### `life_expectancy_years`
- **Meaning:** period life expectancy at birth: how long a baby born that year would live if that year's death rates stayed the same all its life.
- **Unit:** years. **Group rule:** population-weighted average (approximate but standard).
- **Source:** OWID chart [`life-expectancy`](https://ourworldindata.org/grapher/life-expectancy). **Producer:** from 1950 onwards (all the years Emolé keeps), the UN World Population Prospects 2024. **Licence:** CC BY 3.0 IGO (UN WPP); OWID's processing CC BY 4.0.
- **Years (as checked):** to 2023 (OWID's next update was expected in October 2026).
- **Quirks:** crisis years (wars, epidemics) show sharp one-year dips, because the UN counts crisis deaths in the year they happened.

#### `under5_deaths_per_1000`
- **Meaning:** deaths before age five per 1,000 live births (the under-five mortality rate).
- **Unit:** deaths per 1,000 live births. **Group rule:** population-weighted average (approximate: the true weight is births).
- **Source:** World Bank indicator [SH.DYN.MORT](https://data.worldbank.org/indicator/SH.DYN.MORT). **Producer:** UN Inter-agency Group for Child Mortality Estimation (UNICEF, WHO, World Bank, UN DESA), via World Bank. **Licence:** CC BY 4.0.
- **Why the World Bank (decision E-37):** OWID's child mortality charts show a share in % and list the UN IGME source under a UNICEF copyright notice. The World Bank publishes the same estimates in the unit Emolé needs, under CC BY 4.0.
- **Years (as checked):** 1960 to 2024 (kept from 1970).

#### `health_spend_per_capita_ppp`
- **Meaning:** current spending on health per person, public and private together.
- **Unit:** current international-$ (PPP). **Group rule:** population-weighted average (exact).
- **Source:** OWID chart [`annual-healthcare-expenditure-per-capita`](https://ourworldindata.org/grapher/annual-healthcare-expenditure-per-capita) (SH.XPD.CHEX.PP.CD). **Producer:** WHO Global Health Expenditure Database, via World Bank. **Licence:** CC BY 4.0 (as listed by the World Bank).
- **Years (as checked):** 2000 to 2024.
- **Quirks:** **current** prices, NOT adjusted for inflation. Comparing countries in the same year is fair; comparing one country across years overstates growth. Emolé should say "in current international dollars" when comparing years.

#### `population`
- **Meaning:** people living in the country (mid-year estimate, all residents).
- **Unit:** people. **Group rule:** sum. It is also the weight for every population-weighted average.
- **Source:** World Bank indicator [SP.POP.TOTL](https://data.worldbank.org/indicator/SP.POP.TOTL). **Producer:** World Bank estimates based on UN World Population Prospects and national sources. **Licence:** CC BY 4.0.
- **Why the World Bank (decision E-37):** OWID's long-run population series switches to UN projections after 2023. The weights for 2024 and 2025 group averages must be estimates, not projections, and the World Bank's series gives estimates up to 2025.
- **Years (as checked):** 1960 to 2025 (July 2026 edition; kept from 1970).
- **Quirks:** the World Bank does not publish Taiwan, so Taiwan has no population here and is left out of population-weighted averages (the coverage note shows it as missing).

#### `urban_pop_pct`
- **Meaning:** share of people living in urban areas, as each country defines "urban".
- **Unit:** % of population. **Group rule:** population-weighted average (exact).
- **Source:** OWID chart [`share-of-population-urban`](https://ourworldindata.org/grapher/share-of-population-urban) (SP.URB.TOTL.IN.ZS). **Producer:** UN World Urbanization Prospects, via World Bank. **Licence:** CC BY 4.0.
- **Years (as checked):** 1960 to 2024 (kept from 1970).
- **Quirks:** countries define "urban" differently, so comparisons between countries are rough.

### E: Energy

#### `electricity_access_pct`
- **Meaning:** share of the population with access to electricity.
- **Unit:** % of population. **Group rule:** population-weighted average (exact).
- **Source:** OWID chart [`share-of-the-population-with-access-to-electricity`](https://ourworldindata.org/grapher/share-of-the-population-with-access-to-electricity) (EG.ELC.ACCS.ZS). **Producer:** World Bank. **Licence:** CC BY 4.0.
- **Years (as checked):** 1990 to 2024 (newest edition seen).
- **Quirks:** "access" is a low bar (enough for basic lighting and charging a phone); it does not mean reliable 24-hour power. Countries the UN classes as developed are assumed to have universal access.

#### `renewables_share_elec_pct`
- **Meaning:** share of the country's **electricity** generated from renewables: hydropower, solar, wind, bioenergy, geothermal, wave and tidal.
- **Unit:** % of electricity generation. **Group rule:** population-weighted average (approximate: the true weight is electricity generation).
- **Source:** OWID chart [`share-electricity-renewables`](https://ourworldindata.org/grapher/share-electricity-renewables). **Producer:** Ember (from 2000) and the Energy Institute Statistical Review of World Energy (earlier years). **Licence:** Ember data CC BY 4.0; Energy Institute data free to use with attribution.
- **Why electricity, not all energy (decision E-36):** Ember reports electricity for over 200 countries up to 2025, which covers Nigeria and every peer. It also matches what people usually mean by "renewable power".
- **Years (as checked):** 1985 to 2025.
- **Quirks:** in Ember's 2025 data only 91 countries had their full-year figure, so 2025 is thin; the broad-coverage year is likely 2024. Large hydropower makes some poorer countries score very high. It says nothing about cooking fuel or transport.

#### `co2_per_capita_t`
- **Meaning:** carbon dioxide from burning fossil fuels and from industry (cement and so on), per person. Land-use change (for example deforestation) is NOT included.
- **Unit:** tonnes per person. **Group rule:** population-weighted average (exact).
- **Source:** OWID chart [`co-emissions-per-capita`](https://ourworldindata.org/grapher/co-emissions-per-capita). **Producer:** Global Carbon Project (Global Carbon Budget); per-person figures use OWID's population. **Licence:** CC BY 4.0.
- **Years (as checked):** 1750 to 2024 (kept from 1970); next update expected November 2026.
- **Quirks:** production-based (emissions inside the country), not consumption-based. Small oil and gas producers show very high values.

---

## 4. Groupings

### 4.1 `continent` and `subregion`: UN M49
- **Source:** the UN Statistics Division's M49 standard, [unstats.un.org/unsd/methodology/m49](https://unstats.un.org/unsd/methodology/m49/). UNSD offers no stable download link (its buttons are made by JavaScript), so the list was taken from the open-source package [`un-m49`](https://github.com/wooorm/un-m49) version 2.2.0 (MIT licence), which holds the same standard. File fingerprint (sha256, first 16 characters): `14faf74380d185db`. Converted by `scripts/make_m49_reference.py` into the committed file `data/reference/un_m49.csv` (248 countries and areas).
- `continent` = the M49 region: Africa, Americas, Asia, Europe, Oceania.
- `subregion` = the most specific M49 level: the intermediate region where M49 has one (Nigeria: Western Africa; Brazil: South America), otherwise the M49 subregion (Egypt: Northern Africa; Saudi Arabia: Western Asia).
- **Added by hand** (`data/reference/manual_regions.csv`), because M49 does not list them: Taiwan (Asia, Eastern Asia) and Kosovo (Europe, Southern Europe).
- Note: in M49, Sudan sits in Northern Africa, and Cyprus and Turkiye in Western Asia (Asia).

### 4.2 `wb_region` and `income_group`: World Bank
- **Source:** the World Bank country list (`api.worldbank.org/v2/country`), downloaded at build time. Licence CC BY 4.0.
- `income_group` values: `low`, `lower-middle`, `upper-middle`, `high`. Empty where the World Bank does not classify a country.
- **Which classification:** the CURRENT one, **FY2027, effective 1 July 2026**, based on 2025 income (Atlas method). Thresholds: low income up to $1,175; lower-middle $1,176 to $4,635; upper-middle $4,636 to $14,375; high above $14,375. In this update Jordan, Micronesia, the Philippines, Sri Lanka and Viet Nam moved up to upper-middle income and Togo moved up to lower-middle; no country moved down. Ethiopia (unclassified the year before) was classified low income and Venezuela lower-middle income.
- **Applied to every year** (rule 2 above). Income groups change over time, so Emolé says "current income group".

### 4.3 Bloc columns (true/false)
All lists live in `data/reference/blocs.yaml`, with their "as of" date (8 November 2026) and sources. The build stops if a list's member count does not match.

| Column | Members | Notes |
|---|---|---|
| `is_ecowas` | 12 | Benin, Cabo Verde, Cote d'Ivoire, The Gambia, Ghana, Guinea, Guinea-Bissau, Liberia, Nigeria, Senegal, Sierra Leone, Togo. **Burkina Faso, Mali and Niger are NOT counted:** they announced their exit in January 2024 and ECOWAS confirmed it took effect on 29 January 2025. Mauritania left in 2000. |
| `is_african_union` | 55 | Every widely recognised African country plus the Sahrawi Arab Democratic Republic (Western Sahara). Suspended members are still members. |
| `is_eu` | 27 | No new member since Croatia in 2013; the UK left in 2020. Montenegro is expected next; the European Commission has pointed to an accession treaty in 2027 and membership around 2028. |
| `is_g20` | 19 | The 19 country members. The G20 also has two union members, the EU and the African Union; they are not countries, so use `is_eu` and `is_african_union` for them. |
| `is_middle_east` | 16 | Emolé's own list, below. |

### 4.4 Emolé's Middle East (decision E-07, E-42)
No single official list exists. Emolé uses the common core found in most news and reference works:

**Bahrain, Egypt, Iran, Iraq, Israel, Jordan, Kuwait, Lebanon, Oman, Palestine, Qatar, Saudi Arabia, Syria, Turkiye, United Arab Emirates, Yemen** (16).

Left out on purpose: Cyprus (an EU member, usually grouped with Europe); Armenia, Azerbaijan and Georgia (in the UN's "Western Asia" but usually called the South Caucasus); and the Maghreb (Morocco, Algeria, Tunisia, Libya), which belong to "Middle East and North Africa" but not the Middle East itself. When asked, Emolé says which definition she used and can offer the UN one (`subregion = 'Western Asia'`) or the World Bank region instead.

### 4.5 Countries and territories
Rows are kept for every code that is a real country or territory, the way the World Bank does (Hong Kong, Puerto Rico, Greenland and so on are rows). Territories have fewer columns filled. A ranking of "countries" may therefore include a territory; Step 2 decides whether rankings should skip rows with no `income_group` or similar.

---

## 5. Group maths (decision E-06, E-44)

Emolé never lets the model invent group maths. A group figure (region, bloc, income group, "the world") is always made from its member countries by the rule in `column_meta.aggregation`. The helper `src/emole/groupmath.py` does it in Python and gives the SAME maths as SQL (`sql_expression`), and the tests prove both give the same number.

| Rule | Maths | Columns |
|---|---|---|
| `sum` | add the countries up | air_passengers, air_departures, air_freight_mtkm, population |
| `pop_weighted` | sum(value x population) / sum(population), over countries that have BOTH | internet_users_pct, mobile_subs_per_100, gdp_per_capita_ppp, unemployment_pct, life_expectancy_years, under5_deaths_per_1000, health_spend_per_capita_ppp, urban_pop_pct, electricity_access_pct, renewables_share_elec_pct, co2_per_capita_t |
| `gdp_weighted` | sum(value x GDP) / sum(GDP), with GDP = gdp_per_capita_ppp x population | gdp_growth_pct |
| `median` | the middle country's value | inflation_cpi_pct |

Why weights matter, in one example: with a plain average, Cape Verde (about half a million people) would count as much as Nigeria (over 200 million).

Where population weighting is only approximate (written in `column_meta.weight_note`): unemployment (true weight: labour force), under-five deaths (true weight: births), renewables share (true weight: electricity generated), life expectancy (true figure needs life tables).

**Every group answer reports its coverage**, made by code: "Based on 11 of 12 ECOWAS countries with data for 2023." A country counts as "with data" only if it has the value AND its weight that year. **World totals** are labelled "total of countries with data", because they can differ slightly from official world figures (decision E-05).

---

## 6. What the build removes, and why (decision E-05, E-38)

Every removed row is listed in `data/processed/removed_rows.csv` (column, code, name, rows, reason).

- **OWID group rows.** "World" (code `OWID_WRL`), continents, income groups and unions such as "European Union (27)" (blank code). Rule: keep only rows whose code is 3 capital letters. Emolé makes every group figure herself, the same way every time, so "World" can never top a country ranking.
- **OWID former countries.** USSR, Yugoslavia, Czechoslovakia and similar carry `OWID_` codes and are removed.
- **Kosovo** is the one `OWID_` code that is a real country today: it is kept, renamed from `OWID_KOS` to the World Bank's `XKX` so both sources land on the same row.
- **World Bank group rows.** The World Bank's groups use 3-letter codes too (WLD = World, SSF = Sub-Saharan Africa, EUU = European Union, HIC = High income, and so on), so the 3-letter rule alone would let them in. They are removed by checking each code against the World Bank's own country list, which marks groups as "Aggregates".
- **Empty values** and **years outside 1970 to the current year** are dropped (counted in `build_info`).

---

## 7. The committed snapshot (decision E-45)

The built table is committed as `data/processed/country_year.parquet`, with `column_meta.csv`, `build_info.json` and `removed_rows.csv`. The database itself (`data/emole.duckdb`) is not committed; `python scripts/build_data.py --from-snapshot` rebuilds it from the snapshot in seconds, with no internet. Why: Docker builds (Step 5) and the evaluation's gold answers (Step 3) must give the same numbers even if a source changes or goes offline. All sources allow sharing with attribution (section 9).

---

## 8. Left out of version 1

- **Tourism arrivals** (decision E-08): considered, and left out because of the licence. OWID's tourism figures come from UN Tourism, which asks people to contact it for commercial licensing and asks students to send formal requests for free data, so it is not an open licence. The World Bank's copy is CC BY 4.0 but appears to stop around 2020.
- **Synthetic data** (decision E-10): none, anywhere. (The tiny files in `tests/fixtures/` hold made-up round numbers used only to test the code; they are never part of Emolé's data.)

---

## 9. Credits (attribution required by the licences)

Use this block wherever Emolé's data is shown (README, website credits page, posts that show numbers):

> Data: Our World in Data (ourworldindata.org, CC BY 4.0) and the World Bank World Development Indicators (data.worldbank.org, CC BY 4.0). Original producers: International Civil Aviation Organization (ICAO); International Telecommunication Union (ITU); World Bank, Eurostat, OECD and IMF (International Comparison Program); World Bank and OECD national accounts; IMF International Financial Statistics; International Labour Organization (ILO) modelled estimates; UN World Population Prospects 2024 (CC BY 3.0 IGO); UN Inter-agency Group for Child Mortality Estimation; WHO Global Health Expenditure Database; UN World Urbanization Prospects; Ember (CC BY 4.0) and the Energy Institute Statistical Review of World Energy; Global Carbon Project (Global Carbon Budget). Regions: UN Statistics Division, M49 standard (via the un-m49 package, MIT). Income groups and regions: World Bank country classifications (FY2027). Processed by Emolé.

Per-column citation format (used by the website in Step 4):
`<Producer>, via <World Bank | Our World in Data> (<year of download>), <licence>. <source link>`
For example: `International Civil Aviation Organization (ICAO), via Our World in Data (2026), CC BY 4.0. https://ourworldindata.org/grapher/air-passengers-carried`

---

## 10. Changes to this file

| Date | Step | Change |
|---|---|---|
| 8 Nov 2026 | 1 | First version: 17 columns checked, groupings, blocs, Middle East list, group maths, snapshot, credits. Measured years to be confirmed from the first real build. |
```

### `docs/PROJECT_STATE.md`

````markdown
# PROJECT_STATE.md

**Last updated:** 8 November 2026, end of Step 1 of 6 (delivered; waiting for the owner's first real build)
**Project:** Emolé, an expert on Movement, Output, Life and Energy
**Repository:** https://github.com/Dee-ui/emole (public; created in Step 1)
**Local path:** `C:\Users\Dauda Agbonoga\Documents\Projects\Project Emole`
**Live demo:** not yet (Step 5)

---

## 0. What this document is

The anchor for the whole project. It is rewritten in full at the end of every step, never
patched. If everything else is lost, this file alone is enough to understand what was
built, why every choice was made, what was verified, and what remains open.

---

## 1. Project at a glance

| Item | Value |
|---|---|
| Name | **Emolé** (display); `emole` in every technical name (repo, folders, package, URLs). Inspired by ìmọ́lẹ̀, the Yoruba word for light. Said "ee-maw-leh". |
| Introduction (fixed) | "I'm Emolé, an expert on Movement, Output, Life and Energy." |
| What it is | A chatbot that answers plain-English questions (typed or spoken) about countries: economy, energy, digital, aviation and health, over time and across regions, with exact figures, charts and a spoken reply |
| Core idea | Deterministic: the model writes ONE read-only SQL query; the database computes every number; code checks every number in the answer |
| Built from | A port of the owner's earlier private build (patterns only; no data, scores, history or branding from it) |
| Data | Public only: Our World in Data (13 columns) and the World Bank (4 columns), in one DuckDB table `country_year` |
| Modes (later steps) | local (Ollama), team (login, inside a network), public (free hosted models on Render) |
| Platform | Windows laptop, VS Code, PowerShell, Python 3.11.9 in `.venv`; Intel Core Ultra 7 265H, about 32 GB RAM, no NVIDIA |
| Owner | Dauda Agbonoga ("R&D"), GitHub `Dee-ui`, LinkedIn `dauda-agbonoga`, X `iam_the_Dee_ui` |
| Secrets | `.env` only (git-ignored), blocked at commit time by `scripts/check_no_secrets.py` |

**Step 1 headline:** a reproducible pipeline (`python scripts/build_data.py`) that builds
`country_year` with 17 checked columns, 4 grouping columns and 5 bloc columns; a
coverage report; a full data dictionary; group maths in Python and SQL that agree;
51 offline tests passing; and a secrets hook proven to block a fake key.

---

## 2. Why this data

One question ties the columns together: **"What does a country's money turn into?"**
A country earns money (Output), money buys power (Energy), power enables connection and
movement (internet, phones, flights), and all of it shows up in how long and how well
people live (Life). Population makes countries comparable. Every column describes the
same country in the same year, so cross-industry questions need no joins. Emolé reports
numbers side by side and never claims that one caused another.

---

## 3. The six-step plan

| Step | Content | Status |
|---|---|---|
| 1 | Foundations and data: repo, sources, build, coverage, data dictionary, tests | **Delivered.** Owner to run the first real build, agree drops, push, merge, tag `v0.1.0-step1` |
| 2 | Port the engine: SQL pipeline, checks, provider chain (Ollama, Groq, Gemini) | Not started |
| 3 | Evaluation and safety: test set, four providers, injection suite, threat model, CI | Not started |
| 4 | Website, voice and orb: three modes, garden look, pronunciation | Not started |
| 5 | Packaging and deployment: Docker, Render, README, `v1.0.0` | Not started |
| 6 | Demo video, 12-month content plan, launch, earning | Not started |

---

## 4. Decision log

### Planning (6 to 8 November 2026)

| ID | Decision | Reason |
|---|---|---|
| E-01 | Port the owner's earlier private build into a clean new repo `emole`; reuse the build and ideas, never data, scores, history, branding or company material | Data privacy; the portfolio must stand on its own |
| E-02 | Cross-industry theme connected by one question, mapped to M, O, L, E | Industries that connect, not a disconnected set |
| E-03 | OWID is the main source; the World Bank's free data service only for columns OWID lacks | One file shape, standard names |
| E-04 | One table `country_year` for the model; metadata in a code-only table | No joins; shippable fast |
| E-05 | Remove OWID's group rows; calculate every group from member countries; world totals labelled "total of countries with data" | "World" must not top country rankings; consistent group maths |
| E-06 | Counts summed; rates and per-person figures population-weighted; every group answer reports coverage | A plain average misleads |
| E-07 | "Middle East" uses Emolé's own documented list | No single official definition |
| E-08 | Tourism left out of version 1 | Not openly licensed; the open copy is stale |
| E-09 | Aviation columns carry the "registered airlines, not airports" caveat | Otherwise answers mislead |
| E-10 | Public data only, no synthetic data | Owner's standard |
| E-11 | Public demo on Render free; local mode on Ollama | No budget; a free server cannot run a 7B model |
| E-12 | Provider chain Groq and Gemini Flash-Lite (optionally OpenRouter); order by Step 3 accuracy, then speed | Free quotas are shared |
| E-13 | SQL quality beats prompt size; size measured, not capped | Owner's ruling |
| E-14 | Three modes: local, team, public | Sells internal, external, individual and team deployment |
| E-15 | Public mode: open guest use with limits, no stored chats | Low friction, protected quota |
| E-16 | Browser speech in public mode; Whisper and Kokoro locally; simulated orb level for browser voices | 512 MB server |
| E-17 | Pronunciation "ee-maw-leh": Kokoro phonemes, pre-recorded intro clip, tested respelling, owner's approval by ear | Very important to the owner |
| E-18 | Female persona and voice | Owner's choice |
| E-19 | New look: calm paradise garden, greens and sunlight gold | Clearly different from the earlier build |
| E-20 | English only; stock voices; no cloning | Shippable scope |
| E-21 | Post log from Step 1; posts in recent past tense | Scheduled posts must stay true |
| E-22 | LinkedIn and X are separate initiatives, never copies | Owner's instruction |
| E-23 | 2 posts a day per platform in month 1; 3 to 5 a week for months 2 to 12 | Owner's instruction |
| E-24 | Demo video in Step 6 | Owner's choice |
| E-25 | No causation claims, no political verdicts | Deterministic promise |
| E-26 | "Inspired by ìmọ́lẹ̀"; `emole` in technical names | Variant claim unconfirmed; accents break URLs |
| E-27 | Free tiers and limits verified before code relies on them | Rule D-72 |
| E-28 | Upload-your-own-data, MCP server, agent chains: roadmap only | Selling points without the build |
| E-29 | Earning options planned in Step 6 | Owner's request |

### Step 1: foundations and data

| ID | Decision | Reason |
|---|---|---|
| E-30 | Local folder `C:\Users\Dauda Agbonoga\Documents\Projects\Project Emole` (owner's choice, outside OneDrive); GitHub repo `Dee-ui/emole`, public | Owner confirmed both. The folder name may differ from the repo name: all paths are worked out from the code's own location (`config.PROJECT_ROOT`) |
| E-31 | Code layout `src/emole/` as an installable package (`pyproject.toml`; `-e .` inside `requirements.txt`) | One way to import (`from emole import config`) for scripts, tests, the website and Docker; no `sys.path` edits as in the earlier build; tests run against the installed package |
| E-32 | MIT licence for the code; data keeps its original licences | Simple and permissive for a portfolio and client work. **Awaiting the owner's confirmation** |
| E-33 | All sources in `data/sources.yaml`; bloc lists in `data/reference/blocs.yaml`; both checked before any download | Adding a column is one entry; a typo stops the build with a clear message |
| E-34 | OWID files downloaded with `csvType=full&useColumnShortNames=true` (OWID's own recommendation); the value column is picked automatically, or named with `value_column` | Short names are stable; key columns are always `Entity, Code, Year` (OWID chart API docs) |
| E-35 | GDP per person = PPP, constant 2021 international dollars (NY.GDP.PCAP.PP.KD, from 1990) | Fair across countries and years; immune to currency swings |
| E-36 | Renewables = share of electricity generation (Ember from 2000, Energy Institute before), not of all primary energy | Ember covers over 200 countries to 2025, including Nigeria and all peers; matches what people mean by "renewable power" |
| E-37 | Four World Bank columns: departures (no OWID chart), GDP growth (OWID's chart is the SDG series, 2000 to 2023 only), under-five mortality (needed unit, under CC BY 4.0), population (OWID switches to projections after 2023; weights need estimates) | Each reason written in `sources.yaml` and `DATA.md`. **Awaiting the owner's agreement**, because E-03 says "only for columns OWID lacks" |
| E-38 | Group-row removal: OWID rows need a 3-letter code (blank and `OWID_` codes removed; `OWID_KOS` kept as `XKX`); World Bank rows are checked against the World Bank's own list of aggregates | World Bank groups use 3-letter codes too (WLD, SSF, EUU), so one rule cannot clean both sources |
| E-39 | Territories (Hong Kong, Puerto Rico ...) kept as rows | As the World Bank does; Step 2 decides how rankings treat them |
| E-40 | `continent` and `subregion` from UN M49 (via the MIT `un-m49` package v2.2.0, committed as `data/reference/un_m49.csv`); Taiwan and Kosovo added by hand; `wb_region` and `income_group` from the World Bank country list, CURRENT classification (FY2027, effective 1 July 2026) applied to all years | UNSD has no stable download link; a committed file keeps the build offline-safe. Current classification is simpler and honest if stated |
| E-41 | Blocs use CURRENT membership for all years; membership not suspension; G20 = its 19 countries (EU and AU via their own columns) | Simple for version 1; Emolé must say "current members". History can be added later |
| E-42 | Middle East = 16 countries (Bahrain, Egypt, Iran, Iraq, Israel, Jordan, Kuwait, Lebanon, Oman, Palestine, Qatar, Saudi Arabia, Syria, Turkiye, UAE, Yemen) | Common core of most definitions; exclusions written in `DATA.md` 4.4. **Awaiting the owner's agreement** |
| E-43 | Years 1970 to the current year | Aviation starts in 1970; no projections can slip in. Confirm after the coverage report |
| E-44 | Group rules: `sum` (4 columns), `pop_weighted` (11), plus two exceptions: `gdp_weighted` for GDP growth and `median` for inflation (both as the World Bank does). Helper gives the same number in Python and SQL; coverage counts a country only if it has the value AND its weight | Exact where possible; outliers and economy size handled honestly. **Exceptions await the owner's agreement**, because E-06 says rates are population-weighted |
| E-45 | Commit the processed snapshot (`country_year.parquet`, `column_meta.csv`, `build_info.json`, `removed_rows.csv`); keep `emole.duckdb` git-ignored; `--from-snapshot` rebuilds it offline | Reproducible Docker builds and gold answers even if a source changes or goes offline; licences allow it with credit |
| E-46 | Polite downloads: User-Agent names the project (no email); dated raw files; reuse unless `--refresh`; `--offline` never downloads | Courtesy to publishers; repeatable builds |
| E-47 | Two "latest" years per column: `latest_year` (any data) and `latest_broad_year` (at least 80% of the column's best count in the last 10 years) | Ember's 2025 data covers 91 countries; a ranking on a thin year compares the reporters, not the world |
| E-48 | Coverage flag rule written before the first real build: under 60% of countries with a population figure, or Nigeria with no value in the latest 5 years, or a peer missing more than 3 of them. A flag means review; drops are agreed with the owner | Pre-registered rules cannot be bent by results (IEEE-CIS habit) |
| E-49 | Secrets: `scripts/check_no_secrets.py` as a pre-commit hook and a CI step over all tracked files; test keys glued together at run time and kept out of test names | Prevention beats remembering (IEEE-CIS D-59) |
| E-50 | Pins: duckdb 1.4.5, pandas 2.3.3, numpy 2.4.6, pyarrow 26.0.1, requests 2.34.2, PyYAML 6.0.3, pytest 9.2.0, ruff 0.17.4, pre-commit 4.7.0 | DuckDB 1.4.5 and pandas 2.3.3 are the versions the earlier build ran with (its read-only settings were tested on 1.4.5); DuckDB 2.0.0 and pandas 3 are new major releases to revisit later |
| E-51 | A light CI from Step 1: secrets scan, ruff, offline pytest | Branch, PR and "CI green before merge" need CI to exist; Step 3 extends it |
| E-52 | `.gitattributes` stores text with LF endings; every CSV the code writes uses LF | Windows and Linux copies otherwise look different on every line |
| E-53 | Tests run offline on tiny fixtures in the real file shapes, with round, clearly labelled test-only numbers | CI cannot download; the fixtures are test inputs, never Emolé's data, so E-10 still holds |

---

## 5. Verified results

### 5.1 Sources checked by hand (8 November 2026)

| Letter | Column | Source and id | Unit | Licence | Years as checked |
|---|---|---|---|---|---|
| M | air_passengers | OWID `air-passengers-carried` (IS.AIR.PSGR) | passengers | CC BY 4.0 | 1970-2023 |
| M | air_departures | World Bank IS.AIR.DPRT | departures | CC BY 4.0 | 1970-2023 |
| M | air_freight_mtkm | OWID `air-transport-freight-ton-km` (IS.AIR.GOOD.MT.K1) | million tonne-km | CC BY 4.0 | 1970-2023 |
| M | internet_users_pct | OWID `share-of-individuals-using-the-internet` (IT.NET.USER.ZS) | % of population | CC BY 4.0 | 1990-2025 |
| M | mobile_subs_per_100 | OWID `mobile-cellular-subscriptions-per-100-people` (IT.CEL.SETS.P2) | per 100 people | CC BY 4.0 | 1960-2025 |
| O | gdp_per_capita_ppp | OWID `gdp-per-capita-worldbank` (NY.GDP.PCAP.PP.KD) | intl-$ 2021 prices | CC BY 4.0 | 1990-2024 |
| O | gdp_growth_pct | World Bank NY.GDP.MKTP.KD.ZG | % per year | CC BY 4.0 | 1961-2024 |
| O | inflation_cpi_pct | OWID `inflation-of-consumer-prices` (FP.CPI.TOTL.ZG) | % per year | CC BY 4.0 | 1960-2025 |
| O | unemployment_pct | OWID `unemployment-rate` (SL.UEM.TOTL.ZS) | % of labour force | CC BY 4.0 | 1991-2025 |
| L | life_expectancy_years | OWID `life-expectancy` (UN WPP 2024 from 1950) | years | CC BY 3.0 IGO / CC BY 4.0 | to 2023 |
| L | under5_deaths_per_1000 | World Bank SH.DYN.MORT | per 1,000 live births | CC BY 4.0 | 1960-2024 |
| L | health_spend_per_capita_ppp | OWID `annual-healthcare-expenditure-per-capita` (SH.XPD.CHEX.PP.CD) | current intl-$ | CC BY 4.0 | 2000-2024 |
| L | population | World Bank SP.POP.TOTL | people | CC BY 4.0 | 1960-2025 |
| L | urban_pop_pct | OWID `share-of-population-urban` (SP.URB.TOTL.IN.ZS) | % of population | CC BY 4.0 | 1960-2024 |
| E | electricity_access_pct | OWID `share-of-the-population-with-access-to-electricity` (EG.ELC.ACCS.ZS) | % of population | CC BY 4.0 | 1990-2024 |
| E | renewables_share_elec_pct | OWID `share-electricity-renewables` (Ember, Energy Institute) | % of electricity | CC BY 4.0 / attribution | 1985-2025 |
| E | co2_per_capita_t | OWID `co-emissions-per-capita` (Global Carbon Budget) | tonnes per person | CC BY 4.0 | 1750-2024 |

Other facts checked on the same date: ECOWAS has 12 members (Burkina Faso, Mali and Niger
left, effective 29 January 2025); the AU has 55 members including Western Sahara; the EU
has 27; the G20 has 19 country members plus the EU and AU; the World Bank FY2027 income
classification took effect on 1 July 2026 (low up to $1,175; high above $14,375).

### 5.2 Code verified in the build workspace (Linux, Python 3.11.18)

- **Tests:** 51 passed in about 0.6 s, offline, twice in a row (second run with the pytest cache present). `ruff check .` clean.
- **Build pipeline, end to end on fixtures:** only real countries survive (OWID World, Africa, income groups, EU, USSR removed; World Bank WLD, SSF and a blank code removed); Kosovo from `OWID_KOS` and from the World Bank's `XKX` land on one row; every country-year kept exactly once; a year before 1970 dropped and counted; whole-number totals stored as integers; groupings filled (Taiwan's missing World Bank region listed, not hidden); `column_meta` years correct, including a broad year one year behind the latest; DuckDB written and readable; snapshot round trip identical; two builds identical.
- **Group maths:** sum, population-weighted, GDP-weighted and median checked against hand calculations; the SQL form gives the same number as the Python form for all four rules on DuckDB 1.4.5.
- **Secrets hook in a real Git repository:** with `pre-commit install`, a clean first commit passed both hooks; a commit holding a fake Groq-shaped key was BLOCKED and never created.
- **UN M49 file:** 248 of 248 entries converted (after a fix: see corrections), fingerprint `14faf74380d185db`.
- **Friendly failures:** `--offline` with no saved files, `--from-snapshot` with no snapshot and `--refresh --offline` each stop with one clear sentence.

### 5.3 Not verified yet (could not run in the build workspace)

The build workspace cannot reach ourworldindata.org or api.worldbank.org (every request
returned a proxy error), so the **real downloads, the real summary and the real coverage
report have not run yet**. The owner runs them on his laptop (guide Part 3, steps 6 to 8).

### 5.4 First real build (to be pasted by the owner)

```
(paste the summary printed by: python scripts/build_data.py)
```

Coverage flags and the drops agreed with the owner:

| Column | Flag reason | Decision |
|---|---|---|
| (from docs/coverage_report.md) | | |

---

## 6. Repository structure

```
Project Emole/                      (the local folder; the GitHub repo is "emole")
├── .github/workflows/ci.yml        secrets scan + ruff + offline tests
├── .env.example                    template; copy to .env (git-ignored)
├── .gitattributes                  LF line endings
├── .gitignore
├── .pre-commit-config.yaml         secrets hook + ruff before every commit
├── LICENSE                         MIT (code only)
├── README.md                       placeholder ("work in progress")
├── pyproject.toml                  makes src/emole an installable package
├── requirements.txt                pinned versions, plus "-e ."
├── data/
│   ├── sources.yaml                the 17 columns: source, unit, rule, licence, years
│   ├── reference/
│   │   ├── un_m49.csv              UN M49 continents and subregions (248 rows)
│   │   ├── manual_regions.csv      Taiwan, Kosovo
│   │   └── blocs.yaml              ECOWAS, AU, EU, G20, Middle East (with as-of dates)
│   ├── raw/                        downloads (git-ignored)
│   ├── processed/                  committed snapshot (after the first real build)
│   └── emole.duckdb                the database (git-ignored, rebuilt)
├── docs/
│   ├── PROJECT_STATE.md            this file
│   ├── POST_LOG.md                 findings for posts
│   ├── DATA.md                     data dictionary, sources, licences, group rules
│   ├── coverage_report.md          written by scripts/coverage_report.py
│   └── steps/step1.md              this step's guide
├── scripts/
│   ├── build_data.py               one command builds the database
│   ├── coverage_report.py          writes docs/coverage_report.md
│   ├── check_no_secrets.py         the secrets check
│   └── make_m49_reference.py       refreshes un_m49.csv (rarely needed)
├── src/emole/
│   ├── __init__.py
│   ├── config.py                   paths and settings
│   ├── groupmath.py                group rules in Python and SQL
│   └── data/
│       ├── sources.py              reads and checks the lists
│       ├── fetch.py                polite downloads, dated raw files
│       ├── parse.py                cleaning; group-row removal
│       ├── groups.py               continent, region, income group, blocs
│       ├── build.py                the build
│       └── coverage.py             the coverage report
└── tests/                          51 offline tests + fixtures
```

`src/emole/pipeline/` (the engine) arrives in Step 2; `web/` in Step 4; `Dockerfile` in Step 5.

---

## 7. Environment

| Item | Value |
|---|---|
| Python | 3.11.9 on the laptop (tested here on 3.11.18) |
| Install | `pip install -r requirements.txt` (also installs `emole` itself in editable mode) |

### 7.1 Library versions and the gotchas each one caused

| Library | Version | Notes |
|---|---|---|
| duckdb | 1.4.5 | Same as the earlier build. 2.0.0 exists (new major), not adopted. Step 2's read-only settings (`enable_external_access = false`, `lock_configuration = true`) were tested on 1.4.5 there |
| pandas | 2.3.3 | Nullable `Int64` for whole-number totals. Mixed `None`/`NaN` in text columns triggers a FutureWarning in frame comparisons; the build turns every empty text value into `None` |
| numpy | 2.4.6 | numpy 2.x: no `np.NaN` |
| pyarrow | 26.0.1 | Parquet snapshot |
| requests | 2.34.2 | Custom User-Agent from `config.USER_AGENT` |
| PyYAML | 6.0.3 | `safe_load` only |
| pytest | 9.2.0 | Parametrised test names are saved in `.pytest_cache`: never put secret-shaped strings in test ids |
| ruff | 0.17.4 | Rules E, F, W, I, B; line length 110; B905 wants `zip(..., strict=True)` |
| pre-commit | 4.7.0 | Hooks use `language: system`, so the `.venv` must be active when committing |

### 7.2 Data-source gotchas found in Step 1

- World Bank group rows use 3-letter codes (WLD, SSF ...): removed via the World Bank's aggregate list.
- World Bank region names can carry trailing spaces ("Sub-Saharan Africa "): stripped.
- OWID's Kosovo is `OWID_KOS`; the World Bank's is `XKX`: renamed to `XKX`.
- The un-m49 package writes names with apostrophes in double quotes: the converter accepts both and checks the count.
- Python's `csv` module writes Windows line endings by default: every CSV uses `lineterminator="\n"`.

---

## 8. Conventions

**Code**
- All paths from `src/emole/config.py`. No `sys.path` edits (the package is installed).
- Every script is a thin wrapper around a function in `src/emole/` (testable, importable).
- Expected failures stop with one plain sentence (`BUILD STOPPED: ...`), not a traceback.
- Decision rules that use results are written down before the results are seen (E-48).
- Secrets never appear in a source file, notebook, terminal command, test name or chat.
- Platform pricing, free tiers and sources are verified before code is written against them (E-27).

**Git**
- Branch `step-NN-short-description`; commits `type: message` (`feat:`, `fix:`, `docs:`, `test:`, `chore:`); formatting-only changes in their own commit.
- Pull request per step, CI green before merging, squash-merge, tag after merge (`v0.1.0-step1` ... `v1.0.0` after Step 5).

**Documentation**
- No em dashes. Plain words. Explanation before every code block. Full files, never fragments.
- The owner's earlier private build is called only "the earlier build" in this public repo; its name, its employer context and its data are never written here (Context rule 13).
- Every step ends with: the guide (`docs/steps/stepN.md`), a zip, this file rewritten in full, new `POST_LOG.md` entries.
- When an earlier claim turns out wrong, correct it openly in the next deliverable.

---

## 9. Corrections made

| # | Step | Correction |
|---|---|---|
| 1 | 1 | The first M49 conversion read 246 countries, not 248: names with an apostrophe (North Korea, Laos) were skipped. Fixed, and the converter now stops if any entry is missed (PL-007) |
| 2 | 1 | Planning expected air cargo to need the World Bank; OWID publishes it (`air-transport-freight-ton-km`). Only departures needed the World Bank |
| 3 | 1 | Before delivery, two links in `blocs.yaml` that had not been opened during the checks, and a World Bank region name that had not been verified, were replaced with checked links and neutral wording; an unverified hyperinflation figure was removed from the docs |

---

## 10. Completed

- [x] Sources verified for all 17 columns, groupings and blocs (8 Nov 2026)
- [x] Repo scaffold, package layout, pinned requirements, licence, gitignore, env template
- [x] Build script, coverage report, group maths helper, data dictionary
- [x] 51 offline tests passing; ruff clean; secrets hook proven in a real Git commit
- [ ] First real build on the owner's laptop; summary pasted in 5.4
- [ ] Coverage report reviewed; drops agreed and recorded in `DATA.md`
- [ ] Repo on GitHub, PR merged with CI green, tag `v0.1.0-step1` pushed

---

## 11. Open questions

| # | Question | Status |
|---|---|---|
| Q-01 | MIT licence for the code? | Open, owner to confirm (E-32) |
| Q-02 | Agree the 4 World Bank columns and their reasons? | Open (E-37) |
| Q-03 | Agree the 2 group-maths exceptions (GDP growth GDP-weighted, inflation median)? | Open (E-44) |
| Q-04 | Agree the 16-country Middle East list? | Open (E-42) |
| Q-05 | Peer list as suggested in planning (Nigeria, Ghana, Kenya, South Africa, Egypt, Ethiopia, Cote d'Ivoire, Senegal, Morocco, United States, United Kingdom, India, Brazil, Indonesia, China, Germany, UAE)? | Used as is; owner may change it in `config.PEER_COUNTRIES` |
| Q-06 | Keep 1970 as the first year? | Open until the coverage report |
| Q-07 | Which flagged columns (if any) to drop? | Open until the first real build |
| Q-08 | Should rankings skip territories (rows with no income group)? | For Step 2 |
| Q-09 | Store the group rules as DuckDB macros in the database, so Step 2's SQL can call them by name? | Idea for Step 2 |
| Q-10 | Historical bloc membership and income groups? | Future version |

---

## 12. How to resume from nothing

```powershell
cd "C:\Users\Dauda Agbonoga\Documents\Projects"
git clone https://github.com/Dee-ui/emole.git "Project Emole"
cd "Project Emole"

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pre-commit install

Copy-Item .env.example .env       # Step 1 needs no keys

pytest                             # 51 offline tests
python scripts/build_data.py --from-snapshot   # rebuild the database from the committed snapshot
python scripts/coverage_report.py

code docs/PROJECT_STATE.md
```

To refresh the data from the sources instead: `python scripts/build_data.py --refresh`.

---

## 13. Glossary

| Term | Plain meaning |
|---|---|
| OWID | Our World in Data, a free publisher of cleaned global data |
| WDI | World Development Indicators, the World Bank's main data collection |
| ISO3 | A country's 3-letter code (NGA = Nigeria) |
| UN M49 | The UN standard list of regions (Africa, Western Africa ...) |
| Aggregate | A group row (World, a region, an income group) rather than a country |
| DuckDB | A small, fast database stored in one file |
| Parquet | A compact file format for tables that keeps data types |
| Snapshot | The committed copy of the built table, so the database can be rebuilt offline |
| Population-weighted average | An average where bigger countries count more, in proportion to their population |
| Median | The middle value when all values are sorted |
| Broad-coverage year | The newest year in which most of a column's usual countries report |
| Pre-commit hook | A check Git runs before saving a commit; it can block the commit |
| CI | Automatic checks on a clean machine every time code is pushed |
| Fixture | A small, made-up input file used only by tests |
````

### `docs/POST_LOG.md`

```markdown
# Emolé post log

Real findings from building Emolé, written as they happen (decision E-21). Step 6
writes every LinkedIn and X post from this file, so the content comes from real events.

**Rules for entries**
- Write in recent past tense ("Emolé failed 3 group questions because..."), never as live reporting.
- Only real events and measured numbers. If a number is not measured yet, say so; never estimate one.
- Nothing about the owner's employer, its clients or its data, and no history from the owner's earlier private build.
- No em dashes.

**Entry format**

| Field | Meaning |
|---|---|
| ID | PL-001, PL-002 ... |
| Step | which step |
| What happened | plain description |
| Real numbers | measured figures, before and after |
| Why it matters | the lesson, in one or two lines |
| Evidence | screenshot, clip, chart, log line or commit to capture (with file path) |
| Angles | a possible LinkedIn angle and a possible X angle |

---

### PL-001: One question tied five industries together
- **Step:** 1 (planning decision, built in Step 1)
- **What happened:** Instead of picking unrelated datasets, the columns were chosen to answer one question: "What does a country's money turn into?" Money (Output) buys power (Energy), power enables connection and movement (internet, phones, flights), and all of it shows up in how long and how well people live (Life). The four groups spell the assistant's name: Movement, Output, Life, Energy.
- **Real numbers:** 17 columns in 4 groups (5 Movement, 4 Output, 5 Life, 3 Energy) in one table, `country_year`, so cross-industry questions need no joins.
- **Why it matters:** a dataset with a story makes better questions possible ("which countries grew fast but still lack electricity?") and is easier to explain than a pile of indicators.
- **Evidence:** `data/sources.yaml` (the 17 entries); the column table in `docs/DATA.md` section 1.
- **Angles:** LinkedIn: how one framing question turned a data dump into a product. X: "Movement, Output, Life, Energy: the four letters of the name are also the four groups of columns."

### PL-002: The World Bank's "World" row wears a country-style code
- **Step:** 1
- **What happened:** OWID marks its group rows with a blank code or an `OWID_` code, so "keep 3-letter codes only" removes them. But the World Bank's group rows use 3-letter codes too (WLD for World, SSF for Sub-Saharan Africa, EUU for the European Union, HIC for High income). The same rule would have let every World Bank group into the country table, and "World" would have topped every country ranking. A second filter now checks each World Bank code against the World Bank's own country list, which marks groups as "Aggregates".
- **Real numbers:** in the test files, 2 of 2 World Bank aggregates were removed (WLD, SSF) along with 5 OWID group names. The count in the real data is measured by the first full build (to be filled from `data/processed/removed_rows.csv`).
- **Why it matters:** a cleaning rule that works for one source can silently fail for another. Check every source's group rows separately.
- **Evidence:** `src/emole/data/parse.py` (two rules); `tests/test_parse.py::test_world_bank_aggregates_are_removed_even_with_3_letter_codes`; after the real build, `data/processed/removed_rows.csv`.
- **Angles:** LinkedIn: a data-quality lesson in one sentence, "the World would have been the biggest country". X: before/after of a ranking with WLD at number 1.

### PL-003: Emolé calculates every group herself
- **Step:** 1
- **What happened:** Both sources publish their own totals for regions and income groups. All of them were removed, and every group figure is now calculated from member countries with one of four documented rules (sum, population-weighted, GDP-weighted, median). A helper produces the same number in Python and in SQL, and tests prove they match.
- **Real numbers:** 4 rules across 17 columns (4 summed, 11 population-weighted, 1 GDP-weighted, 1 median). In the tests, a two-country example with internet use of 45% (205 million people) and 65% (31 million people) gave 47.6% with population weights, against 55.0% with a plain average.
- **Why it matters:** a plain average lets a country of half a million count as much as a country of 200 million. Consistent, explainable group maths is part of being deterministic.
- **Evidence:** `src/emole/groupmath.py`; `tests/test_groupmath.py::test_population_weighted_average`.
- **Angles:** LinkedIn: why "average of averages" is a trap in business reporting too. X: the 47.6% vs 55.0% example in two lines.

### PL-004: "Nigeria's air passengers" does not mean passengers at Nigerian airports
- **Step:** 1
- **What happened:** While checking the aviation sources, the definition turned out to be "passengers carried by air carriers registered in the country, regardless of origin or destination". Foreign airlines flying into Lagos are not in Nigeria's figure. Every aviation column now carries a caveat flag, and the answer code (Step 2) must add a plain note whenever one is used.
- **Real numbers:** 3 of 17 columns carry the caveat (`air_passengers`, `air_departures`, `air_freight_mtkm`); all three end in 2023.
- **Why it matters:** the most natural reading of a number can be wrong. An honest assistant says what a figure counts.
- **Evidence:** `caveat: aviation` in `data/sources.yaml`; ICAO definition quoted in `docs/DATA.md` section 3.
- **Angles:** LinkedIn: "read the definition before the number", for anyone building dashboards. X: one-line myth vs fact about airline statistics.

### PL-005: ECOWAS has 12 members, not 15
- **Step:** 1
- **What happened:** Before writing the bloc lists, ECOWAS membership was checked. Burkina Faso, Mali and Niger announced their exit in January 2024 and ECOWAS confirmed it took effect on 29 January 2025, so the list has 12 members. A design trade-off followed: version 1 applies current membership to every year, so "ECOWAS in 2010" uses today's 12, and Emolé must say "current members".
- **Real numbers:** 15 to 12 members. The bloc file stops the build if a list's count does not match its members.
- **Why it matters:** reference lists go stale. Record an "as of" date and a source for every list.
- **Evidence:** `data/reference/blocs.yaml`; `tests/test_sources.py::test_bloc_lists_match_the_checked_memberships`.
- **Angles:** LinkedIn: keeping reference data honest when the world changes. X: "my data assistant had to learn that ECOWAS shrank".

### PL-006: Tourism was left out because of its licence
- **Step:** 1 (decided in planning, recorded in the data dictionary)
- **What happened:** Tourism arrivals would have fitted the Movement group, but OWID's tourism data comes from UN Tourism, which asks for contact about commercial licensing, and the openly licensed World Bank copy appears to stop around 2020. The column was left out and the reason was written into the README and data dictionary.
- **Real numbers:** 17 columns kept; 1 considered and dropped for licence reasons.
- **Why it matters:** "publicly visible" is not the same as "free to reuse". A portfolio project that will be deployed for clients must respect licences from day one.
- **Evidence:** `docs/DATA.md` section 8.
- **Angles:** LinkedIn: licences as a product decision, not a legal afterthought. X: "the column I wanted and could not use".

### PL-007: Two countries vanished because their names had an apostrophe
- **Step:** 1
- **What happened:** The UN M49 region list (which country sits in which subregion) was converted from an open-source package. The first run found 246 countries; a cross-check against the source file found 248. The missing two were "Democratic People's Republic of Korea" and "Lao People's Democratic Republic": names with an apostrophe are written in double quotes in the source, and the pattern only accepted single quotes. The pattern was fixed, and the script now stops if the number of entries it reads differs from the number in the file.
- **Real numbers:** 246 before the fix, 248 after; 0 silent losses allowed from now on.
- **Why it matters:** silent data loss is worse than a crash. A count check costs one line.
- **Evidence:** `scripts/make_m49_reference.py` (the comment above `ENTRY` and the count check); `tests/test_sources.py::test_m49_reference_is_complete` (checks Laos is present).
- **Angles:** LinkedIn: "always reconcile counts" as a habit, with this real example. X: the one-character bug (a quote mark) that deleted two countries.

### PL-008: Choosing the population source changed the maths for 2024 and 2025
- **Step:** 1
- **What happened:** Population is the weight for every group average, so it must cover the same years as the other columns. OWID's long-run population series switches to UN projections after 2023, which would have made 2024 and 2025 group averages depend on projections. The World Bank's population series has estimates up to 2025, so population comes from the World Bank. Three other columns also came from the World Bank with written reasons (departures: no OWID chart; GDP growth: OWID's chart covers only 2000 to 2023; under-five mortality: the needed unit under CC BY 4.0).
- **Real numbers:** 13 of 17 columns from OWID, 4 from the World Bank, each fallback with a reason in `data/sources.yaml`.
- **Why it matters:** the weight column matters as much as the values it weights. "Same source for everything" is a good default, not a rule to follow blindly.
- **Evidence:** `why_source` fields in `data/sources.yaml`; `docs/DATA.md` section 3.
- **Angles:** LinkedIn: documenting every exception to your own rule. X: "projections disguised as data" in one tweet.

### PL-009: Inflation uses the median, because one country can break an average
- **Step:** 1
- **What happened:** Most rates use a population-weighted average, but inflation was given the median instead, the same method the World Bank uses for this indicator. A single hyperinflation (hundreds or thousands of percent in a year) would swamp any average for its region. GDP growth was given a GDP-weighted average, as the World Bank does for regional growth.
- **Real numbers:** 2 of 17 columns use an exception to the population-weighted rule; both are written in `column_meta.weight_note`.
- **Why it matters:** the right summary depends on the shape of the data. Outliers decide whether a mean tells the truth.
- **Evidence:** `data/sources.yaml` (inflation and GDP growth entries); `tests/test_groupmath.py::test_median`.
- **Angles:** LinkedIn: mean vs median explained with a real data decision. X: "why my assistant reports median inflation for regions".

### PL-010: "Latest year" turned out not to be one number
- **Step:** 1
- **What happened:** Ember's electricity data has 2025 figures for 91 countries, far fewer than its usual coverage, so "the latest year" for renewables is either 2025 (any data) or 2024 (broad coverage). The build now stores both for every column: `latest_year` and `latest_broad_year` (the newest year where at least 80% of the column's usual countries report). Rankings and group answers will use the broad year.
- **Real numbers:** in the test files, one column's newest year had 2 of its usual 3 countries, so its broad year moved back one year. The real values for all 17 columns come from the first full build.
- **Why it matters:** a ranking built on a thin year silently compares the 91 countries that reported, not the world.
- **Evidence:** `src/emole/data/build.py::broad_year`; `tests/test_build.py::test_column_meta_measures_years`; after the real build, section 1 of `docs/coverage_report.md`.
- **Angles:** LinkedIn: "latest" is a definition, not a fact. X: the 91-countries example.

### PL-011: The secrets check caught fake keys hiding in the test cache
- **Step:** 1
- **What happened:** A pre-commit hook now blocks token-shaped strings (Groq, Google, Hugging Face, GitHub and AWS key shapes, private keys, and long secret assignments) before any commit. Its tests build fake keys at run time so the test file itself is clean. A repo-wide test then found the fake keys inside pytest's own cache, because parametrised test names included them. The cache is never committed, but the test names were changed so no fake key is ever written anywhere. In a real Git test, a clean commit passed and a commit holding a fake Groq-shaped key was blocked.
- **Real numbers:** 5 key shapes tested; 1 fake-key commit blocked out of 1 tried; 0 hits in a scan of the whole repository.
- **Why it matters:** secrets leak through side doors (caches, logs, test names), not just source files. Prevention beats remembering.
- **Evidence:** `scripts/check_no_secrets.py`; `.pre-commit-config.yaml`; `tests/test_secrets.py`; terminal output of the blocked commit (capture a screenshot when you repeat the test in the guide, Part 3).
- **Angles:** LinkedIn: secrets hygiene for AI apps that use API keys. X: "my secrets scanner found secrets in my test cache".

### PL-012: The data is committed, so the demo never depends on a source being online
- **Step:** 1
- **What happened:** After each build, the finished table is saved as a small Parquet snapshot in the repo, with its column metadata, build info and the list of removed rows. The database can be rebuilt from it with no internet. Docker builds and test answers will use the same numbers even if a source changes or goes offline.
- **Real numbers:** rebuilding from the snapshot was tested (same table, row for row). Snapshot size is measured after the first real build.
- **Why it matters:** reproducibility. A test answer key that changes when a website updates is not an answer key.
- **Evidence:** `data/processed/`; `tests/test_build.py::test_snapshot_rebuild_gives_the_same_table`.
- **Angles:** LinkedIn: reproducible data for AI evaluation. X: "my CI never downloads data".

### PL-013: Every free source was checked before any download code was written
- **Step:** 1
- **What happened:** Following the rule learned in an earlier project (verify free tiers and sources before writing code against them), all 17 sources were checked by hand for the exact chart or code, unit, producer, licence and years before the download code existed. The check settled several open points: air cargo turned out to be on OWID (planning expected the World Bank), departures needed the World Bank as expected, GDP growth, under-five mortality and population moved to the World Bank with reasons (PL-008), and renewables was defined as a share of electricity rather than of all energy.
- **Real numbers:** 17 sources checked; 4 World Bank fallbacks, each with a written reason; 0 sources with a non-open licence kept.
- **Why it matters:** an hour of checking prevents a week of rework.
- **Evidence:** the `checked` fields in `data/sources.yaml`; `docs/DATA.md` section 3.
- **Angles:** LinkedIn: "verify before you build" as an engineering habit. X: a checklist screenshot of the 17 sources.
```

### `data/reference/un_m49.csv`

Generated by `scripts/make_m49_reference.py` (248 rows).

```text
iso3,m49_code,name,continent,m49_subregion,intermediate_region,subregion
ABW,533,Aruba,Americas,Latin America and the Caribbean,Caribbean,Caribbean
AFG,004,Afghanistan,Asia,Southern Asia,,Southern Asia
AGO,024,Angola,Africa,Sub-Saharan Africa,Middle Africa,Middle Africa
AIA,660,Anguilla,Americas,Latin America and the Caribbean,Caribbean,Caribbean
ALA,248,Åland Islands,Europe,Northern Europe,,Northern Europe
ALB,008,Albania,Europe,Southern Europe,,Southern Europe
AND,020,Andorra,Europe,Southern Europe,,Southern Europe
ARE,784,United Arab Emirates,Asia,Western Asia,,Western Asia
ARG,032,Argentina,Americas,Latin America and the Caribbean,South America,South America
ARM,051,Armenia,Asia,Western Asia,,Western Asia
ASM,016,American Samoa,Oceania,Polynesia,,Polynesia
ATA,010,Antarctica,,,,
ATF,260,French Southern Territories,Africa,Sub-Saharan Africa,Eastern Africa,Eastern Africa
ATG,028,Antigua and Barbuda,Americas,Latin America and the Caribbean,Caribbean,Caribbean
AUS,036,Australia,Oceania,Australia and New Zealand,,Australia and New Zealand
AUT,040,Austria,Europe,Western Europe,,Western Europe
AZE,031,Azerbaijan,Asia,Western Asia,,Western Asia
BDI,108,Burundi,Africa,Sub-Saharan Africa,Eastern Africa,Eastern Africa
BEL,056,Belgium,Europe,Western Europe,,Western Europe
BEN,204,Benin,Africa,Sub-Saharan Africa,Western Africa,Western Africa
BES,535,"Bonaire, Sint Eustatius and Saba",Americas,Latin America and the Caribbean,Caribbean,Caribbean
BFA,854,Burkina Faso,Africa,Sub-Saharan Africa,Western Africa,Western Africa
BGD,050,Bangladesh,Asia,Southern Asia,,Southern Asia
BGR,100,Bulgaria,Europe,Eastern Europe,,Eastern Europe
BHR,048,Bahrain,Asia,Western Asia,,Western Asia
BHS,044,Bahamas,Americas,Latin America and the Caribbean,Caribbean,Caribbean
BIH,070,Bosnia and Herzegovina,Europe,Southern Europe,,Southern Europe
BLM,652,Saint Barthélemy,Americas,Latin America and the Caribbean,Caribbean,Caribbean
BLR,112,Belarus,Europe,Eastern Europe,,Eastern Europe
BLZ,084,Belize,Americas,Latin America and the Caribbean,Central America,Central America
BMU,060,Bermuda,Americas,Northern America,,Northern America
BOL,068,Bolivia (Plurinational State of),Americas,Latin America and the Caribbean,South America,South America
BRA,076,Brazil,Americas,Latin America and the Caribbean,South America,South America
BRB,052,Barbados,Americas,Latin America and the Caribbean,Caribbean,Caribbean
BRN,096,Brunei Darussalam,Asia,South-eastern Asia,,South-eastern Asia
BTN,064,Bhutan,Asia,Southern Asia,,Southern Asia
BVT,074,Bouvet Island,Americas,Latin America and the Caribbean,South America,South America
BWA,072,Botswana,Africa,Sub-Saharan Africa,Southern Africa,Southern Africa
CAF,140,Central African Republic,Africa,Sub-Saharan Africa,Middle Africa,Middle Africa
CAN,124,Canada,Americas,Northern America,,Northern America
CCK,166,Cocos (Keeling) Islands,Oceania,Australia and New Zealand,,Australia and New Zealand
CHE,756,Switzerland,Europe,Western Europe,,Western Europe
CHL,152,Chile,Americas,Latin America and the Caribbean,South America,South America
CHN,156,China,Asia,Eastern Asia,,Eastern Asia
CIV,384,Côte d’Ivoire,Africa,Sub-Saharan Africa,Western Africa,Western Africa
CMR,120,Cameroon,Africa,Sub-Saharan Africa,Middle Africa,Middle Africa
COD,180,Democratic Republic of the Congo,Africa,Sub-Saharan Africa,Middle Africa,Middle Africa
COG,178,Congo,Africa,Sub-Saharan Africa,Middle Africa,Middle Africa
COK,184,Cook Islands,Oceania,Polynesia,,Polynesia
COL,170,Colombia,Americas,Latin America and the Caribbean,South America,South America
COM,174,Comoros,Africa,Sub-Saharan Africa,Eastern Africa,Eastern Africa
CPV,132,Cabo Verde,Africa,Sub-Saharan Africa,Western Africa,Western Africa
CRI,188,Costa Rica,Americas,Latin America and the Caribbean,Central America,Central America
CUB,192,Cuba,Americas,Latin America and the Caribbean,Caribbean,Caribbean
CUW,531,Curaçao,Americas,Latin America and the Caribbean,Caribbean,Caribbean
CXR,162,Christmas Island,Oceania,Australia and New Zealand,,Australia and New Zealand
CYM,136,Cayman Islands,Americas,Latin America and the Caribbean,Caribbean,Caribbean
CYP,196,Cyprus,Asia,Western Asia,,Western Asia
CZE,203,Czechia,Europe,Eastern Europe,,Eastern Europe
DEU,276,Germany,Europe,Western Europe,,Western Europe
DJI,262,Djibouti,Africa,Sub-Saharan Africa,Eastern Africa,Eastern Africa
DMA,212,Dominica,Americas,Latin America and the Caribbean,Caribbean,Caribbean
DNK,208,Denmark,Europe,Northern Europe,,Northern Europe
DOM,214,Dominican Republic,Americas,Latin America and the Caribbean,Caribbean,Caribbean
DZA,012,Algeria,Africa,Northern Africa,,Northern Africa
ECU,218,Ecuador,Americas,Latin America and the Caribbean,South America,South America
EGY,818,Egypt,Africa,Northern Africa,,Northern Africa
ERI,232,Eritrea,Africa,Sub-Saharan Africa,Eastern Africa,Eastern Africa
ESH,732,Western Sahara,Africa,Northern Africa,,Northern Africa
ESP,724,Spain,Europe,Southern Europe,,Southern Europe
EST,233,Estonia,Europe,Northern Europe,,Northern Europe
ETH,231,Ethiopia,Africa,Sub-Saharan Africa,Eastern Africa,Eastern Africa
FIN,246,Finland,Europe,Northern Europe,,Northern Europe
FJI,242,Fiji,Oceania,Melanesia,,Melanesia
FLK,238,Falkland Islands (Malvinas),Americas,Latin America and the Caribbean,South America,South America
FRA,250,France,Europe,Western Europe,,Western Europe
FRO,234,Faroe Islands,Europe,Northern Europe,,Northern Europe
FSM,583,Micronesia (Federated States of),Oceania,Micronesia,,Micronesia
GAB,266,Gabon,Africa,Sub-Saharan Africa,Middle Africa,Middle Africa
GBR,826,United Kingdom of Great Britain and Northern Ireland,Europe,Northern Europe,,Northern Europe
GEO,268,Georgia,Asia,Western Asia,,Western Asia
GGY,831,Guernsey,Europe,Northern Europe,,Northern Europe
GHA,288,Ghana,Africa,Sub-Saharan Africa,Western Africa,Western Africa
GIB,292,Gibraltar,Europe,Southern Europe,,Southern Europe
GIN,324,Guinea,Africa,Sub-Saharan Africa,Western Africa,Western Africa
GLP,312,Guadeloupe,Americas,Latin America and the Caribbean,Caribbean,Caribbean
GMB,270,Gambia,Africa,Sub-Saharan Africa,Western Africa,Western Africa
GNB,624,Guinea-Bissau,Africa,Sub-Saharan Africa,Western Africa,Western Africa
GNQ,226,Equatorial Guinea,Africa,Sub-Saharan Africa,Middle Africa,Middle Africa
GRC,300,Greece,Europe,Southern Europe,,Southern Europe
GRD,308,Grenada,Americas,Latin America and the Caribbean,Caribbean,Caribbean
GRL,304,Greenland,Americas,Northern America,,Northern America
GTM,320,Guatemala,Americas,Latin America and the Caribbean,Central America,Central America
GUF,254,French Guiana,Americas,Latin America and the Caribbean,South America,South America
GUM,316,Guam,Oceania,Micronesia,,Micronesia
GUY,328,Guyana,Americas,Latin America and the Caribbean,South America,South America
HKG,344,"China, Hong Kong Special Administrative Region",Asia,Eastern Asia,,Eastern Asia
HMD,334,Heard Island and McDonald Islands,Oceania,Australia and New Zealand,,Australia and New Zealand
HND,340,Honduras,Americas,Latin America and the Caribbean,Central America,Central America
HRV,191,Croatia,Europe,Southern Europe,,Southern Europe
HTI,332,Haiti,Americas,Latin America and the Caribbean,Caribbean,Caribbean
HUN,348,Hungary,Europe,Eastern Europe,,Eastern Europe
IDN,360,Indonesia,Asia,South-eastern Asia,,South-eastern Asia
IMN,833,Isle of Man,Europe,Northern Europe,,Northern Europe
IND,356,India,Asia,Southern Asia,,Southern Asia
IOT,086,British Indian Ocean Territory,Africa,Sub-Saharan Africa,Eastern Africa,Eastern Africa
IRL,372,Ireland,Europe,Northern Europe,,Northern Europe
IRN,364,Iran (Islamic Republic of),Asia,Southern Asia,,Southern Asia
IRQ,368,Iraq,Asia,Western Asia,,Western Asia
ISL,352,Iceland,Europe,Northern Europe,,Northern Europe
ISR,376,Israel,Asia,Western Asia,,Western Asia
ITA,380,Italy,Europe,Southern Europe,,Southern Europe
JAM,388,Jamaica,Americas,Latin America and the Caribbean,Caribbean,Caribbean
JEY,832,Jersey,Europe,Northern Europe,,Northern Europe
JOR,400,Jordan,Asia,Western Asia,,Western Asia
JPN,392,Japan,Asia,Eastern Asia,,Eastern Asia
KAZ,398,Kazakhstan,Asia,Central Asia,,Central Asia
KEN,404,Kenya,Africa,Sub-Saharan Africa,Eastern Africa,Eastern Africa
KGZ,417,Kyrgyzstan,Asia,Central Asia,,Central Asia
KHM,116,Cambodia,Asia,South-eastern Asia,,South-eastern Asia
KIR,296,Kiribati,Oceania,Micronesia,,Micronesia
KNA,659,Saint Kitts and Nevis,Americas,Latin America and the Caribbean,Caribbean,Caribbean
KOR,410,Republic of Korea,Asia,Eastern Asia,,Eastern Asia
KWT,414,Kuwait,Asia,Western Asia,,Western Asia
LAO,418,Lao People's Democratic Republic,Asia,South-eastern Asia,,South-eastern Asia
LBN,422,Lebanon,Asia,Western Asia,,Western Asia
LBR,430,Liberia,Africa,Sub-Saharan Africa,Western Africa,Western Africa
LBY,434,Libya,Africa,Northern Africa,,Northern Africa
LCA,662,Saint Lucia,Americas,Latin America and the Caribbean,Caribbean,Caribbean
LIE,438,Liechtenstein,Europe,Western Europe,,Western Europe
LKA,144,Sri Lanka,Asia,Southern Asia,,Southern Asia
LSO,426,Lesotho,Africa,Sub-Saharan Africa,Southern Africa,Southern Africa
LTU,440,Lithuania,Europe,Northern Europe,,Northern Europe
LUX,442,Luxembourg,Europe,Western Europe,,Western Europe
LVA,428,Latvia,Europe,Northern Europe,,Northern Europe
MAC,446,"China, Macao Special Administrative Region",Asia,Eastern Asia,,Eastern Asia
MAF,663,Saint Martin (French Part),Americas,Latin America and the Caribbean,Caribbean,Caribbean
MAR,504,Morocco,Africa,Northern Africa,,Northern Africa
MCO,492,Monaco,Europe,Western Europe,,Western Europe
MDA,498,Republic of Moldova,Europe,Eastern Europe,,Eastern Europe
MDG,450,Madagascar,Africa,Sub-Saharan Africa,Eastern Africa,Eastern Africa
MDV,462,Maldives,Asia,Southern Asia,,Southern Asia
MEX,484,Mexico,Americas,Latin America and the Caribbean,Central America,Central America
MHL,584,Marshall Islands,Oceania,Micronesia,,Micronesia
MKD,807,North Macedonia,Europe,Southern Europe,,Southern Europe
MLI,466,Mali,Africa,Sub-Saharan Africa,Western Africa,Western Africa
MLT,470,Malta,Europe,Southern Europe,,Southern Europe
MMR,104,Myanmar,Asia,South-eastern Asia,,South-eastern Asia
MNE,499,Montenegro,Europe,Southern Europe,,Southern Europe
MNG,496,Mongolia,Asia,Eastern Asia,,Eastern Asia
MNP,580,Northern Mariana Islands,Oceania,Micronesia,,Micronesia
MOZ,508,Mozambique,Africa,Sub-Saharan Africa,Eastern Africa,Eastern Africa
MRT,478,Mauritania,Africa,Sub-Saharan Africa,Western Africa,Western Africa
MSR,500,Montserrat,Americas,Latin America and the Caribbean,Caribbean,Caribbean
MTQ,474,Martinique,Americas,Latin America and the Caribbean,Caribbean,Caribbean
MUS,480,Mauritius,Africa,Sub-Saharan Africa,Eastern Africa,Eastern Africa
MWI,454,Malawi,Africa,Sub-Saharan Africa,Eastern Africa,Eastern Africa
MYS,458,Malaysia,Asia,South-eastern Asia,,South-eastern Asia
MYT,175,Mayotte,Africa,Sub-Saharan Africa,Eastern Africa,Eastern Africa
NAM,516,Namibia,Africa,Sub-Saharan Africa,Southern Africa,Southern Africa
NCL,540,New Caledonia,Oceania,Melanesia,,Melanesia
NER,562,Niger,Africa,Sub-Saharan Africa,Western Africa,Western Africa
NFK,574,Norfolk Island,Oceania,Australia and New Zealand,,Australia and New Zealand
NGA,566,Nigeria,Africa,Sub-Saharan Africa,Western Africa,Western Africa
NIC,558,Nicaragua,Americas,Latin America and the Caribbean,Central America,Central America
NIU,570,Niue,Oceania,Polynesia,,Polynesia
NLD,528,Netherlands (Kingdom of the),Europe,Western Europe,,Western Europe
NOR,578,Norway,Europe,Northern Europe,,Northern Europe
NPL,524,Nepal,Asia,Southern Asia,,Southern Asia
NRU,520,Nauru,Oceania,Micronesia,,Micronesia
NZL,554,New Zealand,Oceania,Australia and New Zealand,,Australia and New Zealand
OMN,512,Oman,Asia,Western Asia,,Western Asia
PAK,586,Pakistan,Asia,Southern Asia,,Southern Asia
PAN,591,Panama,Americas,Latin America and the Caribbean,Central America,Central America
PCN,612,Pitcairn,Oceania,Polynesia,,Polynesia
PER,604,Peru,Americas,Latin America and the Caribbean,South America,South America
PHL,608,Philippines,Asia,South-eastern Asia,,South-eastern Asia
PLW,585,Palau,Oceania,Micronesia,,Micronesia
PNG,598,Papua New Guinea,Oceania,Melanesia,,Melanesia
POL,616,Poland,Europe,Eastern Europe,,Eastern Europe
PRI,630,Puerto Rico,Americas,Latin America and the Caribbean,Caribbean,Caribbean
PRK,408,Democratic People's Republic of Korea,Asia,Eastern Asia,,Eastern Asia
PRT,620,Portugal,Europe,Southern Europe,,Southern Europe
PRY,600,Paraguay,Americas,Latin America and the Caribbean,South America,South America
PSE,275,State of Palestine,Asia,Western Asia,,Western Asia
PYF,258,French Polynesia,Oceania,Polynesia,,Polynesia
QAT,634,Qatar,Asia,Western Asia,,Western Asia
REU,638,Réunion,Africa,Sub-Saharan Africa,Eastern Africa,Eastern Africa
ROU,642,Romania,Europe,Eastern Europe,,Eastern Europe
RUS,643,Russian Federation,Europe,Eastern Europe,,Eastern Europe
RWA,646,Rwanda,Africa,Sub-Saharan Africa,Eastern Africa,Eastern Africa
SAU,682,Saudi Arabia,Asia,Western Asia,,Western Asia
SDN,729,Sudan,Africa,Northern Africa,,Northern Africa
SEN,686,Senegal,Africa,Sub-Saharan Africa,Western Africa,Western Africa
SGP,702,Singapore,Asia,South-eastern Asia,,South-eastern Asia
SGS,239,South Georgia and the South Sandwich Islands,Americas,Latin America and the Caribbean,South America,South America
SHN,654,Saint Helena,Africa,Sub-Saharan Africa,Western Africa,Western Africa
SJM,744,Svalbard and Jan Mayen Islands,Europe,Northern Europe,,Northern Europe
SLB,090,Solomon Islands,Oceania,Melanesia,,Melanesia
SLE,694,Sierra Leone,Africa,Sub-Saharan Africa,Western Africa,Western Africa
SLV,222,El Salvador,Americas,Latin America and the Caribbean,Central America,Central America
SMR,674,San Marino,Europe,Southern Europe,,Southern Europe
SOM,706,Somalia,Africa,Sub-Saharan Africa,Eastern Africa,Eastern Africa
SPM,666,Saint Pierre and Miquelon,Americas,Northern America,,Northern America
SRB,688,Serbia,Europe,Southern Europe,,Southern Europe
SSD,728,South Sudan,Africa,Sub-Saharan Africa,Eastern Africa,Eastern Africa
STP,678,Sao Tome and Principe,Africa,Sub-Saharan Africa,Middle Africa,Middle Africa
SUR,740,Suriname,Americas,Latin America and the Caribbean,South America,South America
SVK,703,Slovakia,Europe,Eastern Europe,,Eastern Europe
SVN,705,Slovenia,Europe,Southern Europe,,Southern Europe
SWE,752,Sweden,Europe,Northern Europe,,Northern Europe
SWZ,748,Eswatini,Africa,Sub-Saharan Africa,Southern Africa,Southern Africa
SXM,534,Sint Maarten (Dutch part),Americas,Latin America and the Caribbean,Caribbean,Caribbean
SYC,690,Seychelles,Africa,Sub-Saharan Africa,Eastern Africa,Eastern Africa
SYR,760,Syrian Arab Republic,Asia,Western Asia,,Western Asia
TCA,796,Turks and Caicos Islands,Americas,Latin America and the Caribbean,Caribbean,Caribbean
TCD,148,Chad,Africa,Sub-Saharan Africa,Middle Africa,Middle Africa
TGO,768,Togo,Africa,Sub-Saharan Africa,Western Africa,Western Africa
THA,764,Thailand,Asia,South-eastern Asia,,South-eastern Asia
TJK,762,Tajikistan,Asia,Central Asia,,Central Asia
TKL,772,Tokelau,Oceania,Polynesia,,Polynesia
TKM,795,Turkmenistan,Asia,Central Asia,,Central Asia
TLS,626,Timor-Leste,Asia,South-eastern Asia,,South-eastern Asia
TON,776,Tonga,Oceania,Polynesia,,Polynesia
TTO,780,Trinidad and Tobago,Americas,Latin America and the Caribbean,Caribbean,Caribbean
TUN,788,Tunisia,Africa,Northern Africa,,Northern Africa
TUR,792,Türkiye,Asia,Western Asia,,Western Asia
TUV,798,Tuvalu,Oceania,Polynesia,,Polynesia
TZA,834,United Republic of Tanzania,Africa,Sub-Saharan Africa,Eastern Africa,Eastern Africa
UGA,800,Uganda,Africa,Sub-Saharan Africa,Eastern Africa,Eastern Africa
UKR,804,Ukraine,Europe,Eastern Europe,,Eastern Europe
UMI,581,United States Minor Outlying Islands,Oceania,Micronesia,,Micronesia
URY,858,Uruguay,Americas,Latin America and the Caribbean,South America,South America
USA,840,United States of America,Americas,Northern America,,Northern America
UZB,860,Uzbekistan,Asia,Central Asia,,Central Asia
VAT,336,Holy See,Europe,Southern Europe,,Southern Europe
VCT,670,Saint Vincent and the Grenadines,Americas,Latin America and the Caribbean,Caribbean,Caribbean
VEN,862,Venezuela (Bolivarian Republic of),Americas,Latin America and the Caribbean,South America,South America
VGB,092,British Virgin Islands,Americas,Latin America and the Caribbean,Caribbean,Caribbean
VIR,850,United States Virgin Islands,Americas,Latin America and the Caribbean,Caribbean,Caribbean
VNM,704,Viet Nam,Asia,South-eastern Asia,,South-eastern Asia
VUT,548,Vanuatu,Oceania,Melanesia,,Melanesia
WLF,876,Wallis and Futuna Islands,Oceania,Polynesia,,Polynesia
WSM,882,Samoa,Oceania,Polynesia,,Polynesia
YEM,887,Yemen,Asia,Western Asia,,Western Asia
ZAF,710,South Africa,Africa,Sub-Saharan Africa,Southern Africa,Southern Africa
ZMB,894,Zambia,Africa,Sub-Saharan Africa,Eastern Africa,Eastern Africa
ZWE,716,Zimbabwe,Africa,Sub-Saharan Africa,Eastern Africa,Eastern Africa
```
