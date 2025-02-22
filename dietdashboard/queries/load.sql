-- Nutrient mapping table
CREATE OR REPLACE TABLE nutrient_map AS (
    SELECT id, ciqual_name, ciqual_id, ciqual_unit, calnut_name, calnut_unit, calnut_const_code,
    off_id, count, nnr2023_id, nutrient_type,
    FROM read_csv('data/nutrient_map.csv')
    WHERE calnut_const_code IS NOT NULL
);
/* Documentation: https://ciqual.anses.fr/cms/sites/default/files/inline-files/Table%20CALNUT%202020_doc_FR_2020%2007%2007.pdf
Table 0 contains food group information (2 119 rows)
Table 1 contains nutrient information for each food and nutrient (131 378 rows)
Both tables are joined on the ALIM_CODE and FOOD_LABEL columns
Fetched from https://github.com/openfoodfacts/openfoodfacts-server/tree/main/external-data/ciqual/calnut
*/
CREATE OR REPLACE TABLE calnut_0 AS (
    SELECT ALIM_CODE, FOOD_LABEL,
    alim_grp_code, alim_ssgrp_code, alim_ssssgrp_code,
    alim_grp_nom_fr, alim_ssgrp_nom_fr, alim_ssssgrp_nom_fr,
    FROM read_csv('data/calnut.0.csv')
    WHERE HYPOTH = 'MB'  -- to only have one row per food
);
CREATE OR REPLACE TABLE calnut_1 AS (
    SELECT ALIM_CODE, FOOD_LABEL, CONST_LABEL, CONST_CODE,
    CAST(indic_combl AS BOOL) as combl,
    CAST(REPLACE(LB, ',', '.') AS FLOAT) as lb,
    CAST(REPLACE(UB, ',', '.') AS FLOAT) as ub,
    CAST(REPLACE(MB, ',', '.') AS FLOAT) as mean,
    FROM read_csv('data/calnut.1.csv')
);
-- Huggingface Documentation for open-prices data: https://huggingface.co/datasets/openfoodfacts/open-prices
-- Number of rows as of 27/01/2025: 70 283
CREATE OR REPLACE TABLE prices AS (
    SELECT * FROM read_parquet('data/prices.parquet')
);
/* Open Food Facts data page: https://world.openfoodfacts.org/data
The exported parquet file is missing the 'categories_properties' that contains the ciqual information.
Therefore the jsonl databse dump is used, available at: https://static.openfoodfacts.org/data/openfoodfacts-products.jsonl.gz
Note: there are duplicates of the code, it is not a unique key
Number of rows as of 17/02/2025: 3 667 647
*/
CREATE OR REPLACE TABLE products AS (
    SELECT
    p._id,
    p.code,
    p.countries_tags,
    p.ecoscore_score,
    p.nova_group,
    p.nutriments,
    p.nutriscore_score,
    p.product_name,
    p.product_quantity_unit,
    CAST(p.product_quantity AS FLOAT) as product_quantity,
    p.quantity as quantity_str,
    p.categories_properties,
    COALESCE(
        p.categories_properties['ciqual_food_code:en'],
        p.categories_properties['agribalyse_food_code:en'],
        p.categories_properties['agribalyse_proxy_food_code:en']
    ) AS ciqual_food_code,
    CASE
        WHEN p.categories_properties['ciqual_food_code:en'] IS NOT NULL THEN 'ciqual'
        WHEN p.categories_properties['agribalyse_food_code:en'] IS NOT NULL THEN 'agribalyse'
        WHEN p.categories_properties['agribalyse_proxy_food_code:en'] IS NOT NULL THEN 'agribalyse_proxy'
        ELSE 'unknown'
    END AS ciqual_food_code_origin,
    FROM read_ndjson('data/openfoodfacts-products.jsonl.gz') AS p
);
