-- Comparison table with one row per price.
SELECT
-- p.code AS product_code,
-- p.product_quantity,
-- p.product_quantity_unit,
-- pr.id AS price_id,
-- pr.price as product_price,
-- pr.currency as product_currency,
pr.location_id,
-- pr.location_osm_id,
split_part(pr.location_osm_display_name, ',', 1) AS location_name,
p.product_name[1].text AS product_name,
-- pr.location_osm_lat,
-- pr.location_osm_lon,
pr.price as product_price,
-- Price in EUR per 100g
100 * pr.price / p.product_quantity / ex.rate AS price,  -- TODO: this assumes that product_quantity is in grams
pr.date,
pr.proof_date,
pr.created,
pr.updated,
-- COUNT(*) AS count,
FROM prices AS pr
JOIN products AS p ON pr.product_code = p.code
JOIN euro_exchange_rates AS ex ON pr.currency = ex.currency
WHERE location_id IN $locations
  -- AND p.product_quantity > 0
  -- AND pr.proof_date BETWEEN '2024-09-21' AND '2024-10-11'
ORDER BY pr.proof_date, price;
-- GROUP BY pr.location_id, pr.location_osm_display_name
-- ORDER BY count DESC;
