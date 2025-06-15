WITH
  c AS (
    SELECT column_name, comment FROM duckdb_columns()
    WHERE table_name = 'final_table'
      AND data_type IN ('DECIMAL','FLOAT','DOUBLE','REAL')
  ),
  s AS (SELECT * FROM (SUMMARIZE final_table))
SELECT
  c.column_name,
  c.comment,
  s.min,
  s.max,
  printf('%.2f', CAST(s.avg AS FLOAT)) AS mean,
FROM c
JOIN s ON c.column_name = s.column_name;
