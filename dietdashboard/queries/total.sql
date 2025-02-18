CREATE OR REPLACE TABLE products AS (
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
    FROM read_ndjson('openfoodfacts-products.jsonl.gz')
    WHERE code IS NOT NULL AND
          'en:france' IN countries_tags OR 'en:switzerland' IN countries_tags
);
CREATE OR REPLACE TABLE calnut_1 AS (
    SELECT ALIM_CODE, FOOD_LABEL, CONST_LABEL, CONST_CODE,
    CAST(indic_combl AS BOOL) as combl,
    CAST(REPLACE(LB, ',', '.') AS FLOAT) as lb,
    CAST(REPLACE(UB, ',', '.') AS FLOAT) as ub,
    CAST(REPLACE(MB, ',', '.') AS FLOAT) as mean,
    FROM read_csv('calnut.1.csv')
);
CREATE OR REPLACE TABLE nutrient_map AS (
    SELECT calnut_name, calnut_unit, calnut_const_code, off_id FROM read_csv('nutrient_map.csv')
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
    FROM products
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
