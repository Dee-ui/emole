"""executor.py: run the model's SQL safely against the database.

The SQL is written by a language model, and from Step 4 strangers type the questions.
A clever question could try to make the model write something harmful ("delete the
table", "read /etc/passwd"). So the query must pass FIVE layers before and while it runs:

  1. One statement only, and it must start with SELECT or WITH (the allowlist).
  2. No dangerous keyword: INSERT, DROP, COPY, ATTACH, PRAGMA, SET, INSTALL, LOAD ...
  3. No dangerous function: read_csv, read_parquet, read_json, glob, query() ...
     (query() would run a SQL string hidden inside the query) and no FROM 'file.csv'.
  4. Only the table country_year may be read (DuckDB's own parser lists the tables).
  5. The database is opened READ-ONLY, with external access OFF (no files, no internet,
     no extensions) and the configuration LOCKED, so SQL cannot switch any of it back.

Layers 1 to 4 give a clear reason when they block something; layer 5 holds even if a
trick ever slips past the text checks.
"""
import re

import duckdb

from emole import config

ALLOWED_TABLES = {"country_year"}
MAX_ROWS = config.MAX_ROWS

FORBIDDEN_WORDS = ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "ATTACH",
                   "DETACH", "COPY", "PRAGMA", "INSTALL", "LOAD", "EXPORT", "IMPORT", "CALL", "SET",
                   "RESET", "VACUUM", "CHECKPOINT", "TRUNCATE", "MERGE", "GRANT", "USE",
                   "BEGIN", "COMMIT", "ROLLBACK", "DESCRIBE", "SUMMARIZE", "SHOW")
FORBIDDEN_FUNCTIONS = re.compile(
    r"\b(read_\w+|parquet_\w+|glob|query|query_table|sniff_csv|httpfs\w*|http_\w+|"
    r"sqlite_\w+|postgres_\w+|mysql_\w+|iceberg_\w+|delta_\w+|st_read\w*|duckdb_\w+|"
    r"pragma_\w+|getenv|current_setting|which_secret|load_extension)\s*\(", re.I)


class UnsafeQueryError(Exception):
    """The SQL is not one safe, read-only query on country_year."""


def _strip_strings(sql: str) -> str:
    """Replace the text inside '...' with nothing, so a country name such as
    'Saint Kitts and Nevis' can never look like a keyword."""
    return re.sub(r"'(?:[^']|'')*'", "''", sql)


def validate(sql: str, con=None) -> str:
    """Return the cleaned SQL, or raise UnsafeQueryError with a plain reason.
    con: an open read-only connection (it knows the group-maths macros); one is opened if needed."""
    clean = (sql or "").strip().rstrip(";").strip()
    if not clean:
        raise UnsafeQueryError("Empty query.")
    bare = _strip_strings(clean)
    if ";" in bare:
        raise UnsafeQueryError("Only one statement is allowed. Combine everything into ONE "
                               "SELECT with GROUP BY or IN (no UNION ALL, no second query).")
    if re.search(r"--|/\*", bare):
        raise UnsafeQueryError("Comments are not allowed in the query.")
    head = bare.split(None, 1)[0].upper()
    if head not in ("SELECT", "WITH"):
        raise UnsafeQueryError(f"Only SELECT (or WITH ... SELECT) is allowed, got '{head}'.")
    upper = bare.upper()
    for word in FORBIDDEN_WORDS:
        if re.search(rf"\b{word}\b", upper):
            raise UnsafeQueryError(f"Forbidden keyword: {word}.")
    m = FORBIDDEN_FUNCTIONS.search(bare)
    if m:
        raise UnsafeQueryError(f"Forbidden function: {m.group(1)}().")
    if re.search(r"\b(FROM|JOIN)\s+'", bare, re.I):
        raise UnsafeQueryError("Reading a file by name is not allowed. Use FROM country_year.")
    own = con is None
    con = con or connect()
    try:
        tables = {t.lower() for t in con.get_table_names(clean)}
    except Exception as e:                      # DuckDB could not even read it
        raise UnsafeQueryError(f"The query could not be read: {str(e).splitlines()[0][:200]}") from e
    finally:
        if own:
            con.close()
    other = tables - ALLOWED_TABLES
    if other:
        raise UnsafeQueryError(f"Only the table country_year may be used, not: {', '.join(sorted(other))}.")
    return clean


def connect():
    """A read-only connection that cannot touch any other file, the internet or its
    own settings."""
    if not config.DB_PATH.exists():
        raise FileNotFoundError(f"No database at {config.DB_PATH}. Build it first: "
                                "python scripts/build_data.py --from-snapshot")
    return duckdb.connect(str(config.DB_PATH), read_only=True,
                          config={"enable_external_access": False, "lock_configuration": True})


def run_sql(sql: str):
    """Validate, then run. Returns a DataFrame with at most MAX_ROWS rows;
    df.attrs['truncated'] is True when more rows existed."""
    con = connect()
    try:
        clean = validate(sql, con)
        df = con.execute(f"SELECT * FROM ({clean}) AS q LIMIT {MAX_ROWS + 1}").fetchdf()
    finally:
        con.close()
    truncated = len(df) > MAX_ROWS
    df = df.head(MAX_ROWS).copy()
    df.attrs["truncated"] = truncated
    return df


def query(sql: str, params=None):
    """For the CODE's own queries (catalog, coverage notes), never the model's.
    Still read-only."""
    con = connect()
    try:
        return con.execute(sql, params or []).fetchdf()
    finally:
        con.close()
