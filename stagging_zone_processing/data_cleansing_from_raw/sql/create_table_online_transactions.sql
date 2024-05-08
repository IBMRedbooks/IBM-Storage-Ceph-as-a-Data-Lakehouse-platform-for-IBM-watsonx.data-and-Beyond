CREATE TABLE ecommerce_transactions.transactions.transactions (
    client_id bigint,
    transaction_id varchar,
    item_id varchar,
    transaction_date timestamp,
    country varchar,
    customer_type varchar,
    item_description varchar,
    category varchar,
    quantity integer,
    total_amount double,
    marketing_campaign varchar,
    returned boolean
)
WITH (
    external_location = 's3a://ecommtrans/transactions',
    format = 'PARQUET'
);
