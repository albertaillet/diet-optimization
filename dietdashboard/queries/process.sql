CREATE OR REPLACE TABLE final_table AS (
WITH
/* Illustration of step_1:
┌──────────────┬───────────────┬──────────────────┬───┬────────────────────┬──────────────────┬──────────────────────┬──────────────────────┐
│ product_name │     code      │ product_quantity │ … │ product_quantity_1 │ ciqual_food_code │ ciqual_food_code_o…  │      nutriments      │
│   varchar    │    varchar    │      float       │   │       float        │      int32       │       varchar        │ struct("name" varc…  │
├──────────────┼───────────────┼──────────────────┼───┼────────────────────┼──────────────────┼──────────────────────┼──────────────────────┤
│ Pois chiches │ 3111950001928 │           1000.0 │ … │             1000.0 │            20516 │ ciqual               │ [{'name': energy, …  │
│ Tofu natur   │ 4099200179193 │            350.0 │ … │              350.0 │            20904 │ ciqual               │ [{'name': energy, …  │
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
│ 3111950001928 │            20516 │ ciqual               │ protein     │ proteins │             25000 │ g           │             25000 │ g           │
│ 3111950001928 │            20516 │ ciqual               │ sodium      │ sodium   │             10110 │ mg          │             10110 │ mg          │
│ 4099200179193 │            20904 │ ciqual               │ protein     │ proteins │             25000 │ g           │             25000 │ g           │
│ 4099200179193 │            20904 │ ciqual               │ sodium      │ sodium   │             10110 │ mg          │             10110 │ mg          │
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
  WHERE nm.ciqual_const_code IS NOT NULL OR nm.calnut_const_code IS NOT NULL -- TODO: Possibly use disabled here as well
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
│ 3111950001928 │            20516 │ nova-group         │ NULL          │           NULL │ false                     │
│ 3111950001928 │            20516 │ sodium             │ g             │          0.024 │ true                      │
│ 3111950001928 │            20516 │ energy-kj          │ kJ            │         1480.0 │ true                      │
│ 3111950001928 │            20516 │ sugars             │ g             │            6.5 │ true                      │
│ 3111950001928 │            20516 │ fat                │ g             │            5.9 │ true                      │
│       ·       │              ·   │  ·                 │ ·             │             ·  │  ·                        │
│       ·       │              ·   │  ·                 │ ·             │             ·  │  ·                        │
│       ·       │              ·   │  ·                 │ ·             │             ·  │  ·                        │
│ 4099200179193 │            20904 │ energy-kj          │ kJ            │          528.0 │ true                      │
│ 4099200179193 │            20904 │ carbohydrates      │ g             │            0.0 │ true                      │
│ 4099200179193 │            20904 │ nutrition-score-fr │ NULL          │           NULL │ false                     │
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
    n.unnest.value AS nutrient_value,
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
    -- nm.ciqual_food_code_origin, -- TODO: use ciqual_food_code_origin as part of the final_nutrient_origin
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
      WHEN ciq.mean IS NOT NULL THEN CONCAT('ciqual_', ciq.code_confiance, '_', ciq.source_code)
      WHEN cal.mean IS NOT NULL THEN CONCAT('calnut', CASE WHEN cal.combl THEN '_combl' ELSE '' END)
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
/* Illustration of step_6:
┌───────────────┬──────────────┬──────────────────┬──────────────────────┬───┬────────────────┬───────────────┬──────────────┬────────────────┐
│ product_code  │ product_name │ product_quantity │ product_quantity_u…  │ … │ sodium_origin  │ protein_value │ protein_unit │ protein_origin │
│    varchar    │   varchar    │      float       │       varchar        │   │    varchar     │     float     │   varchar    │    varchar     │
├───────────────┼──────────────┼──────────────────┼──────────────────────┼───┼────────────────┼───────────────┼──────────────┼────────────────┤
│ 3111950001928 │ Pois chiches │           1000.0 │ g                    │ … │ ciqual_C_81259 │          20.5 │ g            │ product        │
│ 4099200179193 │ Tofu natur   │            350.0 │ g                    │ … │ ciqual_A_83096 │          13.0 │ g            │ product        │
│ 4099200179193 │ Tofu natur   │            350.0 │ g                    │ … │ ciqual_A_83096 │          13.0 │ g            │ product        │
├───────────────┴──────────────┴──────────────────┴──────────────────────┴───┴────────────────┴───────────────┴──────────────┴────────────────┤
│ 3 rows                                                                                                                 26 columns (8 shown) │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
*/
step_6 AS (
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
    -- Price columns
    pr.id AS price_id,
    pr.price,
    pr.currency,
    pr.location_id,
    pr.location_osm_id,
    pr.location_osm_display_name,
    pr.location_osm_lat,
    pr.location_osm_lon,
    -- DEBUG columns start --
    -- pr.type AS price_type,
    -- pr.owner AS price_owner,
    -- pr.price_is_discounted,
    -- pr.price_without_discount,
    -- pr.price_per,
    -- pr.date AS price_date,
    -- pr.created AS price_created,
    -- pr.updated AS price_updated,
    -- pr.source AS price_source,
    -- pr.location_type,
    -- pr.location_osm_type,
    -- pr.location_osm_tag_key,
    -- pr.location_osm_tag_value,
    -- pr.location_osm_address_postcode,
    -- pr.location_osm_address_city,
    -- pr.location_osm_address_country,
    -- pr.location_osm_address_country_code,
    -- pr.location_website_url,
    -- pr.location_source,
    -- pr.location_created,
    -- pr.location_updated,
    -- DEBUG columns end --
    -- Price per quantity
    1000 * pr.price / p.product_quantity AS price_per_quantity,  -- TODO: this assumes that the quantity is in grams
    -- Nutrient columns
    prev.*,
  FROM prices AS pr
  JOIN step_5 AS prev
    ON pr.product_code = prev.code
  JOIN step_1 AS p
    ON pr.product_code = p.code
  LEFT JOIN ciqual_alim AS ciq
    ON prev.ciqual_food_code = ciq.alim_code
)
SELECT * FROM step_6
);
