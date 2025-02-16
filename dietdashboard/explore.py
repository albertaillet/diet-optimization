# %%
import csv
import json
from pathlib import Path

import duckdb

data_path = Path.cwd().parent / "data"
prices = data_path / "prices.parquet"
food = data_path / "food.parquet"
calnut_0 = data_path / "calnut.0.csv"
calnut_1 = data_path / "calnut.1.csv"
nutrient_map = data_path / "nutrient_map.csv"

# %%
duckdb.sql(f"SELECT * FROM read_parquet('{prices}') LIMIT 1").show()

# %%
duckdb.sql(f"DESCRIBE SELECT * FROM read_parquet('{prices}')").show()

# %%
owner_id = duckdb.sql(f"""
    WITH data AS (SELECT * FROM read_parquet('{prices}')),
    swiss_owners AS (
        SELECT DISTINCT owner
        FROM data
        WHERE location_osm_address_country = 'Schweiz/Suisse/Svizzera/Svizra'
    ),
    french_owners AS (
        SELECT DISTINCT owner
        FROM data
        WHERE location_osm_address_country = 'France'
    )
    SELECT swiss_owners.owner
    FROM swiss_owners
    INNER JOIN french_owners ON swiss_owners.owner = french_owners.owner
    LIMIT 1
""").fetchone()
assert owner_id is not None
owner_id = owner_id[0]

# %%
duckdb.sql(f"""
    SELECT location_osm_address_city
    FROM read_parquet('{prices}')
    WHERE owner = '{owner_id}'
""").show()

# %%
duckdb.sql(f"SELECT * FROM read_parquet('{food}') LIMIT 1").show()

# %%
duckdb.sql(f"DESCRIBE SELECT * FROM read_parquet('{food}')").show()

# %%

with (Path.cwd().parent / "tmp.txt").open("w") as f:
    columns = duckdb.sql(f"SELECT * FROM read_parquet('{food}') LIMIT 0").columns
    for col in columns:
        f.write(f"{col},\n")

# %%
# Create a persistent connection
con = duckdb.connect(":memory:")

# Create and register the tables
con.sql(f"""
  CREATE TABLE my_data AS
  SELECT *
  FROM read_parquet('{prices}') AS prices
  LEFT JOIN read_parquet('{food}') AS food ON prices.product_code = food.code
  WHERE prices.owner = '{owner_id}'
""")

# %%
con.sql("SELECT * FROM my_data").to_csv("my_data.csv")

# %%
# Extract only the valuable information
con.sql("""
SELECT
  code,
  product_name,
  ingredients_text,
  allergens_tags,
  nutriments,
  location_osm_address_country,
  location_osm_lat,
  location_osm_lon,
  product_code,
  price,
  date,
  ciqual_food_name_tags,
  ingredients,
FROM my_data
""")


# %%
nutriments_data = con.sql("SELECT nutriments FROM my_data").fetchall()
with (Path.cwd().parent / "nutriments.json").open("w") as f:
    json.dump([row[0] for row in nutriments_data], f, indent=2)

# %%
nutriments_names = set()
for row in nutriments_data:
    if row[0] is None:
        continue
    nutriments_names.update(nutriment["name"] for nutriment in row[0])

print("Unique nutriment names:")
for name in sorted(nutriments_names):
    print(name)

# %%
con.sql("SELECT ingredients_text FROM my_data").show()
# %%
# Documentation here: https://ciqual.anses.fr/cms/sites/default/files/inline-files/Table%20CALNUT%202020_doc_FR_2020%2007%2007.pdf
# From table 1 we get upper_bound, lower_bound, mean, and an indicator of the completeness of the data
# From table 0 we get the food group and subgroup
# Both tables are linked by the ALIM_CODE and FOOD_LABEL columns
duckdb.sql(f"SELECT * FROM read_csv('{calnut_1}')").show()

# %%
duckdb.sql(f"""
  SELECT DISTINCT indic_combl
  FROM read_csv('{calnut_1}')
  ORDER BY ALIM_CODE, CONST_LABEL
""").show()

# %%
# First get all unique CONST_LABELs
const_labels = duckdb.sql(f"""
  SELECT DISTINCT CONST_LABEL
  FROM read_csv('{calnut_1}')
  ORDER BY CONST_LABEL
""").fetchall()

# %%
duplicates = duckdb.sql(f"""
  SELECT COUNT(*)
  FROM read_csv('{calnut_1}')
  GROUP BY ALIM_CODE, CONST_LABEL
  HAVING COUNT(*) > 1
""").fetchall()
assert len(duplicates) == 0, "Found duplicate combinations of ALIM_CODE and CONST_LABEL"


# %%
def make_pivot_column(label, stat):
    if stat == "combl":
        return f"MAX(CAST(CASE WHEN CONST_LABEL = '{label}' THEN combl END AS INT)) as {label}_combl"
    return f"MAX(CAST(CASE WHEN CONST_LABEL = '{label}' THEN REPLACE({stat}, ',', '.') END AS FLOAT)) as {label}_{stat}"


# %%
pivot_expressions = ",\n".join([
    make_pivot_column(label[0], stat) for label in const_labels for stat in ["lb", "mean", "ub", "combl"]
])

# Available columns:
# ALIM_CODE,FOOD_LABEL,indic_combl,LB,UB,MB,CONST_CODE,CONST_LABEL
query = f"""
  WITH source AS (
  SELECT
  ALIM_CODE,
  FOOD_LABEL,
  CONST_LABEL,
  LB as lb,
  UB as ub,
  MB as mean,
  indic_combl as combl
  FROM read_csv('{calnut_1}')
  )
  SELECT
  ALIM_CODE,
  FOOD_LABEL,
  {pivot_expressions}
  FROM source
  GROUP BY ALIM_CODE, FOOD_LABEL
"""

