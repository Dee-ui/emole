"""catalog.py: measure what is REALLY in the database (the "data facts").

The model cannot see the data. Without facts it guesses which years exist and how a
region is spelled. So every fact here is measured from the database itself, and
re-measured whenever the database file changes: new data needs no retraining.

What is measured:
  - every column's meaning, unit, group rule and years (first, latest, broad-coverage
    latest) from the column_meta table the build wrote
  - every value of the grouping columns (continents, subregions, World Bank regions,
    income groups) with how many countries each has
  - the bloc columns with their member counts
  - every country and territory, with its ISO3 code (for name matching)
"""
from emole import config
from emole.pipeline import executor

GROUPING_COLUMNS = ("continent", "subregion", "wb_region", "income_group")
BLOC_COLUMNS = {"is_ecowas": "ECOWAS", "is_african_union": "African Union", "is_eu": "European Union",
                "is_g20": "G20", "is_middle_east": "Middle East (Emolé's list of 16)"}
REQUIRED_MACROS = ("pop_avg", "gdp_avg")

_cache = {"mtime": None, "facts": None}


class DatabaseOutOfDate(RuntimeError):
    """The database was built before Step 2 (no group-maths macros)."""


def _int(v):
    return None if v is None or v != v else int(v)       # v != v is True only for NaN


def get_facts() -> dict:
    """All facts, re-measured only when the database file changes."""
    mtime = config.DB_PATH.stat().st_mtime if config.DB_PATH.exists() else None
    if _cache["facts"] is not None and _cache["mtime"] == mtime:
        return _cache["facts"]
    con = executor.connect()
    try:
        macros = {r[0] for r in con.execute(
            "SELECT function_name FROM duckdb_functions() WHERE function_type = 'macro'").fetchall()}
        missing = [m for m in REQUIRED_MACROS if m not in macros]
        if missing:
            raise DatabaseOutOfDate(
                f"The database has no {', '.join(missing)} macro: it was built before Step 2. "
                "Rebuild it: python scripts/build_data.py --from-snapshot")
        meta = con.execute("SELECT * FROM column_meta").fetchdf()
        columns = {}
        for r in meta.to_dict("records"):
            columns[r["column"]] = {
                "letter": r["letter"], "description": r["description"], "unit": r["unit"],
                "rule": r["aggregation"], "caveat": r.get("caveat") or None,
                "first_year": _int(r["first_year"]), "latest_year": _int(r["latest_year"]),
                "broad_year": _int(r["latest_broad_year"]),
                "countries_broad": _int(r["countries_broad"]),
            }
        groups = {}
        for col in GROUPING_COLUMNS:
            groups[col] = dict(con.execute(
                f"SELECT {col}, COUNT(DISTINCT iso3) FROM country_year WHERE {col} IS NOT NULL "
                f"GROUP BY 1 ORDER BY 1").fetchall())
        blocs = {col: con.execute(f"SELECT COUNT(DISTINCT iso3) FROM country_year WHERE {col}")
                 .fetchone()[0] for col in BLOC_COLUMNS}
        countries = dict(con.execute(
            "SELECT iso3, any_value(country) FROM country_year GROUP BY 1 ORDER BY 2").fetchall())
        years = con.execute("SELECT MIN(year), MAX(year) FROM country_year").fetchone()
    finally:
        con.close()
    facts = {"columns": columns, "groups": groups, "blocs": blocs, "countries": countries,
             "year_min": int(years[0]), "year_max": int(years[1])}
    _cache.update(mtime=mtime, facts=facts)
    return facts


def column(name: str) -> dict:
    return get_facts()["columns"][name]


def coverage_sentence(col: str) -> str:
    """'Air passengers data runs from 1970 to 2023.' (with the broad year if different)"""
    from emole.pipeline.columns import COLUMNS
    c = column(col)
    label = COLUMNS[col]["label"]
    text = f"{label[0].upper() + label[1:]} data runs from {c['first_year']} to {c['latest_year']}."
    if c["broad_year"] and c["broad_year"] != c["latest_year"]:
        text += (f" {c['latest_year']} has values for only some countries, so rankings and group "
                 f"figures use {c['broad_year']}.")
    return text


def data_summary() -> str:
    """One plain sentence about everything Emolé holds (used in greetings and no-data replies)."""
    f = get_facts()
    return (f"I hold {len(f['columns'])} measures for {len(f['countries'])} countries and "
            f"territories, from {f['year_min']} to {f['year_max']}; each measure has its own "
            "latest year.")


def facts_text() -> str:
    """The DATA FACTS block for the SQL prompt."""
    f = get_facts()
    lines = ["DATA FACTS (measured from the database just now; trust these over anything else):",
             f"- country_year has {len(f['countries'])} countries and territories, years "
             f"{f['year_min']} to {f['year_max']}. Group rows (World, regions) are NOT in the table.",
             "- Columns: name | unit | group rule | years | broad-coverage latest year:"]
    for name, c in f["columns"].items():
        broad = ("" if c["broad_year"] == c["latest_year"]
                 else f" | use {c['broad_year']} for rankings and groups")
        lines.append(f"    {name} | {c['unit']} | {c['rule']} | {c['first_year']}-{c['latest_year']}{broad}")
    for col, values in f["groups"].items():
        shown = ", ".join(f"'{v}' ({n})" for v, n in values.items())
        lines.append(f"- {col} values (countries): {shown}")
    lines.append("- Bloc columns (true/false, CURRENT members applied to every year): "
                 + ", ".join(f"{col} ({n} members)" for col, n in f["blocs"].items()))
    lines.append("- There is NO data outside the years listed for each column.")
    return "\n".join(lines)
