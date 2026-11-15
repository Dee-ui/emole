"""The coverage report runs on a built database and writes every section."""
from emole.data.coverage import report


def test_report_has_every_section(built, tmp_path):
    out = tmp_path / "coverage_report.md"
    text = report(db_path=built["out"] / "emole.duckdb", out=out,
                  removed_csv=built["out"] / "processed" / "removed_rows.csv")
    assert out.exists()
    for heading in ("## 1. Columns", "## 2. Flags", "## 3. Nigeria and peers",
                    "## 4. Regions, income groups and blocs", "## 5. Rows removed"):
        assert heading in text
    assert "Nigeria (NGA)" in text
    assert "is_ecowas" in text
    assert "\u2014" not in text                  # no em dashes anywhere (owner's rule)
