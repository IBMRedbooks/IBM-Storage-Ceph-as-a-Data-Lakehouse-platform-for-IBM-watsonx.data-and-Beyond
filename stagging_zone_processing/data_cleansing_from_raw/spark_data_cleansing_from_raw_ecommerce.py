import os
import sys
import logging
import boto3
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, BooleanType, DateType
from pyspark.sql.functions import col, to_timestamp
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_environment_variables():
    """ Check for all necessary environment variables """
    required_vars = [
        'AWS_REGION', 'S3_ENDPOINT', 'SOURCE_BUCKET', 'DESTINATION_BUCKET',
        'SOURCE_ROLE_ARN', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY',
        'SPARK_MASTER_URL', 'STS_ENDPOINT', 'STS_REGION', 'SESSION_DURATION',
        'SPARK_DRIVER_HOST', 'S3_OBJECT_KEY'
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logging.error("Missing environment variables:")
        for var in missing_vars:
            logging.error(var)
        sys.exit(1)

def get_s3_client():
    """ Get a configured S3 client using assumed role credentials """
    session = boto3.Session(
        region_name=os.getenv('AWS_REGION'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    sts_client = session.client(
        'sts',
        endpoint_url=os.getenv('STS_ENDPOINT'),
        region_name=os.getenv('STS_REGION')
    )
    assumed_role = sts_client.assume_role(
        RoleArn=os.getenv('SOURCE_ROLE_ARN'),
        RoleSessionName="AssumeRoleSession",
        DurationSeconds=int(os.getenv('SESSION_DURATION'))
    )
    credentials = assumed_role['Credentials']
    return boto3.client(
        's3',
        region_name=os.getenv('AWS_REGION'),
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
        endpoint_url=os.getenv('S3_ENDPOINT')
    )


def check_s3_object_tag(bucket, key, tag_key):
    """ Check if the S3 object has a specific tag set """
    s3 = get_s3_client()
    try:
        tagging_info = s3.get_object_tagging(Bucket=bucket, Key=key)
        tags = {tag['Key']: tag['Value'] for tag in tagging_info['TagSet']}
        return tags.get(tag_key) == 'true'
    except ClientError as e:
        logging.error(f"Failed to get tags for {key}: {e}")
        return False

def tag_parquet_files(bucket, prefix, tag_key, tag_value):
    """ Tag all Parquet files in a specified S3 bucket prefix """
    s3 = get_s3_client()
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix, PaginationConfig={'PageSize': 1000}):
        for obj in page.get('Contents', []):
            if obj['Key'].endswith('.parquet'):
                s3.put_object_tagging(
                    Bucket=bucket,
                    Key=obj['Key'],
                    Tagging={'TagSet': [{'Key': tag_key, 'Value': tag_value}]}
                )


def main():
    """ Main function to process data using Spark with AWS IAM role assumption """
    check_environment_variables()
    source_bucket = os.getenv('SOURCE_BUCKET')
    destination_bucket = os.getenv('DESTINATION_BUCKET')
    s3_object_key = os.getenv('S3_OBJECT_KEY')
    browsing_prefix = 'browsing/'
    masked_prefix = 'masked/'

    if check_s3_object_tag(source_bucket, s3_object_key, 'processed'):
        logging.info(f"Object {s3_object_key} has already been processed.")
        return

    spark_master_url = os.getenv('SPARK_MASTER_URL', 'spark://localhost:7077')
    spark = SparkSession.builder \
        .appName("Data Processing with IAM Role Assumption") \
        .master(spark_master_url) \
        .config("spark.driver.host", os.getenv('SPARK_DRIVER_HOST')) \
        .config("spark.hadoop.fs.s3a.endpoint", os.getenv('S3_ENDPOINT')) \
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.auth.AssumedRoleCredentialProvider") \
        .config("spark.hadoop.fs.s3a.access.key", os.getenv('AWS_ACCESS_KEY_ID')) \
        .config("spark.hadoop.fs.s3a.secret.key", os.getenv('AWS_SECRET_ACCESS_KEY')) \
        .config("spark.hadoop.fs.s3a.assumed.role.arn", os.getenv('SOURCE_ROLE_ARN')) \
        .config("spark.hadoop.fs.s3a.assumed.role.sts.endpoint", os.getenv('STS_ENDPOINT')) \
        .config("spark.hadoop.fs.s3a.assumed.role.sts.endpoint.region", os.getenv('STS_REGION')) \
        .config("spark.hadoop.fs.s3a.assumed.role.session.duration", os.getenv('SESSION_DURATION')) \
        .config("spark.hadoop.fs.s3a.assumed.role.session.name", "sparkSession") \
        .config("spark.hadoop.fs.s3a.assumed.role.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.path.style.access", True) \
        .getOrCreate()

    browsing_schema = StructType([
        StructField("ip", StringType(), True),
        StructField("ts", StringType(), True),
        StructField("tz", StringType(), True),
        StructField("verb", StringType(), True),
        StructField("resource_type", StringType(), True),
        StructField("resource_fk", StringType(), True),
        StructField("response", IntegerType(), True),
        StructField("browser", StringType(), True),
        StructField("os", StringType(), True),
        StructField("customer", IntegerType(), True),
        StructField("d_day_name", StringType(), True),
        StructField("i_current_price", DoubleType(), True),
        StructField("i_category", StringType(), True),
        StructField("i_description", StringType(), True),
        StructField("c_preferred_cust_flag", BooleanType(), True),
        StructField("ds", DateType(), True)
    ])

    # Load and cleanse browsing data
    file_path = f"s3a://{source_bucket}/{s3_object_key}"
    browsing_df = spark.read.schema(browsing_schema).csv(file_path)
    browsing_df = browsing_df.withColumn("ts", to_timestamp(col("ts"), "yyyy-MM-dd HH:mm:ss"))
    browsing_cleaned = browsing_df.dropDuplicates()

    browsing_cleaned.write.partitionBy("ds").mode("overwrite").parquet(f"s3a://{destination_bucket}/{browsing_prefix}")
    browsing_cleaned.drop("ip", "customer").write.partitionBy("ds").mode("overwrite").parquet(f"s3a://{destination_bucket}/{masked_prefix}")

    # Tag the original object as processed
    s3 = get_s3_client()
    s3.put_object_tagging(
        Bucket=source_bucket,
        Key=s3_object_key,
        Tagging={'TagSet': [{'Key': 'processed', 'Value': 'true'}]}
    )
    tag_parquet_files(destination_bucket, browsing_prefix, 'secclearance', 'red')


    spark.stop()

if __name__ == "__main__":
    main()
