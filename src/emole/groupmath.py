"""groupmath.py: the one correct way to turn country values into a group value.

Emolé never lets the model invent group maths. Every group figure (a region, a bloc,
an income group, "the world") is made from its member countries by ONE of four rules,
read from column_meta (decision E-06 and E-44):

  sum           add up the countries                  (air passengers, population ...)
  pop_weighted  average, each country counted by its population
                (internet %, GDP per person, life expectancy ...)
  gdp_weighted  average, each country counted by the size of its economy
                (GDP growth: weight = gdp_per_capita_ppp x population)
  median        the middle country's value            (inflation)

Why not a plain average? With a plain average, Cape Verde (about half a million
people) would count as much as Nigeria (over 200 million).

Every result also says how many members had data, so answers can add a note such as
"based on 11 of 12 ECOWAS countries with data for 2023". A country counts as
"with data" only if it has the value AND its weight (population, or GDP) that year,
because without the weight it cannot be included in a weighted average.

Two ways to use it:
  group_value(...)      in Python (tests, coverage report, checks)
  sql_expression(...)   the same maths as a DuckDB SQL expression (Step 2's SQL rules
                        and instant fixes). The tests prove both give the same number.
"""
from dataclasses import dataclass, field

import pandas as pd

RULES = ("sum", "pop_weighted", "gdp_weighted", "median")


@dataclass
class GroupResult:
    value: float
    rule: str
    year: int
    n_with_data: int
    n_members: int
    missing: list = field(default_factory=list)

    def note(self, group_name: str = "", world: bool = False) -> str:
        """The plain-English coverage note added by CODE, never by the model."""
        if world:
            return (f"This is the total of countries with data ({self.n_with_data} of "
                    f"{self.n_members}) for {self.year}, so it can differ slightly from "
                    "official world figures.")
        who = f"{group_name} countries" if group_name else "countries"
        return f"Based on {self.n_with_data} of {self.n_members} {who} with data for {self.year}."


def _usable(rows: pd.DataFrame, column: str, rule: str) -> pd.Series:
    ok = rows[column].notna()
    if rule == "pop_weighted":
        ok &= rows["population"].notna() & (rows["population"] > 0)
    elif rule == "gdp_weighted":
        ok &= (rows["population"].notna() & (rows["population"] > 0)
               & rows["gdp_per_capita_ppp"].notna() & (rows["gdp_per_capita_ppp"] > 0))
    return ok


def group_value(df: pd.DataFrame, column: str, rule: str, year: int, members=None) -> GroupResult:
    """Compute a group value for one column and one year.

    df       rows of country_year (any years; this function picks `year`)
    members  iso3 codes in the group; None = every country in df ("the world")
    """
    if rule not in RULES:
        raise ValueError(f"Unknown rule {rule!r}; use one of {RULES}")
    members = sorted(set(df["iso3"]) if members is None else set(members))
    rows = df[(df["year"] == year) & (df["iso3"].isin(members))]
    ok = _usable(rows, column, rule)
    use = rows[ok]
    have = set(use["iso3"])
    missing = [m for m in members if m not in have]
    if use.empty:
        value = None
    elif rule == "sum":
        value = float(use[column].sum())
    elif rule == "median":
        value = float(use[column].median())
    else:
        w = use["population"] if rule == "pop_weighted" else use["population"] * use["gdp_per_capita_ppp"]
        value = float((use[column] * w).sum() / w.sum())
    return GroupResult(value=value, rule=rule, year=year, n_with_data=len(have),
                       n_members=len(members), missing=missing)


def sql_expression(column: str, rule: str) -> str:
    """The same maths as one DuckDB aggregate expression, to use inside
    SELECT ... FROM country_year WHERE <group filter> AND year = <year>.
    The FILTER clauses make sure the value and its weight come from the SAME rows."""
    c = column
    if rule == "sum":
        return f"SUM({c})"
    if rule == "median":
        return f"MEDIAN({c})"
    if rule == "pop_weighted":
        return (f"SUM({c} * population) FILTER (WHERE {c} IS NOT NULL AND population > 0) / "
                f"SUM(population) FILTER (WHERE {c} IS NOT NULL AND population > 0)")
    if rule == "gdp_weighted":
        cond = f"{c} IS NOT NULL AND population > 0 AND gdp_per_capita_ppp > 0"
        return (f"SUM({c} * population * gdp_per_capita_ppp) FILTER (WHERE {cond}) / "
                f"SUM(population * gdp_per_capita_ppp) FILTER (WHERE {cond})")
    raise ValueError(f"Unknown rule {rule!r}; use one of {RULES}")


def sql_coverage(column: str, rule: str) -> str:
    """How many countries were used (to fill 'based on N of M countries')."""
    if rule == "pop_weighted":
        return f"COUNT(*) FILTER (WHERE {column} IS NOT NULL AND population > 0)"
    if rule == "gdp_weighted":
        return (f"COUNT(*) FILTER (WHERE {column} IS NOT NULL AND population > 0 "
                "AND gdp_per_capita_ppp > 0)")
    return f"COUNT({column})"
