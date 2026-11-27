"""Charts: the right kind for the result's shape, with units on the axes."""
import pandas as pd

from emole.pipeline import visualizer as v


def test_text_or_chart(engine_db):
    one = pd.DataFrame({"country": ["Ghana"], "year": [2023], "internet_users_pct": [65.0]})
    trend = pd.DataFrame({"country": ["Ghana"] * 3, "year": [2021, 2022, 2023],
                          "internet_users_pct": [55.0, 60.0, 65.0]})
    assert v.decide_output("Ghana internet 2023", one) == "text"
    assert v.decide_output("Ghana internet", trend) == "chart"


def test_several_measures_get_one_panel_each(engine_db):
    df = pd.DataFrame({"country": ["Ghana"] * 2, "year": [2022, 2023], "internet_users_pct": [60.0, 65.0],
                       "population": [30e6, 31e6]})
    spec = v.choose_chart(df, "Ghana internet and population")
    assert spec["facets"] and spec["kind"] == "line"
    out = v.build_chart("Ghana internet and population", df, save_files=False)
    assert "Internet users (% of population)" in out["figure"]


def test_ranking_is_bars_without_a_legend(engine_db):
    df = pd.DataFrame({"country": ["Ghana", "Nigeria"], "year": [2023, 2023],
                       "internet_users_pct": [65.0, 45.0]})
    spec = v.choose_chart(df, "Rank countries by internet use as a pie chart")
    assert spec["kind"] == "pie"
    spec = v.choose_chart(df, "Rank countries by internet use")
    assert spec["kind"] == "bar" and spec["series"] is None


def test_title_and_short_numbers():
    assert v.chart_title("Show air passengers in Nigeria as a bar chart") == "Air passengers in Nigeria"
    assert [v.short_number(x) for x in (950, 54321, 1.2e6, 0.25)] == ["950", "54.3k", "1.2M", "0.25"]
