# PROJECT_STATE.md

**Last updated:** 23 November 2026, Step 2 delivered (the engine, 147 offline tests passing). Waiting for the owner's runs with real models (Ollama, Groq, Gemini) and the forced-failure test; their results go into a Step 2 close-out, as in Step 1.
**Project:** Emolé ("Immy"), an expert on Movement, Output, Life and Energy
**Repository:** https://github.com/Dee-ui/emole (public)
**Local path:** `C:\Users\Dauda Agbonoga\Documents\Projects\Project Emole`
**Tags:** `v0.1.0-step1`, `v0.1.1-step1` (pushed); `v0.2.0-step2` (to be pushed by the owner after the Step 2 PR is merged)
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
| Nickname | **Immy** (said "IM-ee"). She answers to Emolé, Emole and Immy (E-54). |
| Introduction (approved 23 Nov 2026) | "I'm Emolé, an expert on Movement, Output, Life and Energy. You can call me Immy." Written by code, never by the model (`prompts.INTRODUCTION`). |
| What it is | A chatbot that answers plain-English questions (typed or spoken) about countries: economy, energy, digital, aviation and health, over time and across regions, with exact figures, charts and a spoken reply |
| Core idea | Deterministic: the model writes ONE read-only SQL query; the database computes every number; code checks the query before it runs and every number in the answer after |
| Front door | `emole.pipeline.engine.ask(question, history)`, used by the terminal chat now and by the evaluator (Step 3) and website (Step 4) later |
| Built from | A port of the owner's earlier private build (patterns only; no data, scores, history or branding from it) |
| Data | Public only: Our World in Data (13 columns) and the World Bank (4 columns), in one DuckDB table `country_year`: 13,328 rows, 238 countries and territories, 1970 to 2025 |
| Models | local and team: Ollama `qwen2.5:7b-instruct`; public: Groq `llama-3.3-70b-versatile`, then Gemini `gemini-3.5-flash-lite`, then `gemini-3.1-flash-lite` (order to be set by Step 3) |
| Platform | Windows laptop, VS Code, PowerShell, Python 3.11.9 in `.venv`; Intel Core Ultra 7 265H, about 32 GB RAM, no NVIDIA |
| Owner | Dauda Agbonoga ("R&D"), GitHub `Dee-ui`, LinkedIn `dauda-agbonoga`, X `iam_the_Dee_ui` |
| Secrets | `.env` only (git-ignored), blocked at commit time by `scripts/check_no_secrets.py`; code only ever says whether a key is set, never its value |
| How guides deliver files | No zip files (E-55). Each guide gives every new or changed file in full, with its path |

