"""The whole build on the fixtures: right rows, right values, groups filled, files written."""
import duckdb
import pandas as pd

from emole.data.build import read_snapshot, run

from .conftest import RAW, SOURCES

EXPECTED_ROWS = {("NGA", 2022), ("NGA", 2023), ("GHA", 2022), ("GHA", 2023),
                 ("XKX", 2022), ("XKX", 2023), ("TWN", 2023)}


def test_only_real_countries_survive(built):
    wide = built["wide"]
    assert set(wide["iso3"]) == {"NGA", "GHA", "XKX", "TWN"}
    assert not wide["iso3"].isin(["WLD", "SSF", "OWID_WRL", "OWID_USS"]).any()
    assert not wide["country"].isin(["World", "Africa", "Sub-Saharan Africa"]).any()


def test_join_keeps_every_country_year_exactly_once(built):
    wide = built["wide"]
    keys = set(zip(wide["iso3"], wide["year"], strict=True))
    assert keys == EXPECTED_ROWS
    assert not wide.duplicated(["iso3", "year"]).any()


def test_values_land_in_the_right_cells(built):
    w = built["wide"].set_index(["iso3", "year"])
    assert w.loc[("NGA", 2023), "air_passengers"] == 110
    assert w.loc[("NGA", 2023), "internet_users_pct"] == 45
    assert w.loc[("NGA", 2023), "population"] == 205_000_000
    assert w.loc[("XKX", 2022), "air_passengers"] == 10          # from OWID_KOS
    assert w.loc[("XKX", 2023), "population"] == 1_800_000       # from the World Bank, same row
    assert pd.isna(w.loc[("GHA", 2023), "air_passengers"])       # empty in the source
    assert w.loc[("GHA", 2023), "gdp_growth_pct"] == 5.0


def test_years_outside_the_range_are_dropped(built):
    assert built["wide"]["year"].min() >= 1970
    assert built["info"]["sources"]["air_passengers"]["rows_outside_years"] == 1


def test_names_and_column_order(built):
    wide = built["wide"]
    assert list(wide.columns[:3]) == ["country", "iso3", "year"]
    names = dict(zip(wide["iso3"], wide["country"], strict=True))
    assert names["NGA"] == "Nigeria" and names["XKX"] == "Kosovo" and names["TWN"] == "Taiwan"
    assert wide.columns.get_loc("population") > wide.columns.get_loc("is_middle_east")


def test_totals_are_stored_as_whole_numbers(built):
    wide = built["wide"]
    assert str(wide["air_passengers"].dtype) == "Int64"
    assert str(wide["population"].dtype) == "Int64"
    assert wide["internet_users_pct"].dtype == float


def test_grouping_columns_are_filled_or_listed(built):
    g = built["wide"].drop_duplicates("iso3").set_index("iso3")
    assert g.loc["NGA", "continent"] == "Africa" and g.loc["NGA", "subregion"] == "Western Africa"
    assert g.loc["NGA", "wb_region"] == "Sub-Saharan Africa"
    assert g.loc["NGA", "income_group"] == "lower-middle"
    assert bool(g.loc["NGA", "is_ecowas"]) and bool(g.loc["NGA", "is_african_union"])
    assert not bool(g.loc["NGA", "is_g20"])
    assert g.loc["XKX", "subregion"] == "Southern Europe"           # manual entry
    assert g.loc["TWN", "continent"] == "Asia"                      # manual entry
    assert "TWN" in built["unmatched"]["wb_region"]                  # listed, not hidden
    for col in ("continent", "subregion"):
        assert built["unmatched"][col] == []


def test_removed_rows_are_recorded(built):
    rem = built["removed"]
    assert {"Africa", "World", "Western Africa (WB)", "Sub-Saharan Africa"} <= set(rem["entity"])
    assert (rem["rows"] > 0).all()


def test_column_meta_measures_years(built):
    meta = built["meta"].set_index("column")
    assert meta.loc["air_passengers", "latest_year"] == 2023
    # 2023 has only 2 of the usual 3 countries (below 80%), so the broad year is 2022
    assert meta.loc["air_passengers", "latest_broad_year"] == 2022
    assert meta.loc["internet_users_pct", "latest_broad_year"] == 2023
    assert meta.loc["gdp_growth_pct", "aggregation"] == "gdp_weighted"
    assert meta.loc["population", "source_url"].endswith("SP.POP.TOTL")


def test_database_is_written_and_readable(built):
    db = built["out"] / "emole.duckdb"
    con = duckdb.connect(str(db), read_only=True)
    try:
        tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        assert {"country_year", "column_meta", "build_info"} <= tables
        n = con.execute("SELECT COUNT(*) FROM country_year").fetchone()[0]
        version = con.execute("SELECT value FROM build_info WHERE key = 'build_version'").fetchone()[0]
    finally:
        con.close()
    assert n == len(EXPECTED_ROWS) and version == "1"


def test_snapshot_rebuild_gives_the_same_table(built, tmp_path):
    out = built["out"] / "processed"
    wide, meta, info = read_snapshot(out)
    pd.testing.assert_frame_equal(wide, built["wide"], check_dtype=False)
    again = run(from_snapshot=True, out_dir=out, db_path=tmp_path / "again.duckdb")
    assert len(again["wide"]) == len(built["wide"])


def test_build_is_repeatable(built, tmp_path):
    second = run(offline=True, sources_file=SOURCES, raw_dir=RAW, out_dir=tmp_path / "p",
                 db_path=tmp_path / "e.duckdb", year_min=1970, year_max=2026)
    pd.testing.assert_frame_equal(second["wide"], built["wide"])
