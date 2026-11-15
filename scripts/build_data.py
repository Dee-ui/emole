"""build_data.py: build Emole's database from public data, in one command.

    python scripts/build_data.py                  download what is missing, then build
    python scripts/build_data.py --refresh        download fresh copies of every source
    python scripts/build_data.py --offline        never download; use saved copies in data/raw/
    python scripts/build_data.py --from-snapshot  rebuild data/emole.duckdb from the committed
                                                  snapshot in data/processed/ (no internet)

It writes:
    data/emole.duckdb                      the database Emole reads (git-ignored)
    data/processed/country_year.parquet    the committed snapshot of the table
    data/processed/column_meta.csv         one row per column: unit, rule, source, years
    data/processed/build_info.json         when and how it was built
    data/processed/removed_rows.csv        every group row that was removed, and why
Then run:  python scripts/coverage_report.py
"""
from emole.data.build import main

if __name__ == "__main__":
    main()
