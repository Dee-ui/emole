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
