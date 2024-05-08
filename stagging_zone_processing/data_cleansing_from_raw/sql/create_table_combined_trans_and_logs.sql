CREATE TABLE "ecommerce_curated_table"."joint_table_logs_trans".combined_browsing_transactions
WITH (
    format = 'PARQUET',
    partitioning = ARRAY['ds']
) AS
SELECT 
    b.ip, 
    b.ts, 
    b.tz, 
    b.verb, 
    b.resource_type, 
    b.resource_fk,
    b.response, 
    b.browser, 
    b.os, 
    b.customer, 
    b.d_day_name,
    b.i_current_price, 
    b.i_category, 
    b.i_description,
    b.c_preferred_cust_flag, 
    b.ds,
    t."transaction id" AS transaction_id, 
    t."item description" AS item_description, 
    t.category,
    t.quantity, 
    t."total amount" AS total_amount, 
    t."credit card number" AS credit_card_number, 
    t."transaction date" AS transaction_date
FROM 
    ecommerce_transactions.transactions.transactions t
JOIN 
    ecommerce_broswer_logs.browsing.browsing_data_partitioned b
ON 
    t."client id" = b.customer AND t."item id" = b.resource_fk;
