-- Final table with one row per food type in the ciqual database, enriched with price and agribalyse data.
CREATE OR REPLACE TABLE final_table_food AS (
WITH
/* All alim codes.
Illustration of step_1:
┌──────────────────┐
│ ciqual_food_code │
│      int64       │
├──────────────────┤
│            20516 │
│            20904 │
└──────────────────┘
*/
step_1 AS (
  SELECT alim_code AS ciqual_food_code FROM ciqual_alim
    UNION
  SELECT alim_code AS ciqual_food_code FROM calnut_0
    UNION
  SELECT ciqual_food_code FROM agribalyse
),
/* All alim code x nutrient_map (table to later be pivoted)
Illustration of step_2:
┌──────────────────┬─────────────┬───────────────────┬─────────────┬───────────────────┬─────────────┐
│ ciqual_food_code │ nutrient_id │ ciqual_const_code │ ciqual_unit │ calnut_const_code │ calnut_unit │
│      int64       │   varchar   │       int64       │   varchar   │       int64       │   varchar   │
├──────────────────┼─────────────┼───────────────────┼─────────────┼───────────────────┼─────────────┤
│            20516 │ sodium      │             10110 │ mg          │             10110 │ mg          │
│            20516 │ protein     │             25000 │ g           │             25000 │ g           │
│            20904 │ protein     │             25000 │ g           │             25000 │ g           │
│            20904 │ sodium      │             10110 │ mg          │             10110 │ mg          │
└──────────────────┴─────────────┴───────────────────┴─────────────┴───────────────────┴─────────────┘
*/
step_2 AS (
  SELECT
    prev.ciqual_food_code,
    nm.id AS nutrient_id,
    nm.ciqual_const_code, nm.ciqual_unit,
    nm.calnut_const_code, nm.calnut_unit,
  FROM step_1 AS prev
  JOIN nutrient_map AS nm ON TRUE
  WHERE nm.ciqual_const_code IS NOT NULL OR nm.calnut_const_code IS NOT NULL
),
/* Illustration of step_3:
┌─────────────┬──────────────────┬──────────────────────┬─────────────────────┬───────────────────────┐
│ nutrient_id │ ciqual_food_code │ final_nutrient_value │ final_nutrient_unit │ final_nutrient_origin │
│   varchar   │      int64       │        float         │       varchar       │        varchar        │
├─────────────┼──────────────────┼──────────────────────┼─────────────────────┼───────────────────────┤
│ protein     │            20516 │                 20.5 │ g                   │ ciqual_C_81271        │
│ protein     │            20904 │                 13.4 │ g                   │ ciqual_A_83108        │
│ sodium      │            20516 │                 23.2 │ mg                  │ ciqual_C_81259        │
│ sodium      │            20904 │                 10.0 │ mg                  │ ciqual_A_83096        │
└─────────────┴──────────────────┴──────────────────────┴─────────────────────┴───────────────────────┘
*/
step_3 AS (
  SELECT
    nm.nutrient_id,
    nm.ciqual_food_code,
    CASE
      WHEN ciq.mean IS NOT NULL THEN ciq.mean
      WHEN cal.mean IS NOT NULL THEN cal.mean
      ELSE 0  -- When unknown, assume 0
    END AS final_nutrient_value,
    CASE
      WHEN ciq.mean IS NOT NULL THEN nm.ciqual_unit
      WHEN cal.mean IS NOT NULL THEN nm.calnut_unit
      ELSE nm.ciqual_unit
    END AS final_nutrient_unit,
    CASE
      WHEN ciq.mean IS NOT NULL THEN CONCAT('ciqual_', ciq.code_confiance, '_', ciq.source_code)
      WHEN cal.mean IS NOT NULL THEN CONCAT('calnut_', CASE WHEN cal.combl THEN 'combl' ELSE '' END)
      ELSE 'assumed 0'
    END AS final_nutrient_origin,
  FROM step_2 AS nm
  LEFT JOIN ciqual_compo AS ciq
    ON nm.ciqual_food_code = ciq.alim_code AND ciq.const_code = nm.ciqual_const_code
  LEFT JOIN calnut_1 AS cal
    ON nm.ciqual_food_code = cal.ALIM_CODE AND cal.CONST_CODE = nm.calnut_const_code
),
/* Illustration of step_4:
┌──────────────────┬──────────────┬─────────────┬────────────────┬───────────────┬──────────────┬────────────────┐
│ ciqual_food_code │ sodium_value │ sodium_unit │ sodium_origin  │ protein_value │ protein_unit │ protein_origin │
│      int64       │    float     │   varchar   │    varchar     │     float     │   varchar    │    varchar     │
├──────────────────┼──────────────┼─────────────┼────────────────┼───────────────┼──────────────┼────────────────┤
│            20516 │         23.2 │ mg          │ ciqual_C_81259 │          20.5 │ g            │ ciqual_C_81271 │
│            20904 │         10.0 │ mg          │ ciqual_A_83096 │          13.4 │ g            │ ciqual_A_83108 │
└──────────────────┴──────────────┴─────────────┴────────────────┴───────────────┴──────────────┴────────────────┘
*/
step_4 AS (
  SELECT * FROM step_3
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
    GROUP BY ciqual_food_code
  )
),
/* Strip the `_value` suffix from any column name
Illustration of step_5:
┌──────────────────┬────────┬─────────────┬────────────────┬─────────┬──────────────┬────────────────┐
│ ciqual_food_code │ sodium │ sodium_unit │ sodium_origin  │ protein │ protein_unit │ protein_origin │
│      int64       │ float  │   varchar   │    varchar     │  float  │   varchar    │    varchar     │
├──────────────────┼────────┼─────────────┼────────────────┼─────────┼──────────────┼────────────────┤
│            20516 │   23.2 │ mg          │ ciqual_C_81259 │    20.5 │ g            │ ciqual_C_81271 │
│            20904 │   10.0 │ mg          │ ciqual_A_83096 │    13.4 │ g            │ ciqual_A_83108 │
└──────────────────┴────────┴─────────────┴────────────────┴─────────┴──────────────┴────────────────┘
*/
step_5 AS (
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
  FROM step_4
),
/* Illustration of step_6:
┌──────────────────┬─────────────────────┬───────┐
│ ciqual_food_code │        price        │ count │
│      int32       │       double        │ int64 │
├──────────────────┼─────────────────────┼───────┤
│            20516 │ 0.20499999821186066 │     2 │
│            20904 │ 0.41217599115862913 │     3 │
└──────────────────┴─────────────────────┴───────┘
*/
step_6 AS (
  SELECT
    p.ciqual_food_code,
    median(100 * pr.price / p.product_quantity / ex.rate) AS price,
    count(*) AS count
  FROM prices AS pr
  JOIN products AS p ON pr.product_code = p.code
  JOIN euro_exchange_rates AS ex ON pr.currency  = ex.currency
  WHERE pr.price IS NOT NULL
    AND p.product_quantity BETWEEN 1 AND 30000
    AND p.ciqual_food_code IS NOT NULL
  GROUP BY p.ciqual_food_code
),
/* Illustration of step_7:
┌─────────────┬──────────────────┬───────────────────┬───┬──────────────────────┬──────────────────────┬──────────────────────┐
│ ciqual_code │   ciqual_name    │ ciqual_group_code │ … │ biogenic_climate_c…  │ fossil_climate_cha…  │ land_use_change_cl…  │
│    int64    │     varchar      │      varchar      │   │        double        │        double        │        double        │
├─────────────┼──────────────────┼───────────────────┼───┼──────────────────────┼──────────────────────┼──────────────────────┤
│       20516 │ Chick pea, dried │ 02                │ … │               0.0148 │                0.709 │                0.175 │
│       20904 │ Tofu, plain      │ 04                │ … │               0.0161 │                0.986 │              0.00187 │
├─────────────┴──────────────────┴───────────────────┴───┴──────────────────────┴──────────────────────┴──────────────────────┤
│ 2 rows                                                                                                 41 columns (6 shown) │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
*/
step_7 AS (
  SELECT
    ciq.alim_code AS ciqual_code,
    ciq.alim_nom_eng AS ciqual_name,
    ciq.alim_grp_code AS ciqual_group_code,
    ciq.alim_ssgrp_code AS ciqual_subgroup_code,
    ciq.alim_ssssgrp_code AS ciqual_subsubgroup_code,
    -- Color column
    COALESCE(sc.color, '#ffffff') AS color,
    -- Price columns
    pr.price,
    pr.count AS price_count,
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
  FROM step_5 AS prev
  LEFT JOIN step_6 AS pr ON prev.ciqual_food_code = pr.ciqual_food_code
  LEFT JOIN ciqual_alim AS ciq ON ciq.alim_code = prev.ciqual_food_code
  LEFT JOIN agribalyse AS ab ON ab.ciqual_food_code = prev.ciqual_food_code
  LEFT JOIN ssgrp_colors AS sc ON ciq.alim_ssgrp_code = sc.alim_ssgrp_code
)
SELECT * FROM step_7
);
