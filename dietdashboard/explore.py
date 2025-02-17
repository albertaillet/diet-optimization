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
products = data_path / "openfoodfacts-products.jsonl.gz"

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
const_labels = duckdb.sql(f"""
  SELECT DISTINCT CONST_LABEL, CONST_CODE
  FROM read_csv('{calnut_1}')
  ORDER BY CONST_LABEL
""").fetchall()

# write to a file
with (Path.cwd().parent / "const_labels.csv").open("w") as f:
    writer = csv.writer(f)
    writer.writerow(["CONST_LABEL", "UNIT", "CONST_CODE"])
    for row in const_labels:
        unit = row[0].split("_")[-1]
        label = row[0].replace(f"_{unit}", "")
        writer.writerow([label, unit, row[1]])

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

# Available columns:
# ALIM_CODE,FOOD_LABEL,indic_combl,LB,UB,MB,CONST_CODE,CONST_LABEL
const_labels_str = str(tuple(label[0] for label in const_labels))
query = f"""
  WITH source AS (
  SELECT ALIM_CODE, FOOD_LABEL, CONST_LABEL, CONST_CODE,
  CAST(indic_combl AS BOOL) as combl,
  CAST(REPLACE(LB, ',', '.') AS FLOAT) as lb,
  CAST(REPLACE(UB, ',', '.') AS FLOAT) as ub,
  CAST(REPLACE(MB, ',', '.') AS FLOAT) as mean,
  FROM read_csv('{calnut_1}')
  )
  SELECT *
  FROM source
  PIVOT (
    first(lb) AS lb,
    first(mean) AS mean,
    first(ub) AS ub,
    first(combl) AS combl
    FOR CONST_LABEL IN
    {const_labels_str}
    GROUP BY ALIM_CODE, FOOD_LABEL
  )
"""
print(query)
duckdb.sql(query).to_csv("calnut_pivoted.csv")

# %%
# Queries to get an example table to add as documentation
# Before:
con = duckdb.connect(":memory:")
con.sql(f"""
    CREATE TABLE example_before AS
    SELECT ALIM_CODE, FOOD_LABEL, CONST_LABEL, CONST_CODE,
    CAST(indic_combl AS BOOL) as combl,
    CAST(REPLACE(LB, ',', '.') AS FLOAT) as lb,
    CAST(REPLACE(UB, ',', '.') AS FLOAT) as ub,
    CAST(REPLACE(MB, ',', '.') AS FLOAT) as mean,
    FROM read_csv('{calnut_1}')
    WHERE (FOOD_LABEL == 'Gruyère' OR FOOD_LABEL == 'Saint-Marcellin') AND
          (CONST_LABEL == 'proteines_g' OR CONST_LABEL == 'ag_20_4_ara_g')
""")
con.sql("SELECT * FROM example_before").show()

