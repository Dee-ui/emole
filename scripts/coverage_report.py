"""coverage_report.py: write docs/coverage_report.md from data/emole.duckdb.

    python scripts/coverage_report.py

Run it after every build. It shows what data really exists (by column, for Nigeria
and the peer countries, and for every region and bloc) and flags columns to review.
"""
from emole.data.coverage import report

if __name__ == "__main__":
    report()
