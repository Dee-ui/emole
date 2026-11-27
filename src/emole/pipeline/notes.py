"""notes.py: the sentences that CODE adds to an answer (never the model).

  coverage   every group figure says how many member countries had data, e.g.
             "Based on 16 of 17 Western Africa countries with data for 2024
             (population-weighted average)." World figures are labelled
             "total of countries with data" (decision E-05).
  aviation   any answer using an aviation column says it counts airlines REGISTERED
             in the country, not traffic at its airports (decision E-09).
  latest     a year asked for after a column's last year gets "Air passengers data
             ends in 2023."

The counts come from groupmath.group_value, the same helper the tests and the
coverage report use, so the note and the number always agree on who was included.
"""
import re

import pandas as pd

from emole import groupmath
from emole.pipeline import catalog, checks, executor
from emole.pipeline.columns import AVIATION, COLUMNS

RULE_WORDS = {"sum": "", "pop_weighted": " (population-weighted average)",
              "gdp_weighted": " (weighted by the size of each economy)",
              "median": " (the median country's value)"}
AVIATION_NOTE = ("Aviation figures count airlines registered in a country, not traffic at its "
                 "airports.")
MAX_GROUPS_LISTED = 8


def _result_columns(df) -> list:
    """Metric columns in the result, including <column>_per_person."""
    known = catalog.get_facts()["columns"]
    out = []
    for c in df.columns:
        base = c[:-len("_per_person")] if str(c).endswith("_per_person") else c
        if base in known:
            out.append((c, base, str(c).endswith("_per_person")))
    return out


def _members(column: str, value) -> list:
    if value is True:
        where, params = f"{column}", []
    elif isinstance(value, tuple):
        where, params = f"{column} IN ({', '.join('?' for _ in value)})", list(value)
    else:
        where, params = f"{column} = ?", [value]
    return executor.query(f"SELECT DISTINCT iso3 FROM country_year WHERE {where}", params)["iso3"].tolist()


def coverage_notes(sql: str, df, res) -> list:
    if not checks.across_countries(sql) or df is None or "year" not in df.columns:
        return []
    cols = _result_columns(df)
    if not cols:
        return []
    years = sorted({int(y) for y in df["year"].dropna().unique()})
    base_cols = sorted({b for _, b, _ in cols})
    extra = "".join(f", {c}" for c in base_cols if c not in ("population", "gdp_per_capita_ppp"))
    data = executor.query(f"SELECT iso3, year, population, gdp_per_capita_ppp{extra} FROM country_year "
                          f"WHERE year IN ({', '.join(str(y) for y in years)})")

    # Which groups? 1) the result lists groups (GROUP BY continent AS group_name ...),
    # 2) one group named in the question, 3) otherwise all countries ("the world").
    groups = []
    gb = checks._group_by(sql)
    by_col = next((g for g in checks.GROUPING if g in gb), None)
    if by_col and "group_name" in df.columns:
        for v in df["group_name"].dropna().unique():
            groups.append((str(v), _members(by_col, v), False))
    elif res.groups:
        p = res.groups[0]
        groups.append((p.name, _members(p.column, p.value), False))
    else:
        groups.append(("", None, True))

    notes = []
    for _shown, base, per_person in cols:
        rule = "pop_weighted" if per_person else catalog.column(base)["rule"]
        if per_person:                                   # needs the total AND population
            data["_pp"] = data[base] / data["population"]
            column = "_pp"
        else:
            column = base
        parts = []
        for name, members, world in groups:
            counts = [groupmath.group_value(data, column, rule, y, members) for y in years]
            counts = [c for c in counts if c.n_members]
            if not counts:
                continue
            lo, hi = min(c.n_with_data for c in counts), max(c.n_with_data for c in counts)
            n_members = counts[0].n_members
            parts.append((name, lo, hi, n_members, world))
        if not parts:
            continue
        label = COLUMNS.get(base, {}).get("label", base)
        how = RULE_WORDS[rule]
        when = f"for {years[0]}" if len(years) == 1 else "in each year"
        if len(parts) == 1:
            name, lo, hi, m, world = parts[0]
            count = f"{lo}" if lo == hi else f"{lo} to {hi}"
            if world:
                kind = "total" if rule == "sum" else "average"
                notes.append(f"The {label} figure is the {kind} of countries with data ({count} of {m}) "
                             f"{when}{how}, so it can differ slightly from official world figures.")
            else:
                notes.append(f"The {label} figure is based on {count} of {m} {name} countries with "
                             f"data {when}{how}.")
        else:
            listed = ", ".join(f"{n} {lo if lo == hi else f'{lo}-{hi}'} of {m}"
                               for n, lo, hi, m, _ in parts[:MAX_GROUPS_LISTED])
            more = "" if len(parts) <= MAX_GROUPS_LISTED else " (more in the table)"
            notes.append(f"Countries with {label} data {when}{how}: {listed}{more}.")
    return notes


def aviation_note(sql: str) -> list:
    return [AVIATION_NOTE] if any(c in AVIATION for c in checks.metric_columns(sql)) else []


def latest_notes(question: str, sql: str) -> list:
    asked = [int(y) for y in re.findall(r"\b(19[7-9]\d|20\d\d)\b", question)]
    if not asked:
        return []
    out = []
    for c in checks.metric_columns(sql):
        latest = catalog.column(c)["latest_year"]
        if max(asked) > latest:
            label = COLUMNS.get(c, {}).get("label", c)
            out.append(f"{label[0].upper() + label[1:]} data ends in {latest}.")
    return out


def all_notes(question: str, sql: str, df: pd.DataFrame, res) -> list:
    return coverage_notes(sql, df, res) + latest_notes(question, sql) + aviation_note(sql)
