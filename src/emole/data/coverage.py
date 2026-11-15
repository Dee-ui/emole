"""coverage.py: write docs/coverage_report.md, a health check of what is REALLY in
the database (in the spirit of the earlier build's data audit script).

It answers four questions:
  1. For every column: first year, latest year, latest year with broad coverage,
     and how many countries have data.
  2. For Nigeria and each peer: which of the latest 5 years are missing, per column.
  3. For each region, income group and bloc: how many members have data in each
     column's broad-coverage year.
  4. Which columns are FLAGGED by the rule written before the first real build
     (see config.FLAG_*). A flag means "look at this", never "drop it": drops are
     agreed with the owner.
"""
import datetime as dt
from pathlib import Path

import duckdb
import pandas as pd

from emole import config


def load(db_path: Path = None):
    con = duckdb.connect(str(db_path or config.DB_PATH), read_only=True)
    try:
        wide = con.execute("SELECT * FROM country_year").fetchdf()
        meta = con.execute("SELECT * FROM column_meta").fetchdf()
    finally:
        con.close()
    return wide, meta


def peer_gaps(wide: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    """One row per peer, one column per data column: 'ok' or the missing years."""
    rows = []
    for iso, name in config.PEER_COUNTRIES.items():
        row = {"country": f"{name} ({iso})"}
        mine = wide[wide["iso3"] == iso]
        for _, m in meta.iterrows():
            col, latest = m["column"], m["latest_year"]
            if pd.isna(latest):
                row[col] = "no data"
                continue
            years = range(int(latest) - config.RECENT_YEARS + 1, int(latest) + 1)
            have = set(mine.loc[mine[col].notna(), "year"])
            gaps = [y for y in years if y not in have]
            row[col] = "ok" if not gaps else ("none" if len(gaps) == len(years)
                                              else "miss " + ",".join(str(y)[2:] for y in gaps))
        rows.append(row)
    return pd.DataFrame(rows)


def group_coverage(wide: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    """'members with data / members' in each column's broad-coverage year."""
    groups = []
    for col in ("continent", "subregion", "wb_region", "income_group"):
        for val in sorted(wide[col].dropna().unique()):
            groups.append((f"{col} = {val}", wide.loc[wide[col] == val, "iso3"].unique()))
    for col in [c for c in wide.columns if c.startswith("is_")]:
        groups.append((col, wide.loc[wide[col].fillna(False).astype(bool), "iso3"].unique()))
    rows = []
    for label, members in groups:
        row = {"group": label, "members": len(members)}
        part = wide[wide["iso3"].isin(members)]
        for _, m in meta.iterrows():
            year = m["latest_broad_year"]
            if pd.isna(year):
                row[m["column"]] = "-"
                continue
            n = part.loc[(part["year"] == int(year)) & part[m["column"]].notna(), "iso3"].nunique()
            row[m["column"]] = f"{n}/{len(members)}"
        rows.append(row)
    return pd.DataFrame(rows)


def flags(wide: pd.DataFrame, meta: pd.DataFrame, peers: pd.DataFrame) -> list:
    """Apply the pre-registered rule. Returns [(column, reason), ...]."""
    out = []
    for _, m in meta.iterrows():
        col, year = m["column"], m["latest_broad_year"]
        if pd.isna(year):
            out.append((col, "no data at all"))
            continue
        base = wide.loc[(wide["year"] == int(year)) & wide["population"].notna(), "iso3"].nunique()
        n = wide.loc[(wide["year"] == int(year)) & wide[col].notna(), "iso3"].nunique()
        if base and n / base < config.FLAG_MIN_COUNTRY_SHARE:
            out.append((col, f"only {n} of {base} countries with a population figure have it in {int(year)}"))
        ng = peers.loc[peers["country"].str.contains("(NGA)", regex=False), col]
        if len(ng) and ng.iloc[0] in ("none", "no data"):
            out.append((col, "Nigeria has no value in the latest 5 years"))
        bad = []
        for _, p in peers.iterrows():
            v = p[col]
            if v in ("none", "no data"):
                bad.append(p["country"])
            elif v.startswith("miss ") and len(v[5:].split(",")) > config.FLAG_MAX_PEER_GAPS:
                bad.append(p["country"])
        if bad:
            out.append((col, f"peers missing more than {config.FLAG_MAX_PEER_GAPS} of the latest "
                             f"{config.RECENT_YEARS} years: {', '.join(bad)}"))
    return out


def _md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join("" if pd.isna(v) else str(v) for v in r) + " |")
    return "\n".join(lines)


def report(db_path: Path = None, out: Path = None, removed_csv: Path = None) -> str:
    wide, meta = load(db_path)
    peers = peer_gaps(wide, meta)
    groups = group_coverage(wide, meta)
    flagged = flags(wide, meta, peers)
    removed_csv = Path(removed_csv or config.REMOVED_ROWS)

    cols = meta[["letter", "column", "unit", "first_year", "latest_year", "latest_broad_year",
                 "countries_latest", "countries_broad", "aggregation", "source", "source_id"]]
    parts = [
        "# Emolé coverage report",
        "",
        f"Generated {dt.date.today().isoformat()} by `python scripts/coverage_report.py` from "
        f"`data/emole.duckdb` ({len(wide):,} rows, {wide['iso3'].nunique()} countries and territories, "
        f"years {int(wide['year'].min())}-{int(wide['year'].max())}).",
        "",
        "**How to read it.** `latest` is the newest year with any data. `broad` is the newest year "
        f"in which at least {int(config.BROAD_COVERAGE_SHARE * 100)}% of the column's usual countries "
        "report: use it for rankings and group answers. A country's own latest year can be newer.",
        "",
        "## 1. Columns",
        "",
        _md_table(cols),
        "",
        "## 2. Flags (rule written before the first real build)",
        "",
        f"A column is flagged when: fewer than {int(config.FLAG_MIN_COUNTRY_SHARE * 100)}% of countries "
        "with a population figure have it in its broad year; or Nigeria has no value in its latest "
        f"{config.RECENT_YEARS} years; or a peer misses more than {config.FLAG_MAX_PEER_GAPS} "
        "of those years. A flag means review, not drop. Drops are agreed with the owner "
        "and recorded in docs/DATA.md.",
        "",
    ]
    parts += [f"- **{c}**: {r}" for c, r in flagged] or ["- No column is flagged."]
    parts += [
        "",
        f"## 3. Nigeria and peers: gaps in each column's latest {config.RECENT_YEARS} years",
        "",
        "`ok` = all years present. `miss 21,23` = 2021 and 2023 missing. `none` = no value in those years.",
        "",
        _md_table(peers),
        "",
        "## 4. Regions, income groups and blocs: members with data in each column's broad year",
        "",
        "Membership and income groups are the CURRENT ones, applied to every year.",
        "",
        _md_table(groups),
        "",
    ]
    if removed_csv.exists():
        rem = pd.read_csv(removed_csv, keep_default_na=False)
        summ = (rem.groupby("reason").agg(names=("entity", "nunique"), rows=("rows", "sum"))
                .reset_index())
        parts += ["## 5. Rows removed during the build", "",
                  "Full list: `data/processed/removed_rows.csv`.", "", _md_table(summ), ""]
    text = "\n".join(parts)
    out = Path(out or config.COVERAGE_REPORT)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"Coverage report written to {out}")
    print(f"Flagged columns: {len(flagged)}")
    for c, r in flagged:
        print(f"  - {c}: {r}")
    return text
