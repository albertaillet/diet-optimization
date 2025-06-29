-- Price comparison: one row = category, one column = location
WITH base AS (
  SELECT
    p.compared_to_category AS category,
    pr.location_id,
    round(1000 * pr.price / p.product_quantity / ex.rate, 2) AS price
  FROM prices AS pr
  JOIN products AS p ON pr.product_code = p.code
  JOIN euro_exchange_rates ex ON pr.currency = ex.currency
  WHERE pr.location_id IN $locations
    AND p.product_quantity > 0
    AND p.compared_to_category IS NOT NULL
),
agg AS (
  SELECT
    category,
    location_id,
    MIN(price) AS price,
  FROM base
  GROUP BY category, location_id
)
SELECT *
FROM agg
PIVOT (MIN(price) FOR location_id IN $locations)
ORDER BY category;
