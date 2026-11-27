"""Sentences: quick answers, the number check, no causation, and the notes code adds."""
import pandas as pd

from emole.pipeline import names, notes, responder


def test_quick_answer_needs_no_model(engine_db):
    df = pd.DataFrame({"country": ["Nigeria"], "year": [2023], "population": [205000000]})
    assert responder.quick_answer("How many people lived in Nigeria in 2023?", df) == \
        "Nigeria had a population of 205,000,000 in 2023."
    assert responder.quick_answer("How did Nigeria's population change?", df) is None


def test_number_check(engine_db):
    df = pd.DataFrame({"country": ["Ghana"], "year": [2023], "internet_users_pct": [65.0]})
    assert responder.is_grounded("65% of people in Ghana used the internet in 2023.", "q", df)
    assert not responder.is_grounded("70% of people in Ghana used the internet in 2023.", "q", df)


def test_causation_gets_one_rewrite_then_a_template(engine_db, stand_in):
    df = pd.DataFrame({"country": ["Ghana", "Ghana"], "year": [2022, 2023],
                       "internet_users_pct": [60.0, 65.0], "gdp_growth_pct": [None, 5.0]})
    stand_in.answers = ["Internet use rose to 65% in 2023, which caused growth of 5%.",
                        "Because of the internet, growth was 5% in 2023."]
    out = responder.answer("Did internet use cause growth in Ghana?", df)
    assert out["grounded"] is False and out["text"].startswith("Here is what the data shows")
    stand_in.answers = ["Internet use rose to 65% in 2023, which caused growth of 5%.",
                        "In Ghana, internet use went from 60% in 2022 to 65% in 2023, and GDP growth "
                        "was 5% in 2023."]
    out = responder.answer("Did internet use cause growth in Ghana?", df)
    assert out["grounded"] is True and out["rewrites"] == 1


def test_coverage_note_for_a_group(engine_db):
    q = "internet use in ECOWAS in 2023"
    sql = ("SELECT 'ECOWAS' AS group_name, year, pop_avg(internet_users_pct) AS internet_users_pct "
           "FROM country_year WHERE is_ecowas AND year = 2023 GROUP BY year")
    df = pd.DataFrame({"group_name": ["ECOWAS"], "year": [2023], "internet_users_pct": [47.6]})
    got = notes.coverage_notes(sql, df, names.resolve(q))
    assert got == ["The internet users figure is based on 2 of 2 ECOWAS countries with data for 2023 "
                   "(population-weighted average)."]


def test_world_note_and_aviation_caveat(engine_db):
    sql = "SELECT 'World' AS group_name, year, SUM(air_passengers) AS air_passengers FROM country_year " \
          "WHERE year = 2022 GROUP BY year"
    df = pd.DataFrame({"group_name": ["World"], "year": [2022], "air_passengers": [160]})
    all_notes = notes.all_notes("world air passengers in 2022", sql, df, names.resolve("world"))
    assert "total of countries with data (3 of 3)" in all_notes[0]
    assert all_notes[-1] == notes.AVIATION_NOTE


def test_identity_and_opinion_are_answered_in_code(engine_db, stand_in):
    assert responder.chat_answer("Who is Immy?").startswith("I'm Emolé, an expert on Movement")
    assert responder.chat_answer("Which president ruined Nigeria's economy?") == responder.OPINION_REPLY
    assert stand_in.calls == []
