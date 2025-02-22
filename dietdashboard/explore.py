# %%
import re
from pathlib import Path

import duckdb

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "explore.db"
con = duckdb.connect(DB_PATH)

# %%
# Get the owners that have prices in both Switzerland and France
owner_id = con.sql("""
    WITH
    swiss_owners AS (
        SELECT DISTINCT owner
        FROM prices
        WHERE location_osm_address_country = 'Schweiz/Suisse/Svizzera/Svizra'
    ),
    french_owners AS (
        SELECT DISTINCT owner
        FROM prices
        WHERE location_osm_address_country = 'France'
    )
    SELECT swiss_owners.owner
    FROM swiss_owners
    INNER JOIN french_owners ON swiss_owners.owner = french_owners.owner
    LIMIT 1
""").fetchone()
assert owner_id is not None
owner_id = owner_id[0]
print(owner_id)

# %%
# Get the data for the owner and save it to a CSV file
con.sql(
    """SELECT products.code, products.product_name, price, location_osm_display_name, -- prices.*
    FROM prices
    LEFT JOIN products ON prices.product_code = products.code
    WHERE prices.owner = $owner_id""",
    params={"owner_id": owner_id},
).to_csv("owner_data.csv")

# %%
# Pivot the ciqual 1 table to have on column per CONST_LABEL
# Get the unique values for the CONST_LABEL columns
const_labels = con.sql("SELECT DISTINCT CONST_LABEL FROM calnut_1 ORDER BY CONST_LABEL").fetchall()

# First get all unique CONST_LABELs
duplicates = con.sql("""
  SELECT COUNT(*)
  FROM calnut_1
  GROUP BY ALIM_CODE, CONST_LABEL
  HAVING COUNT(*) > 1
""").fetchall()
assert len(duplicates) == 0, "Found duplicate combinations of ALIM_CODE and CONST_LABEL"

# Available columns:
# ALIM_CODE,FOOD_LABEL,indic_combl,LB,UB,MB,CONST_CODE,CONST_LABEL
const_labels_str = str(tuple(label[0] for label in const_labels))
con.sql(f"""
  SELECT *
  FROM calnut_1
  PIVOT (
    first(lb) AS lb,
    first(mean) AS mean,
    first(ub) AS ub,
    first(combl) AS combl
    FOR CONST_LABEL IN
    {const_labels_str}
    GROUP BY ALIM_CODE, FOOD_LABEL
  )
""")

# %%
# Queries to get an example table to add as documentation
# Before:
con.sql("""DROP TABLE IF EXISTS example_before;
CREATE TABLE example_before AS SELECT * FROM calnut_1
WHERE (FOOD_LABEL == 'Gruyère' OR FOOD_LABEL == 'Saint-Marcellin') AND
      (CONST_LABEL == 'proteines_g' OR CONST_LABEL == 'ag_20_4_ara_g')
""")
con.sql("SELECT * FROM example_before").show()

# After:
con.sql("""
SELECT * FROM example_before
PIVOT (
  first(lb) AS lb,
  first(mean) AS mean,
  first(ub) AS ub,
  first(combl) AS combl
  FOR CONST_LABEL IN
  ('proteines_g', 'ag_20_4_ara_g')
  GROUP BY ALIM_CODE, FOOD_LABEL
);
""").show(max_width=10000)  # type: ignore

# %%
# One row per product and nutriment
con.sql("""
SELECT
  p.code,
  v.nutrient_name,
  v.nutrient_value,
  v.nutrient_unit,
  v.nutrient_100g
FROM (SELECT * FROM products LIMIT 50) p
CROSS JOIN LATERAL (
  VALUES
    ('sodium',         p.nutriments.sodium_value,         p.nutriments.sodium_unit,         p.nutriments.sodium_100g),
    ('proteins',       p.nutriments.proteins_value,       p.nutriments.proteins_unit,       p.nutriments.proteins_100g),
    ('fat',            p.nutriments.fat_value,            p.nutriments.fat_unit,            p.nutriments.fat_100g),
    ('carbohydrates',  p.nutriments.carbohydrates_value,  p.nutriments.carbohydrates_unit,  p.nutriments.carbohydrates_100g),
    ('sugars',         p.nutriments.sugars_value,         p.nutriments.sugars_unit,         p.nutriments.sugars_100g)
) AS v(nutrient_name, nutrient_value, nutrient_unit, nutrient_100g)
WHERE v.nutrient_value IS NOT NULL
""")

