# %%
import csv
from pathlib import Path

import duckdb

DATA_DIR = Path(__file__).parent.parent / "data"
con = duckdb.connect(DATA_DIR / "explore.db")


# %%
con.sql("SELECT * FROM prices LIMIT 1")

# %%
con.sql("DESCRIBE SELECT * FROM prices")

# %%
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
con.sql(
    """
    SELECT location_osm_address_city
    FROM prices
    WHERE owner = '$owner_id'
""".replace("$owner_id", owner_id)
)

# %%
con.sql("SELECT * FROM products LIMIT 1")

# %%
con.sql("DESCRIBE SELECT * FROM products")

# %%
with (Path.cwd().parent / "tmp.txt").open("w") as f:
    columns = con.sql("SELECT * FROM products LIMIT 0").columns
    for col in columns:
        f.write(f"{col},\n")

# %%
# Get the data for the owner
con.sql(
    """SELECT * FROM prices AS prices
  LEFT JOIN products AS food ON prices.product_code = food.code
  WHERE prices.owner = $owner_id
""",
    params={"owner_id": owner_id},
).to_csv("my_prices.csv")

# %%
# Documentation here: https://ciqual.anses.fr/cms/sites/default/files/inline-files/Table%20CALNUT%202020_doc_FR_2020%2007%2007.pdf
# From table 1 we get upper_bound, lower_bound, mean, and an indicator of the completeness of the data
# From table 0 we get the food group and subgroup
# Both tables are linked by the ALIM_CODE and FOOD_LABEL columns
con.sql("SELECT * FROM calnut_1")

# %%
con.sql("SELECT DISTINCT combl FROM calnut_1")

# %%
# Write all the distince nutrient labels to a file
const_labels = con.sql("""
  SELECT DISTINCT CONST_LABEL, CONST_CODE
  FROM calnut_1
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
# Pivot the ciqual 1 table to have on column per CONST_LABEL
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
query = f"""
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
"""
print(query)
con.sql(query).to_csv("calnut_pivoted.csv")

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
# From columns to get from this:
# alim_code,FOOD_LABEL,alim_grp_code,alim_grp_nom_fr,alim_ssgrp_code,alim_ssgrp_nom_fr,alim_ssssgrp_code,alim_ssssgrp_nom_fr
con.sql("""
  SELECT
  ALIM_CODE,FOOD_LABEL,
  alim_grp_code,alim_grp_nom_fr,
  alim_ssgrp_code,alim_ssgrp_nom_fr,
  alim_ssssgrp_code,alim_ssssgrp_nom_fr
  FROM calnut_0
""")

# %%
# Count the number of rows in the products table
con.sql("SELECT count(*) FROM products")
# 3667647

# %%
# Count the number of rows in the prices table
con.sql("SELECT count(*) FROM prices")
# 70283

# %%
# Write all the columns to a file
columns = con.sql("SELECT * FROM products LIMIT 1").columns
f = ["ingredients", "_name", "packaging", "origin", "nutri"]
filtered_columns = [col for col in columns if not any(s in col for s in f)]
with (Path.cwd().parent / "tmp.txt").open("w") as f:
    for col in sorted(filtered_columns):
        f.write(f"{col},\n")

# %%
# Describe the categories_properties column
con.sql("""
DESCRIBE SELECT * FROM products
""")

# %%
# How the fields in the nutriments column are structured
out = con.sql("DESCRIBE SELECT nutriments FROM products").fetchall()[0][1]
with (Path.cwd().parent / "nutriment_fields.csv").open("w") as f:
    fields = str(out).replace("STRUCT(", "").replace(")", "").split(", ")
    f.write(",\n".join(fields))


# %%
# One row per product and nutriment
con.sql("""
WITH few_products AS (
  SELECT * FROM products LIMIT 50
)
SELECT
  p.code,
  v.nutrient_name,
  v.nutrient_value,
  v.nutrient_unit,
  v.nutrient_100g
FROM few_products p
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
con.sql("""
SELECT
  code,
  nutriments.*
FROM products LIMIT 50;
""")
