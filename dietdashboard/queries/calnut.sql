-- Documentation here: https://ciqual.anses.fr/cms/sites/default/files/inline-files/Table%20CALNUT%202020_doc_FR_2020%2007%2007.pdf
-- From table 0 we get the food group and subgroup
-- From table 1 we get upper_bound, lower_bound, mean, and an indicator of the completeness of the data
-- Both tables are joined by the ALIM_CODE and FOOD_LABEL columns
CREATE OR REPLACE TABLE calnut AS
WITH
calnut_0 AS (
    SELECT ALIM_CODE, FOOD_LABEL,
    alim_grp_code, alim_grp_nom_fr,
    alim_ssgrp_code, alim_ssgrp_nom_fr,
    alim_ssssgrp_code, alim_ssssgrp_nom_fr
    FROM read_csv($calnut_0_path)
    WHERE HYPOTH = 'MB'  -- to only have one row per food
),
calnut_1 AS (
    SELECT ALIM_CODE, FOOD_LABEL, CONST_LABEL, CONST_CODE,
    CAST(indic_combl AS BOOL) as combl,
    CAST(REPLACE(LB, ',', '.') AS FLOAT) as lb,
    CAST(REPLACE(UB, ',', '.') AS FLOAT) as ub,
    CAST(REPLACE(MB, ',', '.') AS FLOAT) as mean,
    FROM read_csv($calnut_1_path)
),
/* Pivoting the table to have one row per food
Following is an illustrative example of before and after pivoting:
Before:
┌───────────┬─────────────────┬───────────────┬────────────┬─────────┬───────┬───────┬───────┐
│ ALIM_CODE │   FOOD_LABEL    │  CONST_LABEL  │ CONST_CODE │  combl  │  lb   │  ub   │ mean  │
│   int64   │     varchar     │    varchar    │   int64    │ boolean │ float │ float │ float │
├───────────┼─────────────────┼───────────────┼────────────┼─────────┼───────┼───────┼───────┤
│     12114 │ Gruyère         │ proteines_g   │      25000 │ false   │  28.4 │  28.4 │  28.4 │
│     12049 │ Saint-Marcellin │ proteines_g   │      25000 │ false   │  15.1 │  15.1 │  15.1 │
│     12114 │ Gruyère         │ ag_20_4_ara_g │      42046 │ true    │ 0.024 │ 0.025 │ 0.025 │
│     12049 │ Saint-Marcellin │ ag_20_4_ara_g │      42046 │ false   │  0.02 │  0.02 │  0.02 │
└───────────┴─────────────────┴───────────────┴────────────┴─────────┴───────┴───────┴───────┘
After:
┌───────────┬─────────────────┬────────────────┬──────────────────┬────────────────┬───────────────────┬──────────────────┬────────────────────┬──────────────────┬─────────────────────┐
│ ALIM_CODE │   FOOD_LABEL    │ proteines_g_lb │ proteines_g_mean │ proteines_g_ub │ proteines_g_combl │ ag_20_4_ara_g_lb │ ag_20_4_ara_g_mean │ ag_20_4_ara_g_ub │ ag_20_4_ara_g_combl │
│   int64   │     varchar     │     float      │      float       │     float      │      boolean      │      float       │       float        │      float       │       boolean       │
├───────────┼─────────────────┼────────────────┼──────────────────┼────────────────┼───────────────────┼──────────────────┼────────────────────┼──────────────────┼─────────────────────┤
│     12049 │ Saint-Marcellin │           15.1 │             15.1 │           15.1 │ false             │             0.02 │               0.02 │             0.02 │ false               │
│     12114 │ Gruyère         │           28.4 │             28.4 │           28.4 │ false             │            0.024 │              0.025 │            0.025 │ true                │
└───────────┴─────────────────┴────────────────┴──────────────────┴────────────────┴───────────────────┴──────────────────┴────────────────────┴──────────────────┴─────────────────────┘
*/
calnut_1_pivoted AS (
    SELECT *
    FROM calnut_1
    PIVOT (
        first(lb) AS lb,
        first(mean) AS mean,
        first(ub) AS ub,
        first(combl) AS combl
        FOR CONST_LABEL IN
        ('acides_organiques_g', 'ag_04_0_g', 'ag_06_0_g', 'ag_08_0_g', 'ag_10_0_g', 'ag_12_0_g', 'ag_14_0_g', 'ag_16_0_g', 'ag_18_0_g',
        'ag_18_1_ole_g', 'ag_18_2_lino_g', 'ag_18_3_a_lino_g', 'ag_20_4_ara_g', 'ag_20_5_epa_g', 'ag_20_6_dha_g', 'agmi_g', 'agpi_g',
        'ags_g', 'alcool_g', 'amidon_g', 'beta_carotene_mcg', 'calcium_mg', 'cholesterol_mg', 'cuivre_mg', 'eau_g', 'fer_mg', 'fibres_g',
        'fructose_g', 'galactose_g', 'glucides_g', 'glucose_g', 'iode_mcg', 'lactose_g', 'lipides_g', 'magnesium_mg', 'maltose_g', 'manganese_mg',
        'nrj_kcal', 'nrj_kj', 'phosphore_mg', 'polyols_g', 'potassium_mg', 'proteines_g', 'retinol_mcg', 'saccharose_g', 'sel_g', 'selenium_mcg',
        'sodium_mg', 'sucres_g', 'vitamine_b12_mcg', 'vitamine_b1_mg', 'vitamine_b2_mg', 'vitamine_b3_mg', 'vitamine_b5_mg', 'vitamine_b6_mg',
        'vitamine_b9_mcg', 'vitamine_c_mg', 'vitamine_d_mcg', 'vitamine_e_mg', 'vitamine_k1_mcg', 'vitamine_k2_mcg', 'zinc_mg')
        GROUP BY ALIM_CODE, FOOD_LABEL
    )
)
SELECT calnut_0.alim_ssssgrp_code, calnut_0.alim_ssgrp_code, calnut_0.alim_grp_code,
    calnut_1_pivoted.*,
    calnut_0.alim_ssssgrp_nom_fr, calnut_0.alim_ssgrp_nom_fr, calnut_0.alim_grp_nom_fr
FROM calnut_1_pivoted
INNER JOIN calnut_0 ON calnut_1_pivoted.ALIM_CODE = calnut_0.ALIM_CODE
ORDER BY calnut_0.alim_ssssgrp_code, calnut_0.alim_ssgrp_code, calnut_0.alim_grp_code, calnut_0.alim_code
