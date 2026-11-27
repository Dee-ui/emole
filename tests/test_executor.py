"""The query runner refuses anything but one read-only query on country_year."""
import pytest

from emole.pipeline import executor
from emole.pipeline.executor import UnsafeQueryError

BLOCKED = {
    "two statements": "SELECT 1 FROM country_year; DROP TABLE country_year",
    "drop": "DROP TABLE country_year",
    "delete inside": "WITH x AS (DELETE FROM country_year) SELECT 1",
    "read a file": "SELECT * FROM read_csv('secret.csv')",
    "parquet": "SELECT * FROM read_parquet('x.parquet')",
    "query()": "SELECT * FROM query('SELECT 1')",
    "file by name": "SELECT * FROM 'data.csv'",
    "copy": "COPY country_year TO 'out.csv'",
    "attach": "ATTACH 'other.duckdb'",
    "pragma": "PRAGMA database_list",
    "set": "SET enable_external_access = true",
    "install": "INSTALL httpfs",
    "other table": "SELECT * FROM column_meta",
    "system table": "SELECT * FROM duckdb_settings()",
    "comment": "SELECT 1 FROM country_year -- hidden",
}


@pytest.mark.parametrize("sql", list(BLOCKED.values()), ids=list(BLOCKED))
def test_dangerous_sql_is_blocked(engine_db, sql):
    with pytest.raises(UnsafeQueryError):
        executor.run_sql(sql)


def test_text_inside_quotes_is_not_a_keyword(engine_db):
    df = executor.run_sql("SELECT country FROM country_year WHERE country = 'Set Drop Copy'")
    assert len(df) == 0


def test_with_select_and_group_macros_work(engine_db):
    df = executor.run_sql("WITH w AS (SELECT * FROM country_year WHERE is_ecowas) "
                          "SELECT year, pop_avg(internet_users_pct) AS v FROM w GROUP BY year ORDER BY year")
    # 2023: Nigeria 45% of 205m and Ghana 65% of 31m -> (45*205 + 65*31) / 236
    assert df.loc[df.year == 2023, "v"].item() == pytest.approx((45 * 205 + 65 * 31) / 236)


def test_row_cap(engine_db, monkeypatch):
    monkeypatch.setattr(executor, "MAX_ROWS", 2)
    df = executor.run_sql("SELECT * FROM country_year")
    assert len(df) == 2 and df.attrs["truncated"] is True
