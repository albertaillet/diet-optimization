-- Nutrient mapping table
CREATE OR REPLACE TABLE nutrient_map AS (
    SELECT id, ciqual_name, ciqual_id, ciqual_unit, calnut_name, calnut_unit, calnut_const_code,
    off_id, countprep, nnr2023_id, nutrient_type,
    FROM read_csv('nutrient_map.csv')
    WHERE disabled IS NULL
);
/* Documentation: https://ciqual.anses.fr/cms/sites/default/files/inline-files/Table%20CALNUT%202020_doc_FR_2020%2007%2007.pdf
Table 0 contains food group information (2 119 rows)
Table 1 contains nutrient information for each food and nutrient (131 378 rows)
Both tables are joined on the ALIM_CODE and FOOD_LABEL columns
*/
CREATE OR REPLACE TABLE calnut_0 AS (
    SELECT ALIM_CODE, FOOD_LABEL,
    alim_grp_code, alim_ssgrp_code, alim_ssssgrp_code,
    alim_grp_nom_fr, alim_ssgrp_nom_fr, alim_ssssgrp_nom_fr,
    FROM read_csv('calnut.0.csv')
    WHERE HYPOTH = 'MB'  -- to only have one row per food
);
CREATE OR REPLACE TABLE calnut_1 AS (
    SELECT ALIM_CODE, FOOD_LABEL, CONST_LABEL, CONST_CODE,
    CAST(indic_combl AS BOOL) as combl,
    CAST(REPLACE(LB, ',', '.') AS FLOAT) as lb,
    CAST(REPLACE(UB, ',', '.') AS FLOAT) as ub,
    CAST(REPLACE(MB, ',', '.') AS FLOAT) as mean,
    FROM read_csv('calnut.1.csv')
);
-- Huggingface Documentation for open-prices data: https://huggingface.co/datasets/openfoodfacts/open-prices
CREATE OR REPLACE TABLE prices AS (
    SELECT * FROM read_parquet('prices.parquet')
);
/* Open Food Facts data page: https://world.openfoodfacts.org/data
The exported parquet file is missing the 'categories_properties' that contains the ciqual information.
Therefore the jsonl databse dump is used, available at: https://static.openfoodfacts.org/data/openfoodfacts-products.jsonl.gz
Note: there are duplicates of the code, it is not a unique key
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
    p.product_quantity,
    p.quantity,
    p.categories_properties,
    FROM read_ndjson('openfoodfacts-products.jsonl.gz') AS p
    -- with no filtering: 3 667 647
    -- WHERE code IS NOT NULL AND 'en:france' IN countries_tags OR 'en:switzerland' IN countries_tags
    -- french and swiss products: 1 190 620
    -- JOIN prices ON p.code = prices.product_code
    -- products with prices: 32 892
);
CREATE OR REPLACE TABLE products_with_prices AS (
    SELECT * FROM products
    WHERE EXISTS ( SELECT 1 FROM prices WHERE products.code = prices.product_code )
);
CREATE OR REPLACE TABLE products_with_ciqual AS (
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
    FROM products_with_prices
);
CREATE OR REPLACE TABLE final_nutrient_table AS (
WITH
products_nutriments AS (
    SELECT
    p.code,
    p.ciqual_food_code,
    p.ciqual_food_code_origin,
    v.nutrient_name,
    v.nutrient_value,
    v.nutrient_unit,
    v.nutrient_100g
    FROM products_with_ciqual p
    CROSS JOIN LATERAL (
    VALUES
    ('energy-kcal',        p.nutriments."energy-kcal_value",        p.nutriments."energy-kcal_unit",        p.nutriments."energy-kcal_100g"        ),
    -- ('water',              p.nutriments."water_value",              p.nutriments."water_unit",              p.nutriments."water_100g"              ),
    ('proteins',           p.nutriments."proteins_value",           p.nutriments."proteins_unit",           p.nutriments."proteins_100g"           ),
    ('carbohydrates',      p.nutriments."carbohydrates_value",      p.nutriments."carbohydrates_unit",      p.nutriments."carbohydrates_100g"      ),
    ('fat',                p.nutriments."fat_value",                p.nutriments."fat_unit",                p.nutriments."fat_100g"                ),
    ('sugars',             p.nutriments."sugars_value",             p.nutriments."sugars_unit",             p.nutriments."sugars_100g"             ),
    -- ('fructose',           p.nutriments."fructose_value",           p.nutriments."fructose_unit",           p.nutriments."fructose_100g"           ),
    -- ('galactose',          p.nutriments."galactose_value",          p.nutriments."galactose_unit",          p.nutriments."galactose_100g"          ),
    -- ('glucose',            p.nutriments."glucose_value",            p.nutriments."glucose_unit",            p.nutriments."glucose_100g"            ),
    ('lactose',            p.nutriments."lactose_value",            p.nutriments."lactose_unit",            p.nutriments."lactose_100g"            ),
    -- ('maltose',            p.nutriments."maltose_value",            p.nutriments."maltose_unit",            p.nutriments."maltose_100g"            ),
    -- ('sucrose',            p.nutriments."sucrose_value",            p.nutriments."sucrose_unit",            p.nutriments."sucrose_100g"            ),
    ('starch',             p.nutriments."starch_value",             p.nutriments."starch_unit",             p.nutriments."starch_100g"             ),
    ('fiber',              p.nutriments."fiber_value",              p.nutriments."fiber_unit",              p.nutriments."fiber_100g"              ),
    ('polyols',            p.nutriments."polyols_value",            p.nutriments."polyols_unit",            p.nutriments."polyols_100g"            ),
    ('saturated-fat',      p.nutriments."saturated-fat_value",      p.nutriments."saturated-fat_unit",      p.nutriments."saturated-fat_100g"      ),
    ('monounsaturated-fat',p.nutriments."monounsaturated-fat_value",p.nutriments."monounsaturated-fat_unit",p.nutriments."monounsaturated-fat_100g"),
    ('polyunsaturated-fat',p.nutriments."polyunsaturated-fat_value",p.nutriments."polyunsaturated-fat_unit",p.nutriments."polyunsaturated-fat_100g"),
    ('cholesterol',        p.nutriments."cholesterol_value",        p.nutriments."cholesterol_unit",        p.nutriments."cholesterol_100g"        ),
    ('salt',               p.nutriments."salt_value",               p.nutriments."salt_unit",               p.nutriments."salt_100g"               ),
    ('calcium',            p.nutriments."calcium_value",            p.nutriments."calcium_unit",            p.nutriments."calcium_100g"            ),
    -- ('chloride',           p.nutriments."chloride_value",           p.nutriments."chloride_unit",           p.nutriments."chloride_100g"           ),
    ('copper',             p.nutriments."copper_value",             p.nutriments."copper_unit",             p.nutriments."copper_100g"             ),
    ('iron',               p.nutriments."iron_value",               p.nutriments."iron_unit",               p.nutriments."iron_100g"               ),
    ('iodine',             p.nutriments."iodine_value",             p.nutriments."iodine_unit",             p.nutriments."iodine_100g"             ),
    ('magnesium',          p.nutriments."magnesium_value",          p.nutriments."magnesium_unit",          p.nutriments."magnesium_100g"          ),
    ('manganese',          p.nutriments."manganese_value",          p.nutriments."manganese_unit",          p.nutriments."manganese_100g"          ),
    ('potassium',          p.nutriments."potassium_value",          p.nutriments."potassium_unit",          p.nutriments."potassium_100g"          ),
    ('selenium',           p.nutriments."selenium_value",           p.nutriments."selenium_unit",           p.nutriments."selenium_100g"           ),
    ('zinc',               p.nutriments."zinc_value",               p.nutriments."zinc_unit",               p.nutriments."zinc_100g"               ),
    ('vitamin-d',          p.nutriments."vitamin-d_value",          p.nutriments."vitamin-d_unit",          p.nutriments."vitamin-d_100g"          ),
    ('vitamin-e',          p.nutriments."vitamin-e_value",          p.nutriments."vitamin-e_unit",          p.nutriments."vitamin-e_100g"          ),
    ('vitamin-c',          p.nutriments."vitamin-c_value",          p.nutriments."vitamin-c_unit",          p.nutriments."vitamin-c_100g"          ),
    ('vitamin-b6',         p.nutriments."vitamin-b6_value",         p.nutriments."vitamin-b6_unit",         p.nutriments."vitamin-b6_100g"         ),
    ('vitamin-b12',        p.nutriments."vitamin-b12_value",        p.nutriments."vitamin-b12_unit",        p.nutriments."vitamin-b12_100g"        ),
    ) AS v(nutrient_name, nutrient_value, nutrient_unit, nutrient_100g)
),
calnut_mapped AS (
    SELECT * FROM calnut_1 AS c
    JOIN nutrient_map nm
    ON c.CONST_CODE = nm.calnut_const_code
),
products_nutriments_mapped AS (
    SELECT
    p.code,
    p.ciqual_food_code,
    p.nutrient_value,
    p.nutrient_name,
    p.nutrient_unit,
    c.ALIM_CODE,
    c.CONST_CODE,
    c.lb,
    c.ub,
    c.mean,
    c.CONST_LABEL,
    c.calnut_name,
    c.calnut_unit,
    FROM products_nutriments p
    JOIN calnut_mapped c
    ON p.ciqual_food_code = c.ALIM_CODE AND
        p.nutrient_name = c.off_id
),
nutriments_selected AS (
  SELECT
  code,
  ciqual_food_code,
  calnut_name,
  CASE
    WHEN nutrient_value IS NOT NULL
      AND nutrient_unit IS NOT NULL
      AND nutrient_unit != ''
    THEN nutrient_value
    ELSE mean
  END AS final_nutrient_value,
  CASE
    WHEN nutrient_value IS NOT NULL
      AND nutrient_unit IS NOT NULL
      AND nutrient_unit != ''
    THEN nutrient_unit
    ELSE calnut_unit
  END AS final_nutrient_unit
  FROM products_nutriments_mapped
)
SELECT *
FROM nutriments_selected
PIVOT (
    first(final_nutrient_value) AS value,
    first(final_nutrient_unit) AS unit
    FOR calnut_name IN
    ('agmi', 'agpi', 'ags', 'amidon', 'calcium', 'cholesterol', 'cuivre', 'fer', 'fibres', 'glucides', 'iode', 'lactose', 'lipides',
    'magnesium', 'manganese', 'nrj', 'polyols', 'potassium', 'proteines', 'sel', 'selenium', 'sucres', 'vitamine_b12',
    'vitamine_b6', 'vitamine_c', 'vitamine_d', 'vitamine_e', 'zinc')
    GROUP BY code, ciqual_food_code
)
);
CREATE OR REPLACE TABLE final_table AS (
  SELECT
    -- Product columns
    p.code                 AS product_code,
    p.product_name         AS product_name,
    fnt.ciqual_food_code   AS ciqual_code,
    c.FOOD_LABEL           AS ciqual_name,
    -- add ciqual name to nutrient table
    -- Use the price id as an identifier (or generate one if needed)
    pr.id                  AS price_id,
    pr.price               AS price,
    pr.currency            AS currency,
    pr.date                AS price_date,
    pr.location_osm_display_name AS location,
    pr.location_osm_id     AS location_osm_id,
    -- Nutrient columns
    fnt.*,
  FROM prices pr
  JOIN final_nutrient_table fnt ON pr.product_code = fnt.code
  JOIN products p ON pr.product_code = p.code
  JOIN calnut_0 c ON fnt.ciqual_food_code = c.ALIM_CODE
);  -- Final table count: 70283
SELECT *
FROM final_table;
