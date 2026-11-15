"""Group maths: sums, weighted averages, medians and coverage, checked by hand,
and the SQL version must give exactly the same numbers as the Python version."""
import duckdb
import pytest

from emole.groupmath import group_value, sql_coverage, sql_expression

ECOWAS_PAIR = ["NGA", "GHA"]


def test_sum_with_coverage(built):
    r = group_value(built["wide"], "air_passengers", "sum", 2023, ECOWAS_PAIR)
    assert r.value == 110                       # Ghana has no 2023 value
    assert (r.n_with_data, r.n_members, r.missing) == (1, 2, ["GHA"])
    assert r.note("ECOWAS") == "Based on 1 of 2 ECOWAS countries with data for 2023."


def test_population_weighted_average(built):
    r = group_value(built["wide"], "internet_users_pct", "pop_weighted", 2023, ECOWAS_PAIR)
    # (45 x 205m + 65 x 31m) / (205m + 31m)
    assert r.value == pytest.approx((45 * 205 + 65 * 31) / 236)
    assert r.value != pytest.approx((45 + 65) / 2)    # NOT the plain average


def test_gdp_weighted_average(built):
    r = group_value(built["wide"], "gdp_growth_pct", "gdp_weighted", 2023, ECOWAS_PAIR)
    w_ng, w_gh = 6000 * 205e6, 7000 * 31e6
    assert r.value == pytest.approx((3.0 * w_ng + 5.0 * w_gh) / (w_ng + w_gh))


def test_median(built):
    r = group_value(built["wide"], "gdp_growth_pct", "median", 2023, ECOWAS_PAIR)
    assert r.value == 4.0


def test_country_without_a_weight_is_left_out_and_counted(built):
    # Taiwan has an internet value but no population figure: it cannot be weighted.
    r = group_value(built["wide"], "internet_users_pct", "pop_weighted", 2023)
    assert r.n_members == 4 and r.n_with_data == 3 and r.missing == ["TWN"]
    assert r.value == pytest.approx((45 * 205 + 65 * 31 + 80 * 1.8) / (205 + 31 + 1.8))
    assert "total of countries with data" in r.note(world=True)


def test_no_data_gives_none(built):
    r = group_value(built["wide"], "air_passengers", "sum", 1999, ECOWAS_PAIR)
    assert r.value is None and r.n_with_data == 0


def test_unknown_rule_is_rejected(built):
    with pytest.raises(ValueError):
        group_value(built["wide"], "population", "average", 2023)


@pytest.mark.parametrize("column,rule", [
    ("air_passengers", "sum"),
    ("internet_users_pct", "pop_weighted"),
    ("gdp_growth_pct", "gdp_weighted"),
    ("gdp_growth_pct", "median"),
])
def test_sql_gives_the_same_number_as_python(built, column, rule):
    con = duckdb.connect()
    con.register("country_year", built["wide"])
    sql = (f"SELECT {sql_expression(column, rule)} AS v, {sql_coverage(column, rule)} AS n "
           "FROM country_year WHERE year = 2023 AND iso3 IN ('NGA', 'GHA')")
    v, n = con.execute(sql).fetchone()
    py = group_value(built["wide"], column, rule, 2023, ECOWAS_PAIR)
    assert float(v) == pytest.approx(py.value) and n == py.n_with_data
