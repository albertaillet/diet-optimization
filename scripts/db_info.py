#!/usr/bin/env -S uv run
# Prints info of all tables in the database file given as first argument.
import sys
from pathlib import Path

import duckdb

DATA_DIR = Path(__file__).parent.parent / "data"
db_con = duckdb.connect(Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR / "data.db")
tables = db_con.sql("""SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'""").fetchall()

result_con = duckdb.connect(":memory:")
result_con.sql("""CREATE TABLE result_table (table_name VARCHAR, n_rows INTEGER, n_cols INTEGER, n_cells INTEGER)""")

for table in tables:
    table_name = table[0]
    n_rows = db_con.sql(f"""SELECT COUNT(*) FROM {table_name}""").fetchone()[0]  # type: ignore[reportOptionalSubscript]
    n_cols = db_con.sql(f"""SELECT COUNT(*) FROM pragma_table_info('{table_name}')""").fetchone()[0]  # type: ignore[reportOptionalSubscript]
    result_con.sql(f"""INSERT INTO result_table (table_name, n_rows, n_cols, n_cells)
        VALUES ('{table_name}', {n_rows}, {n_cols}, {n_rows * n_cols})""")

db_con.close()

result_con.sql("""SELECT * FROM result_table ORDER BY n_cells DESC""").show()
result_con.close()
