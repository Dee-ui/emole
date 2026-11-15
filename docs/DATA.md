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
