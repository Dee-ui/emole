# Step 1 close-out: the first real build, fixed and recorded

**Date:** 18 November 2026
**Branch:** `step-01b-closeout` &nbsp; **Tag after merge:** `v0.1.1-step1`
**Time needed:** about 30 to 40 minutes
**Before you start:** your laptop, the project open in VS Code, the `.venv` active, and the raw files you downloaded on 15 November still in `data/raw/` (they are, unless you deleted them).

Sir, this guide closes Step 1 properly before Step 2 starts. Your first real build worked,
and it also found two problems no test could have found. This guide records the build,
fixes the second problem, adds tests for your fix of the first one, and updates the three
project documents.

From this guide on there is **no zip** (decision E-55). Part 4 holds every file you need
to change, in full, with its path. Each file says whether it is a **new file** or a
**replace the whole file**, and lists what changed, so for a small change you can also
edit the lines by hand. Either way, the result must match Part 4 exactly.

---

## Part 0. What changes, in one table

| # | What | Files | Why |
|---|---|---|---|
| 1 | Tests for your OWID format fix | `tests/test_parse.py` | Your fix in `fetch.py` and `parse.py` is already on `main`. Tests make sure no future change undoes it |
| 2 | Air freight unit corrected | `data/sources.yaml`, `src/emole/data/sources.py`, `src/emole/data/build.py`, `tests/test_sources.py`, `tests/test_build.py` | The values were a million times too big |
| 3 | Channel Islands given a region | `data/reference/manual_regions.csv` | `CHI` had no continent or subregion |
| 4 | Rebuilt snapshot and coverage report | `data/processed/*`, `docs/coverage_report.md` | Made by the scripts, not by hand |
| 5 | Evidence folder | `docs/evidence/README.md` (new), your screenshot | A fixed home for post screenshots |
| 6 | Documents | `docs/DATA.md`, `docs/POST_LOG.md`, `docs/PROJECT_STATE.md`, this guide | Record the build, the decisions and the corrections |

Your `src/emole/data/fetch.py` and `src/emole/data/parse.py` are **not** changed. The
versions you merged in commit `6168394` are the current versions.

---

## Part 1. What changed and why

### 1.1 Your OWID fix becomes a permanent rule, with tests (E-56)

Between 8 November (when I checked the sources) and 15 November (your first build), Our
World in Data changed its CSV downloads in two ways: the header row came back in
lowercase (`entity,code,year`), and every file gained an extra column, `owid_region`. The
Step 1 code expected the exact text `Entity,Code,Year`, so it stopped on the first column.
That stop was the right behaviour: it refused to import a file it did not understand.

Your fix matches the three key columns by name without caring about upper or lower case,
and drops any column whose name starts with `owid_` before picking the value column. That
is now the long-term pattern (written in `docs/DATA.md` section 6.1). Being tolerant of
casing and metadata never means guessing: if a file has two real value columns, no key
columns, or is a web page instead of a CSV, the build still stops.

What was missing was a test. Without one, a later edit could quietly undo your fix and
nothing would notice until the next real download. `tests/test_parse.py` gains four tests:

| Test | What it proves |
|---|---|
| `test_new_owid_format_lowercase_header_and_owid_columns` | A file in the new format parses, the real value column is picked (not `owid_region`), and "World" is still removed |
| `test_old_owid_format_still_works` | The capitalised format still works too |
| `test_download_check_ignores_header_case` | The download check accepts the lowercase header. It uses a pretend web response, so it needs no internet |
| `test_download_check_still_stops_on_a_web_page` | If a web page comes back instead of a CSV, the build still stops |

### 1.2 Air freight was a million times too big (E-59)

After your build I read the smallest, middle and largest 2019 value of every column, plus
Nigeria's, to see if the sizes made sense. Sixteen columns looked right. Air freight did
not: the United States showed **42,498,260,000** "million tonne-km". That is far more than
the whole world's air freight. The World Bank shows **42,498** for the same country, year
and indicator code (`IS.AIR.GOOD.MT.K1`).

The reason: the World Bank publishes this series in million tonne-km, and Our World in
Data republishes the same code converted to plain tonne-km. Step 1 took the unit from the
World Bank's definition and never compared it with OWID's actual numbers, because my
workspace could not download the files. That was my mistake, and it is recorded in
`PROJECT_STATE.md` section 9.

The fix adds one optional field to `sources.yaml`, `scale`: every value of that column is
multiplied by it during the build. Air freight gets `scale: 0.000001`. The column keeps
its name and its unit, and its numbers now match the World Bank site that anyone can open
to check. `sources.py` refuses a scale that is zero, negative, text or true/false, and
`build.py` records the scale in `build_info.json` so the conversion is never hidden.

Why not rename the column to plain tonne-km instead? Because million tonne-km is the unit
the World Bank and ICAO publish, so Emolé's answers can be checked against them directly.

### 1.3 The Channel Islands get a region (E-60)

Your build summary said one country had no continent: `CHI`. That is the World Bank's
single code for Jersey and Guernsey together. The UN's M49 list does put the Channel
Islands (code 830) in Northern Europe, but they have no ISO 3-letter code, so the M49 file
could not match them. One line in `manual_regions.csv` fixes it, the same way Taiwan and
Kosovo were added. After the rebuild, the continent and subregion gaps go from 1 to 0.

