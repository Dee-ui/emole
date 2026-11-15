"""groups.py: the grouping columns of country_year.

  continent, subregion   UN M49 (data/reference/un_m49.csv), plus Taiwan and Kosovo
                         from data/reference/manual_regions.csv (they are not in M49)
  wb_region              World Bank region, from the World Bank country list
  income_group           World Bank income group: low, lower-middle, upper-middle, high.
                         It is the CURRENT classification (FY2027, effective 1 July 2026)
                         applied to every year, and Emolé must say so.
  is_ecowas ... is_middle_east   true/false, from data/reference/blocs.yaml

Every country in the table gets every column filled where a source exists; countries
with no match are listed (never silently left blank).
"""
from pathlib import Path

import pandas as pd

from emole import config
from emole.data.parse import INCOME_GROUPS
from emole.data.sources import load_blocs

GROUP_COLUMNS = ["continent", "subregion", "wb_region", "income_group"]


def load_regions(ref_dir: Path = None) -> pd.DataFrame:
    ref_dir = Path(ref_dir or config.REFERENCE_DIR)
    m49 = pd.read_csv(ref_dir / "un_m49.csv", dtype=str, keep_default_na=False)
    manual = pd.read_csv(ref_dir / "manual_regions.csv", dtype=str, keep_default_na=False)
    clash = set(m49["iso3"]) & set(manual["iso3"])
    if clash:
        raise ValueError(f"manual_regions.csv repeats codes already in UN M49: {sorted(clash)}")
    both = pd.concat([m49[["iso3", "name", "continent", "subregion"]],
                      manual[["iso3", "name", "continent", "subregion"]]], ignore_index=True)
    return both.replace({"": None})


def build_groups(iso3_list, wb_countries: pd.DataFrame, ref_dir: Path = None):
    """Returns (groups, unmatched).
    groups: one row per iso3 with every grouping column.
    unmatched: {"continent": [...codes...], "wb_region": [...], ...} for the report."""
    ref_dir = Path(ref_dir or config.REFERENCE_DIR)
    base = pd.DataFrame({"iso3": sorted(set(iso3_list))})
    regions = load_regions(ref_dir)
    g = base.merge(regions[["iso3", "continent", "subregion"]], on="iso3", how="left")

    wb = wb_countries[~wb_countries["is_aggregate"]][["iso3", "wb_region", "wb_income"]]
    g = g.merge(wb, on="iso3", how="left")
    g["income_group"] = g["wb_income"].map(INCOME_GROUPS)     # "Not classified" -> empty
    g = g.drop(columns=["wb_income"])
    g["wb_region"] = g["wb_region"].replace({"": None})

    blocs = load_blocs(ref_dir / "blocs.yaml")
    for b in blocs.values():
        g[b["column"]] = g["iso3"].isin(b["members"])

    unmatched = {col: g.loc[g[col].isna(), "iso3"].tolist() for col in GROUP_COLUMNS}
    present = set(g["iso3"])
    unmatched["bloc members missing from the table"] = sorted(
        {m for b in blocs.values() for m in b["members"] if m not in present})
    return g, unmatched


def bloc_columns(ref_dir: Path = None) -> list:
    blocs = load_blocs(Path(ref_dir or config.REFERENCE_DIR) / "blocs.yaml")
    return [b["column"] for b in blocs.values()]
