# PROJECT_STATE.md

**Last updated:** 18 November 2026, Step 1 complete and closed out (first real build done; close-out branch `step-01b-closeout` ready for the owner). Step 2 not started: waiting for its prerequisites (section 11).
**Project:** Emolé ("Immy"), an expert on Movement, Output, Life and Energy
**Repository:** https://github.com/Dee-ui/emole (public)
**Local path:** `C:\Users\Dauda Agbonoga\Documents\Projects\Project Emole`
**Tags:** `v0.1.0-step1` (pushed 15 November 2026); `v0.1.1-step1` (close-out, to be pushed by the owner)
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
| Nickname | **Immy** (said "IM-ee"), for people who find Emolé hard to say. She answers to both names and knows both are her (E-54). |
| Introduction | "I'm Emolé, an expert on Movement, Output, Life and Energy. You can call me Immy." The first sentence stays fixed for the video, landing page and pinned post; the second adds the nickname (E-54; wording awaits the owner's approval, Q-12). |
| What it is | A chatbot that answers plain-English questions (typed or spoken) about countries: economy, energy, digital, aviation and health, over time and across regions, with exact figures, charts and a spoken reply |
| Core idea | Deterministic: the model writes ONE read-only SQL query; the database computes every number; code checks every number in the answer |
| Built from | A port of the owner's earlier private build (patterns only; no data, scores, history or branding from it) |
| Data | Public only: Our World in Data (13 columns) and the World Bank (4 columns), in one DuckDB table `country_year`: 13,328 rows, 238 countries and territories, 1970 to 2025 |
| Modes (later steps) | local (Ollama), team (login, inside a network), public (free hosted models on Render) |
| Platform | Windows laptop, VS Code, PowerShell, Python 3.11.9 in `.venv`; Intel Core Ultra 7 265H, about 32 GB RAM, no NVIDIA |
| Owner | Dauda Agbonoga ("R&D"), GitHub `Dee-ui`, LinkedIn `dauda-agbonoga`, X `iam_the_Dee_ui` |
| Secrets | `.env` only (git-ignored), blocked at commit time by `scripts/check_no_secrets.py` (proven on the owner's laptop, 15 November 2026) |
| How guides deliver files | No zip files from now on (E-55). Each guide gives every new or changed file in full, with its path, and the owner creates or edits it by hand |

**Step 1 headline:** a reproducible pipeline (`python scripts/build_data.py`) built
`country_year` from 17 checked public sources on the owner's laptop: 13,328 rows,
238 countries and territories, 25,489 group rows removed with reasons, one column
flagged and kept after review, 62 offline tests passing, and a secrets hook proven to
block a fake key. The first real build also found two problems that no test could have
found (a source format change and a unit a million times too big), both now fixed.

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
| 1 | Foundations and data: repo, sources, build, coverage, data dictionary, tests | **Complete.** Merged (PR #1), tagged `v0.1.0-step1`. Close-out (`step-01b-closeout`: format fix tests, freight unit, Channel Islands, docs) ready for the owner; tag `v0.1.1-step1` after merge |
| 2 | Port the engine: SQL pipeline, checks, provider chain (Ollama, Groq, Gemini) | **Not started.** Waiting for: keys in `.env`, provider model IDs and limits read from the consoles, the Middle East answer, agreement on the work groups (section 11) |
| 3 | Evaluation and safety: test set, providers compared, injection suite, threat model, CI | Not started |
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
| E-30 | Local folder `C:\Users\Dauda Agbonoga\Documents\Projects\Project Emole` (owner's choice, outside OneDrive); GitHub repo `Dee-ui/emole`, public | Owner confirmed both. All paths are worked out from the code's own location (`config.PROJECT_ROOT`) |
| E-31 | Code layout `src/emole/` as an installable package (`pyproject.toml`; `-e .` inside `requirements.txt`) | One way to import (`from emole import config`) for scripts, tests, the website and Docker; no `sys.path` edits |
| E-32 | MIT licence for the code; data keeps its original licences | **Confirmed by the owner (18 Nov 2026)** |
| E-33 | All sources in `data/sources.yaml`; bloc lists in `data/reference/blocs.yaml`; both checked before any download | Adding a column is one entry; a typo stops the build with a clear message |
| E-34 | OWID files downloaded with `csvType=full&useColumnShortNames=true`; the value column is picked automatically, or named with `value_column` | Short names are stable. (Key column casing turned out NOT to be stable: see E-56) |
| E-35 | GDP per person = PPP, constant 2021 international dollars (NY.GDP.PCAP.PP.KD, from 1990) | Fair across countries and years; immune to currency swings |
| E-36 | Renewables = share of electricity generation (Ember from 2000, Energy Institute before) | Ember covers over 200 countries to 2025; matches what people mean by "renewable power" |
| E-37 | Four World Bank columns: departures, GDP growth, under-five mortality, population, each with a written reason | **Agreed by the owner (18 Nov 2026)** |
| E-38 | Group-row removal: OWID rows need a 3-letter code (blank and `OWID_` codes removed; `OWID_KOS` kept as `XKX`); World Bank rows are checked against the World Bank's own list of aggregates | World Bank groups use 3-letter codes too (WLD, SSF, EUU) |
| E-39 | Territories (Hong Kong, Puerto Rico ...) kept as rows | As the World Bank does; Step 2 decides how rankings treat them (Q-08) |
| E-40 | `continent` and `subregion` from UN M49 (via the MIT `un-m49` package v2.2.0, committed as `data/reference/un_m49.csv`); Taiwan, Kosovo (and since E-60 the Channel Islands) added by hand; `wb_region` and `income_group` from the World Bank country list, CURRENT classification (FY2027) applied to all years | Offline-safe; current classification is simpler and honest if stated |
| E-41 | Blocs use CURRENT membership for all years; G20 = its 19 countries | Simple for version 1; Emolé must say "current members" |
| E-42 | Middle East = 16 countries (Bahrain, Egypt, Iran, Iraq, Israel, Jordan, Kuwait, Lebanon, Oman, Palestine, Qatar, Saudi Arabia, Syria, Turkiye, UAE, Yemen) | Common core of most definitions. **Still awaiting the owner's agreement (Q-04)** |
| E-43 | Years 1970 to the current year | **Confirmed by the first build:** 9 of 17 columns start in 1970; nothing after 2025 entered |
| E-44 | Group rules: `sum` (4 columns), `pop_weighted` (11), `gdp_weighted` for GDP growth, `median` for inflation; same number in Python and SQL; coverage counts a country only if it has the value AND its weight | **Exceptions agreed by the owner (18 Nov 2026)** |
| E-45 | Commit the processed snapshot; keep `emole.duckdb` git-ignored; `--from-snapshot` rebuilds it offline | Reproducible Docker builds and gold answers |
| E-46 | Polite downloads: User-Agent names the project; dated raw files; reuse unless `--refresh`; `--offline` never downloads | Courtesy to publishers; repeatable builds. **Proven useful:** a timed-out run resumed from 10 saved files (PL-015) |
| E-47 | Two "latest" years per column: `latest_year` and `latest_broad_year` (80% of the column's best count in the last 10 years) | **Proven needed:** internet use has 2025 values for 10 countries only |
| E-48 | Coverage flag rule written before the first real build | Pre-registered rules cannot be bent by results. Fired once (E-57) |
| E-49 | Secrets: `scripts/check_no_secrets.py` as a pre-commit hook and a CI step | Prevention beats remembering |
| E-50 | Pins: duckdb 1.4.5, pandas 2.3.3, numpy 2.4.6, pyarrow 26.0.1, requests 2.34.2, PyYAML 6.0.3, pytest 9.2.0, ruff 0.17.4, pre-commit 4.7.0 | Versions the earlier build ran with; new majors revisited later |
| E-51 | A light CI from Step 1: secrets scan, ruff, offline pytest | "CI green before merge" needs CI to exist |
| E-52 | `.gitattributes` stores text with LF endings; every CSV the code writes uses LF | Windows and Linux copies otherwise differ on every line |
| E-53 | Tests run offline on tiny fixtures in the real file shapes, with clearly labelled test-only numbers | CI cannot download; fixtures are never Emolé's data |

### Step 1 close-out (15 to 18 November 2026)

| ID | Decision | Reason |
|---|---|---|
| E-54 | Nickname **Immy**. Introduction: "I'm Emolé, an expert on Movement, Output, Life and Energy. You can call me Immy." She recognises Emolé, Emole and Immy (any case) as her own name in greetings and identity questions. Emolé stays the brand in every title, URL and post; Immy is only how people may address her | Owner's request: some people find Emolé hard to say. Keeping the first sentence unchanged protects E-17's recorded intro. Checked 18 Nov 2026: "ImmyBot" is an existing IT automation product (immy.bot) and "Immy" was an AR headset company that has closed; neither is a chatbot, and Immy is used only as a nickname, never as a product name |
| E-55 | **No zip files.** Guides give every new or changed file in full, with its path, marked "new file" or "replace the whole file", plus a short "what changed" list so a small edit can be made by hand | Owner's instruction: he follows along and builds the files himself. Replaces the zip in Context rule 5 and section 10.2 item 2 |
| E-56 | OWID files are read tolerantly but strictly: key columns `entity, code, year` matched by name in any case; any `owid_*` column dropped as metadata; anything else unexpected still stops the build | OWID changed its header casing and added `owid_region` within one week (PL-014). Long-term pattern, not a patch: `docs/DATA.md` 6.1 |
| E-57 | Keep `air_freight_mtkm` despite its flag | The flag came from one peer (Ghana, no values 2020 to 2023). Nigeria and 15 of 16 peers have values; 137 countries report in 2023; aviation is a core Movement column. Answers state missing values and coverage. Recorded in `docs/DATA.md` 3.1 |
| E-58 | Post evidence lives in the repo: `docs/evidence/stepN/PL-0xx_short-name.png`, with the path in the entry's Evidence line. Videos stay outside Git (`Documents\Emole media\stepN\`) | Posts link to proof in a public place; images stay small; rules against leaking secrets or private details in `docs/evidence/README.md` |
| E-59 | `sources.yaml` gains an optional `scale` field (multiply every value); `air_freight_mtkm` uses `scale: 0.000001` | OWID republishes `IS.AIR.GOOD.MT.K1` in tonne-km, a million times the World Bank's million tonne-km (PL-016). Converting keeps the column's name, unit and numbers matching the World Bank site people check against |
| E-60 | Channel Islands (`CHI`) added to `manual_regions.csv` as Europe, Northern Europe | `CHI` comes from World Bank files; M49 lists the Channel Islands (code 830) in Northern Europe but they have no ISO code, so the M49 file could not match them |
| E-61 | Step 1 fixes land as a small close-out PR (`step-01b-closeout`), tagged `v0.1.1-step1`, before Step 2 starts | Step 2 starts from a correct, tagged base; Step 1's tag stays a true record of what was first merged |

---

## 5. Verified results

### 5.1 Sources checked by hand (8 November 2026)

| Letter | Column | Source and id | Unit | Licence | Years as checked |
|---|---|---|---|---|---|
| M | air_passengers | OWID `air-passengers-carried` (IS.AIR.PSGR) | passengers | CC BY 4.0 | 1970-2023 |
| M | air_departures | World Bank IS.AIR.DPRT | departures | CC BY 4.0 | 1970-2023 |
| M | air_freight_mtkm | OWID `air-transport-freight-ton-km` (IS.AIR.GOOD.MT.K1), scaled by 0.000001 (E-59) | million tonne-km | CC BY 4.0 | 1970-2023 |
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
classification took effect on 1 July 2026.

### 5.2 Code verified in the build workspace (Linux, Python 3.11.18)

- **Tests:** 62 passed offline (51 from Step 1 plus 11 from the close-out); `ruff check .` clean. Run on the merged `main` with the close-out changes applied.
- **New in the close-out:** the old OWID format, the new OWID format (lowercase header plus `owid_region`) and a web page returned instead of a CSV are each tested; `scale` is validated (0, negative, text and true/false are refused) and applied to one column only; the Channel Islands get Europe and Northern Europe.
- **Unit sense check on the real snapshot:** for every column, the smallest, middle and largest 2019 value and Nigeria's 2019 value were read. 16 of 17 columns looked right; air freight was a million times too big (United States 2019: 42,498,260,000 under a "million tonne-km" label, which is far more than the whole world's air freight; the World Bank shows 42,498). Fixed by E-59.
- Step 1's earlier checks (group maths in Python and SQL agree; snapshot round trip identical; friendly failures; M49 file 248 of 248, fingerprint `14faf74380d185db`) still hold.

### 5.3 First real build on the owner's laptop (15 November 2026)

The first run stopped on the first OWID column (format change, PL-014). After the owner's
fix in `fetch.py` and `parse.py`, a second run stopped at the 11th column on a World Bank
read timeout (PL-015). A third run reused the 10 saved files and finished:

```
Emole data build  |  BUILD_VERSION 1  |  built 2026-11-15T03:31:26+00:00
country_year: 13,328 rows | 238 countries and territories | years 1970-2025

  letter column                          latest  broad  countries(broad)  aggregation
  M      air_passengers                   2023   2023               149  sum
  M      air_departures                   2023   2023               150  sum
  M      air_freight_mtkm                 2023   2023               137  sum
  M      internet_users_pct               2025   2024               182  pop_weighted
  M      mobile_subs_per_100              2024   2023               172  pop_weighted
  O      gdp_per_capita_ppp               2025   2025               185  pop_weighted
  O      gdp_growth_pct                   2025   2025               186  gdp_weighted
  O      inflation_cpi_pct                2025   2025               165  median
  O      unemployment_pct                 2025   2025               181  pop_weighted
  L      life_expectancy_years            2023   2023               237  pop_weighted
  L      under5_deaths_per_1000           2024   2024               196  pop_weighted
  L      health_spend_per_capita_ppp      2024   2023               192  pop_weighted
  L      population                       2025   2025               217  sum
  L      urban_pop_pct                    2025   2025               237  pop_weighted
  E      electricity_access_pct           2024   2024               214  pop_weighted
  E      renewables_share_elec_pct        2025   2024               196  pop_weighted
  E      co2_per_capita_t                 2025   2025               219  pop_weighted

Rows removed: OWID_ code 16 names / 6,826 rows; World Bank aggregate 44 / 9,856;
blank World Bank code 5 / 1,120; blank OWID code 66 / 4,892; not 3 capital letters 12 / 2,795.

Grouping gaps: continent 1 (CHI); subregion 1 (CHI); wb_region 21; income_group 21;
bloc members missing from the table: 0.
```

**Snapshot committed:** `country_year.parquet` 1,102,622 bytes; `removed_rows.csv` 438 lines.

**What the close-out rebuild changes** (owner runs `python scripts/build_data.py --offline`,
which reuses the saved raw files): air freight values become a million times smaller
(United States 2019: 42,498.26); the continent and subregion gaps drop from 1 to 0
(`CHI` joins Europe, Northern Europe); Europe goes from 50 to 51 members in the coverage
report. Row count, countries, years and every other column stay the same. The owner
confirms these after the rerun (section 11, "What I need").

### 5.4 Coverage review (pre-registered rule E-48)

| Column | Flag reason | Decision |
|---|---|---|
| `air_freight_mtkm` | Peer missing more than 3 of the latest 5 years: Ghana (no value 2020 to 2023) | **Kept** (E-57) |
| the other 16 | no flag | kept |

Notes from the review (no flag, but Step 2 must handle them):
- Thin newest years: internet use 2025 has 10 countries (broad year 2024: 182); health spending 2024 has 22 (broad 2023: 192); renewables 2025 has 91 (broad 2024: 196).
- Nigeria has every value in the latest 5 years for 15 of 17 columns (internet use misses 2025, health spending misses 2024: not yet published).
- Air freight is the thinnest aviation column: 4 of 12 ECOWAS members, 29 of 58 African countries in 2023.
- 21 territories have no World Bank region or income group (AIA, BES, BLM, COK, ESH, FLK, GGY, GLP, GUF, JEY, MSR, MTQ, MYT, NIU, REU and 6 more). Relevant to Q-08.

### 5.5 Git and secrets on the owner's laptop (15 November 2026)

- Branch `step-01-foundations-data` pushed with one commit (`6168394 feat: complete step 1 foundations and data`, 51 files); PR #1 merged into `main` as `6e53ea3` with CI and the secrets scan passing; tag `v0.1.0-step1` pushed.
- The PR was merged with a merge commit rather than a squash merge. Harmless; from the close-out on, use "Squash and merge" (section 8).
- Leak test: a fake Groq-shaped key in `leak_test.py` was **blocked**: `BLOCKED: leak_test.py:1 looks like a Groq API key.` The file was unstaged and deleted. Screenshot to be saved as `docs/evidence/step1/PL-011_secret-blocked.png`.

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
├── README.md                       placeholder ("work in progress"; written in Step 5)
├── pyproject.toml                  makes src/emole an installable package
├── requirements.txt                pinned versions, plus "-e ."
├── data/
│   ├── sources.yaml                the 17 columns: source, unit, rule, licence, years, scale
│   ├── reference/
│   │   ├── un_m49.csv              UN M49 continents and subregions (248 rows)
│   │   ├── manual_regions.csv      Taiwan, Kosovo, Channel Islands
│   │   └── blocs.yaml              ECOWAS, AU, EU, G20, Middle East (with as-of dates)
│   ├── raw/                        downloads (git-ignored)
│   ├── processed/                  committed snapshot: country_year.parquet, column_meta.csv,
│   │                               build_info.json, removed_rows.csv
│   └── emole.duckdb                the database (git-ignored, rebuilt)
├── docs/
│   ├── PROJECT_STATE.md            this file
│   ├── POST_LOG.md                 findings for posts (PL-001 to PL-018)
│   ├── DATA.md                     data dictionary, sources, licences, group rules, coverage review
│   ├── coverage_report.md          written by scripts/coverage_report.py
│   ├── evidence/                   post evidence (README with the rules; step1/ ...)
│   └── steps/
│       ├── step1.md                Step 1 guide (a record of what was delivered on 8 Nov)
│       └── step1_closeout.md       Step 1 close-out guide
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
│       ├── sources.py              reads and checks the lists (now also `scale`)
│       ├── fetch.py                polite downloads, dated raw files, case-blind CSV check
│       ├── parse.py                cleaning; group-row removal; case-blind keys; owid_* dropped
│       ├── groups.py               continent, region, income group, blocs
│       ├── build.py                the build (applies `scale`)
│       └── coverage.py             the coverage report
└── tests/                          62 offline tests + fixtures
```

Step guides are a record of the day they were delivered. The repository on `main` is
always the current version of every file. `src/emole/pipeline/` (the engine) arrives in
Step 2; `web/` in Step 4; `Dockerfile` in Step 5.

---

## 7. Environment

| Item | Value |
|---|---|
| Python | 3.11.9 on the laptop (tested here on 3.11.18) |
| Install | `pip install -r requirements.txt` (also installs `emole` itself in editable mode) |

### 7.1 Library versions and the gotchas each one caused

| Library | Version | Notes |
|---|---|---|
| duckdb | 1.4.5 | Same as the earlier build. 2.0.0 exists (new major), not adopted |
| pandas | 2.3.3 | Nullable `Int64` for whole-number totals. Empty text values turned into `None` to avoid a FutureWarning |
| numpy | 2.4.6 | numpy 2.x: no `np.NaN` |
| pyarrow | 26.0.1 | Parquet snapshot |
| requests | 2.34.2 | Custom User-Agent; 60-second timeout, 3 tries (`HTTP_TIMEOUT_SEC`, `HTTP_RETRIES`) |
| PyYAML | 6.0.3 | `safe_load` only. `0.000001` is read as a float (1e-06) |
| pytest | 9.2.0 | Never put secret-shaped strings in test ids (they are saved in `.pytest_cache`) |
| ruff | 0.17.4 | Rules E, F, W, I, B; line length 110 |
| pre-commit | 4.7.0 | Hooks use `language: system`, so the `.venv` must be active when committing |

### 7.2 Data-source gotchas

- World Bank group rows use 3-letter codes (WLD, SSF ...): removed via the World Bank's aggregate list.
- World Bank region names can carry trailing spaces: stripped.
- OWID's Kosovo is `OWID_KOS`; the World Bank's is `XKX`: renamed to `XKX`.
- The un-m49 package writes names with apostrophes in double quotes: the converter accepts both and checks the count.
- Python's `csv` module writes Windows line endings by default: every CSV uses `lineterminator="\n"`.
- **(15 Nov) OWID's CSV header casing changed** (`Entity` to `entity`) and an `owid_region` column appeared: handled by E-56.
- **(15 Nov) OWID publishes air freight in tonne-km**, not the World Bank's million tonne-km: handled by `scale` (E-59). Same code, different unit: always sense-check magnitudes against one known value.
- **(15 Nov) OWID files now also hold `WB_` and `UNSDG_` region rows**, and the life expectancy file holds England and Wales, Scotland and Northern Ireland: all removed by the existing rules.
- **(15 Nov) The World Bank API can time out** on large pages (`per_page=20000`): a rerun resumes from the saved files. If it becomes frequent, raise `HTTP_TIMEOUT_SEC` or lower the page size (Q-15).
- **(15 Nov) `CHI`** (Channel Islands) appears in World Bank files but not in M49: added by hand (E-60).

---

## 8. Conventions

**Code**
- All paths from `src/emole/config.py`. No `sys.path` edits (the package is installed).
- Every script is a thin wrapper around a function in `src/emole/` (testable, importable).
- Expected failures stop with one plain sentence (`BUILD STOPPED: ...`), not a traceback.
- Sources are read tolerantly (case, metadata columns) but never guessed: anything unexpected stops the build (E-56).
- Decision rules that use results are written down before the results are seen (E-48).
- Secrets never appear in a source file, notebook, terminal command, test name, screenshot or chat.
- Platform pricing, free tiers and sources are verified before code is written against them (E-27).

**Git**
- Branch `step-NN-short-description` (close-outs: `step-NNb-closeout`); commits `type: message` (`feat:`, `fix:`, `docs:`, `test:`, `chore:`, `data:`); formatting-only changes in their own commit.
- Pull request per step, CI green before merging, **"Squash and merge"** on GitHub, tag after merge (`v0.1.0-step1`, `v0.1.1-step1` ... `v1.0.0` after Step 5).

**Documentation**
- No em dashes. Plain words. Explanation before every code block. Full files, never fragments.
- **No zip files (E-55).** Every guide gives each new or changed file in full with its path, marked "New file" or "Replace the whole file", plus a short "what changed" list.
- Every step ends with: the guide (`docs/steps/stepN.md`), this file rewritten in full, new `POST_LOG.md` entries.
- Post evidence goes in `docs/evidence/stepN/`, named after the entry (E-58).
- The owner's earlier private build is called only "the earlier build" in this public repo; its name, its employer context and its data are never written here (Context rule 13).
- When an earlier claim turns out wrong, correct it openly in the next deliverable.

---

## 9. Corrections made

| # | Step | Correction |
|---|---|---|
| 1 | 1 | The first M49 conversion read 246 countries, not 248: names with an apostrophe (North Korea, Laos) were skipped. Fixed, and the converter now stops if any entry is missed (PL-007) |
| 2 | 1 | Planning expected air cargo to need the World Bank; OWID publishes it (`air-transport-freight-ton-km`). Only departures needed the World Bank |
| 3 | 1 | Before delivery, two unopened links in `blocs.yaml`, an unverified World Bank region name and an unverified hyperinflation figure were replaced or removed |
| 4 | 1 | **The Step 1 download check and cleaning required OWID's exact capitalised header (`Entity,Code,Year`).** OWID switched to lowercase and added `owid_region` between the source check (8 Nov) and the first build (15 Nov), so every OWID column failed. The owner fixed `fetch.py` and `parse.py` (commit `6168394`); the close-out adds the tests and makes it the long-term rule (E-56, PL-014) |
| 5 | 1 | **`air_freight_mtkm` was stored a million times too big.** Step 1 took the unit from the World Bank's definition of `IS.AIR.GOOD.MT.K1` without checking OWID's values (the build workspace could not download, so the real numbers were first seen after the owner's build). OWID publishes tonne-km. Fixed with `scale` (E-59, PL-016). No answer had used the column yet |
| 6 | 1 | The Channel Islands (`CHI`) had no continent or subregion. Added by hand (E-60) |

---

## 10. Completed

- [x] Sources verified for all 17 columns, groupings and blocs (8 Nov 2026)
- [x] Repo scaffold, package layout, pinned requirements, licence, gitignore, env template
- [x] Build script, coverage report, group maths helper, data dictionary
- [x] First real build on the owner's laptop (15 Nov 2026): 13,328 rows, 238 countries and territories
- [x] Coverage report reviewed: 1 flag, 0 drops, recorded in `DATA.md` 3.1
- [x] Repo on GitHub, PR #1 merged with CI green, tag `v0.1.0-step1` pushed
- [x] Secrets hook proven on the owner's laptop
- [x] Owner's answers: MIT, the 4 World Bank columns, the 2 maths exceptions, the peer list
- [x] Close-out prepared: format-change tests, freight scale, Channel Islands, docs, evidence folder; 62 tests passing
- [ ] Owner applies the close-out, reruns the build offline, merges, tags `v0.1.1-step1`
- [ ] Leak-test screenshot saved in `docs/evidence/step1/`

---

## 11. Open questions

| # | Question | Status |
|---|---|---|
| Q-01 | MIT licence for the code? | **Answered: yes** (E-32) |
| Q-02 | Agree the 4 World Bank columns? | **Answered: yes** (E-37) |
| Q-03 | Agree the 2 group-maths exceptions? | **Answered: yes** (E-44) |
| Q-04 | Agree the 16-country Middle East list? | **Open.** Not covered in the owner's 18 Nov answers. Needed before Step 2's name matching ("Middle East" maps to `is_middle_east`) |
| Q-05 | Peer list as suggested in planning? | **Answered: yes**, kept in `config.PEER_COUNTRIES` |
| Q-06 | Keep 1970 as the first year? | **Answered by the build:** kept (E-43) |
| Q-07 | Which flagged columns to drop? | **Answered:** none; air freight kept (E-57) |
| Q-08 | Should rankings skip territories (rows with no income group)? | For Step 2 (21 territories, 5.4) |
| Q-09 | Store the group rules as DuckDB macros, so Step 2's SQL can call them by name? | Idea for Step 2 |
| Q-10 | Historical bloc membership and income groups? | Future version |
| Q-11 | Make Emolé citable: a Zenodo DOI for releases, and possibly a technical report after Step 3? | Open, owner to decide. Recommendation in the 18 Nov reply: Zenodo DOI at `v1.0.0`; a report only if Step 3's evaluation is strong enough to stand as research |
| Q-12 | Approve the introduction wording with the nickname (E-54)? | Open |
| Q-13 | Step 2 prerequisites: Groq and Gemini keys in `.env` (never in chat); Gemini Flash-Lite model IDs, RPM and TPM from AI Studio; Groq's free models and limits from its console | Open, owner to provide |
| Q-14 | Add a code-computed "trend summary" (first, last, highest, lowest, change) for "how did X change over time" questions in Step 2? | Proposed 18 Nov; owner to decide |
| Q-15 | Raise the World Bank timeout or lower its page size? | Not needed yet (one timeout, recovered by a rerun). Revisit if it repeats |

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

Copy-Item .env.example .env       # Step 1 needs no keys; Step 2 needs Groq and Gemini keys here

pytest                             # 62 offline tests
python scripts/build_data.py --from-snapshot   # rebuild the database from the committed snapshot
python scripts/coverage_report.py

code docs/PROJECT_STATE.md
```

To refresh the data from the sources instead: `python scripts/build_data.py --refresh`.
To rebuild from files already downloaded, with no internet: `python scripts/build_data.py --offline`.

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
| Scale | A number every value of a column is multiplied by, to turn the source's unit into Emolé's |
| Tonne-kilometre | One tonne of cargo flown one kilometre |
| Pre-commit hook | A check Git runs before saving a commit; it can block the commit |
| CI | Automatic checks on a clean machine every time code is pushed |
| Fixture | A small, made-up input file used only by tests |
| DOI | A permanent link for a published work (paper, dataset or software release) that does not break if the website moves |