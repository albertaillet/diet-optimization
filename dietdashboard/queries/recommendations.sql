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