### 1.4 The flagged air freight column stays (E-57)

The flag rule written before the build fired once: air freight, because Ghana has no value
from 2020 to 2023. You asked me to decide. **I kept the column**, for four reasons:

1. The flag is about one peer, not the column. Nigeria and 15 of the 16 other peers have values.
2. 137 countries report in 2023, its broad-coverage year. That is enough for rankings and world totals.
3. Air freight is one of the three aviation columns that make up "Movement". Dropping it would remove the goods side of the story and leave only passengers.
4. The honest handling already exists: if someone asks about Ghana's recent air freight, Emolé says there is no recent value; group answers show their coverage (for example "based on 4 of 12 ECOWAS countries").

The decision and its reasons are in `docs/DATA.md` section 3.1, as the rule requires.

### 1.5 Immy (E-54)

Emolé gets a nickname, **Immy**. Nothing in Step 1's code changes for this: the identity
text, greetings and name recognition are written in Step 2. The proposed introduction keeps
the fixed first sentence and adds a second:

> "I'm Emolé, an expert on Movement, Output, Life and Energy. You can call me Immy."

She will treat "Emolé", "Emole" and "Immy" (any case) as her own name, so "Hi Immy" gets a
greeting and "Who is Immy?" gets the introduction. Emolé stays the name on the website, the
repo and the posts; Immy is how people may address her. Recorded now so Step 2 builds it in.

### 1.6 Where post screenshots live (E-58)

Every post log entry has an **Evidence** line: the screenshot, chart or log line that proves
the post is true. Step 6 writes the posts from the post log, so the evidence needs one fixed
home. It goes in the repo: `docs/evidence/stepN/PL-0xx_short-name.png`. That way a post can
link to the proof in a public place, and the post log and the image always point at each
other. Videos are too big for Git and stay in a folder outside the project. The rules
(no secrets, no private details, small files) are in `docs/evidence/README.md` (Part 4).

The screenshot I asked for in Step 1 is the **leak test**: you create a file holding a
fake key shaped like a Groq key, try to commit it, and the secrets hook blocks the commit.
The screenshot proves the protection works on your real machine, not just in my workspace.
You already ran it on 15 November and it was blocked (your output showed
`BLOCKED: leak_test.py:1 looks like a Groq API key.`). Step 5 below runs it once more so you
can capture the screen. The key is fake (made from the letters `Z9y8X7w6V5` repeated), so
the screenshot is safe to publish.

---

## Part 2. Steps in order

Run every command from the project folder in PowerShell, with the `.venv` active (you see
`(.venv)` at the start of the line). Run commands **one at a time**: last time several
commands pasted together ran into each other.

### Step 1. Start from the latest `main` and make the branch

```powershell
cd "C:\Users\Dauda Agbonoga\Documents\Projects\Project Emole"
.\.venv\Scripts\Activate.ps1
git switch main
git pull
git switch -c step-01b-closeout
```

Why: the close-out starts from exactly what is merged on GitHub, and lives on its own branch
so it gets its own pull request and CI run.

### Step 2. Create and replace the files

Work through Part 4 from top to bottom. For each file:

- **Replace the whole file:** open it in VS Code, select all (`Ctrl + A`), paste the Part 4 contents, save (`Ctrl + S`).
- **New file:** create it at the exact path (in VS Code: right-click the folder, "New File"), paste, save.

Create the two new folders first:

```powershell
New-Item -ItemType Directory -Force docs\evidence\step1
```

Save **this guide** as `docs/steps/step1_closeout.md` too.

### Step 3. Run the tests

```powershell
pytest
ruff check .
```

You should see **62 passed** and `All checks passed!`. Why: 51 tests were there before; the
close-out adds 11 (4 for the OWID format, 6 for `scale`, 1 for the Channel Islands). If
anything fails, stop and send me the full output.

### Step 4. Rebuild with the saved files, then check two numbers

```powershell
python scripts/build_data.py --offline
```

`--offline` means "never download; use the newest saved copy of every file". You downloaded
everything on 15 November, so this rebuild uses the same data as your first build, only
with the new `scale` and the Channel Islands line. It should take well under a minute.

What should change in the printed summary, compared with 15 November:

- `Grouping gaps`: `continent: 0` and `subregion: 0` (before: 1, `CHI`). `wb_region` and `income_group` stay at 21.
- Everything else (13,328 rows, 238 countries, 1970 to 2025, every latest and broad year, every removed-row count) stays the same.

Now check the two fixes directly:

```powershell
python -c "import duckdb; c=duckdb.connect('data/emole.duckdb', read_only=True); d=c.sql('select iso3, year, air_freight_mtkm, continent, subregion from country_year where year = 2019').df(); print(d[d.iso3.isin(['USA','NGA','CHI'])].to_string(index=False))"
```

Expected: `USA` about `42498.26` (pandas may print it as `4.249826e+04`), `NGA` about `1.84`,
and `CHI` with `Europe` and `Northern Europe`.

Then refresh the coverage report:

```powershell
python scripts/coverage_report.py
```

