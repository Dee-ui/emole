"""build.py: build data/emole.duckdb (and the committed snapshot) from the sources.

The steps, in order:
  1. Read and check data/sources.yaml (17 columns) and the reference lists.
  2. Download each source once (or reuse the saved copy in data/raw/).
  3. Clean each file to (iso3, year, value): real countries only, every removed row recorded.
  4. Join all columns on iso3 + year into one wide table, years YEAR_MIN to YEAR_MAX.
  5. Add the country name and the grouping columns (continent ... is_middle_east).
  6. Measure each column: first year, latest year, latest year with broad coverage.
  7. Write the snapshot (data/processed/) and the database (built in a temporary file,
     then swapped in, so there is never a half-built database).

Run through the script:  python scripts/build_data.py   (see that file for options)
"""
import argparse
import datetime as dt
import json
import os
import platform
import sys
from pathlib import Path

import duckdb
import pandas as pd

from emole import config, groupmath
from emole.data import fetch
from emole.data.groups import build_groups, load_regions
from emole.data.parse import ParseError, parse_owid, parse_wb_countries, parse_wb_indicator
from emole.data.sources import SourceListError, load_sources, source_id, source_url

ID_COLUMNS = ["country", "iso3", "year"]


# ---------------------------------------------------------------------------
# 2. DOWNLOAD (or reuse)
# ---------------------------------------------------------------------------
def collect_files(sources: list, raw_dir: Path, refresh: bool, offline: bool) -> dict:
    files = {"_wb_countries": fetch.fetch_wb_countries(refresh, offline, raw_dir)}
    for c in sources:
        print(f"   {c['column']:<28} ", end="", flush=True)
        if c["source"] == "owid":
            files[c["column"]] = fetch.fetch_owid(c["slug"], refresh, offline, raw_dir)
        else:
            files[c["column"]] = fetch.fetch_wb_indicator(c["code"], refresh, offline, raw_dir)
        print(files[c["column"]].name)
    return files


# ---------------------------------------------------------------------------
# 3-5. CLEAN, JOIN, ADD GROUPS
# ---------------------------------------------------------------------------
def build_table(sources: list, files: dict, ref_dir: Path = None,
                year_min: int = None, year_max: int = None):
    """Returns (wide, removed, infos, unmatched). Pure: no downloads, no writing."""
    year_min = config.YEAR_MIN if year_min is None else year_min
    year_max = config.YEAR_MAX if year_max is None else year_max
    wb_countries = parse_wb_countries(files["_wb_countries"])
    aggregates = set(wb_countries.loc[wb_countries["is_aggregate"], "iso3"])

    longs, removed, infos, names = [], [], {}, []
    for c in sources:
        col = c["column"]
        if c["source"] == "owid":
            rows, rem, info = parse_owid(files[col], col, c.get("value_column"))
            names.append(rows[["iso3", "entity"]].assign(src="owid"))
        else:
            rows, rem, info = parse_wb_indicator(files[col], col, aggregates)
            names.append(rows[["iso3", "entity"]].assign(src="wb"))
        scale = c.get("scale", 1)
        if scale != 1:                              # change the source's unit to ours (see sources.yaml)
            rows = rows.assign(value=rows["value"] * scale)
            info["scale"] = scale
        in_range = rows["year"].between(year_min, year_max)
        info.update(rows_kept=int(in_range.sum()), rows_outside_years=int((~in_range).sum()),
                    download_date=fetch.download_date(files[col]))
        infos[col] = info
        longs.append(rows.loc[in_range, ["iso3", "year", "value"]].assign(column=col))
        removed.append(rem)

    long = pd.concat(longs, ignore_index=True)
    wide = long.pivot(index=["iso3", "year"], columns="column", values="value").reset_index()
    wide.columns.name = None
    metric_cols = [c["column"] for c in sources]
    for col in metric_cols:                         # a column with no rows at all still exists
        if col not in wide.columns:
            wide[col] = pd.NA
    # Totals that are whole numbers (passengers, people) are stored as whole numbers.
    for c in sources:
        s = wide[c["column"]]
        if c["aggregation"] == "sum" and s.notna().any() and (s.dropna() % 1 == 0).all():
            wide[c["column"]] = s.round().astype("Int64")

    wide["country"] = wide["iso3"].map(_country_names(pd.concat(names), wb_countries, ref_dir))
    groups, unmatched = build_groups(wide["iso3"].unique(), wb_countries, ref_dir)
    wide = wide.merge(groups, on="iso3", how="left")
    group_cols = [c for c in groups.columns if c != "iso3"]
    for col in ["country"] + [c for c in group_cols if not c.startswith("is_")]:
        # One kind of "empty" (None) everywhere, the same as after a round trip through Parquet.
        wide[col] = wide[col].astype(object).where(wide[col].notna(), None)
    wide = wide[ID_COLUMNS + group_cols + metric_cols].sort_values(["iso3", "year"])
    wide = wide.reset_index(drop=True)
    removed = pd.concat(removed, ignore_index=True).sort_values(["column", "reason", "entity"])
    return wide, removed.reset_index(drop=True), infos, unmatched


