"""checks.py: plain-code checks on the model's SQL before it runs, and instant fixes.

The model writes the SQL; code decides whether it is right for THIS question. Each
check returns None (fine) or a sentence saying what is wrong, written so the model
can fix it in one repair. Where the fix is certain, code makes it at once
("instant fix", no model call) and the fixed SQL must pass the same check again.

  names        every country and group named in the question is in the SQL    (hard)
  group maths  several countries combined into one value must use the column's
               group rule (SUM, pop_avg, gdp_avg, MEDIAN), never AVG()        (hard, fixed in code)
  per person   "per person" on a total (air passengers ...) must divide by
               population                                                     (hard, fixed in code)
  latest year  no year asked: never a year after the column's latest; rankings
               and groups use the broad-coverage year                         (soft, fixed in code)
  rankings     "which countries" must rank countries, not groups              (soft)

Hard checks must pass before the query runs. Soft checks only ask for a repair when a
repair attempt is still left, so they never block an answer.
"""
import re

from emole.groupmath import RULE_FUNCTION
from emole.pipeline import catalog
from emole.pipeline.columns import AVIATION

AGG_FUNCS = ("sum", "avg", "mean", "median", "pop_avg", "gdp_avg")
YEAR_IN_TEXT = re.compile(r"\b(19[7-9]\d|20\d\d)\b")
TIME_WORDS = re.compile(r"\b(since|trend|trends|over time|over the years|history|historically|each year|"
                        r"every year|per year|by year|yearly|annual|change[ds]?|from|between|decade|"
                        r"years|ever|first)\b", re.I)
PER_PERSON = re.compile(r"\bper (person|capita|head|citizen|inhabitant|resident)\b|\bfor each person\b|"
                        r"\bper (1,?000|thousand|100|hundred|million) (people|persons|inhabitants)\b", re.I)
WHICH_COUNTRIES = re.compile(r"\b(which|what|top|bottom|rank|ranking|list)\b[^?]*\bcountr(y|ies)\b", re.I)
GROUPING = ("continent", "subregion", "wb_region", "income_group")


# ---------------------------------------------------------------------------
# small SQL readers (enough for the simple, one-table queries Emolé writes)
# ---------------------------------------------------------------------------
def _strip_strings(sql: str) -> str:
    return re.sub(r"'(?:[^']|'')*'", "''", sql)


def metric_columns(sql: str) -> list:
    cols = catalog.get_facts()["columns"]
    bare = _strip_strings(sql)
    return [c for c in cols if re.search(rf"\b{c}\b", bare)]


def aggregates(sql: str) -> list:
    """[(function, inner text, start, end)] for SUM/AVG/MEDIAN/pop_avg/gdp_avg calls."""
    out = []
    for m in re.finditer(rf"\b({'|'.join(AGG_FUNCS)})\s*\(", sql, re.I):
        depth, i = 1, m.end()
        while i < len(sql) and depth:
            depth += {"(": 1, ")": -1}.get(sql[i], 0)
            i += 1
        out.append((m.group(1), sql[m.end():i - 1].strip(), m.start(), i))
    return out


def _group_by(sql: str) -> str:
    m = re.search(r"\bgroup\s+by\b(.*?)(\border\s+by\b|\bhaving\b|\blimit\b|$)", sql, re.I | re.S)
    return m.group(1).lower() if m else ""


def single_country(sql: str) -> bool:
    """True when the query is about exactly one country (iso3 = 'NGA')."""
    codes = set(re.findall(r"\biso3\s*=\s*'([A-Z]{3})'", sql))
    in_lists = re.findall(r"\biso3\s+in\s*\(([^)]*)\)", sql, re.I)
    for lst in in_lists:
        codes |= set(re.findall(r"'([A-Z]{3})'", lst))
    return len(codes) == 1


def across_countries(sql: str) -> bool:
    """True when one result value combines SEVERAL countries (a group or world figure)."""
    aggs = [a for a in aggregates(sql) if metric_columns(a[1])]
    if not aggs:
        return False
    gb = _group_by(sql)
    if re.search(r"\b(country|iso3)\b", gb) or single_country(sql):
        return False
    return True


def _inner_column(inner: str):
    """'internet_users_pct' -> ('internet_users_pct', False);
    'air_passengers / population' -> ('air_passengers', True); anything else -> (None, False)."""
    inner = inner.strip().strip("()").strip()
    cols = catalog.get_facts()["columns"]
    if inner in cols:
        return inner, False
    m = re.fullmatch(r"(\w+)\s*/\s*population", inner)
    if m and m.group(1) in cols:
        return m.group(1), True
    return None, False


# ---------------------------------------------------------------------------
# NAMES (hard)
# ---------------------------------------------------------------------------
def names_problem(res, sql: str):
    missing = []
    for p in res.countries:
        if f"'{p.iso3}'" not in sql and p.name.lower() not in sql.lower():
            missing.append(f"{p.said} (iso3 = '{p.iso3}')")
    low = sql.lower()
    for p in res.groups:
        if p.column not in low:
            missing.append(f"{p.said} ({p.column})")
        elif isinstance(p.value, str) and f"'{p.value.lower()}'" not in low and "group by" not in low:
            missing.append(f"{p.said} ({p.column} = '{p.value}')")
    if missing:
        return ("The question names " + ", ".join(missing) + " but the SQL does not use it. "
                "Filter with the values in NAME HINTS.")
    return None


# ---------------------------------------------------------------------------
# GROUP MATHS (hard, fixed in code)
# ---------------------------------------------------------------------------
def _expected_function(inner: str):
    col, per_person = _inner_column(inner)
    if col is None:
        return None, None
    if per_person:
        return "pop_avg", col
    return RULE_FUNCTION[catalog.column(col)["rule"]], col


