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
