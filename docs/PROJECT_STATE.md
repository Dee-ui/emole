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