In `docs/coverage_report.md`, section 4, `continent = Europe` should now show **51** members
(was 50) and `subregion = Northern Europe` **15** (was 14). The flag in section 2 (air
freight, Ghana) stays: the rule is unchanged, and the decision to keep the column is
recorded in `DATA.md`.

### Step 5. The leak test, for the screenshot

Nothing is staged yet, so the fake file is the only thing in the commit attempt. Run these
**one at a time**:

```powershell
python -c "open('leak_test.py', 'w').write('KEY = ' + chr(39) + 'gsk' + '_' + 'Z9y8X7w6V5' * 5 + chr(39) + chr(10))"
```

```powershell
git add leak_test.py
```

```powershell
git commit -m "test: this must be blocked"
```

You should see `block token-shaped secrets ... Failed` and
`BLOCKED: leak_test.py:1 looks like a Groq API key.` Take the screenshot now: press
`Win + Shift + S`, drag around the terminal lines from `git commit` down to the `BLOCKED`
message, then paste into Paint or open the Snipping Tool notification and save it as:

`docs\evidence\step1\PL-011_secret-blocked.png`

Check the image before saving: only the terminal, no other windows, no notifications. Then
clean up, one line at a time:

```powershell
git restore --staged leak_test.py
```

```powershell
Remove-Item leak_test.py
```

```powershell
git status
```

`leak_test.py` must not appear in `git status`.

### Step 6. Commit in small, clear pieces

```powershell
git add tests/test_parse.py
git commit -m "test: cover the new OWID csv format"
```

```powershell
git add data/sources.yaml data/reference/manual_regions.csv src/emole/data/sources.py src/emole/data/build.py tests/test_sources.py tests/test_build.py
git commit -m "fix: scale air freight to million tonne-km and give the Channel Islands a region"
```

```powershell
git add data/processed docs/coverage_report.md
git commit -m "data: rebuild the snapshot with the close-out fixes"
```

```powershell
git add docs/DATA.md docs/POST_LOG.md docs/PROJECT_STATE.md docs/evidence docs/steps/step1_closeout.md
git commit -m "docs: close out step 1 with the first real build"
```

Each commit runs the secrets check and ruff first. All four should pass.

```powershell
git push -u origin step-01b-closeout
```

### Step 7. Pull request, CI, merge, tag

1. Open https://github.com/Dee-ui/emole. GitHub shows a yellow bar "step-01b-closeout had recent pushes": click **Compare & pull request**.
2. Title: `Step 1 close-out: first real build, freight unit, Channel Islands`. In the description, paste the table from Part 0. Click **Create pull request**.
3. Wait for the CI check to turn green (about a minute).
4. Click the small arrow next to the merge button and choose **Squash and merge** (last time the PR used a plain merge commit; squash keeps `main` to one commit per step). Confirm.
5. Back in PowerShell:

```powershell
git switch main
git pull
git tag -a v0.1.1-step1 -m "Step 1 close-out: first real build recorded, freight unit fixed"
git push origin v0.1.1-step1
```

---

## Part 3. What I need from you

1. **The summary printed by `python scripts/build_data.py --offline`** (Step 4), and the output of the two-number check. I will confirm section 5.3 of `PROJECT_STATE.md` against it.
2. **Confirmation** that the PR was squash-merged with CI green and `v0.1.1-step1` was pushed.
3. **Your answer on the Middle East list** (Q-04): Bahrain, Egypt, Iran, Iraq, Israel, Jordan, Kuwait, Lebanon, Oman, Palestine, Qatar, Saudi Arabia, Syria, Turkiye, United Arab Emirates, Yemen. Yes, or which to add or remove.
4. **Your approval of the introduction** with the nickname (Part 1.5), or your preferred wording.
5. The Step 2 prerequisites in my reply (keys in `.env`, model IDs and limits), when you are ready to start Step 2.

You do not need to send me the screenshot. It is saved in the repo and the post log points at it.

---

## Part 4. Every new or changed file, in full

Generated from the exact files that passed the tests (62 passed, ruff clean).

### 4.1 `data/sources.yaml`

**Replace the whole file.** What changed:

- In the comment block at the top, two new lines explain the optional `scale` field (after the `value_column` line).
- In the `air_freight_mtkm` entry, three new lines after `caveat: aviation`: a two-line comment and `scale: 0.000001`.

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
#   scale         optional: multiply every value by this to turn the source's unit into ours
#                 (default 1). Used when a source changes the unit, never to round or adjust.

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
    # OWID republishes this series in plain tonne-km (USA 2019: 42,498,260,000), a million
    # times the World Bank's own unit (USA 2019: 42,498). Found on the first real build.
    scale: 0.000001
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

### 4.2 `data/reference/manual_regions.csv`

**Replace the whole file.** What changed:

- One new last line for `CHI`, the Channel Islands.

```text
iso3,name,continent,subregion,reason
TWN,Taiwan,Asia,Eastern Asia,"Not listed separately in UN M49; placed in its geographic subregion, Eastern Asia"
XKX,Kosovo,Europe,Southern Europe,"Not in UN M49; placed with its neighbours in Southern Europe (OWID code OWID_KOS, World Bank code XKX)"
CHI,Channel Islands,Europe,Northern Europe,"World Bank code for Jersey and Guernsey together; UN M49 lists the Channel Islands (code 830, no ISO code) in Northern Europe"
```