def _country_names(names: pd.DataFrame, wb_countries: pd.DataFrame, ref_dir) -> dict:
    """OWID's standard country names first (they are clean: 'Egypt', not 'Egypt, Arab
    Rep.'), then the World Bank's, then the UN M49 name."""
    out = {}
    m49 = load_regions(ref_dir).set_index("iso3")["name"].to_dict()
    wb = wb_countries.set_index("iso3")["wb_name"].to_dict()
    owid = names[names["src"] == "owid"]
    if not owid.empty:
        out.update(owid.groupby("iso3")["entity"].agg(lambda s: s.value_counts().index[0]).to_dict())
    for code in set(names["iso3"]):
        out.setdefault(code, wb.get(code) or m49.get(code) or code)
    return out


# ---------------------------------------------------------------------------
# 6. MEASURE EACH COLUMN
# ---------------------------------------------------------------------------
def broad_year(counts: pd.Series, latest: int) -> int:
    """Newest year whose country count is at least BROAD_COVERAGE_SHARE of the best
    count in the 10 years up to the latest year."""
    window = counts[(counts.index > latest - 10) & (counts.index <= latest)]
    peak = window.max()
    good = window[window >= config.BROAD_COVERAGE_SHARE * peak]
    return int(good.index.max())


def column_meta(wide: pd.DataFrame, sources: list, infos: dict) -> pd.DataFrame:
    rows = []
    for c in sources:
        col = c["column"]
        have = wide[wide[col].notna()]
        if have.empty:
            first = latest = broad = None
            n_latest = n_broad = 0
        else:
            counts = have.groupby("year")["iso3"].nunique()
            first, latest = int(counts.index.min()), int(counts.index.max())
            broad = broad_year(counts, latest)
            n_latest, n_broad = int(counts[latest]), int(counts[broad])
        info = infos.get(col, {})
        rows.append({
            "column": col, "letter": c["letter"], "description": c["description"],
            "unit": c["unit"], "aggregation": c["aggregation"], "weight_note": c["weight_note"],
            "caveat": c.get("caveat") or "", "source": c["source"], "source_id": source_id(c),
            "original_id": c.get("original_id") or c.get("code") or "",
            "source_url": source_url(c), "producer": c["producer"], "licence": c["licence"],
            "why_source": c.get("why_source") or "",
            "first_year": first, "latest_year": latest, "latest_broad_year": broad,
            "countries_latest": n_latest, "countries_broad": n_broad,
            "raw_file": info.get("file", ""), "download_date": info.get("download_date", ""),
        })
    meta = pd.DataFrame(rows)
    for k in ("first_year", "latest_year", "latest_broad_year"):
        meta[k] = meta[k].astype("Int64")
    return meta