# After:
con.sql("""
SELECT *
FROM example_before
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
con.close()

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
duckdb.sql(
    """
WITH products AS (
  SELECT code, nutriments
  FROM read_parquet($products_path)
  WHERE nutriments IS NOT NULL
  LIMIT 100
)
SELECT code, t.unnest.name, t.unnest.value, t.unnest."100g", t.unnest.serving, t.unnest.unit
FROM products, UNNEST(nutriments) AS t
""",
    params={"products_path": str(food)},
).to_csv("products_sample.csv")

# %%
duckdb.sql(f"SELECT count(*) FROM read_ndjson('{products}', ignore_errors=True)")
# 3667647
# %%
columns = duckdb.sql(f"SELECT * FROM read_ndjson('{products}', ignore_errors=True) LIMIT 1").columns

# %%
# Write all the columns to a file
f = ["ingredients", "_name", "packaging", "origin", "nutri"]
filtered_columns = [col for col in columns if not any(s in col for s in f)]
with (Path.cwd().parent / "tmp.txt").open("w") as f:
    for col in sorted(filtered_columns):
        f.write(f"{col},\n")

# describe the categories_properties column
duckdb.sql(f"""
DESCRIBE SELECT categories_properties FROM read_ndjson('{products}')
""").show()

# %%
duckdb.sql(f"SELECT count(*) FROM read_ndjson('{products}', ignore_errors=True)")

# %%
con = duckdb.connect(":memory:")

# Create and register the tables
con.sql(f"""
  CREATE TABLE products AS
    SELECT
    code,
    countries_tags,
    ecoscore_score,
    nova_group,
    nutriments,
    nutriscore_score,
    product_name,
    product_quantity_unit,
    product_quantity,
    quantity,
    categories_properties,
  FROM read_ndjson('{products}')
  WHERE code IS NOT NULL AND nutriments IS NOT NULL AND
      'en:france' IN countries_tags OR 'en:switzerland' IN countries_tags
  ORDER BY last_modified_t DESC
  LIMIT 1000
""")

# %%
con.sql("SELECT code, nutriments FROM products LIMIT 10").show()

# %%
# One row per product and nutriment
con.sql("""
        SELECT
  p.code,
  v.nutrient_name,
  v.nutrient_value,
  v.nutrient_unit,
  v.nutrient_100g
FROM products p
CROSS JOIN LATERAL (
  VALUES
    ('sodium',         p.nutriments.sodium_value,         p.nutriments.sodium_unit,         p.nutriments.sodium_100g),
    ('proteins',       p.nutriments.proteins_value,       p.nutriments.proteins_unit,       p.nutriments.proteins_100g),
    ('fat',            p.nutriments.fat_value,            p.nutriments.fat_unit,            p.nutriments.fat_100g),
    ('carbohydrates',  p.nutriments.carbohydrates_value,  p.nutriments.carbohydrates_unit,  p.nutriments.carbohydrates_100g),
    ('sugars',         p.nutriments.sugars_value,         p.nutriments.sugars_unit,         p.nutriments.sugars_100g)
) AS v(nutrient_name, nutrient_value, nutrient_unit, nutrient_100g)
WHERE v.nutrient_value IS NOT NULL;
""").show()

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
FROM products;
""").show()

# %%
# One row per product and a column for each nutriment by using struct unpacking
# https://duckdb.org/docs/sql/data_types/struct#struct
con.sql("""
SELECT
  code,
  nutriments.*
FROM products;
""").show()

# %%
con.sql("""
SELECT code, categories_properties FROM products LIMIT 1000
""").show()

# %%
con.sql("""
SELECT
  code,
  COALESCE(
    categories_properties['ciqual_food_code:en'],
    categories_properties['agribalyse_food_code:en'],
    categories_properties['agribalyse_proxy_food_code:en']
  ) AS ciqual_food_code,
  CASE
    WHEN categories_properties['ciqual_food_code:en'] IS NOT NULL THEN 'ciqual'
    WHEN categories_properties['agribalyse_food_code:en'] IS NOT NULL THEN 'agribalyse'
    WHEN categories_properties['agribalyse_proxy_food_code:en'] IS NOT NULL THEN 'agribalyse_proxy'
    ELSE 'unknown'
  END AS ciqual_food_code_origin
FROM products
""").show()

# %%
# Try to merge the two tables
con = duckdb.connect(":memory:")

# Create and register the tables
con.sql(
    """CREATE TABLE products AS
SELECT code, nutriments, categories_properties,
FROM read_ndjson('$products_path')
WHERE code IS NOT NULL AND nutriments IS NOT NULL AND
    'en:france' IN countries_tags OR 'en:switzerland' IN countries_tags
LIMIT 1000
""".replace("$products_path", str(products))
)

