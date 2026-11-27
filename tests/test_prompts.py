"""The prompt: identity, every worked example valid on the REAL table, and every column described."""
import pytest

from emole.data.sources import load_sources
from emole.pipeline import checks, executor, names, prompts
from emole.pipeline.columns import COLUMNS, columns_in


def test_every_column_has_words_and_a_sentence():
    assert set(COLUMNS) == {c["column"] for c in load_sources()}


def test_identity_and_size(real_db):
    assert prompts.INTRODUCTION == ("I'm Emolé, an expert on Movement, Output, Life and Energy. "
                                    "You can call me Immy.")
    system = prompts.sql_system_prompt()
    assert "Immy" in system and "pop_avg" in system and "NO_SQL" in system
    assert prompts.prompt_size()["estimated_tokens"] > 1000


@pytest.mark.parametrize("question,hints,sql", [f for f in prompts.FEW_SHOTS if f[2] != "NO_SQL"],
                         ids=[f[0][:40] for f in prompts.FEW_SHOTS if f[2] != "NO_SQL"])
def test_worked_examples_run_and_pass_the_checks(real_db, question, hints, sql):
    sql = prompts._fill(sql)
    res = names.resolve(question)
    assert checks.hard_problem(question, res, sql) is None
    assert checks.soft_problem(question, sql) is None
    assert len(executor.run_sql(sql)) > 0


def test_question_words_find_columns():
    assert columns_in("How did air passengers and inflation move?") == ["air_passengers", "inflation_cpi_pct"]
    assert columns_in("renewable electricity share") == ["renewables_share_elec_pct"]
    assert columns_in("access to electricity") == ["electricity_access_pct"]