# ---------------------------------------------------------------------------
# 7. WRITE
# ---------------------------------------------------------------------------
def build_info(wide: pd.DataFrame, infos: dict, year_min: int, year_max: int) -> dict:
    return {
        "build_version": config.BUILD_VERSION,
        "built_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "year_min": year_min, "year_max": year_max,
        "rows": int(len(wide)), "countries": int(wide["iso3"].nunique()),
        "first_year_in_table": int(wide["year"].min()), "last_year_in_table": int(wide["year"].max()),
        "python": platform.python_version(), "pandas": pd.__version__, "duckdb": duckdb.__version__,
        "sources": infos,
    }


def write_snapshot(wide, meta, info, removed, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    wide.to_parquet(out_dir / config.SNAPSHOT_TABLE.name, index=False)
    meta.to_csv(out_dir / config.SNAPSHOT_META.name, index=False, encoding="utf-8", lineterminator="\n")
    (out_dir / config.SNAPSHOT_INFO.name).write_text(json.dumps(info, indent=2), encoding="utf-8")
    removed.to_csv(out_dir / config.REMOVED_ROWS.name, index=False, encoding="utf-8", lineterminator="\n")


def write_database(wide, meta, info, db_path: Path) -> Path:
    """Build in a temporary file, then swap it in."""
    db_path = Path(db_path)
    tmp = db_path.with_suffix(".duckdb.tmp")
    if tmp.exists():
        tmp.unlink()
    con = duckdb.connect(str(tmp))
    try:
        con.register("wide_df", wide)
        con.register("meta_df", meta)
        con.execute("CREATE TABLE country_year AS SELECT * FROM wide_df")
        con.execute("CREATE TABLE column_meta AS SELECT * FROM meta_df")
        flat = [(k, json.dumps(v) if isinstance(v, (dict, list)) else str(v)) for k, v in info.items()]
        con.execute("CREATE TABLE build_info (key VARCHAR, value VARCHAR)")
        con.executemany("INSERT INTO build_info VALUES (?, ?)", flat)
        for macro in groupmath.SQL_MACROS.values():    # the group maths, by name (Step 2)
            con.execute(macro)
    finally:
        con.close()
    try:
        os.replace(tmp, db_path)
    except PermissionError:
        sys.exit(f"\nCould not replace {db_path.name}: it is open somewhere (a notebook, the "
                 "chatbot or a database viewer). Close it and run the build again.")
    return db_path


def read_snapshot(out_dir: Path):
    wide = pd.read_parquet(out_dir / config.SNAPSHOT_TABLE.name)
    meta = pd.read_csv(out_dir / config.SNAPSHOT_META.name, keep_default_na=False,
                       na_values={"first_year": [""], "latest_year": [""], "latest_broad_year": [""]})
    for k in ("first_year", "latest_year", "latest_broad_year"):
        meta[k] = meta[k].astype("Int64")
    info = json.loads((out_dir / config.SNAPSHOT_INFO.name).read_text(encoding="utf-8"))
    return wide, meta, info


# ---------------------------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------------------------
def _plural(n: int, word: str) -> str:
    return f"{n:,} {word}" + ("" if n == 1 else "s")


def summary(wide, meta, info, removed=None, unmatched=None) -> str:
    lines = [
        "=" * 78,
        f"Emole data build  |  BUILD_VERSION {info['build_version']}  |  built {info['built_at_utc']}",
        "=" * 78,
        f"country_year: {info['rows']:,} rows | {info['countries']} countries and territories | "
        f"years {info['first_year_in_table']}-{info['last_year_in_table']}",
        "",
        "  letter column                          latest  broad  countries(broad)  aggregation",
    ]
    for _, m in meta.iterrows():
        lines.append(f"  {m['letter']:<6} {m['column']:<30} {str(m['latest_year']):>6} "
                     f"{str(m['latest_broad_year']):>6} {m['countries_broad']:>17}  {m['aggregation']}")
    if removed is not None and len(removed):
        lines.append("")
        lines.append("Rows removed (full list in data/processed/removed_rows.csv):")
        for reason, part in removed.groupby("reason"):
            ents = sorted(set(part["entity"].astype(str)))
            shown = ", ".join(ents[:8]) + (f" ... (+{len(ents) - 8} more)" if len(ents) > 8 else "")
            n_rows = int(part["rows"].sum())
            lines.append(f"  - {reason}: {_plural(len(ents), 'name')}, {_plural(n_rows, 'row')}. {shown}")
    if unmatched:
        lines.append("")
        lines.append("Grouping gaps (countries with no value for a grouping column):")
        for k, v in unmatched.items():
            lines.append(f"  - {k}: {len(v)}" + (f" -> {', '.join(v[:15])}" if v else ""))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def run(refresh: bool = False, offline: bool = False, from_snapshot: bool = False,
        sources_file: Path = None, raw_dir: Path = None, ref_dir: Path = None,
        out_dir: Path = None, db_path: Path = None, year_min: int = None, year_max: int = None) -> dict:
    out_dir = Path(out_dir or config.PROCESSED_DIR)
    db_path = Path(db_path or config.DB_PATH)
    if from_snapshot:
        print("\n[1/2] Reading the committed snapshot (no internet needed)")
        wide, meta, info = read_snapshot(out_dir)
        print("[2/2] Writing the database")
        write_database(wide, meta, info, db_path)
        print(summary(wide, meta, info))
        return {"wide": wide, "meta": meta, "info": info}

    year_min = config.YEAR_MIN if year_min is None else year_min
    year_max = config.YEAR_MAX if year_max is None else year_max
    print("\n[1/4] Checking data/sources.yaml and the reference lists")
    sources = load_sources(sources_file)
    print(f"   {len(sources)} columns listed")
    print("\n[2/4] Downloading (or reusing saved copies in data/raw/)")
    files = collect_files(sources, raw_dir or config.RAW_DIR, refresh, offline)
    print("\n[3/4] Cleaning and joining")
    wide, removed, infos, unmatched = build_table(sources, files, ref_dir, year_min, year_max)
    meta = column_meta(wide, sources, infos)
    info = build_info(wide, infos, year_min, year_max)
    print("\n[4/4] Writing the snapshot and the database")
    write_snapshot(wide, meta, info, removed, out_dir)
    write_database(wide, meta, info, db_path)
    print(summary(wide, meta, info, removed, unmatched))
    print(f"\nWritten: {db_path}\n         {out_dir}")
    return {"wide": wide, "meta": meta, "info": info, "removed": removed, "unmatched": unmatched}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Build Emole's country_year database.")
    ap.add_argument("--refresh", action="store_true", help="download fresh copies of every source")
    ap.add_argument("--offline", action="store_true", help="never download; use saved copies only")
    ap.add_argument("--from-snapshot", action="store_true",
                    help="rebuild the database from data/processed/ (no downloads, no cleaning)")
    args = ap.parse_args(argv)
    if args.refresh and (args.offline or args.from_snapshot):
        ap.error("--refresh cannot be combined with --offline or --from-snapshot")
    if args.from_snapshot and not config.SNAPSHOT_TABLE.exists():
        sys.exit(f"\nNo snapshot yet at {config.SNAPSHOT_TABLE}. Run the full build once "
                 "(python scripts/build_data.py), or pull the latest repo.")
    try:
        run(refresh=args.refresh, offline=args.offline, from_snapshot=args.from_snapshot)
    except (fetch.DownloadError, ParseError, SourceListError, ValueError) as e:
        # Expected problems get one clear sentence, not a page of Python traceback.
        sys.exit(f"\nBUILD STOPPED: {e}")