# %%
con.sql(
    """DROP TABLE IF EXISTS calnut_0;
CREATE TABLE calnut_0 AS
SELECT ALIM_CODE, FOOD_LABEL, CONST_LABEL, CONST_CODE,
CAST(indic_combl AS BOOL) as combl,
CAST(REPLACE(LB, ',', '.') AS FLOAT) as lb,
CAST(REPLACE(UB, ',', '.') AS FLOAT) as ub,
CAST(REPLACE(MB, ',', '.') AS FLOAT) as mean,
FROM read_csv('$calnut_1')
""".replace("$calnut_1", str(calnut_1))
)
# %%
con.sql("""DROP TABLE IF EXISTS products_ciqual;
CREATE TABLE products_ciqual AS
SELECT
code,
COALESCE(
    categories_properties['ciqual_food_code:en'],
    categories_properties['agribalyse_food_code:en'],
    categories_properties['agribalyse_proxy_food_code:en']
) AS ciqual_food_code,
CASE
    WHEN categories_properties['ciqual_food_code:en'] IS NOT NULL THEN 'ciqual'
    WHEN categories_properties['agribalyse_food_code:en'] IS NOT NULL THEN 'agribalyse'
    WHEN categories_properties['agribalyse_proxy_food_code:en'] IS NOT NULL THEN 'agribalyse_proxy'
    ELSE 'unknown'
END AS ciqual_food_code_origin,
nutriments,
FROM products
WHERE categories_properties IS NOT NULL
""")

# %%
con.sql("""DROP TABLE IF EXISTS products_nutriments;
CREATE TABLE products_nutriments AS
SELECT
code,
ciqual_food_code,
ciqual_food_code_origin,
p.code,
v.nutrient_name,
v.nutrient_value,
v.nutrient_unit,
v.nutrient_100g
FROM products_ciqual p
CROSS JOIN LATERAL (
  VALUES
    ('proteins',       p.nutriments.proteins_value,       p.nutriments.proteins_unit,       p.nutriments.proteins_100g),
    ('fat',            p.nutriments.fat_value,            p.nutriments.fat_unit,            p.nutriments.fat_100g),
    ('carbohydrates',  p.nutriments.carbohydrates_value,  p.nutriments.carbohydrates_unit,  p.nutriments.carbohydrates_100g),
    ('sugars',         p.nutriments.sugars_value,         p.nutriments.sugars_unit,         p.nutriments.sugars_100g),
    ('sodium',         p.nutriments.sodium_value,         p.nutriments.sodium_unit,         p.nutriments.sodium_100g),
) AS v(nutrient_name, nutrient_value, nutrient_unit, nutrient_100g)
WHERE v.nutrient_value IS NOT NULL
""")

# %%
# Show the tables
print("TABLE products_nutriments:")
con.sql("SELECT * FROM products_nutriments LIMIT 5").show(max_width=10000)  # type: ignore
print("TABLE calnut_0:")
con.sql("SELECT * FROM calnut_0 LIMIT 5").show(max_width=10000)  # type: ignore

# %%
con.sql("""
SELECT
  p.code,
  p.ciqual_food_code,
  p.ciqual_food_code_origin,
  p.nutrient_name,
  p.nutrient_value,
  p.nutrient_unit,
  p.nutrient_100g,
  c.ALIM_CODE,
  c.FOOD_LABEL,
  c.CONST_LABEL,
  c.CONST_CODE,
  c.combl,
  c.lb,
  c.ub,
  c.mean,
  -- Merge the two source indicators into one
  CASE
    WHEN p.ciqual_food_code_origin NOT IN ('ciqual', 'agribalyse', 'agribalyse_proxy')
      THEN 'product'
    WHEN p.ciqual_food_code_origin = 'ciqual' THEN
      CASE WHEN c.combl = TRUE THEN 'ciqual_combl' ELSE 'ciqual' END
    WHEN p.ciqual_food_code_origin = 'agribalyse' THEN
      CASE WHEN c.combl = TRUE THEN 'agribalyse_combl' ELSE 'agribalyse' END
    WHEN p.ciqual_food_code_origin = 'agribalyse_proxy' THEN
      CASE WHEN c.combl = TRUE THEN 'agribalyse_proxy_combl' ELSE 'agribalyse_proxy' END
  END AS merged_source
FROM products_nutriments p
LEFT JOIN calnut_0 c ON p.ciqual_food_code = c.ALIM_CODE;
""").show(max_width=10000)  # type: ignore

# Join on the ciqual code and the nutrient name


# %%
