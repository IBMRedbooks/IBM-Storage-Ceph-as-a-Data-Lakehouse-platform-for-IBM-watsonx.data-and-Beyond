CREATE TABLE IF NOT EXISTS "ecommerce_browser_logs"."ecomm_logs".masked_data_partitioned (
    ts TIMESTAMP,
    tz VARCHAR,
    verb VARCHAR,
    resource_type VARCHAR,
    resource_fk VARCHAR,
    response INTEGER,
    browser VARCHAR,
    os VARCHAR,
    d_day_name VARCHAR,
    i_current_price DOUBLE,
    i_category VARCHAR,
    i_description VARCHAR,
    c_preferred_cust_flag BOOLEAN,
    ds DATE
)
WITH (
    format = 'Parquet',
    external_location = 's3a://ecommlogs/masked/',
    partitioned_by = ARRAY['ds']
);
