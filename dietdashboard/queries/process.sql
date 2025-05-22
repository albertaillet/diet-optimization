-- TODO: Add illustrations of queries.
CREATE OR REPLACE TABLE products_with_ciqual_and_price AS (
    SELECT * FROM products
    WHERE ciqual_food_code IS NOT NULL
    AND EXISTS ( SELECT 1 FROM prices WHERE products.code = prices.product_code )
);
CREATE OR REPLACE TABLE products_nutriments AS (
    SELECT
    p.code,
    p.ciqual_food_code,
    p.ciqual_food_code_origin,
    n.unnest.name AS off_id,
    n.unnest.unit AS nutrient_unit,
    n.unnest.value AS nutrient_value,
    nutrient_value IS NOT NULL AND nutrient_unit IS NOT NULL AS product_nutrient_is_valid,
    FROM products_with_ciqual_and_price p,
    UNNEST(p.nutriments) AS n
    -- nutriments: STRUCT(
    --     name VARCHAR, unit VARCHAR, value FLOAT, 100g FLOAT, serving FLOAT,
    --     prepared_100g FLOAT, prepared_value FLOAT, prepared_serving FLOAT, prepared_unit VARCHAR
    -- )[]
);
-- Problem: p.nutriments is missing some nutrients present in nutrient_map.
-- TODO: create a row for each of the nutrients in nutrient_map for each product (with a calnut_const_code).
-- Then ./scripts/template_nutriments_query.py can be removed.
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
    JOIN nutrient_map nm ON p.off_id = nm.off_id
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