### 4.3 `src/emole/data/sources.py`

**Replace the whole file.** What changed:

- In `load_sources`, three new lines after the `source must be owid or worldbank` check: `scale` must be a positive number.

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
        scale = c.get("scale", 1)
        if isinstance(scale, bool) or not isinstance(scale, (int, float)) or scale <= 0:
            raise SourceListError(f"{name}: scale must be a positive number (it multiplies every value)")
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

### 4.4 `src/emole/data/build.py`

**Replace the whole file.** What changed:

- In `build_table`, four new lines just before `in_range = ...`: multiply the values by `scale` when it is not 1, and record it in `info`.

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
        scale = c.get("scale", 1)
        if scale != 1:                              # change the source's unit to ours (see sources.yaml)
            rows = rows.assign(value=rows["value"] * scale)
            info["scale"] = scale
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

### 4.5 `tests/test_parse.py`

**Replace the whole file.** What changed:

- Four new tests at the end, with a small sample of the new OWID format (`NEW_OWID_FORMAT`) and a pretend web response (`_FakeResponse`).

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


# OWID changed its CSV download between the source check (8 Nov 2026) and the first real
# build (15 Nov 2026): a lowercase header and an extra owid_region column (PL-014).
NEW_OWID_FORMAT = (
    "entity,code,year,is_air_psgr,owid_region\n"
    "Nigeria,NGA,2023,110,Africa\n"
    "Ghana,GHA,2023,40,Africa\n"
    "World,OWID_WRL,2023,999,\n"
)


def test_new_owid_format_lowercase_header_and_owid_columns(tmp_path):
    path = tmp_path / "owid_new__2026-11-15.csv"
    path.write_text(NEW_OWID_FORMAT, encoding="utf-8")
    rows, removed, info = parse_owid(path, "air_passengers")
    assert info["value_column"] == "is_air_psgr"            # owid_region was dropped, not picked
    assert set(rows["iso3"]) == {"NGA", "GHA"}
    assert "World" in set(removed["entity"])


def test_old_owid_format_still_works():
    rows, _, _ = parse_owid(RAW / "owid_test-air__2026-01-01.csv", "air_passengers")
    assert len(rows) > 0                                    # capitalised Entity,Code,Year


class _FakeResponse:
    def __init__(self, text):
        self.text, self.content = text, text.encode("utf-8")


def test_download_check_ignores_header_case(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch, "get", lambda url, session=None: _FakeResponse(NEW_OWID_FORMAT))
    path = fetch.fetch_owid("test-new", raw_dir=tmp_path)
    assert path.exists() and path.name.startswith("owid_test-new__")


def test_download_check_still_stops_on_a_web_page(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch, "get", lambda url, session=None: _FakeResponse("<!DOCTYPE html><html>"))
    with pytest.raises(fetch.DownloadError, match="expected CSV"):
        fetch.fetch_owid("test-broken", raw_dir=tmp_path)
```

### 4.6 `tests/test_sources.py`

**Replace the whole file.** What changed:

- Three new tests at the end (one of them runs 4 times): freight is scaled, a bad `scale` is refused, the Channel Islands have a continent.

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


def test_freight_is_scaled_to_million_tonne_km():
    freight = next(c for c in load_sources() if c["column"] == "air_freight_mtkm")
    assert freight["unit"] == "million tonne-km"
    assert freight["scale"] == pytest.approx(1e-6)


@pytest.mark.parametrize("bad", [0, -1, "1e-6", True])
def test_scale_must_be_a_positive_number(tmp_path, bad):
    text = (config.SOURCES_FILE.read_text(encoding="utf-8")
            .replace("scale: 0.000001", f"scale: {bad!r}" if isinstance(bad, str) else f"scale: {bad}"))
    path = tmp_path / "sources.yaml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(SourceListError, match="scale"):
        load_sources(path)


def test_channel_islands_has_a_continent():
    from emole.data.groups import load_regions
    regions = load_regions().set_index("iso3")
    assert regions.loc["CHI", "continent"] == "Europe"
    assert regions.loc["CHI", "subregion"] == "Northern Europe"
```

### 4.7 `tests/test_build.py`

**Replace the whole file.** What changed:

- `import pytest` added at the top; one new test at the end: `scale` changes only its own column and is recorded.

```python
"""The whole build on the fixtures: right rows, right values, groups filled, files written."""
import duckdb
import pandas as pd
import pytest

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


def test_scale_changes_the_unit_and_is_recorded():
    from emole import config
    from emole.data.build import build_table, collect_files
    from emole.data.sources import load_sources
    sources = load_sources(SOURCES)
    files = collect_files(sources, RAW, refresh=False, offline=True)
    plain, _, _, _ = build_table(sources, files, config.REFERENCE_DIR, 1970, 2026)
    scaled_sources = [dict(c, scale=0.001) if c["column"] == "air_passengers" else c for c in sources]
    scaled, _, infos, _ = build_table(scaled_sources, files, config.REFERENCE_DIR, 1970, 2026)
    p = plain.set_index(["iso3", "year"])
    s = scaled.set_index(["iso3", "year"])
    before = p.loc[("NGA", 2023), "air_passengers"]
    assert s.loc[("NGA", 2023), "air_passengers"] == pytest.approx(before * 0.001)
    assert s.loc[("NGA", 2023), "population"] == p.loc[("NGA", 2023), "population"]   # others untouched
    assert infos["air_passengers"]["scale"] == 0.001
```

