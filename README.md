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