**Step 2 headline:** Emolé's engine. One front door, `engine.ask()`, turns a question into
a checked answer: place names are matched in code, one SQL query is written by a model
from a chain of providers (local Ollama, or Groq then Gemini), five code checks fix or
reject the query before it runs read-only, and the sentence passes a number check and a
no-causation check, with coverage notes written by code. 147 offline tests pass with a
stand-in model. Real models have not run yet (the workspace has no keys and no Ollama).

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
| 1 | Foundations and data: repo, sources, build, coverage, data dictionary, tests | **Complete.** `v0.1.0-step1` and close-out `v0.1.1-step1` merged and tagged |
| 2 | Port the engine: SQL pipeline, checks, provider chain (Ollama, Groq, Gemini) | **Delivered** (guide `docs/steps/step2.md`). Owner: apply, run tests, run the smoke list on 3 providers and the forced failure, merge, tag `v0.2.0-step2`, send results for the close-out |
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
| E-39 | Territories (Hong Kong, Puerto Rico ...) kept as rows | As the World Bank does. Rankings include them (E-69) |
| E-40 | `continent` and `subregion` from UN M49 (via the MIT `un-m49` package v2.2.0, committed as `data/reference/un_m49.csv`); Taiwan, Kosovo (and since E-60 the Channel Islands) added by hand; `wb_region` and `income_group` from the World Bank country list, CURRENT classification (FY2027) applied to all years | Offline-safe; current classification is simpler and honest if stated |
| E-41 | Blocs use CURRENT membership for all years; G20 = its 19 countries | Simple for version 1; Emolé must say "current members" |
| E-42 | Middle East = 16 countries (Bahrain, Egypt, Iran, Iraq, Israel, Jordan, Kuwait, Lebanon, Oman, Palestine, Qatar, Saudi Arabia, Syria, Turkiye, UAE, Yemen) | Common core of most definitions. **Approved by the owner (23 Nov 2026)** |
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
| E-54 | Nickname **Immy**. Introduction: "I'm Emolé, an expert on Movement, Output, Life and Energy. You can call me Immy." She recognises Emolé, Emole and Immy (any case) as her own name in greetings and identity questions. Emolé stays the brand in every title, URL and post; Immy is only how people may address her | Owner's request: some people find Emolé hard to say. Keeping the first sentence unchanged protects E-17's recorded intro. Checked 18 Nov 2026: "ImmyBot" is an existing IT automation product (immy.bot) and "Immy" was an AR headset company that has closed; neither is a chatbot, and Immy is used only as a nickname, never as a product name. **Wording approved by the owner (23 Nov 2026)** |
| E-55 | **No zip files.** Guides give every new or changed file in full, with its path, marked "new file" or "replace the whole file", plus a short "what changed" list so a small edit can be made by hand | Owner's instruction: he follows along and builds the files himself. Replaces the zip in Context rule 5 and section 10.2 item 2 |
| E-56 | OWID files are read tolerantly but strictly: key columns `entity, code, year` matched by name in any case; any `owid_*` column dropped as metadata; anything else unexpected still stops the build | OWID changed its header casing and added `owid_region` within one week (PL-014). Long-term pattern, not a patch: `docs/DATA.md` 6.1 |
| E-57 | Keep `air_freight_mtkm` despite its flag | The flag came from one peer (Ghana, no values 2020 to 2023). Nigeria and 15 of 16 peers have values; 137 countries report in 2023; aviation is a core Movement column. Answers state missing values and coverage. Recorded in `docs/DATA.md` 3.1 |
| E-58 | Post evidence lives in the repo: `docs/evidence/stepN/PL-0xx_short-name.png`, with the path in the entry's Evidence line. Videos stay outside Git (`Documents\Emole media\stepN\`) | Posts link to proof in a public place; images stay small; rules against leaking secrets or private details in `docs/evidence/README.md` |
| E-59 | `sources.yaml` gains an optional `scale` field (multiply every value); `air_freight_mtkm` uses `scale: 0.000001` | OWID republishes `IS.AIR.GOOD.MT.K1` in tonne-km, a million times the World Bank's million tonne-km (PL-016). Converting keeps the column's name, unit and numbers matching the World Bank site people check against |
| E-60 | Channel Islands (`CHI`) added to `manual_regions.csv` as Europe, Northern Europe | `CHI` comes from World Bank files; M49 lists the Channel Islands (code 830) in Northern Europe but they have no ISO code, so the M49 file could not match them |
| E-61 | Step 1 fixes land as a small close-out PR (`step-01b-closeout`), tagged `v0.1.1-step1`, before Step 2 starts | Step 2 starts from a correct, tagged base; Step 1's tag stays a true record of what was first merged |

### Step 2: the engine (23 November 2026)