### 4.8 `docs/evidence/README.md`

**New file.** What changed:

- The rules for post evidence (E-58).

````markdown
# Evidence for the post log

Screenshots, small charts and short clips that prove a `docs/POST_LOG.md` entry
(decision E-58). Step 6 writes the LinkedIn and X posts from the post log and links
here, so every claim in a post has its proof in the repo.

## Where files go

```
docs/evidence/
  step1/
    PL-011_secret-blocked.png
  step2/
    PL-0xx_short-name.png
```

- One folder per step: `stepN/`.
- Name every file after its post log entry: `PL-<number>_<two-to-four-words>.png`.
- If one entry needs several images, add a letter: `PL-016a_...`, `PL-016b_...`.
- Write the path in the entry's **Evidence** line, so the two always point at each other.

## Rules before you save a file here

This folder is public. Check every image before you commit it.

1. **No secrets.** No real API key, password, token or `.env` content, even partly hidden. A fake test key made by the guide's leak test is fine.
2. **No private details.** No email address, phone number, other people's names, open browser tabs or desktop notifications. Crop to the part that proves the point.
3. **Small files.** PNG for terminal and screen captures, JPG for photos, about 500 KB at most. Use the Windows Snipping Tool (`Win + Shift + S`) and save the cropped area only.
4. **Videos stay out of Git.** Screen recordings and demo clips are large. Keep them in a local folder outside the project, for example `Documents\Emole media\stepN\`, named the same way (`PL-0xx_...mp4`). Only a short GIF under 2 MB may live here.
5. **Real events only.** Capture the actual run. Never stage or edit a screenshot to show a result that did not happen.
````

### 4.9 `docs/DATA.md`

**Replace the whole file.** What changed:

- Top: the first real build line.
- Section 3, `air_freight_mtkm`: the unit note, the scale, and the zeros and coverage quirks.
- New section 3.1: the coverage review (air freight kept, thin newest years).
- Section 4.1: the Channel Islands added by hand. Section 4.2: the 21 territories with no World Bank group.
- Section 6: the `WB_` and `UNSDG_` codes, the UK nations, a table of real removal counts, and new section 6.1 (source formats are not fixed).
- Section 10: a new change-log row.

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

**First real build:** 15 November 2026, on the owner's laptop: 13,328 rows, 238
countries and territories, years 1970 to 2025 (`data/processed/build_info.json`).

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
- **Unit:** million tonne-km, the World Bank's own unit for this code. **Group rule:** sum.
- **Scaled at build time:** OWID publishes this series in plain tonne-km (the United States in 2019: 42,498,260,000), a million times the World Bank's figure for the same code (42,498). `sources.yaml` sets `scale: 0.000001`, so the stored numbers match the World Bank site that anyone can check against. The first real build showed the mismatch; see PL-016.
- **Source:** OWID chart [`air-transport-freight-ton-km`](https://ourworldindata.org/grapher/air-transport-freight-ton-km) (IS.AIR.GOOD.MT.K1). **Producer:** ICAO, via World Bank. **Licence:** CC BY 4.0.
- **Years (as checked):** 1970 to 2023.
- **Quirks:** registered-airlines caveat. The figure grows with distance, so a country whose airlines fly long routes shows more tonne-km for the same cargo weight. Some countries report exactly 0 in some years (25 countries in 2019, Ghana in 2018 and 2019); a 0 is the source's own value, not a gap. Coverage is the thinnest of the three aviation columns (137 countries in 2023; 4 of 12 ECOWAS members).

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

### 3.1 Coverage review of the first real build (15 November 2026)

The pre-registered flag rule (decision E-48) flagged one column. Nothing was dropped.

| Column | Flag | Decision |
|---|---|---|
| `air_freight_mtkm` | A peer misses more than 3 of the latest 5 years: Ghana has no value for 2020 to 2023 (and reported 0 in 2018 and 2019) | **Kept** (E-57). Nigeria and the other 15 peers have values; 137 countries report in 2023, its broad-coverage year. The flag is about one peer, not the column. Answers that compare Ghana's air freight say there is no recent value, and group answers carry the usual coverage note ("based on 4 of 12 ECOWAS countries"). |

Other things the review showed (no flag, but Emolé must handle them):
- **A newest year can be thin.** `internet_users_pct` has 2025 values for only 10 countries (its broad year is 2024, with 182); `health_spend_per_capita_ppp` has 2024 for 22 (broad 2023, 192); `renewables_share_elec_pct` has 2025 for 91 (broad 2024, 196). Rankings and group answers use the broad year (E-47).
- **Every peer misses 2025 internet use** except India and China, and every peer except the UK and Germany misses 2024 health spending: this is publication timing, not a data problem.

---

## 4. Groupings

### 4.1 `continent` and `subregion`: UN M49
- **Source:** the UN Statistics Division's M49 standard, [unstats.un.org/unsd/methodology/m49](https://unstats.un.org/unsd/methodology/m49/). UNSD offers no stable download link (its buttons are made by JavaScript), so the list was taken from the open-source package [`un-m49`](https://github.com/wooorm/un-m49) version 2.2.0 (MIT licence), which holds the same standard. File fingerprint (sha256, first 16 characters): `14faf74380d185db`. Converted by `scripts/make_m49_reference.py` into the committed file `data/reference/un_m49.csv` (248 countries and areas).
- `continent` = the M49 region: Africa, Americas, Asia, Europe, Oceania.
- `subregion` = the most specific M49 level: the intermediate region where M49 has one (Nigeria: Western Africa; Brazil: South America), otherwise the M49 subregion (Egypt: Northern Africa; Saudi Arabia: Western Asia).
- **Added by hand** (`data/reference/manual_regions.csv`), because the M49 file has no row for them: Taiwan (Asia, Eastern Asia), Kosovo (Europe, Southern Europe) and, since the first real build, the Channel Islands (`CHI`, Europe, Northern Europe). `CHI` is the World Bank's single code for Jersey and Guernsey together; M49 lists the Channel Islands (code 830) in Northern Europe but they have no ISO 3-letter code, so the M49 file could not match them.
- Note: in M49, Sudan sits in Northern Africa, and Cyprus and Turkiye in Western Asia (Asia).

### 4.2 `wb_region` and `income_group`: World Bank
- **Source:** the World Bank country list (`api.worldbank.org/v2/country`), downloaded at build time. Licence CC BY 4.0.
- `income_group` values: `low`, `lower-middle`, `upper-middle`, `high`. Empty where the World Bank does not classify a country.
- **Which classification:** the CURRENT one, **FY2027, effective 1 July 2026**, based on 2025 income (Atlas method). Thresholds: low income up to $1,175; lower-middle $1,176 to $4,635; upper-middle $4,636 to $14,375; high above $14,375. In this update Jordan, Micronesia, the Philippines, Sri Lanka and Viet Nam moved up to upper-middle income and Togo moved up to lower-middle; no country moved down. Ethiopia (unclassified the year before) was classified low income and Venezuela lower-middle income.
- **Applied to every year** (rule 2 above). Income groups change over time, so Emolé says "current income group".
- **No World Bank region or income group** (first real build): 21 territories that the World Bank does not list as economies, for example Anguilla (AIA), Bonaire (BES), the Cook Islands (COK), Western Sahara (ESH), Guernsey (GGY), Jersey (JEY), Martinique (MTQ), Reunion (REU). They keep their UN continent and subregion. The full list is printed by the build ("Grouping gaps").

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
- **Codes that are not 3 capital letters.** OWID now also publishes World Bank regions (`WB_SSA`, `WB_EAP` ...) and UN SDG regions (`UNSDG_ENA` ...) as rows. They are not countries and are removed by the same 3-letter rule.
- **England and Wales, Scotland, Northern Ireland** appear in OWID's life expectancy file with a blank code; they are removed (the United Kingdom row stays).
- **Empty values** and **years outside 1970 to the current year** are dropped (counted in `build_info`).

**Measured on the first real build (15 November 2026):**

| Reason | Names | Rows |
|---|---|---|
| OWID `OWID_` code (World, continents, income groups, USSR ...) | 16 | 6,826 |
| World Bank aggregate with a 3-letter code (WLD, SSF, EUU ...) | 44 | 9,856 |
| Blank code in a World Bank file (income-group rows) | 5 | 1,120 |
| Blank code in an OWID file (regions, unions, UK nations) | 66 | 4,892 |
| Code not 3 capital letters (`WB_` and `UNSDG_` regions) | 12 | 2,795 |
| **Total** | **143** | **25,489** |

### 6.1 Source file formats are not fixed (decision E-56)

OWID changed its CSV download between the source check (8 November 2026) and the first
real build (15 November 2026): the header came back in lowercase (`entity,code,year`
instead of `Entity,Code,Year`) and every file gained an extra metadata column,
`owid_region`. The build stopped at once with one clear message instead of importing a
broken column (PL-014).

The long-term pattern, not a one-off patch:
- The three key columns are matched **by name, ignoring upper and lower case**, then renamed to fixed names (`parse.py`, `parse_owid`; the download check in `fetch.py`, `fetch_owid`, ignores case too).
- **Any column whose name starts with `owid_` is OWID's own metadata** and is dropped before the value column is picked, so exactly one value column remains.
- Anything else unexpected (a second value column, a missing key column, a web page instead of a CSV) still **stops the build** with a plain message. Being tolerant of casing and metadata never means guessing which number is the value.
- Tests cover the old format, the new format and a web page returned by mistake (`tests/test_parse.py`).

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
| 18 Nov 2026 | 1 (close-out) | First real build recorded; coverage review (3.1, nothing dropped); air freight scaled from tonne-km to million tonne-km; Channel Islands given a region; 21 territories without a World Bank group listed; new removal reason and real removal counts (6); OWID format note (6.1). |
```

