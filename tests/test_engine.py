"""engine.ask(), end to end, with a stand-in model and the fixture database."""
from emole import config
from emole.pipeline import engine, llm


def test_single_value_gets_a_quick_sentence(engine_db, stand_in):
    q = "What was Nigeria's population in 2023?"
    stand_in.sql[q] = "SELECT country, year, population FROM country_year WHERE iso3 = 'NGA' AND year = 2023"
    out = engine.ask(q, save_chart_files=False)
    assert out["kind"] == "text" and out["text"] == "Nigeria had a population of 205,000,000 in 2023."
    assert [c[0] for c in stand_in.calls] == ["sql"] and stand_in.calls[0][1] == 0.0   # temperature 0
    assert out["provider"] == "standin:scripted"


def test_year_guard_names_the_measure(real_db, stand_in):
    # real data: air passengers end in 2023, the table runs to 2025
    out = engine.ask("How many air passengers did Nigeria carry in 2025?")
    assert out["kind"] == "no_data" and "latest year I have for air passengers is 2023" in out["text"]
    assert stand_in.calls == []


def test_guards_answer_without_a_model(engine_db, stand_in):
    out = engine.ask("What was GDP growth in Wakanda?")
    assert out["kind"] == "unknown_name"
    out = engine.ask("Who are you?")
    assert out["kind"] == "chat" and "You can call me Immy" in out["text"]
    out = engine.ask("Population in 1950?")
    assert out["kind"] == "no_data" and "from 2022 to 2023" in out["text"]
    assert stand_in.calls == []


def test_group_question_is_fixed_and_carries_its_coverage(engine_db, stand_in):
    q = "What share of people in ECOWAS used the internet in 2023?"
    stand_in.sql[q] = ("SELECT 'ECOWAS' AS group_name, year, AVG(internet_users_pct) AS internet_users_pct "
                       "FROM country_year WHERE is_ecowas AND year = 2023 GROUP BY year")
    stand_in.answers = ["In 2023, 47.63% of people in ECOWAS used the internet."]
    out = engine.ask(q, save_chart_files=False)
    assert out["fixed_in_code"] == ["group maths"] and "pop_avg(internet_users_pct)" in out["sql"]
    assert out["df"]["internet_users_pct"].item() == (45 * 205 + 65 * 31) / 236
    assert "based on 2 of 2 ECOWAS countries with data for 2023 (population-weighted average)" in out["text"]


def test_follow_up_is_rewritten_and_shown(engine_db, stand_in):
    first = "What was Nigeria's population in 2023?"
    second = "What was Ghana's population in 2023?"
    stand_in.sql[second] = ("SELECT country, year, population FROM country_year "
                            "WHERE iso3 = 'GHA' AND year = 2023")
    stand_in.followups["and Ghana?"] = second
    out = engine.ask("and Ghana?", history=[first], save_chart_files=False)
    assert out["resolved"] == second and out["text"] == "Ghana had a population of 31,000,000 in 2023."


def test_failed_sql_is_repaired_once(engine_db, stand_in):
    q = "What was Ghana's internet use in 2023?"
    stand_in.sql[q] = ("SELECT country, year, internet_pct FROM country_year "
                       "WHERE iso3 = 'GHA' AND year = 2023")
    stand_in.repairs = ["SELECT country, year, internet_users_pct FROM country_year "
                        "WHERE iso3 = 'GHA' AND year = 2023"]
    out = engine.ask(q, save_chart_files=False)
    assert out["repaired"] and out["kind"] == "text" and "65.0%" in out["text"]
    assert "internet_pct" in out["checks"][0]


def test_unsafe_sql_never_runs(engine_db, stand_in):
    q = "What was Ghana's population in 2023?"
    stand_in.sql[q] = "SELECT 1 FROM country_year; DROP TABLE country_year"
    stand_in.repairs = ["DROP TABLE country_year"]
    out = engine.ask(q, save_chart_files=False)
    assert out["kind"] == "error" and out["df"] is None


def test_chart_for_several_years(engine_db, stand_in):
    q = "Compare internet use in Nigeria and Ghana over time"
    stand_in.sql[q] = ("SELECT country, year, internet_users_pct FROM country_year "
                       "WHERE iso3 IN ('NGA', 'GHA') ORDER BY country, year")
    out = engine.ask(q, save_chart_files=False)
    assert out["kind"] == "chart" and out["chart"]["kind"] == "line" and out["chart"]["series"] == "country"


def test_evaluator_mode_skips_the_sentence(engine_db, stand_in):
    q = "What was Nigeria's population in 2023?"
    stand_in.sql[q] = "SELECT country, year, population FROM country_year WHERE iso3 = 'NGA' AND year = 2023"
    out = engine.ask(q, phrase=False)
    assert out["text"] == "" and len(out["df"]) == 1 and [c[0] for c in stand_in.calls] == ["sql"]


def test_all_providers_busy(engine_db, monkeypatch):
    def busy(*args):
        raise llm.ProviderError("too many requests (429)")
    monkeypatch.setitem(config.PROVIDERS, "busy", {"kind": "busy"})
    monkeypatch.setitem(llm.SENDERS, "busy", busy)
    monkeypatch.setattr(config, "PROVIDER_CHAIN", ["busy:one", "busy:two"])
    monkeypatch.setattr(config, "EMOLE_MODE", "public")
    out = engine.ask("What was Ghana's population in 2023?")
    assert out["kind"] == "busy" and out["text"] == engine.BUSY_TEXT
