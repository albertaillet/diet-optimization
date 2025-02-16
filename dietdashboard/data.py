import os
from pathlib import Path

import duckdb

DATA_DIR = Path(os.getenv("DATA_DIR", "data")).resolve()

QUERIES_DIR = Path(__file__).parent / "queries"
CREATE_CALNUT_QUERY = (QUERIES_DIR / "calnut.sql").read_text()
CREATE_PRODUCTS_QUERY = (QUERIES_DIR / "products.sql").read_text().replace("$products_path", f"'{DATA_DIR / 'food.parquet'}'")


def create_calnut_table(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        CREATE_CALNUT_QUERY,
        parameters={"calnut_0_path": str(DATA_DIR / "calnut.0.csv"), "calnut_1_path": str(DATA_DIR / "calnut.1.csv")},
    )
    # con.execute("CREATE INDEX calnut_alim_code_idx ON calnut (ALIM_CODE)")


def create_food_table(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(CREATE_PRODUCTS_QUERY)


if __name__ == "__main__":
    con = duckdb.connect(":memory:")

    # create_calnut_table(con)

    # con.sql("SELECT * FROM calnut").to_csv("calnut_sample.csv")

    create_food_table(con)

    # con.sql("SELECT * FROM products").to_csv("products_sample.csv")
