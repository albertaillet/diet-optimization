-- Nutrient mapping table
CREATE OR REPLACE TABLE nutrient_map AS (
    SELECT id, ciqual_name, ciqual_id, ciqual_unit, calnut_name, calnut_unit, calnut_const_code,
    off_id, count, nnr2023_id, nutrient_type,
    FROM read_csv('nutrient_map.csv')
    WHERE off_id IS NOT NULL OR calnut_const_code IS NOT NULL
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
    FROM read_ndjson('openfoodfacts-products.jsonl.gz') AS p
    -- with no filtering: 3 667 647
    -- WHERE code IS NOT NULL AND 'en:france' IN countries_tags OR 'en:switzerland' IN countries_tags
    -- french and swiss products: 1 190 620
);
CREATE OR REPLACE TABLE products_with_ciqual_and_price AS (
    SELECT * FROM products
    WHERE ciqual_food_code IS NOT NULL
    AND EXISTS ( SELECT 1 FROM prices WHERE products.code = prices.product_code )
    -- products with ciqual: 1 027 480
    -- products with prices: 32 892
    -- products with prices and ciqual: 23 650
);
CREATE OR REPLACE TABLE products_nutriments AS (
    SELECT
    p.code,
    p.ciqual_food_code,
    p.ciqual_food_code_origin,
    v.nutrient_id,
    v.nutrient_value,
    v.nutrient_unit,
    v.nutrient_value IS NOT NULL AND v.nutrient_unit IS NOT NULL AS nutrient_is_valid,
    FROM products_with_ciqual_and_price p
    CROSS JOIN LATERAL (
    VALUES
('energy_kj',          p.nutriments."energy-kj_value",          p.nutriments."energy-kj_unit"          ),
('energy_kcal',        p.nutriments."energy-kcal_value",        p.nutriments."energy-kcal_unit"        ),
('water',              NULL,                                    NULL,                                  ),
('protein',            p.nutriments."proteins_value",           p.nutriments."proteins_unit"           ),
('carbohydrate',       p.nutriments."carbohydrates_value",      p.nutriments."carbohydrates_unit"      ),
('fat',                p.nutriments."fat_value",                p.nutriments."fat_unit"                ),
('sugars',             p.nutriments."sugars_value",             p.nutriments."sugars_unit"             ),
('fructose',           NULL,                                    NULL,                                  ),
('galactose',          NULL,                                    NULL,                                  ),
('glucose',            NULL,                                    NULL,                                  ),
('lactose',            p.nutriments."lactose_value",            p.nutriments."lactose_unit"            ),
('maltose',            NULL,                                    NULL,                                  ),
('sucrose',            NULL,                                    NULL,                                  ),
('starch',             p.nutriments."starch_value",             p.nutriments."starch_unit"             ),
('fiber',              p.nutriments."fiber_value",              p.nutriments."fiber_unit"              ),
('polyols',            p.nutriments."polyols_value",            p.nutriments."polyols_unit"            ),
('alcohol',            p.nutriments."alcohol_value",            p.nutriments."alcohol_unit"            ),
('organic_acids',      NULL,                                    NULL,                                  ),
('saturated_fat',      p.nutriments."saturated-fat_value",      p.nutriments."saturated-fat_unit"      ),
('monounsaturated_fat',p.nutriments."monounsaturated-fat_value",p.nutriments."monounsaturated-fat_unit"),
('polyunsaturated_fat',p.nutriments."polyunsaturated-fat_value",p.nutriments."polyunsaturated-fat_unit"),
('fa_04_0',            NULL,                                    NULL,                                  ),
('fa_06_0',            NULL,                                    NULL,                                  ),
('fa_08_0',            NULL,                                    NULL,                                  ),
('fa_10_0',            NULL,                                    NULL,                                  ),
('fa_12_0',            NULL,                                    NULL,                                  ),
('fa_14_0',            NULL,                                    NULL,                                  ),
('fa_16_0',            NULL,                                    NULL,                                  ),
('fa_18_0',            NULL,                                    NULL,                                  ),
('fa_18_1_ole',        NULL,                                    NULL,                                  ),
('fa_18_2_lino',       NULL,                                    NULL,                                  ),
('fa_18_3_a_lino',     NULL,                                    NULL,                                  ),
('fa_20_4_ara',        NULL,                                    NULL,                                  ),
('fa_20_5_epa',        NULL,                                    NULL,                                  ),
('fa_20_6_dha',        NULL,                                    NULL,                                  ),
('cholesterol',        p.nutriments."cholesterol_value",        p.nutriments."cholesterol_unit"        ),
('salt',               p.nutriments."salt_value",               p.nutriments."salt_unit"               ),
('calcium',            p.nutriments."calcium_value",            p.nutriments."calcium_unit"            ),
('copper',             p.nutriments."copper_value",             p.nutriments."copper_unit"             ),
('iron',               p.nutriments."iron_value",               p.nutriments."iron_unit"               ),
('iodine',             p.nutriments."iodine_value",             p.nutriments."iodine_unit"             ),
('magnesium',          p.nutriments."magnesium_value",          p.nutriments."magnesium_unit"          ),
('manganese',          p.nutriments."manganese_value",          p.nutriments."manganese_unit"          ),
('phosphorus',         p.nutriments."phosphorus_value",         p.nutriments."phosphorus_unit"         ),
('potassium',          p.nutriments."potassium_value",          p.nutriments."potassium_unit"          ),
('selenium',           p.nutriments."selenium_value",           p.nutriments."selenium_unit"           ),
('sodium',             p.nutriments."sodium_value",             p.nutriments."sodium_unit"             ),
('zinc',               p.nutriments."zinc_value",               p.nutriments."zinc_unit"               ),
('retinol',            NULL,                                    NULL,                                  ),
('beta_carotene',      NULL,                                    NULL,                                  ),
('vitamin_d',          p.nutriments."vitamin-d_value",          p.nutriments."vitamin-d_unit"          ),
('vitamin_e',          p.nutriments."vitamin-e_value",          p.nutriments."vitamin-e_unit"          ),
('vitamin_k1',         NULL,                                    NULL,                                  ),
('vitamin_k2',         NULL,                                    NULL,                                  ),
('vitamin_c',          p.nutriments."vitamin-c_value",          p.nutriments."vitamin-c_unit"          ),
('vitamin_b1',         p.nutriments."vitamin-b1_value",         p.nutriments."vitamin-b1_unit"         ),
('vitamin_b2',         p.nutriments."vitamin-b2_value",         p.nutriments."vitamin-b2_unit"         ),
('vitamin_pp',         p.nutriments."vitamin-pp_value",         p.nutriments."vitamin-pp_unit"         ),
('pantothenic_acid',   p.nutriments."pantothenic-acid_value",   p.nutriments."pantothenic-acid_unit"   ),
('vitamin_b6',         p.nutriments."vitamin-b6_value",         p.nutriments."vitamin-b6_unit"         ),
('vitamin_b9',         p.nutriments."vitamin-b9_value",         p.nutriments."vitamin-b9_unit"         ),
('folates',            p.nutriments."folates_value",            p.nutriments."folates_unit"            ),
('vitamin_b12',        p.nutriments."vitamin-b12_value",        p.nutriments."vitamin-b12_unit"        ),
) AS v(nutrient_id, nutrient_value, nutrient_unit)
);
CREATE OR REPLACE TABLE products_nutriments_selected AS (
    SELECT
    p.code,
    p.ciqual_food_code,
    p.ciqual_food_code_origin,
    p.nutrient_value,
    p.nutrient_unit,
    c.ALIM_CODE,
    c.CONST_CODE,
    c.combl,
    c.lb,
    c.ub,
    c.mean,
    c.CONST_LABEL,
    nm.id AS nutrient_id,
    nm.calnut_name,
    nm.calnut_unit,
    CASE
        WHEN p.nutrient_is_valid AND p.nutrient_unit == nm.calnut_unit
        THEN p.nutrient_value ELSE c.mean
    END AS final_nutrient_value,
    CASE
        WHEN p.nutrient_is_valid AND p.nutrient_unit == nm.calnut_unit
        THEN p.nutrient_unit ELSE nm.calnut_unit
    END AS final_nutrient_unit,
    CASE
        WHEN p.nutrient_is_valid AND p.nutrient_unit == nm.calnut_unit
        THEN 'product' ELSE CONCAT(p.ciqual_food_code_origin, CASE WHEN c.combl THEN '_combl' ELSE '' END)
    END AS final_nutrient_origin,
    FROM products_nutriments p
    JOIN calnut_1 c
    ON p.ciqual_food_code = c.ALIM_CODE
    JOIN nutrient_map nm
    ON c.CONST_CODE = nm.calnut_const_code AND
        p.nutrient_id = nm.id
);
CREATE OR REPLACE TABLE final_nutrient_table AS (
SELECT * FROM products_nutriments_selected
PIVOT (
    first(final_nutrient_value) AS value,
    first(final_nutrient_unit) AS unit,
    first(final_nutrient_origin) AS origin,
    FOR nutrient_id IN
    ('energy_kj', 'energy_kcal', 'water', 'protein', 'carbohydrate', 'fat',
    'sugars', 'fructose', 'galactose', 'glucose', 'lactose', 'maltose', 'sucrose', 'starch', 'fiber', 'polyols',
    'alcohol', 'organic_acids', 'saturated_fat', 'monounsaturated_fat', 'polyunsaturated_fat',
    'fa_04_0', 'fa_06_0', 'fa_08_0', 'fa_10_0', 'fa_12_0', 'fa_14_0', 'fa_16_0', 'fa_18_0', 'fa_18_1_ole', 'fa_18_2_lino',
    'fa_18_3_a_lino', 'fa_20_4_ara', 'fa_20_5_epa', 'fa_20_6_dha', 'cholesterol', 'salt', 'calcium', 'copper', 'iron', 'iodine',
    'magnesium', 'manganese', 'phosphorus', 'potassium', 'selenium', 'sodium', 'zinc', 'retinol', 'beta_carotene',
    'vitamin_d', 'vitamin_e', 'vitamin_k1', 'vitamin_k2', 'vitamin_c', 'vitamin_b1', 'vitamin_b2', 'vitamin_pp',
    'pantothenic_acid', 'vitamin_b6', 'vitamin_b9', 'folates', 'vitamin_b12')
    GROUP BY code, ciqual_food_code
)
-- Final nutrient table count: 19 369
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
  pr.owner               AS price_owner,
  -- Nutrient columns
  fnt.*,
  FROM prices pr
  JOIN final_nutrient_table fnt ON pr.product_code = fnt.code
  JOIN products p ON pr.product_code = p.code
  JOIN calnut_0 c ON fnt.ciqual_food_code = c.ALIM_CODE
  -- final table count: 36 904
);
SELECT *
FROM final_table;
