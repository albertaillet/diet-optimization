# %%
import json
from pathlib import Path

import duckdb

# %%
data_path = Path.cwd().parent / "data"
# %%
prices = data_path / "prices.parquet"

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
food = data_path / "food.parquet"
duckdb.sql(f"SELECT * FROM read_parquet('{food}') LIMIT 1").show()

# %%
duckdb.sql(f"DESCRIBE SELECT * FROM read_parquet('{food}')").show()

# %%

with (Path.cwd().parent / "tmp.txt").open("w") as f:
    columns = duckdb.sql(f"SELECT * FROM read_parquet('{food}') LIMIT 0").columns
    for col in columns:
        f.write(f"{col}\n")

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
calnut_1 = data_path / "calnut.1.csv"
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
# From columns to get from this:
# alim_code,FOOD_LABEL,alim_grp_code,alim_grp_nom_fr,alim_ssgrp_code,alim_ssgrp_nom_fr,alim_ssssgrp_code,alim_ssssgrp_nom_fr
calnut_0 = data_path / "calnut.0.csv"
duckdb.sql(f"""SELECT
  ALIM_CODE,FOOD_LABEL,
  alim_grp_code,alim_grp_nom_fr,
  alim_ssgrp_code,alim_ssgrp_nom_fr,
  alim_ssssgrp_code,alim_ssssgrp_nom_fr
  FROM read_csv('{calnut_0}')""").show()

# %%
