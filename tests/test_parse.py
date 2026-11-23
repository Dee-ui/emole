"""Cleaning keeps real countries only, and records everything it removes."""
import pytest

from emole.data import fetch
from emole.data.parse import ParseError, parse_owid, parse_wb_countries, parse_wb_indicator

from .conftest import RAW


def test_owid_group_rows_are_removed_and_listed():
    rows, removed, _ = parse_owid(RAW / "owid_test-air__2026-01-01.csv", "air_passengers")
    assert set(rows["iso3"]) == {"NGA", "GHA", "XKX", "TWN"}
    gone = set(removed["entity"])
    assert {"Africa", "World", "High-income countries", "European Union (27)", "USSR"} <= gone
    assert "Kosovo" not in gone


def test_kosovo_gets_the_world_bank_code():
    rows, _, _ = parse_owid(RAW / "owid_test-air__2026-01-01.csv", "air_passengers")
    assert rows.loc[rows["entity"] == "Kosovo", "iso3"].tolist() == ["XKX"]


def test_empty_values_are_dropped():
    rows, _, _ = parse_owid(RAW / "owid_test-air__2026-01-01.csv", "air_passengers")
    assert not ((rows["iso3"] == "GHA") & (rows["year"] == 2023)).any()


def test_two_value_columns_need_value_column():
    path = RAW / "owid_test-multi__2026-01-01.csv"
    with pytest.raises(ParseError, match="value_column"):
        parse_owid(path, "x")
    rows, _, info = parse_owid(path, "x", value_column="value_b")
    assert rows["value"].tolist() == [2] and info["value_column"] == "value_b"


def test_world_bank_aggregates_are_removed_even_with_3_letter_codes():
    countries = parse_wb_countries(RAW / "wb_countries__2026-01-01.json")
    aggregates = set(countries.loc[countries["is_aggregate"], "iso3"])
    assert aggregates == {"WLD", "SSF"}
    rows, removed, info = parse_wb_indicator(RAW / "wb_SP.POP.TOTL__2026-01-01.json",
                                             "population", aggregates)
    assert set(rows["iso3"]) == {"NGA", "GHA", "XKX"}
    assert {"World", "Sub-Saharan Africa", "Not classified"} <= set(removed["entity"])
    assert info["lastupdated"] == "2026-07-14"


def test_world_bank_region_names_lose_trailing_spaces():
    countries = parse_wb_countries(RAW / "wb_countries__2026-01-01.json").set_index("iso3")
    assert countries.loc["NGA", "wb_region"] == "Sub-Saharan Africa"


def test_newest_saved_copy_is_used():
    assert fetch.latest_raw("owid_test-air", "csv", RAW).name == "owid_test-air__2026-01-01.csv"
    assert fetch.download_date(RAW / "owid_test-air__2026-01-01.csv") == "2026-01-01"


def test_offline_without_a_saved_copy_fails_clearly(tmp_path):
    with pytest.raises(fetch.DownloadError, match="offline"):
        fetch.fetch_owid("not-downloaded-yet", offline=True, raw_dir=tmp_path)


# OWID changed its CSV download between the source check (8 Nov 2026) and the first real
# build (15 Nov 2026): a lowercase header and an extra owid_region column (PL-014).
NEW_OWID_FORMAT = (
    "entity,code,year,is_air_psgr,owid_region\n"
    "Nigeria,NGA,2023,110,Africa\n"
    "Ghana,GHA,2023,40,Africa\n"
    "World,OWID_WRL,2023,999,\n"
)


def test_new_owid_format_lowercase_header_and_owid_columns(tmp_path):
    path = tmp_path / "owid_new__2026-11-15.csv"
    path.write_text(NEW_OWID_FORMAT, encoding="utf-8")
    rows, removed, info = parse_owid(path, "air_passengers")
    assert info["value_column"] == "is_air_psgr"            # owid_region was dropped, not picked
    assert set(rows["iso3"]) == {"NGA", "GHA"}
    assert "World" in set(removed["entity"])


def test_old_owid_format_still_works():
    rows, _, _ = parse_owid(RAW / "owid_test-air__2026-01-01.csv", "air_passengers")
    assert len(rows) > 0                                    # capitalised Entity,Code,Year


class _FakeResponse:
    def __init__(self, text):
        self.text, self.content = text, text.encode("utf-8")


def test_download_check_ignores_header_case(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch, "get", lambda url, session=None: _FakeResponse(NEW_OWID_FORMAT))
    path = fetch.fetch_owid("test-new", raw_dir=tmp_path)
    assert path.exists() and path.name.startswith("owid_test-new__")


def test_download_check_still_stops_on_a_web_page(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch, "get", lambda url, session=None: _FakeResponse("<!DOCTYPE html><html>"))
    with pytest.raises(fetch.DownloadError, match="expected CSV"):
        fetch.fetch_owid("test-broken", raw_dir=tmp_path)
