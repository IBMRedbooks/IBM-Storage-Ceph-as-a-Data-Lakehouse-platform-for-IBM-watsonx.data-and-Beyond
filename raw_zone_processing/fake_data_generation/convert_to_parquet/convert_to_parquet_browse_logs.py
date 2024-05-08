import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import sys
import os

def csv_to_parquet(input_file):
    data_types = {
        'ip': 'str',
        'ts': 'str', 
        'tz': 'str',
        'verb': 'str',
        'resource_type': 'str',
        'resource_fk': 'str',
        'response': 'int32',
        'browser': 'str',
        'os': 'str',
        'customer': 'int64',
        'd_day_name': 'str',
        'i_current_price': 'float64',
        'i_category': 'str',
        'i_description': 'str',
        'c_preferred_cust_flag': 'bool',
        'ds': 'str'
    }

    df = pd.read_csv(input_file, dtype=data_types)

    df['ts'] = pd.to_datetime(df['ts'], format='%Y-%m-%d %H:%M:%S')

    df['ds'] = pd.to_datetime(df['ds']).dt.date

    print(df.dtypes)

    schema = pa.schema([
        ('ip', pa.string()),
        ('ts', pa.timestamp('us')),
        ('tz', pa.string()),
        ('verb', pa.string()),
        ('resource_type', pa.string()),
        ('resource_fk', pa.string()),
        ('response', pa.int32()),
        ('browser', pa.string()),
        ('os', pa.string()),
        ('customer', pa.int64()),
        ('d_day_name', pa.string()),
        ('i_current_price', pa.float64()),
        ('i_category', pa.string()),
        ('i_description', pa.string()),
        ('c_preferred_cust_flag', pa.bool_()),
        ('ds', pa.date32())
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
