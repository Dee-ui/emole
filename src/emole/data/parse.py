"""parse.py: turn each downloaded file into a tidy list of (iso3, year, value) rows,
keeping ONLY real countries and territories, and recording everything removed.

Why removal needs two different rules (decision E-38)
  OWID files: group rows ("World", "Africa", "High-income countries", "European Union
  (27)") have a blank Code or a code starting with OWID_ (World is OWID_WRL).
  So "keep rows whose Code is 3 capital letters" removes them all.

  World Bank files: group rows use 3-letter codes too (WLD = World, SSF = Sub-Saharan
  Africa, EUU = European Union, HIC = High income ...). The 3-letter rule would let
  every one of them in, and "World" would top every country ranking. So World Bank
  rows are checked against the World Bank's own country list, which marks each
  group as an "Aggregate".
"""
import json
import re
from pathlib import Path

import pandas as pd

from emole import config

ISO3 = re.compile(r"^[A-Z]{3}$")
KEYS = ("Entity", "Code", "Year")


class ParseError(ValueError):
    """A downloaded file does not have the shape we expect."""


def _removed(df: pd.DataFrame, reason: str, column: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["column", "code", "entity", "rows", "reason"])
    out = (df.groupby(["code", "entity"], dropna=False).size().reset_index(name="rows"))
    out["reason"] = reason
    out["column"] = column
    return out[["column", "code", "entity", "rows", "reason"]]


def pick_value_column(df: pd.DataFrame, wanted: str = None, label: str = "") -> str:
    """OWID files have Entity, Code, Year and usually ONE value column. If there are
    several, sources.yaml must name the right one in value_column."""
    others = [c for c in df.columns if c not in KEYS]
    if wanted:
        if wanted not in df.columns:
            raise ParseError(f"{label}: value_column '{wanted}' not found. Columns are: {others}")
        return wanted
    numeric = [c for c in others if pd.api.types.is_numeric_dtype(df[c])]
    if len(numeric) == 1:
        return numeric[0]
    raise ParseError(f"{label}: expected one numeric value column, found {numeric or others}. "
                     "Add value_column: <name> to this entry in data/sources.yaml.")


def parse_owid(path: Path, column: str, value_column: str = None):
    """Returns (rows, removed, info). rows has iso3, year, value, entity."""
    df = pd.read_csv(path, encoding="utf-8")
    # OWID has changed the exact header casing over time (sometimes "Entity,Code,Year",
    # sometimes "entity,code,year"), so the three key columns are matched without
    # caring about case, then renamed to the fixed names the rest of this file expects.
    by_lower = {c.lower(): c for c in df.columns}
    missing = [k for k in ("entity", "code", "year") if k not in by_lower]
    if missing:
        raise ParseError(f"{Path(path).name}: missing {missing}. Columns: {list(df.columns)}")
    df = df.rename(columns={by_lower["entity"]: "Entity", by_lower["code"]: "Code",
                            by_lower["year"]: "Year"})
    # OWID now adds its own metadata columns to every download (for example "owid_region").
    # These are not values to keep, so they are dropped before picking the value column.
    meta_cols = [c for c in df.columns if c.lower().startswith("owid_")]
    df = df.drop(columns=meta_cols)
    vcol = pick_value_column(df, value_column, Path(path).name)
    df = df.rename(columns={"Entity": "entity", "Code": "code", "Year": "year", vcol: "value"})
    df["code"] = df["code"].fillna("").astype(str).str.strip()
    renamed = df["code"].isin(config.OWID_CODE_RENAMES)
    df.loc[renamed, "code"] = df.loc[renamed, "code"].map(config.OWID_CODE_RENAMES)

    blank = df["code"] == ""
    owid_code = df["code"].str.startswith("OWID_")
    other_bad = ~blank & ~owid_code & ~df["code"].str.match(ISO3)
    removed = pd.concat([
        _removed(df[blank], "blank code: an OWID group row (region, income group, union)", column),
        _removed(df[owid_code], "OWID_ code: OWID group or former country (World, USSR ...)", column),
        _removed(df[other_bad], "code is not 3 capital letters", column),
    ], ignore_index=True)
    keep = df[~(blank | owid_code | other_bad)].copy()
    keep["value"] = pd.to_numeric(keep["value"], errors="coerce")
    keep = keep.dropna(subset=["value"])
    keep["year"] = keep["year"].astype(int)
    _no_duplicates(keep, Path(path).name)
    info = {"value_column": vcol, "file": Path(path).name}
    return keep.rename(columns={"code": "iso3"})[["iso3", "year", "value", "entity"]], removed, info


def parse_wb_countries(path: Path) -> pd.DataFrame:
    """The World Bank country list: one row per code, with region, income group and
    whether it is an aggregate (a group row)."""
    body = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = []
    for r in body["records"]:
        region = (r.get("region") or {}).get("value", "").strip()     # values can carry trailing spaces
        income = (r.get("incomeLevel") or {}).get("value", "").strip()
        rows.append({"iso3": r["id"].strip(), "wb_name": r.get("name", "").strip(),
                     "wb_region": region, "wb_income": income,
                     "is_aggregate": region == "Aggregates"})
    df = pd.DataFrame(rows)
    if df.empty or df["is_aggregate"].all():
        raise ParseError(f"{Path(path).name}: no countries found in the World Bank list")
    return df


INCOME_GROUPS = {
    "Low income": "low",
    "Lower middle income": "lower-middle",
    "Upper middle income": "upper-middle",
    "High income": "high",
}


def parse_wb_indicator(path: Path, column: str, aggregates: set):
    """Returns (rows, removed, info) for one World Bank indicator file."""
    body = json.loads(Path(path).read_text(encoding="utf-8"))
    recs = body.get("records") or []
    df = pd.DataFrame({
        "code": [str(r.get("countryiso3code") or "").strip() for r in recs],
        "entity": [(r.get("country") or {}).get("value", "") for r in recs],
        "year": [r.get("date") for r in recs],
        "value": [r.get("value") for r in recs],
    })
    if df.empty:
        raise ParseError(f"{Path(path).name}: no records")
    blank = df["code"] == ""
    agg = df["code"].isin(aggregates)
    other_bad = ~blank & ~agg & ~df["code"].str.match(ISO3)
    removed = pd.concat([
        _removed(df[blank], "blank code in World Bank file", column),
        _removed(df[agg], "World Bank aggregate (a group row with a 3-letter code)", column),
        _removed(df[other_bad], "code is not 3 capital letters", column),
    ], ignore_index=True)
    keep = df[~(blank | agg | other_bad)].copy()
    keep["value"] = pd.to_numeric(keep["value"], errors="coerce")
    keep["year"] = pd.to_numeric(keep["year"], errors="coerce")
    keep = keep.dropna(subset=["value", "year"])
    keep["year"] = keep["year"].astype(int)
    _no_duplicates(keep, Path(path).name)
    info = {"file": Path(path).name, "lastupdated": (body.get("meta") or {}).get("lastupdated")}
    return keep.rename(columns={"code": "iso3"})[["iso3", "year", "value", "entity"]], removed, info


def _no_duplicates(df: pd.DataFrame, label: str) -> None:
    dup = df.duplicated(["code", "year"]) if "code" in df.columns else df.duplicated(["iso3", "year"])
    if dup.any():
        sample = df[dup].head(3).to_dict("records")
        raise ParseError(f"{label}: the same country and year appears twice, e.g. {sample}")
