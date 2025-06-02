/* Queries for loading data into the database
Links to data documentation can be found in the Makefile.
*/
-- Nutrient mapping table
CREATE OR REPLACE TABLE nutrient_map AS (
  SELECT id, name, nutrient_type,
  ciqual_const_code, ciqual_const_name_eng, ciqual_unit,
  calnut_const_code, calnut_const_name, calnut_unit,
  off_id, count, template, nnr2023_id, disabled
  FROM read_csv('data/nutrient_map.csv')
  WHERE calnut_const_code IS NOT NULL
);
-- Hardcoded macronutrient recommendations
CREATE OR REPLACE TABLE recommendations_macro AS (
  SELECT id, unit,
  value_males, value_females, value_upper_intake
  FROM read_csv('data/recommendations_macro.csv')
);
-- Hardcoded micronutrient recommendations
CREATE OR REPLACE TABLE recommendations_nnr2023 AS (
  SELECT nutrient, unit, RI_or_AI,
  value_males, value_females, value_upper_intake
  FROM read_csv('data/recommendations_nnr2023.csv')
);
/* Tables:
- alim: information about the food (3 185 rows)
- compo: information about the nutrients in the food (211 898 rows)
- const: information about the nutrients (67 rows) (already in nutrient_map)
- sources: information about the sources of the data (207 896 rows)
Illustration of ciqual_alim:
┌───────────┬──────────────────┬───────────────┬─────────────────┬───────────────────┐
│ alim_code │   alim_nom_eng   │ alim_grp_code │ alim_ssgrp_code │ alim_ssssgrp_code │
│   int64   │     varchar      │    varchar    │     varchar     │      varchar      │
├───────────┼──────────────────┼───────────────┼─────────────────┼───────────────────┤
│     20516 │ Chick pea, dried │ 02            │ 0203            │ 020303            │
│     20904 │ Tofu, plain      │ 04            │ 0411            │ 000000            │
└───────────┴──────────────────┴───────────────┴─────────────────┴───────────────────┘
Illustration of ciqual_compo:
┌───────────┬────────────┬────────────────┬─────────────┬───────┬───────┬───────┐
│ alim_code │ const_code │ code_confiance │ source_code │  lb   │  ub   │ mean  │
│   int64   │   int64    │    varchar     │    int64    │ float │ float │ float │
├───────────┼────────────┼────────────────┼─────────────┼───────┼───────┼───────┤
│     20516 │      25000 │ C              │       81271 │  20.0 │  25.8 │  20.5 │
│     20516 │      10110 │ C              │       81259 │   5.5 │  40.0 │  23.2 │
│     20904 │      10110 │ A              │       83096 │   7.0 │ 158.0 │  10.0 │
│     20904 │      25000 │ A              │       83108 │  6.84 │  NULL │  13.4 │
└───────────┴────────────┴────────────────┴─────────────┴───────┴───────┴───────┘
*/
CREATE OR REPLACE TABLE ciqual_alim AS (
  SELECT alim_code, alim_nom_eng, alim_grp_code, alim_ssgrp_code, alim_ssssgrp_code
  FROM read_csv('data/ciqual2020/alim.csv')
);
CREATE OR REPLACE TABLE ciqual_compo AS (
  SELECT alim_code, const_code, code_confiance, source_code,
  CASE WHEN min = '-' THEN NULL ELSE CAST(REPLACE(REPLACE(min, 'traces', '0'), ',', '.') AS FLOAT) END AS lb,
  CASE WHEN max = '-' THEN NULL ELSE CAST(REPLACE(REPLACE(max, 'traces', '0'), ',', '.') AS FLOAT) END AS ub,
  CASE WHEN teneur = '-' THEN NULL ELSE CAST(REPLACE(REPLACE(teneur, 'traces', '0'), ',', '.') AS FLOAT) END AS mean
  FROM read_csv('data/ciqual2020/compo.csv')
);
CREATE OR REPLACE TABLE ciqual_sources AS (
  SELECT source_code, ref_citation FROM read_csv('data/ciqual2020/sources.csv')
);
/* Table 0 contains food group information (2 119 rows)
Table 1 contains nutrient information for each food and nutrient (131 378 rows)
Both tables are joined on the ALIM_CODE and FOOD_LABEL columns
Illustration of calnut_0:
┌───────────┬──────────────────────┬───────────────┬─────────────────┬───┬──────────────────────┬──────────────────────┬─────────────────────┐
│ alim_code │      FOOD_LABEL      │ alim_grp_code │ alim_ssgrp_code │ … │   alim_grp_nom_fr    │  alim_ssgrp_nom_fr   │ alim_ssssgrp_nom_fr │
│   int64   │       varchar        │    varchar    │     varchar     │   │       varchar        │       varchar        │       varchar       │
├───────────┼──────────────────────┼───────────────┼─────────────────┼───┼──────────────────────┼──────────────────────┼─────────────────────┤
│     20904 │ Tofu nature, préem…  │ 04            │ 0411            │ … │ viandes, œufs, poi…  │ substitus de produ…  │ -                   │
├───────────┴──────────────────────┴───────────────┴─────────────────┴───┴──────────────────────┴──────────────────────┴─────────────────────┤
│ 1 rows                                                                                                                 8 columns (7 shown) │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
Illustration of calnut_1:
┌───────────┬─────────────────────────┬─────────────┬────────────┬─────────┬───────┬───────┬───────┐
│ ALIM_CODE │       FOOD_LABEL        │ CONST_LABEL │ CONST_CODE │  combl  │  lb   │  ub   │ mean  │
│   int64   │         varchar         │   varchar   │   int64    │ boolean │ float │ float │ float │
├───────────┼─────────────────────────┼─────────────┼────────────┼─────────┼───────┼───────┼───────┤
│     20904 │ Tofu nature, préemballé │ sodium_mg   │      10110 │ false   │  10.0 │  10.0 │  10.0 │
│     20904 │ Tofu nature, préemballé │ proteines_g │      25000 │ false   │  13.4 │  13.4 │  13.4 │
└───────────┴─────────────────────────┴─────────────┴────────────┴─────────┴───────┴───────┴───────┘
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
  CAST(indic_combl AS BOOL) AS combl,
  CAST(REPLACE(LB, ',', '.') AS FLOAT) AS lb,
  CAST(REPLACE(UB, ',', '.') AS FLOAT) AS ub,
  CAST(REPLACE(MB, ',', '.') AS FLOAT) AS mean,
  FROM read_csv('data/calnut.1.csv')
);
/* Illustration of prices:
┌───────┬─────────┬───────────────┬──────────────────────┬───┬──────────────────────┬─────────────────┬──────────────────────┬──────────────────────┐
│  id   │  type   │ product_code  │     product_name     │ … │ location_website_url │ location_source │   location_created   │   location_updated   │
│ int64 │ varchar │    varchar    │       varchar        │   │       varchar        │     varchar     │ timestamp with tim…  │ timestamp with tim…  │
├───────┼─────────┼───────────────┼──────────────────────┼───┼──────────────────────┼─────────────────┼──────────────────────┼──────────────────────┤
│ 29904 │ PRODUCT │ 4099200179193 │ NULL                 │ … │ NULL                 │ NULL            │ 2024-07-06 14:35:3…  │ 2024-07-07 15:35:3…  │
│ 29955 │ PRODUCT │ 3111950001928 │ NULL                 │ … │ NULL                 │ NULL            │ 2024-07-06 19:59:0…  │ 2024-07-07 09:55:1…  │
│ 77758 │ PRODUCT │ 4099200179193 │ Tofu bio nature fu…  │ … │ NULL                 │ NULL            │ 2024-07-06 14:35:3…  │ 2024-07-07 15:35:3…  │
├───────┴─────────┴───────────────┴──────────────────────┴───┴──────────────────────┴─────────────────┴──────────────────────┴──────────────────────┤
│ 3 rows                                                                                                                       48 columns (8 shown) │
└───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
*/
CREATE OR REPLACE TABLE prices AS (
  SELECT * FROM read_parquet('data/prices.parquet')
);
/* Note: there are duplicates of the code in products, it is not a unique key
Illustration of products:
┌───────────────┬──────────────────┬──────────────────────┬──────────────────────┬───┬──────────────────┬──────────────────────┬──────────────────────┐
│     code      │ product_quantity │     product_name     │ product_quantity_u…  │ … │ ciqual_food_code │ ciqual_food_code_o…  │      nutriments      │
│    varchar    │      float       │ struct(lang varcha…  │       varchar        │   │      int32       │       varchar        │ struct("name" varc…  │
├───────────────┼──────────────────┼──────────────────────┼──────────────────────┼───┼──────────────────┼──────────────────────┼──────────────────────┤
│ 3111950001928 │           1000.0 │ [{'lang': main, 't…  │ g                    │ … │            20516 │                      │ [{'name': energy, …  │
│ 4099200179193 │            350.0 │ [{'lang': main, 't…  │ g                    │ … │            20904 │                      │ [{'name': energy, …  │
├───────────────┴──────────────────┴──────────────────────┴──────────────────────┴───┴──────────────────┴──────────────────────┴──────────────────────┤
│ 2 rows                                                                                                                          8 columns (7 shown) │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
*/
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
  CAST(product_quantity AS FLOAT) AS product_quantity,
  quantity AS quantity_str,
  categories_properties,
  COALESCE(
      categories_properties.ciqual_food_code,
      categories_properties.agribalyse_food_code,
      categories_properties.agribalyse_proxy_food_code
  ) AS ciqual_food_code,
  CASE
      WHEN categories_properties.ciqual_food_code IS NOT NULL THEN ''
      WHEN categories_properties.agribalyse_food_code IS NOT NULL THEN 'agribalyse_'
      WHEN categories_properties.agribalyse_proxy_food_code IS NOT NULL THEN 'agribalyse_proxy_'
      ELSE 'unknown'
  END AS ciqual_food_code_origin,
  FROM read_parquet('data/products.parquet')
);
