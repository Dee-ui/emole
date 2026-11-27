"""schema.py: the plain-English description of country_year that goes into the SQL prompt.

It is built from the column_meta table (meaning, unit, group rule, caveat) that the
data build wrote, so it can never disagree with the data. The words people use for
each measure come from columns.py. Which YEARS each column has is not written here:
that is measured live by catalog.py (DATA FACTS).
"""
from emole.pipeline import catalog
from emole.pipeline.columns import COLUMNS

IDENTITY_COLUMNS = """  country           TEXT     the country or territory's name, e.g. 'Nigeria'
  iso3              TEXT     its ISO 3-letter code, e.g. 'NGA'. Filter countries with iso3.
  year              INTEGER  the year, e.g. 2023
  continent         TEXT     UN M49 continent: 'Africa', 'Americas', 'Asia', 'Europe', 'Oceania'
  subregion         TEXT     UN M49 subregion, e.g. 'Western Africa', 'Eastern Asia', 'South America'
  wb_region         TEXT     World Bank region, e.g. 'Sub-Saharan Africa'
  income_group      TEXT     World Bank income group (CURRENT, applied to every year):
                             'low', 'lower-middle', 'upper-middle', 'high'
  is_ecowas         BOOLEAN  member of ECOWAS today (12 members)
  is_african_union  BOOLEAN  member of the African Union today (55 members)
  is_eu             BOOLEAN  member of the European Union today (27 members)
  is_g20            BOOLEAN  one of the 19 G20 member countries
  is_middle_east    BOOLEAN  in Emolé's Middle East list (16 countries)"""


def get_schema_prompt() -> str:
    facts = catalog.get_facts()
    lines = ["TABLE: country_year  (one row = one country or territory in one year)",
             "It holds ONLY countries and territories. There are no rows for the world, regions or",
             "groups: every group figure is computed from member countries with the group rules.",
             "", "Identity and grouping columns:", IDENTITY_COLUMNS, "",
             "Measures (name | meaning | unit | group rule | also called):"]
    for name, c in facts["columns"].items():
        words = ", ".join(COLUMNS[name]["words"][:4]) if name in COLUMNS else ""
        lines.append(f"  {name} | {c['description']} | {c['unit']} | {c['rule']} | {words}")
    lines += ["",
              "Notes:",
              "  - Aviation columns (air_passengers, air_departures, air_freight_mtkm) count airlines",
              "    REGISTERED in the country, not traffic at its airports.",
              "  - Each measure has its own latest year (see DATA FACTS). A missing value is NULL.",
              "  - Group rules: sum = add up; pop_weighted = pop_avg(column);",
              "    gdp_weighted = gdp_avg(column); median = MEDIAN(column)."]
    return "\n".join(lines)
