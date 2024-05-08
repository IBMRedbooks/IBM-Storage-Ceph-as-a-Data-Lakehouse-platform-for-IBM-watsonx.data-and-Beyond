CREATE TABLE IF NOT EXISTS physical_store_sales (
    invoice_no BIGINT,
    stock_code BIGINT,
    product_name VARCHAR,
    quantity INTEGER,
    invoice_date TIMESTAMP,
    price DECIMAL(10, 2),
    customer_id BIGINT,
    country VARCHAR,
    payment_method VARCHAR,
    product_category VARCHAR
) WITH (
    format = 'CSV',
    external_location = 's3://your-bucket-name/physical_store_sales/',
    partitioned_by = ARRAY['country']  -- Optional: Partition based on your query patterns
);