| ID | Decision | Reason |
|---|---|---|
| E-62 | The engine lives in `src/emole/pipeline/` (13 modules), imported as `emole.pipeline.*`; scripts are thin wrappers (`scripts/chat.py`, `smoke_test.py`, `speed_check.py`, `review_log.py`, `prompt_size.py`) | Same package rule as E-31; no `sys.path` edits as in the earlier build |
| E-63 | Temperature 0 for SQL on Ollama and Groq; **no temperature sent to Gemini**; hosted models get at least 2,048 output tokens | Checked 23 Nov 2026: Google lists temperature as deprecated and ignored for Gemini 3.5 Flash-Lite and advises leaving it at the default for Gemini 3; Gemini 3 thinking cannot be switched off and uses output tokens. Changes Context 6.1 "temperature 0" for Gemini only (PL-020) |
| E-64 | The weighted group rules are stored in the database as macros `pop_avg(column)` and `gdp_avg(column)` (BUILD_VERSION 2); `pop_avg(total / population)` gives a group's per-person figure | Answers Q-09. The maths is written once (`groupmath.py`), short for the model, and checked in code |
| E-65 | Place names (countries, nicknames, adjectives, regions, blocs, income groups, "the world") are matched in code (`names.py`) and given to the model as NAME HINTS with exact codes; an unknown capitalised name gets "I don't recognise ..." with suggestions and no model call | A name match is right or wrong; code is never tired. Saves a model call on typos |
| E-66 | Provider chain: a provider that says busy (429, out of quota, timeout, 5xx) rests 60 s or as long as it asks; a broken one (wrong key, unknown model, refused request) rests 10 min and prints one warning naming the provider and error number; resting providers are tried last, not never; when all fail, `AllProvidersBusy` (public mode says "every model I use is busy, try again in a minute") | Free quotas are shared; the website (Step 4) turns the error into "the demo is full today". Trying resting providers last means starting Ollama fixes the next question at once |
| E-67 | Default public chain: `groq:llama-3.3-70b-versatile`, `gemini:gemini-3.5-flash-lite`, `gemini:gemini-3.1-flash-lite`; any chain can be set in `.env` (`EMOLE_PROVIDER_CHAIN`) | Llama 3.3 70B is Groq's general model without hidden reasoning (the gpt-oss models reason first and spend output tokens on it). Model IDs checked in Google's docs on 23 Nov 2026; **the owner confirms IDs and limits in his consoles (Q-13)**. Step 3 decides the order by accuracy, then speed (E-12) |
| E-68 | Prompt size measured, not cut: 18,044 characters, about 4,500 tokens (characters / 4), 22 worked examples; Ollama context 12,288 tokens; exact counts come from the providers on each call. `tiktoken` not used | E-13. tiktoken downloads its encoding file the first time it runs, a network dependency for one estimate |
| E-69 | Rankings of "countries" include territories (as World Bank rankings include Hong Kong and Macao); each ranked row shows its name | Answers Q-08. Step 3 tests whether it confuses answers; the fallback is to skip the 21 rows with no World Bank region |
| E-70 | Greetings, thanks, "who are you" and opinion or blame questions are answered by code, with no model call; NO_SQL from the model leads to a short chat reply whose numbers must come from DATA FACTS | Fixed wording for the introduction (E-54); no political verdicts (E-25); no wasted quota |
| E-71 | Five code checks before a query runs: names (hard), group maths (hard, fixed in code), per person (hard, fixed in code), latest year (soft, fixed in code), rankings use countries (soft). Hard checks must pass; soft checks only ask for a repair while one is left; one model repair at most | The earlier build's pattern (instant fixes first, one repair, soft checks never block), rebuilt for this data |
| E-72 | Code adds the notes, never the model: group coverage ("based on 16 of 17 Western Africa countries with data for 2024 (population-weighted average)"), "total of countries with data" for world figures, the aviation caveat, and "X data ends in YEAR" | E-05, E-06, E-09. A country counts only with the value AND its weight, the same rule as `groupmath.py` |
| E-73 | Sentences: one-value answers for one country and year use a fixed sentence per column (17 in `columns.py`); model sentences must pass the number check, a full-sentence check, a no-causation check and a no-verdict check, get one rewrite with the reason, then fall back to a code template | E-25 made checkable. Quick sentences save a model call |
| E-74 | Charts are yearly only (the earlier build's month, quarter and week logic was removed, not kept); several countries over time = lines; one country with several measures = one small chart per measure with its own unit; rankings = bars without a legend; units on every axis | The data is annual; measures with different units cannot share an axis |
| E-75 | Worked examples use years from the database (`{broad:column}`), and answer examples use real values from the 15 Nov build | Examples never go stale and never show invented numbers (E-10) |
| E-76 | Step 2 tests: a stand-in model returns scripted SQL and sentences (no keys, no network); the fixture database for logic; the REAL snapshot only to prove every worked example runs and passes the checks (no assertions on its values) | Context rule 6; CI stays offline; examples are guaranteed valid on the real table |
| E-77 | Smoke-test reports (`logs/smoke_*.md`) are copied into `docs/evidence/step2/` when they back a post | E-58: logs are git-ignored, evidence is public |

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

### 5.2 Step 1 code (unchanged facts)

The data build, group maths in Python and SQL, snapshot round trip, friendly failures and
M49 file (248 of 248, fingerprint `14faf74380d185db`) are as verified in Step 1. The
close-out added the OWID format tests, the freight `scale`, and the Channel Islands.

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
report. Row count, countries, years and every other column stay the same.

**Confirmed by the owner's close-out rebuild (23 November 2026, `--offline`):** 13,328 rows,
238 countries and territories, 1970 to 2025, every latest and broad year unchanged;
grouping gaps continent 0 and subregion 0 (was 1 each, `CHI`); air freight 2019: United
States 42,498.26, Nigeria 1.843419 million tonne-km; `CHI` in Europe, Northern Europe.
The close-out PR #2 was squash-merged and `v0.1.1-step1` pushed (tag object `863cf65`).

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
- Leak test: a fake Groq-shaped key in `leak_test.py` was **blocked**: `BLOCKED: leak_test.py:1 looks like a Groq API key.` The file was unstaged and deleted. Screenshot saved as `docs/evidence/step1/PL-011_secret-blocked.png` (in the close-out PR).

### 5.6 Step 2 verified in the build workspace (Linux, Python 3.11.18, 23 November 2026)

- **Tests:** 147 passed offline in about 7 s (62 from Step 1, 85 new); `ruff check .` clean; secrets scan clean.
- **What the tests cover:** name matching (nicknames, adjectives, longest name first, "World Bank" is not the world, typos with suggestions); the executor blocks 15 kinds of unsafe SQL (two statements, DROP, DELETE inside WITH, read_csv, read_parquet, query(), FROM 'file', COPY, ATTACH, PRAGMA, SET, INSTALL, other tables, system tables, comments) and allows WITH ... SELECT with the macros; the provider chain (fallback after 429, resting, resting tried last, all busy, default chains by mode, a missing key named but never printed, Gemini request without temperature, 429 and 503 = busy, 401 and 404 = broken); every check and instant fix; quick sentences, number check, causation rewrite then template; coverage, world and aviation notes; the engine end to end (quick answer, guards with no model call, group fix with coverage note, follow-up, repair, unsafe SQL never runs, chart, evaluator mode, all busy); every worked example runs on the real table and passes the checks.
- **Real table with a stand-in model (scripted SQL, deliberate mistakes):** 15 smoke questions ran end to end. `AVG(electricity_access_pct)` for West Africa was fixed to `pop_avg` in code; `year = 2025` in an internet ranking was fixed to the broad year 2024; a per-person question without division was fixed to `air_passengers / population`; "air passengers in 2025" got "the latest year I have for air passengers is 2023" with no model call; "Who are you?" and "Which president ruined Nigeria's economy?" were answered by code; "Wakanda" got "Did you mean Rwanda?".
- **Wire-level checks with pretend servers:** the Ollama sender sent `num_ctx` 12,288, `num_predict` 400, temperature 0 and `keep_alive` 60m, and read the token counts and load time; the hosted sender sent no temperature to Gemini, a 2,048-token cap, the key in the Authorization header only, and on a 429 with "retry after 7" fell back to the next provider and rested the first for 7 s.
- **Charts:** PNG and interactive versions drawn for a ranking (bars), a trend (line), continents compared (bars) and three measures over time (three panels with their own units); checked by eye.

**Not tested in the workspace (no keys, no Ollama, no internet to the providers):** any real model's SQL or sentences, real response times, real token counts, real rate limits, the warm-up on a real Ollama, and the real forced failure. These are the owner's runs (guide Part 6).

### 5.7 Real-model smoke runs (to be filled from the owner's results)

| Provider and model | Questions answered correctly | Average seconds | Prompt tokens (exact) | Fixes in code | Repairs | Notes |
|---|---|---|---|---|---|---|
| ollama:qwen2.5:7b-instruct | (pending) | | | | | |
| groq:llama-3.3-70b-versatile | (pending) | | | | | |
| gemini:gemini-3.5-flash-lite | (pending) | | | | | |
| forced failure: groq:no-such-model then gemini | (pending) | | | | | |

---

## 6. Repository structure

```
Project Emole/                      (the local folder; the GitHub repo is "emole")
├── .github/workflows/ci.yml        secrets scan + ruff + offline tests
├── .env.example                    template; copy to .env (git-ignored)
├── .gitattributes, .gitignore, .pre-commit-config.yaml, LICENSE, README.md, pyproject.toml
├── requirements.txt                pinned versions, plus "-e ."
├── data/
│   ├── sources.yaml                the 17 columns: source, unit, rule, licence, years, scale
│   ├── reference/                  un_m49.csv, manual_regions.csv, blocs.yaml
│   ├── raw/                        downloads (git-ignored)
│   ├── processed/                  committed snapshot (BUILD_VERSION 2 after the owner's rebuild)
│   └── emole.duckdb                the database, with the pop_avg and gdp_avg macros (git-ignored)
├── docs/
│   ├── PROJECT_STATE.md, POST_LOG.md (PL-001 to PL-025), DATA.md, coverage_report.md
│   ├── evidence/                   post evidence (README with the rules; step1/, step2/)
│   └── steps/                      step1.md, step1_closeout.md, step2.md
├── scripts/
│   ├── build_data.py, coverage_report.py, check_no_secrets.py, make_m49_reference.py   (Step 1)
│   ├── chat.py                     talk to Emolé in the terminal
│   ├── smoke_test.py               15 everyday questions on a chosen provider, report saved
│   ├── speed_check.py              where the time goes, per model call
│   ├── review_log.py               the questions that went wrong
│   └── prompt_size.py              measures the SQL prompt
├── src/emole/
│   ├── config.py                   paths and settings (Step 2 section: modes, providers, speed)
│   ├── groupmath.py                group rules in Python and SQL, plus the database macros
│   ├── data/                       the build (Step 1)
│   └── pipeline/                   the engine (Step 2)
│       ├── engine.py               ask(): the one front door
│       ├── llm.py                  the provider chain (Ollama, Groq, Gemini, OpenRouter)
│       ├── names.py                place names to exact codes, in code
│       ├── catalog.py              DATA FACTS measured from the database
│       ├── schema.py               the table described for the prompt
│       ├── columns.py              words, labels and fixed sentences for the 17 measures
│       ├── prompts.py              all prompt text and the worked examples
│       ├── nl_to_sql.py            question to SQL, and the one repair
│       ├── checks.py               the five checks and the instant fixes
│       ├── executor.py             runs SQL safely (5 layers)
│       ├── notes.py                coverage, aviation and latest-year notes
│       ├── responder.py            sentences and their checks; greetings and opinions
│       ├── visualizer.py           text or chart, and the chart
│       ├── followup.py             follow-up questions
│       ├── query_log.py            the question log (no rows, no keys)
│       └── chatbot.py              the terminal chat
└── tests/                          147 offline tests + fixtures (conftest has the stand-in model)
```

Step guides are a record of the day they were delivered. The repository on `main` is
always the current version of every file. `web/` arrives in Step 4; `Dockerfile` in Step 5.

---

## 7. Environment

| Item | Value |
|---|---|
| Python | 3.11.9 on the laptop (tested here on 3.11.18) |
| Install | `pip install -r requirements.txt` (also installs `emole` itself in editable mode) |
| Ollama | the app on the laptop, model `qwen2.5:7b-instruct` (`ollama pull qwen2.5:7b-instruct`) |

### 7.1 Library versions and the gotchas each one caused

| Library | Version | Notes |
|---|---|---|
| duckdb | 1.4.5 | Same as the earlier build. Macros stored in the database work on a read-only connection with external access off. `get_table_names` must be called on a connection that knows the macros (PL-023). Read-only connections still allow `CREATE TEMP` objects, so CREATE stays blocked by the executor |
| pandas | 2.3.3 | Nullable `Int64` for whole-number totals |
| numpy | 2.4.6 | numpy 2.x: no `np.NaN` |
| pyarrow | 26.0.1 | Parquet snapshot |
| requests | 2.34.2 | Data downloads; 60-second timeout, 3 tries |
| PyYAML | 6.0.3 | `safe_load` only |
| openai | 3.57.0 | Only as the OpenAI-compatible client for Groq and Gemini; `max_retries=0` so the chain decides; errors map to busy or broken |
| ollama | 0.6.3 | `Client(host, timeout)`; `chat(..., options={num_ctx, num_predict, temperature}, keep_alive)`; durations are nanoseconds |
| python-dotenv | 1.2.4 | Reads `.env` once in `config.py`; an empty line such as `OLLAMA_HOST=` is read as empty, so the code falls back to the default |
| plotly | 6.9.0 | Same as the earlier build (7.x exists; not adopted yet) |
| matplotlib | 3.10.9 | PNG charts with the Agg backend (no screen needed) |
| pytest | 9.2.0 | Never put secret-shaped strings in test ids |
| ruff | 0.17.4 | Rules E, F, W, I, B; line length 110 |
| pre-commit | 4.7.0 | Hooks use `language: system`, so the `.venv` must be active when committing |

### 7.2 Data and provider gotchas

- World Bank group rows use 3-letter codes (WLD, SSF ...): removed via the World Bank's aggregate list.
- OWID's CSV header casing changed and an `owid_region` column appeared (E-56).
- OWID publishes air freight in tonne-km, not the World Bank's million tonne-km (`scale`, E-59).
- OWID files also hold `WB_` and `UNSDG_` region rows and UK nations: removed by the existing rules.
- The World Bank API can time out; a rerun resumes from the saved files (Q-15).
- `CHI` (Channel Islands) is in World Bank files; OWID reports Guernsey and Jersey separately (E-60).
- **(Step 2) Gemini 3.5 Flash-Lite ignores temperature** and Gemini 3 models think before answering (E-63).
- **(Step 2) Groq's free limits are per model and per organisation**; Llama 3.3 70B's tokens-per-minute limit fits only a couple of questions a minute with a 4,500-token prompt. `scripts/smoke_test.py --pause 30` spaces questions out.
- **(Step 2) Country names that hide inside others:** Niger in Nigeria, Guinea in Guinea-Bissau, Sudan in South Sudan, Dominica in Dominican Republic: longest names are matched first, adjectives shortest ending first (PL-022).

---

## 8. Conventions

**Code**
- All paths from `src/emole/config.py`. No `sys.path` edits (the package is installed).
- Every script is a thin wrapper around a function in `src/emole/` (testable, importable).
- `engine.ask()` is the one front door; nothing else calls the model to answer a user.
- The model only writes SQL and sentences. Names, group maths, coverage, notes, greetings and the introduction are code.
- Expected failures stop with one plain sentence, not a traceback.
- Sources are read tolerantly (case, metadata columns) but never guessed (E-56).
- Decision rules that use results are written down before the results are seen (E-48).
- Secrets never appear in a source file, notebook, terminal command, test name, log, screenshot or chat; code says only "key set" or "KEY MISSING".
- Platform pricing, free tiers, model IDs and sources are verified before code is written against them (E-27).

**Git**
- Branch `step-NN-short-description` (close-outs: `step-NNb-closeout`); commits `type: message` (`feat:`, `fix:`, `docs:`, `test:`, `chore:`, `data:`); formatting-only changes in their own commit.
- Pull request per step, CI green before merging, **"Squash and merge"**, tag after merge.

**Documentation**
- No em dashes. Plain words. Explanation before every code block. Full files, never fragments.
- **No zip files (E-55).** Every guide gives each new or changed file in full with its path, marked "New file" or "Replace the whole file", plus a short "what changed" list.
- Every step ends with: the guide (`docs/steps/stepN.md`), this file rewritten in full, new `POST_LOG.md` entries.
- Post evidence goes in `docs/evidence/stepN/`, named after the entry (E-58, E-77).
- The owner's earlier private build is called only "the earlier build" in this public repo.
- When an earlier claim turns out wrong, correct it openly in the next deliverable.

---

## 9. Corrections made

| # | Step | Correction |
|---|---|---|
| 1 | 1 | The first M49 conversion read 246 countries, not 248 (apostrophes). Fixed, and the converter now stops if any entry is missed (PL-007) |
| 2 | 1 | Planning expected air cargo to need the World Bank; OWID publishes it |
| 3 | 1 | Before delivery, unopened links, an unverified region name and an unverified figure were replaced or removed |
| 4 | 1 | The Step 1 download check and cleaning required OWID's exact capitalised header; OWID changed it within a week. Fixed by the owner; tests and the long-term rule added (E-56, PL-014) |
| 5 | 1 | `air_freight_mtkm` was stored a million times too big (OWID publishes tonne-km). Fixed with `scale` (E-59, PL-016) |
| 6 | 1 | The Channel Islands (`CHI`) had no continent or subregion. Added by hand (E-60) |
| 7 | 2 | The planning context said "temperature 0 for SQL" for every provider. For Gemini 3.x that setting is ignored or discouraged by Google, so it is no longer sent to Gemini (E-63, PL-020) |
| 8 | 2 | During the build, two Step 2 bugs were caught before delivery and are recorded as posts: "Nigerian" read as Niger (PL-022), and the safety check rejecting every query that used a macro (PL-023) |

---

## 10. Completed

- [x] Step 1: sources, build, coverage, data dictionary, first real build, close-out, tags `v0.1.0-step1` and `v0.1.1-step1`
- [x] Owner's answers: MIT, World Bank columns, maths exceptions, peers, Middle East list (23 Nov), Immy wording (23 Nov)
- [x] Step 2 code: 13 engine modules, 5 scripts, macros in the database, provider chain with fallback
- [x] Step 2 tests: 147 offline tests passing; ruff clean; secrets scan clean
- [x] Step 2 stand-in run on the real table; wire-level checks of both senders; charts checked by eye
- [x] Prompt measured (about 4,500 tokens, estimate)
- [ ] Owner: Groq and Gemini keys in `.env`; model IDs and limits read from the consoles (Q-13)
- [ ] Owner: rebuild the database (`--offline`), run the tests, chat, the smoke list on Ollama, Groq and Gemini, and the forced failure
- [ ] Owner: PR merged with CI green, tag `v0.2.0-step2`
- [ ] Step 2 close-out: real results into 5.7, post log entries with real times and token counts

---

## 11. Open questions

| # | Question | Status |
|---|---|---|
| Q-01 to Q-03, Q-05 to Q-07 | Licence, World Bank columns, maths exceptions, peers, first year, drops | **Answered** (Step 1) |
| Q-04 | The 16-country Middle East list? | **Answered: approved 23 Nov 2026** (E-42) |
| Q-08 | Should rankings skip territories? | **Answered by E-69:** no, they stay and are named; Step 3 re-checks |
| Q-09 | Store the group rules as DuckDB macros? | **Answered by E-64:** yes, `pop_avg` and `gdp_avg` |
| Q-10 | Historical bloc membership and income groups? | Future version |
| Q-11 | Make Emolé citable (Zenodo DOI at `v1.0.0`; a technical report only if Step 3's evaluation is strong)? | Open, owner to decide later |
| Q-12 | Approve the introduction wording with the nickname? | **Answered: approved 23 Nov 2026** |
| Q-13 | Exact Gemini Flash-Lite model IDs, RPM, TPM and RPD from AI Studio; Groq's free models and limits from its console; keys in `.env` | Open, owner to provide (guide Part 1). Defaults in `config.py` come from Google's and third-party pages read on 23 Nov 2026 |
| Q-14 | Add a code-computed trend summary (first, last, highest, lowest, change) for "how did X change" questions? | Open. Not built in Step 2; proposed for Step 3 once real answers show whether it is needed |
| Q-15 | Raise the World Bank timeout or lower its page size? | Not needed yet |
| Q-16 | Is `llama-3.3-70b-versatile` still the best free Groq model for SQL in the owner's console, or should Step 3 compare a second Groq model? | Open; Step 3 can compare two Groq models in the evaluation |

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

Copy-Item .env.example .env       # then add your Groq and Gemini keys in .env (never in chat)

pytest                             # 147 offline tests
python scripts/build_data.py --from-snapshot   # the database, with the group-maths macros
python scripts/chat.py             # talk to Emolé (Ollama running, or EMOLE_MODE=public with keys)

code docs/PROJECT_STATE.md
```

To refresh the data from the sources: `python scripts/build_data.py --refresh`.
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
| Provider chain | The list of model services tried in order; a busy one is skipped and rests for a while |
| 429 | The web's "too many requests" answer: a free tier's limit was reached |
| Macro | A named formula stored in the database, e.g. `pop_avg(internet_users_pct)` |
| NAME HINTS | The exact codes for the places in a question, found by code and given to the model |
| Instant fix | A certain correction made by code to the model's SQL, with no second model call |
| Stand-in model | A pretend model in the tests that returns scripted SQL, so the engine is tested without keys |
| Thinking tokens | Words a model writes to itself before answering; some providers count them in the output limit |