### 4.10 `docs/POST_LOG.md`

**Replace the whole file.** What changed:

- PL-002, PL-010, PL-011 and PL-012: the measured numbers from the real build replace "to be measured"; PL-011's evidence now points at the screenshot.
- New entries PL-014 to PL-018.

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
- **Real numbers:** in the test files, 2 of 2 World Bank aggregates were removed (WLD, SSF) along with 5 OWID group names. On the first real build (15 November 2026), 44 World Bank aggregates were removed (9,856 rows), plus 5 blank-coded World Bank income-group rows (1,120 rows). Across both sources, 143 group names and 25,489 rows were removed in total, and no group row reached `country_year`.
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
- **Real numbers:** in the test files, one column's newest year had 2 of its usual 3 countries, so its broad year moved back one year. On the first real build, 3 of 17 columns had a newest year far thinner than the one before it: internet use had 2025 values for 10 countries against 182 in 2024; health spending had 2024 values for 22 countries against 192 in 2023; renewables had 2025 values for 91 countries against 196 in 2024.
- **Why it matters:** a ranking built on a thin year silently compares the 91 countries that reported, not the world.
- **Evidence:** `src/emole/data/build.py::broad_year`; `tests/test_build.py::test_column_meta_measures_years`; after the real build, section 1 of `docs/coverage_report.md`.
- **Angles:** LinkedIn: "latest" is a definition, not a fact. X: the 91-countries example.

