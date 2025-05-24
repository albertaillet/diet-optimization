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
/* Documentation: https://ciqual.anses.fr/cms/sites/default/files/inline-files/Table%20Ciqual%202020_doc_XML_ENG_2020%2007%2007.pdf
Downloaded from: https://ciqual.anses.fr/#/cms/telechargement/node/20 (XML format)
Tables:
- alim: information about the food (3 185 rows)
- compo: information about the nutrients in the food (211 898 rows)
- const: information about the nutrients (67 rows) (already in nutrient_map)
- sources: information about the sources of the data (207 896 rows)
Illustration of ciqual_alim:
┌┘
Illustration of ciqual_compo:
┌┘
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
    SELECT source_code,ref_citation FROM read_csv('data/ciqual2020/sources.csv')
);
/* Documentation: https://ciqual.anses.fr/cms/sites/default/files/inline-files/Table%20CALNUT%202020_doc_FR_2020%2007%2007.pdf
Table 0 contains food group information (2 119 rows)
Table 1 contains nutrient information for each food and nutrient (131 378 rows)
Both tables are joined on the ALIM_CODE and FOOD_LABEL columns
Fetched from https://github.com/openfoodfacts/openfoodfacts-server/tree/main/external-data/ciqual/calnut
Illustration of calnut_0:
┌┘
Illustration of calnut_1:
┌┘
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
/* Huggingface Documentation for open-prices data: https://huggingface.co/datasets/openfoodfacts/open-prices
Illustration of prices:
┌┘
*/
CREATE OR REPLACE TABLE prices AS (
    SELECT * FROM read_parquet('data/prices.parquet')
);
/* Open Food Facts data page: https://world.openfoodfacts.org/data
Huggingface dataset: https://huggingface.co/datasets/openfoodfacts/product-database
Note: there are duplicates of the code, it is not a unique key
Illustration of products:
┌┘
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
        WHEN categories_properties.ciqual_food_code IS NOT NULL THEN 'ciqual'
        WHEN categories_properties.agribalyse_food_code IS NOT NULL THEN 'agribalyse'
        WHEN categories_properties.agribalyse_proxy_food_code IS NOT NULL THEN 'agribalyse_proxy'
        ELSE 'unknown'
    END AS ciqual_food_code_origin,
    FROM read_parquet('data/products.parquet')
);
