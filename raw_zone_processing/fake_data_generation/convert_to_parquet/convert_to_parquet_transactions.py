import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import sys
import os

def csv_to_parquet(input_file):
    data_types = {
        'client_id': 'int64',
        'transaction_id': 'str',
        'item_id': 'str',
        'transaction_date': 'str', 
        'country': 'str',
        'customer_type': 'str',
        'item_description': 'str',
        'category': 'str',
        'quantity': 'int32',
        'total_amount': 'float64',
        'marketing_campaign': 'str',
        'returned': 'bool'
    }

    df = pd.read_csv(input_file, dtype=data_types)

    df['transaction_date'] = pd.to_datetime(df['transaction_date'], format='%Y-%m-%d %H:%M:%S')

    schema = pa.schema([
        ('client_id', pa.int64()),
        ('transaction_id', pa.string()),
        ('item_id', pa.string()),
        ('transaction_date', pa.timestamp('us')),
        ('country', pa.string()),
        ('customer_type', pa.string()),
        ('item_description', pa.string()),
        ('category', pa.string()),
        ('quantity', pa.int32()),
        ('total_amount', pa.float64()),
        ('marketing_campaign', pa.string()),
        ('returned', pa.bool_())
    ])

    output_file = os.path.splitext(input_file)[0] + '.parquet'
    table = pa.Table.from_pandas(df, schema=schema, preserve_index=False)
    pq.write_table(table, output_file, compression='snappy')

    print(f"Converted '{input_file}' to '{output_file}' successfully.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <input_file.csv>")
        sys.exit(1)

    input_file = sys.argv[1]
    csv_to_parquet(input_file)

