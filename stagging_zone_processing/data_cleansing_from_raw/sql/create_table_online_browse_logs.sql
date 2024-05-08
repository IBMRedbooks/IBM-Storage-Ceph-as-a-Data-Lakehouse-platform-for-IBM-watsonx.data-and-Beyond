CREATE TABLE IF NOT EXISTS "ecommerce_broswer_logs"."browsing".browsing_data_partitioned (
    ip VARCHAR,
    ts TIMESTAMP,
    tz VARCHAR,
    verb VARCHAR,
    resource_type VARCHAR,
    resource_fk VARCHAR,
    response INTEGER,
    browser VARCHAR,
    os VARCHAR,
    customer BIGINT,
    d_day_name VARCHAR,
    i_current_price DOUBLE,
    i_category VARCHAR,
    i_description VARCHAR,
    c_preferred_cust_flag BOOLEAN,
    ds DATE
) 
WITH (
    format = 'Parquet',
    external_location = 's3a://ecommlogs/browsing/',
    partitioned_by = ARRAY['ds']
);

CALL ecommerce_broswer_logs.system.sync_partition_metadata(schema_name => 'ecomm_logs', table_name => 'browsing_data_partitioned', mode => 'ADD');
