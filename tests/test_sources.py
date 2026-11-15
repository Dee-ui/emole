"""The real source list and bloc lists are complete and consistent."""
import pandas as pd
import pytest

from emole import config
from emole.data.sources import SourceListError, load_blocs, load_sources


def test_real_sources_have_all_17_columns():
    cols = load_sources()
    assert len(cols) == 17
    assert {c["letter"] for c in cols} == {"M", "O", "L", "E"}
    names = [c["column"] for c in cols]
    assert len(names) == len(set(names))


def test_totals_are_summed_and_rates_are_weighted():
    rules = {c["column"]: c["aggregation"] for c in load_sources()}
    for total in ("air_passengers", "air_departures", "air_freight_mtkm", "population"):
        assert rules[total] == "sum"
    assert rules["internet_users_pct"] == "pop_weighted"
    assert rules["gdp_per_capita_ppp"] == "pop_weighted"
    assert rules["gdp_growth_pct"] == "gdp_weighted"
    assert rules["inflation_cpi_pct"] == "median"


def test_every_aviation_column_carries_the_caveat():
    for c in load_sources():
        if c["column"].startswith("air_"):
            assert c.get("caveat") == "aviation", c["column"]


def test_units_appear_in_column_names_where_promised():
    names = {c["column"] for c in load_sources()}
    assert {"internet_users_pct", "co2_per_capita_t", "under5_deaths_per_1000"} <= names


def test_bloc_lists_match_the_checked_memberships():
    b = load_blocs()
    eco = set(b["ecowas"]["members"])
    assert len(eco) == 12 and "NGA" in eco
    assert not eco & {"BFA", "MLI", "NER", "MRT"}          # left ECOWAS
    assert len(b["african_union"]["members"]) == 55 and "ESH" in b["african_union"]["members"]
    assert len(b["eu"]["members"]) == 27 and "GBR" not in b["eu"]["members"]
    assert len(b["g20"]["members"]) == 19
    assert len(b["middle_east"]["members"]) == 16 and "CYP" not in b["middle_east"]["members"]


def test_ecowas_members_are_all_au_members():
    b = load_blocs()
    assert set(b["ecowas"]["members"]) <= set(b["african_union"]["members"])


def test_m49_reference_is_complete():
    m49 = pd.read_csv(config.REFERENCE_DIR / "un_m49.csv", keep_default_na=False)
    assert len(m49) == 248 and m49["iso3"].is_unique
    row = m49.set_index("iso3")
    assert row.loc["NGA", "subregion"] == "Western Africa"
    assert row.loc["EGY", "subregion"] == "Northern Africa"
    assert row.loc["LAO", "continent"] == "Asia"          # name with an apostrophe (was missed once)
    assert "TWN" not in row.index and "XKX" not in row.index


def test_bad_source_list_is_rejected(tmp_path):
    bad = tmp_path / "s.yaml"
    bad.write_text("columns:\n  - column: x\n    letter: M\n", encoding="utf-8")
    with pytest.raises(SourceListError, match="missing"):
        load_sources(bad)


def test_bloc_count_mismatch_is_rejected(tmp_path):
    bad = tmp_path / "blocs.yaml"
    bad.write_text("x:\n  column: is_x\n  as_of: 2026-01-01\n  count: 3\n  members: [NGA, GHA]\n",
                   encoding="utf-8")
    with pytest.raises(SourceListError, match="says 3 members"):
        load_blocs(bad)
