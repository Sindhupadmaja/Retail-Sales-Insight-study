-- name: monthly_kpis
SELECT
    order_month,
    COUNT(*)                                   AS orders,
    COUNT(DISTINCT customer_unique_id)         AS customers,
    SUM(product_revenue)                       AS revenue,
    SUM(product_revenue) / COUNT(*)            AS avg_order_value,
    AVG(review_score)                          AS avg_review,
    AVG(is_late)                               AS late_rate
FROM fact_orders
WHERE order_month BETWEEN $start AND $end
GROUP BY order_month
ORDER BY order_month;

-- name: yoy_growth
-- Same calendar months in both years, so seasonality does not distort the comparison.
SELECT
    SUM(CASE WHEN YEAR(order_month) = 2018 THEN product_revenue END) /
    SUM(CASE WHEN YEAR(order_month) = 2017 THEN product_revenue END) - 1   AS revenue_growth,
    COUNT(CASE WHEN YEAR(order_month) = 2018 THEN 1 END) * 1.0 /
    COUNT(CASE WHEN YEAR(order_month) = 2017 THEN 1 END) - 1               AS order_growth
FROM fact_orders
WHERE MONTH(order_month) BETWEEN 1 AND 8 AND YEAR(order_month) IN (2017, 2018);

-- name: category_performance
WITH cat AS (
    SELECT category,
           SUM(price)                                       AS revenue,
           COUNT(DISTINCT order_id)                         AS orders,
           AVG(review_score)                                AS avg_review,
           SUM(CASE WHEN YEAR(order_month) = 2017 AND MONTH(order_month) <= 8 THEN price END) AS rev_2017,
           SUM(CASE WHEN YEAR(order_month) = 2018 AND MONTH(order_month) <= 8 THEN price END) AS rev_2018
    FROM fact_items
    GROUP BY category
)
SELECT *,
       revenue / SUM(revenue) OVER ()                                         AS revenue_share,
       SUM(revenue) OVER (ORDER BY revenue DESC ROWS UNBOUNDED PRECEDING)
         / SUM(revenue) OVER ()                                               AS cumulative_share,
       rev_2018 / NULLIF(rev_2017, 0) - 1                                     AS yoy_growth
FROM cat
ORDER BY revenue DESC;

-- name: repeat_customers
WITH per_customer AS (
    SELECT customer_unique_id, COUNT(*) AS orders FROM fact_orders GROUP BY 1
)
SELECT COUNT(*)                                        AS customers,
       AVG(CASE WHEN orders > 1 THEN 1.0 ELSE 0 END)   AS repeat_rate,
       SUM(orders) * 1.0 / COUNT(*)                    AS orders_per_customer
FROM per_customer;

-- name: delivery_vs_reviews
SELECT
    CASE WHEN is_late = 1 THEN 'late' ELSE 'on time' END          AS delivery,
    COUNT(*)                                                      AS orders,
    AVG(review_score)                                             AS avg_review,
    AVG(CASE WHEN review_score <= 2 THEN 1.0 ELSE 0 END)          AS share_1_2_stars,
    AVG(CASE WHEN review_score = 5 THEN 1.0 ELSE 0 END)           AS share_5_stars,
    AVG(delivery_days)                                            AS avg_delivery_days
FROM fact_orders
WHERE is_late IS NOT NULL AND review_score IS NOT NULL
GROUP BY 1
ORDER BY 1;

-- name: review_by_days_late
SELECT
    LEAST(GREATEST(DATE_DIFF('day', estimated_at, delivered_at), -20), 20) AS days_vs_estimate,
    COUNT(*)            AS orders,
    AVG(review_score)   AS avg_review
FROM fact_orders
WHERE delivered_at IS NOT NULL AND review_score IS NOT NULL
GROUP BY 1
ORDER BY 1;

-- name: state_performance
SELECT
    customer_state                                AS state,
    COUNT(*)                                      AS orders,
    SUM(product_revenue)                          AS revenue,
    SUM(freight) / SUM(product_revenue)           AS freight_to_revenue,
    AVG(is_late)                                  AS late_rate,
    AVG(delivery_days)                            AS avg_delivery_days,
    AVG(review_score)                             AS avg_review
FROM fact_orders
GROUP BY 1
ORDER BY revenue DESC;

-- name: weekday_hour
SELECT DAYOFWEEK(purchased_at) AS weekday, HOUR(purchased_at) AS hour, COUNT(*) AS orders
FROM fact_orders
GROUP BY 1, 2
ORDER BY 1, 2;

-- name: peak_days
SELECT CAST(purchased_at AS DATE) AS day, COUNT(*) AS orders, SUM(product_revenue) AS revenue
FROM fact_orders
GROUP BY 1
ORDER BY orders DESC
LIMIT 5;
