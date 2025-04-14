-- TODO: Add illustrations of queries.
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
    v.nutrient_value IS NOT NULL AND v.nutrient_unit IS NOT NULL AS product_nutrient_is_valid,
    FROM products_with_ciqual_and_price p
    CROSS JOIN LATERAL (
    VALUES
('energy_fibre_kj',    p.nutriments."energy-kj_value",          p.nutriments."energy-kj_unit"          ),
('energy_fibre_kcal',  p.nutriments."energy-kcal_value",        p.nutriments."energy-kcal_unit"        ),
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
    ciq.lb AS ciqual_lb,
    ciq.ub AS ciqual_ub,
    ciq.mean AS ciqual_mean,
    ciq.code_confiance AS ciqual_code_confiance,
    ciq.source_code AS ciqual_source_code,
    cal.lb AS calnut_lb,
    cal.ub AS calnut_ub,
    cal.mean AS calnut_mean,
    cal.combl AS calnut_combl,
    nm.id AS nutrient_id,
    nm.ciqual_const_code,
    nm.ciqual_unit,
    nm.calnut_unit,
    -- TODO: convert product_value to correct unit to be able to use it
    CASE
        WHEN p.product_nutrient_is_valid AND p.nutrient_unit == nm.ciqual_unit THEN p.nutrient_value
        WHEN ciq.mean IS NOT NULL THEN ciq.mean
        WHEN cal.mean IS NOT NULL THEN cal.mean
        ELSE 0  -- When unknown, assume 0
    END AS final_nutrient_value,
    CASE
        WHEN p.product_nutrient_is_valid AND p.nutrient_unit == nm.ciqual_unit THEN p.nutrient_unit
        WHEN ciq.mean IS NOT NULL THEN nm.ciqual_unit
        WHEN cal.mean IS NOT NULL THEN nm.calnut_unit
        ELSE nm.ciqual_unit
    END AS final_nutrient_unit,
    CASE
        WHEN p.product_nutrient_is_valid AND p.nutrient_unit == nm.calnut_unit THEN 'product'
        WHEN ciq.mean IS NOT NULL THEN CONCAT('ciqual_', ciq.code_confiance, '_', ciq.source_code)
        WHEN cal.mean IS NOT NULL THEN CONCAT('calnut', CASE WHEN cal.combl THEN '_combl' ELSE '' END)
        ELSE 'assumed 0'
    END AS final_nutrient_origin,
    FROM products_nutriments p
    JOIN nutrient_map nm ON p.nutrient_id = nm.id
    LEFT JOIN ciqual_compo ciq
    ON p.ciqual_food_code = ciq.alim_code AND ciq.const_code = nm.ciqual_const_code
    LEFT JOIN calnut_1 cal
    ON p.ciqual_food_code = cal.ALIM_CODE AND cal.CONST_CODE = nm.calnut_const_code
);
CREATE OR REPLACE TABLE final_nutrient_table AS (
SELECT * FROM products_nutriments_selected
PIVOT (
    first(final_nutrient_value) AS value,
    first(final_nutrient_unit) AS unit,
    first(final_nutrient_origin) AS origin,
    FOR nutrient_id IN
    ('energy_fibre_kj', 'energy_fibre_kcal', 'water', 'protein', 'carbohydrate', 'fat',
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
    p.code AS product_code,
    p.product_name,
    p.product_quantity,
    p.product_quantity_unit,
    -- Calnut 0 columns
    ciq.alim_nom_eng AS ciqual_name,
    ciq.alim_code AS ciqual_code,
    ciq.alim_grp_code AS ciqual_group_code,
    ciq.alim_ssgrp_code AS ciqual_subgroup_code,
    ciq.alim_ssssgrp_code AS ciqual_subsubgroup_code,
    -- Price columns
    pr.id AS price_id,
    pr.price,
    pr.type AS price_type,
    pr.owner AS price_owner,
    pr.price_is_discounted,
    pr.price_without_discount,
    pr.price_per,
    pr.currency,
    pr.date AS price_date,
    pr.created AS price_created,
    pr.updated AS price_updated,
    pr.source AS price_source,
    pr.location_id,
    pr.location_type,
    pr.location_osm_type,
    pr.location_osm_id,
    pr.location_osm_display_name,
    pr.location_osm_display_name,
    pr.location_osm_tag_key,
    pr.location_osm_tag_value,
    pr.location_osm_address_postcode,
    pr.location_osm_address_city,
    pr.location_osm_address_country,
    pr.location_osm_address_country_code,
    pr.location_osm_lat,
    pr.location_osm_lon,
    pr.location_website_url,
    pr.location_source,
    pr.location_created,
    pr.location_updated,
    -- Price per quantity
    1000 * pr.price / p.product_quantity AS price_per_quantity,  -- TODO: this assumes that the quantity is in grams
    -- Nutrient columns
    fnt.*,
    FROM prices pr
    JOIN final_nutrient_table fnt ON pr.product_code = fnt.code
    JOIN products_with_ciqual_and_price p ON pr.product_code = p.code
    -- TODO: may filter out a few codes available in calnut and not in ciqual
    JOIN ciqual_alim ciq ON fnt.ciqual_food_code = ciq.alim_code
    -- final table count: 36 904
);
-- Recommendations
CREATE OR REPLACE TABLE recommendations AS (
    SELECT
    nm.id, nm.name, nm.nutrient_type,
    COALESCE(rec_macro.value_males, rec_micro.value_males) AS value_males,
    COALESCE(rec_macro.value_females, rec_micro.value_females) AS value_females,
    COALESCE(rec_macro.value_upper_intake, rec_micro.value_upper_intake) AS value_upper_intake,
    COALESCE(rec_macro.unit, rec_micro.unit) AS rec_unit,
    FROM nutrient_map nm
    LEFT JOIN recommendations_macro rec_macro ON rec_macro.id = nm.id
    LEFT JOIN recommendations_nnr2023 rec_micro ON rec_micro.nutrient = nm.nnr2023_id
    WHERE nm.disabled IS NULL
    AND (rec_macro.value_males IS NOT NULL OR rec_micro.value_males IS NOT NULL)
    AND rec_unit = ciqual_unit
);
