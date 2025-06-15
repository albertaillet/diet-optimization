SELECT
$objective as objective,
COLUMNS($nutrient_ids),
price_id,
product_code,
product_name,
ciqual_code,
ciqual_name,
color,
price,
location_osm_display_name,
location_osm_id,
FROM final_table
WHERE price IS NOT NULL
  AND price > 0
  AND location_id IN (SELECT UNNEST($locations))
  AND product_quantity > 0;
