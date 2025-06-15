CREATE TABLE ciqual_const AS SELECT * FROM read_csv('data/ciqual2020/const.csv');
CREATE TABLE nutrient_map AS SELECT *, ROW_NUMBER() OVER () AS row_num FROM read_csv('data/nutrient_map.csv');
CREATE TABLE new_nutrient_map AS
  SELECT
    nm.id,
    nm.name,
    cc.const_code AS ciqual_const_code,
    cc.const_nom_eng AS ciqual_const_name_eng,
    cc.const_nom_fr AS ciqual_const_name_fr,
    nm.ciqual_unit,
    nm.calnut_const_code,
    nm.calnut_const_name,
    nm.calnut_unit,
    nm.off_id,
    nm.count,
    nm.template,
    nm.nnr2023_id,
    nm.nutrient_type,
    nm.disabled,
    nm.comments,
  FROM nutrient_map nm
  FULL JOIN ciqual_const cc ON nm.ciqual_const_code = cc.const_code
  ORDER BY nm.row_num;
COPY new_nutrient_map TO 'data/nutrient_map.csv';
-- Select all rows that do not have a matching ciqual_const_code
SELECT id, name, ciqual_const_code, ciqual_const_name_eng, ciqual_const_name_fr
FROM nutrient_map
ANTI JOIN ciqual_const ON nutrient_map.ciqual_const_code = ciqual_const.const_code;
