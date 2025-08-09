-- Comparison table with one row per price.
SELECT
-- product_quantity,
-- product_quantity_unit,
-- price_id,
-- category,
-- location_osm_id,
-- location_osm_lat,
-- location_osm_lon,
product_name,
split_part(location_osm_display_name, ',', 1) AS location_name,
round(10 * price, 2) AS eur_price_per_kg,
product_price,
product_currency as currency,
product_quantity as product_quantity_g,
product_code,
price_id,
location_id,
price_date,
FROM final_table_price AS pr
WHERE location_id IN $locations
  -- AND product_name ILIKE '%lentil%'
  -- AND product_name ILIKE '%moul%'
  -- AND product_name ILIKE '%tomat%'
  -- AND product_name ILIKE '%pois%'
  -- AND price_date BETWEEN '2025-02-04' AND '2025-02-06'
  -- AND location_name like '%Aldi%'
-- ORDER BY price_date, price_per_kg;
ORDER BY eur_price_per_kg;
