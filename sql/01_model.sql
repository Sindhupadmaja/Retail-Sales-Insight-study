-- Analytical model: one clean row per order and one per order item.
-- Canceled and unavailable orders never shipped, so they are excluded from sales.

CREATE OR REPLACE VIEW fact_orders AS
SELECT
    o.order_id,
    c.customer_unique_id,
    c.customer_state,
    o.order_status,
    CAST(o.order_purchase_timestamp AS TIMESTAMP)            AS purchased_at,
    DATE_TRUNC('month', CAST(o.order_purchase_timestamp AS TIMESTAMP)) AS order_month,
    CAST(o.order_delivered_customer_date AS TIMESTAMP)      AS delivered_at,
    CAST(o.order_estimated_delivery_date AS TIMESTAMP)      AS estimated_at,
    i.items,
    i.product_revenue,
    i.freight,
    r.review_score,
    CASE WHEN o.order_delivered_customer_date IS NULL THEN NULL
         WHEN CAST(o.order_delivered_customer_date AS TIMESTAMP)
              > CAST(o.order_estimated_delivery_date AS TIMESTAMP) THEN 1 ELSE 0 END AS is_late,
    DATE_DIFF('day', CAST(o.order_purchase_timestamp AS TIMESTAMP),
              CAST(o.order_delivered_customer_date AS TIMESTAMP)) AS delivery_days
FROM orders o
JOIN customers c USING (customer_id)
JOIN (
    SELECT order_id, COUNT(*) AS items, SUM(price) AS product_revenue, SUM(freight_value) AS freight
    FROM order_items GROUP BY order_id
) i USING (order_id)
LEFT JOIN (
    -- A few orders have more than one review; keep the most recent.
    SELECT order_id, review_score
    FROM order_reviews
    QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY review_answer_timestamp DESC) = 1
) r USING (order_id)
WHERE o.order_status NOT IN ('canceled', 'unavailable');

CREATE OR REPLACE VIEW fact_items AS
SELECT
    f.order_id,
    f.order_month,
    f.review_score,
    COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
    oi.price,
    oi.freight_value
FROM order_items oi
JOIN fact_orders f USING (order_id)
LEFT JOIN products p USING (product_id)
LEFT JOIN category_translation t USING (product_category_name);