def group_maths_problem(sql: str):
    if not across_countries(sql):
        return None
    wrong = []
    for func, inner, _, _ in aggregates(sql):
        expected, col = _expected_function(inner)
        if expected and func.lower() != expected.lower():
            wrong.append(f"{func}({inner}) should be {expected}({inner}) "
                         f"({col} uses the {catalog.column(col)['rule']} rule)")
    if wrong:
        return ("Group figures must use each column's group rule, never a plain average: "
                + "; ".join(wrong) + ".")
    return None


def fix_group_maths(sql: str):
    if not across_countries(sql):
        return None
    new, changed = sql, False
    for func, inner, start, end in reversed(aggregates(sql)):     # right to left keeps positions valid
        expected, _ = _expected_function(inner)
        if expected and func.lower() != expected.lower():
            new = new[:start] + f"{expected}({inner})" + new[end:]
            changed = True
    return new if changed else None


# ---------------------------------------------------------------------------
# PER PERSON (hard, fixed in code)
# ---------------------------------------------------------------------------
def _divided(sql: str, col: str) -> bool:
    return bool(re.search(rf"\b{col}\s*\)?\s*/\s*(\(?\s*)?(sum\s*\(\s*)?population\b", sql, re.I))


def per_person_problem(question: str, sql: str):
    if not PER_PERSON.search(question):
        return None
    totals = [c for c in metric_columns(sql) if c in AVIATION]
    bad = [c for c in totals if not _divided(sql, c)]
    if bad:
        return ("The question asks per person, but " + ", ".join(bad) + " is a total. Divide it by "
                "population: <column> / population for one country, pop_avg(<column> / population) "
                "for a group.")
    return None


def fix_per_person(question: str, sql: str):
    if not per_person_problem(question, sql):
        return None
    new = sql
    for col in [c for c in metric_columns(sql) if c in AVIATION and not _divided(sql, c)]:
        # a group: SUM(col) [AS alias] -> pop_avg(col / population) AS col_per_person
        new2 = re.sub(rf"\b(sum|avg|pop_avg)\s*\(\s*{col}\s*\)(\s+as\s+\w+)?",
                      f"pop_avg({col} / population) AS {col}_per_person", new, count=1, flags=re.I)
        if new2 == new:
            # one country: a plain "col" or "col AS alias" in the SELECT list
            head = re.match(r"(?is)\s*select\s+(.*?)\s+from\s", new)
            if not head or len(re.findall(rf"\b{col}\b", head.group(1))) != 1:
                return None
            select = re.sub(rf"\b{col}\b(\s+as\s+\w+)?", f"{col} / population AS {col}_per_person",
                            head.group(1), count=1, flags=re.I)
            new2 = new[:head.start(1)] + select + new[head.end(1):]
        new = new2
    return new if new != sql and not per_person_problem(question, new) else None


# ---------------------------------------------------------------------------
# LATEST YEAR (soft, fixed in code)
# ---------------------------------------------------------------------------
def _target_year(sql: str, ranking: bool):
    cols = metric_columns(sql)
    if not cols:
        return None
    if ranking:
        return min((catalog.column(c)["broad_year"] or catalog.column(c)["latest_year"]) for c in cols)
    return min(catalog.column(c)["latest_year"] for c in cols)


def _is_ranking(sql: str) -> bool:
    return across_countries(sql) or (bool(re.search(r"\border\s+by\b", sql, re.I))
                                     and not single_country(sql))


def latest_year_problem(question: str, sql: str):
    if YEAR_IN_TEXT.search(question) or TIME_WORDS.search(question):
        return None
    years = [int(y) for y in re.findall(r"\byear\s*=\s*(\d{4})\b", sql)]
    if len(set(years)) != 1:
        return None
    target = _target_year(sql, _is_ranking(sql))
    if target and years[0] != target:
        what = "its broad-coverage year" if _is_ranking(sql) else "its latest year"
        return (f"No year was asked, so use {what}: year = {target}, not {years[0]} "
                f"(see DATA FACTS).")
    return None


def fix_latest_year(question: str, sql: str):
    if not latest_year_problem(question, sql):
        return None
    target = _target_year(sql, _is_ranking(sql))
    return re.sub(r"\byear\s*=\s*\d{4}\b", f"year = {target}", sql)


# ---------------------------------------------------------------------------
# RANKINGS USE COUNTRIES (soft)
# ---------------------------------------------------------------------------
def ranking_problem(question: str, sql: str):
    if not WHICH_COUNTRIES.search(question):
        return None
    gb = _group_by(sql)
    if any(g in gb for g in GROUPING) and "country" not in gb:
        return ("The question asks which COUNTRIES; rank countries (SELECT country, year and the value), "
                "not groups.")
    return None


# ---------------------------------------------------------------------------
# ALL TOGETHER
# ---------------------------------------------------------------------------
def apply_instant_fixes(question: str, sql: str):
    """Returns (sql, list of fixes made). Each fix is kept only if its check then passes."""
    made = []
    steps = (
        ("per person", lambda s: per_person_problem(question, s), lambda s: fix_per_person(question, s)),
        ("group maths", group_maths_problem, fix_group_maths),
        ("latest year", lambda s: latest_year_problem(question, s), lambda s: fix_latest_year(question, s)),
    )
    for name, problem, fix in steps:
        if problem(sql):
            new = fix(sql)
            if new and not problem(new):
                sql = new
                made.append(name)
    return sql, made


def hard_problem(question: str, res, sql: str):
    return names_problem(res, sql) or per_person_problem(question, sql) or group_maths_problem(sql)


def soft_problem(question: str, sql: str):
    return latest_year_problem(question, sql) or ranking_problem(question, sql)