duckdb.sql(query).to_csv("calnut_pivoted.csv")

# %%
# Queries to get an example table to add as documentation
# Before:
duckdb.sql(f"""
    SELECT * FROM read_csv('{calnut_1}')
    WHERE (FOOD_LABEL == 'Gruyère' OR FOOD_LABEL == 'Saint-Marcellin') AND
          (CONST_LABEL == 'lipides_g' OR CONST_LABEL == 'proteines_g')
""").show()

# After:
pivot_expressions_example = ",\n".join([
    make_pivot_column(label, stat) for label in ["lipides_g", "proteines_g"] for stat in ["lb", "mean", "ub", "combl"]
])
duckdb.sql(f"""
  WITH source AS (
  SELECT
  ALIM_CODE,
  FOOD_LABEL,
  CONST_LABEL,
  LB as lb,
  UB as ub,
  MB as mean,
  indic_combl as combl
  FROM read_csv('{calnut_1}')
  WHERE (FOOD_LABEL == 'Gruyère' OR FOOD_LABEL == 'Saint-Marcellin') AND
        (CONST_LABEL == 'lipides_g' OR CONST_LABEL == 'proteines_g')
  )
  SELECT
  ALIM_CODE,
  FOOD_LABEL,
  {pivot_expressions_example}
  FROM source
  GROUP BY ALIM_CODE, FOOD_LABEL
""").show(max_width=10000)  # type: ignore


# %%
# From columns to get from this:
# alim_code,FOOD_LABEL,alim_grp_code,alim_grp_nom_fr,alim_ssgrp_code,alim_ssgrp_nom_fr,alim_ssssgrp_code,alim_ssssgrp_nom_fr
duckdb.sql(f"""SELECT
  ALIM_CODE,FOOD_LABEL,
  alim_grp_code,alim_grp_nom_fr,
  alim_ssgrp_code,alim_ssgrp_nom_fr,
  alim_ssssgrp_code,alim_ssssgrp_nom_fr
  FROM read_csv('{calnut_0}')""").show()

# %%

con = duckdb.connect(":memory:")

# Create and register the tables
con.sql("CREATE TABLE products AS SELECT * FROM read_parquet($products_path) LIMIT 10000", params={"products_path": str(food)})

# %%
con.sql("SELECT * FROM products LIMIT 2").show()

# %%
# countries_tags
# can look like this: ["en:france", "en:switzerland"]
# filter out all products that are from either France or Switzerland
duckdb.sql(
    """
SELECT
  code,
  quantity,
  nutriments,
FROM read_parquet($products_path)
WHERE code IS NOT NULL AND
      'en:france' IN countries_tags OR 'en:switzerland' IN countries_tags
LIMIT 1000
""",
    params={"products_path": str(food)},
).to_csv("products_sample.csv")

# %%
duckdb.sql(f"DESCRIBE SELECT nutriments FROM read_parquet('{food}')").show(max_width=10000)  # type: ignore
# ┌─────────────┬───────────────┬─────────┬─────────┬─────────┬─────────┐
# │ column_name │  column_type  │  null   │   key   │ default │  extra  │
# │   varchar   │    varchar    │ varchar │ varchar │ varchar │ varchar │
# ├─────────────┼───────────────┼─────────┼─────────┼─────────┼─────────┤
# │ nutriments  │ STRUCT(...)[] │ YES     │ NULL    │ NULL    │ NULL    │
# └─────────────┴───────────────┴─────────┴─────────┴─────────┴─────────┘
# Where STRUCT(...)[] =
# STRUCT("name" VARCHAR,
#        "value" FLOAT,
#        "100g" FLOAT,
#        serving FLOAT,
#        unit VARCHAR,
#        prepared_value FLOAT,
#        prepared_100g FLOAT,
#        prepared_serving FLOAT,
#        prepared_unit VARCHAR)[]

# %%
# Get all unique nutriment names with their counts
duckdb.sql(
    """
WITH products AS (
  SELECT nutriments
  FROM read_parquet($products_path)
  WHERE nutriments IS NOT NULL
)
SELECT
  t.unnest.name,
  COUNT(*) as count
FROM products, UNNEST(nutriments) AS t
GROUP BY t.unnest.name
ORDER BY count DESC
""",
    params={"products_path": str(food)},
).to_csv("nutriments_names_n.csv")

# %%
# Get all unique nutriment names with their counts
nutrients_to_add = [row["off_id"] for row in csv.DictReader(nutrient_map.open()) if row["off_id"]]

# %%
nutrients_to_add, len(nutrients_to_add)
# %%
top_nutriments = [row["name"] for row in csv.DictReader(open("nutriments_names_n.csv"))]  # noqa: SIM115, PTH123

# %%
set(top_nutriments[:45]) - set(nutrients_to_add)

# %%
set(nutrients_to_add) - set(top_nutriments[:105])

# %%
unnest_expressions = ",\n".join([
    f"""
      MAX(CAST(CASE WHEN t.unnest.name = '{nutriment}' THEN t.unnest.value END AS FLOAT)) as {nutriment}
"""
    for nutriment in nutrients_to_add
])
unnest_query = f"""
WITH products AS (
  SELECT nutriments
  FROM read_parquet($products_path)
  WHERE nutriments IS NOT NULL
  LIMIT 100
)
SELECT
  code,
  quantity,
  {unnest_expressions}
FROM products, UNNEST(nutriments) AS t
GROUP BY code, quantity
"""
print(unnest_query)

duckdb.sql(
    unnest_query,
    params={"products_path": str(food)},
).to_csv("products_sample.csv")

# %%
