-- Final table with one row per price in the price database, enriched with ciqual and agribalyse data.
CREATE OR REPLACE TABLE final_table_price AS (
WITH
/* Illustration of step_1:
┌──────────────┬───────────────┬──────────────────┬───┬────────────────────┬──────────────────┬──────────────────────┬──────────────────────┐
│ product_name │     code      │ product_quantity │ … │ product_quantity_1 │ ciqual_food_code │ ciqual_food_code_o…  │      nutriments      │
│   varchar    │    varchar    │      float       │   │       float        │      int32       │       varchar        │ struct("name" varc…  │
├──────────────┼───────────────┼──────────────────┼───┼────────────────────┼──────────────────┼──────────────────────┼──────────────────────┤
│ Pois chiches │ 3111950001928 │           1000.0 │ … │             1000.0 │            20516 │                      │ [{'name': energy, …  │
│ Tofu natur   │ 4099200179193 │            350.0 │ … │              350.0 │            20904 │                      │ [{'name': energy, …  │
├──────────────┴───────────────┴──────────────────┴───┴────────────────────┴──────────────────┴──────────────────────┴──────────────────────┤
│ 2 rows                                                                                                                9 columns (7 shown) │
└───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
*/
step_1 AS (
  SELECT product_name[1].text AS product_name, *
  FROM products
  WHERE ciqual_food_code IS NOT NULL
    AND EXISTS ( SELECT 1 FROM prices WHERE products.code = prices.product_code )
),
/* step_1 x nutrient_map (table to later be pivoted)
Illustration of step_2:
┌───────────────┬──────────────────┬──────────────────────┬─────────────┬──────────┬───────────────────┬─────────────┬───────────────────┬─────────────┐
│     code      │ ciqual_food_code │ ciqual_food_code_o…  │ nutrient_id │  off_id  │ ciqual_const_code │ ciqual_unit │ calnut_const_code │ calnut_unit │
│    varchar    │      int32       │       varchar        │   varchar   │ varchar  │       int64       │   varchar   │       int64       │   varchar   │
├───────────────┼──────────────────┼──────────────────────┼─────────────┼──────────┼───────────────────┼─────────────┼───────────────────┼─────────────┤
│ 3111950001928 │            20516 │                      │ protein     │ proteins │             25000 │ g           │             25000 │ g           │
│ 3111950001928 │            20516 │                      │ sodium      │ sodium   │             10110 │ mg          │             10110 │ mg          │
│ 4099200179193 │            20904 │                      │ protein     │ proteins │             25000 │ g           │             25000 │ g           │
│ 4099200179193 │            20904 │                      │ sodium      │ sodium   │             10110 │ mg          │             10110 │ mg          │
└───────────────┴──────────────────┴──────────────────────┴─────────────┴──────────┴───────────────────┴─────────────┴───────────────────┴─────────────┘
*/
step_2 AS (
  SELECT
    prev.code,
    prev.ciqual_food_code,
    prev.ciqual_food_code_origin,
    nm.id AS nutrient_id,
    nm.off_id,
    nm.ciqual_const_code, nm.ciqual_unit,
    nm.calnut_const_code, nm.calnut_unit,
  FROM step_1 AS prev
  JOIN nutrient_map AS nm ON TRUE
  WHERE nm.ciqual_const_code IS NOT NULL OR nm.calnut_const_code IS NOT NULL
),
/* To be LEFT JOIN with step_2
nutriments: STRUCT(
    name VARCHAR, unit VARCHAR, value FLOAT, 100g FLOAT, serving FLOAT,
    prepared_100g FLOAT, prepared_value FLOAT, prepared_serving FLOAT, prepared_unit VARCHAR
)[]
Illustration of step_3:
┌───────────────┬──────────────────┬────────────────────┬───────────────┬────────────────┬───────────────────────────┐
│     code      │ ciqual_food_code │       off_id       │ nutrient_unit │ nutrient_value │ product_nutrient_is_valid │
│    varchar    │      int32       │      varchar       │    varchar    │     float      │          boolean          │
├───────────────┼──────────────────┼────────────────────┼───────────────┼────────────────┼───────────────────────────┤
│ 3111950001928 │            20516 │ energy             │ kJ            │         1480.0 │ true                      │
│ 3111950001928 │            20516 │ fiber              │ g             │           13.3 │ true                      │
│ 3111950001928 │            20516 │ carbohydrates      │ g             │           47.5 │ true                      │
│ 3111950001928 │            20516 │ saturated-fat      │ g             │            0.6 │ true                      │
│ 3111950001928 │            20516 │ salt               │ g             │           0.06 │ true                      │
│ 3111950001928 │            20516 │ nova-group         │ NULL          │            1.0 │ false                     │
│ 3111950001928 │            20516 │ sodium             │ g             │          0.024 │ true                      │
│ 3111950001928 │            20516 │ energy-kj          │ kJ            │         1480.0 │ true                      │
│ 3111950001928 │            20516 │ sugars             │ g             │            6.5 │ true                      │
│ 3111950001928 │            20516 │ fat                │ g             │            5.9 │ true                      │
│       ·       │              ·   │  ·                 │ ·             │             ·  │  ·                        │
│       ·       │              ·   │  ·                 │ ·             │             ·  │  ·                        │
│       ·       │              ·   │  ·                 │ ·             │             ·  │  ·                        │
│ 4099200179193 │            20904 │ energy-kj          │ kJ            │          528.0 │ true                      │
│ 4099200179193 │            20904 │ carbohydrates      │ g             │            0.0 │ true                      │
│ 4099200179193 │            20904 │ nutrition-score-fr │ NULL          │           -3.0 │ false                     │
│ 4099200179193 │            20904 │ sodium             │ g             │          0.008 │ true                      │
│ 4099200179193 │            20904 │ fat                │ g             │           7.99 │ true                      │
│ 4099200179193 │            20904 │ sugars             │ g             │            0.0 │ true                      │
│ 4099200179193 │            20904 │ saturated-fat      │ g             │            1.4 │ true                      │
│ 4099200179193 │            20904 │ proteins           │ g             │           13.0 │ true                      │
│ 4099200179193 │            20904 │ energy-kcal        │ kcal          │          126.0 │ true                      │
│ 4099200179193 │            20904 │ energy             │ kJ            │          528.0 │ true                      │
├───────────────┴──────────────────┴────────────────────┴───────────────┴────────────────┴───────────────────────────┤
│ 26 rows (20 shown)                                                                                       6 columns │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
*/
step_3 AS (
  SELECT
    p.code,
    p.ciqual_food_code,
    n.unnest.name AS off_id,
    n.unnest.unit AS nutrient_unit,
    n.unnest."100g" AS nutrient_value,
    nutrient_value IS NOT NULL AND nutrient_unit IS NOT NULL AS product_nutrient_is_valid,
  FROM step_1 AS p,
  UNNEST(p.nutriments) AS n
),
/* Illustration of step_4:
┌───────────────┬─────────────┬──────────────────┬──────────────────────┬─────────────────────┬───────────────────────┐
│     code      │ nutrient_id │ ciqual_food_code │ final_nutrient_value │ final_nutrient_unit │ final_nutrient_origin │
│    varchar    │   varchar   │      int32       │        float         │       varchar       │        varchar        │
├───────────────┼─────────────┼──────────────────┼──────────────────────┼─────────────────────┼───────────────────────┤
│ 3111950001928 │ sodium      │            20516 │                 23.2 │ mg                  │ ciqual_C_81259        │
│ 3111950001928 │ protein     │            20516 │                 20.5 │ g                   │ product               │
│ 4099200179193 │ sodium      │            20904 │                 10.0 │ mg                  │ ciqual_A_83096        │
│ 4099200179193 │ protein     │            20904 │                 13.0 │ g                   │ product               │
└───────────────┴─────────────┴──────────────────┴──────────────────────┴─────────────────────┴───────────────────────┘
*/
step_4 AS (
  SELECT
    nm.code,
    nm.nutrient_id,
    nm.ciqual_food_code,
    -- DEBUG columns start --
    -- p.nutrient_value,
    -- p.nutrient_unit,
    -- ciq.lb AS ciqual_lb,
    -- ciq.ub AS ciqual_ub,
    -- ciq.mean AS ciqual_mean,
    -- ciq.code_confiance AS ciqual_code_confiance,
    -- ciq.source_code AS ciqual_source_code,
    -- cal.lb AS calnut_lb,
    -- cal.ub AS calnut_ub,
    -- cal.mean AS calnut_mean,
    -- cal.combl AS calnut_combl,
    -- nm.ciqual_food_code_origin,
    -- nm.ciqual_const_code,
    -- nm.ciqual_unit,
    -- nm.calnut_const_code,
    -- nm.calnut_unit,
    -- DEBUG columns end --
    -- TODO: convert product_value to correct unit to be able to use it
    CASE
      WHEN p.product_nutrient_is_valid AND p.nutrient_unit = nm.ciqual_unit THEN p.nutrient_value
      WHEN ciq.mean IS NOT NULL THEN ciq.mean
      WHEN cal.mean IS NOT NULL THEN cal.mean
      ELSE 0  -- When unknown, assume 0
    END AS final_nutrient_value,
    CASE
      WHEN p.product_nutrient_is_valid AND p.nutrient_unit = nm.ciqual_unit THEN p.nutrient_unit
      WHEN ciq.mean IS NOT NULL THEN nm.ciqual_unit
      WHEN cal.mean IS NOT NULL THEN nm.calnut_unit
      ELSE nm.ciqual_unit
    END AS final_nutrient_unit,
    CASE
      WHEN p.product_nutrient_is_valid AND p.nutrient_unit = nm.ciqual_unit THEN 'product'
      WHEN ciq.mean IS NOT NULL THEN CONCAT('ciqual_', nm.ciqual_food_code_origin, ciq.code_confiance, '_', ciq.source_code)
      WHEN cal.mean IS NOT NULL THEN CONCAT('calnut_', nm.ciqual_food_code_origin, CASE WHEN cal.combl THEN '_combl' ELSE '' END)
      ELSE 'assumed 0'
    END AS final_nutrient_origin,
  FROM step_2 AS nm
  LEFT JOIN ciqual_compo AS ciq
    ON nm.ciqual_food_code = ciq.alim_code AND ciq.const_code = nm.ciqual_const_code
  LEFT JOIN calnut_1 AS cal
    ON nm.ciqual_food_code = cal.ALIM_CODE AND cal.CONST_CODE = nm.calnut_const_code
  LEFT JOIN step_3 AS p
    ON nm.code = p.code AND nm.ciqual_food_code = p.ciqual_food_code AND nm.off_id = p.off_id
),
/* Illustration of step_5:
┌───────────────┬──────────────────┬──────────────┬─────────────┬────────────────┬───────────────┬──────────────┬────────────────┐
│     code      │ ciqual_food_code │ sodium_value │ sodium_unit │ sodium_origin  │ protein_value │ protein_unit │ protein_origin │
│    varchar    │      int32       │    float     │   varchar   │    varchar     │     float     │   varchar    │    varchar     │
├───────────────┼──────────────────┼──────────────┼─────────────┼────────────────┼───────────────┼──────────────┼────────────────┤
│ 3111950001928 │            20516 │         23.2 │ mg          │ ciqual_C_81259 │          20.5 │ g            │ product        │
│ 4099200179193 │            20904 │         10.0 │ mg          │ ciqual_A_83096 │          13.0 │ g            │ product        │
└───────────────┴──────────────────┴──────────────┴─────────────┴────────────────┴───────────────┴──────────────┴────────────────┘
*/
step_5 AS (
  SELECT * FROM step_4
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
),
/* Strip the `_value` suffix from any column name
Illustration of step_6:
┌───────────────┬──────────────────┬────────┬─────────────┬────────────────┬─────────┬──────────────┬────────────────┐
│     code      │ ciqual_food_code │ sodium │ sodium_unit │ sodium_origin  │ protein │ protein_unit │ protein_origin │
│    varchar    │      int32       │ float  │   varchar   │    varchar     │  float  │   varchar    │    varchar     │
├───────────────┼──────────────────┼────────┼─────────────┼────────────────┼─────────┼──────────────┼────────────────┤
│ 3111950001928 │            20516 │   23.2 │ mg          │ ciqual_C_81259 │    20.5 │ g            │ product        │
│ 4099200179193 │            20904 │   10.0 │ mg          │ ciqual_A_83096 │    13.0 │ g            │ product        │
└───────────────┴──────────────────┴────────┴─────────────┴────────────────┴─────────┴──────────────┴────────────────┘
*/
step_6 AS (
  SELECT *
  RENAME (
    energy_fibre_kj_value AS energy_fibre_kj,
    energy_fibre_kcal_value AS energy_fibre_kcal,
    water_value AS water,
    protein_value AS protein,
    carbohydrate_value AS carbohydrate,
    fat_value AS fat,
    sugars_value AS sugars,
    fructose_value AS fructose,
    galactose_value AS galactose,
    glucose_value AS glucose,
    lactose_value AS lactose,
    maltose_value AS maltose,
    sucrose_value AS sucrose,
    starch_value AS starch,
    fiber_value AS fiber,
    polyols_value AS polyols,
    alcohol_value AS alcohol,
    organic_acids_value AS organic_acids,
    saturated_fat_value AS saturated_fat,
    monounsaturated_fat_value AS monounsaturated_fat,
    polyunsaturated_fat_value AS polyunsaturated_fat,
    fa_04_0_value AS fa_04_0,
    fa_06_0_value AS fa_06_0,
    fa_08_0_value AS fa_08_0,
    fa_10_0_value AS fa_10_0,
    fa_12_0_value AS fa_12_0,
    fa_14_0_value AS fa_14_0,
    fa_16_0_value AS fa_16_0,
    fa_18_0_value AS fa_18_0,
    fa_18_1_ole_value AS fa_18_1_ole,
    fa_18_2_lino_value AS fa_18_2_lino,
    fa_18_3_a_lino_value AS fa_18_3_a_lino,
    fa_20_4_ara_value AS fa_20_4_ara,
    fa_20_5_epa_value AS fa_20_5_epa,
    fa_20_6_dha_value AS fa_20_6_dha,
    cholesterol_value AS cholesterol,
    salt_value AS salt,
    calcium_value AS calcium,
    copper_value AS copper,
    iron_value AS iron,
    iodine_value AS iodine,
    magnesium_value AS magnesium,
    manganese_value AS manganese,
    phosphorus_value AS phosphorus,
    potassium_value AS potassium,
    selenium_value AS selenium,
    sodium_value AS sodium,
    zinc_value AS zinc,
    retinol_value AS retinol,
    beta_carotene_value AS beta_carotene,
    vitamin_d_value AS vitamin_d,
    vitamin_e_value AS vitamin_e,
    vitamin_k1_value AS vitamin_k1,
    vitamin_k2_value AS vitamin_k2,
    vitamin_c_value AS vitamin_c,
    vitamin_b1_value AS vitamin_b1,
    vitamin_b2_value AS vitamin_b2,
    vitamin_pp_value AS vitamin_pp,
    pantothenic_acid_value AS pantothenic_acid,
    vitamin_b6_value AS vitamin_b6,
    vitamin_b9_value AS vitamin_b9,
    folates_value AS folates,
    vitamin_b12_value AS vitamin_b12,
  )
  FROM step_5
),
/* Illustration of step_7:
┌───────────────┬──────────────┬──────────────────┬──────────────────────┬───┬──────────────────────┬──────────────────────┬──────────────────────┐
│ product_code  │ product_name │ product_quantity │ product_quantity_u…  │ … │ biogenic_climate_c…  │ fossil_climate_cha…  │ land_use_change_cl…  │
│    varchar    │   varchar    │      float       │       varchar        │   │        double        │        double        │        double        │
├───────────────┼──────────────┼──────────────────┼──────────────────────┼───┼──────────────────────┼──────────────────────┼──────────────────────┤
│ 3111950001928 │ Pois chiches │           1000.0 │ g                    │ … │               0.0148 │                0.709 │                0.175 │
│ 3111950001928 │ Pois chiches │           1000.0 │ g                    │ … │               0.0148 │                0.709 │                0.175 │
│ 4099200179193 │ Tofu natur   │            350.0 │ g                    │ … │               0.0161 │                0.986 │              0.00187 │
│ 4099200179193 │ Tofu natur   │            350.0 │ g                    │ … │               0.0161 │                0.986 │              0.00187 │
│ 4099200179193 │ Tofu natur   │            350.0 │ g                    │ … │               0.0161 │                0.986 │              0.00187 │
├───────────────┴──────────────┴──────────────────┴──────────────────────┴───┴──────────────────────┴──────────────────────┴──────────────────────┤
│ 5 rows                                                                                                                     74 columns (7 shown) │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
*/
step_7 AS (
  SELECT
    -- Product columns
    p.code AS product_code,
    p.product_name,
    p.product_quantity,
    p.product_quantity_unit,
    -- Ciqual columns
    ciq.alim_code AS ciqual_code,
    ciq.alim_nom_eng AS ciqual_name,
    ciq.alim_grp_code AS ciqual_group_code,
    ciq.alim_ssgrp_code AS ciqual_subgroup_code,
    ciq.alim_ssssgrp_code AS ciqual_subsubgroup_code,
    -- Color column
    COALESCE(sc.color, '#ffffff') AS color,
    -- Price columns
    pr.id AS price_id,
    pr.price as product_price,
    pr.currency as product_currency,
    pr.location_id,
    pr.location_osm_id,
    pr.location_osm_display_name,
    pr.location_osm_lat,
    pr.location_osm_lon,
    -- DEBUG columns start --
    pr.type AS price_type,
    pr.owner AS price_owner,
    pr.price_is_discounted,
    pr.price_without_discount,
    pr.price_per,
    pr.date AS price_date,
    pr.created AS price_created,
    pr.updated AS price_updated,
    pr.source AS price_source,
    pr.location_type,
    pr.location_osm_type,
    pr.location_osm_tag_key,
    pr.location_osm_tag_value,
    pr.location_osm_address_postcode,
    pr.location_osm_address_city,
    pr.location_osm_address_country,
    pr.location_osm_address_country_code,
    pr.location_website_url,
    pr.location_source,
    pr.location_created,
    pr.location_updated,
    -- DEBUG columns end --
    -- Price in EUR per 100g
    100 * pr.price / p.product_quantity / ex.rate AS price,  -- TODO: this assumes that product_quantity is in grams
    -- Nutrient columns
    prev.*,
    -- Agribalyse columns
    ab.season_code,
    ab.air_transport_code,
    ab.delivery_method,
    ab.packaging_approach,
    ab.preparation_method,
    ab.data_quality_rating,
    ab.eco_score,
    ab.climate_change,
    ab.ozone_depletion,
    ab.ionizing_radiation,
    ab.photochemical_ozone_formation,
    ab.fine_particles,
    ab.non_carcinogenic_toxicity,
    ab.carcinogenic_toxicity,
    ab.terrestrial_acidification,
    ab.freshwater_eutrophication,
    ab.marine_eutrophication,
    ab.terrestrial_eutrophication,
    ab.freshwater_ecotoxicity,
    ab.land_use,
    ab.water_depletion,
    ab.energy_depletion,
    ab.mineral_depletion,
    ab.biogenic_climate_change_emissions,
    ab.fossil_climate_change_emissions,
    ab.land_use_change_climate_change_emissions,
  FROM prices AS pr
  JOIN step_6 AS prev ON pr.product_code = prev.code
  JOIN step_1 AS p ON pr.product_code = p.code
  JOIN euro_exchange_rates AS ex ON pr.currency = ex.currency
  LEFT JOIN ciqual_alim AS ciq ON ciq.alim_code = prev.ciqual_food_code
  LEFT JOIN agribalyse AS ab ON ab.ciqual_food_code = prev.ciqual_food_code
  LEFT JOIN ssgrp_colors AS sc ON ciq.alim_ssgrp_code = sc.alim_ssgrp_code
  WHERE pr.price IS NOT NULL AND p.product_quantity > 0 and p.product_quantity < 30000 -- Filter out invalid quantities (e.g. 0 or >30 kg)
)
SELECT * FROM step_7
);
COMMENT ON TABLE final_table_price IS 'Final table with products, prices, ciqual and agribalyse data';
COMMENT ON COLUMN final_table_price.product_code IS 'Product code (EAN-13)';
COMMENT ON COLUMN final_table_price.product_name IS 'Product name in Original language';
COMMENT ON COLUMN final_table_price.product_quantity IS 'Product quantity in grams or milliliters';
COMMENT ON COLUMN final_table_price.product_quantity_unit IS 'Product quantity unit (g or ml)';
COMMENT ON COLUMN final_table_price.product_price IS 'Price of one product in EUR';
COMMENT ON COLUMN final_table_price.price IS 'Price in EUR/100g';
COMMENT ON COLUMN final_table_price.product_currency IS 'Product price currency (EUR)';
COMMENT ON COLUMN final_table_price.price_id IS 'Price ID in Open Prices';
-- SELECT product_quantity_unit AS unit, count(*) AS cnt from final_table_price GROUP BY unit ORDER BY cnt DESC;
COMMENT ON COLUMN final_table_price.ciqual_code IS 'Ciqual food code (Aliment code)';
COMMENT ON COLUMN final_table_price.ciqual_name IS 'Ciqual food name in English';
COMMENT ON COLUMN final_table_price.energy_fibre_kj IS 'Energy in kJ/100g';
COMMENT ON COLUMN final_table_price.energy_fibre_kcal IS 'Energy in kcal/100g';
COMMENT ON COLUMN final_table_price.water IS 'Water g/100g';
COMMENT ON COLUMN final_table_price.protein IS 'Protein g/100g';
COMMENT ON COLUMN final_table_price.carbohydrate IS 'Carbohydrate g/100g';
COMMENT ON COLUMN final_table_price.fat IS 'Fat g/100g';
COMMENT ON COLUMN final_table_price.sugars IS 'Sugars g/100g';
COMMENT ON COLUMN final_table_price.fructose IS 'Fructose g/100g';
COMMENT ON COLUMN final_table_price.galactose IS 'Galactose g/100g';
COMMENT ON COLUMN final_table_price.glucose IS 'Glucose g/100g';
COMMENT ON COLUMN final_table_price.lactose IS 'Lactose g/100g';
COMMENT ON COLUMN final_table_price.maltose IS 'Maltose g/100g';
COMMENT ON COLUMN final_table_price.sucrose IS 'Sucrose g/100g';
COMMENT ON COLUMN final_table_price.starch IS 'Starch g/100g';
COMMENT ON COLUMN final_table_price.fiber IS 'Fiber g/100g';
COMMENT ON COLUMN final_table_price.polyols IS 'Polyols g/100g';
COMMENT ON COLUMN final_table_price.alcohol IS 'Alcohol g/100g';
COMMENT ON COLUMN final_table_price.organic_acids IS 'Organic acids g/100g';
COMMENT ON COLUMN final_table_price.saturated_fat IS 'Saturated fat g/100g';
COMMENT ON COLUMN final_table_price.monounsaturated_fat IS 'Monounsaturated fat g/100g';
COMMENT ON COLUMN final_table_price.polyunsaturated_fat IS 'Polyunsaturated fat g/100g';
COMMENT ON COLUMN final_table_price.fa_04_0 IS 'Fatty acid 04:0 g/100g';
COMMENT ON COLUMN final_table_price.fa_06_0 IS 'Fatty acid 06:0 g/100g';
COMMENT ON COLUMN final_table_price.fa_08_0 IS 'Fatty acid 08:0 g/100g';
COMMENT ON COLUMN final_table_price.fa_10_0 IS 'Fatty acid 10:0 g/100g';
COMMENT ON COLUMN final_table_price.fa_12_0 IS 'Fatty acid 12:0 g/100g';
COMMENT ON COLUMN final_table_price.fa_14_0 IS 'Fatty acid 14:0 g/100g';
COMMENT ON COLUMN final_table_price.fa_16_0 IS 'Fatty acid 16:0 g/100g';
COMMENT ON COLUMN final_table_price.fa_18_0 IS 'Fatty acid 18:0 g/100g';
COMMENT ON COLUMN final_table_price.fa_18_1_ole IS 'Fatty acid 18:1 oleic g/100g';
COMMENT ON COLUMN final_table_price.fa_18_2_lino IS 'Fatty acid 18:2 linoleic g/100g';
COMMENT ON COLUMN final_table_price.fa_18_3_a_lino IS 'Fatty acid 18:3 alpha-linolenic g/100g';
COMMENT ON COLUMN final_table_price.fa_20_4_ara IS 'Fatty acid 20:4 arachidonic g/100g';
COMMENT ON COLUMN final_table_price.fa_20_5_epa IS 'Fatty acid 20:5 eicosapentaenoic g/100g';
COMMENT ON COLUMN final_table_price.fa_20_6_dha IS 'Fatty acid 20:6 docosahexaenoic g/100g';
COMMENT ON COLUMN final_table_price.cholesterol IS 'Cholesterol mg/100g';
COMMENT ON COLUMN final_table_price.salt IS 'Salt g/100g';
COMMENT ON COLUMN final_table_price.calcium IS 'Calcium mg/100g';
COMMENT ON COLUMN final_table_price.copper IS 'Copper mg/100g';
COMMENT ON COLUMN final_table_price.iron IS 'Iron mg/100g';
COMMENT ON COLUMN final_table_price.iodine IS 'Iodine µg/100g';
COMMENT ON COLUMN final_table_price.magnesium IS 'Magnesium mg/100g';
COMMENT ON COLUMN final_table_price.manganese IS 'Manganese mg/100g';
COMMENT ON COLUMN final_table_price.phosphorus IS 'Phosphorus mg/100g';
COMMENT ON COLUMN final_table_price.potassium IS 'Potassium mg/100g';
COMMENT ON COLUMN final_table_price.selenium IS 'Selenium µg/100g';
COMMENT ON COLUMN final_table_price.sodium IS 'Sodium mg/100g';
COMMENT ON COLUMN final_table_price.zinc IS 'Zinc mg/100g';
COMMENT ON COLUMN final_table_price.retinol IS 'Retinol µg/100g';
COMMENT ON COLUMN final_table_price.beta_carotene IS 'Beta-carotene µg/100g';
COMMENT ON COLUMN final_table_price.vitamin_d IS 'Vitamin D µg/100g';
COMMENT ON COLUMN final_table_price.vitamin_e IS 'Vitamin E mg/100g';
COMMENT ON COLUMN final_table_price.vitamin_k1 IS 'Vitamin K1 µg/100g';
COMMENT ON COLUMN final_table_price.vitamin_k2 IS 'Vitamin K2 µg/100g';
COMMENT ON COLUMN final_table_price.vitamin_c IS 'Vitamin C mg/100g';
COMMENT ON COLUMN final_table_price.vitamin_b1 IS 'Vitamin B1 mg/100g';
COMMENT ON COLUMN final_table_price.vitamin_b2 IS 'Vitamin B2 mg/100g';
COMMENT ON COLUMN final_table_price.vitamin_pp IS 'Vitamin PP mg/100g';
COMMENT ON COLUMN final_table_price.pantothenic_acid IS 'Pantothenic acid mg/100g';
COMMENT ON COLUMN final_table_price.vitamin_b6 IS 'Vitamin B6 mg/100g';
COMMENT ON COLUMN final_table_price.vitamin_b9 IS 'Vitamin B9 µg/100g';
COMMENT ON COLUMN final_table_price.folates IS 'Folates';
COMMENT ON COLUMN final_table_price.vitamin_b12 IS 'Vitamin B12 µg/100g';
-- See documentation links for agribalyse in Makefile
-- This document was used: Agribalyse-Guide-VF_Planche.pdf
COMMENT ON COLUMN final_table_price.data_quality_rating IS 'Agribalyse data quality rating';
COMMENT ON COLUMN final_table_price.eco_score IS 'Agribalyse eco score';
COMMENT ON COLUMN final_table_price.climate_change IS 'Agribalyse climate change (kg CO2 eq)';
COMMENT ON COLUMN final_table_price.ozone_depletion IS 'Agribalyse ozone depletion (kg CFC-11 eq)';
COMMENT ON COLUMN final_table_price.fine_particles IS 'Agribalyse fine particles (Disease incidences)';
COMMENT ON COLUMN final_table_price.terrestrial_acidification IS 'Agribalyse terrestrial acidification (mol H+ eq)';
COMMENT ON COLUMN final_table_price.freshwater_eutrophication IS 'Agribalyse freshwater eutrophication (kg P eq)';
COMMENT ON COLUMN final_table_price.marine_eutrophication IS 'Agribalyse marine eutrophication (kg N eq)';
COMMENT ON COLUMN final_table_price.terrestrial_eutrophication IS 'Agribalyse terrestrial eutrophication (mol N eq)';
COMMENT ON COLUMN final_table_price.ionizing_radiation IS 'Agribalyse ionizing radiation (kBq U-235 eq)';
COMMENT ON COLUMN final_table_price.photochemical_ozone_formation IS 'Agribalyse photochemical ozone formation (kg NMVOC eq)';
COMMENT ON COLUMN final_table_price.freshwater_ecotoxicity IS 'Agribalyse freshwater ecotoxicity (CTUe)';
COMMENT ON COLUMN final_table_price.carcinogenic_toxicity IS 'Agribalyse carcinogenic toxicity (CTUh)';
COMMENT ON COLUMN final_table_price.non_carcinogenic_toxicity IS 'Agribalyse non-carcinogenic toxicity (CTUh)';
COMMENT ON COLUMN final_table_price.land_use IS 'Agribalyse land use (point score, based on the LANCA model)';
COMMENT ON COLUMN final_table_price.energy_depletion IS 'Agribalyse energy depletion (MJ)';
COMMENT ON COLUMN final_table_price.mineral_depletion IS 'Agribalyse mineral depletion (kg Sb eq)';
COMMENT ON COLUMN final_table_price.water_depletion IS 'Agribalyse water depletion (m3 Eau eq)';
COMMENT ON COLUMN final_table_price.biogenic_climate_change_emissions IS 'Agribalyse biogenic climate change emissions';
COMMENT ON COLUMN final_table_price.fossil_climate_change_emissions IS 'Agribalyse fossil climate change emissions';
COMMENT ON COLUMN final_table_price.land_use_change_climate_change_emissions IS 'Agribalyse land use change climate change emissions';
--
