#!/usr/bin/env -S uv run --extra sql
"""This script creates a subset of the data and prints the intermediate tables for debugging."""

from pathlib import Path

import duckdb
import sqlglot
import sqlglot.expressions as exp

# sqlglot.pretty = True  # Enable pretty printing
DATA_DIR = Path(__file__).parent.parent / "data"

con = duckdb.connect(":memory:")
# Attach the explore database with the full data to the in-memory database,
# Then create a subset of the tables for the example
con.sql(f"ATTACH DATABASE '{DATA_DIR / 'data.db'}' AS full_tables;")
con.sql("""
CREATE OR REPLACE TABLE nutrient_map AS
SELECT * FROM full_tables.nutrient_map
WHERE id IN ('sodium', 'protein');

CREATE OR REPLACE TABLE ciqual_alim AS
SELECT * FROM full_tables.ciqual_alim
WHERE alim_code IN ('20516', '20904');

CREATE OR REPLACE TABLE ciqual_compo AS
SELECT * FROM full_tables.ciqual_compo
WHERE const_code in ('10110', '25000')
AND alim_code IN ('20516', '20904');

CREATE OR REPLACE TABLE calnut_0 AS
SELECT * FROM full_tables.calnut_0
WHERE alim_code IN ('20516', '20904');

CREATE OR REPLACE TABLE calnut_1 AS
SELECT * FROM full_tables.calnut_1
WHERE CONST_CODE in ('10110', '25000') -- Same as CONST_LABEL in ('sodium_mg', 'proteines_g')
AND ALIM_CODE IN ('20516', '20904');

CREATE OR REPLACE TABLE prices AS
SELECT * FROM full_tables.prices
WHERE product_code IN ('3111950001928', '4099200179193');

CREATE OR REPLACE TABLE products AS
SELECT code, product_quantity, product_name, product_quantity_unit, product_quantity,
ciqual_food_code, ciqual_food_code_origin, nutriments
FROM full_tables.products WHERE code IN ('3111950001928', '4099200179193');
""")


def print_tables(*tables: str):
    for table in tables:
        print(f'Table "{table}"')
        con.table(table).show()


print_tables("nutrient_map", "ciqual_alim", "ciqual_compo", "calnut_1", "products", "prices")

process_query_path = Path(__file__).parent / "queries/process.sql"
process_query = process_query_path.read_text()
expression = sqlglot.parse_one(process_query)
# --- Replace the chosen nutrients in the pivot expression ---
expression.find(exp.Pivot).find(exp.In).args["expressions"] = ["sodium", "protein"]  # type: ignore[reportOptionalMemberAccess]
# --- Run each CTE as a CREATE TABLE statement ---
for cte_expression in expression.find(exp.With).expressions:  # type: ignore[reportOptionalMemberAccess]
    table = exp.Table(this=exp.Identifier(this=cte_expression.alias))
    create_table = exp.Create(this=table, kind="TABLE", expression=cte_expression.this)
    con.execute(create_table.sql())
    print(f'Table "{table.name}"')
    con.table(table.name).show()