# %%
# One row per product and a column for each nutriment
con.sql("""
SELECT
  code,
  nutriments.sodium_value AS sodium_value,
  nutriments.sodium_unit AS sodium_unit,
  nutriments.sodium_100g AS sodium_100g,
  nutriments.proteins_value AS proteins_value,
  nutriments.proteins_unit AS proteins_unit,
  nutriments.proteins_100g AS proteins_100g,
  nutriments.fat_value AS fat_value,
  nutriments.fat_unit AS fat_unit,
  nutriments.fat_100g AS fat_100g,
  nutriments.carbohydrates_value AS carbohydrates_value,
  nutriments.carbohydrates_unit AS carbohydrates_unit,
  nutriments.carbohydrates_100g AS carbohydrates_100g,
  nutriments.sugars_value AS sugars_value,
  nutriments.sugars_unit AS sugars_unit,
  nutriments.sugars_100g AS sugars_100g
FROM products LIMIT 50;
""")

# %%
# One row per product and a column for each nutriment by using struct unpacking
# https://duckdb.org/docs/sql/data_types/struct#struct
con.sql("""SELECT code, nutriments.* FROM products LIMIT 50""")

# %%
# I wan to find a price about chickpeas
con.sql("""
SELECT id, product_code, product_name
FROM prices
WHERE product_code IN (
  SELECT code
  FROM products
  WHERE product_name LIKE '%pois%' AND product_name IS NOT NULL
)
""")
# %%
# Close the connection to explore.db
con.close()

# %%
# Connect to the in-memory database
con = duckdb.connect(":memory:")
# Attach the explore database with the full data to the in-memory database,
# Then create a subset of the tables for the example
con.sql(f"ATTACH DATABASE '{DATA_DIR / 'data.db'}' AS full_tables;")
con.sql("""
CREATE OR REPLACE TABLE nutrient_map AS
SELECT id, calnut_name, calnut_unit, calnut_const_code, off_id
FROM full_tables.nutrient_map WHERE id IN ('sodium', 'protein');

CREATE OR REPLACE TABLE calnut_0 AS
SELECT * FROM full_tables.calnut_0
WHERE alim_code IN ('20532', '20904', '19644');

CREATE OR REPLACE TABLE calnut_1 AS
SELECT * FROM full_tables.calnut_1
WHERE CONST_LABEL in ('sodium_mg', 'proteines_g')
AND ALIM_CODE IN ('20532', '20904', '19644');

CREATE OR REPLACE TABLE prices AS
SELECT id, product_code, price, currency, date, owner, location_osm_display_name, location_osm_id
FROM full_tables.prices WHERE product_code IN ('3111950001928', '4099200179193');

CREATE OR REPLACE TABLE products AS
SELECT code, product_quantity, product_name, product_quantity_unit, product_quantity,
ciqual_food_code, ciqual_food_code_origin, nutriments
FROM full_tables.products WHERE code IN ('3111950001928', '4099200179193');
""")


# %%
def print_tables(*tables: str):
    for table in tables:
        print(f'Table "{table}"')
        con.table(table).show(max_width=10000)  # type: ignore


print_tables("nutrient_map", "calnut_0", "calnut_1", "products", "prices")

# %%
process_query_path = Path(__file__).parent / "queries/process.sql"
process_query = process_query_path.read_text()
process_query = re.sub(r"^\s*\('(?!sodium|protein)[^']*',.*?\),?$\n", "", process_query, flags=re.MULTILINE)
process_query = re.sub(r"\('\w+'(?:,\s+'\w+'\s?)+\)", "('sodium', 'protein')", process_query)
con.execute(process_query)

# %%
print_tables("products_with_ciqual_and_price", "products_nutriments", "products_nutriments_selected", "final_nutrient_table")

# %%
