-- Comparison table with one row per price.
SELECT
p.code AS product_code,
pr.id AS price_id,
-- p.product_quantity,
-- p.product_quantity_unit,
-- pr.id AS price_id,
-- pr.currency as product_currency,
pr.location_id,
p.compared_to_category AS category,
-- pr.location_osm_id,
split_part(pr.location_osm_display_name, ',', 1) AS location_name,
p.product_name[1].text AS product_name,
-- pr.location_osm_lat,
-- pr.location_osm_lon,
pr.price as product_price,
p.product_quantity,
-- Price in EUR per kg
round(1000 * pr.price / p.product_quantity / ex.rate, 2) AS price_per_kg,
pr.date,
-- pr.proof_date,
-- pr.created,
-- pr.updated,
FROM prices AS pr
JOIN products AS p ON pr.product_code = p.code
JOIN euro_exchange_rates AS ex ON pr.currency = ex.currency
WHERE location_id IN $locations
  -- AND category ILIKE '%tomat%'
  -- AND p.product_name[1].text ILIKE '%lentil%'
  -- AND p.product_name[1].text ILIKE '%tomat%'
  AND p.product_name[1].text ILIKE '%pois%'
  -- AND p.product_quantity > 0
  -- AND pr.proof_date BETWEEN '2025-02-04' AND '2025-02-06'
  -- AND location_name like '%Aldi%'
-- ORDER BY pr.proof_date, price_per_kg;
ORDER BY price_per_kg;
