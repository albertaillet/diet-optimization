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
-- Hardcoded unit conversions
CREATE OR REPLACE TABLE unit_conversion AS (
  SELECT from_unit, to_unit, conversion_factor FROM read_csv('data/unit_conversion.csv')
);
-- Hardcoded colors
CREATE OR REPLACE TABLE ssgrp_colors AS (
  SELECT color, alim_ssgrp_code, alim_ssgrp_nom_eng FROM read_csv('data/ssgrp_colors.csv')
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
┌───────────┬─────────────────────────┬───────────────┬─────────────────┬───────────────────┬──────────────────────────────────────┬──────────────────────────────┬─────────────────────┐
│ alim_code │       FOOD_LABEL        │ alim_grp_code │ alim_ssgrp_code │ alim_ssssgrp_code │           alim_grp_nom_fr            │      alim_ssgrp_nom_fr       │ alim_ssssgrp_nom_fr │
│   int64   │         varchar         │    varchar    │     varchar     │      varchar      │               varchar                │           varchar            │       varchar       │
├───────────┼─────────────────────────┼───────────────┼─────────────────┼───────────────────┼──────────────────────────────────────┼──────────────────────────────┼─────────────────────┤
│     20904 │ Tofu nature, préemballé │ 04            │ 0411            │ 000000            │ viandes, œufs, poissons et assimilés │ substitus de produits carnés │ -                   │
└───────────┴─────────────────────────┴───────────────┴─────────────────┴───────────────────┴──────────────────────────────────────┴──────────────────────────────┴─────────────────────┘
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
/* Illustration of agribalyse:
┌──────────────────────┬──────────────────┬──────────────────┬─────────────┬───┬──────────────────┬───────────────────┬──────────────────────┬──────────────────────┬──────────────────────┐
│ agribalyse_food_code │ ciqual_food_code │ ciqual_food_name │ season_code │ … │ energy_depletion │ mineral_depletion │ biogenic_climate_c…  │ fossil_climate_cha…  │ land_use_change_cl…  │
│       varchar        │      int64       │     varchar      │    int64    │   │      double      │      double       │        double        │        double        │        double        │
├──────────────────────┼──────────────────┼──────────────────┼─────────────┼───┼──────────────────┼───────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ 20516                │            20516 │ Chick pea, dried │           2 │ … │             14.5 │           4.9e-06 │               0.0148 │                0.709 │                0.175 │
│ 20904                │            20904 │ Tofu, plain      │           2 │ … │             27.5 │          5.15e-06 │               0.0161 │                0.986 │              0.00187 │
├──────────────────────┴──────────────────┴──────────────────┴─────────────┴───┴──────────────────┴───────────────────┴──────────────────────┴──────────────────────┴──────────────────────┤
│ 2 rows                                                                                                                                                              29 columns (9 shown) │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
*/
CREATE OR REPLACE TABLE agribalyse AS (
  SELECT
  "Code AGB" as agribalyse_food_code,
  "Code CIQUAL" as ciqual_food_code,
  "LCI Name" as ciqual_food_name,
  "code saison" as season_code,
  "code avion" as air_transport_code,
  "Livraison" as delivery_method,
  "Approche emballage" as packaging_approach,
  "Préparation" as preparation_method,
  "DQR" as data_quality_rating,
  "Score unique EF" as eco_score,
  "Changement climatique" as climate_change,
  "Appauvrissement de la couche d'ozone" as ozone_depletion,
  "Rayonnements ionisants" as ionizing_radiation,
  "Formation photochimique d'ozone" as photochemical_ozone_formation,
  "Particules fines" as fine_particles,
  "Effets toxicologiques sur la santé humaine : substances non-cancérogènes" as non_carcinogenic_toxicity,
  "Effets toxicologiques sur la santé humaine : substances cancérogènes" as carcinogenic_toxicity,
  "Acidification terrestre et eaux douces" as terrestrial_acidification,
  "Eutrophisation eaux douces" as freshwater_eutrophication,
  "Eutrophisation marine" as marine_eutrophication,
  "Eutrophisation terrestre" as terrestrial_eutrophication,
  "Écotoxicité pour écosystèmes aquatiques d'eau douce" as freshwater_ecotoxicity,
  "Utilisation du sol" as land_use,
  "Épuisement des ressources eau" as water_depletion,
  "Épuisement des ressources énergétiques" as energy_depletion,
  "Épuisement des ressources minéraux" as mineral_depletion,
  "Changement climatique - émissions biogéniques" as biogenic_climate_change_emissions,
  "Changement climatique - émissions fossiles" as fossil_climate_change_emissions,
  "Changement climatique - émissions liées au changement d'affectation des sols" as land_use_change_climate_change_emissions
  FROM read_csv('data/agribalyse_synthese.csv')
  WHERE agribalyse_food_code IS NOT NULL AND ciqual_food_code IS NOT NULL
);
/* Illustration of euro_exchange_rates:
┌──────────┬─────────┐
│ currency │  rate   │
│ varchar  │ double  │
├──────────┼─────────┤
│ CHF      │  0.9358 │
│ EUR      │     1.0 │
│ NOK      │  11.533 │
│ SEK      │ 10.9245 │
└──────────┴─────────┘
*/
CREATE OR REPLACE TABLE euro_exchange_rates AS (
  SELECT currency, rate FROM read_csv('data/euro_exchange_rates/latest.csv')
);
/* Illustration of prices:
┌───────┬─────────┬───────────────┬──────────────────────┬──────────────┬───┬──────────────────┬──────────────────────┬─────────────────┬──────────────────────┬──────────────────────┐
│  id   │  type   │ product_code  │     product_name     │ category_tag │ … │ location_osm_lon │ location_website_url │ location_source │   location_created   │   location_updated   │
│ int64 │ varchar │    varchar    │       varchar        │   varchar    │   │      double      │       varchar        │     varchar     │ timestamp with tim…  │ timestamp with tim…  │
├───────┼─────────┼───────────────┼──────────────────────┼──────────────┼───┼──────────────────┼──────────────────────┼─────────────────┼──────────────────────┼──────────────────────┤
│ 29904 │ PRODUCT │ 4099200179193 │ NULL                 │ NULL         │ … │        6.0860762 │ NULL                 │ NULL            │ 2024-07-06 14:35:3…  │ 2024-07-07 15:35:3…  │
│ 29955 │ PRODUCT │ 3111950001928 │ NULL                 │ NULL         │ … │        6.0966205 │ NULL                 │ NULL            │ 2024-07-06 19:59:0…  │ 2024-07-07 09:55:1…  │
│ 77758 │ PRODUCT │ 4099200179193 │ Tofu bio nature fu…  │ NULL         │ … │        6.0860762 │ NULL                 │ NULL            │ 2024-07-06 14:35:3…  │ 2024-07-07 15:35:3…  │
├───────┴─────────┴───────────────┴──────────────────────┴──────────────┴───┴──────────────────┴──────────────────────┴─────────────────┴──────────────────────┴──────────────────────┤
│ 3 rows                                                                                                                                                        48 columns (10 shown) │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
*/
CREATE OR REPLACE TABLE prices AS (
  SELECT * FROM read_parquet('data/prices.parquet')
);
/* Note: there are duplicates of the code in products, it is not a unique key
Illustration of products:
┌───────────────┬──────────────────┬──────────────────────┬──────────────────────┬────────────────────┬──────────────────┬──────────────────────┬────────────────────────────────────────────┐
│     code      │ product_quantity │     product_name     │ product_quantity_u…  │ product_quantity_1 │ ciqual_food_code │ ciqual_food_code_o…  │                 nutriments                 │
│    varchar    │      float       │ struct(lang varcha…  │       varchar        │       float        │      int32       │       varchar        │ struct("name" varchar, "value" float, "1…  │
├───────────────┼──────────────────┼──────────────────────┼──────────────────────┼────────────────────┼──────────────────┼──────────────────────┼────────────────────────────────────────────┤
│ 3111950001928 │           1000.0 │ [{'lang': main, 't…  │ g                    │             1000.0 │            20516 │                      │ [{'name': energy, 'value': 1480.0, '100g…  │
│ 4099200179193 │            350.0 │ [{'lang': main, 't…  │ g                    │              350.0 │            20904 │                      │ [{'name': energy, 'value': 528.0, '100g'…  │
└───────────────┴──────────────────┴──────────────────────┴──────────────────────┴────────────────────┴──────────────────┴──────────────────────┴────────────────────────────────────────────┘
*/
CREATE OR REPLACE TABLE products AS (
  SELECT
  code,
  countries_tags,
  nova_group,
  nutriments,
  ecoscore_score as eco_score,
  nutriscore_score as nutri_score,
  product_name,
  product_quantity_unit,
  CAST(product_quantity AS FLOAT) AS product_quantity,
  quantity AS quantity_str,
  categories,
  categories_tags,
  compared_to_category,
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
