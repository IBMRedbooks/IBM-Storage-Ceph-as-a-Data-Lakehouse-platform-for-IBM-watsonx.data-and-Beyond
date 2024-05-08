Summarize Total Sales by Product Category:
SELECT product_category, SUM(price * quantity) AS TotalSales
FROM physical_store_sales
GROUP BY product_category;

Find Top Selling Products:
SELECT product_name, SUM(quantity) AS TotalUnitsSold
FROM physical_store_sales
GROUP BY product_name
ORDER BY TotalUnitsSold DESC
LIMIT 10;

Average Sale Amount Per Invoice:
SELECT invoice_no, AVG(price * quantity) AS AvgSaleAmount
FROM physical_store_sales
GROUP BY invoice_no;

List of Products Sold on a Given Date:
SELECT DISTINCT product_name
FROM physical_store_sales
WHERE date(invoice_date) = date('YYYY-MM-DD');

Count of Unique Customers by Country:
SELECT country, COUNT(DISTINCT customer_id) AS UniqueCustomers
FROM physical_store_sales
GROUP BY country;

Sales Trends Over Time (Monthly):
SELECT date_format(invoice_date, '%Y-%m') AS Month, SUM(price * quantity) AS MonthlySales
FROM physical_store_sales
GROUP BY date_format(invoice_date, '%Y-%m')
ORDER BY Month;

Identify Return Customers:
SELECT customer_id, COUNT(DISTINCT invoice_no) AS NumberOfPurchases
FROM physical_store_sales
GROUP BY customer_id
HAVING COUNT(DISTINCT invoice_no) > 1;

Performance of Promotional Items:
SELECT product_name, SUM(quantity) AS UnitsSold, SUM(price * quantity) AS RevenueGenerated
FROM physical_store_sales
WHERE product_name LIKE '%Special%'
GROUP BY product_name;

Breakdown of Payment Methods:
SELECT payment_method, COUNT(*) AS Transactions, SUM(price * quantity) AS TotalAmount
FROM physical_store_sales
GROUP BY payment_method;

Sales Data for a Specific Country:
SELECT *
FROM physical_store_sales
WHERE country = 'Spain';