### PL-011: The secrets check caught fake keys hiding in the test cache
- **Step:** 1
- **What happened:** A pre-commit hook now blocks token-shaped strings (Groq, Google, Hugging Face, GitHub and AWS key shapes, private keys, and long secret assignments) before any commit. Its tests build fake keys at run time so the test file itself is clean. A repo-wide test then found the fake keys inside pytest's own cache, because parametrised test names included them. The cache is never committed, but the test names were changed so no fake key is ever written anywhere. In a real Git test, a clean commit passed and a commit holding a fake Groq-shaped key was blocked.
- **Real numbers:** 5 key shapes tested; 1 fake-key commit blocked out of 1 tried in the build workspace, and 1 of 1 again on the owner's Windows laptop on 15 November 2026 ("BLOCKED: leak_test.py:1 looks like a Groq API key."); 0 hits in a scan of the whole repository.
- **Why it matters:** secrets leak through side doors (caches, logs, test names), not just source files. Prevention beats remembering.
- **Evidence:** `scripts/check_no_secrets.py`; `.pre-commit-config.yaml`; `tests/test_secrets.py`; screenshot `docs/evidence/step1/PL-011_secret-blocked.png` (the blocked commit in PowerShell).
- **Angles:** LinkedIn: secrets hygiene for AI apps that use API keys. X: "my secrets scanner found secrets in my test cache".

### PL-012: The data is committed, so the demo never depends on a source being online
- **Step:** 1
- **What happened:** After each build, the finished table is saved as a small Parquet snapshot in the repo, with its column metadata, build info and the list of removed rows. The database can be rebuilt from it with no internet. Docker builds and test answers will use the same numbers even if a source changes or goes offline.
- **Real numbers:** rebuilding from the snapshot was tested (same table, row for row). The first real snapshot holds 13,328 rows for 238 countries and territories (1970 to 2025) in a 1.1 MB Parquet file (1,102,622 bytes).
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

