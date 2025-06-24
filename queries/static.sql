-- This SQL script generates static data files.

-- Locations
COPY (
  SELECT
    location_id AS id,
    location_osm_lat AS lat,
    location_osm_lon AS lon,
    location_osm_display_name AS name,
    COUNT(*) AS count
  FROM final_table
  GROUP BY id, lat, lon, name
  ORDER BY location_id, count DESC
)
TO 'dietdashboard/static/locations.csv';

-- Column descriptions
COPY (
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
  JOIN s ON c.column_name = s.column_name
)
TO 'dietdashboard/static/column_description.csv';
