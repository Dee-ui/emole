# Emolé coverage report

Generated 2026-11-15 by `python scripts/coverage_report.py` from `data/emole.duckdb` (13,328 rows, 238 countries and territories, years 1970-2025).

**How to read it.** `latest` is the newest year with any data. `broad` is the newest year in which at least 80% of the column's usual countries report: use it for rankings and group answers. A country's own latest year can be newer.

## 1. Columns

| letter | column | unit | first_year | latest_year | latest_broad_year | countries_latest | countries_broad | aggregation | source | source_id |
|---|---|---|---|---|---|---|---|---|---|---|
| M | air_passengers | passengers | 1970 | 2023 | 2023 | 149 | 149 | sum | owid | air-passengers-carried |
| M | air_departures | departures | 1970 | 2023 | 2023 | 150 | 150 | sum | worldbank | IS.AIR.DPRT |
| M | air_freight_mtkm | million tonne-km | 1970 | 2023 | 2023 | 137 | 137 | sum | owid | air-transport-freight-ton-km |
| M | internet_users_pct | % of population | 1990 | 2025 | 2024 | 10 | 182 | pop_weighted | owid | share-of-individuals-using-the-internet |
| M | mobile_subs_per_100 | subscriptions per 100 people | 1980 | 2024 | 2023 | 151 | 172 | pop_weighted | owid | mobile-cellular-subscriptions-per-100-people |
| O | gdp_per_capita_ppp | international-$ (2021 prices) | 1990 | 2025 | 2025 | 185 | 185 | pop_weighted | owid | gdp-per-capita-worldbank |
| O | gdp_growth_pct | % per year | 1970 | 2025 | 2025 | 186 | 186 | gdp_weighted | worldbank | NY.GDP.MKTP.KD.ZG |
| O | inflation_cpi_pct | % per year | 1970 | 2025 | 2025 | 165 | 165 | median | owid | inflation-of-consumer-prices |
| O | unemployment_pct | % of labour force | 1991 | 2025 | 2025 | 181 | 181 | pop_weighted | owid | unemployment-rate |
| L | life_expectancy_years | years | 1970 | 2023 | 2023 | 237 | 237 | pop_weighted | owid | life-expectancy |
| L | under5_deaths_per_1000 | deaths per 1,000 live births | 1970 | 2024 | 2024 | 196 | 196 | pop_weighted | worldbank | SH.DYN.MORT |
| L | health_spend_per_capita_ppp | current international-$ | 2000 | 2024 | 2023 | 22 | 192 | pop_weighted | owid | annual-healthcare-expenditure-per-capita |
| L | population | people | 1970 | 2025 | 2025 | 217 | 217 | sum | worldbank | SP.POP.TOTL |
| L | urban_pop_pct | % of population | 1970 | 2025 | 2025 | 237 | 237 | pop_weighted | owid | share-of-population-urban |
| E | electricity_access_pct | % of population | 1990 | 2024 | 2024 | 214 | 214 | pop_weighted | owid | share-of-the-population-with-access-to-electricity |
| E | renewables_share_elec_pct | % of electricity generation | 1970 | 2025 | 2024 | 91 | 196 | pop_weighted | owid | share-electricity-renewables |
| E | co2_per_capita_t | tonnes per person | 1970 | 2025 | 2025 | 219 | 219 | pop_weighted | owid | co-emissions-per-capita |

## 2. Flags (rule written before the first real build)

A column is flagged when: fewer than 60% of countries with a population figure have it in its broad year; or Nigeria has no value in its latest 5 years; or a peer misses more than 3 of those years. A flag means review, not drop. Drops are agreed with the owner and recorded in docs/DATA.md.

- **air_freight_mtkm**: peers missing more than 3 of the latest 5 years: Ghana (GHA)

## 3. Nigeria and peers: gaps in each column's latest 5 years

`ok` = all years present. `miss 21,23` = 2021 and 2023 missing. `none` = no value in those years.

