import os
from pathlib import Path

import duckdb

DATA_DIR = Path(os.getenv("DATA_DIR", "data")).resolve()

QUERIES_DIR = Path(__file__).parent / "queries"
CREATE_CALNUT_QUERY = (QUERIES_DIR / "calnut.sql").read_text()


def create_calnut_table(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        CREATE_CALNUT_QUERY,
        parameters={"calnut_0_path": str(DATA_DIR / "calnut.0.csv"), "calnut_1_path": str(DATA_DIR / "calnut.1.csv")},
    )


if __name__ == "__main__":
    con = duckdb.connect(":memory:")

    create_calnut_table(con)

    con.sql("SELECT * FROM calnut").to_csv("calnut_sample.csv")
