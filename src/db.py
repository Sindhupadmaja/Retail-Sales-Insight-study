"""Load the raw CSVs into an in-memory DuckDB database and run the SQL model and queries."""
import re

import duckdb


def connect(raw_dir, tables):
    con = duckdb.connect()
    for name, file in tables.items():
        con.execute(f"CREATE TABLE {name} AS SELECT * FROM read_csv_auto(?, header=true)",
                    [str(raw_dir / file)])
    return con


def run_script(con, path):
    con.execute(path.read_text())


def load_queries(path):
    """Split a .sql file into named queries using '-- name: <query>' markers."""
    parts = re.split(r"^-- name:\s*(\w+)\s*$", path.read_text(), flags=re.M)
    return {name: sql.strip().rstrip(";") for name, sql in zip(parts[1::2], parts[2::2])}


def query(con, sql, params=None):
    return con.execute(sql, params or {}).df()