| country | air_passengers | air_departures | air_freight_mtkm | internet_users_pct | mobile_subs_per_100 | gdp_per_capita_ppp | gdp_growth_pct | inflation_cpi_pct | unemployment_pct | life_expectancy_years | under5_deaths_per_1000 | health_spend_per_capita_ppp | population | urban_pop_pct | electricity_access_pct | renewables_share_elec_pct | co2_per_capita_t |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Nigeria (NGA) | ok | ok | ok | miss 25 | ok | ok | ok | ok | ok | ok | ok | miss 24 | ok | ok | ok | ok | ok |
| Ghana (GHA) | ok | ok | miss 20,21,22,23 | miss 25 | ok | ok | ok | ok | ok | ok | ok | miss 24 | ok | ok | ok | miss 25 | ok |
| Kenya (KEN) | ok | ok | ok | miss 25 | ok | ok | ok | ok | ok | ok | ok | miss 24 | ok | ok | ok | ok | ok |
| South Africa (ZAF) | ok | ok | ok | miss 25 | ok | ok | ok | ok | ok | ok | ok | miss 24 | ok | ok | ok | ok | ok |
| Egypt (EGY) | ok | ok | ok | miss 25 | ok | ok | ok | ok | ok | ok | ok | miss 24 | ok | ok | ok | ok | ok |
| Ethiopia (ETH) | ok | ok | ok | miss 25 | ok | ok | ok | ok | ok | ok | ok | miss 24 | ok | ok | ok | ok | ok |
| Cote d'Ivoire (CIV) | ok | ok | ok | miss 25 | ok | ok | ok | ok | ok | ok | ok | miss 24 | ok | ok | ok | miss 25 | ok |
| Senegal (SEN) | ok | ok | miss 23 | miss 25 | ok | ok | ok | ok | ok | ok | ok | miss 24 | ok | ok | ok | miss 25 | ok |
| Morocco (MAR) | ok | ok | ok | miss 25 | ok | ok | ok | ok | ok | ok | ok | miss 24 | ok | ok | ok | ok | ok |
| United States (USA) | ok | ok | ok | miss 25 | ok | ok | ok | miss 25 | ok | ok | ok | miss 24 | ok | ok | ok | ok | ok |
| United Kingdom (GBR) | ok | ok | ok | miss 25 | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok |
| India (IND) | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok | miss 24 | ok | ok | ok | ok | ok |
| Brazil (BRA) | ok | ok | ok | miss 25 | ok | ok | ok | ok | ok | ok | ok | miss 24 | ok | ok | ok | ok | ok |
| Indonesia (IDN) | ok | ok | ok | miss 25 | ok | ok | ok | ok | ok | ok | ok | miss 24 | ok | ok | ok | miss 25 | ok |
| China (CHN) | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok | miss 24 | ok | ok | ok | ok | ok |
| Germany (DEU) | ok | ok | ok | miss 25 | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok |
| United Arab Emirates (ARE) | ok | ok | ok | miss 25 | ok | miss 25 | miss 25 | ok | ok | ok | ok | miss 24 | ok | ok | ok | miss 25 | ok |

## 4. Regions, income groups and blocs: members with data in each column's broad year

Membership and income groups are the CURRENT ones, applied to every year.