### PL-014: Our World in Data changed its file format, and the build refused to guess
- **Step:** 1 (first real build, 15 November 2026)
- **What happened:** The sources were checked on 8 November. When the owner ran the first real build a week later, it stopped on the very first column with one message: `BUILD STOPPED: OWID chart 'air-passengers-carried' did not return the expected CSV (first characters: 'entity,code,year,is_air_psgr,owid_region ...')`. Two things had changed at OWID: the header row now came back in lowercase (`entity,code,year` instead of `Entity,Code,Year`), and every download carried an extra metadata column, `owid_region`, next to the real value. Every OWID column would have failed the same way. The owner fixed two functions: the download check now ignores upper and lower case, and the cleaning step matches the three key columns by name in any case and drops any column starting with `owid_` before picking the value column. The fix became the long-term rule (decision E-56), and four regression tests now cover the old format, the new format and a web page returned by mistake.
- **Real numbers:** 1 format change, 13 of 17 columns affected (every OWID column), 0 rows imported before the stop, 2 functions changed, 4 tests added. After the fix the build finished: 13,328 rows, 238 countries and territories.
- **Why it matters:** a source can change between the day you check it and the day you run it. A pipeline that stops loudly is far better than one that "works" and quietly loads the wrong column (here, `owid_region` could have been picked as the value).
- **Evidence:** the stop message above (owner's terminal, 15 November 2026); the fix in commit `6168394` (`src/emole/data/fetch.py::fetch_owid`, `src/emole/data/parse.py::parse_owid`); `tests/test_parse.py::test_new_owid_format_lowercase_header_and_owid_columns`; `docs/DATA.md` section 6.1.
- **Angles:** LinkedIn: "fail loudly" as a data engineering habit, with the one-line message as the hero image. X: "A data source changed its header from Entity to entity in one week. My build stopped instead of guessing. Good."

### PL-015: A download timed out halfway, and the rerun picked up where it stopped
- **Step:** 1 (first real build)
- **What happened:** On the first full run, the World Bank's server took too long to answer for under-five mortality (`SH.DYN.MORT`), the 11th of 17 columns. After 3 tries the build stopped with `BUILD STOPPED: Could not download ... (ReadTimeout)`. Because every download is saved with its date in the file name, running the same command again reused the 10 files already saved that day and only downloaded the remaining 7, then finished.
- **Real numbers:** 3 tries with a 60-second limit each before stopping; 10 of 17 files reused on the second run; 0 changes to code or settings needed.
- **Why it matters:** free public APIs are slow sometimes. Saving each finished download means a failure costs one file, not the whole run.
- **Evidence:** the two runs in the owner's terminal (15 November 2026); `src/emole/data/fetch.py` (`raw_path`, `latest_raw`).
- **Angles:** LinkedIn: designing for flaky free APIs. X: "Build died at file 11 of 17. Reran it. It skipped the 10 it already had."

### PL-016: The same indicator code, a million times apart
- **Step:** 1 (review of the first real build)
- **What happened:** A sense check of every column after the first build showed that air freight was far too big: the United States carried 42,498,260,000 in 2019, against a world air freight total of about 220 billion tonne-km that year. The World Bank publishes this indicator (`IS.AIR.GOOD.MT.K1`) in million tonne-km, where the United States shows 42,498. Our World in Data republishes the same code converted to plain tonne-km, a million times bigger, while Emolé's column name and unit said "million". No error was raised anywhere, because nothing was broken: only the unit was wrong. A new optional `scale` field in `sources.yaml` now converts the values at build time (`scale: 0.000001`), and tests check it.
- **Real numbers:** 1 of 17 columns wrong by a factor of 1,000,000. United States 2019: 42,498,260,000 before, 42,498.26 million tonne-km after. Nigeria 2023: 3,141,785 before, 3.14 after. The other 16 columns were checked the same way (smallest, middle and largest value in 2019, plus Nigeria) and looked right.
- **Why it matters:** the same code from two publishers does not guarantee the same unit. Checking magnitudes against one known value catches what no type check or test can.
- **Evidence:** the `scale` line and its comment in `data/sources.yaml`; `docs/DATA.md` section 3 (`air_freight_mtkm`); `tests/test_sources.py::test_freight_is_scaled_to_million_tonne_km`; `tests/test_build.py::test_scale_changes_the_unit_and_is_recorded`.
- **Angles:** LinkedIn: "my data was right in every way except the one that matters", a short lesson on sanity checks. X: "Same indicator code. Two publishers. A factor of one million."

### PL-017: 238 countries in, 143 group names out
- **Step:** 1 (first real build)
- **What happened:** The first real build turned 17 downloads into one table of real countries and territories. It removed every row that described a group instead of a country: OWID continents and income groups, World Bank aggregates, and some surprises, such as World Bank and UN regions that OWID now also publishes (`WB_SSA`, `UNSDG_ENA`), the USSR, and "England and Wales" and "Scotland" in the life expectancy file. Each removal is listed with its reason in `removed_rows.csv`.
- **Real numbers:** 13,328 rows; 238 countries and territories; 1970 to 2025; 25,489 rows removed under 143 group names, in 5 reasons (OWID_ codes 6,826 rows; World Bank aggregates 9,856; blank World Bank codes 1,120; blank OWID codes 4,892; non-standard codes 2,795).
- **Why it matters:** an assistant that ranks countries must only see countries. "World" or "High income" at the top of a ranking is the most common silent error in public data work.
- **Evidence:** `data/processed/removed_rows.csv`; the build summary (owner's terminal); `docs/DATA.md` section 6.
- **Angles:** LinkedIn: a breakdown of what "cleaning" meant in numbers. X: "25,489 rows deleted. Every one of them was a region pretending to be a country."

### PL-018: The pre-registered flag fired once, and the column was kept
- **Step:** 1 (coverage review)
- **What happened:** The flag rule was written before the first build (under 60% coverage, Nigeria missing recent years, or a peer missing more than 3 of the last 5 years). It fired for exactly one column: air freight, because Ghana has no value from 2020 to 2023 (and reported 0 in 2018 and 2019). The rule says a flag means review, not drop. On review the column stayed: Nigeria and 15 of 16 peers have values, and 137 countries report in 2023. Emolé will say when a country has no recent value, and group answers show their coverage (4 of 12 ECOWAS countries report air freight).
- **Real numbers:** 17 columns checked; 1 flagged; 0 dropped. Nigeria had every value in the latest 5 years for 15 of 17 columns (internet use is missing 2025 and health spending 2024, both because those years are not published yet).
- **Why it matters:** a rule written before the results keeps the review honest, and "flag means review" stops a single gap from deleting a useful column.
- **Evidence:** `docs/coverage_report.md` sections 2 and 3; `docs/DATA.md` section 3.1.
- **Angles:** LinkedIn: pre-registration for data decisions. X: "Wrote the rule before seeing the data. It flagged one column. I kept it, and wrote down why."
```

### 4.11 `docs/PROJECT_STATE.md`

**Replace the whole file.** What changed:

- Rewritten in full, as every step requires: decisions E-54 to E-61, the real build in 5.3, the coverage review in 5.4, Git and secrets results in 5.5, corrections 4 to 6, answered and new questions.

````markdown
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
````
