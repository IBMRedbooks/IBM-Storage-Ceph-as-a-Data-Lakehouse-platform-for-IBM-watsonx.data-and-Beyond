Join Transactions and Browsing Logs on Client ID:
SELECT t.client_id, t.transaction_date, b.view_date, t.total_amount
FROM transactions t
JOIN browsing_logs b ON t.client_id = b.client_id
WHERE t.total_amount > 100;

Aggregate Total Sales by Product Category:
SELECT t.category, SUM(t.total_amount) AS total_sales
FROM transactions t
GROUP BY t.category;

Find Top 5 Most Frequently Purchased Products:
SELECT t.item_name, COUNT(*) AS purchase_count
FROM transactions t
GROUP BY t.item_name
ORDER BY purchase_count DESC
LIMIT 5;
List Transactions Along with Customer Browsing Before Purchase:

SELECT t.client_id, t.item_name, t.transaction_date, b.browser, b.os
FROM transactions t
JOIN browsing_logs b ON t.client_id = b.client_id AND t.item_id = b.item_id
WHERE t.transaction_date > b.view_date
ORDER BY t.transaction_date DESC;
Determine How Many Clients Have Browsed But Not Purchased:

SELECT b.client_id
FROM browsing_logs b
LEFT JOIN transactions t ON b.client_id = t.client_id
WHERE t.client_id IS NULL
GROUP BY b.client_id;
Advanced SQL Examples for Data Enrichment
Analyze Time Lag Between Browsing and Purchasing:

SELECT t.client_id, AVG(t.transaction_date - b.view_date) AS avg_time_diff
FROM transactions t
JOIN browsing_logs b ON t.client_id = b.client_id AND t.item_id = b.item_id
GROUP BY t.client_id;
Identify Cross-Selling Opportunities by Analyzing Co-Purchased Items:

SELECT t1.item_name AS item1, t2.item_name AS item2, COUNT(*) AS times_co_purchased
FROM transactions t1
JOIN transactions t2 ON t1.client_id = t2.client_id AND t1.transaction_id = t2.transaction_id AND t1.item_id != t2.item_id
GROUP BY t1.item_name, t2.item_name
ORDER BY times_co_purchased DESC;

Classify Clients Based on Browsing and Spending Patterns:
SELECT client_id,
       CASE 
           WHEN AVG(total_amount) > 500 THEN 'High spender'
           WHEN AVG(b.view_duration) > 300 THEN 'Engaged browser'
           ELSE 'Regular shopper'
       END AS shopper_type
FROM transactions t
JOIN browsing_logs b ON t.client_id = b.client_id
GROUP BY client_id;

Calculate Conversion Rate from Browsing to Purchase:
SELECT COUNT(DISTINCT t.client_id) / COUNT(DISTINCT b.client_id) AS conversion_rate
FROM transactions t
CROSS JOIN browsing_logs b;

Find Geographic Trends in Product Popularity:
SELECT b.country, t.item_name, COUNT(*) AS num_sales
FROM transactions t
JOIN browsing_logs b ON t.client_id = b.client_id
GROUP BY b.country, t.item_name
ORDER BY num_sales DESC;


##This would be for enrich with physical and online store.

Join on Customer ID:
SELECT o.client_id, o.transaction_date, p.invoice_date, o.total_amount, p.price
FROM online_transactions o
JOIN physical_store_sales p ON o.client_id = p.customer_id
WHERE o.item_name = p.product_name;
Aggregate Sales by Product Across Channels:

SELECT o.item_name, SUM(o.total_amount) AS online_sales, SUM(p.price * p.quantity) AS physical_sales
FROM online_transactions o
JOIN physical_store_sales p ON o.item_name = p.product_name
GROUP BY o.item_name;
Cross-Channel Customer Behavior:

SELECT o.client_id, COUNT(DISTINCT o.transaction_id) AS online_purchases, COUNT(DISTINCT p.invoice_no) AS physical_purchases
FROM online_transactions o
JOIN physical_store_sales p ON o.client_id = p.customer_id
GROUP BY o.client_id;

Product Category Performance Across Channels:
SELECT o.category, SUM(o.total_amount) AS online_revenue, SUM(p.price * p.quantity) AS physical_revenue
FROM online_transactions o
JOIN physical_store_sales p ON o.category = p.product_category
GROUP BY o.category;