| group | members | air_passengers | air_departures | air_freight_mtkm | internet_users_pct | mobile_subs_per_100 | gdp_per_capita_ppp | gdp_growth_pct | inflation_cpi_pct | unemployment_pct | life_expectancy_years | under5_deaths_per_1000 | health_spend_per_capita_ppp | population | urban_pop_pct | electricity_access_pct | renewables_share_elec_pct | co2_per_capita_t |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| continent = Africa | 58 | 37/58 | 37/58 | 29/58 | 51/58 | 46/58 | 52/58 | 52/58 | 45/58 | 51/58 | 58/58 | 54/58 | 54/58 | 54/58 | 58/58 | 54/58 | 50/58 | 57/58 |
| continent = Americas | 55 | 24/55 | 24/55 | 23/55 | 34/55 | 29/55 | 34/55 | 35/55 | 29/55 | 33/55 | 55/55 | 37/55 | 35/55 | 46/55 | 55/55 | 46/55 | 41/55 | 49/55 |
| continent = Asia | 51 | 48/51 | 48/51 | 46/51 | 43/51 | 47/51 | 44/51 | 44/51 | 42/51 | 48/51 | 51/51 | 48/51 | 47/51 | 50/51 | 51/51 | 50/51 | 51/51 | 51/51 |
| continent = Europe | 50 | 30/50 | 31/50 | 29/50 | 43/50 | 42/50 | 41/50 | 41/50 | 40/50 | 38/50 | 50/50 | 43/50 | 42/50 | 47/50 | 50/50 | 46/50 | 40/50 | 43/50 |
| continent = Oceania | 23 | 10/23 | 10/23 | 10/23 | 11/23 | 8/23 | 14/23 | 14/23 | 9/23 | 11/23 | 23/23 | 14/23 | 14/23 | 19/23 | 23/23 | 18/23 | 14/23 | 19/23 |
| subregion = Australia and New Zealand | 2 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| subregion = Caribbean | 28 | 5/28 | 5/28 | 4/28 | 13/28 | 10/28 | 13/28 | 13/28 | 10/28 | 11/28 | 28/28 | 15/28 | 13/28 | 22/28 | 28/28 | 22/28 | 17/28 | 23/28 |
| subregion = Central America | 8 | 7/8 | 7/8 | 7/8 | 8/8 | 7/8 | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 |
| subregion = Central Asia | 5 | 5/5 | 5/5 | 5/5 | 4/5 | 4/5 | 5/5 | 5/5 | 3/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| subregion = Eastern Africa | 20 | 12/20 | 12/20 | 10/20 | 16/20 | 17/20 | 16/20 | 16/20 | 14/20 | 16/20 | 20/20 | 18/20 | 18/20 | 18/20 | 20/20 | 18/20 | 17/20 | 20/20 |
| subregion = Eastern Asia | 8 | 7/8 | 7/8 | 7/8 | 6/8 | 6/8 | 6/8 | 6/8 | 6/8 | 7/8 | 8/8 | 5/8 | 4/8 | 7/8 | 8/8 | 7/8 | 8/8 | 8/8 |
| subregion = Eastern Europe | 10 | 8/10 | 8/10 | 8/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 9/10 | 10/10 | 10/10 | 9/10 | 10/10 | 10/10 | 10/10 | 9/10 | 10/10 |
| subregion = Melanesia | 5 | 4/5 | 4/5 | 4/5 | 3/5 | 3/5 | 4/5 | 4/5 | 4/5 | 5/5 | 5/5 | 4/5 | 4/5 | 5/5 | 5/5 | 5/5 | 4/5 | 5/5 |
| subregion = Micronesia | 7 | 3/7 | 3/7 | 3/7 | 5/7 | 2/7 | 5/7 | 5/7 | 1/7 | 1/7 | 7/7 | 5/7 | 5/7 | 7/7 | 7/7 | 7/7 | 3/7 | 5/7 |
| subregion = Middle Africa | 9 | 6/9 | 6/9 | 5/9 | 9/9 | 7/9 | 9/9 | 9/9 | 7/9 | 9/9 | 9/9 | 9/9 | 9/9 | 9/9 | 9/9 | 9/9 | 7/9 | 9/9 |
| subregion = Northern Africa | 7 | 6/7 | 6/7 | 6/7 | 5/7 | 4/7 | 6/7 | 6/7 | 5/7 | 5/7 | 7/7 | 6/7 | 6/7 | 6/7 | 7/7 | 6/7 | 6/7 | 6/7 |
| subregion = Northern America | 5 | 2/5 | 2/5 | 2/5 | 2/5 | 2/5 | 2/5 | 2/5 | 1/5 | 2/5 | 5/5 | 2/5 | 2/5 | 4/5 | 5/5 | 4/5 | 4/5 | 5/5 |
| subregion = Northern Europe | 14 | 6/14 | 7/14 | 7/14 | 10/14 | 10/14 | 10/14 | 10/14 | 10/14 | 10/14 | 14/14 | 10/14 | 10/14 | 12/14 | 14/14 | 12/14 | 10/14 | 11/14 |
| subregion = Polynesia | 9 | 1/9 | 1/9 | 1/9 | 1/9 | 1/9 | 3/9 | 3/9 | 2/9 | 3/9 | 9/9 | 3/9 | 3/9 | 5/9 | 9/9 | 4/9 | 5/9 | 7/9 |
| subregion = South America | 14 | 10/14 | 10/14 | 10/14 | 11/14 | 10/14 | 11/14 | 12/14 | 10/14 | 12/14 | 14/14 | 12/14 | 12/14 | 12/14 | 14/14 | 12/14 | 12/14 | 13/14 |
| subregion = South-eastern Asia | 11 | 10/11 | 10/11 | 9/11 | 9/11 | 11/11 | 11/11 | 11/11 | 10/11 | 11/11 | 11/11 | 11/11 | 11/11 | 11/11 | 11/11 | 11/11 | 11/11 | 11/11 |
| subregion = Southern Africa | 5 | 4/5 | 4/5 | 2/5 | 5/5 | 5/5 | 5/5 | 5/5 | 4/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 4/5 | 5/5 |
| subregion = Southern Asia | 9 | 9/9 | 9/9 | 9/9 | 9/9 | 9/9 | 8/9 | 8/9 | 8/9 | 9/9 | 9/9 | 9/9 | 9/9 | 9/9 | 9/9 | 9/9 | 9/9 | 9/9 |
| subregion = Southern Europe | 17 | 9/17 | 9/17 | 7/17 | 14/17 | 13/17 | 14/17 | 14/17 | 13/17 | 12/17 | 17/17 | 15/17 | 14/17 | 16/17 | 17/17 | 15/17 | 14/17 | 14/17 |
| subregion = Western Africa | 17 | 9/17 | 9/17 | 6/17 | 16/17 | 13/17 | 16/17 | 16/17 | 15/17 | 16/17 | 17/17 | 16/17 | 16/17 | 16/17 | 17/17 | 16/17 | 16/17 | 17/17 |
| subregion = Western Asia | 18 | 17/18 | 17/18 | 16/18 | 15/18 | 17/18 | 14/18 | 14/18 | 15/18 | 16/18 | 18/18 | 18/18 | 18/18 | 18/18 | 18/18 | 18/18 | 18/18 | 18/18 |
| subregion = Western Europe | 9 | 7/9 | 7/9 | 7/9 | 9/9 | 9/9 | 7/9 | 7/9 | 7/9 | 7/9 | 9/9 | 8/9 | 9/9 | 9/9 | 9/9 | 9/9 | 7/9 | 8/9 |
| wb_region = East Asia & Pacific | 37 | 27/37 | 27/37 | 26/37 | 26/37 | 25/37 | 31/37 | 31/37 | 25/37 | 29/37 | 37/37 | 30/37 | 29/37 | 37/37 | 37/37 | 36/37 | 31/37 | 34/37 |
| wb_region = Europe & Central Asia | 58 | 39/58 | 40/58 | 38/58 | 51/58 | 50/58 | 50/58 | 50/58 | 47/58 | 47/58 | 57/58 | 52/58 | 51/58 | 58/58 | 57/58 | 56/58 | 50/58 | 53/58 |
| wb_region = Latin America & Caribbean | 42 | 22/42 | 22/42 | 21/42 | 32/42 | 27/42 | 32/42 | 33/42 | 28/42 | 31/42 | 42/42 | 35/42 | 33/42 | 42/42 | 42/42 | 42/42 | 36/42 | 38/42 |
| wb_region = Middle East, North Africa, Afghanistan & Pakistan | 23 | 21/23 | 21/23 | 20/23 | 20/23 | 21/23 | 18/23 | 18/23 | 19/23 | 21/23 | 23/23 | 23/23 | 23/23 | 23/23 | 23/23 | 23/23 | 23/23 | 23/23 |
| wb_region = North America | 3 | 2/3 | 2/3 | 2/3 | 2/3 | 2/3 | 2/3 | 2/3 | 1/3 | 2/3 | 3/3 | 2/3 | 2/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| wb_region = South Asia | 6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |
| wb_region = Sub-Saharan Africa | 48 | 32/48 | 32/48 | 24/48 | 45/48 | 41/48 | 46/48 | 46/48 | 39/48 | 45/48 | 48/48 | 48/48 | 48/48 | 48/48 | 48/48 | 48/48 | 44/48 | 48/48 |
| income_group = high | 86 | 50/86 | 51/86 | 51/86 | 66/86 | 65/86 | 63/86 | 63/86 | 58/86 | 62/86 | 85/86 | 65/86 | 64/86 | 86/86 | 85/86 | 84/86 | 72/86 | 74/86 |
| income_group = low | 25 | 14/25 | 14/25 | 12/25 | 19/25 | 18/25 | 19/25 | 19/25 | 15/25 | 23/25 | 25/25 | 25/25 | 24/25 | 25/25 | 25/25 | 25/25 | 24/25 | 25/25 |
| income_group = lower-middle | 47 | 39/47 | 39/47 | 32/47 | 43/47 | 43/47 | 45/47 | 46/47 | 41/47 | 44/47 | 47/47 | 47/47 | 47/47 | 47/47 | 47/47 | 47/47 | 43/47 | 47/47 |
| income_group = upper-middle | 59 | 46/59 | 46/59 | 42/59 | 54/59 | 46/59 | 58/59 | 58/59 | 51/59 | 52/59 | 59/59 | 59/59 | 57/59 | 59/59 | 59/59 | 58/59 | 54/59 | 59/59 |
| is_ecowas | 12 | 6/12 | 6/12 | 4/12 | 12/12 | 10/12 | 12/12 | 12/12 | 11/12 | 12/12 | 12/12 | 12/12 | 12/12 | 12/12 | 12/12 | 12/12 | 12/12 | 12/12 |
| is_african_union | 55 | 37/55 | 37/55 | 29/55 | 51/55 | 46/55 | 52/55 | 52/55 | 45/55 | 51/55 | 55/55 | 54/55 | 54/55 | 54/55 | 55/55 | 54/55 | 50/55 | 54/55 |
| is_eu | 27 | 22/27 | 23/27 | 23/27 | 27/27 | 27/27 | 27/27 | 27/27 | 27/27 | 27/27 | 27/27 | 27/27 | 27/27 | 27/27 | 27/27 | 27/27 | 27/27 | 27/27 |
| is_g20 | 19 | 19/19 | 19/19 | 19/19 | 19/19 | 19/19 | 19/19 | 19/19 | 17/19 | 19/19 | 19/19 | 19/19 | 19/19 | 19/19 | 19/19 | 19/19 | 19/19 | 19/19 |
| is_middle_east | 16 | 15/16 | 15/16 | 14/16 | 13/16 | 15/16 | 12/16 | 12/16 | 13/16 | 14/16 | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |

## 5. Rows removed during the build

Full list: `data/processed/removed_rows.csv`.

| reason | names | rows |
|---|---|---|
| OWID_ code: OWID group or former country (World, USSR ...) | 16 | 6826 |
| World Bank aggregate (a group row with a 3-letter code) | 44 | 9856 |
| blank code in World Bank file | 5 | 1120 |
| blank code: an OWID group row (region, income group, union) | 66 | 4892 |
| code is not 3 capital letters | 12 | 2795 |
